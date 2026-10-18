# How the aggressive trading funds work

UPRO aims for **three times the S&P 500's daily return**, before fees and expenses. SPXU aims for **three times the opposite of its daily return**. If the index rises 1% in a day, their targets are approximately +3% and -3%. These targets apply to one day, not to the total return over a month or a year. [UPRO summary prospectus](https://www.proshares.com/globalassets/proshares/prospectuses/upro_summary_prospectus.pdf), [SPXU summary prospectus](https://www.proshares.com/globalassets/proshares/prospectuses/spxu_summary_prospectus.pdf).

Buying SPXU means owning shares of an inverse fund. The investor does not borrow stock or sell shares short. The fund itself uses derivatives to obtain inverse leveraged exposure. Similarly, owning UPRO without a margin loan still creates leveraged economic exposure. Investing all the account in either fund puts all the account at risk; the prospectuses describe circumstances in which the entire investment could be lost. [UPRO prospectus, principal risks](https://www.proshares.com/globalassets/proshares/prospectuses/upro_summary_prospectus.pdf), [SPXU prospectus, principal risks](https://www.proshares.com/globalassets/proshares/prospectuses/spxu_summary_prospectus.pdf).

## A two-day illustration

The following numbers are arithmetic examples, **not actual observations or backtest results**. Assume each fund meets its daily target exactly and ignore fees.

| Hypothetical investment | Start | After the index rises 10% | After the index falls 9.09% the next day |
| --- | ---: | ---: | ---: |
| Index | $100.00 | $110.00 | $100.00 |
| Fund targeting +3x daily | $100.00 | $130.00 | $94.55 |
| Fund targeting -3x daily | $100.00 | $70.00 | $89.09 |

The second day's exact index move is -1/11, or about -9.09%. The positive fund first gains 30%, then loses about 27.27% of its new balance. The inverse fund first loses 30%, then gains about 27.27% of its smaller balance. The index ends where it started, while both funds lose money. A steady trend can produce a different result. The point is that the sequence of daily moves matters. [SEC explanation of daily resets and compounding](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec).

The fund manager resets exposure each day even when an investor holds the same shares for a whole month. A monthly trading rule therefore cannot assume that UPRO earns three times SPY's monthly return, or that SPXU earns the negative of that amount.

## How the project measures them

The aggressive extension uses the funds' actual daily adjusted-price paths, rather than multiplying an ordinary fund's monthly returns. Adjusted prices account for splits and distributions and provide a retrospective total-return proxy. They are not actual adjusted-price execution quotes. Fund expenses, financing costs and tracking differences already affect the observed fund performance; subtracting another invented leverage or stock-borrow charge would double count costs. Investor trading fees remain separate, and are charged on purchases and sales under the frozen strategy protocol. [Yahoo adjusted-close definition](https://in.help.yahoo.com/kb/adjusted-close-sln28256.html), [UPRO financing and transaction costs](https://www.proshares.com/globalassets/proshares/prospectuses/upro_summary_prospectus.pdf), [SPXU financing and transaction costs](https://www.proshares.com/globalassets/proshares/prospectuses/spxu_summary_prospectus.pdf).

Each decision uses a completed month's captured headline measure. The trade takes place at the close of the first trading session strictly after the following month's first calendar day. A new holding earns returns only after that close. A purchase of an inverse fund is recorded as a positive holding of SPXU, not as a negative holding of UPRO. The account does not borrow outside the funds. Missing prices are never filled and no leveraged return is synthesized for an unavailable period.

A monthly 50% UPRO / 50% SPXU comparison holds equal fund values at each rebalance. It is not a safe cash substitute or a continuously market-neutral portfolio: the holdings drift, both funds reset daily, and both can lose value in a volatile market. Its purpose is to show what a balanced allocation to the same products does without a headline-based choice of direction.

Daily closing-price drawdown measures losses visible at daily closes. It cannot show the worst intraday loss, execution failure, trading halt or investor-specific tax outcome. An attractive hypothetical return would still require scrutiny of these risks and a separate prospective test. The SEC cautions that leveraged and inverse funds can have large losses and returns over longer periods that differ substantially from their daily targets. [SEC investor bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec).

## What the headline signal can establish

The proposed signal averages Reuters' and NPR's negative-title fractions equally, then subtracts the Colorado Sun's fraction. Multiplying the difference by 100 expresses it in percentage points. Those outlets were selected for continuous coverage, without looking at strategy returns. They keep publisher composition fixed, but national and Colorado stories can cover different conditions and topics; one Colorado publication does not represent all local US reporting. The measure captures relative wording and content mix in this sample. It does not establish false reporting, irrational readers, a deviation from fair security prices, or a causal market effect. The separate provider bar chart does not select trades. Using the signal alone makes the trading hypothesis easy to inspect, but does not make the signal valid or profitable.

The strategy rules and comparison family must be recorded before calculating their performance. They are retrospective educational hypotheses developed after the original study and earlier investment comparison, not an untouched historical discovery. Every declared rule must remain in the results, including losing rules; a favorable direction must not be chosen after seeing returns.

## Primary references and market endpoints

- [ProShares UPRO issuer page](https://www.proshares.com/our-etfs/leveraged-and-inverse/upro) and [September 28, 2026 summary prospectus](https://www.proshares.com/globalassets/proshares/prospectuses/upro_summary_prospectus.pdf).
- [ProShares SPXU issuer page](https://www.proshares.com/our-etfs/leveraged-and-inverse/spxu) and [September 28, 2026 summary prospectus](https://www.proshares.com/globalassets/proshares/prospectuses/spxu_summary_prospectus.pdf).
- [SEC Investor.gov, Updated Investor Bulletin: Leveraged and Inverse ETFs](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec), August 29, 2023.
- Yahoo chart endpoint templates: [UPRO](https://query1.finance.yahoo.com/v8/finance/chart/UPRO), [SPXU](https://query1.finance.yahoo.com/v8/finance/chart/SPXU). Exact dated requests, raw payloads, retrieval times and hashes belong in the acquisition manifest; a bare endpoint is not a frozen dataset or a guarantee of future endpoint access.

Issuer objectives and prospectuses were checked for this October 17, 2026 research extension. Current displayed fund performance is not evidence that any proposed headline strategy works. The two-day illustration is separate from all empirical tables.
