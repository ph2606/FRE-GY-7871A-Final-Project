# Compact statistical evidence for the original research question

These tables repackage the frozen observations and forecasts. No specification, threshold, sample or primary test family was selected again. Macroeconomic inputs use historical vintages; survey-target revisions and reconstructed media remain limitations, so chronological scoring is not proof of full historical deployability. Read alongside the report’s plain-language explanations and the executed notebook.

## Do media variables improve the same forecasts?

All three rows use the same 44 monthly outcomes, February 2023–September 2026. Loss is augmented-model squared error minus baseline squared error, in squared survey-index points. Negative favors adding media. Confidence intervals describe the average loss difference, not the RMSE difference. HAC(3) allows nearby loss errors to be related; nested models and the short sample limit the approximation. Intervals are pointwise, not simultaneous. Only the p-values are BH adjusted within the original three-test family.

| Added-media model / reference | RMSE reference → added | Mean loss difference [95% CI] | Raw p / BH q |
| --- | --- | --- | --- |
| M2_economic_media / M1_economic | 11.855 → 11.845 | -0.225 [-7.089, 6.640] | 0.949 / 0.949 |
| M3_economic_media_controls / M1_controls | 12.007 → 11.950 | -1.362 [-11.837, 9.113] | 0.799 / 0.949 |
| AR_macro_media / AR_macro | 4.662 → 4.617 | -0.414 [-2.276, 1.448] | 0.663 / 0.949 |

The point improvements are small, but failure to find an improvement is not proof of zero media influence. The intervals permit both better and worse prediction. No equivalence margin was registered, and these are not causal-effect bounds.

## How large is the fitted tone association?

A tone change of +0.1 could mean -0.2 becoming -0.1 on the classifier’s -1 to +1 scale. These are full 80-month fitted associations, not newly evaluated forecasts. All intervals use HAC(3); the copied coefficient q-values belong to the original pooled association-test family, distinct from the forecast-loss family.

| Model | Survey-point association for tone +0.1 [95% CI] |
| --- | --- |
| M2_economic_media | 1.660 [-1.139, 4.460] |
| M3_economic_media_controls | 1.854 [-0.857, 4.564] |
| AR_macro_media | 0.971 [-0.290, 2.231] |

The M2 rolling tone coefficient changes from -1.573 to +17.539 over 44 refits, with 37 positive estimates. Its sign and size are not stable enough to interpret as an invariant structural effect.

## Are three macroeconomic indicators enough?

On the 141 common historical test months, M1 has 8.403 times the squared prediction error of simply repeating the previous survey. The household-control version still has 6.681 times that error. These ratios answer a predictive comparison; neither an in-sample fit statistic nor a forecast residual identifies how much pessimism economics causally explains.

| Full-history fitted model | Months | Adjusted R-squared | Durbin–Watson | Ljung–Box(12) p |
| --- | --- | --- | --- | --- |
| M1_economic | 201 | 0.494 | 0.214 | 3.86e-227 |
| AR1 | 201 | 0.920 | 1.816 | 0.0497 |
| AR_macro | 201 | 0.921 | 1.794 | 0.131 |

Adjusted R-squared is a penalized descriptive fit statistic, not an out-of-sample or causal share explained. A Durbin–Watson value near two is compatible with little first-order residual correlation; M1’s very low value and Ljung–Box test show persistent errors. HAC standard errors alone do not repair that forecasting model.

| Specification, same 141 months | RMSE | Latest September gap |
| --- | --- | --- |
| AR1 | 4.302 | -4.39 |
| AR_macro | 4.593 | -4.64 |
| M1_GDP_yoy | 12.153 | -22.35 |
| M1_controls | 11.008 | -23.16 |
| M1_economic | 12.345 | -22.57 |
| M1_method_control | 7.975 | -3.99 |
| M1_rolling60 | 9.960 | -12.47 |
| M1_seasonality | 12.384 | -21.81 |
| Persistence | 4.259 | -3.60 |

The survey-mode ramp reduces the latest gap, but it also absorbs every coincident post-2024 change. Its improvement is not identification of a causal survey-mode effect. GDP definitions, annual sine/cosine terms and the 60-month window are sensitivities, not return-based or outcome-based choices of a winning model.

## Persistent levels and independent sensitivities

Historical sentiment has lag-one correlation 0.959. ADF p=0.910 and KPSS p=0.011 warn that simple level regressions may be unreliable. The tests have different nulls; breaks can resemble nonstationarity, so neither establishes the integration order.

| Exploratory change model, same 44 months | RMSE |
| --- | --- |
| D_macro | 4.3005 |
| D_macro_AR | 4.2227 |
| D_macro_AR_media | 4.2234 |
| D_macro_media | 4.2729 |

With lagged sentiment change, adding tone changes RMSE from 4.2227 to 4.2234. The separate two-contrast dynamic family has BH q=0.991. It was added after the original analysis and remains exploratory. Macroeconomic changes here are changes in the available information features, including revisions, not clean surprises.

| Alternative media measure / lag | Test months | RMSE | Gain versus its same-pool macro model |
| --- | --- | --- | --- |
| dictionary_lag1 | 44 | 12.003 | -1.25% |
| contextual_lag2 | 43 | 11.058 | 1.39% |
| contextual_lag3 | 42 | 10.759 | 1.19% |
| exclude_social_lag1 | 44 | 11.929 | -0.62% |
| national_only_lag1 | 44 | 12.019 | -1.38% |
| local_only_lag1 | 44 | 12.136 | -2.37% |
| price_frame_lag1 | 44 | 11.754 | 0.85% |
| post2022_contextual_lag1 | 9 | 4.576 | -1.09% |

Different lags have different matched test periods. They must not be ranked against one another as if they used identical samples. The post-2022 measurement check has only nine test months; it is weak evidence about a future deployment. These alternatives do not replace the original three contrasts.

## Separate headline, current conditions and expectations

September final values and economic-only forecasts below preserve the required survey distinctions. Prediction ranges based on past forecast errors are wide; neither a negative gap nor a component difference measures cognitive bias.

| September final outcome | Observed / prediction | Gap | Past-error 95% range |
| --- | --- | --- | --- |
| current_conditions | 50.9 / 76.95 | -26.05 | [43.13, 110.76] |
| expectations | 46.3 / 66.63 | -20.33 | [43.37, 89.89] |
| sentiment | 48.1 / 70.67 | -22.57 | [44.13, 97.21] |

## Prospective causal identification

The assignment permits observational evidence plus a detailed stronger-design proposal. The [prospective plan](CAUSAL_POWER_PLAN.md) specifies the estimand, truthful stimuli, outcome scoring, analysis, missingness, multiplicity and a planning sample size. No participants or experimental effects are claimed.

Rebuild these tables with `python -m src.rubric_evidence`. All source hashes and planning assumptions are in `outputs/tables/rubric_evidence_summary.json`. Detailed datasets remain local under the no-data-commit policy.
