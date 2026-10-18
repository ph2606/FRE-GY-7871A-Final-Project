# Final-project requirements audit

October 18 integration: the main report now adds explicit uncertainty, class/source AI concordance, a separate external human-consensus transfer benchmark, factual spot checks, a powered causal proposal and a clearly separated Part B manifesto. The user explicitly instructed integrating Part B and disregarding the report's original page cap. The 6-8 minute presentation target remains. The two independent human annotators on 300 target-corpus items are still missing; external published labels do not satisfy that criterion. Grading weights and the original page requirement below are retained as the assignment states them, not silently reinterpreted.

Source of requirements: `Final_Project_Applications_in_Finance_Oct_2026.pdf`, five pages, read in full before implementation. The supplied workbook was inspected separately. This is a checklist for review, not a claim that every item is already satisfied.

## Required questions and evidence locations

| Required research question | Required evidence in final deliverables |
| --- | --- |
| 1. How can coverage/social bias be measured? | Coding guide with explicit benchmarks; tone, salience, framing, factual calibration and political attribution; matched-event/source comparisons; distinction between unfavorable facts and emotional language. |
| 2. What impact might depress Michigan sentiment? | Lagged association and incremental forecast tests, explicit reverse causality/common shocks, and the feasible causal-design proposal. Do not translate supply or engagement into respondent exposure. |
| 3. How much can unemployment, inflation and GDP explain? | Economic-only chronological forecasts, error metrics, uncertainty intervals and sentiment gaps; a simple benchmark; no causal “share explained” from an in-sample fit. |
| 4. Which perceptual mechanisms are measurable? | Price-level versus inflation-rate framing and selective topic attention are textual measures. Negativity in wording is measurable. Individual availability, confirmation bias and anchoring require exposure, recall, beliefs or experiments unavailable in a text corpus. |
| 5. Do media measures improve predictions? | Same-date/target comparison of economic-only, economic-plus-media and full-control models on the same chronological holdout; report overlap size and missingness. If historical media support is inadequate, describe the failed identification/power and leave improvement unestablished. |
| 6. What would contradict media bias? | Null/inconsistent matched-event asymmetries; no out-of-sample media gain; gap shrinking with household burdens or method controls; factual unfavorable reporting; subgroup patterns inconsistent with claimed exposure. |

## Rubric checklist

| Component | Weight | Must be visible in the report/package |
| --- | ---: | --- |
| Economic measurement and timing | 20% | Monthly history preferably from 2010; headline/current/expectations separately where available; official SA U-3; headline PCE YoY calculated from price index; quarterly real GDP with annualization stated; observation dates, release dates, revisions and cutoff. No artificial monthly GDP interpolation. Household controls and cumulative prices. |
| Corpus and validated AI | 25% | Documented national/local news and one social platform; queries, sampling, timestamps, unit of text, geography/audience, duplicates/reposts/ads/bot heuristics, failures and missingness. At least four coding dimensions with benchmarks. Two independent human annotators on at least 300 stratified items, agreement/adjudication and class/source performance. Dictionary comparison, pinned model/prompts/evidence, name/source invariance. |
| Statistics and causal reasoning | 30% | Three models, chronological forecasts, prediction intervals, stability, autocorrelation/seasonality/lags/multiple tests; observational versus causal claims; feasible causal proposal if exposure data unavailable. Explain transportability to the national Michigan index. |
| Reproducibility/dashboard | 15% | Provenance, download/transform scripts, dependency pins, executed notebook, prompts and labeling guide; updateable dashboard with observed/model sentiment, interval/gap, media dimensions, releases/events, composition/missingness and model diagnostics. |
| Communication/ethics | 10% | 10–12 page report, 6–8 minute presentation and practical financial implication; source attribution; findings versus hypotheses; privacy/licensing/required human-research approval; clear cutoff and prospective plan. |

Demographic, geographic and political splits are required only **where data permit**. Missing respondent exposure, identification or subgroup variables must not be inferred from usernames or publisher location. Michigan mode comparability and 2026 methodological reports must be discussed even if subgroup microdata are unavailable.

## Material gaps that cannot be filled with invented results

1. **Human validation:** two real, independent annotators must label at least 300 actual items. A prepared packet, blank forms, AI labels or AI-agent agreement do not fulfill this requirement. Until completed, label performance as unvalidated; report human agreement and accuracy as pending. This is a direct risk in the 25% corpus criterion, not permission to fabricate work or an automatic 25-point deduction.
2. **Historical information vintages:** release-date gating alone does not make a current-vintage workbook an as-of backtest. If real-time vintages cannot be reconstructed, explicitly call historical results retrospective current-vintage estimates, and limit forecasting claims accordingly.
3. **Short media overlap:** thousands of texts do not produce thousands of independent monthly sentiment outcomes. Model comparison is limited by the number of overlapping months. Do not infer causal impact or validated forecasting improvement from a one- or two-month monitor.
4. **Full election outcome:** work as of October 13 precedes the November election. Monitoring can end at the cutoff, with a documented future update plan. There is no observed election effect to report.

## Supplied workbook audit

`Sheet1` contains four independent date/value column pairs separated by blank columns. Row position is not a common observation date. Read and join each pair by its own date.

| Series label | Nonmissing observations | Span | Required treatment |
| --- | ---: | --- | --- |
| Unemployment | 584 | Jan 1978–Sep 2026 | Oct 2025 is missing, reflecting an official collection gap; preserve missingness. |
| Consumer Sentiment | 586 | Jan 1978–Oct 2026 | Oct 46.3 is a preliminary estimate already released Oct 9; month-end is a period label, not publication time. |
| PCE YoY | 584 | Jan 1978–Aug 2026 | Latest workbook value 3.00759 conflicts with official **headline** August YoY 3.4%; resembles official core 3.0. Verify index/definition and recompute headline. |
| Real GDP QoQ Annualized | 195 | Q1 1978–Q3 2026 | Q3 value 3.7 is unavailable at the Oct 13 cutoff; quarantine. Q2 latest 2.2 was released Sep 30 and earlier Q2 vintages were 1.5. |

These counts describe the supplied file, not the cleaned model sample. No duplicate dates were found within each pair. No release metadata or source links are supplied in the workbook; provenance cannot be inferred solely from numerical agreement. Verified official sources and the applicable publication dates are in [sources.md](sources.md).

## Suggested 12-page allocation

1: question, cutoff and findings; 2: official measures/workbook audit; 3: information sets and economic forecasting; 4: household/model sensitivity; 5: corpus and sampling; 6: coding and benchmarks; 7: validation/invariance; 8: media association and model comparison; 9: mechanisms and falsification; 10: causal design/method comparability; 11: dashboard/financial implication/update plan; 12: limitations and references. Layout must follow actual evidence, not force nonexistent results into this plan.
