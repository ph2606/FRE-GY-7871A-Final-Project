# What happened when the headline gap alone chose the trades

Two of the three aggressive rules made a hypothetical profit after modeled costs. **All three grew less than simply holding SPY and suffered deeper losses along the way.** The experiment therefore does not establish a profitable advantage from the headline signal. Increasing leverage increased the financial consequences of a decision; it did not improve the quality of the evidence behind that decision.

These results cover **February 2, 2021 through October 2, 2026**, with 68 monthly decisions and 1,424 daily closing observations. The [protocol](BIAS_TRADING_PROTOCOL.md) was fixed before calculating the new strategy returns. It followed the original study and the earlier SPY/BIL allocation comparison, whose results were already known. It is a retrospective educational extension, not an untouched historical test or actual account performance. All three rules remain reported, including the losing one. No financial trades were placed.

## What made each decision

The signal averages Reuters' and NPR's negative-title fractions equally, subtracts the Colorado Sun's fraction, and multiplies by 100. It is a difference in percentage points, not a verified measure of false or unfair reporting. The fixed roster was selected for continuous coverage before calculating these trading results. It changes neither the original media corpus nor the separate provider bar chart.

At each first-calendar-day origin, the signal uses the immediately preceding completed month's gap. Its usual level is the median of the twelve calendar months before that measured month, excluding the measured month itself. The three ideas are:

- **Fade the gap:** buy UPRO when the gap is above its usual level; buy SPXU when it is below.
- **Follow the gap:** make the opposite choice.
- **Wait for a turn:** buy UPRO when the gap is above usual but falling, or SPXU when it is below usual but rising; otherwise hold BIL.

Ties and missing required inputs mean BIL. No unemployment, inflation, GDP, survey residual, price trend or stop-loss enters these choices. The February 2021 origin uses January 2021 text and a January–December 2020 baseline. The September 2026 origin uses August text; September text and incomplete October text do not determine any evaluated trade. The 68 current signal months contain 1,708 titles. The [signal method](BIAS_SIGNAL_METHOD.md) documents counts, exact rules and measurement limits.

## Costs and trading dates

Each rule invests all available value in its selected ETF. UPRO and SPXU seek +3x and -3x **daily** S&P 500 returns, before fund expenses. Actual daily adjusted ETF prices supply the return paths; the code never multiplies a monthly SPY return by three. The investor does not borrow outside the funds, but the funds themselves use leveraged exposure and derivatives. Their operating and financing costs already affect observed fund performance. The [fund explainer](LEVERAGED_FUNDS_EXPLAINED.md) gives a clearly labeled two-day arithmetic example and primary references.

Trades occur at the close of the first common exchange session strictly after each origin. Existing holdings earn the return into that close; the new choice earns only subsequent returns. Final liquidation is at the October 2 close, before the original October 13 study cutoff. Benchmarks use the same entry and exit dates.

The main assumption charges **10 basis points, or 0.10%, per dollar bought or sold**, including entry and liquidation. A full switch charges both the sale and the purchase. Fees are solved from available wealth, and holdings drift between rebalances. No missing prices are filled. Fractional adjusted-price units and reinvested distributions approximate a total-return account, rather than actual execution quotes. Taxes, nonlinear impact and investor-specific commissions are omitted.

## Results after the stated costs

The ending-value column starts every portfolio with the same $10,000. Drawdown means the largest fall from a prior portfolio peak measured at daily closes; intraday losses could be worse.

| Rule or comparison | Annual compound growth | Worst closing drawdown | Ending value |
| --- | ---: | ---: | ---: |
| Fade the gap | 6.59% | -63.73% | $14,352 |
| Follow the gap | -25.76% | -89.07% | $1,852 |
| Wait for a turn | 5.94% | -34.43% | $13,868 |
| Hold SPY | 14.70% | -24.50% | $21,734 |
| Hold BIL | 3.18% | -0.22% | $11,941 |
| Hold UPRO | 27.04% | -63.94% | $38,772 |
| Hold SPXU | -36.38% | -92.74% | $773 |
| Monthly 50% UPRO / 50% SPXU | -1.46% | -13.52% | $9,202 |
| Monthly 60% SPY / 40% BIL | 10.20% | -14.99% | $17,328 |

Fade's positive ending value came with a fall of almost two-thirds from a previous peak. Follow lost more than four-fifths of its initial value. Wait spent most decisions in BIL, but still had a 34.43% closing drawdown. Its lower exposure did not produce a lower observed drawdown than SPY. Always-UPRO's larger profit also came with a roughly 64% drawdown; it is a risk comparison, not a safe alternative or proof of useful timing. Equal amounts of UPRO and SPXU did not cancel to cash: both funds reset daily, their weights drift, and costs and compounding matter.

