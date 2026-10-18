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
    names = {'M1_economic':'M1: economy only','M2_economic_media':'M2: economy + headlines',
             'M3_economic_media_controls':'M3: add household pressures',
             'AR1':'Learn from last month’s survey','AR_macro':'Last survey + economy',
             'AR_macro_media':'Last survey + economy + headlines',
             'M1_controls':'Economy + household pressures','Persistence':'Repeat last month’s survey'}
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


def bias_trading_evidence():
    summary = load(T / 'bias_trading_summary.json')
    return summary, {row['model']: row for row in summary['full_metrics']}


def bias_trading_rows(rows):
    names = [('Fade_gap', 'Fade the gap'),
             ('Follow_gap', 'Follow the gap'),
             ('Wait_turn', 'Wait for a turn'), ('SPY_hold', 'Hold ordinary stock fund')]
    return [[label, '$'+f"{rows[model]['terminal_value_10000']:,.0f}",
             fmt(100*rows[model]['net_cagr'])+'%',
             fmt(abs(100*rows[model]['max_drawdown']))+'%'] for model, label in names]


def verdict(e):
    m = e['comparison'].set_index('model')
    if {'M1_economic','M2_economic_media'}.issubset(m.index):
        delta = float(m.loc['M1_economic','rmse'] - m.loc['M2_economic_media','rmse'])
        n = int(m.loc['M2_economic_media','n'])
        text = f'Across the same {n} test months, adding headline tone '
        text += f"{'lowers' if delta > 0 else 'raises'} the forecast-error score by {abs(delta):.2f} survey points."
        if {'AR_macro','AR_macro_media'}.issubset(m.index):
            ar_delta = float(m.loc['AR_macro','rmse'] - m.loc['AR_macro_media','rmse'])
            text += f" When the model also knows last month’s survey, headlines {'lower' if ar_delta > 0 else 'raise'} the score by {abs(ar_delta):.2f} points."
        return text
    return 'There are no matching test months, so we cannot fairly compare forecasts with and without headlines.'


def ai_review_text():
    s=load(ROOT/'outputs/ai_diagnostic_validation_metrics.json')
    if not s:
        return 'Separate AI checks are pending. Accuracy against human answers is unavailable.'
    return (f"The two AI reviews agree on {100*s['tone_agreement']:.1f}% of the original {s['completed_independent_pairs']} titles "
            f"(chance-adjusted agreement, or kappa, {s['tone_cohens_kappa']:.3f}). Later relevance checks retain {s['annotation_pool_final_eligible_n']} "
            f"and exclude {s['annotation_pool_final_excluded_n']}; original judgments are saved. The context-reading model matches both AI reviewers "
            "more often than the word list on the retained positive/neutral/negative items. Mixed or uncertain answers are left out of that comparison, "
            "not forced into a class. The notebook shows results for each class and source. Agreement between machines is not human-checked accuracy.")


def stability_text():
    data=csv('media_rolling_coefficients.csv')
    d=data[(data.model=='M2_economic_media')&(data.variable=='media_tone_lag1')]
    tests=csv('predictive_loss_tests.csv')
    return (f"M2 is rebuilt {len(d)} times. A one-point increase in earlier tone changes its prediction by {d.coefficient.min():.2f} to "
            f"{d.coefficient.max():.2f} survey points, depending on the learning period; the link is positive {int((d.coefficient>0).sum())} times. "
            "Changing signs warn that the link is unstable. "
            "After allowing for three comparisons, statistical checks do not establish a reliable improvement. The notebook checks different time lags, sources and wording rules, "
            "and allows errors in nearby months to be related. Such calculations cannot fix a poorly specified model.")


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
    mix=(f" The events are {sum(str(x).startswith('employment_') for x in ids)} jobs reports and "
         f"{sum(str(x).startswith('cpi_') for x in ids)} consumer-price report.") if ids else ''
    return (f"Same-event comparison: {len(d)} providers, {int(d.n_events.iloc[0])} reports and {int(d.n_titles.sum()):,} headlines.{mix} "
            "Bars show extra negative-headline share compared with the other providers, in percentage points. Each report counts equally. "
            f"The n labels count headlines. Lines show how results vary when the {int(d.n_month_clusters.iloc[0])} months are repeatedly sampled; "
            "they leave out search and AI-label errors.")


def dynamics_text():
    s=load(T/'dynamics_summary.json')
    if not s:
        return 'Long-lasting patterns and major economic changes make simple relationships unreliable; extra checks are in the notebook.'
    diagnostics=s['historical_sentiment_diagnostics']
    metrics={x['model']:x for x in s['metrics']}
    q=max(x['bh_qvalue_within_bandwidth_family'] for x in s['dynamic_loss_tests_hac3'])
    return (f"One month’s sentiment is strongly related to the next: their correlation is {diagnostics['lag1_correlation']:.3f} "
            "on a scale where +1 means a perfect positive relationship. That makes last month’s survey a demanding comparison. "
            "Two statistical checks warn that long-run relationships may shift; their full results are in the notebook. "
            f"A separate test predicts monthly changes instead of levels. Adding headlines changes its error score from "
            f"{metrics['D_macro_AR']['rmse']:.4f} to {metrics['D_macro_AR_media']['rmse']:.4f}, with no reliable improvement.")


