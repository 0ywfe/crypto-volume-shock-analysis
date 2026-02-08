# Volume Shock Drift Strategy - LSE Analysis

## Overview
A systematic trading strategy that detects abnormal volume spikes in LSE stocks (2005-2024) and tests whether they predict future returns. Started with a simple hypothesis about illiquid stocks, ended up finding something way more interesting (and completely untradable).

**TL;DR**: Found a real edge that makes 300%+ annual returns but loses money on most trades. It's a lottery ticket detector, not a proper trading strategy. Moving to crypto next.

**Note**: Cryptocurrency research will continue in a separate repository. This LSE analysis is now public and represents completed research.

## Current Findings

### Best Strategy: HIGH_VOL + HIGH_CONV + Q5 + Earnings-like + 90d Hold

**Performance (2005-2024)**:
- **Mean annual return**: 326.66%
- **Positive years**: 20/20 (100%)
- **Worst year**: 56.31% (2022)
- **Best year**: 912.63% (2005)
- **Sample size**: 14,050 events (approximately 700 trades annually)

**Risk Metrics**:
- **Sharpe ratio**: 0.078 (catastrophically low)
- **Median return**: -8.79% (most trades lose money)
- **Win rate**: 41.5% (majority are losers)
- **Standard deviation**: 4,117% (extreme volatility)

### Key Filter Performance Comparison

**Extended Holding Periods**:
- 90d: +36.67% mean, 0.023 Sharpe, 51.5% win rate
- 60d: +24.16% mean, 0.020 Sharpe, 51.1% win rate
- 30d: +12.11% mean, 0.016 Sharpe, 49.6% win rate
- 10d: +3.67% mean, 0.009 Sharpe, 46.3% win rate

**Earnings-like Events vs Non-earnings** (10d horizon):
- Earnings-like (|price change| > 10%): +18.11% mean, 0.024 Sharpe
- Non-earnings: +2.33% mean, 0.007 Sharpe

**Short Side Test**:
- All horizons show negative Sharpe ratios
- Confirms directional long bias, not mean reversion
- Volume shocks predict upward drift, not reversals

### Filter Components
- **HIGH_VOL**: 90th percentile realized volatility regime
- **HIGH_CONV**: Intraday range >1.5x recent average (wide-ranging days)
- **Q5**: Top liquidity quintile by average daily volume
- **Earnings-like**: Absolute price change >10% on shock day

## Hypothesis Evolution

### ❌ Rejected: Low-Liquidity Drift
**Original theory**: Volume shocks in illiquid stocks create delayed institutional participation → sustained drift

**Reality**: Backwards. Institutions need liquidity to participate. Low-liquidity shocks are noise, high-liquidity shocks attract institutional follow-through.

**Evidence**: Q1 (lowest liquidity) produced +1.08% vs Q5 (highest liquidity) +13.25% at 10d horizon.

### ✓ Supported: Volatility + Conviction Filter
**Theory**: Combining high volatility regime with high conviction signals (wide intraday ranges) isolates information-rich events

**Evidence**: 
- HIGH_VOL alone: +11.14% (10d)
- HIGH_CONV alone: +9.42% (10d)
- Combined: +13.37% (10d)
- Combined + Q5: +28.04% (10d)
- Combined + Q5 + Earnings-like + 90d: +36.67%

### ✓ Confirmed: Extended Holding Periods Capture More Alpha
**Theory**: Corporate events (takeovers, earnings developments) require 60-90 days to fully play out

**Evidence**: Monotonic improvement in Sharpe ratio from 1d (0.002) to 90d (0.023), with win rate crossing 50% only at extended horizons.

## Deep Dive: 2016-2018 Outlier Analysis

### The Numbers
Three consecutive years produced 57% of all cumulative 20-year returns:
- **2016**: +146.28% (2,184 trades, 45.6% win rate)
- **2017**: +72.10% (1,797 trades, 43.5% win rate)
- **2018**: +87.33% (1,795 trades, 37.7% win rate)

### Brexit Hypothesis: Why 2016 Exploded

**The Perfect Storm (June 23, 2016 Referendum):**

1. **Massive volatility spike** - Brexit vote triggered sustained high-vol regime, causing filters to trigger more frequently

2. **Currency collapse created bargains** - GBP crashed 10-15% overnight, making UK assets cheap for foreign buyers whilst domestic fundamentals remained solid

3. **M&A wave started** - Foreign institutions (US, EU, Asian) exploited mispricing, creating takeover wave with 30-50% premiums. Volume shocks likely caught information leakage before announcements.

4. **UK fundamentals stayed strong** - Unlike 2011 Eurozone crisis, this was opportunity (mispricing) not solvency crisis. Buyers had confidence to deploy capital.

5. **Retail panic created inefficiency** - Retail sold in fear, institutions bought the dip. Volume shocks captured this institutional accumulation.