| Rule | UPRO decisions | SPXU decisions | BIL decisions |
| --- | ---: | ---: | ---: |
| Fade the gap | 38 | 29 | 1 |
| Follow the gap | 29 | 38 | 1 |
| Wait for a turn | 8 | 5 | 55 |

Those are monthly choices, not equal-duration daily exposure shares or round-trip trade counts. Fade and Follow each generated 78 purchase/sale legs including entry and exit; Wait generated 46. At 0 / 10 / 25 basis points per dollar traded, annual compound growth was **8.07% / 6.59% / 4.41%** for Fade, **-24.73% / -25.76% / -27.27%** for Follow, and **6.81% / 5.94% / 4.66%** for Wait. The cost sensitivities do not reveal a SPY-beating rule.

## A positive average difference is not compounded outperformance

Fade's mean daily return minus SPY's mean daily return, multiplied by 252, is **+3.19 percentage points a year**. Yet Fade's annual compound growth is 6.59%, below SPY's 14.70%. These are different calculations. Compound growth follows the product of daily gains and losses; large fluctuations can leave much less ending wealth than the arithmetic average suggests. The positive arithmetic difference must not be described as annual compounded outperformance.

The declared statistical family compares each rule's mean daily net return with SPY using HAC(21) uncertainty and Holm adjustment across three two-sided tests. The intervals below concern annualized **arithmetic mean differences**, not compound growth or future-profit ranges.

| Rule minus SPY | Annualized arithmetic difference | HAC(21) 95% interval | Holm-adjusted p |
| --- | ---: | ---: | ---: |
| Fade the gap | +3.19 percentage points | [-35.10, +41.49] | 0.870 |
| Follow the gap | -33.11 percentage points | [-75.65, +9.42] | 0.381 |
| Wait for a turn | -7.39 percentage points | [-23.63, +8.85] | 0.745 |

None supplies statistically reliable evidence of a positive advantage under the declared comparison. Failure to reject a difference does not show that the rules are equally good or equally safe; the realized growth and loss records remain important. These tests compare portfolios with different risks. They are not market-adjusted alpha tests, do not establish causality and do not account for every possible strategy someone could have tried.

Both prespecified allocation-origin subperiods are retained. Fade grows 9.33% annually in February 2021–December 2023 origins and 3.68% in January 2024–September 2026 origins; Follow loses 31.70% and 18.95%; Wait grows 2.01% and 10.28%. Each subperiod runs to its following execution boundary and charges its own entry and liquidation. These are retrospective stability descriptions, not new holdouts or a basis for selecting the better period.

## What was independently checked

An independent audit reconstructed the fixed-roster measure directly from frozen final-eligible title classes: 1,923 titles across 81 months, with all three outlets present every month. Equal weighting of Reuters and NPR matches the saved series within 7.1e-15 percentage point. All 68 earlier-twelve-month medians, strict signal lags and three fund choices match an independently written calculation. Every current-signal title's saved availability proxy precedes its origin's end; that metadata check does not recover original historical wording or search visibility.

A separate implementation held cash-valued ETF units and used an independent Brent numerical solver for self-financing fees. It reproduced **all nine daily wealth paths** within 1.2e-14 per initial dollar. Daily return chains, date bounds, compound growth and drawdowns match. A manual Newey–West calculation and Holm adjustment reproduce the reported tests. Raw UPRO/SPXU payload hashes, input hashes and the pre-performance protocol hash match the saved evidence. The large April 9–10, 2025 fund moves also appear in raw closing prices with stable adjustment factors and no split or distribution on those days; they are not created by a corporate-action adjustment. This checks a possible data artifact rather than independently certifying every historical quote. These checks found no consequential timing or accounting defect; they do not validate the trading hypothesis.

## What the experiment supports

The signal is a difference in sampled headline classifications, with different geography and topics on its two sides. Colorado Sun can contribute as few as one title in a month. Equal source weights preserve membership but cannot remove sampling noise, classifier error or differences in the facts being covered. Original wording and indexed feeds are not preserved at each historical date; the classifier was introduced after the earliest observations. There is no completed independent human validation of these labels for this use.

The evidence supports keeping these three ideas as transparent educational experiments. It does not support adopting one as a demonstrated edge, interpreting national-versus-local wording as irrationality, or promising a profitable trade. A separate frozen prospective test would be needed to investigate new predictive value. More leverage would magnify gains and losses without repairing the measurement limitations.

The local evidence is `outputs/tables/bias_trading_metrics.csv`, `bias_trading_daily.csv`, `bias_trading_summary.json` and `bias_trading_acquisition.json`, together with `data/processed/bias_trading_monthly.csv`, `bias_trading_signals.csv` and `bias_trading_prices.csv`. Data remain excluded from Git under the established submission policy.