def household_control_text(e):
    historical = e['metrics'].loc[(e['metrics'].target == 'sentiment') &
                                  (e['metrics']['sample'] == 'historical_oos')].set_index('model')
    common = e['comparison'].set_index('model')
    return (f"Adding these household measures lowers the long-period error score from {historical.loc['M1_economic','rmse']:.2f} "
            f"to {historical.loc['M1_controls','rmse']:.2f} across {int(historical.loc['M1_controls','n'])} months. "
            f"But in the {int(common.loc['M1_controls','n'])} months with headline data, they score "
            f"{common.loc['M1_controls','rmse']:.2f} versus {common.loc['M1_economic','rmse']:.2f} for M1. "
            "The benefit changes with the period. This does not identify one household pressure as the cause of the gap.")


def media_description_rows(data):
    means = data.mean(numeric_only=True)
    share = lambda name: f'{100*means[name]:.1f}%'
    return [
        ['Tone', f"Score {means['media_tone']:.3f}; {share('negative_share')} negative; "
                 f"{share('emotional_wording_proxy')} flagged emotional words"],
        ['Topic attention', f"{share('salience_housing')} housing; {share('salience_wages')} wages; "
                                 f"{share('salience_layoffs')} layoffs; {share('salience_hiring')} hiring"],
        ['Framing', f"{share('frame_price_level')} price level versus {share('frame_inflation_rate')} inflation rate; "
                    f"{share('frame_household')} household versus {share('frame_national')} national"],
        ['Political credit/blame', f"{share('political_actor_mention')} political mentions; "
                                  f"{share('political_credit_proxy')} credit and {share('political_blame_proxy')} blame word matches"]]


