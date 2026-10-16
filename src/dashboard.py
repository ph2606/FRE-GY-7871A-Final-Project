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
NAVY, TEAL, RED = '#172F43', '#167D8D', '#C77B68'
SLATE, PALE, PAPER = '#657787', '#EAF1F4', '#FCFBF8'
COLORWAY = [TEAL, NAVY, RED, SLATE, '#8CAFB5', '#A48E79', '#798B9B', '#B7AAA0']


def frame(path):
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def style(fig, title, height=410, ytitle=None):
    fig.update_layout(title={'text':title,'x':0,'xanchor':'left','y':.97,
                             'font':{'family':'Georgia, Times New Roman, serif','size':23,'color':NAVY}},
                      template='plotly_white', height=height,
                      font={'family': 'Segoe UI, Arial, sans-serif', 'size':12, 'color': SLATE},
                      colorway=COLORWAY,
                      margin={'l':64,'r':38,'t':78,'b':92},
                      legend={'orientation':'h','y':-.18,'yanchor':'top','x':0,
                              'font':{'size':11,'color':SLATE},'tracegroupgap':8,
                              'traceorder':'normal',
                              'itemclick':'toggle','itemdoubleclick':'toggleothers'},
                      hovermode='x unified', paper_bgcolor=PAPER, plot_bgcolor=PAPER,
                      hoverlabel={'bgcolor':'#FFFFFF','bordercolor':'#D8E3E8',
                                  'font':{'family':'Segoe UI, Arial, sans-serif','color':NAVY,'size':12}},
                      bargap=.34, separators='.,')
    fig.update_xaxes(showgrid=False,zeroline=False,showline=False,
                     tickfont={'size':11,'color':SLATE},automargin=True)
    fig.update_yaxes(gridcolor='#E5ECEF',gridwidth=1,zeroline=False,showline=False,
                     tickfont={'size':11,'color':SLATE},title_font={'size':12,'color':SLATE},
                     automargin=True,nticks=5)
    fig.update_annotations(font={'family':'Segoe UI, Arial, sans-serif','size':12,'color':SLATE})
    if ytitle:
        fig.update_yaxes(title_text=ytitle)
    return fig


def table_html(df, limit=25):
    if df.empty:
        return '<p class="muted">Unavailable in this snapshot.</p>'
    display = df.head(limit).copy()
    labels = {'provider':'Provider','bias_pp':'Relative negativity · pp',
              'lower_95':'Range · lower','upper_95':'Range · upper','n_titles':'Titles',
              'n_events':'Releases','comparison_status':'Comparison status','model':'Model',
              'n':'Months','start':'First month','end':'Last month','rmse':'RMSE','mae':'MAE',
              'coverage_95':'Approx. 95% coverage','empirical_coverage_95':'Empirical 95% coverage'}
    for column in ['coverage_95','empirical_coverage_95']:
        if column in display:
            display[column] = display[column].map(lambda value:f'{100*value:.1f}%' if pd.notna(value) else 'Unavailable')
    display = display.rename(columns={c:labels.get(c,c.replace('_',' ').capitalize()) for c in display})
    return display.to_html(index=False,border=0,classes='data-table',na_rep='Unavailable',
                           float_format=lambda x:f'{x:,.3f}')


def date_axes(fig):
    fig.update_xaxes(tickformat='%b<br>%Y',nticks=8)
    return fig


