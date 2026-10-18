"""Compact statistical evidence from frozen outputs; no model refitting or search.

The only new inference is a confidence interval for each existing HAC loss
contrast. Planning sample sizes are hypothetical design calculations, never
participant observations. Existing predictive-test families remain unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, nct, t
import statsmodels.api as sm

from .economics import ROOT, bh_adjust, sha256, write_json

TABLES = ROOT / 'outputs/tables'
CONTRASTS = (
    ('M2_economic_media', 'M1_economic'),
    ('M3_economic_media_controls', 'M1_controls'),
    ('AR_macro_media', 'AR_macro'),
)


def loss_contrasts(forecasts: pd.DataFrame, maxlags: int = 3) -> pd.DataFrame:
    """Reproduce the existing paired loss tests, adding HAC mean-loss intervals.

    Refuse different or missing months instead of silently changing a pair's
    evaluation sample. Negative loss differences favor the augmented model.
    """
    frame = forecasts.copy()
    if 'target' in frame:
        frame = frame.loc[frame.target.eq('sentiment')]
    frame['month'] = pd.to_datetime(frame.month)
    if frame.duplicated(['month', 'model']).any():
        raise ValueError('Repeated model/month forecasts')
    rows = []
    for augmented, baseline in CONTRASTS:
        series = []
        for model in (augmented, baseline):
            values = frame.loc[frame.model.eq(model)].set_index('month').error.sort_index()
            if values.empty or not np.isfinite(values).all():
                raise ValueError(f'Missing/nonfinite forecast errors: {model}')
            series.append(values)
        extra, reference = series
        if not extra.index.equals(reference.index):
            raise ValueError('Paired models must have identical evaluation months')
        if not extra.index.equals(pd.date_range(extra.index.min(), extra.index.max(), freq='MS')):
            raise ValueError('Evaluation months must form the exact monthly grid')
        difference = extra.to_numpy() ** 2 - reference.to_numpy() ** 2
        fit = sm.OLS(difference, np.ones((len(difference), 1))).fit(
            cov_type='HAC', cov_kwds={'maxlags': maxlags})
        lower, upper = np.asarray(fit.conf_int(alpha=.05))[0]
        base_rmse = float(np.sqrt(np.mean(reference.to_numpy() ** 2)))
        extra_rmse = float(np.sqrt(np.mean(extra.to_numpy() ** 2)))
        rows.append({'augmented': augmented, 'baseline': baseline, 'n': len(extra),
                     'start': str(extra.index.min().date()), 'end': str(extra.index.max().date()),
                     'baseline_rmse': base_rmse, 'augmented_rmse': extra_rmse,
                     'rmse_gain_points': base_rmse-extra_rmse,
                     'mean_squared_loss_difference': float(difference.mean()),
                     'hac_se_mean_loss_difference': float(fit.bse[0]),
                     'loss_difference_lower_95': float(lower),
                     'loss_difference_upper_95': float(upper),
                     'hac_pvalue_two_sided': float(fit.pvalues[0]), 'hac_maxlags': maxlags,
                     'units': 'mean squared survey-index points; negative favors augmented model'})
    result = pd.DataFrame(rows)
    result['bh_qvalue_existing_three_test_family'] = bh_adjust(result.hac_pvalue_two_sided.to_numpy())
    return result


def power_plan(effect_sd: float, alpha: float = .05, power: float = .80,
               attrition: float = .20, arms: int = 3) -> dict:
    """Equal-arm prospective sample size for one two-sided contrast.

    A normal approximation initializes a finite-sample noncentral-t calculation.
    No ANCOVA efficiency gain is assumed. The third arm supports secondary
    comparisons; the primary contrast compares two arms. Complete-outcome
    counts are inflated for the planning attrition rate.
    """
    if (not np.isfinite([effect_sd, alpha, power, attrition, arms]).all() or
            effect_sd <= 0 or not 0 < alpha < 1 or not .5 < power < 1 or
            not 0 <= attrition < 1 or arms < 2 or int(arms) != arms):
        raise ValueError('Invalid prospective design assumptions')
    approximation = int(np.ceil(2*(norm.ppf(1-alpha/2)+norm.ppf(power))**2/effect_sd**2))
    observed = max(2, approximation)
    def achieved(n):
        df = 2*n-2
        critical = t.ppf(1-alpha/2, df)
        noncentrality = effect_sd*np.sqrt(n/2)
        return float(nct.sf(critical, df, noncentrality) + nct.cdf(-critical, df, noncentrality))
    while achieved(observed) < power:
        observed += 1
    while observed > 2 and achieved(observed-1) >= power:
        observed -= 1
    assigned = int(np.ceil(observed/(1-attrition)))
    return {'standardized_effect_sd': effect_sd, 'two_sided_alpha': alpha, 'target_power': power,
            'assumed_attrition': attrition, 'normal_approximation_complete_per_arm': approximation,
            'complete_outcomes_per_arm': observed, 'finite_t_power_at_complete_n': achieved(observed),
            'randomized_per_arm': assigned, 'arms': arms, 'randomized_total': arms*assigned,
            'status': 'prospective planning assumptions, not participant data'}


def markdown_table(headers, rows):
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join(['| ' + ' | '.join(map(cell, headers)) + ' |',
                      '| ' + ' | '.join(['---']*len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(cell, row)) + ' |' for row in rows])


def build(root: Path = ROOT) -> dict:
    tables = root / 'outputs/tables'
    sources = {name: tables/name for name in [
        'media_forecasts.csv', 'predictive_loss_tests.csv', 'association_coefficients.csv',
        'model_metrics.csv', 'model_diagnostics.csv', 'forecasts.csv',
        'media_sensitivity_metrics.csv', 'media_rolling_coefficients.csv', 'dynamics_summary.json']}
    sources['monthly_dataset.csv'] = root/'data/processed/monthly_dataset.csv'
    hashes = {str(path.relative_to(root)): sha256(path) for path in sources.values()}
    loss = loss_contrasts(pd.read_csv(sources['media_forecasts.csv']))
    original = pd.read_csv(sources['predictive_loss_tests.csv'])
    check = loss.merge(original, on=['augmented','baseline'], validate='one_to_one', suffixes=('', '_original'))
    if not (np.array_equal(check.n, check.n_original) and
            np.allclose(check.hac_pvalue_two_sided, check.hac_pvalue_two_sided_original, atol=1e-12) and
            np.allclose(check.bh_qvalue_existing_three_test_family, check.bh_qvalue, atol=1e-12)):
        raise ValueError('Frozen primary tests changed; investigate before publishing')
    metrics = pd.read_csv(sources['model_metrics.csv'])
    diagnostics = pd.read_csv(sources['model_diagnostics.csv'])
    forecasts = pd.read_csv(sources['forecasts.csv'])
    coefficients = pd.read_csv(sources['association_coefficients.csv'])
    association = coefficients.loc[coefficients['sample'].eq('common_media_history') &
                                   coefficients.variable.eq('media_tone_lag1')].copy()
    for original_name, new_name in [('coefficient','effect_for_tone_plus_0_1'),
                                    ('lower_95','effect_lower_95'),('upper_95','effect_upper_95')]:
        association[new_name] = .1*association[original_name]
    association = association.merge(diagnostics[['sample','model','n']], on=['sample','model'], validate='one_to_one')
    association['interpretation'] = 'Full-history fitted association; tone shift 0.1; HAC(3); not an OOS effect or causality'
    components = forecasts.loc[forecasts.model.eq('M1_economic')].sort_values('month').groupby('target').tail(1)
    components = components[['target','month','observed','prediction','gap','lower_95','upper_95',
                             'empirical_lower_95','empirical_upper_95','training_n']].sort_values('target')
    historical = metrics.loc[metrics['sample'].eq('common_historical_oos') & metrics.target.eq('sentiment')].copy()
    base_rmse = float(historical.loc[historical.model.eq('M1_economic'), 'rmse'].iloc[0])
    historical['rmse_gain_percent_vs_M1'] = 100*(1-historical.rmse/base_rmse)
    latest = forecasts.loc[forecasts.target.eq('sentiment')].sort_values('month').groupby('model').tail(1)
    economic_sensitivity = historical.merge(latest[['model','gap']], on='model', validate='one_to_one')
    economic_sensitivity = economic_sensitivity[['model','n','start','end','rmse','mae',
                                                 'rmse_gain_percent_vs_M1','gap']]
    economic_sensitivity = economic_sensitivity.rename(columns={'gap':'latest_september_gap'})
    media_sensitivity = pd.read_csv(sources['media_sensitivity_metrics.csv'])
    media_sensitivity = media_sensitivity.loc[media_sensitivity.model.eq('M2_sensitivity')].copy()
    dynamic_summary = json.loads(sources['dynamics_summary.json'].read_text(encoding='utf-8'))
    dynamic = pd.DataFrame(dynamic_summary['metrics'])
    dynamic['status'] = dynamic_summary['status']
    model_diagnostics = diagnostics.loc[
        diagnostics['sample'].eq('historical_2010_2026') &
        diagnostics.model.isin(['M1_economic','AR1','AR_macro'])].copy()
    skill_rows = []
    for sample in ['common_historical_oos','common_media_oos']:
        group = metrics.loc[metrics['sample'].eq(sample) & metrics.target.eq('sentiment')]
        persistence = group.loc[group.model.eq('Persistence')].iloc[0]
        for row in group.itertuples():
            if row.n != persistence.n or row.start != persistence.start or row.end != persistence.end:
                raise ValueError('Forecast skill comparisons require identical periods')
            ratio = float((row.rmse/persistence.rmse)**2)
            skill_rows.append({'sample': sample, 'model': row.model, 'n': row.n,
                               'start': row.start, 'end': row.end, 'rmse': row.rmse,
                               'mse_ratio_to_persistence': ratio,
                               'oos_skill_vs_persistence': 1-ratio,
                               'interpretation': 'Predictive skill against repeat-last-month; not causal explained variance'})
    skill = pd.DataFrame(skill_rows)
    rolling = pd.read_csv(sources['media_rolling_coefficients.csv'])
    rolling = rolling.loc[rolling.model.eq('M2_economic_media') & rolling.variable.eq('media_tone_lag1')]
    m1_ratio = float(skill.loc[skill['sample'].eq('common_historical_oos') & skill.model.eq('M1_economic'), 'mse_ratio_to_persistence'].iloc[0])
    controls_ratio = float(skill.loc[skill['sample'].eq('common_historical_oos') & skill.model.eq('M1_controls'), 'mse_ratio_to_persistence'].iloc[0])
    dynamic_lookup = dynamic.set_index('model')
    dynamic_q = max(row['bh_qvalue_within_bandwidth_family'] for row in dynamic_summary['dynamic_loss_tests_hac3'])
    planning = pd.DataFrame([power_plan(effect) for effect in [.20,.25,.30]])
    output_frames = {'loss_contrasts': loss, 'tone_associations': association,
                     'survey_components': components, 'economic_sensitivities': economic_sensitivity,
                     'media_sensitivities': media_sensitivity, 'dynamic_sensitivities': dynamic,
                     'forecast_skill': skill, 'model_diagnostics': model_diagnostics,
                     'power_plan': planning}
    for name, frame in output_frames.items():
        frame.to_csv(tables/f'rubric_{name}.csv', index=False)
    summary = {'status': 'Evidence packaging only; frozen forecasts and original test families unchanged',
               'input_sha256': hashes, 'script_sha256': sha256(Path(__file__)),
               'existing_loss_test_family_size': 3,
               'loss_interpretation': 'Negative mean squared loss difference favors media; intervals are HAC(3) approximations, not evidence of equivalence',
               'prospective_primary_power_plan': power_plan(.25),
               'stationarity_diagnostics': dynamic_summary['historical_sentiment_diagnostics'],
               'dynamic_loss_tests_hac3': dynamic_summary['dynamic_loss_tests_hac3'],
               'artifacts': [f'outputs/tables/rubric_{name}.csv' for name in output_frames]}
    write_json(tables/'rubric_evidence_summary.json', summary)
    def f(value, places=3): return f'{float(value):.{places}f}'
    text = ['# Compact statistical evidence for the original research question',
            'These tables repackage the frozen observations and forecasts. No specification, threshold, sample or primary test family was selected again. Macroeconomic inputs use historical vintages; survey-target revisions and reconstructed media remain limitations, so chronological scoring is not proof of full historical deployability. Read alongside the report’s plain-language explanations and the executed notebook.',
            '## Do media variables improve the same forecasts?',
            'All three rows use the same 44 monthly outcomes, February 2023–September 2026. Loss is augmented-model squared error minus baseline squared error, in squared survey-index points. Negative favors adding media. Confidence intervals describe the average loss difference, not the RMSE difference. HAC(3) allows nearby loss errors to be related; nested models and the short sample limit the approximation. Intervals are pointwise, not simultaneous. Only the p-values are BH adjusted within the original three-test family.',
            markdown_table(['Added-media model / reference','RMSE reference → added','Mean loss difference [95% CI]','Raw p / BH q'],
                           [[f'{r.augmented} / {r.baseline}',f'{f(r.baseline_rmse)} → {f(r.augmented_rmse)}',
                             f'{f(r.mean_squared_loss_difference)} [{f(r.loss_difference_lower_95)}, {f(r.loss_difference_upper_95)}]',
                             f'{f(r.hac_pvalue_two_sided)} / {f(r.bh_qvalue_existing_three_test_family)}'] for r in loss.itertuples()]),
            'The point improvements are small, but failure to find an improvement is not proof of zero media influence. The intervals permit both better and worse prediction. No equivalence margin was registered, and these are not causal-effect bounds.',
            '## How large is the fitted tone association?',
            'A tone change of +0.1 could mean -0.2 becoming -0.1 on the classifier’s -1 to +1 scale. These are full 80-month fitted associations, not newly evaluated forecasts. All intervals use HAC(3); the copied coefficient q-values belong to the original pooled association-test family, distinct from the forecast-loss family.',
            markdown_table(['Model','Survey-point association for tone +0.1 [95% CI]'],
                           [[r.model,f'{f(r.effect_for_tone_plus_0_1)} [{f(r.effect_lower_95)}, {f(r.effect_upper_95)}]'] for r in association.itertuples()]),
            f'The M2 rolling tone coefficient changes from {rolling.coefficient.min():.3f} to {rolling.coefficient.max():+.3f} over {len(rolling)} refits, with {int(rolling.coefficient.gt(0).sum())} positive estimates. Its sign and size are not stable enough to interpret as an invariant structural effect.',
            '## Are three macroeconomic indicators enough?',
            f'On the 141 common historical test months, M1 has {m1_ratio:.3f} times the squared prediction error of simply repeating the previous survey. The household-control version still has {controls_ratio:.3f} times that error. These ratios answer a predictive comparison; neither an in-sample fit statistic nor a forecast residual identifies how much pessimism economics causally explains.',
            markdown_table(['Full-history fitted model','Months','Adjusted R-squared','Durbin–Watson','Ljung–Box(12) p'],
                           [[r.model,int(r.n),f(r.adjusted_r2_in_sample),f(r.durbin_watson),f'{r.ljung_box_pvalue:.3g}'] for r in model_diagnostics.itertuples()]),
            'Adjusted R-squared is a penalized descriptive fit statistic, not an out-of-sample or causal share explained. A Durbin–Watson value near two is compatible with little first-order residual correlation; M1’s very low value and Ljung–Box test show persistent errors. HAC standard errors alone do not repair that forecasting model.',
            markdown_table(['Specification, same 141 months','RMSE','Latest September gap'],
                           [[r.model,f(r.rmse),f(r.latest_september_gap,2)] for r in economic_sensitivity.itertuples()]),
            'The survey-mode ramp reduces the latest gap, but it also absorbs every coincident post-2024 change. Its improvement is not identification of a causal survey-mode effect. GDP definitions, annual sine/cosine terms and the 60-month window are sensitivities, not return-based or outcome-based choices of a winning model.',
            '## Persistent levels and independent sensitivities',
            f"Historical sentiment has lag-one correlation {dynamic_summary['historical_sentiment_diagnostics']['lag1_correlation']:.3f}. ADF p={dynamic_summary['historical_sentiment_diagnostics']['adf_pvalue']:.3f} and KPSS p={dynamic_summary['historical_sentiment_diagnostics']['kpss_pvalue_tabulated']:.3f} warn that simple level regressions may be unreliable. The tests have different nulls; breaks can resemble nonstationarity, so neither establishes the integration order.",
            markdown_table(['Exploratory change model, same 44 months','RMSE'],
                           [[r.model,f(r.rmse,4)] for r in dynamic.itertuples()]),
            f"With lagged sentiment change, adding tone changes RMSE from {dynamic_lookup.loc['D_macro_AR','rmse']:.4f} to {dynamic_lookup.loc['D_macro_AR_media','rmse']:.4f}. The separate two-contrast dynamic family has BH q={dynamic_q:.3f}. It was added after the original analysis and remains exploratory. Macroeconomic changes here are changes in the available information features, including revisions, not clean surprises.",
            markdown_table(['Alternative media measure / lag','Test months','RMSE','Gain versus its same-pool macro model'],
                           [[r.sample,int(r.n),f(r.rmse),f'{f(r.rmse_improvement_percent_vs_same_pool_macro,2)}%'] for r in media_sensitivity.itertuples()]),
            'Different lags have different matched test periods. They must not be ranked against one another as if they used identical samples. The post-2022 measurement check has only nine test months; it is weak evidence about a future deployment. These alternatives do not replace the original three contrasts.',
            '## Separate headline, current conditions and expectations',
            'September final values and economic-only forecasts below preserve the required survey distinctions. Prediction ranges based on past forecast errors are wide; neither a negative gap nor a component difference measures cognitive bias.',
            markdown_table(['September final outcome','Observed / prediction','Gap','Past-error 95% range'],
                           [[r.target,f'{f(r.observed,1)} / {f(r.prediction,2)}',f(r.gap,2),
                             f'[{f(r.empirical_lower_95,2)}, {f(r.empirical_upper_95,2)}]'] for r in components.itertuples()]),
            '## Prospective causal identification',
            'The assignment permits observational evidence plus a detailed stronger-design proposal. The [prospective plan](CAUSAL_POWER_PLAN.md) specifies the estimand, truthful stimuli, outcome scoring, analysis, missingness, multiplicity and a planning sample size. No participants or experimental effects are claimed.',
            'Rebuild these tables with `python -m src.rubric_evidence`. All source hashes and planning assumptions are in `outputs/tables/rubric_evidence_summary.json`. Detailed datasets remain local under the no-data-commit policy.']
    (root/'docs/STATISTICAL_EVIDENCE.md').write_text('\n\n'.join(text)+'\n', encoding='utf-8', newline='\n')
    return summary


if __name__ == '__main__':
    result = build()
    print(json.dumps({'artifacts': result['artifacts'], 'planning_only': result['prospective_primary_power_plan']}, indent=2))