def perturbation_text(summary):
    tests = {row['test']: row for row in summary['perturbation']['variant_comparisons']}
    def result(name):
        row = tests[name]
        return (f"{round(row['n']*row['class_switch_rate'])}/{row['n']} labels "
                f"(average size of score change {row['mean_absolute_tone_delta']:.3f})")
    return (f"Changing political names switched {result('political_name_swap')}; adding a Gothamist name tag switched "
            f"{result('source_prefix_Gothamist')}, and a Reuters prefix {result('source_prefix_Reuters')}. "
            "The scoring therefore hides source names. A changed name can also change meaning, so these checks alone do not prove political unfairness.")


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
    bias, trading = bias_trading_evidence()
    pages = []
    pages.append(('The question and the main findings', [
        p('People can hear that the economy is growing and still worry about paying their bills. This project asks why. The University of Michigan’s consumer sentiment index is a survey score about people’s finances, business conditions and buying plans. Higher means more optimism. A score of 60 does not mean 60% of people are happy; this index is not a percentage or a scale capped at 100.'),
        p('We compare three explanations: household pressures missed by national statistics; the stories people see and how those stories are worded; and problems with the data or forecasting model. Artificial intelligence (AI) software labels headline wording. A negative headline can accurately describe bad news, so negative does not automatically mean biased.'),
        p(f"The first forecasting model, called M1, uses jobs, prices and national output. For the latest completed month, the actual survey score was {fmt(latest.observed,1)} and M1 predicted {fmt(latest.prediction,1)}. The gap is actual minus predicted: {fmt(latest.gap,1)} points. For example, an actual score of 60 minus a prediction of 70 gives a gap of −10. A gap is a model’s mistake, not proof that people are irrational."),
        p(verdict(e) + ' This score gives larger mistakes extra weight; page 4 explains the calculation. The gains are tiny; statistical checks do not establish a reliable improvement. Page 11 compares how providers describe the same news.'),
        table(['What we use','What it can tell us'], [
            ['Economy','Monthly history from 2010; earlier published versions of the jobs, price and output data'],
            ['Headlines',f'{total_items:,} titles in {len(media)} months; national news, local news and Hacker News'],
            ['Study date','Economic information frozen October 13, 2026; October survey/news are incomplete'],
            ['Accuracy checks','AI checks completed; the required two independent human reviewers are still missing'],
            ['Investment tests','Rules, gains, losses and their limits are explained on page 12']], [.24,.76]),
        p(f"A separate historical simulation applies three text-only trading rules to past prices. Starting with $10,000, two finish near ${trading['Fade_gap']['terminal_value_10000']:,.0f} and ${trading['Wait_turn']['terminal_value_10000']:,.0f}; one falls to ${trading['Follow_gap']['terminal_value_10000']:,.0f}. All finish below simply holding a broad stock fund, ${trading['SPY_hold']['terminal_value_10000']:,.0f}. These aggressive rules also suffer larger falls along the way. Making some money is not the same as being a good strategy.")]))
    pages.append(('1. Check what was known at the time', [
        p('A number’s date can mean the month it describes, not the day people first learned it. Using a later release in an earlier prediction would be like answering a quiz after seeing the answers. The spreadsheet has four separate date/value pairs, so they must be joined by the periods they describe.'),
        p('Official jobs data come from the Bureau of Labor Statistics (BLS). Prices and output come from the Bureau of Economic Analysis (BEA). Gross domestic product (GDP) means the country’s total economic output. The Personal Consumption Expenditures (PCE) price index tracks consumer prices. The required headline index includes food and energy; the core index leaves them out.'),
        table(['Spreadsheet issue','What the official records show'],[
            ['October survey: 46.3','A first estimate was released October 9. Keep it for monitoring, separate from completed final months.'],
            ['July–September GDP: 3.7','The first official release is October 29, after our cutoff. Do not use the supplied value.'],
            ['August inflation: 3.00759','All 584 spreadsheet values match core inflation. Required headline inflation is 3.419%, rounded by BEA to 3.4%.'],
            ['October 2025 unemployment missing','BLS did not collect the household survey during the shutdown. Do not invent the missing number.'],
            ['GDP later revised','September 30 updates cannot enter predictions made before that date.']], [.29,.71]),
        p('We use the Federal Reserve’s historical data archive, ALFRED, to recover earlier published versions of the economic numbers. The saved files record request addresses, download times and digital fingerprints that reveal file changes. This makes the economic inputs checkable.'),
        p('There is still a limit: the downloaded Michigan history contains today’s final survey values, not every version originally published. Old headlines may also have been edited or removed. The notebook saves summary results, while detailed data stay local under the course’s no-data-upload rule. A fresh download may not recover exactly the same sample.')]))
    pages.append(('2. Build a fair forecast', [
        p('A forecast is a prediction made before its answer is published. For each target month, we use the economic data available by the end of its first calendar day. We cannot recover every release’s exact hour, so we allow the whole first day. GDP is published quarterly, every three months: keep the latest known quarter until a new release arrives, rather than invent monthly GDP figures.'),
        table(['Input','Meaning and calculation'],[
            ['Unemployment, official U-3 rate','Share of the labor force without a job and actively seeking work. Seasonal adjustment removes recurring calendar patterns.'],
            ['Headline PCE inflation','Percentage price change over twelve months: 100 × (current index / index twelve months earlier − 1). An index rising from 100 to 110 means 10% inflation.'],
            ['Real GDP growth','Output growth after allowing for price changes. Main measure: 100 × [(this quarter / previous quarter)^4 − 1], the annual rate if that quarter’s pace continued.'],
            ['Alternative GDP measure','Compare output with the same quarter a year earlier. This is different from extending one quarter’s pace for a year.'],
            ['Household pressures','Add three years of accumulated price increases and growth in after-tax income after inflation. National averages still miss differences between households.']], [.27,.73]),
        p('The overall survey, its Current Economic Conditions score and its Consumer Expectations score are analyzed separately. Current Economic Conditions describes today; Consumer Expectations asks about the future. These questions cover everyday finances and buying decisions, so unemployment, inflation and GDP cannot be expected to explain everything.'),
        p('Each model learns from months before its prediction month. A simple comparison repeats last month’s survey score. News enters with a one-month delay, and October’s incomplete news cannot be used to make an October 1 prediction. Some survey interviews began in the previous month, so the prediction is before the published score but not necessarily before every interview.'),
        p('Each record keeps the period its number describes and the historical data version used. Missing calendar months cannot be skipped when calculating a twelve-month change. The model adds weighted inputs. Ordinary least squares chooses weights to make earlier squared mistakes as small as possible. The notebook includes the formulas, release records and checks; revised survey histories remain a limitation.')]))
    pages.append(('3. How wrong were the forecasts?', [
        p('M1 learns from at least 60 earlier months of unemployment, headline inflation and GDP. We test it on later months, then move forward and repeat. This is an out-of-sample test: each answer belongs to a later month than the months used for learning.'),
        p('Root mean squared error (RMSE) is a forecast-error score, measured here in survey points. Square each mistake, average the squares, then take the square root. Errors of 3 and 4 points give square root of ((9 + 16) / 2) = 3.54. Bigger errors receive extra weight; lower is better.'),
        figure('economic_forecast','The dark line is the actual survey score; the other line is M1’s earlier prediction. The shaded prediction interval is a plausible range based on earlier errors, not a guarantee. An absent band means too little earlier error history.'),
        p('Across 141 test months, M1’s error score is 12.35 points. Simply repeating last month’s survey scores 4.26, much better. Separate models for current conditions and expectations score 16.50 and 10.44. The three economic inputs alone therefore leave important information out.'),
        p('A range aimed at 95% coverage should contain the answer about 95 times in 100 comparable tests. M1’s formula-based range covers only 72.3% of outcomes. A range built from earlier errors covers 78.4% of 116 usable tests. September’s 48.1 is below the first range, 50.23–91.10, but inside the second, 44.13–97.21. How unusual the gap looks depends on the uncertainty calculation.'),
        p('Mistakes in nearby months are related, and relationships changed around the pandemic and inflation surge. The notebook checks shorter learning windows, seasons, different GDP definitions and survey methods. It also lets a model learn from the previous survey rather than assuming three national statistics are enough.')]))
    pages.append(('4. Other reasons people may feel worse', [
        figure('recent_gap','Each bar is actual sentiment minus M1’s earlier prediction. A bar below zero means M1 expected more optimism. It is not a percentage of irrational people or an estimated media effect.'),
        p('Falling inflation does not mean prices returned to their old level. Suppose a basket rises from $100 to $110, then to $112.20. Inflation slows from 10% to 2%, but the basket still costs 12.2% more than before. We therefore add accumulated price increases and inflation-adjusted household income. Housing costs, debt, inequality and job insecurity can still be missing.'),
        p(household_control_text(e)),
        p('How the survey is collected can also matter. Michigan moved from phone to web, with web shares of 25%, 50%, 75% and 100% from April through July 2024. Allowing a gradual change over those months reduces September’s gap to −3.99; a model that also knows earlier sentiment gives −4.64 instead of M1’s −22.57. Many things changed at once, so this does not prove the survey switch caused the gap. Michigan’s revised July 2026 report still finds low sentiment when comparing the same collection methods.'),
        p('Michigan reports differences by political affiliation, income and stock ownership. Its October description highlights lower-income households and smaller portfolios. These published summaries provide context, not individual records in our dataset. We cannot estimate what a particular political group read, believed or experienced.'),
        p(dynamics_text())]))
    pages.append(('5. What the headline sample represents', [
        p(f'The sample runs from January 2020 through October 12, 2026: {len(completed)} complete months and an incomplete October. National sources are the Associated Press, Reuters and National Public Radio (NPR). Local sources are Gothamist, Texas Tribune and Colorado Sun. Hacker News supplies user-posted story titles. The same search topics cover the economy, inflation, jobs, wages, housing and living costs; searches do not ask only for bad news.'),
        figure('media_coverage','Top: number of captured titles. Bottom: number of available sources and source groups, using a different vertical scale. A missing source does not mean it published no economic news.'),
        p('We measure titles, not complete articles, comments or what survey respondents actually saw. A repeatable computer rule selects at most twelve titles per source per month. First average titles within a source, then sources within each national/local/social group, then give each available group equal weight. A busy publisher therefore cannot dominate just by supplying more headlines.'),
        p('We remove exact duplicates, repeated records, obvious promotions, wrong dates and clearly foreign-only titles. Similar rewritten stories, unknown geography and possible automated posts cannot all be resolved. Hacker News is a selected technology community, not a representative sample of American adults. A vote count seen at download time cannot tell us who saw the original post years earlier.'),
        p('Search feeds rank and limit their results. Headlines can change or disappear, and missing sources can change the measured tone. Content supply means what is published; engagement means actions such as voting; exposure means what a person actually encounters. These are different. The dashboard shows source counts so readers can check whether a change in tone also reflects a change in the sample.')]))
    pages.append(('6. Turn wording into checkable measurements', [
        table(['What we measure','Plain meaning and boundary'],[
            ['Tone','How positive or negative the wording sounds. The model score is positive-wording weight minus negative-wording weight, from −1 to +1.'],
            ['Topic attention (salience)','How much of the captured coverage mentions jobs, layoffs, prices, wages, housing, growth or recession. This is attention within our sample.'],
            ['Framing','Which aspect is emphasized: high prices versus slowing inflation; household experience versus national totals; current conditions versus forecasts.'],
            ['Fact checking (calibration)','Compare a numerical claim with the right official measure, period and information available then. Spotting a number is not checking that it is correct.'],
            ['Political credit/blame','Who is mentioned and who appears to receive credit or blame. Criticizing a politician does not by itself establish bias.']], [.25,.75]),
        p('The coding guide was written before scoring; later changes to headline eligibility are documented. A fixed Cardiff language model reads words in context. We compare it with VADER, a word-list sentiment method. The model was not trained on Michigan survey outcomes. Word-match rules for topics, emotion, framing and blame remain rough indicators awaiting human checks.'),
        p('Bad facts and emotional wording are different: "unemployment rose" can be an accurate, calmly worded report. A model released in 2022 also could not have been used in 2020. Our earlier text scores use that later tool and headlines retrieved now, so they are historical reconstructions, not proof of what a working system could have known then.'),
        p('A fair comparison needs a reference. Page 11 compares providers covering the same official reports. It cannot make every truthful detail identical. Testing equal good/bad economic surprises would also need the forecasts people expected beforehand and a fuller record of what was published. Eight selected unemployment-title percentages match official releases, but incomplete definitions, periods and release times prevent a full accuracy judgment.'),
        table(['Measurement','January–September 2026: average monthly result'], media_description_rows(focus), [.25,.75]),
        p(f"These results use {len(focus)} complete months and {int(focus.item_count.sum())} titles. Each month and source group counts equally; topics can overlap. The {100*focus.negative_share.mean():.1f}% negative measure describes weighted headlines, not unhappy people. Negativity bias means giving bad news extra weight; availability bias means judging by what comes easily to mind; confirmation bias means favoring an existing belief; anchoring means relying on an earlier reference such as an old price. Titles alone cannot show these processes inside readers’ minds."),
        p(perturbation_text(e['media_summary']))]))
    pages.append(('7. What has and has not been checked', [
        p('A label is a reviewer’s judgment, such as negative, neutral or positive. The assignment requires at least 300 items labeled independently by two people. Those completed human labels are unavailable. We prepared the worksheets and instructions and ran separate AI reviews, but machines do not replace the two required people. This is an unfinished assignment requirement.'),
        table(['Check','Current status'],[
            ['300-item human packet','Prepared with different item orders, hidden source/date information and space for evidence.'],
            ['Human agreement','Unavailable until both people judge the items independently.'],
            ['Human-checked accuracy','Unavailable without reliable human reference answers. Matching a word list is not accuracy.'],
            ['Separate AI reviews','Useful for finding possible errors; explicitly identified as AI, not human judgments.'],
            ['Fact-checking accuracy','No verified error rate for the full headline sample. Numerical claims still need official checks.'],
            ['Resolving disagreements','Save both original labels; a later reviewer records a reasoned final decision and supporting words.']], [.29,.71]),
        p('For real human results, report both the share of matching answers and chance-adjusted agreement, called Cohen’s kappa. Precision asks how many items called negative really are negative; recall asks how many genuinely negative items were found. Their combined score is F1; macro-F1 gives each class equal weight. Report each class and source separately, because a strong overall average can hide poor results for one group.'),
        p('A headline may quote someone, use sarcasm, or describe good national news alongside household hardship. Reviewers therefore keep a short quotation supporting their label and distinguish calm bad news from emotional wording. Mixed and uncertain cases need explicit treatment. After using reviews to improve a model, test it on new items that did not guide those changes.'),
        p(ai_review_text())]))
    pages.append(('8. Do headlines improve the prediction?', [
        p('We compare the same test months. M1 uses the economy only. M2 adds the previous month’s headline tone. M3 also adds household income and accumulated prices. These comparisons learn from February 2020 onward, using at least 36 earlier months. They differ from the longer-history M1 chart on page 4. A household-only addition and models using last month’s survey help show what actually adds information.'),
        p('In the table, Months is the number of tests. RMSE is the error score defined on page 4. Mean absolute error (MAE) is the average size of the mistakes, ignoring their signs. Coverage is the share of answers inside a range intended to cover 95%. Lower errors and coverage near 95% are better; a range can also be too wide to be useful.'),
        table(['Forecast rule','Months','RMSE','MAE','Range coverage'],comparison_rows(e),[.44,.08,.14,.14,.20]),
        p('Test months: ' + comp_dates + '. ' + verdict(e)),
        figure('model_accuracy','Error scores for identical test months. Lower bars mean smaller mistakes. The very small gain from headlines does not show that headlines caused survey sentiment to fall.'),
        p(stability_text())]))
    pages.append(('9. What would show cause and effect?', [
        p('Two things moving together does not show which caused which. Job losses may worsen both news and sentiment. Worried readers may seek bad news, and publishers may respond to that demand. Political identity can affect both source choice and survey answers. Monthly national averages cannot separate these paths.'),
        p('The assignment permits an observational study plus a detailed plan for a stronger test. We propose randomly assigning consenting people equally accurate summaries of the same report. One could emphasize high prices, another slowing inflation. Keep the numbers, source, length and reading difficulty the same. Measure beliefs, household outlook and recall before and after. Set the comparisons and sample-size calculation in advance and obtain required approval before recruitment. No participants were recruited here.'),
        p('Random assignment makes the groups comparable on average. Check whether participants understood the framing without misunderstanding the facts. Count everyone in their originally assigned group, report who dropped out, and allow for testing several outcomes. An unrelated summary and a later follow-up help check alternative explanations. These are proposed procedures, not completed experimental results.'),
        table(['Evidence against a media-bias explanation','What it would mean'],[
            ['Headlines add no reliable forecasting gain','The text may add little beyond economic conditions and last month’s survey.'],
            ['Household or survey-method checks shrink the gap','Everyday costs or measurement differences may explain it.'],
            ['Negative headlines accurately describe bad outcomes','Reporting bad news does not establish distorted coverage.'],
            ['Provider differences disappear after expected-news checks','Different surprises may explain different wording.'],
            ['A large enough framing experiment finds no effect','The tested wording may not change beliefs through the proposed route.']], [.54,.46]),
        p('Even a convincing experiment with volunteers would not establish an effect on the national Michigan score. We would also need to know what the wider population saw, recruit or reweight a representative sample, compare the same outcomes, and justify applying the result to other people. The detailed plan, including these assumptions, is in docs/causal_design.md.')]))
    pages.append(('10. Read the provider bars and trading risks', [
        figure('provider_bias',provider_caption()),
        p('A provider with 40% negative headlines versus a 30% average for the others gets +10 percentage points: 40 minus 30. Zero means matching these peers, not perfect neutrality. Average within each provider/report first, compare with the other providers equally, then give each report equal weight. The lines show variation when months are sampled again; they omit search and AI-label errors.'),
        p('The separate October 15, 2026 sample uses six providers and six shared reports. A documented change used coverage counts, not scores, after the original set shared only four. CNBC and the two Fox publications remain separate. Different truthful details can explain different wording; some signs change under other checks. Human validation is missing here, and the earlier AI review had no CNBC or Fox items. The bars do not measure lying, political loyalty or effects on readers.'),
        p('Trading uses a different monthly news gap, B: average the negative-headline percentages for Reuters and NPR, then subtract Colorado Sun. These three sources supply 1,923 titles across 81 complete months; different stories and audiences can explain their differences. Compare last month’s B with the median of the twelve months before it. The median is the middle value after sorting; for twelve values, average the middle two. This news gap never uses the Michigan survey gap.'),
        p('Stocks are ownership shares in companies. An exchange-traded fund (ETF) is a basket of investments traded like a stock. The S&P 500 tracks roughly 500 large American companies; SPY is an ordinary fund tracking it. UPRO aims for three times its daily move; SPXU aims for the opposite three-times daily move. A 1% index rise means targets near +3% and -3%, respectively. BIL lends to the U.S. government for short periods. The aggressive funds magnify exposure internally even though this simulated account does not borrow.'),
        p('The three-times target resets every day. If the index rises 10% and then falls 9.09%, it returns to its start; an ideal three-times upward fund instead loses about 5.45%, before fees. It is not three times the whole-period return. Nearly all invested money can be lost. Yearly growth below is the constant annual rate connecting start and finish, not the gain every year. Worst fall means the largest drop from an earlier peak, not from the starting balance.'),
        p('The dashboard preserves the October 13 economic snapshot, with survey, forecasts and missing-source checks. October 23’s final survey and October 29’s price/output releases remain later updates; election timing alone establishes no cause.')]))
    pages.append(('11. Answers and three text-only trading tests', [
        table(['Required question','What the evidence supports'],[
            ['How measure coverage bias?','Compare the same events; separate tone, topics, framing, facts and political blame. These are still rough content indicators.'],
            ['Impact on Michigan sentiment?','A forecasting link does not show that news caused the national score to fall.'],
            ['How much does the economy explain?','The three inputs leave large errors; last month’s survey often predicts better. Costs and measurement still matter.'],
            ['Which thinking biases are measurable?','We see wording, not readers’ attention, memory or beliefs. Individual thinking biases remain unobserved.'],
            ['Do headlines improve predictions?','Only tiny, statistically unreliable gains on matching test months.'],
            ['What would contradict a media explanation?','Household costs explaining the gap, accurate negative reporting, or no reliable forecasting/experimental effect.']], [.31,.69]),
        p('Only the news gap B chooses these trades. Fade buys the three-times up fund above usual and the down fund below usual. Follow reverses those choices. Wait buys up only when B is above usual but falling, or down when below usual but rising; otherwise it holds the bill fund. A news gap equal to usual, or missing inputs, means bills for all three. The choices never use economic statistics, survey scores or price trends.'),
        figure('bias_trading',
               'October 17, 2026 final revision, after the October 13 economic cutoff. Historical simulation: February 2, 2021 to October 2, 2026. Monthly choices use completed earlier headlines and start earning returns after execution at the first shared-session close after the first calendar day.',
               height='145pt'),
        table(['Rule: same dates/costs','End from $10,000','Yearly growth','Worst fall'],
              bias_trading_rows(trading), [.40,.22,.19,.19]),
        p(f"Costs are {bias['cost_bps']/100:.2f}% per purchase or sale: $1 per $1,000 traded, charged on both legs of a switch and at entry/final exit. Gains include approximated reinvested distributions. Two rules made money, yet all three grew less and fell more than the ordinary stock fund. Waiting held bills in {bias['rule_fund_counts']['Wait_turn']['BIL']} of {bias['allocation_periods']} decisions. Historical profit alone does not make these better investments."),
        p('Rules were fixed before calculating these returns, after earlier findings were known. Reconstructed headlines, later software and revised prices prevent a claim that these signals were available then. Human validation, taxes, market impact and an untouched future test are missing. Full rules and comparisons: docs/BIAS_TRADING_PROTOCOL.md; older allocation tests remain in the notebook.'),
        p('Sources: [Michigan](https://www.sca.isr.umich.edu/), [BLS](https://www.bls.gov/cps/), [BEA](https://www.bea.gov/data), [ALFRED](https://alfred.stlouisfed.org/), [CardiffNLP](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest), [VADER](https://github.com/cjhutto/vaderSentiment), [ProShares](https://www.proshares.com/our-etfs/leveraged-and-inverse/upro); [Budak et al. (2016)](https://5harad.com/papers/mediabias.pdf), [Gentzkow-Shapiro (2010)](https://web.stanford.edu/~gentzkow/research/biasmeas.pdf). Full references and methods: docs/sources.md and protocols. Terms: docs/READING_GUIDE.md. AI help: AI_USE.md.')]))

    return pages