def media_tone_figure(monthly):
    """Keep signed tone and negative-class shares on separate, labeled scales."""
    fig = make_subplots(rows=1,cols=2,horizontal_spacing=.12,column_widths=[.6,.4],
                        subplot_titles=['Directional wording · signed score','Titles classified negative · share'])
    tone_specs = [('media_tone','Overall tone',TEAL,True,'solid'),
                  ('national_tone','National tone',NAVY,'legendonly','solid'),
                  ('local_tone','Local tone',SLATE,'legendonly','solid'),
                  ('social_tone','Social tone',RED,'legendonly','solid'),
                  ('vader_tone','Dictionary tone',RED,'legendonly','dash'),
                  ('media_tone_all_groups','Complete-group tone','#8CAFB5','legendonly','dot')]
    share_specs = [('negative_share','Negative share',NAVY,True,'solid'),
                   ('national_negative_share','National negative share',TEAL,'legendonly','solid'),
                   ('local_negative_share','Local negative share',SLATE,'legendonly','solid'),
                   ('social_negative_share','Social negative share',RED,'legendonly','solid'),
                   ('vader_negative_share','Dictionary negative share',RED,'legendonly','dash')]
    for specs,column in [(tone_specs,1),(share_specs,2)]:
        for key,label,color,visible,dash in specs:
            if key not in monthly:
                continue
            fig.add_trace(go.Scatter(x=monthly.month,y=monthly[key],name=label,visible=visible,
                                    line={'color':color,'width':2.6 if visible is True else 1.8,'dash':dash},
                                    hovertemplate=label+': %{y:.3f}<extra></extra>'),row=1,col=column)
    style(fig,'Media wording, with the scales kept separate',480)
    fig.add_hline(y=0,line_color='#A8B8C2',line_width=.8,row=1,col=1)
    fig.update_yaxes(title_text='P(positive) − P(negative)',rangemode='tozero',row=1,col=1)
    fig.update_yaxes(title_text='Share of sampled titles',tickformat='.0%',range=[0,1],row=1,col=2)
    date_axes(fig)
    fig.update_layout(legend={'y':-.23,'font':{'size':10}},margin={'b':128})
    return fig


