# Investment extension: results and independent audit

The fixed macro-and-trend allocation made a positive hypothetical historical profit after modeled costs, but failed its comparison with a simpler allocation. From January 2, 2015 through October 2, 2026, its net compound annual growth rate was **5.52%**, versus **9.17%** for a monthly-rebalanced **60% SPY / 40% BIL** portfolio. The fixed mix is therefore the preferred research reference after this comparison. This preference follows the observed results; it was not a preselected winning strategy, an optimized allocation, or evidence of future profitability.

This extension was designed October 17, after the project's economic and media findings were known. The [protocol](INVESTMENT_PROTOCOL.md) preceded calculation of strategy performance, and its SHA-256 matches the protocol hash recorded with both market acquisitions. That chronology prevents a claim of an untouched historical test. The economic study remains frozen October 13, and investment returns stop at the **October 2, 2026 closing execution boundary**. No subsequent returns enter the results. Retrieval occurred October 17 in New York, recorded October 18 in UTC. No financial trades were placed.

## Rule, information and accounting

At each first-calendar-day origin from January 2015 through September 2026, the primary rule holds 80% SPY and 20% BIL when the prior completed month's SPY adjusted close exceeds its ten-month average and the as-of unemployment deterioration measure is below 0.50 percentage point. Otherwise it holds 20% SPY and 80% BIL. The primary signal uses the actual ALFRED UNRATE snapshot for each origin and excludes revised sentiment targets and reconstructed media text. SPY represents US large-cap equities; BIL holds short Treasury bills, rather than a broad bond portfolio. [SPY issuer](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-sp-500-etf-trust-spy), [BIL issuer](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil).

The labor guard is a **custom Sahm-style measure**, not the published SAHMREALTIME series. It subtracts the minimum of the latest twelve three-month means, including the latest mean, from that latest mean. FRED's published definition refers to the previous twelve months; the custom measure can therefore differ and cannot be negative. Three-month means require all three exact calendar observations; at least nine of the twelve comparison means must be valid. The missing October 2025 CPS observation is never bridged or filled. Incomplete recent windows make the January and February 2026 origins defensive. These conventions were retained without return-based adjustment. [Published Sahm definition](https://fred.stlouisfed.org/series/SAHMREALTIME).

