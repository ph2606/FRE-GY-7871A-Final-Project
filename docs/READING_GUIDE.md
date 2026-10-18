# Start here: what this project is saying

The central question is simple: **why can people feel bad about the economy when some national numbers look better?** The project checks everyday household costs, news wording, and weaknesses in the data or prediction method. Its evidence does not prove that misleading news caused the national survey to fall.

## The two different gaps

**The survey gap compares a survey with a prediction.** If the survey score is 60 and the prediction is 70, the gap is 60 - 70 = -10 points. This says the model expected too much optimism. It does not tell us that ten percent of people are biased.

**The news gap compares wording across outlets.** Suppose Reuters has 40% negative titles, NPR has 60%, and Colorado Sun has 30%. Give the two national outlets equal weight: (40 + 60) / 2 = 50%. Then subtract the local outlet: 50 - 30 = +20 percentage points. The news gap is +20. Different real events or audiences can produce this difference. It is a proposed framing indicator, not a fact-check or a political label.

The trading rules use only the second gap and its earlier monthly values. They do not use the Michigan survey gap, economic releases, or stock-price trends to choose a fund. The separate CNBC/Fox provider graph uses another, much smaller matched-report sample; its bars do not choose the trades.

## A worked trading decision

These are invented teaching numbers, not extra research observations. Suppose the most recently completed month's news gap is +20, its usual level over the earlier twelve months is +10, and last month's value was +25. The gap is unusually high and has started falling.

| Idea | Choice in this example | Reason |
| --- | --- | --- |
| Fade the gap | UPRO, the fund targeting 3x the market's daily rise | Bet against unusually negative national emphasis |
| Follow the gap | SPXU, the fund targeting 3x the opposite daily move | Treat negative emphasis as a warning |
| Wait for a turn | UPRO | Negative emphasis is still unusual but has started easing |

The usual level is the **median**: sort the earlier twelve monthly scores and average the middle two. The current measured month is not allowed inside that reference. The strategy waits until the following month to trade, so it cannot earn a return that happened before the decision. These are reconstructed historical decisions, because today's searches and a later language model do not recover a fully working system from every earlier date.

## How to read the investment results

Every line starts with the same $10,000 before trading costs. The ending value answers, “How much money was left?” **Annual compound growth** is the steady yearly rate that would connect the starting and ending values; the real path was uneven. It is not the arithmetic average of daily gains multiplied by a year.

**Worst fall**, also called drawdown, measures a drop from an earlier high. An account that climbs from $10,000 to $20,000 and then falls to $8,000 has a 60% drawdown: (20,000 - 8,000) / 20,000. Its loss compared with the original $10,000 is only 20%. Those are different questions.

Two tested news rules ended with more than $10,000, but all three grew less than simply holding the ordinary S&P 500 fund and suffered deeper percentage falls. More aggressive exposure did not establish a better trading signal. A larger profit from always holding a 3x rising-market fund would also not prove that the news helped.

UPRO and SPXU target **daily** moves. If the index rises 1% in a day, their targets are approximately +3% and -3%. Holding one for a month does not promise three times the month's return. See the [two-day example](LEVERAGED_FUNDS_EXPLAINED.md), where the market finishes flat while both idealized 3x funds lose money.

## Small glossary

| Word | Meaning here |
| --- | --- |
| Consumer sentiment | People's outlook for money, business conditions and purchases, measured by a survey score |
| Inflation | How quickly prices rise; slower inflation can still leave prices much higher than before |
| GDP | Gross domestic product: the country's economic output |
| Forecast / model | A prediction / a mathematical rule that learns relationships from earlier data |
| Benchmark | A simple comparison, such as repeating last month's survey or just holding a stock fund |
| RMSE | A forecast-mistake score: square mistakes, average them, then take the square root; lower is better |
| Uncertainty range | A plausible spread of outcomes, not a guarantee that the next answer will be inside it |
| Tone | How positive or negative wording sounds; it does not establish truth |
| Framing | Which aspect of a story is emphasized |
| Percentage point | A difference between percentages: 40% minus 30% is ten percentage points |
| ETF | Exchange-traded fund: a bundle of investments that can be bought like a stock |
| S&P 500 / SPY | An index of roughly 500 large US companies / an ordinary fund tracking that market |
| Treasury bill / BIL | Short-term US government debt / a fund holding very short Treasury bills |
| Leverage | Amplified market exposure, which can amplify losses as well as gains |
| Dividend / split | A cash distribution to investors / a change in share count and per-share price that alone does not change wealth |
| Trading cost | A charge for buying or selling; the test assumes $1 per $1,000 traded on each leg |
| Retrospective test | A simulation of past decisions reconstructed later, with limitations a live future test would not share |
| Human validation | People independently checking labels; the assignment's two-person requirement remains unmet |

The extended report first presents the empirical study, then Part B's manifesto and evidence review, followed by trading appendices. The presentation covers both parts within the original 6–8 minute target. A manifesto states values and proposals; it is not a new finding from the headline dataset. Fertility measures births, not intelligence; short-term test performance and IQ are different. The notebook preserves calculations, all strategies and benchmarks, uncertainty checks and the external human-consensus stress test. The target-corpus two-human requirement remains incomplete.

## Reading the 100-country bar charts

The five charts continue from rank 1 through rank 100, highest to lowest. Read down the left panel, then down the right; each chart contains 20 entries. The common horizontal scale starts at zero. A value of 40 means 40 births in a year per 1,000 people, or about 4%; it does not mean 40 children per woman. These 2023 World Bank figures cover countries and economies, including some territories, and exclude world/regional/income aggregates. Many lower-birth-rate economies lie outside the highest 100. The standalone five-page PDF contains all charts at full size.