def media_dimensions_figure(monthly):
    """Use a view selector instead of overlapping unrelated proxy families."""
    groups = {
        'Framing': [('frame_price_level','Price levels'),('frame_inflation_rate','Inflation rates'),
                    ('frame_household','Household experience'),('frame_national','National aggregates'),
                    ('frame_forecast','Forecasts'),('frame_current','Current conditions'),
                    ('price_level_minus_inflation_frame','Price-level minus rate contrast')],
        'Issue salience': [('salience_housing','Housing'),('salience_rising_prices','Rising prices'),
                          ('salience_hiring','Hiring'),('salience_recession','Recession'),
                          ('salience_layoffs','Layoffs'),('salience_falling_inflation','Falling inflation'),
                          ('salience_growth','Growth'),('salience_wages','Wages')],
        'Attribution': [('political_actor_mention','Political actor mentioned'),
                        ('political_credit_proxy','Credit proxy'),('political_blame_proxy','Blame proxy'),
                        ('actor_president','President / administration'),('actor_democrats','Democrats'),
                        ('actor_republicans','Republicans'),('actor_fed','Federal Reserve'),
                        ('actor_congress','Congress'),('credit_word_proxy','Credit wording'),
                        ('blame_word_proxy','Blame wording'),('emotional_wording_proxy','Emotional wording')],
    }
    fig=go.Figure(); trace_groups=[]; positions=[]
    for family,specs in groups.items():
        for index,(key,label) in enumerate(specs):
            if key not in monthly:
                continue
            trace_groups.append(family);positions.append(index)
            visible = (True if index<3 else 'legendonly') if family=='Framing' else False
            fig.add_trace(go.Scatter(x=monthly.month,y=monthly[key],name=label,visible=visible,
                                    line={'color':COLORWAY[index%len(COLORWAY)],'width':2.2,
                                          'dash':'dash' if index>=len(COLORWAY) else 'solid'},
                                    hovertemplate=label+': %{y:.3f}<extra></extra>'))
    buttons=[]
    for family in groups:
        visibility=[(True if position<3 else 'legendonly') if group==family else False
                    for group,position in zip(trace_groups,positions)]
        buttons.append({'label':family,'method':'update',
                        'args':[{'visible':visibility},{'yaxis.title.text':'Share / framing contrast'}]})
    style(fig,'Framing, issue salience & attribution',470,'Share / framing contrast')
    fig.update_layout(updatemenus=[{'buttons':buttons,'direction':'down','x':1,'xanchor':'right',
                                   'y':1.21,'yanchor':'top','showactive':True,
                                   'bgcolor':PAPER,'bordercolor':'#D7E2E7',
                                   'font':{'size':11,'color':NAVY},'pad':{'r':0,'t':0}}],
                      legend={'y':-.21},margin={'t':100,'b':110})
    fig.update_yaxes(tickformat='.0%',rangemode='tozero')
    return date_axes(fig)


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
        interval_name='Empirical 95% interval' if lower.startswith('empirical') else 'Approximate 95% interval'
        fig.add_trace(go.Scatter(x=primary.month, y=primary[lower], mode='lines',
                                line={'width':0},fill='tonexty',fillcolor='rgba(22,125,141,.11)',
                                name=interval_name,hoverinfo='skip',legendrank=30))
        fig.add_trace(go.Scatter(x=primary.month, y=primary.prediction,
                                name='M1 economic prediction',line={'color':TEAL,'width':2.4},legendrank=20,
                                hovertemplate='M1 prediction: %{y:.2f}<extra></extra>'))
        fig.add_trace(go.Scatter(x=primary.month, y=primary.observed,
                                name='Observed headline',line={'color':NAVY,'width':2.4},legendrank=10,
                                hovertemplate='Observed final: %{y:.1f}<extra></extra>'))
        if not monitor.empty:
            r = monitor.iloc[-1]
            fig.add_trace(go.Scatter(x=[r.month], y=[r.observed_preliminary], mode='markers',
                                    name='October preliminary',legendrank=40,
                                    marker={'color':RED,'symbol':'diamond','size':10,
                                            'line':{'color':PAPER,'width':1.5}},
                                    hovertemplate='October preliminary: %{y:.1f}<extra></extra>'))
            fig.add_trace(go.Scatter(x=[r.month], y=[r.prediction], mode='markers',
                                    name='October 1 forecast / interval',legendrank=50,
                                    marker={'color':TEAL,'symbol':'circle-open','size':10},
                                    error_y={'type':'data','array':[r.empirical_upper_95-r.prediction],
                                             'arrayminus':[r.prediction-r.empirical_lower_95],
                                             'color':TEAL,'thickness':1.3,'width':5},
                                    hovertemplate='October 1 M1 forecast: %{y:.2f}<extra></extra>'))
        fig.update_xaxes(rangeslider={'visible':True,'thickness':.085,'bgcolor':PALE,
                                      'bordercolor':'#D7E2E7','borderwidth':1})
        style(fig,'Consumer sentiment, observed & expected',530,'Michigan index points')
        fig.update_layout(legend={'y':1.04,'yanchor':'bottom'},margin={'t':112,'b':85})
        figures.append(date_axes(fig))
        gap = go.Figure(go.Bar(x=primary.month, y=primary.gap,
                              marker_color=np.where(primary.gap < 0, RED, TEAL),name='Observed − M1 prediction',
                              hovertemplate='Observed − predicted: %{y:.2f} points<extra></extra>'))
        gap.add_hline(y=0,line_color=SLATE,line_width=1)
        if not monitor.empty:
            r = monitor.iloc[-1]
            gap.add_trace(go.Scatter(x=[r.month],y=[r.gap_preliminary],mode='markers',
                                    name='October preliminary gap',marker={'color':RED,'symbol':'diamond','size':11}))
        figures.append(date_axes(style(gap,'The sentiment gap under M1',360,'Observed − predicted · points')))
    if not providers.empty:
        providers = providers.sort_values('provider')
        custom = np.column_stack([providers.n_titles,providers.n_events,providers.lower_95,providers.upper_95])
        fig = go.Figure(go.Bar(x=providers.provider,y=providers.bias_pp,
                    marker_color=NAVY,name='Provider framing proxy',customdata=custom,
                    marker_line={'color':PAPER,'width':1},
                    hovertemplate='<b>%{x}</b><br>Relative negative framing: %{y:.2f} pp<br>Conditional 95% resampling range: [%{customdata[2]:.2f}, %{customdata[3]:.2f}]<br>Titles: %{customdata[0]:.0f}<br>Common releases: %{customdata[1]:.0f}<extra></extra>'))
        interval_x,interval_y=[],[]
        for row in providers.itertuples():
            interval_x += [row.provider,row.provider,None]
            interval_y += [row.lower_95,row.upper_95,None]
        fig.add_trace(go.Scatter(x=interval_x,y=interval_y,mode='lines+markers',
                                 line={'color':SLATE,'width':1.6},
                                 marker={'symbol':'line-ew','size':10,'color':SLATE},
                                 showlegend=False,hoverinfo='skip'))
        fig.add_hline(y=0,line_color=SLATE,line_width=1,line_dash='dot')
        fig.update_xaxes(title_text='News provider · alphabetical',categoryorder='array',
                         categoryarray=providers.provider.tolist(),tickangle=0)
        fig.update_layout(showlegend=False,hovermode='closest')
        figures.append(style(fig,'Provider framing: relative to the same-release peers',460,
                             'Excess negative headlines<br>percentage points vs peers'))
    if not monthly.empty:
        figures.append(media_tone_figure(monthly))
        figures.append(media_dimensions_figure(monthly))
        counts = [c for c in ['item_count','source_count','group_count'] if c in monthly]
        fig=make_subplots(specs=[[{'secondary_y':True}]])
        partial=monthly.partial_month.fillna(False).astype(bool) if 'partial_month' in monthly else pd.Series(False,index=monthly.index)
        if 'item_count' in monthly:
            fig.add_trace(go.Bar(x=monthly.month,y=monthly.item_count,name='Sampled titles · left axis',
                                marker_color=np.where(partial,RED,'#D0E0E5'),
                                customdata=np.where(partial,'Partial month','Completed month'),
                                hovertemplate='Titles: %{y:.0f}<br>%{customdata}<extra></extra>'),secondary_y=False)
        for key,label,color,dash in [('source_count','Outlets · right axis',TEAL,'solid'),
                                     ('group_count','Source groups · right axis',NAVY,'dash')]:
            if key in monthly:
                fig.add_trace(go.Scatter(x=monthly.month,y=monthly[key],name=label,
                                        line={'color':color,'width':2.2,'dash':dash},
                                        hovertemplate=label.split(' · ')[0]+': %{y:.0f}<extra></extra>'),secondary_y=True)
        if counts:
            style(fig,'Sample size & source coverage',400)
            fig.update_yaxes(title_text='Sampled titles',rangemode='tozero',tickformat=',.0f',secondary_y=False)
            fig.update_yaxes(title_text='Outlets / source groups',rangemode='tozero',dtick=1,
                             showgrid=False,secondary_y=True)
            figures.append(date_axes(fig))
        fig = make_subplots(rows=1,cols=2,horizontal_spacing=.13,
                            subplot_titles=['Screened numerical claims','Purposive numeric alignment checks'])
        fig.add_trace(go.Scatter(x=monthly.month,y=monthly.numeric_claim_eligible,
                                name='Eligibility · not factual error',line={'color':TEAL,'width':2.4}),row=1,col=1)
        for col in ['numeric_alignment_checked_count','numeric_alignment_aligned_count']:
            if col in monthly:
                fig.add_trace(go.Bar(x=monthly.month,y=monthly[col],
                                    name='Claims checked' if 'checked' in col else 'Numerically aligned',
                                    marker_color=NAVY if 'checked' in col else RED),row=1,col=2)
        style(fig,'Calibration: eligibility is not accuracy',410)
        fig.update_layout(barmode='group')
        fig.update_yaxes(title_text='Share of sampled titles',tickformat='.0%',rangemode='tozero',row=1,col=1)
        fig.update_yaxes(title_text='Claims · purposive subset',dtick=1,rangemode='tozero',row=1,col=2)
        figures.append(date_axes(fig))
    if not macro.empty:
        fig = make_subplots(rows=1,cols=3,horizontal_spacing=.09,
                            subplot_titles=['U-3 unemployment','Headline PCE · year on year','Real GDP · QoQ annualized'])
        for i, col in enumerate(['unemployment','pce_yoy','gdp_qoq_annualized']):
            fig.add_trace(go.Scatter(x=macro.month, y=macro[col], name=col,
                                    line={'color':[NAVY,TEAL,RED][i],'width':2.2},showlegend=False,
                                    hovertemplate='%{y:.2f}%<extra></extra>'),row=1,col=i+1)
        style(fig,'Economic information available at each forecast origin',370)
        fig.update_yaxes(ticksuffix='%')
        fig.update_layout(margin={'b':56})
        figures.append(date_axes(fig))
    embedded = []
    for i, fig in enumerate(figures):
        embedded.append(pio.to_html(fig, full_html=False, include_plotlyjs=True if i == 0 else False,
                                   config={'displaylogo':False,'responsive':True,'displayModeBar':'hover',
                                           'modeBarButtonsToRemove':['lasso2d','select2d'],
                                           'toImageButtonOptions':{'format':'png','scale':2}},div_id=f'chart-{i}'))
    release_path = ROOT / 'docs' / 'release_calendar.json'
    releases = read_json(release_path)
    events = pd.DataFrame(releases.get('events', []))
    latest = read_json(OUT / 'economic_latest.json')
    latest_text = escape(json.dumps(latest, ensure_ascii=False, indent=2))
    html = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Economic Narratives — Pre-election Monitor</title>
