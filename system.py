# system.py
# v0.4 — LSE Volume Shock Signal Detection (Extended)

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

from config import Config
from market import MarketState


@dataclass
class VolumeShockEvent:
    """Volume shock event with forward return data"""
    dsseccode: float
    shock_date: pd.Timestamp
    close_price: float
    volume: int
    volume_zscore: float
    adv_60d: float
    liquidity_quintile: int
    forward_returns: Dict[int, float]
    
    # Direction & conviction metrics
    price_change_pct: float
    daily_range_pct: float
    shock_direction: str
    high_conviction: bool
    
    # Volatility regime
    volatility_20d: float
    vol_regime: str
    
    # NEW: Earnings proxy
    likely_earnings: bool  # True if extreme price move (>10%)


class VolumeShockDetector:
    """Detects volume shocks and computes forward returns"""
    
    def __init__(self, config: Config):
        self.config = config
        self.shock_events: List[VolumeShockEvent] = []
    
    def process_security(self, df: pd.DataFrame) -> List[VolumeShockEvent]:
        """
        Process a single security's daily data to detect volume shocks.
        
        Args:
            df: DataFrame with columns [marketdate, open_, high, low, close_, volume]
            Assumed sorted by marketdate ascending
        
        Returns:
            List of VolumeShockEvent objects
        """
        if len(df) < self.config.MIN_OBSERVATIONS_PER_STOCK:
            return []
        
        df = df.copy()
        df = df.sort_values('marketdate').reset_index(drop=True)
        
        # Compute rolling volume statistics
        df['volume_mean'] = df['volume'].rolling(
            self.config.VOLUME_LOOKBACK_DAYS,
            min_periods=self.config.VOLUME_LOOKBACK_DAYS
        ).mean()
        
        df['volume_std'] = df['volume'].rolling(
            self.config.VOLUME_LOOKBACK_DAYS,
            min_periods=self.config.VOLUME_LOOKBACK_DAYS
        ).std()
        
        # Z-score
        df['volume_zscore'] = (df['volume'] - df['volume_mean']) / df['volume_std']
        
        # Flag shocks
        df['is_shock'] = (
            (df['volume_zscore'] > self.config.VOLUME_SHOCK_THRESHOLD_STD) &
            (df['volume_mean'].notna()) &
            (df['volume_std'] > 0)
        )
        
        # Compute liquidity proxy (ADV)
        df['adv_60d'] = df['volume'].rolling(
            self.config.LIQUIDITY_ADV_WINDOW_DAYS,
            min_periods=20
        ).mean()
        
        # Price change and range metrics
        df['price_change_pct'] = (df['close_'] / df['close_'].shift(1) - 1) * 100
        df['daily_range_pct'] = ((df['high'] - df['low']) / df['close_']) * 100
        
        # Volatility regime (rolling 20d std of returns)
        df['returns'] = df['close_'].pct_change()
        df['volatility_20d'] = df['returns'].rolling(20, min_periods=20).std() * np.sqrt(252) * 100  # Annualized %
        
        # Forward returns (standard + extended)
        all_horizons = self.config.FORWARD_HORIZONS_DAYS + self.config.EXTENDED_HORIZONS
        for horizon in all_horizons:
            df[f'fwd_ret_{horizon}d'] = (
                df['close_'].shift(-horizon) / df['close_'] - 1
            )
        
        # Extract shock events
        shock_rows = df[df['is_shock']].copy()
        
        events = []
        for _, row in shock_rows.iterrows():
            fwd_rets = {}
            for h in all_horizons:
                ret = row.get(f'fwd_ret_{h}d')
                if pd.notna(ret):
                    fwd_rets[h] = float(ret)
            
            if not fwd_rets:  # Skip if no valid forward returns
                continue
            
            # Classify shock direction
            pct_change = row['price_change_pct']
            if pd.isna(pct_change):
                shock_dir = 'FLAT'
            elif pct_change > 0.5:
                shock_dir = 'UP'
            elif pct_change < -0.5:
                shock_dir = 'DOWN'
            else:
                shock_dir = 'FLAT'
            
            # High conviction = wide range
            daily_range = row['daily_range_pct']
            high_conviction = (
                pd.notna(daily_range) and 
                daily_range > self.config.HIGH_CONVICTION_RANGE_THRESHOLD_PCT
            )
            
            # Volatility regime
            vol = row['volatility_20d']
            if pd.isna(vol):
                vol_regime = 'MEDIUM'
            elif vol < 20:
                vol_regime = 'LOW'
            elif vol > 40:
                vol_regime = 'HIGH'
            else:
                vol_regime = 'MEDIUM'
            
            # Earnings proxy
            abs_pct_change = abs(pct_change) if pd.notna(pct_change) else 0
            likely_earnings = abs_pct_change > self.config.EARNINGS_PROXY_THRESHOLD_PCT
            
            events.append(VolumeShockEvent(
                dsseccode=row['dsseccode'],
                shock_date=row['marketdate'],
                close_price=float(row['close_']),
                volume=int(row['volume']),
                volume_zscore=float(row['volume_zscore']),
                adv_60d=float(row['adv_60d']) if pd.notna(row['adv_60d']) else 0.0,
                liquidity_quintile=0,  # Assigned later
                forward_returns=fwd_rets,
                price_change_pct=float(pct_change) if pd.notna(pct_change) else 0.0,
                daily_range_pct=float(daily_range) if pd.notna(daily_range) else 0.0,
                shock_direction=shock_dir,
                high_conviction=high_conviction,
                volatility_20d=float(vol) if pd.notna(vol) else 0.0,
                vol_regime=vol_regime,
                likely_earnings=likely_earnings,
            ))
        
        return events
    
    def assign_liquidity_quintiles(self, events: List[VolumeShockEvent]):
        """Assign liquidity quintiles based on ADV across all events"""
        if not events:
            return
        
        advs = [e.adv_60d for e in events if e.adv_60d > 0]
        if not advs:
            return
        
        quintile_edges = np.percentile(advs, [0, 20, 40, 60, 80, 100])
        
        for event in events:
            if event.adv_60d <= 0:
                event.liquidity_quintile = 0
                continue
            
            for q in range(1, self.config.LIQUIDITY_QUINTILES + 1):
                if event.adv_60d <= quintile_edges[q]:
                    event.liquidity_quintile = q
                    break