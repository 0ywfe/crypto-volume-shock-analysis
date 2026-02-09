# backtest.py
# Crypto Volume Shock Drift Analysis

import pandas as pd
import numpy as np
from typing import Dict, List
import argparse


def load_crypto_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['coin', 'timestamp']).reset_index(drop=True)
    df = df.dropna(subset=['close', 'volume'])
    return df


def detect_volume_shocks(df: pd.DataFrame, lookback: int = 20, threshold_std: float = 2.0) -> pd.DataFrame:
    df = df.copy()
    
    df['volume_mean'] = df.groupby('coin')['volume'].transform(
        lambda x: x.rolling(lookback, min_periods=lookback).mean()
    )
    df['volume_std'] = df.groupby('coin')['volume'].transform(
        lambda x: x.rolling(lookback, min_periods=lookback).std()
    )
    df['volume_zscore'] = (df['volume'] - df['volume_mean']) / df['volume_std']
    
    df['is_shock'] = (
        (df['volume_zscore'] > threshold_std) &
        (df['volume_mean'].notna()) &
        (df['volume_std'] > 0)
    )
    
    # Price metrics
    df['price_change_pct'] = df.groupby('coin')['close'].transform(lambda x: x.pct_change() * 100)
    df['daily_range_pct'] = ((df['high'] - df['low']) / df['close']) * 100
    
    # Direction
    df['shock_direction'] = 'FLAT'
    df.loc[df['price_change_pct'] > 0.5, 'shock_direction'] = 'UP'
    df.loc[df['price_change_pct'] < -0.5, 'shock_direction'] = 'DOWN'
    
    # Conviction (wide range)
    df['high_conviction'] = df['daily_range_pct'] > 5.0
    
    # Volatility regime
    df['returns'] = df.groupby('coin')['close'].transform(lambda x: x.pct_change())
    df['volatility_20d'] = df.groupby('coin')['returns'].transform(
        lambda x: x.rolling(20, min_periods=20).std() * np.sqrt(365) * 100
    )
    
    df['vol_regime'] = 'MEDIUM'
    df.loc[df['volatility_20d'] < 50, 'vol_regime'] = 'LOW'
    df.loc[df['volatility_20d'] > 100, 'vol_regime'] = 'HIGH'
    
    # Earnings proxy (extreme moves)
    df['likely_event'] = df['price_change_pct'].abs() > 15.0
    
    # Liquidity proxy (ADV)
    df['adv_60d'] = df.groupby('coin')['volume'].transform(
        lambda x: x.rolling(60, min_periods=20).mean()
    )
    
    return df


def compute_forward_returns(df: pd.DataFrame, horizons: List[int]) -> pd.DataFrame:
    df = df.copy()
    
    for N in horizons:
        df[f'fwd_ret_{N}d'] = df.groupby('coin')['close'].transform(
            lambda x: x.shift(-N) / x - 1
        )
    
    return df