Execution occurs at the close of the first jointly observed ETF session **strictly after** each first-calendar-day origin. The first entry is January 2, 2015; final liquidation is October 2, 2026. A new weight receives only subsequent returns. Existing holdings earn the return into a rebalance close before the rebalance occurs. Daily prices are checked against exchange sessions; missing prices are never filled. Yahoo adjusted closes provide a retrospective split/distribution-adjusted total-return proxy. They are not executable adjusted-price quotes, and dividends are not added a second time. [Yahoo adjustment definition](https://in.help.yahoo.com/kb/adjusted-close-sln28256.html).

All portfolios pay **10 basis points per dollar bought or sold**, including initial purchases and final liquidation. Both legs count: selling $1 of one ETF and buying $1 of the other incurs approximately 20 basis points on that switched capital. Rebalancing solves `F = c × sum_i |w_i × (V − F) − H_i|`, where `F` is the fee, `c = 0.001`, `V` is pre-trade wealth, `H_i` is each pre-trade holding and `w_i` is its target weight. It does not assume costless restoration of weights. Holdings drift daily between rebalances. SPY and BIL buy-and-hold use identical entry and liquidation dates; the fixed mix rebalances on the same monthly dates as the primary rule. Fractional synthetic total-return units, reinvested distributions and no borrowing are assumed. Fund expenses already reflected in prices are not subtracted again. Taxes and nonlinear market impact are omitted; the cost rate is an assumption, not an observed historical spread.

## Main comparison

There are 141 allocation periods and 2,955 marked daily observations. Percentages below are nominal, net of the stated costs; terminal values assume $10,000 initially.

| Portfolio | Net total return | Net CAGR | Maximum daily drawdown | Terminal value |
| --- | ---: | ---: | ---: | ---: |
| Primary macro + trend rule | 88.01% | 5.52% | -20.11% | $18,801 |
| Fixed 60% SPY / 40% BIL | 180.16% | 9.17% | -20.78% | $28,016 |
| SPY buy-and-hold | 353.78% | 13.74% | -33.72% | $45,378 |
| BIL buy-and-hold | 25.29% | 1.94% | -0.23% | $12,529 |

The primary rule reduced volatility relative to SPY, but the fixed mix had a similar maximum drawdown and substantially stronger growth. Primary annualized daily volatility was 9.55%, versus 10.34% for the fixed mix; BIL-relative Sharpe ratios were 0.408 and 0.714. Average daily equity weights were 63.41% and 60.09%, respectively. Lower market exposure alone therefore does not explain the entire comparison. The primary's higher gross turnover also increases its cost burden. Its CAGR is 5.85% with zero modeled costs and 5.03% at 25 basis points per dollar traded; neither sensitivity changes the main comparison.

The primary-minus-fixed-mix **arithmetic mean daily return difference**, annualized by multiplying by 252, is -3.480 percentage points, with HAC(21) 95% interval [-6.372, -0.589] and p=0.0183. This is a different quantity from the difference in geometric CAGRs. Independent bandwidth checks give p=0.0183 at 63 lags and p=0.0203 at 126 lags. These are conditional historical comparisons, not corrections for choosing a strategy after observing economic history or for every possible investment rule.

Positive historical profit also differs from alpha. In the regression of the primary's daily return minus BIL's return on SPY's return minus BIL's return, the annualized arithmetic intercept is **-1.784 percentage points**, HAC(21) 95% interval [-4.839, +1.271], p=0.2525; estimated market beta is 0.454. This provides no evidence of positive market-model alpha. The regression adjusts for one market factor, not every investment risk or dynamic exposure. The calculated beta is a covariance-based coefficient and need not equal the average portfolio weight.

## Exploratory sentiment and media overlays

The two ten-percentage-point tilts use only the 44 original common origins, February 2023 through September 2026, with execution-to-execution returns from February 2, 2023 through October 2, 2026. They are explicitly pseudo-real-time: the lagged M1 gap uses revised survey history, while the media measure uses retrospectively reconstructed titles and a later language representation. The provider comparison never selects assets or trades.

| Rule on the common 44 periods | Net CAGR | Trigger frequency |
| --- | ---: | --- |
| Primary allocation | 12.31% | 36/44 origins in the higher-equity state |
| Gap overlay: add 10 points of equity when lagged gap is negative | 13.82% | 44/44 negative gaps |
| Media overlay: subtract 10 points when lagged tone is negative | 10.80% | 43/44 negative tones |
| Fixed 60% SPY / 40% BIL | 13.53% | Fixed allocation |

Every gap is negative, so the gap overlay is exactly an additional ten percentage points of target equity throughout this sample. It supplies no variation that could demonstrate useful gap timing. The media overlay is almost always a ten-point equity reduction. Raw overlay-minus-primary annualized arithmetic mean differences are +1.478 and -1.467 percentage points; their two-test BH-adjusted q-values are both 0.0233. These tests detect return differences, which can arise from equity exposure. They do not establish incremental information, mispricing, or a causal effect of pessimistic coverage.

After those results, an explicitly explanatory regression of each overlay-minus-primary daily return on SPY-minus-BIL returns estimates additional market betas of +0.0991 for the gap tilt and -0.0960 for the media tilt. The respective annualized arithmetic intercepts are +0.0178 percentage point, HAC(21) 95% interval [-0.0029, +0.0384], p=0.0920; and -0.0520 percentage point, interval [-0.2306, +0.1265], p=0.5679. Neither supplies evidence of positive incremental market-model alpha at the 5% level. These small intercepts explain why statistically detectable raw return differences do not demonstrate an informative trading signal. The diagnostics were added after inspecting results, remain exploratory, and do not replace the original two-test BH family; their quoted p-values are unadjusted.

## Audit and practical interpretation

An independent read-only audit rebuilt all 141 origin signals from the saved raw UNRATE vintages and prior completed-month prices, finding zero discrepancies. A separate cash-unit implementation with an independent numerical fee solver reproduced all ten saved full/common daily wealth paths to a maximum absolute error of 1.7e-14 per initial dollar. Return chains, date bounds, CAGR and daily drawdowns were also checked. These checks support code correctness; they do not validate an economic theory or future investment performance.

The project supports preferring the simple fixed SPY/BIL mix to the tested macro timing rule as a research reference, while retaining SPY buy-and-hold as the higher-equity-risk benchmark. It does not establish 60/40 as a universally suitable or optimal allocation. No winning rule is retuned after this comparison. A separately frozen prospective paper-trading period would be needed before claiming new predictive investment value. The SEC distinguishes hypothetical backtests from actual investment performance; historical positive net returns cannot promise future profit. [SEC performance-claims bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-47).

Computed evidence is retained locally in `outputs/tables/investment_metrics.csv`, `investment_summary.json`, `investment_full_daily.csv` and `investment_common_44_daily.csv`; source requests/hashes are in `investment_acquisition.json`, and origin signals are in `data/processed/investment_signals.csv`. These datasets remain outside Git under the established submission policy.