### Why 2017-2018 Continued (But Weakened)

**2017 (+72%):**
- Post-Brexit M&A wave continued (Article 50, snap election uncertainty)
- Volatility remained elevated but normalizing
- Fewer takeover targets remaining

**2018 (+87%):**
- Second volatility wave (Brexit deadline fears, trade wars)
- Opportunistic M&A continued
- Win rate dropped to 37.7% (worst except 2011) - bigger outliers carrying fewer trades

### Comparison: Why Other Crisis Years Differed

**2011 (-2.11%): Eurozone Debt Crisis**
- Volume shocks = panic selling (not information)
- No M&A activity (solvency crisis, no buyer confidence)
- Result: strategies caught falling knives, not bargains

**2020 (+16%): COVID Crash**
- Volume shocks = margin calls and panic
- Government stimulus created bounce
- But no M&A wave (uncertainty too high)
- Result: captured mean reversion but no takeover premiums

**Key insight**: Volume shocks work when they signal information (buying opportunity) not when they signal fear (selling pressure). Distinguishing between the two in advance appears impossible.

### Edge Decay Analysis (2019-2024)

Recent performance suggests potential saturation:
- **2023**: +2.56% (weakest non-crisis year)
- **2024**: +12.27% (better but still weak vs historical)
- **2016-2018**: Peak performance (Brexit windfall)

Possible explanations:
- Post-2016 analysis by quant shops led to strategy saturation
- Brexit created one-time structural opportunity
- Market microstructure changes (faster information dissemination)

## What This Strategy Actually Captures

The research reveals this approach functions as a detector for rare, extreme events rather than systematic alpha generation:

**Event Types Captured**:
- Takeover announcements (require 60-90 days for regulatory approval)
- Extreme earnings surprises (multi-quarter drift effects)
- Short squeezes in heavily shorted names
- Material corporate developments (restructuring, asset sales)

**Why 90-Day Holds Work**:
- Corporate actions require regulatory approval timelines
- Post-earnings drift extends across multiple quarters
- Short squeezes persist for months as positions unwind
- Market digests transformative news slowly

**Why Most Trades Lose**:
- Strategy has 700 annual signals but only handful develop into mega-events
- Volume spikes often reflect noise rather than information
- High volatility creates false positives
- Transaction costs in illiquid names erode small gains

## Why This Cannot Be Traded Systematically

### Statistical Issues
- Sharpe ratio of 0.078 requires decades of data for confidence
- Extreme variance (4,117% std dev) makes significance testing unreliable
- 20 years of positive returns still insufficient given fat tails

### Position Sizing Impossibility
- 58.5% of trades lose money (median -8.79%)
- Strategy depends on rare mega-winners
- Kelly criterion and risk parity approaches fail with such extreme distributions
- No scientifically sound way to size positions

### Operational Complexity
- 700 trades annually with 90-day holds
- Requires constant portfolio turnover
- Simultaneous management of dozens of positions
- Capital commitment across many small positions

### Transaction Costs
- Strategy assumes 50 basis points
- Realistic market impact in illiquid LSE small-caps during high volatility: 100-150 basis points
- Entering positions during volume shocks increases market impact
- Costs likely eliminate most of the edge

### Institutional Requirements
- Institutions typically require Sharpe >1.0 for equity strategies
- Strategy produces Sharpe of 0.078 (13x below threshold)
- Risk-adjusted returns insufficient for professional capital deployment

## Honest Assessment

This research uncovered a genuine phenomenon. The pattern exists and persists across 20 years. Every calendar year tested produced positive returns. The edge is statistically real.

However, the edge is not a systematic alpha factor suitable for institutional deployment. Instead, it functions as a lottery ticket detector that occasionally identifies stocks before transformative events. The strategy succeeds by maintaining exposure when lightning strikes, accepting that most exposure attempts result in small losses.

The work demonstrates:
- Rigorous backtesting methodology
- Proper hypothesis testing and rejection
- Recognition of edge limitations
- Honest assessment of practical constraints

These research capabilities apply to finding edges in less-saturated markets where similar patterns might produce better risk-adjusted returns.

## Next Direction: Crypto Markets

Cryptocurrency research will continue in a separate repository. This keeps the LSE work clean and allows the crypto analysis to develop independently without mixing datasets and methodologies.

The decision to pivot toward cryptocurrency markets reflects several factors:

**Market Efficiency Differential**:
- Cryptocurrency markets remain substantially less efficient than developed equity markets
- The LSE edge likely worked better in 2005-2010 before systematic saturation
- Cryptocurrency markets today resemble equity markets from that earlier, less efficient era

**Structural Advantages**:
- Extreme volatility and fat-tailed distributions suit the research methodology
- Volume shock framework translates directly to crypto exchange data
- Information propagation through decentralised exchanges creates inefficiencies
- Price discovery remains imperfect across fragmented liquidity