def assign_liquidity_quintiles(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    shock_df = df[df['is_shock']].copy()
    
    if len(shock_df) == 0:
        df['liquidity_quintile'] = 0
        return df
    
    advs = shock_df['adv_60d'].dropna()
    if len(advs) == 0:
        df['liquidity_quintile'] = 0
        return df
    
    # Create quintiles only for rows with valid ADV
    valid_mask = df['adv_60d'].notna()
    df['liquidity_quintile'] = 0
    
    df.loc[valid_mask, 'liquidity_quintile'] = pd.qcut(
        df.loc[valid_mask, 'adv_60d'], 
        q=5, 
        labels=[1, 2, 3, 4, 5], 
        duplicates='drop'
    ).astype(int)
    
    return df

    


def compute_portfolio_metrics(df: pd.DataFrame, horizon: int, cost_bps: float) -> Dict:
    col = f'fwd_ret_{horizon}d'
    
    valid = df[col].dropna()
    if len(valid) == 0:
        return {}
    
    gross_ret = valid.mean()
    net_ret = gross_ret - (cost_bps / 10000)
    
    returns_net = valid - (cost_bps / 10000)
    
    return {
        'n_events': len(valid),
        'mean_gross_ret': gross_ret,
        'mean_net_ret': net_ret,
        'median_net_ret': returns_net.median(),
        'std_ret': returns_net.std(),
        'sharpe': (returns_net.mean() / returns_net.std()) if returns_net.std() > 0 else 0,
        'win_rate': (returns_net > 0).mean(),
    }


def print_overall_results(shock_df: pd.DataFrame, horizons: List[int], cost_bps: float):
    print("\n" + "="*70)
    print("OVERALL VOLUME SHOCK ANALYSIS")
    print("="*70)
    
    for horizon in horizons:
        metrics = compute_portfolio_metrics(shock_df, horizon, cost_bps)
        if not metrics:
            continue
        
        print(f"\n{horizon}-Day Forward Period:")
        print(f"  Events:           {metrics['n_events']:,}")
        print(f"  Mean Gross Ret:   {metrics['mean_gross_ret']*100:>8.3f}%")
        print(f"  Mean Net Ret:     {metrics['mean_net_ret']*100:>8.3f}%")
        print(f"  Median Net Ret:   {metrics['median_net_ret']*100:>8.3f}%")
        print(f"  Std Dev:          {metrics['std_ret']*100:>8.3f}%")
        print(f"  Sharpe Ratio:     {metrics['sharpe']:>8.3f}")
        print(f"  Win Rate:         {metrics['win_rate']*100:>8.1f}%")


def print_filter_breakdown(shock_df: pd.DataFrame, horizons: List[int], cost_bps: float):
    print("\n" + "="*70)
    print("FILTER BREAKDOWN")
    print("="*70)
    
    filters = {
        'ALL': shock_df,
        'HIGH_VOL': shock_df[shock_df['vol_regime'] == 'HIGH'],
        'HIGH_CONV': shock_df[shock_df['high_conviction']],
        'HIGH_VOL+CONV': shock_df[(shock_df['vol_regime'] == 'HIGH') & (shock_df['high_conviction'])],
        'HIGH_VOL+CONV+Q5': shock_df[(shock_df['vol_regime'] == 'HIGH') & 
                                      (shock_df['high_conviction']) & 
                                      (shock_df['liquidity_quintile'] == 5)],
        'EVENT': shock_df[shock_df['likely_event']],
        'HIGH_VOL+EVENT': shock_df[(shock_df['vol_regime'] == 'HIGH') & (shock_df['likely_event'])],
    }
    
    rows = []
    for name, subset in filters.items():
        for h in horizons:
            m = compute_portfolio_metrics(subset, h, cost_bps)
            if m:
                rows.append({
                    'filter': name,
                    'horizon': f'{h}d',
                    'n': m['n_events'],
                    'net_ret_%': round(m['mean_net_ret']*100, 2),
                    'sharpe': round(m['sharpe'], 3),
                    'win_%': round(m['win_rate']*100, 1),
                })
    
    df = pd.DataFrame(rows)
    if df.empty:
        return
    
    print("\nNet Returns (%):")
    print(df.pivot(index='filter', columns='horizon', values='net_ret_%').to_string())
    
    print("\nSharpe Ratios:")
    print(df.pivot(index='filter', columns='horizon', values='sharpe').to_string())
    
    print("\nSample Sizes:")
    print(df.pivot(index='filter', columns='horizon', values='n').to_string())


def test_extended_horizons(shock_df: pd.DataFrame, horizons: List[int], cost_bps: float):
    print("\n" + "="*70)
    print("EXTENDED HOLDING PERIODS")
    print("="*70)
    
    for h in horizons:
        m = compute_portfolio_metrics(shock_df, h, cost_bps)
        if m:
            print(f"\n{h}d: {m['mean_net_ret']*100:>7.2f}% | Sharpe {m['sharpe']:.3f} | n={m['n_events']:,}")


def analyze_yearly(shock_df: pd.DataFrame, horizon: int, cost_bps: float):
    print("\n" + "="*70)
    print(f"YEARLY PERFORMANCE ({horizon}d hold)")
    print("="*70)
    
    col = f'fwd_ret_{horizon}d'
    valid = shock_df[[col, 'timestamp']].dropna()
    
    if len(valid) == 0:
        print("No data")
        return
    
    valid['year'] = valid['timestamp'].dt.year
    valid['net_ret'] = valid[col] - (cost_bps / 10000)
    
    yearly = valid.groupby('year')['net_ret'].agg([
        ('n', 'count'),
        ('mean_%', lambda x: x.mean()*100),
        ('median_%', lambda x: x.median()*100),
        ('win_%', lambda x: (x>0).mean()*100),
    ])
    
    print(yearly.to_string())
    
    pos_years = (yearly['mean_%'] > 0).sum()
    total_years = len(yearly)
    
    print(f"\nPositive Years: {pos_years}/{total_years} ({pos_years/total_years*100:.0f}%)")
    print(f"Mean Annual: {yearly['mean_%'].mean():.2f}%")
    print(f"Worst Year: {yearly['mean_%'].min():.2f}%")
    print(f"Best Year: {yearly['mean_%'].max():.2f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crypto Volume Shock Backtest")
    parser.add_argument("--csv", default="Data/crypto_daily_prices.csv")
    parser.add_argument("--lookback", type=int, default=20)
    parser.add_argument("--threshold", type=float, default=2.0)
    parser.add_argument("--horizons", nargs="+", type=int, default=[1, 3, 5, 10])
    parser.add_argument("--extended", nargs="+", type=int, default=[20, 30, 60, 90])
    parser.add_argument("--cost", type=float, default=30.0)
    parser.add_argument("--test-extended", action="store_true")
    parser.add_argument("--test-yearly", action="store_true")
    parser.add_argument("--test-all", action="store_true")
    
    args = parser.parse_args()
    
    if args.test_all:
        args.test_extended = True
        args.test_yearly = True
    
    print(f"Loading {args.csv}...")
    df = load_crypto_data(args.csv)
    print(f"Loaded {len(df):,} rows, {df['coin'].nunique()} coins")
    
    print(f"\nDetecting shocks (lookback={args.lookback}d, threshold={args.threshold}σ)...")
    df = detect_volume_shocks(df, lookback=args.lookback, threshold_std=args.threshold)
    
    print("Computing forward returns...")
    all_horizons = args.horizons + args.extended
    df = compute_forward_returns(df, all_horizons)
    
    print("Assigning liquidity quintiles...")
    df = assign_liquidity_quintiles(df)
    
    shock_df = df[df['is_shock']].copy()
    print(f"\nDetected {len(shock_df):,} volume shocks")
    
    if len(shock_df) == 0:
        print("No shocks found. Exiting.")
        exit(0)
    
    print_overall_results(shock_df, args.horizons, args.cost)
    print_filter_breakdown(shock_df, args.horizons, args.cost)
    
    if args.test_extended:
        test_extended_horizons(shock_df, args.extended, args.cost)
    
    if args.test_yearly:
        analyze_yearly(shock_df, 10, args.cost)
    
    print(f"\n{'='*70}")
    print("DONE")
    print(f"{'='*70}")