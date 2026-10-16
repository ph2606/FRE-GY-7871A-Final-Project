"""Self-contained, updateable Plotly monitoring artifact; no hosting required."""
from pathlib import Path
from html import escape
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'tables'
NAVY, TEAL, RED = '#18354B', '#087E83', '#C05252'


def frame(path):
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def style(fig, title, height=380, ytitle=None):
    fig.update_layout(title=title, template='plotly_white', height=height,
                      font={'family': 'Calibri, Arial', 'color': NAVY},
                      margin={'l': 55, 'r': 25, 't': 65, 'b': 45},
                      legend={'orientation': 'h', 'y': 1.01, 'x': 0},
                      hovermode='x unified', paper_bgcolor='white')
    if ytitle:
        fig.update_yaxes(title=ytitle)
    return fig


def table_html(df, limit=25):
    return df.head(limit).to_html(index=False, border=0, classes='data-table',
                                 na_rep='Unavailable',float_format=lambda x: f'{x:.3f}') if not df.empty else '<p>Unavailable in this snapshot.</p>'


def build():
    forecasts = frame(OUT / 'forecasts.csv')
    metrics = frame(OUT / 'model_metrics.csv')
    monthly = frame(ROOT / 'data' / 'processed' / 'media_monthly.csv')
    macro = frame(ROOT / 'data' / 'processed' / 'monthly_dataset.csv')
    monitoring = frame(OUT / 'monitoring_forecasts.csv')
    monitor = monitoring[monitoring.model.eq('M1_economic')] if not monitoring.empty else monitoring
    media_summary = read_json(ROOT / 'outputs' / 'media_summary.json')
    provider_coverage = frame(OUT / 'provider_bias.csv')
    providers = provider_coverage.copy()
    if 'comparison_status' in providers:
        providers=providers.loc[providers.comparison_status.eq('main_common_event_panel')]
    provider_summary = read_json(OUT / 'provider_bias_summary.json')
    ai = read_json(ROOT / 'outputs' / 'ai_diagnostic_validation_metrics.json')
    figures = []
    if not forecasts.empty:
        primary = forecasts[(forecasts['target'] == 'sentiment') &
                            (forecasts['model'] == 'M1_economic')].sort_values('month')
        fig = go.Figure()
        lower = 'empirical_lower_95' if primary['empirical_lower_95'].notna().sum() >= 12 else 'lower_95'
        upper = lower.replace('lower', 'upper')
        fig.add_trace(go.Scatter(x=primary.month, y=primary[upper], mode='lines',
                                line={'width': 0}, showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=primary.month, y=primary[lower], mode='lines',
                                line={'width': 0}, fill='tonexty', fillcolor='rgba(8,126,131,.14)',
                                name='Empirical 95% interval'))
        fig.add_trace(go.Scatter(x=primary.month, y=primary.prediction,
                                name='M1 prediction', line={'color': TEAL}))
        fig.add_trace(go.Scatter(x=primary.month, y=primary.observed,
                                name='Observed headline', line={'color': NAVY}))
        if not monitor.empty:
            r = monitor.iloc[-1]
            fig.add_trace(go.Scatter(x=[r.month], y=[r.observed_preliminary], mode='markers',
                                    name='October preliminary',
                                    marker={'color': RED,'symbol':'diamond','size':12}))
            fig.add_trace(go.Scatter(x=[r.month], y=[r.prediction], mode='markers',
                                    name='October 1 forecast / interval',
                                    marker={'color':TEAL,'symbol':'circle-open','size':10},
                                    error_y={'type':'data','array':[r.empirical_upper_95-r.prediction],
                                             'arrayminus':[r.prediction-r.empirical_lower_95]}))
        fig.update_xaxes(rangeslider_visible=True)
        figures.append(style(fig, 'Consumer sentiment and economic-model prediction', 470, 'Michigan index'))
        gap = go.Figure(go.Bar(x=primary.month, y=primary.gap,
                              marker_color=np.where(primary.gap < 0, RED, TEAL), name='Observed − predicted'))
        gap.add_hline(y=0, line_color=NAVY, line_width=1)
        if not monitor.empty:
            r = monitor.iloc[-1]
            gap.add_trace(go.Scatter(x=[r.month],y=[r.gap_preliminary],mode='markers',
                                    name='October preliminary gap',marker={'color':RED,'symbol':'diamond','size':11}))
        figures.append(style(gap, 'Sentiment gap: unexplained under M1, without a causal interpretation', 320, 'Index points'))
    if not providers.empty:
        providers = providers.sort_values('provider')
        custom = np.column_stack([providers.n_titles,providers.n_events,providers.lower_95,providers.upper_95])
        fig = go.Figure(go.Bar(x=providers.provider,y=providers.bias_pp,
                    marker_color=NAVY,name='Provider framing proxy',customdata=custom,
                    hovertemplate='%{x}<br>Relative negative framing: %{y:.2f} pp<br>95% resampling range: [%{customdata[2]:.2f}, %{customdata[3]:.2f}]<br>Titles: %{customdata[0]:.0f}<br>Common releases: %{customdata[1]:.0f}<extra></extra>'))
        interval_x,interval_y=[],[]
        for row in providers.itertuples():
            interval_x += [row.provider,row.provider,None]
            interval_y += [row.lower_95,row.upper_95,None]
        fig.add_trace(go.Scatter(x=interval_x,y=interval_y,mode='lines+markers',
                                 line={'color':'#536977','width':1.3},
                                 marker={'symbol':'line-ew','size':9,'color':'#536977'},
                                 showlegend=False,hoverinfo='skip'))
        fig.add_hline(y=0,line_color='#657782',line_width=1)
        fig.update_xaxes(title='News provider')
        fig.update_layout(showlegend=False)
        figures.append(style(fig,'Provider bias proxy: same-release negative framing',450,
                             'Excess negative headlines<br>(percentage points vs same-release peers)'))
    if not monthly.empty:
        candidates = [c for c in monthly if (c.startswith('salience_') or any(t in c.lower() for t in
                      ['tone','valence','negative','price_level','inflation_rate','household','national','forecast','layoff','hiring','recession','political','calibrat'])
                      ) and pd.api.types.is_numeric_dtype(monthly[c])]
        tone = [c for c in candidates if any(t in c.lower() for t in ['tone', 'valence', 'negative'])]
        other = [c for c in candidates if c not in tone]
        for cols, title in [(tone[:8], 'Media tone: measured wording, unvalidated for population beliefs'),
                            (other[:12], 'Framing, issue salience and political-attribution measures')]:
            fig = go.Figure()
            for col in cols:
                fig.add_trace(go.Scatter(x=monthly['month'], y=monthly[col], name=col.replace('_',' ')))
            if cols:
                figures.append(style(fig, title, 390))
        counts = [c for c in ['item_count','source_count','group_count'] if c in monthly]
        fig = go.Figure()
        for col in counts[:10]:
            fig.add_trace(go.Scatter(x=monthly['month'], y=monthly[col], name=col.replace('_',' ')))
        if counts:
            figures.append(style(fig, 'Sample composition and missingness', 350, 'Count / coverage'))
        fig = make_subplots(rows=1,cols=2,subplot_titles=['Numerical-claim eligibility share','Purposive numeric alignment counts'])
        fig.add_trace(go.Scatter(x=monthly.month,y=monthly.numeric_claim_eligible,name='Eligibility; not factual error'),row=1,col=1)
        for col in ['numeric_alignment_checked_count','numeric_alignment_aligned_count']:
            if col in monthly:
                fig.add_trace(go.Bar(x=monthly.month,y=monthly[col],name=col.replace('_',' ')),row=1,col=2)
        figures.append(style(fig,'Factual-calibration diagnostics: corpus accuracy remains unavailable',350))
    if not macro.empty:
        fig = make_subplots(rows=1, cols=3, subplot_titles=['U-3 (%)', 'Headline PCE YoY (%)', 'Latest available real GDP QoQ annualized (%)'])
        for i, col in enumerate(['unemployment','pce_yoy','gdp_qoq_annualized']):
            fig.add_trace(go.Scatter(x=macro.month, y=macro[col], name=col,
                                    line={'color': TEAL}, showlegend=False), row=1, col=i+1)
        figures.append(style(fig, 'Economic inputs available at each monthly prediction origin', 340))
    embedded = []
    for i, fig in enumerate(figures):
        embedded.append(pio.to_html(fig, full_html=False, include_plotlyjs=True if i == 0 else False,
                                   config={'displaylogo': False, 'responsive': True}, div_id=f'chart-{i}'))
    release_path = ROOT / 'docs' / 'release_calendar.json'
    releases = read_json(release_path)
    events = pd.DataFrame(releases.get('events', []))
    latest = read_json(OUT / 'economic_latest.json')
    latest_text = escape(json.dumps(latest, ensure_ascii=False, indent=2))
    html = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Economic Narratives — Pre-election Monitor</title>
