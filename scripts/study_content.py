"""One computed narrative shared by the report, notebook and presentation."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / 'outputs' / 'tables'


def load(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def csv(name):
    path = T / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def fmt(x, digits=2):
    try:
        return f'{float(x):.{digits}f}' if np.isfinite(float(x)) else 'Unavailable'
    except (TypeError, ValueError):
        return str(x)


def p(text): return {'type': 'p', 'text': text}
def table(headers, rows, widths=None):
    result = {'type': 'table', 'headers': headers, 'rows': rows}
    if widths: result['widths'] = widths
    return result
def figure(name, caption, width='.96', height=None):
    result = {'type': 'figure', 'name': name, 'caption': caption, 'width': width}
    if height is not None: result['height'] = height
    return result


def evidence():
    f = csv('forecasts.csv')
    metrics = csv('model_metrics.csv')
    macro = pd.read_csv(ROOT / 'data' / 'processed' / 'monthly_dataset.csv')
    media = pd.read_csv(ROOT / 'data' / 'processed' / 'media_monthly.csv')
    primary = f[(f.target == 'sentiment') & (f.model == 'M1_economic')].sort_values('month')
    recent = primary[primary.month >= '2026-01-01']
    m = metrics[(metrics.target == 'sentiment') & metrics.model.isin([
        'M1_economic','M2_economic_media','M3_economic_media_controls','M1_controls','AR1','AR_macro','AR_macro_media','Persistence'])]
    common = m[m['sample'].astype(str).str.contains('common')]
    if len(common):
        samples = common.groupby('sample').model.nunique()
        m = common[common['sample'] == samples.idxmax()]
    elif m['sample'].nunique() > 1:
        m = m[m['sample'] == m.groupby('sample').model.nunique().idxmax()]
    m = m.drop_duplicates('model')
    return {'forecasts': f, 'metrics': metrics, 'comparison': m, 'macro': macro,
            'media': media, 'primary': primary, 'recent': recent,
            'media_summary': load(ROOT / 'outputs' / 'media_summary.json'),
            'economic_summary': load(T / 'economic_summary.json')}


def comparison_rows(e):
    names = {'M1_economic':'M1: economics','M2_economic_media':'M2: economics + media',
             'M3_economic_media_controls':'M3: economics + media + controls',
             'AR1':'Fitted AR1','AR_macro':'Autoregression + economics',
             'AR_macro_media':'Autoregression + economics + media',
             'M1_controls':'Economics + household controls','Persistence':'Last observed sentiment'}
    return [[names.get(r.model,r.model),int(r.n),fmt(r.rmse),fmt(r.mae),fmt(100*r.coverage_95,1)+'%' if pd.notna(r.coverage_95) else '—']
            for r in e['comparison'].itertuples()]


def investment_evidence():
    summary = load(T / 'investment_summary.json')
    rows = {row['model']: row for row in summary['full_metrics']}
    return summary, rows


def investment_rows(rows):
    names = [('Static_60_40', 'Monthly 60% SPY / 40% BIL'),
             ('Macro_trend_80_20', 'Macro + trend allocation'),
             ('SPY_hold', 'SPY buy-and-hold'), ('BIL_hold', 'BIL buy-and-hold')]
    return [[label, fmt(100*rows[model]['net_cagr'])+'%',
             fmt(100*rows[model]['max_drawdown'])+'%'] for model, label in names]


def verdict(e):
    m = e['comparison'].set_index('model')
    if {'M1_economic','M2_economic_media'}.issubset(m.index):
        delta = float(m.loc['M1_economic','rmse'] - m.loc['M2_economic_media','rmse'])
        n = int(m.loc['M2_economic_media','n'])
        text = f'On the common {n}-month chronological assessment sample, adding the specified media variables '
        text += f"{'reduces' if delta > 0 else 'increases'} RMSE by {abs(delta):.2f} index points relative to M1."
        if {'AR_macro','AR_macro_media'}.issubset(m.index):
            ar_delta = float(m.loc['AR_macro','rmse'] - m.loc['AR_macro_media','rmse'])
            text += f" With lagged sentiment included, media {'reduces' if ar_delta > 0 else 'increases'} RMSE by {abs(ar_delta):.2f} points."
        return text
    return 'A common-sample media comparison is unavailable; no incremental forecasting claim is supported.'


def ai_review_text():
    s=load(ROOT/'outputs/ai_diagnostic_validation_metrics.json')
    if not s:
        return 'Independent AI review metrics are pending; no human-reference performance is available.'
    return (f"The two AI reviews agree on {100*s['tone_agreement']:.1f}% of the original {s['completed_independent_pairs']} titles "
            f"(kappa {s['tone_cohens_kappa']:.3f}). After relevance refinement, {s['annotation_pool_final_eligible_n']} remain eligible and "
            f"{s['annotation_pool_final_excluded_n']} are excluded; the originals are preserved. On final-eligible three-class references, "
            "contextual concordance exceeds dictionary concordance in both reviews. Mixed/uncertain cases are excluded explicitly from "
            "three-class metrics. These are AI development diagnostics, not human accuracy. Class/source breakdowns are retained in the notebook.")


def stability_text():
    data=csv('media_rolling_coefficients.csv')
    d=data[(data.model=='M2_economic_media')&(data.variable=='media_tone_lag1')]
    tests=csv('predictive_loss_tests.csv')
    return (f"Across {len(d)} recursive M2 fits, the lagged-tone coefficient ranges from {d.coefficient.min():.2f} to "
            f"{d.coefficient.max():.2f} and is positive in {int((d.coefficient>0).sum())} fits. "
            f"The three loss comparisons have BH q values of {tests.bh_qvalue.min():.3f}–{tests.bh_qvalue.max():.3f}; "
            "none establishes a reliable gain. Dictionary, lag, source, framing and post-2022 checks are exploratory sensitivities. "
            "HAC standard errors cannot repair M1’s serial misspecification or structural breaks.")


def provider_evidence():
    data=csv('provider_bias.csv')
    if 'comparison_status' in data:
        data=data.loc[data.comparison_status.eq('main_common_event_panel')]
    if data.empty:
        raise FileNotFoundError('Run the provider comparison before building the revised submission.')
    required={'CNBC','Fox News'}
    assert required.issubset(set(data.provider)), 'CNBC and Fox News must have real, comparable observations.'
    assert data.n_events.nunique()==1, 'Provider bars require an identical release set.'
    return data


def provider_caption():
    d=provider_evidence()
    s=load(T/'provider_bias_summary.json')
    ids=s.get('common_event_ids',[])
    mix=(f" The shared set contains {sum(str(x).startswith('employment_') for x in ids)} employment and "
         f"{sum(str(x).startswith('cpi_') for x in ids)} CPI releases.") if ids else ''
    return (f"Separate matched-release supplement: {len(d)} providers, {int(d.n_events.iloc[0])} identical releases and "
            f"{int(d.n_titles.sum()):,} headlines.{mix} Bars are each provider’s negative-headline share minus its equal-weight "
            "same-release peers, averaged across releases. Positive means relatively more negative wording; zero is a peer "
            f"reference. n labels count headlines. The 95% stability ranges resample {int(d.n_month_clusters.iloc[0])} calendar-month clusters "
            "and omit classification/retrieval uncertainty.")


def dynamics_text():
    s=load(T/'dynamics_summary.json')
    if not s:
        return 'Level persistence and structural breaks limit coefficient interpretation; differenced-model diagnostics are retained separately.'
    diagnostics=s['historical_sentiment_diagnostics']
    metrics={x['model']:x for x in s['metrics']}
    q=max(x['bh_qvalue_within_bandwidth_family'] for x in s['dynamic_loss_tests_hac3'])
    return (f"Historical sentiment has lag-one correlation {diagnostics['lag1_correlation']:.3f}; ADF p={diagnostics['adf_pvalue']:.3f} "
            f"and KPSS p={diagnostics['kpss_pvalue_tabulated']:.3f} warn against interpreting persistent levels mechanically. "
            "Breaks can mimic nonstationarity. In an exploratory differenced model with lagged sentiment change, adding media "
            f"changes RMSE from {metrics['D_macro_AR']['rmse']:.4f} to {metrics['D_macro_AR_media']['rmse']:.4f}; "
            f"the separate two-test family supplies no reliable improvement (BH q={q:.3f}). The primary tests remain unchanged.")


def household_control_text(e):
    historical = e['metrics'].loc[(e['metrics'].target == 'sentiment') &
                                  (e['metrics']['sample'] == 'historical_oos')].set_index('model')
    common = e['comparison'].set_index('model')
    return (f"Adding household controls lowers historical RMSE from {historical.loc['M1_economic','rmse']:.2f} "
            f"to {historical.loc['M1_controls','rmse']:.2f} across {int(historical.loc['M1_controls','n'])} months. "
            f"On the {int(common.loc['M1_controls','n'])}-month media-overlap sample, controls yield "
            f"{common.loc['M1_controls','rmse']:.2f} versus {common.loc['M1_economic','rmse']:.2f} for M1. "
            "Their predictive benefit is period-dependent, not evidence that one omitted pressure explains the gap.")


def media_description_rows(data):
    means = data.mean(numeric_only=True)
    share = lambda name: f'{100*means[name]:.1f}%'
    return [
        ['Tone', f"Score {means['media_tone']:.3f}; {share('negative_share')} negative; "
                 f"{share('emotional_wording_proxy')} emotional-keyword proxy"],
        ['Selection / salience', f"{share('salience_housing')} housing; {share('salience_wages')} wages; "
                                 f"{share('salience_layoffs')} layoffs; {share('salience_hiring')} hiring"],
        ['Framing', f"{share('frame_price_level')} price level versus {share('frame_inflation_rate')} inflation rate; "
                    f"{share('frame_household')} household versus {share('frame_national')} national"],
        ['Political attribution', f"{share('political_actor_mention')} actor mentions; "
                                 f"{share('political_credit_proxy')} credit and {share('political_blame_proxy')} blame co-occurrence"]]


def perturbation_text(summary):
    tests = {row['test']: row for row in summary['perturbation']['variant_comparisons']}
    def result(name):
        row = tests[name]
        return (f"{round(row['n']*row['class_switch_rate'])}/{row['n']} labels "
                f"(mean absolute tone change {row['mean_absolute_tone_delta']:.3f})")
    return (f"Political-name swaps changed {result('political_name_swap')}; adding a Gothamist prefix changed "
            f"{result('source_prefix_Gothamist')}, and a Reuters prefix {result('source_prefix_Reuters')}. "
            "These stress tests motivate source-blind inputs; they do not establish political discrimination or factual bias.")


def sections():
    e = evidence()
    latest = e['primary'].iloc[-1]
    gap = e['recent'].gap.mean()
    media = e['media']
    completed = media[media['partial_month'].astype(str).str.lower().isin(['false','0','0.0'])] if 'partial_month' in media else media
    focus = completed.loc[completed.month.ge('2026-01-01') & completed.month.lt('2026-10-01')]
    total_items = int(media.item_count.sum())
    comp = e['comparison']
    comp_dates = f"{str(comp.start.min())[:10]} to {str(comp.end.max())[:10]}" if len(comp) else 'unavailable'
    audit = load(T / 'workbook_audit.json')
    investment, portfolios = investment_evidence()
    adaptive, fixed, spy = [portfolios[model] for model in ['Macro_trend_80_20','Static_60_40','SPY_hold']]
    pages = []
    pages.append(('Question, evidence and practical result', [
        p('This project asks whether economic narratives help explain the divergence between the University of Michigan Index of Consumer Sentiment and headline economic conditions before the November 3, 2026 midterm elections. It separates household pressures, selective information or framing, and measurement or model inadequacy. Negative coverage and pessimistic consumers are not presumed biased.'),
        p(f"The first result is a measurement warning. The supplied workbook is not a release-vintage dataset, its latest PCE value does not match official headline inflation, and its Q3 GDP value precedes the official release. Official economic snapshots replace those values in the main analysis. For the latest completed-month economic forecast, observed sentiment is {fmt(latest.observed,1)}, the M1 prediction is {fmt(latest.prediction,1)}, and the gap is {fmt(latest.gap,1)} points. The mean 2026 assessment gap is {fmt(gap,1)} points. These residuals depend on the model."),
        p(verdict(e) + ' Predictive improvement, if present, cannot distinguish genuine household pressure from framing, reverse causality or omitted shocks. A separate same-release provider comparison, including CNBC and Fox brands, is shown on page 11.'),
        table(['Evidence component','What is actually available'], [
            ['Economic baseline','Monthly data from 2010; historical ALFRED macro vintages; headline and survey components'],
            ['Content sample',f'{total_items:,} sampled titles across {len(media)} calendar months; national, local and Hacker News strata'],
            ['Monitoring','October preliminary sentiment 46.3; incomplete October media; cutoff October 13, 2026'],
            ['Validation status','AI and dictionary diagnostics; two independent HUMAN annotators are not available'],
            ['Identification','Observational analysis and a detailed prospective causal-design proposal']], [.25,.75]),
        p(f"The separate October 17, 2026 investment extension favors a simple benchmark within this historical sample: monthly 60% SPY / 40% BIL earned {fmt(100*fixed['net_cagr'])}% net CAGR, versus {fmt(100*adaptive['net_cagr'])}% for the fixed macro/trend rule, through October 2, 2026. Both were historically profitable after modeled costs; neither establishes alpha or prospective profitability. The investment conclusion and risk comparison are on page 12.")]))
    pages.append(('1. Input audit and source provenance', [
        p('The two supplied files were read before analysis. The spreadsheet has four separate date/value pairs rather than one aligned panel: U-3 unemployment, Michigan headline sentiment, a column labeled PCE YoY, and quarterly GDP growth. Values must be joined by their own observation periods. Month-end labels describe the month; they do not establish the day information became available. The sheet provides no original source URLs, retrieval clocks, publication dates or revision vintages.'),
        table(['Input issue','Official check and treatment'],[
            ['October sentiment 46.3','Michigan released a preliminary October estimate October 9; retain for monitoring, separate from completed final targets.'],
            ['Q3 2026 GDP 3.7','Advance estimate scheduled October 29; quarantine throughout the October 13 snapshot.'],
            ['August PCE YoY 3.00759','All 584 workbook inflation values match core PCE within 0.0001 percentage point. Required headline August inflation is 3.419%, reported as 3.4% by BEA.'],
            ['Missing October 2025 U-3','BLS collected no October CPS data during the shutdown; do not interpolate or invent that observation.'],
            ['Historical GDP revisions','Q2 2026 third estimate and annual updates cannot enter forecasts before September 30. Use each origin’s actual snapshot.']], [.28,.72]),
        p('Official sources are the BLS Current Population Survey, BEA national accounts and PCE releases, and Michigan Surveys of Consumers. ALFRED redistributes BLS/BEA series with historical vintages; it is the transport for the as-of feature matrix, not a different economic definition. Raw payload bytes, exact request URLs, retrieval times and SHA-256 hashes are retained locally. The workbook audit and source provenance are computed and retained as local tables.'),
        p('Acquisition is distinct from interpretation. A current downloaded survey history is used as the final monthly outcome series, while the preliminary October release is kept as a separate monitoring observation. Historical survey-target revisions and original media wording cannot be fully reconstructed. The submitted notebook preserves aggregate exhibits; the repository excludes raw and derived datasets under the established course submission policy. Snapshot hashes support local verification, but code-only re-downloads cannot guarantee identical mutable-feed results.')]))
    pages.append(('2. Economic definitions and prediction timing', [
        p('Each forecast uses the first calendar day of its target month as its historical ALFRED snapshot. Since within-day release time is unresolved, the origin is interpreted as the end of that day. The three required predictors are the latest published seasonally adjusted U-3 unemployment rate, headline PCE year-over-year inflation, and the latest published quarterly real GDP quarter-over-quarter annualized growth. Each row preserves observation periods; age fields count days since the reference period began, not days since publication. GDP is carried as a known quarterly predictor; it is never interpolated into synthetic monthly GDP observations.'),
        table(['Measure','Transformation or interpretation'],[
            ['Headline PCE inflation','100 × (PCEPI_t / PCEPI_(t−12) − 1), computed within the same vintage.'],
            ['GDP QoQ annualized','100 × [(real GDP_q / real GDP_(q−1))^4 − 1].'],
            ['GDP YoY sensitivity','100 × (real GDP_q / real GDP_(q−4) − 1); different from annualized quarterly growth.'],
            ['Cumulative price control','36-month PCE price increase, using the same origin’s price-index history.'],
            ['Household-income control','Real disposable personal income YoY; aggregate income is still not the distribution of household experience.']], [.31,.69]),
        p('A historical vintage establishes that a value was available by the prediction origin; it does not recover the precise publication clock of every historical observation. Recent official release dates are recorded separately. Transformations require the exact calendar lag, so missing periods cannot be silently bridged. Later GDP revisions and chain-base changes are kept within their own vintages.'),
        p('The survey covers personal finances, business conditions and buying conditions, including expectations. It is not a direct referendum on unemployment, inflation and GDP. Headline, Current Economic Conditions and Consumer Expectations are analyzed separately. The distinction matters because inflation can fall while prices remain well above the level households remember; real GDP can grow while housing costs, debt service or the distribution of income worsen for some households.'),
        p('Training uses only targets before each origin. Lagged final sentiment provides a persistence benchmark. First-day predictions precede the published index, but some interviews began the previous month, so the origin need not precede every respondent’s interview. Partial October news cannot be backfilled into an October 1 prediction. Media lags are formed on the full monthly grid before removing incomplete rows.')]))
    pages.append(('3. Out-of-sample economic baseline and uncertainty', [
        p('M1 estimates sentiment from unemployment, headline PCE inflation and quarterly annualized GDP growth, using at least 60 earlier months. Separate Current Conditions and Expectations models have historical test RMSEs of 16.50 and 10.44 points. A negative headline gap is observed sentiment minus its chronological prediction. It measures unexplained pessimism under M1, with uncertainty from model specification and structural instability; it is not an estimate of perceptual bias.'),
        figure('economic_forecast','Observed final headline sentiment and chronological M1 forecasts. Empirical intervals use only earlier forecast errors; absence of an early band means insufficient calibration history.'),
        p('Over the 141 common historical test months, M1 RMSE is 12.35 index points versus 4.26 for last-observation persistence. M1 approximate interval coverage is 72.3%; its empirical interval covers 78.4% of 116 calibrated observations. Strong residual autocorrelation and undercoverage show that the simple macro baseline is inadequate. September sentiment 48.1 falls below its approximate interval [50.23, 91.10] but inside its past-error interval [44.13, 97.21]. The claimed discrepancy depends on how uncertainty is modeled.'),
        p('Residual persistence, pandemic disruption and the post-2021 inflation experience challenge a stable linear mapping from three aggregates to sentiment. Rolling-window, seasonality, GDP-growth-definition and survey-method sensitivities are included in the analytical tables. An AR1 benchmark and macro models with lagged sentiment test whether any apparent improvement merely reflects persistence. Coefficient paths and HAC uncertainty are supplied as diagnostics rather than one invariant structural relationship.')]))
    pages.append(('4. Household pressures and survey comparability', [
        figure('recent_gap','Recent observed-minus-M1 residuals. These are model errors, not percentages of irrational consumers or attributable media effects.'),
        p('The first alternative explanation is omitted economic pressure. Real disposable income growth and the cumulative 36-month PCE price increase add distinct information: current inflation measures the rate of change, while the accumulated increase measures the elevated price level. The controls are manageable and reproducible, but they do not exhaust housing affordability, consumer credit, inequality, regional shocks or job insecurity. A remaining residual can still reflect those omissions.'),
        p(household_control_text(e)),
        p('The second alternative is survey measurement. Michigan’s announced web shares were 25%, 50%, 75% and 100% from April through July 2024. A ramp sensitivity reduces September’s gap to −3.99 points, while the autoregressive macro model yields −4.64 instead of M1’s −22.57. The ramp confounds every coincident post-transition change and cannot identify a causal mode effect. Michigan’s July 2026 report, revised September 4, also finds the 2026 low persists under consistent-mode comparisons; the sensitivity cannot establish that the survey change caused pessimism.'),
        p('Michigan documents partisan differences and releases demographic breakdowns. The October preliminary description emphasizes lower-income consumers and smaller stock portfolios; these published observations are contextual evidence, not respondent-level controls. No individual party identification, exposure, geography, recall or beliefs are observed in the monthly analytic panel. The project does not manufacture subgroup estimates or equate a national aggregate with any specific group.'),
        p(dynamics_text())]))
    pages.append(('5. Media corpus: balance, units and limitations', [
        p(f'The corpus covers January 2020 through October 12, 2026, including {len(completed)} complete months and a partial October monitoring month. Google News RSS retrieves economic titles for a fixed national panel (AP, Reuters, NPR) and a local panel (Gothamist, Texas Tribune, Colorado Sun). Hacker News Algolia supplies public user-posted story titles. The same broad concept family includes the economy, inflation, unemployment, wages, housing and the cost of living; queries do not condition on negative sentiment.'),
        figure('media_coverage','Upper panel: captured title counts. Lower panel: available outlets and source groups, on a separate vertical scale. Sparse or missing outlet-months reflect incomplete capture, not zero coverage of a topic.'),
        p('The unit is a title. News headlines and HN user-submitted titles are analyzed in separate strata before aggregation; neither is a full-article argument or a record of what survey respondents read. Candidates are sampled by a deterministic hash with a fixed maximum per outlet-month. Items average within outlet, outlets within group, and groups across the monthly index. Both available-group and complete-group coverage are reported.'),
        p('Exact normalized duplicates, repeated IDs, obvious promotions, out-of-period items and clearly foreign-only titles are audited. Unknown geographic relevance, near-duplicate syndication and suspected automated activity cannot be fully resolved from titles. HN is a selected technology community and may link to news; it is not a representative sample of US adults. Platform engagement, where returned, is a retrieval-vintage attention proxy and never a historical exposure weight.'),
        p('RSS results are ranked and capped. The fixed panel improves comparability but is not a census or a politically representative sample. Retrospective search visibility, deletions and edited titles limit historical reconstruction. Content supply, engagement and actual exposure remain different quantities. Missingness and source composition are displayed so a change in the index can be assessed against a change in the sample.')]))
    pages.append(('6. Codebook, AI measurement and benchmarks', [
        table(['Dimension','Operational proxy and boundary'],[
            ['Tone','Pinned contextual P(positive) − P(negative), plus VADER. Negative facts and emotionally loaded wording need separate annotation.'],
            ['Selection / salience','Title shares for layoffs, hiring, prices, disinflation, growth, recession, wages and housing; conditional on captured economic coverage.'],
            ['Framing','Price level versus inflation rate, household versus aggregate, and current versus forecast concepts; frames can co-occur.'],
            ['Factual calibration','Screen explicit numerical claims; verify definition, period, units and available official vintage. Eligibility is never accuracy.'],
            ['Political attribution','Actor mentions and directional credit/blame proxies separately. Criticism and attribution do not establish bias.']], [.24,.76]),
        p('The codebook is frozen before project scoring, with subsequent relevance-screen amendments disclosed separately. The primary classifier is an immutably pinned CardiffNLP Twitter RoBERTa sentiment model. Model artifacts and inputs are hashed; the model is not fine-tuned on Michigan outcomes. VADER is the conventional dictionary comparison. Rule-based frame and salience indicators remain unvalidated literal proxies. Exact specifications and annotation instructions are retained in the reproducibility package.'),
        p('The contextual model was introduced in 2022 with training text through 2021. Applying it to earlier titles uses a later language representation, so the full media analysis is retrospective pseudo-out-of-sample measurement. A genuinely historical deployment claim would require models, feeds and original wording frozen at each date. The dictionary and post-2022 sensitivities narrow, but do not eliminate, those limitations.'),
        p('Benchmarks must match the proposed bias. The supplemental comparison on page 11 matches providers on identical official releases and estimates relative negative framing. This controls the release being covered but cannot equate all truthful components emphasized in a headline. An equivalent-surprise selection test remains prospective because archived expectations and a complete publication denominator are unavailable. Eight purposively selected unemployment-title percentages align with official releases; missing definitions/periods and intraday uncertainty prevent a full factual-accuracy classification.'),
        p('Political-name swaps and source-label prefixes stress-test otherwise similar inputs. A changed actor can also change meaning. Evidence excerpts and versioned instructions accompany the annotation workflow. No title-only classifier establishes a reader’s availability, confirmation or negativity bias. Price-level wording and cumulative inflation do not establish anchoring to past prices without individual reference-price, belief or experimental evidence.'),
        table(['Dimension','Jan–Sep 2026: balanced monthly mean'], media_description_rows(focus), [.25,.75]),
        p(f'Descriptive results cover {len(focus)} complete months and {int(focus.item_count.sum())} titles. Titles average within outlets and outlets within source groups; the three groups and each month then receive equal weights. Topic and frame flags can overlap. These weighted content proxies are not pooled-title shares, respondent beliefs or an objective bias rate.'),
        p(perturbation_text(e['media_summary']))]))
    pages.append(('7. Validation status and honest performance claims', [
        p('The assignment explicitly requires at least 300 items labeled by two independent human annotators. No completed independent human labels were available. The project therefore prepares the blinded human worksheets, guide, adjudication procedure and validation code, and conducts independent AI reviews where available. AI reviews do not satisfy the human requirement. This is a material rubric limitation of the delivered project.'),
        table(['Validation component','Status and interpretation'],[
            ['Stratified annotation packet','At least 300 unique sampled items; separate blinded orders, evidence fields and private source/date key.'],
            ['Human agreement / kappa','Unavailable until two people independently complete labels; no fabricated agreement statistic.'],
            ['Human accuracy / class F1','Unavailable without valid human reference/adjudication; model-dictionary agreement is not accuracy.'],
            ['Independent AI diagnostic','Explicitly AI-labeled; useful for error discovery, not independent human ground truth.'],
            ['Factual accuracy','Unverified corpus. Numerical-claim eligibility and a calibration worksheet are supplied; no error rate inferred.'],
            ['Adjudication','Lock original files, identify disagreement, record a third judgment and reason; retain all original evidence.']], [.30,.70]),
        p('The validation code reports raw agreement, Cohen’s kappa, class precision/recall/F1, macro-F1 and source-specific performance only for completed and explicitly identified references. Uncertain and mixed labels must be handled transparently rather than silently mapped to convenient classes. An untouched future test set is needed after any classifier or rule change motivated by review.'),
        p('A plausible AI tone score is insufficient validation of the economic construct. Titles can quote someone else, use sarcasm, attach blame to a target, describe good aggregate news with bad household implications, or express neutral factual adversity. These failure modes motivate short evidence excerpts, emotional-wording labels and frame-specific checks.'),
        p(ai_review_text())]))
    pages.append(('8. Incremental prediction and statistical inference', [
        p('M2 adds one prior-month tone measure; M3 adds cumulative prices and real income growth. All comparison models use the same February 2020 onward training pool, at least 36 prior months and identical tests. These refitted M1 predictions differ from the 2010 onward historical monitoring baseline. A controls-only model isolates M3’s media addition; lagged-sentiment and persistence models provide demanding benchmarks.'),
        table(['Model','N','RMSE','MAE','95% coverage'],comparison_rows(e),[.44,.08,.14,.14,.20]),
        p('Common comparison dates: ' + comp_dates + '. ' + verdict(e)),
        figure('model_accuracy','Common-sample forecast errors. Lower error is useful only with stable performance, valid timing and measured inputs; it does not identify the mechanism.'),
        p(stability_text())]))
    pages.append(('9. Causal reasoning and falsification', [
        p('The selected assignment-permitted route is observational analysis plus a detailed causal-design proposal. A common economic shock can worsen sentiment and increase negative coverage; pessimistic audiences can seek negative content; publishers can respond to audience demand. Political affiliation can influence media choice and survey responses. Aggregate monthly regressions cannot separate these pathways without exposure or assignment information.'),
        p('The proposed stronger design randomizes consenting participants to equally accurate summaries of the same official release, varying price-level versus inflation-rate and household versus aggregate emphasis. Keep numerical values, source credibility, length and reading difficulty constant. Measure baseline and post-treatment beliefs, perceived household conditions, recall and sentiment-related responses. Pre-register outcomes, contrasts, exclusion rules and a power calculation based on pilot variability. Obtain required institutional approval before recruitment; no participants were recruited for this project.'),
        p('Random assignment would identify the effect of assigned framing on outcomes in that sample, subject to compliance, attrition and interference assumptions. A manipulation check verifies that framing changed without factual misunderstanding. Report intention-to-treat estimates, confidence intervals, attrition by arm and multiple-outcome adjustment. A placebo unrelated frame, neutral fact comprehension test and delayed follow-up can test alternative interpretations.'),
        table(['Finding that would challenge a media-bias account','Why it matters'],[
            ['No stable incremental forecast improvement','Narrative measurement may contain no information beyond economic conditions and persistence.'],
            ['Gap shrinks with household controls or mode adjustment','Economic experience or measurement explains the apparent discrepancy.'],
            ['Negative stories are factually calibrated to bad outcomes','Adverse facts do not establish distorted coverage.'],
            ['Matched-release asymmetry vanishes after surprise controls','Different news content can reflect different events rather than selective emphasis.'],
            ['No framing effect or recall mechanism in a powered experiment','Weakens the proposed mechanism under the tested conditions.']], [.57,.43]),
        p('Transporting a sample experiment to the national Michigan index would require representative or reweighted sampling, actual population exposure estimates, outcome comparability, heterogeneous-effect estimates and defensible transportability assumptions. The experiment alone would not identify an effect on the national index. The full plan and assumptions are in docs/causal_design.md.')]))
    pages.append(('10. Provider comparison and monitoring', [
        figure('provider_bias',provider_caption()),
        p('The supplement was retrieved October 15, 2026, after the October 13 economic cutoff. A coverage-only feasibility amendment selected six providers with six shared releases after the initial mandatory core supported only four. The y-axis measures relative negative framing; the x-axis identifies providers. Identical search rules, source-blind classification and equal event weights apply. CNBC, Fox News and Fox Business remain separate publications. The original monthly forecast corpus and results are unchanged.'),
        p('A positive bar is not proof of distortion. Providers can truthfully emphasize different components, such as unemployment versus wages. Zero is not objective neutrality. Some signs change under dictionary or single-title sensitivities; the ranking is unstable. The new providers lack human validation, and the original AI review contains no CNBC or Fox items. Feed selection, few clusters and classification error limit interpretation. The chart does not measure ideological slant, factual dishonesty, exposure or a causal sentiment effect.'),
        p('The interactive dashboard also displays sentiment, the economic prediction and intervals, the gap, media dimensions, source composition and performance. Preserve the October 13 economic snapshot when updating; October 23 Michigan final and October 29 GDP/PCE releases remain prospective. Election proximity is context, not an identified treatment.'),
        p('Use provider differences to target matched-story review and forecast-risk scenarios. The separate investment backtest on page 12 compares macro/trend allocation with simple SPY/BIL portfolios; provider bars never select securities or trades.')]))
    pages.append(('11. Answers and investment conclusion', [
        table(['Required research question','Answer supported by this project'],[
            ['How measure coverage bias?','Define an event/accuracy benchmark; measure tone, selection, framing, calibration and attribution separately. Current proxies measure content, not a validated global bias score.'],
            ['Impact on Michigan sentiment?','Estimate lagged predictive associations with uncertainty; causal depression of the national index is not identified.'],
            ['How much do three macro indicators explain?','Chronological M1 predictions, errors and intervals quantify model-specific fit; omitted pressure and instability remain.'],
            ['Which perceptual mechanisms measurable?','Price-level and household framing are content proxies; individual anchoring, availability, confirmation and negativity bias remain unobserved.'],
            ['Does media improve predictions?','Use the common-sample M1/M2/M3 and autoregressive comparisons on page 9; improvement is conditional on this retrospective sample.'],
            ['What would contradict media bias?','Successful household controls, unstable or null incremental prediction, calibrated coverage, and null properly powered framing effects.']], [.31,.69]),
        figure('investment_strategy',
               f"October 17 retrospective extension: January 2, 2015–October 2, 2026 returns. Yahoo adjusted prices approximate reinvested distributions. Costs: {investment['cost_bps_per_dollar_traded']} bps per dollar bought or sold in either ETF, including entry and final liquidation. No return-based threshold search.",
               height='145pt'),
        table(['Portfolio: same dates and costs','Net CAGR','Worst drawdown'],
              investment_rows(portfolios), [.60,.20,.20]),
        p('The historical comparison favors monthly 60% SPY / 40% BIL. The custom trend/Sahm-style rule holds 80% SPY when prior-month price exceeds its ten-month mean and the as-of three-month unemployment mean is less than 0.50 points above its trailing twelve-month low; otherwise 20%, with BIL the remainder. Incomplete labor windows are defensive. Both rules rebalance at the first joint-session close strictly after each monthly origin. Timing added little drawdown protection over 60/40.'),
        p('Limits: no two-human media validation, corpus-wide factual audit or respondent exposure. Backtests use retrospective adjusted prices and assumed costs, omit taxes and nonlinear impact, and lack untouched validation. Gap/media tilts use revised or reconstructed inputs; all 44 gap signals add equity exposure. Historical net profit establishes neither alpha nor future profit. Details: docs/INVESTMENT_PROTOCOL.md.'),
        p('Primary sources: [Michigan index](https://www.sca.isr.umich.edu/), [calendar](https://data.sca.isr.umich.edu/fetchdoc.php?docid=79628), [web transition](https://www.sca.isr.umich.edu/files/methodtransitionannouncement2024.pdf), [2026 methodology](https://www.sca.isr.umich.edu/files/partisaneconomy202607_revised.pdf); [BLS CPS](https://www.bls.gov/cps/) and [shutdown](https://www.bls.gov/cps/methods/2025-federal-government-shutdown-impact-cps.htm); [BEA PCE](https://www.bea.gov/news/2026/personal-income-and-outlays-august-2026), [GDP](https://www.bea.gov/data/gdp/gross-domestic-product); [ALFRED](https://alfred.stlouisfed.org/); [CardiffNLP](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest); [VADER](https://github.com/cjhutto/vaderSentiment); [HN](https://hn.algolia.com/api); [SPY](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-sp-500-etf-trust-spy) and [BIL](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil). [Budak et al. (2016)](https://5harad.com/papers/mediabias.pdf) and [Gentzkow–Shapiro (2010)](https://web.stanford.edu/~gentzkow/research/biasmeas.pdf) define distinct framing/slant constructs, without validating this proxy. Sources, code, provenance, codebook, notebook and AI_USE.md accompany the project; no participants, trades or institutional submission.')]))
    return pages


def slides():
    e = evidence()
    latest = e['primary'].iloc[-1]
    providers = provider_evidence()
    investment, portfolios = investment_evidence()
    adaptive, fixed, spy = [portfolios[model] for model in ['Macro_trend_80_20','Static_60_40','SPY_hold']]
    deck = [
        {'title':'Economic narratives & consumer sentiment',
         'points':['Ahead of the November 2026 midterms','What explains the gap: household pressure, framing, or measurement?','Panagiotis Housos · ph2606'],
         'notes':'This project asks why consumer sentiment can appear weak while headline economic indicators look stronger. The setting is the months before the November 2026 midterm elections, with an information cutoff of October 13. I compare three explanations: pressures that headline indicators miss, selective information or framing, and differences in measurement or timing. The aim is to separate these explanations with evidence. A negative story is not automatically biased, and a pessimistic consumer is not automatically irrational. The practical application is better forecasting and risk monitoring, rather than a presumed media effect.'},
        {'title':'The input audit changes the analysis',
         'points':['October sentiment 46.3 is a verified preliminary release','Q3 GDP 3.7 is unavailable at the cutoff','Workbook PCE does not match official headline PCE','Historical revisions require historical vintages'],
         'notes':'Reading the supplied workbook first exposed three important timing and definition problems. Michigan released the October preliminary sentiment reading of 46.3 on October 9, so that observation is usable despite its month-end label. The Q3 GDP value cannot be used because the official advance release is scheduled for October 29. The August PCE figure in the workbook also differs from official headline inflation. I therefore compute inflation from the headline price index and use historical ALFRED snapshots for the economic predictors. These corrections matter because otherwise later information can appear to explain earlier perceptions.'},
        {'title':'Define the gap with an honest forecast',
         'points':[f'Latest assessed sentiment: {fmt(latest.observed,1)}',f'M1 prediction: {fmt(latest.prediction,1)}',f'Gap: {fmt(latest.gap,1)} index points','Intervals and coverage qualify the result'],
         'image':'economic_forecast',
         'notes':'The economic model uses unemployment, headline year-over-year PCE inflation and the latest published quarterly GDP growth. Each prediction is evaluated chronologically. I define the gap as observed sentiment minus the economic prediction, and I report uncertainty and coverage. A negative residual means that this model predicted more optimism than the survey measured. It does not identify bias. The chart also shows why structural change matters: relationships estimated in earlier years may not describe the pandemic, the inflation surge or the current period. Persistence and household-control models provide important alternatives to the basic three-variable model.'},
        {'title':'Prices and household experience remain plausible',
         'points':['Falling inflation leaves the price level elevated','Real income and cumulative prices are additional controls','Survey mode changed; party and income matter','An unexplained residual is still model-dependent'],
         'image':'recent_gap',
         'notes':'There are good reasons for household experience to differ from national aggregates. Falling inflation means prices are rising more slowly; it does not undo earlier price increases. Real GDP growth says little about a particular household’s housing costs, debt payments or job insecurity. I include real disposable income growth and cumulative prices as manageable alternatives, while acknowledging remaining omissions. Price-level wording does not establish anchoring without individual reference prices or an experimental anchor. Michigan also changed survey collection methods and documents demographic and partisan differences. These considerations can explain part of an apparent gap without any distorted media coverage. A national aggregate should not be presented as the experience of every household.'},
        {'title':'What the media data can measure',
         'points':['Fixed national + local panel, plus Hacker News','Titles measure content supply, not respondent exposure','Tone, salience, framing and attribution are proxies','Factual accuracy requires an official-vintage check'],
         'image':'media_tone',
         'notes':'The media sample uses the same broad economic queries across a fixed national and local outlet panel, plus user-posted story titles on Hacker News. I average within outlets and groups, and show missing sources and sample sizes. The unit is a title, so I do not claim to have measured full arguments or audience exposure. A pinned contextual model and a dictionary provide tone measures. Transparent rules provide salience and framing proxies. A numerical token only identifies a claim worth checking. Without matching the metric, period and available official release, it cannot establish whether a headline is factually wrong.'},
        {'title':'Prediction: compare the same months',
         'points':['M1: economics','M2: economics + lagged media','M3: add household controls','Also compare autoregressive baselines'],
         'image':'model_accuracy',
         'notes':verdict(e) + ' These comparisons use common assessment months so missing media observations do not create an unfair advantage. I also include lagged-sentiment models because persistence is a strong benchmark. The analysis reports forecast errors, interval coverage, coefficient paths and sensitivity checks. Media variables can help predict sentiment by capturing genuine household pressures or shared shocks, even if the coverage is entirely accurate. A lower error therefore supports forecasting usefulness under these measurements, but does not by itself support a media-bias explanation or a causal effect.'},
        {'title':'Validation is a material limitation',
         'points':['Blinded 300-item annotation packet prepared','Independent AI reviews are explicitly AI','Two-human validation remains unmet','No invented accuracy or factual-error rate'],
         'notes':'The final assignment requires at least 300 items independently labeled by two humans. Those human labels are not available. I prepared blinded worksheets, a labeling guide, an adjudication workflow and validation code, and keep any independent AI review clearly identified as AI. It would be misleading to report AI agreement as human agreement or to call dictionary agreement accuracy. Until the human task is actually completed, the media measurements remain provisional. This limitation is displayed in the report and dashboard because it directly affects how much confidence a forecasting team should place in the narrative indicators.'},
        {'title':'Causal impact requires stronger identification',
         'points':['Reverse causality and common shocks remain','Propose random assignment of truthful frames','Measure beliefs, recall and household perceptions','A sample effect is not the national-index effect'],
         'notes':'The chosen causal route is observational analysis with a stronger-design proposal. Pessimistic consumers may seek negative content, publishers may respond to demand, and economic shocks can drive both coverage and sentiment. A feasible experiment would randomly assign equally accurate price-level or inflation-rate framings of the same official information. It would measure baseline beliefs, subsequent perceptions and recall, with pre-registered contrasts and appropriate approval. Even a well-identified effect in that sample would not establish an effect on the national Michigan index. That would also require population exposure estimates, representative weighting and defensible transportability assumptions.'},
        {'title':'Investment conclusion: prefer the simple mix',
         'layout':'wide_chart',
         'subtitle':'Monthly 60% SPY / 40% BIL · January 2015–October 2, 2026 · retrospective after-cost comparison',
         'caption':f"Net CAGR: fixed 60/40 {fmt(100*fixed['net_cagr'])}% · macro/trend {fmt(100*adaptive['net_cagr'])}% · SPY {fmt(100*spy['net_cagr'])}%. Positive history is not alpha or future profit.",
         'points':['Rebalance 60% SPY / 40% BIL monthly',
                   f"Fixed mix: {fmt(100*fixed['net_cagr'])}% CAGR; {fmt(100*fixed['max_drawdown'])}% drawdown",
                   f"Costs: {investment['cost_bps_per_dollar_traded']} bps per dollar traded, entry/exit included",
                   'Test prospectively; provider bars never trade'],
         'image':'investment_strategy',
         'notes':f"The investment extension compares fixed rules, without searching thresholds for profit. The macro/trend rule holds eighty percent equities when trend and as-of labor conditions pass, otherwise twenty percent. From January 2015 through October 2, 2026, it earned {fmt(100*adaptive['net_cagr'])} percent net CAGR. Monthly sixty percent SPY and forty percent BIL earned {fmt(100*fixed['net_cagr'])} percent, with almost the same maximum drawdown. SPY earned {fmt(100*spy['net_cagr'])} percent but suffered a {fmt(abs(100*spy['max_drawdown']),1)} percent drawdown. Costs are ten basis points per dollar traded, including entry and exit. This retrospective comparison favors the simple mix. Neither alpha nor future profitability is established; revised survey and reconstructed media overlays require separate prospective validation."}
    ]
    deck.insert(5,{'title':'Provider comparison: the same economic releases',
        'layout':'wide_chart',
        'subtitle':f'{len(providers)} providers · {int(providers.n_events.iloc[0])} identical releases · {int(providers.n_titles.sum())} headlines · retrieved October 15',
        'caption':'Relative negative framing; zero = peer reference. Conditional resampling ranges omit retrieval and classifier error.',
        'points':['X-axis: CNBC, Fox brands and other providers',
                  'Y-axis: excess negative-headline share, pp',
                  'Zero is a sampled peer benchmark',
                  'Monthly resampling ranges; provisional labels'],
        'image':'provider_bias',
        'notes':'This chart compares providers covering the same official economic releases. The supplement was retrieved October 15; its common-release panel was selected using coverage only. For each release, I calculate the share of negative economic headlines within each provider and subtract the equal-weight average of the other providers. I then average the differences over an identical set of releases. Positive bars mean more negative wording relative to sampled peers. Zero is a reference, not a declaration of neutrality. The intervals resample calendar months and do not capture classifier or retrieval error. Different true components can justify different headlines, and the new providers lack independent human validation. The chart therefore measures a defined relative framing proxy rather than factual dishonesty, ideological bias, audience exposure or an effect on consumer sentiment.'})
    return deck
