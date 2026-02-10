# Crypto Volume Shock Analysis

Applied the same volume shock strategy from my [LSE research](https://github.com/0ywfe/lse-volume-shock-analysis) to crypto markets. Wanted to test if less efficient markets would produce better risk-adjusted returns.

**Spoiler**: They don't. Found the same edge but worse Sharpe, and it dies even faster.

## What I Found

### Best Strategy: HIGH_VOL + HIGH_CONV + Q5 (10d hold)

- Mean return: 309.57%
- Median return: -1.13% (most trades lose money)
- Sharpe ratio: 0.022 (catastrophically low)
- Win rate: ~45% (worse than coin flip)
- Standard deviation: Extreme (12,000%+ at short horizons)

### Yearly Performance

| Year | Return | What Happened |
|------|--------|---------------|
| 2017-2021 | Building | Edge developing |
| 2022 | +144.36% | Crypto winter (LUNA, FTX) - the golden year |
| 2023 | +1.78% | Edge dying |
| 2024 | +5.63% | Getting weaker |
| 2025 | -1.39% | Now negative |
| 2026 | -7.43% | Dead (17.7% win rate) |

## What Happened

Same story as LSE: one crisis year dominates everything.

**2022 was the crypto equivalent of Brexit 2016**:
- Massive crashes (LUNA, FTX collapse)
- Panic selling created opportunities
- Volume shocks caught the bottom
- Edge peaked at +144%

**Then it died fast**:
- LSE edge took 5+ years to decay
- Crypto edge dead within 2 years
- Information moves faster → arbitrage happens faster

By 2024-2026, the strategy is actively losing money. Edge completely saturated.

## LSE vs Crypto

| Metric | LSE (2005-2024) | Crypto (2017-2026) |
|--------|-----------------|-------------------|
| Best Year | +146% (2016) | +144% (2022) |
| Mean Return | +326% | +310% |
| Median Return | -8.79% | -1.13% |
| Sharpe Ratio | 0.078 | 0.022 |
| Positive Years | 19/20 (95%) | 6/10 (60%) |
| Edge Status | Saturated | Dead |

Crypto is strictly worse on every risk-adjusted metric. The "less efficient markets" thesis doesn't hold up.

## Why This Failed

Same fundamental problems as LSE:

1. **Lottery ticket distribution** - Mean looks good (309%), median is negative (-1.13%)
2. **Terrible Sharpe** - 0.022 is untradable by any institutional standard
3. **One-time opportunity** - 2022 crisis won't repeat, just like Brexit 2016
4. **Already saturated** - Performance collapsing in real-time (2024-2026 negative)

## What I Learned

**Crypto saturates faster than equities**:
- Same patterns work (briefly)
- Die faster (2 years vs 5+ years)
- Information propagates faster in crypto

**Crisis opportunities are unique**:
- Brexit 2016 in LSE
- Crypto winter 2022 in crypto
- Neither will repeat the same way

**AI-generated hypotheses are systematically late**:

This is the second time testing an AI-suggested strategy that peaked years ago:
- Volume shocks in LSE → peaked 2016-2018, saturated now
- Volume shocks in crypto → peaked 2022, dead now

Pattern is clear: LLMs are trained on documented strategies. By the time something is documented enough to train an AI, it's already being traded and arbitraged away. You're systematically 3-5 years too late.

Extended thinking and web search improve reasoning but still search documented knowledge, so the lag remains.

**Honest assessment beats wishful thinking**:
- Both repos document failed strategies
- Recognizing when things don't work is more valuable than pretending they do

## Technical Details

**Data**:
- Source: CoinGecko API
- Period: 2017-2026 (9 years)
- Assets: Top 200 altcoins (excluding BTC/ETH)
- Observations: 401,648 rows
- Shock events detected: 26,104

**Methodology** (identical to LSE):
1. Volume shock detection (2σ above 20-day mean)
2. Liquidity quintiles (by average daily volume)
3. Volatility regime (90th percentile = HIGH_VOL)
4. Conviction signal (intraday range >1.5x average = HIGH_CONV)
5. Event filter (|price change| >10%)
6. Forward returns at 1d, 3d, 5d, 10d, 20d, 30d, 60d, 90d

## How to Run It
```bash
# Collect data
python3 data_fetch.py

# Run analysis
python3 backtest.py --csv Data/crypto_daily_prices.csv --test-all
```

## AI Usage

Built using Claude 4.5 Sonnet and 4.5 Sonnet Extended Thinking, ChatGPT 5.2 and 5.2 Thinking, and DeepSeek 3.2. Used AI for infrastructure, code generation, methodology, and documentation.

**Key discovery**: AI hypotheses are systematically late. LLMs suggest strategies from their training data, which are already documented and being arbitraged. By the time a pattern is well-known enough to train an AI, it's 3-5 years past peak performance.

Extended thinking and web search can improve reasoning quality but can't escape this limitation since they still search documented knowledge rather than discovering novel patterns.

## License

MIT

---