<style>body{margin:0;background:#edf2f4;color:#18354b;font:16px Calibri,Arial,sans-serif}main{max-width:1250px;margin:auto;padding:34px 24px}h1{font-size:38px;margin:8px 0}h2{font-size:23px}p{line-height:1.55}.eyebrow{color:#087e83;letter-spacing:1.5px;font-weight:bold}.card{padding:20px 24px;background:white;border-radius:14px;margin:20px 0;box-shadow:0 2px 10px #18354b09}.notice{border-left:5px solid #c05252}.data-table{border-collapse:collapse;width:100%;font-size:14px}.data-table th,.data-table td{padding:9px 12px;border-bottom:1px solid #dce5e8;text-align:left}.scroll{overflow-x:auto}.pill{display:inline-block;background:#dcefee;padding:7px 12px;border-radius:20px;margin:6px 6px 0 0}pre{white-space:pre-wrap;font-size:13px}details{margin-top:12px}a{color:#087e83}</style></head><body><main>
<div class="eyebrow">AI APPLICATIONS IN FINANCE · PANAGIOTIS HOUSOS · ph2606</div>
<h1>Economic narratives & consumer sentiment</h1>
<p>A pre-election monitoring snapshot. Information cutoff: <strong>October 13, 2026</strong> (New York). Election day: November 3, 2026.</p>
<span class="pill">Official economic vintages</span><span class="pill">Retrospective media sample</span><span class="pill">Human validation outstanding</span>
<div class="card notice"><strong>Interpretation and data status</strong><p>A negative sentiment gap is unexplained under the specified model. It does not establish irrational consumers or a media effect. Media variables measure sampled content supply; exposure and cognitive bias are unobserved. The 2026 monitoring period is a snapshot, and partial October data must not be compared with complete months without qualification.</p><p>Factual accuracy has not been established for the corpus: numerical-claim screening is verification eligibility, never an accuracy score. Independent AI annotation is a development diagnostic; the required two-human validation is incomplete. Q3 GDP from the supplied workbook is quarantined until its official release.</p></div>
'''
    html += ''.join('<div class="card">' + x + '</div>' for x in embedded)
    if not providers.empty:
        html += '<div class="card scroll"><h2>How to read the provider comparison</h2><p>Providers are compared on an identical set of official economic releases. Within each release, the negative-headline share for each provider is compared with the equal-weight average of the other providers; release differences are then averaged. Positive bars mean more negative wording in this sample. Zero means the peer reference, not factual neutrality. Error bars resample calendar-month blocks; few months and selected feeds limit precision.</p><p>Different true components of a release can justify different headlines. This proxy combines framing and emphasis; it does not establish factual error, partisan slant, audience exposure or an effect on consumer sentiment. CNBC and Fox provider records are a separate supplement and never change the frozen historical media forecast.</p>'
        html += table_html(providers[['provider','bias_pp','lower_95','upper_95','n_titles','n_events']],20)+'</div>'
        if len(provider_coverage)>len(providers):
            html += '<div class="card scroll"><h2>Provider coverage and comparability</h2><p>Providers outside the identical-release panel receive no comparable bias bar. Missing comparable coverage is never coded as zero or interpreted as ignoring an event.</p>'
            html += table_html(provider_coverage[['provider','comparison_status','n_titles','n_events']],20)+'</div>'
    if not monitor.empty:
        r = monitor.iloc[-1]
        html += '<div class="card"><h2>October preliminary monitoring</h2>'
        html += f'<p>Released October 9: headline <strong>{r.observed_preliminary:.1f}</strong>; October 1 M1 forecast <strong>{r.prediction:.2f}</strong>; gap <strong>{r.gap_preliminary:.2f}</strong> points. Empirical 95% interval [{r.empirical_lower_95:.2f}, {r.empirical_upper_95:.2f}]. This preliminary target is excluded from completed-final model performance.</p></div>'
    factual = media_summary.get('factual_calibration', {})
    html += '<div class="card"><h2>Calibration and independent-review status</h2><p>Human validation: pending; zero completed human pairs. Corpus-wide factual-error rate: unavailable.</p>'
    if isinstance(factual,dict):
        html += '<p>' + escape(factual.get('interpretation','')) + '</p>'
    if ai:
        html += f'<p>Independent AI development review: {ai.get("completed_independent_pairs",0)} original pairs; agreement {100*ai.get("tone_agreement",0):.1f}%, kappa {ai.get("tone_cohens_kappa",0):.3f}. Final-corpus eligible subset: {ai.get("annotation_pool_final_eligible_n",0)}. These are diagnostic concordance statistics and do not satisfy the two-human requirement.</p>'
    html += '</div>'
    html += '<div class="card scroll"><h2>Model performance and interval coverage</h2><p>Models must be compared on the same months. The nominal 95% intervals require empirical coverage checks; structural change can cause undercoverage.</p>' + table_html(metrics,100) + '</div>'
    html += '<div class="card scroll"><h2>Relevant releases and prospective events</h2>' + table_html(events,30) + '</div>'
    html += '<div class="card"><h2>Latest official observation status</h2><details><summary>Show release and vintage details</summary><pre>' + latest_text + '</pre></details></div>'
    html += '<div class="card"><h2>Update procedure</h2><p>From the project folder, run the collection and scoring commands in README, rerun <code>python scripts/03_analyze.py</code>, and rebuild with <code>python scripts/04_build_deliverables.py</code>. Preserve old raw vintages, record the new cutoff, rerun validation, and rebuild the report, notebook and presentation. Changes to methods or codebook require a new version and sensitivity analysis.</p><p>Only official values published by each origin enter the economic forecast. Missing source-months remain missing. A newly acquired media sample can differ because rankings and wording change. No causal national-index estimate is displayed.</p></div></main></body></html>'
    path = ROOT / 'dashboard.html'
    path.write_text(html, encoding='utf-8')
    print(f'Built {path.name} with {len(figures)} interactive figures.')
    return path


if __name__ == '__main__':
    build()