**Practical Benefits**:
- Transaction costs have declined substantially on major exchanges
- Tight spreads and deep liquidity even during volatile periods
- Faster event development (hours/days vs months in equities)
- 24/7 markets enable more granular testing

**Research Infrastructure Transfer**:
- Volume shock detection logic applies directly
- Regime classification framework remains relevant
- Conviction signals (range expansion) translate cleanly
- Multi-factor filtering approach unchanged
- Main adjustment needed: shorter holding periods for faster event development

## Data
- **Source**: LSE daily prices via Datastream
- **Period**: 2005-2024 (20 years)
- **Securities**: 2,858 stocks
- **Total observations**: 7.2M rows
- **Shock events detected**: 450,744
- **Final filtered sample**: 14,050 events (optimal strategy)

## Methodology
1. **Volume shock detection**: 2σ above 20-day rolling mean
2. **Liquidity classification**: Quintiles by average daily volume
3. **Volatility regime**: 20-day realized vol vs 60-day percentile (>90th = HIGH_VOL)
4. **Conviction signal**: Intraday range vs 20-day average range (>1.5x = HIGH_CONV)
5. **Earnings proxy**: Absolute price change >10% on shock day
6. **Forward returns**: Compute 1d, 3d, 5d, 10d, 20d, 30d, 60d, 90d holding periods
7. **Transaction costs**: 50 basis points per round trip

## Files
- `backtest.py` - Main analysis engine with extended horizon testing
- `config.py` - Parameter configuration
- `system.py` - Signal generation and multi-factor filtering
- `market.py` - Market data handling
- `risk.py` - Risk metrics calculation
- `diagnostic.py` - Statistical testing utilities
- `extended_test_results.xlsx` - Comprehensive results across all tests

## Usage
```bash
# Run full analysis with all new tests
python3 backtest.py --csv lse_daily_prices.csv --test-all-new

# Run original analysis only
python3 backtest.py --csv lse_daily_prices.csv --all-splits
```

## Key Lessons Learned

1. **Outlier-driven strategies require extreme patience**: 20 years of data barely sufficient for confidence with Sharpe 0.078

2. **Median matters more than mean**: Mean return of 326% sounds impressive until you see median of -8.79%

3. **Edge identification ≠ edge tradability**: Finding a real pattern does not guarantee practical implementation

4. **Transaction costs destroy low-Sharpe edges**: 100bp vs 50bp assumption changes everything

5. **Crisis periods create opportunities but are not repeatable**: Brexit was one-time structural event

6. **Market efficiency evolves quickly**: What worked in 2005-2010 became saturated by 2016

7. **Honest assessment beats overfitting**: Better to acknowledge limitations than pretend edge is better than reality

## Caveats and Limitations

- Outlier-driven returns require extreme position sizing discipline impossible to implement scientifically
- Transaction costs modeled at 50bp but likely 100-150bp in reality during high volatility periods
- Survivorship bias possible (LSE data may exclude delistings, though less significant for 90d holds)
- Low Sharpe (0.078) means massive variance unsuitable for any leverage
- 2016-2018 results likely driven by one-time Brexit structural opportunity
- Edge may be saturated post-2018 as strategy became known to systematic funds
- Strategy requires £1M+ capital to diversify across 700 annual positions
- 90-day holding periods create operational complexity for individual traders
- No mechanism to distinguish information-driven volume shocks from noise-driven ones in advance

## Repository Purpose

This repository demonstrates systematic research methodology and technical capabilities rather than a tradable strategy. The work shows:

- Ability to work with large datasets (7.2M rows) and real market data
- Rigorous hypothesis testing including rejection of initial theories
- Multi-dimensional factor analysis and regime classification
- Extended backtesting across 20 years with proper transaction cost modeling
- Honest assessment of limitations and practical constraints
- Clear documentation and thoughtful analysis

These skills apply directly to researching market inefficiencies in less-saturated markets (cryptocurrency, emerging markets, alternative assets) where similar patterns might produce better risk-adjusted returns.

## Conclusion

This research succeeded in its primary objective: discovering whether volume shocks predict subsequent returns in LSE equities. The answer is yes, but with critical caveats that prevent systematic exploitation.

The pattern exists. The edge is real. The returns are positive across all years tested. But the structural characteristics (extreme outlier dependence, catastrophically low Sharpe, majority of trades losing money) make the strategy unsuitable for systematic trading.

The honest conclusion: this is interesting but untradable research. The methodology and infrastructure built here provide excellent foundations for exploring other market inefficiencies where better risk-adjusted returns might exist.

Future work will apply this framework to cryptocurrency markets in a separate repository, where higher inefficiency and better market microstructure may yield more actionable results.

## License
MIT