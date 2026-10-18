# A simple, bias-proxy-only experiment

Think of the signal as a comparison between two thermometers. One measures how often national headlines sound negative; the other does the same for one local newspaper. Their difference can change even when both report the truth. We call it a **relative wording gap**, not a measurement of lies, unfairness or readers' beliefs.

This extension fixes its rules before calculating its new investment returns. The earlier economic, media and investment findings were already known. The three-outlet roster was selected because all three have observations in every completed month, rather than because of any new strategy's profit. This is a retrospective research design, not an untouched historical or live test.

## The exact recipe

Use only final-eligible records in `data/processed/media_scores.csv`, with exact `source` labels **Reuters**, **NPR** and **Colorado Sun**. Retain the existing relevance rules and classifier classes; do not add a new geography, industry, market-price, survey or macroeconomic filter. Exclude incomplete October 2026. The fixed data grid is January 2020 through September 2026.

For each outlet and month, count titles whose `contextual_class` equals `negative`, then divide by all that outlet's retained titles, including neutral and positive titles. Give Reuters and NPR equal weight, regardless of their title counts:

`wording gap B = 100 × [(Reuters negative share + NPR negative share) / 2 − Colorado Sun negative share]`

The unit is percentage points. A gap of +20 means the average national share is 20 percentage points above the Colorado Sun share. It does not mean the national articles are 20% false. Colorado Sun is a convenience comparison, not an unbiased standard or a representative sample of all local news. This is a different sample and measure from the six-event provider bar graph.

An absent outlet produces a missing gap; it never becomes zero or a smaller substitute roster. Each month retains outlet title counts, outlet negative shares, total selected titles, source count and a complete-roster flag. The model has not been independently human-validated for this use.

## When a decision is possible

At each first-calendar-day origin, use the last completed month's gap. Compare it with the median of the **12 calendar months before that measured month**, excluding the measured month itself. Also compare it with the immediately preceding month's gap. No later text, market price, economic indicator or survey target enters the decision.

For the February 1, 2021 origin, January 2021 supplies the current gap; January–December 2020 supplies its baseline. January 2021 cannot be an origin under this recipe because its December 2020 gap lacks a full preceding 12-month baseline. The frozen origin window is therefore **February 2021–September 2026: 68 decisions**. It uses current signal months January 2021–August 2026. Later completed September text is outside that origin window, and incomplete October text is excluded entirely.

Every required calendar month must be present. Never forward-fill or skip a missing month. Missing current or baseline data means BIL. Differences with absolute size at most `1e-10` percentage points count as equality. Equality means BIL. A news title's conservative `available_at` is the next New York midnight; first-day origins refer to information available by that day's end. Historic index membership and original title wording are unavailable, so the content remains a retrospectively reconstructed availability proxy. Execution and leveraged-fund accounting are specified separately in the investment protocol.

## Three fixed ideas, with no search for winning settings

| Rule | If the gap is above its usual level | If the gap is below its usual level | Otherwise |
|---|---|---|---|
| `Fade_gap` | UPRO | SPXU | BIL |
| `Follow_gap` | SPXU | UPRO | BIL |
| `Wait_turn` | UPRO only when the gap has also fallen since last month | SPXU only when the gap has also risen since last month | BIL |

UPRO targets three times the S&P 500's **daily** move; SPXU targets three times its inverse **daily** move, before fees and expenses. [UPRO issuer](https://www.proshares.com/our-etfs/leveraged-and-inverse/upro), [SPXU issuer](https://www.proshares.com/our-etfs/leveraged-and-inverse/spxu). BIL is a short Treasury-bill ETF. These rules are hypotheses about what investors might do, not deductions from a proven media effect. The opposite Fade and Follow ideas are both retained; there is no return-based choice between them. Daily leverage can produce large losses and a multi-day result very different from simply multiplying an index return by three.

## What is actually available

All counts below concern the frozen, final-eligible title data before calculating the new strategies' returns.

| Selected outlet | Complete months | Titles, Jan 2020–Sep 2026 | Minimum / median / maximum titles per month |
|---|---:|---:|---:|
| Reuters | 81 / 81 | 795 | 4 / 10 / 12 |
| NPR | 81 / 81 | 751 | 2 / 11 / 12 |
| Colorado Sun | 81 / 81 | 377 | 1 / 4 / 12 |

There are **1,923 selected titles** across the full 81-month grid. The initial January–December 2020 baseline contains 190 titles: Reuters 99, NPR 68 and Colorado Sun 23. The 68 current signal months contain **1,708 titles**: Reuters 688, NPR 671 and Colorado Sun 349. Every one of those months has all three outlets. In that signal window, the minimum monthly counts are 4, 3 and 1 respectively; the corresponding medians are 10, 11 and 5. This preserves outlet membership, not equal sample precision.

For comparison, the earlier all-national/all-local series changes which outlets are present: only 46 of those 68 signal months have all six news outlets. That coverage problem motivates the new fixed roster. The new measure does not alter the earlier corpus, annotation sample, provider bar or forecast results.

## What this cannot tell us

A one-title local month can move from 0% to 100% negative when one label changes. Equal outlet weights do not remove this noise. National and local headlines also cover different places, topics and events. Genuine differences in economic experience, classifier error and selected search results can create a wording gap without distorted reporting.

Google ranking, saved-title wording and the later language model are retrospective; counts do not measure everything published or what investors read. The pinned CardiffNLP representation dates from 2022, so earlier scores use a model that did not yet exist then; see the [original codebook](MEDIA_CODEBOOK.md). Original geographic eligibility is unchanged: among the 1,923 selected titles, 941 have no explicit US geography in their wording. These remain eligible under the original conservative screen, rather than being reclassified as known US stories. No factual-error rate, causal media effect or public exposure is inferred. More aggressive leverage increases financial risk; it does not improve the quality of the evidence.

The implementation is pure: `monthly_spread(scores)` constructs the monthly comparison; `origin_signals(monthly, origins)` returns `Fade_gap`, `Follow_gap` and `Wait_turn` as fund symbols. It does not download prices, fit parameters, calculate returns or select a winning strategy.