<style>
:root{--ink:#172F43;--teal:#167D8D;--coral:#C77B68;--slate:#657787;--pale:#EAF1F4;--paper:#FCFBF8;--rule:#DCE5E9}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:25px}
body{margin:0;background:var(--pale);color:var(--ink);font:15px/1.65 "Segoe UI",Arial,sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:1328px;margin:auto;padding:40px 40px 64px}a{color:var(--teal);text-underline-offset:3px}
.masthead{display:flex;justify-content:space-between;gap:20px;padding-bottom:18px;border-bottom:1px solid #C7D6DE;color:var(--slate);font-size:11px;letter-spacing:1.7px;text-transform:uppercase}
.masthead strong{font-weight:650;color:var(--ink)}.folio{text-align:right;white-space:nowrap}
.hero{padding:45px 0 29px}.eyebrow,.section-label{font-size:10px;letter-spacing:1.8px;font-weight:650;text-transform:uppercase;color:var(--teal)}
h1{font:400 clamp(38px,4.6vw,61px)/1.08 Georgia,"Times New Roman",serif;letter-spacing:-1.8px;margin:15px 0 18px;max-width:960px}
h1 span{color:var(--teal)}.hero-description{font-size:16px;color:var(--slate);max-width:760px;line-height:1.65;margin:0}
.status-line{display:flex;flex-wrap:wrap;gap:9px;margin-top:22px}.pill{display:inline-flex;align-items:center;gap:8px;padding:6px 11px;border:1px solid #D1DEE5;background:#F4F7F8;font-size:11px;letter-spacing:.12px;border-radius:3px;color:var(--slate)}
.pill:before{content:"";width:5px;height:5px;background:var(--teal);border-radius:50%}.pill.review:before{background:var(--coral)}.pill.retrospective:before{background:var(--slate)}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border:1px solid #D2DEE5;background:var(--paper);margin:3px 0 25px;border-radius:8px;overflow:hidden}
.stat{padding:24px 27px 23px}.stat+.stat{border-left:1px solid var(--rule)}.stat-label{font-size:10px;letter-spacing:1.4px;text-transform:uppercase;color:var(--slate)}
.stat-value{font:400 42px/1.05 Georgia,"Times New Roman",serif;letter-spacing:-1.1px;margin:9px 0;color:var(--ink);font-variant-numeric:tabular-nums}.stat-value.teal{color:var(--teal)}.stat-value.coral{color:var(--coral)}.stat-note{font-size:11px;line-height:1.5;color:var(--slate)}
.card{background:var(--paper);padding:28px 31px;border:1px solid #DCE5E9;border-radius:8px;margin:20px 0;box-shadow:0 3px 13px #172F4303}
.chart-card{padding:23px 25px 19px;scroll-margin-top:25px;overflow:hidden}.card-header{display:flex;align-items:center;justify-content:space-between;gap:20px;margin:0 5px 12px}.interaction-hint{font-size:10px;letter-spacing:.2px;color:#82929E}
h2{font:400 25px/1.25 Georgia,"Times New Roman",serif;letter-spacing:-.3px;margin:0 0 15px}p{margin:12px 0;color:#425A6B;line-height:1.75}.muted,.chart-note{color:var(--slate)}
.chart-note{font-size:11px;line-height:1.65;padding-top:15px;margin:6px 6px 0;border-top:1px solid var(--rule);max-width:1120px}
.notice{border-left:3px solid var(--coral);padding:24px 28px;margin-bottom:27px}.notice strong{font-size:12px;letter-spacing:.2px}.notice p{font-size:12px;line-height:1.75;margin:8px 0;color:#536977}
.jump-nav{display:flex;gap:6px;flex-wrap:wrap;padding:0 0 3px;margin:26px 0 5px}.jump-nav a{font-size:11px;text-decoration:none;border:1px solid #D1DEE5;padding:7px 12px;border-radius:3px;background:transparent;color:var(--ink);transition:background .18s,border-color .18s}
.jump-nav a:hover,.jump-nav a:focus-visible{background:var(--paper);border-color:var(--teal);outline:none}.jump-nav .nav-label{align-self:center;color:var(--slate);font-size:10px;text-transform:uppercase;letter-spacing:1.3px;margin-right:6px}
.data-table{border-collapse:collapse;width:100%;font-size:11px;line-height:1.5;font-variant-numeric:tabular-nums;margin-top:17px;background:transparent}
.data-table th{color:var(--ink);background:#F0F4F5;font-size:10px;letter-spacing:.3px;font-weight:650;white-space:nowrap;border-top:1px solid #CBD9E0;border-bottom:1px solid #CBD9E0;padding:11px 13px;text-align:left!important}
.data-table td{padding:11px 13px;border-bottom:1px solid #E3EAED;color:#536977;vertical-align:top}.data-table tbody tr:nth-child(even){background:#F8F9F7}.data-table tbody tr:hover{background:#EDF3F4}.data-table td:first-child{color:var(--ink);font-weight:500}
.scroll{overflow-x:auto}pre{white-space:pre-wrap;word-break:break-word;font:11px/1.65 Consolas,monospace;background:#EFF3F4;border:1px solid var(--rule);padding:18px;border-radius:4px;color:#425A6B}
details{margin-top:17px}summary{cursor:pointer;color:var(--teal);font-size:12px;font-weight:600;padding:7px 0}summary:focus-visible{outline:2px solid var(--teal);outline-offset:3px}code{font:12px Consolas,monospace;background:#ECF1F3;padding:2px 5px;border-radius:3px}
.table-note{font-size:12px;color:var(--slate)}.page-footer{display:flex;justify-content:space-between;gap:20px;border-top:1px solid #C7D6DE;margin-top:37px;padding-top:18px;font-size:10px;color:var(--slate);letter-spacing:.3px}
.js-plotly-plot .plotly .modebar{background:transparent!important}.js-plotly-plot .plotly .modebar-btn path{fill:#657787!important}
@media(max-width:720px){main{padding:22px 14px 38px}.masthead{font-size:9px;letter-spacing:.8px}.folio{display:none}.hero{padding:31px 5px 24px}h1{font-size:39px;letter-spacing:-1.2px}.hero-description{font-size:14px}.stats{grid-template-columns:1fr}.stat{padding:17px 21px}.stat+.stat{border-left:0;border-top:1px solid var(--rule)}.stat-value{font-size:34px}.card{padding:22px 18px}.chart-card{padding:18px 6px 17px}.card-header{padding:0 10px}.interaction-hint{display:none}.chart-note{margin:6px 13px 0}.notice{padding:20px}.jump-nav{gap:5px}.jump-nav a{font-size:10px;padding:6px 9px}.jump-nav .nav-label{width:100%}.page-footer{flex-direction:column;gap:5px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.jump-nav a{transition:none}}
</style></head><body><main>
<div class="masthead"><strong>AI Applications in Finance · Research monitor</strong><span class="folio">Panagiotis Housos · ph2606</span></div>
<header class="hero"><div class="eyebrow">Economic narratives · Fall 2026</div>
<h1>Economic narratives<br><span>& consumer sentiment</span></h1>
<p class="hero-description">A pre-election monitoring snapshot of economic conditions, consumer assessments and the language of economic news. Information cutoff: <strong>October 13, 2026</strong> (New York). Election day: November 3, 2026.</p>
<div class="status-line"><span class="pill">Official economic vintages</span><span class="pill retrospective">Retrospective media sample</span><span class="pill review">Human validation outstanding</span></div></header>
'''
    if not forecasts.empty and not primary.empty:
        recent=primary.iloc[-1]
        period=pd.Timestamp(recent.month).strftime('%B %Y')
        html += f'''<div class="stats" aria-label="Latest completed final-month assessment">
<div class="stat"><div class="stat-label">Latest final sentiment</div><div class="stat-value">{recent.observed:.1f}</div><div class="stat-note">Michigan index · {escape(period)}</div></div>
<div class="stat"><div class="stat-label">Economic-model prediction</div><div class="stat-value teal">{recent.prediction:.1f}</div><div class="stat-note">M1 · information available at the month’s forecast origin</div></div>
<div class="stat"><div class="stat-label">Model-specific sentiment gap</div><div class="stat-value coral">{recent.gap:+.1f}</div><div class="stat-note">Index points · observed minus M1 prediction</div></div></div>'''
    html += '''<div class="card notice"><strong>Interpretation and data status</strong><p>A negative sentiment gap is unexplained under the specified model. It does not establish irrational consumers or a media effect. Media variables measure sampled content supply; exposure and cognitive bias are unobserved. The 2026 monitoring period is a snapshot, and partial October data must not be compared with complete months without qualification.</p><p>Factual accuracy has not been established for the corpus: numerical-claim screening is verification eligibility, never an accuracy score. Independent AI annotation is a development diagnostic; the required two-human validation is incomplete. Q3 GDP from the supplied workbook is quarantined until its official release.</p></div>'''
    sections=['Sentiment','The gap','Providers','Media wording','Frames & salience','Sample coverage','Calibration','Economic inputs']
    notes=[
        'Historical survey targets are latest-final observations, not historical target vintages. The interval uses earlier forecast errors and is not guaranteed to achieve 95% coverage. October diamonds are preliminary; they are excluded from completed-final assessment.',
        'A negative bar is unexplained pessimism under this economic specification. It is a model residual, not a percentage of biased consumers or a causal media effect.',
        'Providers are alphabetical, with one color for the same metric across every brand. Lines preserve the exact conditional month-resampling ranges. Zero is the same-release peer reference, not objective neutrality; interpretation and coverage details follow below.',
        'Signed tone and negative-class shares have separate scales. Click muted legend entries to show source groups or dictionary sensitivities. These are unvalidated content measures, not population beliefs or actual exposure. October is incomplete.',
        'Choose Framing, Issue salience or Attribution using the view selector. Muted legend entries retain additional dimensions. Shares describe sampled titles; the price-level minus rate contrast is a difference in shares. Literal proxies are unvalidated, and an actor mention is not credit or blame.',
        'Title counts use the left axis; outlet and source-group counts use the right. The coral title bar marks incomplete October. Availability in this captured sample does not establish what survey respondents encountered.',
        'Numerical-claim screening indicates eligibility for review, never factual accuracy. Alignment counts concern a purposive subset and do not identify a corpus-wide error rate.',
        'Each value is the latest released information in that forecast origin’s macro vintage. GDP remains quarterly, without interpolation. Reference-period age is measured from the period’s start, separately from publication timing.'
    ]
    html += '<nav class="jump-nav" aria-label="Monitor sections"><span class="nav-label">Explore the evidence</span>'
    html += ''.join(f'<a href="#panel-{i}">{escape(label)}</a>' for i,label in enumerate(sections[:len(embedded)]))+'</nav>'
    for i,chart in enumerate(embedded):
        html += f'<section class="card chart-card" id="panel-{i}" aria-label="{escape(sections[i])}"><div class="card-header"><span class="section-label">{i+1:02d} / {escape(sections[i])}</span><span class="interaction-hint">Drag to zoom · double-click to reset</span></div>{chart}<p class="chart-note">{escape(notes[i])}</p></section>'
    if not providers.empty:
        html += '<div class="card scroll"><h2>How to read the provider comparison</h2><p>This separate supplement was retrieved October 15, 2026, after the October 13 economic cutoff, and covers January–September releases. A coverage-only amendment selected the displayed panel after the initial mandatory core failed the six-event support threshold; no sentiment score selected its providers.</p><p>Providers are compared on an identical set of official economic releases. Within each release, the negative-headline share for each provider is compared with the equal-weight average of the other providers; release differences are then averaged. Positive bars mean more negative wording in this sample. Zero means the peer reference, not factual neutrality. Error bars are conditional month-resampling stability ranges, not guaranteed population confidence intervals; selected feeds and few fixed months limit generalization.</p><p>Different true components of a release can justify different headlines. This proxy combines framing and emphasis; it does not establish factual error, partisan slant, audience exposure or an effect on consumer sentiment. Retrieval and classifier error are outside the plotted ranges. The supplement never changes the frozen historical media forecast.</p>'
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
    html += '<div class="card scroll"><h2>Model performance and interval coverage</h2><p>Models must be compared on the same months. The nominal 95% intervals require empirical coverage checks; structural change can cause undercoverage.</p>'
    common_metrics=metrics.loc[(metrics['sample']=='common_media_oos') & metrics.target.eq('sentiment')] if not metrics.empty else metrics
    if not common_metrics.empty:
        first=common_metrics.iloc[0]
        span=f'{pd.Timestamp(first.start):%B %Y}–{pd.Timestamp(first.end):%B %Y}'
        html += f'<p class="table-note"><strong>Common headline assessment:</strong> {int(first.n)} months · {escape(span)}. All models below use the same assessment dates.</p>'
        columns=[c for c in ['model','n','rmse','mae','coverage_95','empirical_coverage_95'] if c in common_metrics]
        html += table_html(common_metrics[columns],100)
        html += '<details><summary>All model, outcome and sample results</summary>'+table_html(metrics,100)+'</details>'
    else:
        html += table_html(metrics,100)
    html += '</div>'
    html += '<div class="card scroll"><h2>Relevant releases and prospective events</h2>' + table_html(events,30) + '</div>'
    html += '<div class="card"><h2>Latest official observation status</h2><details><summary>Show release and vintage details</summary><pre>' + latest_text + '</pre></details></div>'
    html += '<div class="card"><h2>Update procedure</h2><p>From the project folder, run the collection and scoring commands in README, rerun <code>python scripts/03_analyze.py</code>, and rebuild with <code>python scripts/04_build_deliverables.py</code>. Preserve old raw vintages, record the new cutoff, rerun validation, and rebuild the report, notebook and presentation. Changes to methods or codebook require a new version and sensitivity analysis.</p><p>Only official values published by each origin enter the economic forecast. Missing source-months remain missing. A newly acquired media sample can differ because rankings and wording change. No causal national-index estimate is displayed.</p></div><footer class="page-footer"><span>Panagiotis Housos · ph2606 · AI Applications in Finance</span><span>Local research artifact · October 13 economic snapshot</span></footer></main></body></html>'
    path = ROOT / 'dashboard.html'
    path.write_text(html, encoding='utf-8')
    print(f'Built {path.name} with {len(figures)} interactive figures.')
    return path


if __name__ == '__main__':
    build()
