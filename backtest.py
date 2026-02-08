# backtest.py
# v0.4 — LSE Volume Shock Drift Hypothesis Backtest
# Tests: Low-liquidity LSE stocks that experience abnormal volume shocks
# exhibit positive short-term drift due to delayed institutional participation.

import pandas as pd
import numpy as np
from typing import Dict, List
import argparse

from market import MarketState
from system import VolumeShockDetector, VolumeShockEvent
from config import Config



def test_optimal_combination(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Test optimal filter combination: High-vol + High-conviction + Q5 + Earnings-like"""
    print("\n" + "="*70)
    print("OPTIMAL COMBINATION TEST")
    print("="*70)
    print("Filters Applied:")
    print("  - High volatility regime (vol > 40%)")
    print("  - High conviction (daily range > 5%)")
    print("  - High liquidity (Q5)")
    print("  - Earnings-like events (|price change| > 10%)")
    
    # Apply all filters
    filtered = [e for e in events if (
        e.vol_regime == 'HIGH' and
        e.high_conviction and
        e.liquidity_quintile == 5 and
        e.likely_earnings
    )]
    
    print(f"\nFiltered events: {len(filtered):,} (from {len(events):,} total)")
    
    if len(filtered) < 100:
        print("\n⚠️  Insufficient events after filtering (<100). Results may be unreliable.")
        return
    
    # Test both standard and extended horizons
    all_horizons = horizons + [20, 30, 60, 90]
    
    rows = []
    for horizon in all_horizons:
        metrics = compute_portfolio_metrics(filtered, horizon, cost_bps)
        if metrics and metrics['n_events'] > 0:
            rows.append({
                'horizon': f"{horizon}d",
                'n_events': metrics['n_events'],
                'mean_net_ret_%': round(metrics['mean_net_ret'] * 100, 3),
                'median_net_ret_%': round(metrics['median_net_ret'] * 100, 3),
                'sharpe': round(metrics['sharpe'], 3),
                'win_rate_%': round(metrics['win_rate'] * 100, 1),
                'std_ret_%': round(metrics['std_ret'] * 100, 3),
            })
    
    df = pd.DataFrame(rows)
    
    if df.empty:
        print("\nNo data available for filtered events.")
        return
    
    print("\nOptimal Combination Performance:")
    print(df.to_string(index=False))
    
    # Find best horizon by Sharpe
    best = df.loc[df['sharpe'].idxmax()]
    
    print("\n" + "="*70)
    print("BEST PERFORMING HORIZON")
    print("="*70)
    print(f"Horizon: {best['horizon']}")
    print(f"Sample Size: {best['n_events']:,} events")
    print(f"Mean Net Return: {best['mean_net_ret_%']:.3f}%")
    print(f"Median Net Return: {best['median_net_ret_%']:.3f}%")
    print(f"Sharpe Ratio: {best['sharpe']:.3f}")
    print(f"Win Rate: {best['win_rate_%']:.1f}%")
    print(f"Std Deviation: {best['std_ret_%']:.3f}%")
    
    # Verdict
    if best['sharpe'] > 0.5 and best['mean_net_ret_%'] > 15:
        print("\n✓ STRONG TRADABLE EDGE DETECTED")
        print("  Sharpe >0.5 and returns >15% with institutional holding period")
    elif best['sharpe'] > 0.3 and best['mean_net_ret_%'] > 10:
        print("\n~ MODERATE EDGE DETECTED")
        print("  Positive Sharpe and double-digit returns, but requires careful execution")
    elif best['mean_net_ret_%'] > 0:
        print("\n~ WEAK EDGE DETECTED")
        print("  Positive returns but low risk-adjusted performance")
    else:
        print("\n✗ NO EDGE AFTER FILTERING")
    
    # Yearly breakdown for best horizon
    if best['n_events'] > 500:
        print("\n" + "="*70)
        print(f"YEARLY CONSISTENCY ({best['horizon']} holding period)")
        print("="*70)
        
        analyze_yearly_performance(filtered, "OPTIMAL_COMBO", int(best['horizon'].replace('d', '')), cost_bps)


def test_short_side(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Test shorting volume shocks instead of going long"""
    print("\n" + "="*70)
    print("SHORT SIDE TEST (Inverse Strategy)")
    print("="*70)
    
    rows = []
    for horizon in horizons:
        returns = []
        for event in events:
            if horizon in event.forward_returns:
                gross_ret = -event.forward_returns[horizon]  # INVERT
                net_ret = gross_ret - (cost_bps / 10000)
                returns.append(net_ret)
        
        if not returns:
            continue
        
        returns = np.array(returns)
        rows.append({
            'horizon': f"{horizon}d",
            'n_events': len(returns),
            'mean_net_ret_%': returns.mean() * 100,
            'median_net_ret_%': np.median(returns) * 100,
            'sharpe': (returns.mean() / returns.std()) if returns.std() > 0 else 0,
            'win_rate_%': (returns > 0).mean() * 100,
        })
    
    df = pd.DataFrame(rows)
    print("\nShort Strategy Performance:")
    print(df.to_string(index=False))
    
    best = df.loc[df['sharpe'].idxmax()]
    print(f"\nBest Sharpe: {best['sharpe']:.3f} at {best['horizon']}")
    
    if best['sharpe'] > 0.5:
        print("✓ SHORT SIDE HAS EDGE")
    else:
        print("✗ SHORT SIDE NO EDGE")


def test_extended_horizons(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Test longer holding periods (20d, 30d, 60d, 90d)"""
    print("\n" + "="*70)
    print("EXTENDED HOLDING PERIODS")
    print("="*70)
    
    rows = []
    for horizon in horizons:
        returns = []
        for event in events:
            if horizon in event.forward_returns:
                gross_ret = event.forward_returns[horizon]
                net_ret = gross_ret - (cost_bps / 10000)
                returns.append(net_ret)
        
        if not returns:
            continue
        
        returns = np.array(returns)
        rows.append({
            'horizon': f"{horizon}d",
            'n_events': len(returns),
            'mean_net_ret_%': returns.mean() * 100,
            'median_net_ret_%': np.median(returns) * 100,
            'sharpe': (returns.mean() / returns.std()) if returns.std() > 0 else 0,
            'win_rate_%': (returns > 0).mean() * 100,
        })
    
    df = pd.DataFrame(rows)
    print("\nExtended Horizon Performance:")
    print(df.to_string(index=False))
    
    best = df.loc[df['sharpe'].idxmax()]
    print(f"\nBest Horizon: {best['horizon']} with Sharpe {best['sharpe']:.3f}")


def test_earnings_proxy(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Test filtering for likely earnings events (>10% price moves)"""
    print("\n" + "="*70)
    print("EARNINGS PROXY FILTER (|Price Change| > 10%)")
    print("="*70)
    
    earnings_events = [e for e in events if e.likely_earnings]
    non_earnings = [e for e in events if not e.likely_earnings]
    
    print(f"\nEarnings-like events: {len(earnings_events):,}")
    print(f"Non-earnings events: {len(non_earnings):,}")
    
    for label, subset in [("EARNINGS-LIKE", earnings_events), ("NON-EARNINGS", non_earnings)]:
        rows = []
        for horizon in horizons:
            metrics = compute_portfolio_metrics(subset, horizon, cost_bps)
            if metrics:
                rows.append({
                    'type': label,
                    'horizon': f"{horizon}d",
                    'n_events': metrics['n_events'],
                    'net_ret_%': round(metrics['mean_net_ret'] * 100, 3),
                    'sharpe': round(metrics['sharpe'], 3),
                })
        
        df = pd.DataFrame(rows)
        if not df.empty:
            print(f"\n{label}:")
            print(df.to_string(index=False))


def test_trailing_stops(df: pd.DataFrame, config: Config):
    """Test dynamic exit strategy with trailing stops"""
    print("\n" + "="*70)
    print("TRAILING STOP STRATEGY")
    print("="*70)
    print(f"Rules:")
    print(f"  - Exit losers after {config.TRAILING_STOP_LOSER_DAYS}d if < {config.TRAILING_STOP_LOSER_PCT}%")
    print(f"  - Hold winners until {config.TRAILING_STOP_WINNER_GIVEBACK_PCT}% drawdown from peak")
    
    # This requires tick-by-tick simulation - would need full price data
    # For now, approximate with daily bars
    
    print("\n⚠️  Trailing stop test requires full daily price series.")
    print("    Skipping for now (would need to reconstruct from raw data)")
    print("    TODO: Implement full simulation with daily bar data")


def test_market_cap_bins(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float, bins: List[int]):
    """Test performance across market cap bins"""
    print("\n" + "="*70)
    print("MARKET CAP BIN ANALYSIS")
    print("="*70)
    print(f"Bins (£M): {bins}")
    
    # NOTE: We don't have market cap in current data
    # Would need to pull from ds2mktval table in WRDS
    
    print("\n⚠️  Market cap data not available in current dataset.")
    print("    Would need to join with WRDS ds2mktval table.")
    print("    TODO: Pull market cap data and add to events")


def test_pairs_strategy(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Test market-neutral pairs strategy"""
    print("\n" + "="*70)
    print("MARKET-NEUTRAL PAIRS STRATEGY")
    print("="*70)
    print("Long: Volume shock stocks")
    print("Short: Matched non-shock stocks (same liquidity quintile)")
    
    # This requires non-shock universe data
    print("\n⚠️  Pairs strategy requires full universe data (shock + non-shock).")
    print("    Current data only contains shock events.")
    print("    TODO: Build matched pairs from full daily price data")


def print_combined_filter_results(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Print results for combined filters (high-vol + high-conviction)"""
    print("\n" + "="*70)
    print("COMBINED FILTER: HIGH VOLATILITY + HIGH CONVICTION")
    print("="*70)
    
    # Filter combinations
    filters = {
        'ALL': events,
        'HIGH_VOL': [e for e in events if e.vol_regime == 'HIGH'],
        'HIGH_CONV': [e for e in events if e.high_conviction],
        'HIGH_VOL + HIGH_CONV': [e for e in events if e.vol_regime == 'HIGH' and e.high_conviction],
        'HIGH_VOL + HIGH_CONV + Q5': [e for e in events if e.vol_regime == 'HIGH' and e.high_conviction and e.liquidity_quintile == 5],
        'HIGH_VOL + HIGH_CONV + DOWN': [e for e in events if e.vol_regime == 'HIGH' and e.high_conviction and e.shock_direction == 'DOWN'],
        'HIGH_VOL + HIGH_CONV + UP': [e for e in events if e.vol_regime == 'HIGH' and e.high_conviction and e.shock_direction == 'UP'],
    }
    
    rows = []
    for filter_name, subset in filters.items():
        for horizon in horizons:
            metrics = compute_portfolio_metrics(subset, horizon, cost_bps)
            if metrics:
                rows.append({
                    'filter': filter_name,
                    'horizon': f"{horizon}d",
                    'n_events': metrics['n_events'],
                    'net_ret_%': round(metrics['mean_net_ret'] * 100, 3),
                    'median_ret_%': round(metrics['median_net_ret'] * 100, 3),
                    'sharpe': round(metrics['sharpe'], 3),
                    'win_rate_%': round(metrics['win_rate'] * 100, 1),
                })
    
    df = pd.DataFrame(rows)
    if df.empty:
        print("No data available.")
        return
    
    print("\nMean Net Return (%):")
    pivot = df.pivot(index='filter', columns='horizon', values='net_ret_%')
    print(pivot.to_string())
    
    print("\nMedian Net Return (%):")
    pivot_med = df.pivot(index='filter', columns='horizon', values='median_ret_%')
    print(pivot_med.to_string())
    
    print("\nSharpe Ratio:")
    pivot_sharpe = df.pivot(index='filter', columns='horizon', values='sharpe')
    print(pivot_sharpe.to_string())
    
    print("\nWin Rate (%):")
    pivot_wr = df.pivot(index='filter', columns='horizon', values='win_rate_%')
    print(pivot_wr.to_string())
    
    print("\nNumber of Events:")
    pivot_n = df.pivot(index='filter', columns='horizon', values='n_events')
    print(pivot_n.to_string())
    
    # Print best combination
    print("\n" + "="*70)
    print("BEST FILTER COMBINATION")
    print("="*70)
    
    best_filter = None
    best_sharpe = -999
    best_horizon = None
    
    for filter_name, subset in filters.items():
        if filter_name == 'ALL':
            continue
        for horizon in horizons:
            metrics = compute_portfolio_metrics(subset, horizon, cost_bps)
            if metrics and metrics['sharpe'] > best_sharpe and metrics['n_events'] > 100:
                best_sharpe = metrics['sharpe']
                best_filter = filter_name
                best_horizon = horizon
    
    if best_filter:
        subset = filters[best_filter]
        metrics = compute_portfolio_metrics(subset, best_horizon, cost_bps)
        print(f"\nFilter: {best_filter}")
        print(f"Horizon: {best_horizon}d")
        print(f"Mean Net Return: {metrics['mean_net_ret']*100:.3f}%")
        print(f"Median Net Return: {metrics['median_net_ret']*100:.3f}%")
        print(f"Sharpe Ratio: {metrics['sharpe']:.3f}")
        print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
        print(f"Sample Size: {metrics['n_events']} events")
        
        if metrics['sharpe'] > 0.5 and metrics['mean_net_ret'] > 0:
            print(f"\n✓ TRADABLE EDGE DETECTED")
        elif metrics['mean_net_ret'] > 0:
            print(f"\n~ EDGE EXISTS BUT LOW SHARPE (outlier-driven)")
        else:
            print(f"\n✗ NO EDGE")
        
        # NEW: Yearly consistency check
        print("\n" + "="*70)
        print("YEARLY CONSISTENCY CHECK")
        print("="*70)
        
        analyze_yearly_performance(subset, best_filter, best_horizon, cost_bps)


def print_conviction_split_results(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Print results split by conviction (high range vs normal)"""
    print("\n" + "="*70)
    print("DRIFT BY CONVICTION (High Range vs Normal)")
    print("="*70)
    
    high_conv = [e for e in events if e.high_conviction]
    normal_conv = [e for e in events if not e.high_conviction]
    
    rows = []
    for label, subset in [('HIGH_RANGE', high_conv), ('NORMAL', normal_conv)]:
        for horizon in horizons:
            metrics = compute_portfolio_metrics(subset, horizon, cost_bps)
            if metrics:
                rows.append({
                    'conviction': label,
                    'horizon': f"{horizon}d",
                    'n_events': metrics['n_events'],
                    'net_ret_%': round(metrics['mean_net_ret'] * 100, 3),
                    'sharpe': round(metrics['sharpe'], 3),
                    'win_rate_%': round(metrics['win_rate'] * 100, 1),
                })
    
    df = pd.DataFrame(rows)
    if df.empty:
        print("No data available.")
        return
    
    print("\nMean Net Return (%):")
    pivot = df.pivot(index='conviction', columns='horizon', values='net_ret_%')
    print(pivot.to_string())
    
    print("\nSharpe Ratio:")
    pivot_sharpe = df.pivot(index='conviction', columns='horizon', values='sharpe')
    print(pivot_sharpe.to_string())


def print_volatility_regime_results(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Print results split by volatility regime"""
    print("\n" + "="*70)
    print("DRIFT BY VOLATILITY REGIME")
    print("="*70)
    
    regime_events = {'LOW': [], 'MEDIUM': [], 'HIGH': []}
    for event in events:
        regime_events[event.vol_regime].append(event)
    
    rows = []
    for regime in ['LOW', 'MEDIUM', 'HIGH']:
        for horizon in horizons:
            metrics = compute_portfolio_metrics(regime_events[regime], horizon, cost_bps)
            if metrics:
                rows.append({
                    'vol_regime': regime,
                    'horizon': f"{horizon}d",
                    'n_events': metrics['n_events'],
                    'net_ret_%': round(metrics['mean_net_ret'] * 100, 3),
                    'sharpe': round(metrics['sharpe'], 3),
                    'win_rate_%': round(metrics['win_rate'] * 100, 1),
                })
    
    df = pd.DataFrame(rows)
    if df.empty:
        print("No data available.")
        return
    
    print("\nMean Net Return (%):")
    pivot = df.pivot(index='vol_regime', columns='horizon', values='net_ret_%')
    print(pivot.to_string())
    
    print("\nSharpe Ratio:")
    pivot_sharpe = df.pivot(index='vol_regime', columns='horizon', values='sharpe')
    print(pivot_sharpe.to_string())


def analyze_yearly_performance(events: List[VolumeShockEvent], filter_name: str, horizon: int, cost_bps: float):
    """Analyze performance broken down by calendar year"""
    print("\n" + "="*70)
    print(f"YEARLY PERFORMANCE: {filter_name} at {horizon}d horizon")
    print("="*70)
    
    # Group events by year
    yearly_data = {}
    for event in events:
        if horizon not in event.forward_returns:
            continue
        
        year = event.shock_date.year
        if year not in yearly_data:
            yearly_data[year] = []
        
        gross_ret = event.forward_returns[horizon]
        net_ret = gross_ret - (cost_bps / 10000)
        yearly_data[year].append(net_ret)
    
    if not yearly_data:
        print("No data available.")
        return
    
    # Compute yearly metrics
    yearly_stats = []
    for year in sorted(yearly_data.keys()):
        returns = np.array(yearly_data[year])
        
        yearly_stats.append({
            'year': year,
            'n_trades': len(returns),
            'mean_ret_%': returns.mean() * 100,
            'median_ret_%': np.median(returns) * 100,
            'win_rate_%': (returns > 0).mean() * 100,
            'total_ret_%': returns.sum() * 100,
            'positive_year': returns.mean() > 0,
        })
    
    df = pd.DataFrame(yearly_stats)
    
    print("\nYearly Breakdown:")
    print(df.to_string(index=False))
    
    print(f"\nSummary Statistics:")
    print(f"  Total Years: {len(df)}")
    print(f"  Positive Years: {df['positive_year'].sum()} ({df['positive_year'].sum()/len(df)*100:.1f}%)")
    print(f"  Mean Annual Return: {df['mean_ret_%'].mean():.2f}%")
    print(f"  Median Annual Return: {df['median_ret_%'].mean():.2f}%")
    print(f"  Worst Year: {df['mean_ret_%'].min():.2f}%")
    print(f"  Best Year: {df['mean_ret_%'].max():.2f}%")
    
    # Check consistency
    positive_years = df['positive_year'].sum()
    total_years = len(df)
    
    if positive_years / total_years >= 0.7 and df['mean_ret_%'].mean() > 10:
        print("\n✓ CONSISTENT EDGE: >70% positive years with >10% average return")
    elif positive_years / total_years >= 0.6:
        print("\n~ INCONSISTENT EDGE: 60-70% positive years")
    else:
        print("\n✗ NO CONSISTENT EDGE: <60% positive years")
    
    return df




def load_lse_data(path: str) -> pd.DataFrame:
    """Load LSE daily price data"""
    df = pd.read_csv(path)
    df['marketdate'] = pd.to_datetime(df['marketdate'])
    df = df.sort_values(['dsseccode', 'marketdate']).reset_index(drop=True)
    df = df.dropna(subset=['close_', 'volume'])
    return df


def compute_portfolio_metrics(events: List[VolumeShockEvent], horizon: int, cost_bps: float) -> Dict:
    """Compute aggregate metrics for a given horizon"""
    returns = []
    
    for event in events:
        if horizon in event.forward_returns:
            gross_ret = event.forward_returns[horizon]
            net_ret = gross_ret - (cost_bps / 10000)
            returns.append(net_ret)
    
    if not returns:
        return {}
    
    returns = np.array(returns)
    
    return {
        'n_events': len(returns),
        'mean_gross_ret': float(np.mean([e.forward_returns[horizon] for e in events if horizon in e.forward_returns])),
        'mean_net_ret': float(np.mean(returns)),
        'median_net_ret': float(np.median(returns)),
        'std_ret': float(np.std(returns)),
        'sharpe': float(np.mean(returns) / np.std(returns)) if np.std(returns) > 0 else 0.0,
        'win_rate': float(np.mean(returns > 0)),
        'pct_25': float(np.percentile(returns, 25)),
        'pct_75': float(np.percentile(returns, 75)),
    }


def print_overall_results(results: Dict[int, Dict]):
    """Print overall results across all liquidity levels"""
    print("\n" + "="*70)
    print("OVERALL VOLUME SHOCK DRIFT ANALYSIS")
    print("="*70)
    
    for horizon in sorted(results.keys()):
        metrics = results[horizon]
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
        print(f"  25th / 75th pct:  {metrics['pct_25']*100:>8.3f}% / {metrics['pct_75']*100:>8.3f}%")


def print_liquidity_split_results(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Print results split by liquidity quintile"""
    print("\n" + "="*70)
    print("DRIFT BY LIQUIDITY QUINTILE (1=Lowest Liquidity, 5=Highest)")
    print("="*70)
    
    # Group events by quintile
    quintile_events = {}
    for event in events:
        q = event.liquidity_quintile
        if q not in quintile_events:
            quintile_events[q] = []
        quintile_events[q].append(event)
    
    # Build summary table
    rows = []
    for q in sorted(quintile_events.keys()):
        if q == 0:  # Skip events without quintile assignment
            continue
        
        for horizon in horizons:
            metrics = compute_portfolio_metrics(quintile_events[q], horizon, cost_bps)
            if metrics:
                rows.append({
                    'quintile': q,
                    'horizon': f"{horizon}d",
                    'n_events': metrics['n_events'],
                    'net_ret_%': round(metrics['mean_net_ret'] * 100, 3),
                    'sharpe': round(metrics['sharpe'], 3),
                    'win_rate_%': round(metrics['win_rate'] * 100, 1),
                })
    
    df = pd.DataFrame(rows)
    
    if df.empty:
        print("No data available.")
        return
    
    # Pivot tables
    print("\nMean Net Return (%):")
    pivot_ret = df.pivot(index='quintile', columns='horizon', values='net_ret_%')
    print(pivot_ret.to_string())
    
    print("\nSharpe Ratio:")
    pivot_sharpe = df.pivot(index='quintile', columns='horizon', values='sharpe')
    print(pivot_sharpe.to_string())
    
    print("\nWin Rate (%):")
    pivot_wr = df.pivot(index='quintile', columns='horizon', values='win_rate_%')
    print(pivot_wr.to_string())
    
    print("\nNumber of Events:")
    pivot_n = df.pivot(index='quintile', columns='horizon', values='n_events')
    print(pivot_n.to_string())


def print_verdict(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Print hypothesis verdict"""
    print("\n" + "="*70)
    print("HYPOTHESIS VERDICT")
    print("="*70)
    
    # Focus on low-liquidity quintile (Q1)
    q1_events = [e for e in events if e.liquidity_quintile == 1]
    
    if not q1_events:
        print("INCONCLUSIVE: Insufficient data in low-liquidity quintile.")
        return
    
    # Check best horizon
    best_horizon = None
    best_net_ret = -999
    
    for horizon in horizons:
        metrics = compute_portfolio_metrics(q1_events, horizon, cost_bps)
        if metrics and metrics['mean_net_ret'] > best_net_ret:
            best_net_ret = metrics['mean_net_ret']
            best_horizon = horizon
    
    if best_horizon is None:
        print("INCONCLUSIVE: No valid forward returns in low-liquidity quintile.")
        return
    
    metrics = compute_portfolio_metrics(q1_events, best_horizon, cost_bps)
    
    print(f"\nLow-Liquidity Quintile (Q1) — Best Horizon: {best_horizon}d")
    print(f"  Mean Net Return: {metrics['mean_net_ret']*100:.3f}%")
    print(f"  Sharpe Ratio:    {metrics['sharpe']:.3f}")
    print(f"  Win Rate:        {metrics['win_rate']*100:.1f}%")
    print(f"  Sample Size:     {metrics['n_events']} events")
    
    if best_net_ret > 0 and metrics['sharpe'] > 0.5:
        print(f"\n✓ HYPOTHESIS SUPPORTED")
        print(f"  Low-liquidity stocks show positive drift after volume shocks.")
    elif best_net_ret > 0:
        print(f"\n~ HYPOTHESIS WEAKLY SUPPORTED")
        print(f"  Positive drift exists but with low Sharpe ratio.")
    else:
        print(f"\n✗ HYPOTHESIS REJECTED")
        print(f"  Low-liquidity stocks show negative or zero drift.")



def print_direction_split_results(events: List[VolumeShockEvent], horizons: List[int], cost_bps: float):
    """Print results split by shock direction (UP/DOWN/FLAT)"""
    print("\n" + "="*70)
    print("DRIFT BY SHOCK DIRECTION")
    print("="*70)
    
    direction_events = {'UP': [], 'DOWN': [], 'FLAT': []}
    for event in events:
        direction_events[event.shock_direction].append(event)
    
    rows = []
    for direction in ['UP', 'DOWN', 'FLAT']:
        for horizon in horizons:
            metrics = compute_portfolio_metrics(direction_events[direction], horizon, cost_bps)
            if metrics:
                rows.append({
                    'direction': direction,
                    'horizon': f"{horizon}d",
                    'n_events': metrics['n_events'],
                    'net_ret_%': round(metrics['mean_net_ret'] * 100, 3),
                    'sharpe': round(metrics['sharpe'], 3),
                    'win_rate_%': round(metrics['win_rate'] * 100, 1),
                })
    
    df = pd.DataFrame(rows)
    if df.empty:
        print("No data available.")
        return
    
    print("\nMean Net Return (%):")
    pivot = df.pivot(index='direction', columns='horizon', values='net_ret_%')
    print(pivot.to_string())
    
    print("\nSharpe Ratio:")
    pivot_sharpe = df.pivot(index='direction', columns='horizon', values='sharpe')
    print(pivot_sharpe.to_string())
    
    print("\nWin Rate (%):")
    pivot_wr = df.pivot(index='direction', columns='horizon', values='win_rate_%')
    print(pivot_wr.to_string())
    
    print("\nNumber of Events:")
    pivot_n = df.pivot(index='direction', columns='horizon', values='n_events')
    print(pivot_n.to_string())



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LSE Volume Shock Drift Backtest — v0.4")
    parser.add_argument("--csv", default="lse_daily_prices.csv")
    parser.add_argument("--lookback", type=int, default=20)
    parser.add_argument("--threshold", type=float, default=2.0)
    parser.add_argument("--horizons", nargs="+", type=int, default=[1, 3, 5, 10])
    parser.add_argument("--cost", type=float, default=50.0)
    
    # Existing splits
    parser.add_argument("--liquidity-split", action="store_true")
    parser.add_argument("--direction-split", action="store_true")
    parser.add_argument("--conviction-split", action="store_true")
    parser.add_argument("--vol-regime-split", action="store_true")
    parser.add_argument("--all-splits", action="store_true")
    
    # NEW: Extended tests
    parser.add_argument("--test-short", action="store_true", help="Test shorting volume shocks")
    parser.add_argument("--test-extended", action="store_true", help="Test 20d, 30d, 60d, 90d holds")
    parser.add_argument("--test-earnings", action="store_true", help="Filter for earnings-like events")
    parser.add_argument("--test-trailing", action="store_true", help="Test trailing stop strategy")
    parser.add_argument("--test-mcap", action="store_true", help="Test market cap bins")
    parser.add_argument("--test-pairs", action="store_true", help="Test market-neutral pairs")
    parser.add_argument("--test-all-new", action="store_true", help="Run all new tests")
    
    parser.add_argument("--out", default="shock_events.csv")
    
    args = parser.parse_args()
    
    if args.all_splits:
        args.liquidity_split = True
        args.direction_split = True
        args.conviction_split = True
        args.vol_regime_split = True
    
    if args.test_all_new:
        args.test_short = True
        args.test_extended = True
        args.test_earnings = True
        args.test_trailing = True
        args.test_mcap = True
        args.test_pairs = True
    
    # Initialize
    cfg = Config()
    cfg.VOLUME_LOOKBACK_DAYS = args.lookback
    cfg.VOLUME_SHOCK_THRESHOLD_STD = args.threshold
    cfg.FORWARD_HORIZONS_DAYS = args.horizons
    cfg.TRANSACTION_COST_BPS = args.cost
    
    detector = VolumeShockDetector(cfg)
    
    print(f"Loading data from {args.csv}...")
    df = load_lse_data(args.csv)
    print(f"Loaded {len(df):,} rows across {df['dsseccode'].nunique():,} securities")
    
    print(f"\nDetecting volume shocks...")
    
    all_events = []
    securities = df['dsseccode'].unique()
    
    for i, sec in enumerate(securities, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(securities)} securities...")
        
        sec_df = df[df['dsseccode'] == sec].copy()
        events = detector.process_security(sec_df)
        all_events.extend(events)
    
    print(f"\nDetected {len(all_events):,} volume shock events")
    
    if not all_events:
        print("No volume shocks detected. Exiting.")
        exit(0)
    
    detector.assign_liquidity_quintiles(all_events)
    
    # Overall analysis
    print("\nComputing portfolio metrics...")
    overall_results = {}
    for horizon in args.horizons:
        overall_results[horizon] = compute_portfolio_metrics(all_events, horizon, args.cost)
    
    print_overall_results(overall_results)
    
    # Existing splits
    if args.liquidity_split:
        print_liquidity_split_results(all_events, args.horizons, args.cost)
        print_verdict(all_events, args.horizons, args.cost)
    
    if args.direction_split:
        print_direction_split_results(all_events, args.horizons, args.cost)
    
    if args.conviction_split:
        print_conviction_split_results(all_events, args.horizons, args.cost)
    
    if args.vol_regime_split:
        print_volatility_regime_results(all_events, args.horizons, args.cost)
    
    if args.all_splits or any([args.liquidity_split, args.direction_split, args.conviction_split, args.vol_regime_split]):
        print_combined_filter_results(all_events, args.horizons, args.cost)
    
    # NEW TESTS
    if args.test_short:
        test_short_side(all_events, args.horizons, args.cost)
    
    if args.test_extended:
        test_extended_horizons(all_events, cfg.EXTENDED_HORIZONS, args.cost)
    
    if args.test_earnings:
        test_earnings_proxy(all_events, args.horizons, args.cost)
    
    if args.test_trailing:
        test_trailing_stops(df, cfg)
    
    if args.test_mcap:
        test_market_cap_bins(all_events, args.horizons, args.cost, cfg.MCAP_BINS)
    
    if args.test_pairs:
        test_pairs_strategy(all_events, args.horizons, args.cost)

    # NEW TESTS
    if args.test_short:
        test_short_side(all_events, args.horizons, args.cost)
    
    if args.test_extended:
        test_extended_horizons(all_events, cfg.EXTENDED_HORIZONS, args.cost)
    
    if args.test_earnings:
        test_earnings_proxy(all_events, args.horizons, args.cost)
    
    # NEW: Optimal combination test (always run with test-all-new)
    if args.test_all_new or args.test_extended:
        test_optimal_combination(all_events, args.horizons, args.cost)
    
    if args.test_trailing:
        test_trailing_stops(df, cfg)
    
    if args.test_mcap:
        test_market_cap_bins(all_events, args.horizons, args.cost, cfg.MCAP_BINS)
    
    if args.test_pairs:
        test_pairs_strategy(all_events, args.horizons, args.cost)
    
    # Save events
    events_data = []
    for e in all_events:
        row = {
            'dsseccode': e.dsseccode,
            'shock_date': e.shock_date,
            'close_price': e.close_price,
            'volume': e.volume,
            'volume_zscore': e.volume_zscore,
            'adv_60d': e.adv_60d,
            'liquidity_quintile': e.liquidity_quintile,
            'shock_direction': e.shock_direction,
            'price_change_pct': e.price_change_pct,
            'daily_range_pct': e.daily_range_pct,
            'high_conviction': e.high_conviction,
            'volatility_20d': e.volatility_20d,
            'vol_regime': e.vol_regime,
            'likely_earnings': e.likely_earnings,
        }
        for h, ret in e.forward_returns.items():
            row[f'fwd_ret_{h}d'] = ret
        events_data.append(row)
    
    events_df = pd.DataFrame(events_data)
    events_df.to_csv(args.out, index=False)
    print(f"\nSaved {len(events_df):,} shock events → {args.out}")