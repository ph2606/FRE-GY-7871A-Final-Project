# Investment extension: fixed rules and evaluation

Protocol recorded October 17, 2026, before this extension calculates market or strategy performance. Market endpoint availability was tested first, without strategy fitting. This is a retrospective research design, not a preregistered experiment or an untouched live test. Rules reflect findings already known from this project; no return-based search, parameter grid or winning-rule selection is permitted.

The economic study remains frozen October 13. Monthly allocation origins run January 2015–September 2026, with returns ending at the October 2026 execution boundary, before October 13. The added market history is retrieved retrospectively for this extension. No trades are placed.

## Primary rule

Use only SPY (US large-cap equities) and BIL (one-to-three-month Treasury-bill ETF), without borrowing, short selling or derivatives. At each first-calendar-day origin:

1. Compute the last completed calendar month's SPY adjusted close and its ten-month simple moving average, including that completed month. Require price strictly above that average.
2. Read the project's actual ALFRED UNRATE snapshot for the origin. Reindex to exact calendar months. Compute the latest three-month mean and subtract the lowest three-month mean among the latest twelve observation months. A difference below 0.50 percentage point passes the labor guard. This is a Sahm-style deterioration guard, not a declaration of recession. If the latest three months are incomplete, do not bridge the missing month: use defensive allocation.
3. Hold 80% SPY / 20% BIL if both conditions pass; otherwise hold 20% SPY / 80% BIL. Rebalance at the close of the first jointly observed ETF session strictly after the first calendar day. No return ending at that close is credited to the new signal.

This is an evidence-gated risk allocation: the project does not establish that negative news or its provider comparison identifies mispricing. The primary rule excludes revised survey targets and reconstructed text. Its economic connection is the need to distinguish genuine labor pressure from model-dependent pessimism; market trend supplies a separate price confirmation. These choices are hypotheses to evaluate, not deductions of profitability from a sentiment forecast.

## Benchmarks and exploratory overlays

Use the same entry/exit sessions for SPY buy-and-hold, BIL buy-and-hold and monthly-rebalanced 60% SPY / 40% BIL. Do not report an exposure-matched portfolio chosen ex post as a prespecified benchmark.

Two secondary rules are evaluated only on the original common February 2023–September 2026 origins (44 periods): add ten percentage points to the primary equity weight when the previous month's M1 observed-minus-forecast gap is negative; or subtract ten points when the previous full month's contextual media tone is negative. Weights remain between 0 and 1. Fixed zero thresholds and ten-point tilts are not optimized. The gap uses latest-final survey history and the media measure uses retrospectively reconstructed titles/model representations; both overlays are pseudo-real-time diagnostics, not validated tradable signals. The provider bars never choose securities or trades.

## Return accounting and evaluation

Acquire daily Yahoo chart close and adjusted-close data, with cash-distribution/split events, for SPY/BIL from 2009 through the required October 2026 boundary. Validate ticker, USD currency, New York date conversion, positive values, unique sorted sessions and explicit date bounds. Preserve exact response bytes, request parameters, hashes and retrieval times. Never forward-fill missing prices or substitute unadjusted prices. Yahoo adjusted prices approximate dividend-reinvested total returns; they are retrospective provider adjustments rather than actual executable prices. Common-session gaps must be audited. Fund expenses are already reflected in observed fund performance; do not subtract today's expense ratio from historical returns again.

Track daily asset-weight drift between monthly rebalances. The primary friction assumption is ten basis points per dollar bought or sold in either ETF, including entry and final liquidation. Solve the self-financing cost equation for target holdings after fees. Include 0 and 25 basis-point sensitivities, fractional units, and no leverage. Taxes, investor-specific commissions and nonlinear market impact are outside this account; the stated cost rate is an assumption, not a measured historical spread.

Report cumulative net return, calendar-time CAGR, daily volatility, maximum daily drawdown, average equity weight, turnover and BIL-relative Sharpe. Report calendar subperiods without selecting the best, and a separate 44-period overlay comparison. Use HAC(21) uncertainty for the primary strategy's daily excess return over the fixed mix, and for its market-beta regression relative to BIL; neither statistic proves portable alpha. The two overlay-versus-primary mean-return tests form one separately disclosed BH-adjusted family. A positive historical net total return permits the phrase 'historically profitable after modeled costs'; it does not imply benchmark outperformance, causal media value, or future profit. Any future deployment requires an untouched prospective paper-trading period.

Primary reference definitions: [SPY issuer](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-sp-500-etf-trust-spy), [BIL issuer](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil), [Sahm indicator definition](https://fred.stlouisfed.org/series/SAHMREALTIME). These definitions motivate the inputs; they do not validate this combined rule.