def slides():
    e = evidence()
    latest = e['primary'].iloc[-1]
    providers = provider_evidence()
    bias, trading = bias_trading_evidence()
    deck = [
        {'title':'The economy and how people feel',
         'points':['Sentiment = people’s outlook for money and big purchases',
                   'A survey score of 60 does not mean 60% are happy',
                   'Test costs, news wording and measurement problems',
                   'Panagiotis Housos · ph2606'],
         'notes':'People can hear that the economy is growing and still struggle with their bills. This project asks why. Consumer sentiment means people’s outlook for their finances and the economy. Michigan measures it with a survey score. Higher means more optimism, but it is not a percentage or a scale capped at one hundred. We compare three possibilities: pressures national statistics miss, the stories people see, and problems with measurement. Artificial intelligence, or AI, labels headline wording. It does not tell us what readers believe. The economic study stops at October 13, before the November election.'},
        {'title':'Use only what was known then',
         'points':['Inflation = how quickly prices rise',
                   'GDP, gross domestic product = national output',
                   'A month’s date is not necessarily its release date',
                   'Later information cannot enter earlier forecasts'],
         'notes':'Imagine answering a quiz after seeing the answer sheet. A forecast has the same problem if it uses information published later. We therefore check each release date and recover earlier published economic data. The October survey score of 46.3 was first released October 9, so it is available for monitoring. But July-to-September output was not due until October 29, after the cutoff. The spreadsheet’s inflation series also leaves out food and energy, while this assignment requires the broader measure. Jobs, prices and output must all be measured consistently before we ask whether the news explains anything.'},
        {'title':'The gap is a forecast mistake',
         'points':['M1 = a model using jobs, prices and output',
                   'Actual 60 − predicted 70 = gap of −10',
                   f"Latest actual {fmt(latest.observed,1)} − predicted {fmt(latest.prediction,1)} = {fmt(latest.gap,1)}",
                   'Shaded range = uncertainty, not a guarantee'],
         'image':'economic_forecast',
         'notes':'The first model, M1, learns how unemployment, prices and output related to earlier surveys. Then it predicts a later month. The gap means actual minus predicted. If actual sentiment is sixty and the forecast is seventy, the gap is minus ten. That means the model expected too much optimism. It does not prove that people are irrational or that the media misled them. The shaded band shows a plausible range, based on earlier forecast mistakes. The model often misses that range, which warns that it leaves important information out. Simply using last month’s survey is a strong comparison.'},
        {'title':'Slower inflation still leaves high prices',
         'points':['A basket costs $100 → $110 → $112.20',
                   'Inflation slows from 10% to 2%; prices stay higher',
                   'Income, housing costs and debts also matter',
                   'Survey collection changed from phone to web'],
         'image':'recent_gap',
         'notes':'Suppose a shopping basket costs one hundred dollars, then one hundred ten, then one hundred twelve dollars and twenty cents. Inflation slows from ten percent to two percent, but the basket still costs much more than before. That is why the study adds accumulated prices and income after inflation. National output also misses a household’s rent, debts and job worries. Michigan changed from phone interviews to web collection during 2024. Allowing for that change shrinks the model’s gap, but many things changed together, so it cannot prove the survey method caused it. These alternatives remain plausible without assuming distorted news.'},
        {'title':'A headline sample is not an audience',
         'points':['National news + local news + Hacker News',
                   'One title is not a full article or a reader’s belief',
                   'Tone describes wording; truth needs fact checking',
                   'Published does not mean seen by survey respondents'],
         'image':'media_tone',
         'notes':'The sample combines national and local news with titles shared on Hacker News, a technology community. The same broad searches cover jobs, prices, wages, housing and the economy. They do not search only for negative stories. Each source and source group receives balanced weight, so a large publisher cannot win by supplying more headlines. Software estimates positive or negative wording, and simple word rules flag topics and frames. But a calmly worded report of job losses can be both negative and true. Titles can change or disappear, and we do not know which ones survey respondents actually saw.'},
        {'title':'Provider bars compare wording, not truth',
         'layout':'wide_chart',
         'subtitle':f'{len(providers)} providers · {int(providers.n_events.iloc[0])} shared reports · {int(providers.n_titles.sum())} headlines · separate October 15 sample',
         'caption':'40% negative − 30% peer average = +10 percentage points. Zero means matching these peers, not perfect neutrality.',
         'points':['Compare the same reports across providers',
                   'Higher bar = more negative wording than peers',
                   'Lines show variation from this small sample',
                   'AI labels have not been checked by humans here'],
         'image':'provider_bias',
         'notes':'These bars compare providers covering the same official reports. Suppose forty percent of one provider’s headlines are called negative, while the others average thirty percent. Forty minus thirty is ten percentage points, so its bar is plus ten. Each report gets equal weight. Zero means matching these sampled peers, not being perfectly neutral. The lines show how the result varies when we repeatedly sample the observed months. They leave out missing-headline and AI-label errors. Providers can truthfully emphasize different details, such as wages or unemployment. There are only six shared reports and no human validation for this provider sample. The bars do not measure dishonesty, political loyalty or effects on readers.'},
        {'title':'Do headlines improve the forecast?',
         'points':['M1: economy only', 'M2: add last month’s headline tone',
                   'M3: also add household income and prices',
                   'Compare every model on the same months'],
         'image':'model_accuracy',
         'notes':'We compare forecasts using exactly the same test months. The error score is called root mean squared error, or RMSE. Square each mistake, average those squares, then take the square root. This gives large mistakes extra weight. Lower is better. '+verdict(e)+' These are very small gains, and statistical checks do not establish a reliable improvement. Models that know the previous survey do much better than the basic economic model. Even a useful headline signal could reflect real household pressures or shared shocks; it would not prove that news caused sentiment to fall.'},
        {'title':'Two human reviewers are still missing',
         'points':['300 titles prepared for independent human judgments',
                   'AI reviewers do not replace those two people',
                   '92% AI agreement is not human-checked accuracy',
                   'Save evidence and resolve disagreements openly'],
         'notes':'A label is a judgment such as negative, neutral or positive. The assignment requires two people to label at least three hundred items independently. Those completed human labels are still missing. We prepared different-order worksheets, hidden source information and an evidence guide. Two AI reviewers agreed on ninety-two percent of the original three hundred titles, but machines can share the same mistake. Their agreement is not accuracy checked against people. Later relevance checks retain two hundred seventy-seven of those titles. The notebook separates results by source and label, and the report clearly identifies this unfinished requirement.'},
        {'title':'How could wording change beliefs?',
         'points':['Randomly assign equally true versions of one report',
                   'Keep numbers, source and length the same',
                   'Compare beliefs before and after reading',
                   'A volunteer-sample effect is not a national effect'],
         'notes':'Two things moving together does not prove cause and effect. Bad economic news can lower both headline tone and sentiment. Worried people may also seek bad news. A stronger test would randomly assign consenting volunteers different truthful summaries of the same report, perhaps high prices versus slowing inflation. Keep the facts and length the same and compare beliefs before and after. Set the plan and required sample size in advance, and obtain approval before recruiting. No participants were recruited here. Even an effect in volunteers would require evidence about the wider population’s exposure and representativeness before explaining the national survey.'},
        {'title':'Three trading ideas: one news signal',
         'layout':'strategy_rules',
         'intro':'News score = average negative % for Reuters and NPR, minus Colorado Sun’s negative %.\nCompare last month with the middle of the twelve months before it.',
         'funds':'UPRO: 3x daily up   •   SPXU: 3x daily down   •   BIL: short government loans\nSPY: ordinary fund tracking roughly 500 large U.S. companies',
         'cards':[
             ('FADE','Bet against the score','Above usual → UPRO\nBelow usual → SPXU'),
             ('FOLLOW','Follow the score','Above usual → SPXU\nBelow usual → UPRO'),
             ('WAIT','Wait for a reversal','High and falling → UPRO\nLow and rising → SPXU\nOtherwise → BIL')],
         'example':'Teaching example: usual +10; last score +20; preceding score +25.\nThe score is high and falling: Fade buys UPRO; Follow buys SPXU; Wait buys UPRO.',
         'caption':'October 17 retrospective extension. The 3x targets reset daily; nearly all invested money can be lost. Equal or missing scores mean BIL.',
         'points':['Stocks = company shares; funds = baskets. SPY tracks roughly 500 large American companies',
                   'UPRO = three-times daily up; SPXU = three-times daily down; BIL = short government loans',
                   'News gap = national minus local negative-headline shares; usual = prior twelve-month middle',
                   'Fade: above usual buys up, below buys down. Follow: reverse those choices.',
                   'Wait: above-and-falling buys up; below-and-rising buys down; otherwise bills. Ties/missing: bills.'],
         'notes':'The news gap is national minus local negative wording, not the survey gap. Compare last month’s score with the middle of the previous twelve scores. The screen shows three fixed ideas: fade unusual negativity, follow it, or wait for it to turn. UPRO targets three times a broad stock index’s daily rise; SPXU targets the opposite. BIL holds government bills; SPY is an ordinary stock fund. Daily reset means three times daily is not three times the whole month.'},
        {'title':'More risk did not produce better growth',
         'layout':'wide_chart',
         'subtitle':'Start with $10,000 | February 2021 to October 2, 2026 | same dates and trading costs',
         'caption':'Worst fall is measured from an earlier high, not the starting balance. All three news rules grew less and fell more than holding ordinary stocks.',
         'points':['Fade and Wait made money, but lagged ordinary stocks',
                   'Follow lost most of the starting money',
                   'Costs: 0.10% on each purchase and sale',
                   'These reconstructed histories do not prove future profit'],
         'image':'bias_trading',
         'notes':f"Starting with ten thousand dollars, Fade finishes near {trading['Fade_gap']['terminal_value_10000']:,.0f}; Follow near {trading['Follow_gap']['terminal_value_10000']:,.0f}; Wait near {trading['Wait_turn']['terminal_value_10000']:,.0f}. Ordinary stocks finish near {trading['SPY_hold']['terminal_value_10000']:,.0f}. The news rules suffer peak-to-later falls of about sixty-four, eighty-nine and thirty-four percent. A fall is measured from an earlier high, not the initial balance. Two rules made money, but all three grew less and fell more than ordinary stocks. Costs are one dollar per thousand bought or sold, including entry and exit. The headlines and model were reconstructed later, and human checks remain missing. Nothing here proves future profit."}

    ]
    return deck
