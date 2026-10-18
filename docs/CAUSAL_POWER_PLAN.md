# Prospective framing experiment: an operational plan

This addendum makes the assignment's permitted **observational study plus stronger-design proposal** concrete. It supplements [the causal reasoning](causal_design.md); it reports no recruited participants, human responses or experimental effects. The existing monthly analysis estimates associations and predictive differences. Its wide uncertainty cannot establish that media effects are absent.

## Target effect, treatments and assignment

The primary estimand is the **intention-to-treat mean difference in next-day sentiment-related responses between price-level and annual-inflation framing**, among the adults recruited into the future study. Intention-to-treat means comparing assigned groups even if someone does not read carefully. It is not an effect on the official Michigan index or all American adults.

After required review and consent, recruit U.S. adults from a probability-based or carefully benchmarked panel, with one participant per household. Assign 1:1:1 within prespecified income and political-affiliation blocks. Use three income bands (below $50,000; $50,000–$99,999; $100,000 or more) and three affiliation groups (Democratic, Republican, other/none), with an explicit missing/declined-information block where needed. Archive the assignment algorithm and seed before data collection. Measure baseline outcomes, financial pressure, age, affiliation and news use before assignment.

Every arm receives the **same factual body, numbers, release date, source, font and layout**. Only its headline changes. Candidate ten-word headlines are:

| Arm | Headline |
| --- | --- |
| Balanced reference | Consumer prices: comparing changes over twelve months and three years. |
| Price-level emphasis | Consumer prices remain 8.8% above their level three years ago. |
| Annual-rate emphasis | Consumer prices rose 3.4% over the past twelve completed months. |

The common body identifies the headline PCE price index, August 2026 reference month and September 30 publication, and gives **both** the annual and cumulative changes. These numbers come from already frozen observations: 3.4190% over twelve months and 8.7933% since August 2023, rounded to 3.4% and 8.8%. They do not claim that every household faced the same price change. The [BEA release](https://www.bea.gov/news/2026/personal-income-and-outlays-august-2026) and the project's within-vintage index calculation are the references. Before any recruitment, freeze the full body and pilot reading difficulty without examining treatment effects. The competing headlines are truthful; they do not alter the underlying information or invent a decline in prices.

## Primary response and analysis

Use the same three questions before exposure and at the next-day follow-up: compared with today, over the next twelve months, how will (1) the household's finances, (2) U.S. business conditions, and (3) conditions for large household purchases change? Responses are much worse, somewhat worse, unchanged, somewhat better, much better, scored 0, 25, 50, 75, 100. The primary response is their equally weighted mean. A don't-know or missing item makes that follow-up composite missing. Higher means more optimism. This is a **new research composite**, not Michigan's questionnaire, weighting or published index.

The primary two-sided test is price-level minus annual-rate framing at alpha 0.05. Estimate ANCOVA:

`next_day_score = intercept + tau_L*assigned_level + tau_R*assigned_rate + beta*baseline_score + randomization_block_effects + error`.

Report `tau_L - tau_R`, its 95% interval and HC2 robust uncertainty, retaining everyone in their assigned arm. Show unadjusted group means as well. Baseline adjustment can improve precision; the power plan below assumes no such gain. No exclusion depends on post-treatment comprehension, beliefs or whether someone agreed with the facts. Record comprehension as a manipulation check, not a filter for the main estimate.

Register six secondary contrasts as one Holm-adjusted family: level versus balanced and rate versus balanced on the next-day primary response; level versus rate on the immediate and one-week response; and level versus rate on next-day numerical inflation beliefs and factual recall. Freeze question wording and recall scoring before recruitment. Component outcomes, income/affiliation interactions, confidence and spending intentions remain explicitly exploratory unless a separate future protocol makes them primary. A recall shift alongside a response shift does not by itself identify causal mediation or confirmation bias.

## Power: planning assumptions, never observed effects

Choose a standardized target difference of **0.25 individual-level standard deviation**, a two-sided 5% test and 80% power. A five-point difference on the proposed 0–100 response with an assumed standard deviation of twenty points is one illustration of that target, **not an estimate from participants or the monthly Michigan series**. Aggregate time-series variability is not an individual-response standard deviation.

The usual equal-arm normal approximation is `n = 2*(z_(0.975)+z_(0.80))^2 / d^2`, rounded up. A finite-sample noncentral-t calculation then finds the smallest equal-arm complete-outcome count meeting the target. It gives **253 complete responses per arm** at d=0.25. Allowing a planning 20% missing-outcome rate requires **317 randomized per arm, 951 in three arms**. The two arms in the primary contrast determine its power; the balanced arm supports secondary comparisons. Attrition inflation is a planning expectation, not a guarantee of adequate retained outcomes.

| Standardized target | Complete outcomes per arm | Randomized per arm at 20% attrition | Total for three arms |
| --- | ---: | ---: | ---: |
| 0.20 | 394 | 493 | 1,479 |
| **0.25, primary planning target** | **253** | **317** | **951** |
| 0.30 | 176 | 220 | 660 |

These are power sensitivities, not alternative effects to select after the experiment. The calculation assumes independent participants, equal allocation and an approximately continuous equal-variance response; small clusters, different variances, attrition imbalance and weak response reliability would require revising the future design before collection. It does not include a promised ANCOVA or weighting benefit. Reproduce the calculations with `python -m src.rubric_evidence`; `outputs/tables/rubric_power_plan.csv` preserves assumptions and achieved finite-t power. No study is being run under this proposal.

## Missingness, identification and national transport

Report assigned and observed counts and dropout by arm. The intention-to-treat estimand includes every assigned participant; missing follow-up outcomes prevent direct observation of that estimand. Prespecify multiple imputation using treatment, baseline response, blocks and measured pre-treatment predictors under a missing-at-random assumption. Report complete-case estimates separately and a sensitivity analysis shifting missing scores by -0.5 to +0.5 assumed standard deviation by arm, clipped to the score's bounds. Neither random assignment nor imputation proves the missingness assumption. Report whether conclusions change rather than selecting a favorable case.

The observational difficulty can be summarized as `economic shocks → headlines` and `economic shocks → sentiment`; prior beliefs and party influence both `chosen exposure` and `sentiment`, while audience demand can influence publishers. Actual exposure is not observed in the monthly title panel. Random assignment breaks confounding of **assigned framing** within the new experiment; it does not make natural media consumption random. Measure sharing and contamination, limit demand cues, and provide the balanced fact sheet at debriefing.

A null estimate would be informative only if its interval excludes a prespecified materially important effect. A wide interval would remain inconclusive. A positive experimental effect would still require population exposure data, representative sampling or defensible reweighting, measured effect modifiers, overlap, repeated-exposure and spillover assumptions, and comparable outcomes before any national attribution. Do not multiply an experimental response difference by headline counts to claim a change in Michigan sentiment. The original 300-item human-labeling requirement is a separate unfinished validation task; this proposed experiment does not replace it.
