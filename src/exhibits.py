"""Editorial research figures drawn only from acquired, computed observations."""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager, ticker

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
TABLES = OUT / 'tables'
NAVY, TEAL, RED = '#172F43', '#167D8D', '#C77B68'
SLATE, PALE, WARM = '#657787', '#EAF1F4', '#FCFBF8'
GRID = '#E1E9ED'

MODEL_LABELS = {
    'M1_economic': 'M1 · Economic indicators',
    'M2_economic_media': 'M2 · Economics + media',
    'M3_economic_media_controls': 'M3 · Economics + media + household',
    'M1_controls': 'Economics + household controls',
    'AR1': 'AR(1)',
    'AR_macro': 'AR + economic indicators',
    'AR_macro_media': 'AR + economics + media',
    'Persistence': 'Persistence',
}


def _theme():
    available = {font.name for font in font_manager.fontManager.ttflist}
    preferred = next((name for name in ['Aptos', 'Calibri'] if name in available), 'DejaVu Sans')
    plt.rcParams.update({
        'font.family': preferred, 'font.size': 10.5,
        'pdf.fonttype': 42, 'ps.fonttype': 42,
        'figure.facecolor': 'white', 'axes.facecolor': WARM,
        'axes.spines.top': False, 'axes.spines.right': False,
        'axes.spines.left': False, 'axes.spines.bottom': False,
        'axes.labelcolor': SLATE, 'text.color': NAVY,
        'xtick.color': SLATE, 'ytick.color': SLATE,
        'axes.titleweight': 'bold', 'axes.labelsize': 10.3,
        'xtick.labelsize': 10, 'ytick.labelsize': 10,
        'axes.axisbelow': True, 'grid.color': GRID,
        'grid.linewidth': .65, 'grid.alpha': 1,
        'lines.solid_capstyle': 'round',
        'savefig.facecolor': 'white', 'savefig.bbox': None, 'axes.unicode_minus': True,
    })


def _figure(title, subtitle, size=(9.4, 3.2)):
    fig = plt.figure(figsize=size, facecolor='white')
    fig.text(.075, .963, title, ha='left', va='top', fontsize=14.4, weight='bold', color=NAVY)
    fig.text(.075, .889, subtitle, ha='left', va='top', fontsize=10, color=SLATE)
    return fig


def _axis(ax, grid='y'):
    ax.tick_params(axis='both', which='both', length=0, pad=7)
    ax.grid(axis=grid)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5))
    ax.margins(y=.12)
    return ax


def _date_axis(ax, dates, padding_months=0):
    dates = pd.to_datetime(dates)
    if len(dates) == 0:
        return
    years = (dates.max() - dates.min()).days / 365.25
    ax.xaxis.set_major_locator(mdates.YearLocator(2 if years > 5 else 1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_xlim(dates.min() - pd.DateOffset(months=1), dates.max() + pd.DateOffset(months=max(1, padding_months)))


def _legend(ax, columns=3):
    return ax.legend(loc='lower left', bbox_to_anchor=(0, 1.025),
                     ncol=columns, frameon=False, borderaxespad=0,
                     fontsize=9.7, handlelength=2, handletextpad=.6, columnspacing=1.8)


def _endpoint(ax, date, value, label, color, dy=0, fontsize=10.5):
    if not np.isfinite(value):
        return
    ax.plot([date], [value], marker='o', ms=4.3, mfc='white', mec=color, mew=1.3, zorder=6)
    ax.annotate(label, (date, value), xytext=(8, dy), textcoords='offset points',
                ha='left', va='center', color=color, fontsize=fontsize,
                weight='bold', annotation_clip=False)


def _partial_note(frame):
    if 'partial_month' in frame and len(frame) and bool(frame.iloc[-1].partial_month):
        return f' · {pd.Timestamp(frame.iloc[-1].month):%b %Y} is partial'
    return ''


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    # Explicit margins keep label hierarchy and the intended report/slide aspect
    # ratio stable. A tight bounding box would change that ratio between charts.
    fig.savefig(OUT / f'{name}.png', dpi=240, facecolor='white')
    fig.savefig(OUT / f'{name}.pdf', facecolor='white')
    plt.close(fig)


def build():
    _theme()
    forecasts = pd.read_csv(TABLES / 'forecasts.csv')
    p = forecasts[(forecasts.target == 'sentiment') & (forecasts.model == 'M1_economic')].copy()
    p['month'] = pd.to_datetime(p.month)
    p = p[p.month >= '2018-01-01'].sort_values('month')
    fig = _figure('Consumer sentiment and the economic baseline',
                  'Monthly Michigan index · chronological economic-only forecasts')
    ax = _axis(fig.add_axes([.075, .18, .83, .56]))
    lower, upper = 'empirical_lower_95', 'empirical_upper_95'
    band = ax.fill_between(p.month, p[lower], p[upper], color=TEAL, alpha=.13,
                           linewidth=0, label='Empirical 95% interval')
    predicted, = ax.plot(p.month, p.prediction, color=TEAL, lw=1.9, label='M1 economic model')
    observed, = ax.plot(p.month, p.observed, color=NAVY, lw=2.15, label='Observed sentiment')
    ax.set_ylabel('Michigan index', labelpad=12)
    _date_axis(ax, p.month, padding_months=13)
    ax.legend([observed, predicted, band], ['Observed sentiment', 'M1 economic model', 'Empirical 95% interval'],
              loc='lower left', bbox_to_anchor=(0, 1.025), ncol=3, frameon=False,
              borderaxespad=0, fontsize=9.7, handlelength=2, columnspacing=1.8)
    if len(p):
        last = p.iloc[-1]
        _endpoint(ax, last.month, last.observed, f'{last.observed:.1f}  Observed', NAVY)
        _endpoint(ax, last.month, last.prediction, f'{last.prediction:.1f}  M1', TEAL)
    save(fig, 'economic_forecast')

    recent = p[p.month >= '2024-01-01']
    fig = _figure('The sentiment gap, month by month',
                  'Observed minus M1 prediction · index points unexplained under this model')
    ax = _axis(fig.add_axes([.075, .18, .85, .59]))
    ax.bar(recent.month, recent.gap, width=22,
           color=np.where(recent.gap < 0, RED, TEAL), alpha=.92, zorder=3)
    ax.axhline(0, color=NAVY, lw=1, zorder=4)
    ax.set_ylabel('Observed − predicted', labelpad=12)
    _date_axis(ax, recent.month)
    if len(recent):
        last = recent.iloc[-1]
        fig.text(.925, .82, f'{last.month:%b %Y} · {last.gap:+.1f} points',
                 ha='right', va='center', fontsize=10.6,
                 weight='bold', color=NAVY)
    save(fig, 'recent_gap')

    metrics = pd.read_csv(TABLES / 'model_metrics.csv')
    subset = metrics[(metrics.target == 'sentiment') & metrics.model.isin(list(MODEL_LABELS))]
    if 'common' in ' '.join(subset['sample'].astype(str)):
        subset = subset[subset['sample'].str.contains('common')]
    if subset['sample'].nunique() > 1:
        chosen = subset.groupby('sample').model.nunique().idxmax()
        subset = subset[subset['sample'] == chosen]
    subset = subset.drop_duplicates('model').sort_values('rmse', ascending=False)
    sample_note = 'Same evaluation dates · lower error is better'
    if len(subset) and subset.n.nunique() == 1:
        sample_note = f'{int(subset.n.iloc[0])} common evaluation months · lower error is better'
    fig = _figure('Forecast accuracy on the same evaluation dates', sample_note)
    ax = _axis(fig.add_axes([.35, .19, .58, .57]), grid='x')
    y = np.arange(len(subset))
    colors = [TEAL if 'media' in model else NAVY for model in subset.model]
    ax.barh(y, subset.rmse, height=.57, color=colors, zorder=3)
    ax.set_yticks(y, [MODEL_LABELS.get(model, model.replace('_', ' ')) for model in subset.model],
                  fontsize=10.3, color=NAVY)
    ax.tick_params(axis='y', pad=12)
    ax.set_xlabel('Out-of-sample RMSE · Michigan index points', labelpad=10)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5))
    if len(subset):
        maximum = float(subset.rmse.max())
        ax.set_xlim(0, maximum * 1.16)
        for i, row in enumerate(subset.itertuples()):
            ax.text(row.rmse + maximum * .018, i, f'{row.rmse:.3f}', va='center',
                    ha='left', fontsize=10.6, weight='bold', color=NAVY)
    fig.text(.35, .825, 'Media predictor', color=TEAL, fontsize=9.6, weight='bold')
    fig.text(.505, .825, 'Other models', color=NAVY, fontsize=9.6)
    save(fig, 'model_accuracy')

    monthly_path = ROOT / 'data' / 'processed' / 'media_monthly.csv'
    if monthly_path.exists():
        m = pd.read_csv(monthly_path)
        m['month'] = pd.to_datetime(m.month)
        m = m.sort_values('month')
        fig = _figure('Economic wording across the captured media panel',
                      'Source-balanced monthly valence · contextual probability difference; dictionary compound' + _partial_note(m))
        ax = _axis(fig.add_axes([.075, .18, .83, .55]))
        tone = [c for c in m if any(x in c for x in ['tone','valence']) and pd.api.types.is_numeric_dtype(m[c])]
        tone_styles = {
            'media_tone': ('Combined contextual', NAVY, 2.1, '-', 1),
            'vader_tone': ('Dictionary (VADER)', SLATE, 1.3, (0, (2, 2)), .9),
            'national_tone': ('National contextual', TEAL, 1.15, '-', .7),
            'local_tone': ('Local contextual', RED, 1.15, '-', .8),
        }
        for col in tone[:4]:
            label, color, width, dash, alpha = tone_styles.get(col, (col.replace('_', ' '), SLATE, 1.3, '-', .8))
            ax.plot(m.month, m[col], label=label, color=color, lw=width, ls=dash, alpha=alpha)
        ax.axhline(0, color=SLATE, lw=.8, ls=(0, (3, 3)))
        ax.set_ylabel('Wording valence', labelpad=12)
        _date_axis(ax, m.month, padding_months=11)
        if tone:
            _legend(ax, columns=4)
        if 'media_tone' in m and len(m):
            last=m.iloc[-1]
            _endpoint(ax, last.month, last.media_tone, f'{last.media_tone:+.2f}  Combined', NAVY, fontsize=10)
        save(fig, 'media_tone')

        fig = _figure('A fixed panel, uneven monthly capture',
                      'Captured titles and source availability · separate vertical scales' + _partial_note(m), size=(9.4, 3.25))
        upper = _axis(fig.add_axes([.075, .405, .83, .365]))
        lower = _axis(fig.add_axes([.075, .16, .83, .19]), grid='y')
        if 'item_count' in m:
            upper.fill_between(m.month, m.item_count, 0, color=PALE, linewidth=0)
            upper.plot(m.month, m.item_count, color=NAVY, lw=1.8)
            upper.set_ylim(0, float(m.item_count.max()) * 1.17)
            upper.set_ylabel('Sampled titles', labelpad=12)
            upper.yaxis.set_major_locator(ticker.MaxNLocator(nbins=3, integer=True))
            if len(m):
                last=m.iloc[-1]
                _endpoint(upper, last.month, last.item_count, f'{int(last.item_count)} titles', NAVY, fontsize=10)
        availability = [('source_count','Sources',NAVY), ('group_count','Groups',TEAL)]
        for col, label, color in availability:
            if col in m:
                lower.plot(m.month, m[col], color=color, lw=1.55,
                           drawstyle='steps-mid', ls='-' if col=='source_count' else (0,(3,2)))
                if len(m):
                    last=m.iloc[-1]
                    _endpoint(lower, last.month, last[col], f'{int(last[col])} {label.lower()}', color, fontsize=9.7)
        availability_columns = [col for col, _, _ in availability if col in m]
        minimum_available = min([3]+[float(m[col].min()) for col in availability_columns])
        maximum_available = max([7]+[float(m[col].max()) for col in availability_columns])
        lower.set_ylim(minimum_available-.65, maximum_available+.8)
        lower.set_yticks(sorted({int(np.floor(minimum_available)),3,5,7,int(np.ceil(maximum_available))}))
        lower.set_ylabel('Available', labelpad=12)
        for axis in [upper, lower]:
            _date_axis(axis, m.month, padding_months=11)
        upper.tick_params(axis='x', labelbottom=False)
        save(fig, 'media_coverage')

    provider_path = TABLES / 'provider_bias.csv'
    if provider_path.exists():
        data=pd.read_csv(provider_path)
        if 'comparison_status' in data:
            data=data.loc[data.comparison_status.eq('main_common_event_panel')]
        provider_bias_figure(data)
    investment_path = TABLES / 'investment_full_daily.csv'
    if investment_path.exists():
        investment_figure(pd.read_csv(investment_path,parse_dates=['date']))
    print('Publication figures rebuilt.')


def investment_figure(data):
    """Four fixed, costed paths; do not imply the preferred benchmark was primary."""
    _theme()
    fig = _figure('A simpler allocation outperformed the timing rule',
                  'Growth of $100 | Jan 2, 2015 to Oct 2, 2026 | 10 bp per dollar traded, including entry and exit',
                  size=(10.2, 3.6))
    ax = _axis(fig.add_axes([.075,.19,.77,.54]))
    styles=[('SPY_hold','SPY',NAVY,1.65,'-'),
            ('Static_60_40','60% SPY / 40% BIL',TEAL,2.55,'-'),
            ('Macro_trend_80_20','Macro + trend rule',RED,1.8,(0,(4,2))),
            ('BIL_hold','BIL',SLATE,1.3,(0,(2,2)))]
    for model,label,color,width,dash in styles:
        series=data.loc[data.model.eq(model)].sort_values('date')
        ax.plot(series.date,100*series.wealth,color=color,lw=width,ls=dash,label=label)
        last=series.iloc[-1]
        _endpoint(ax,last.date,100*last.wealth,f'${100*last.wealth:.0f}',color,fontsize=10.5)
    _legend(ax,columns=4)
    _date_axis(ax,data.date,padding_months=12)
    ax.set_ylim(80,500)
    ax.set_ylabel('Net portfolio value ($)',labelpad=12)
    fig.text(.075,.045,'Retrospective benchmark preference; adjusted-price proxy. Equity exposure explains gains; future profit is uncertain.',
             fontsize=9.7,color=SLATE)
    save(fig,'investment_strategy')


def provider_bias_figure(data):
    """Vertical, alphabetical provider bars with exact raw resampling ranges."""
    _theme()
    data = data.sort_values('provider').reset_index(drop=True)
    fig = _figure('Economic headlines: same releases, different emphasis',
                  '95% month-resampling stability ranges · zero is the sampled-peer reference',
                  size=(10.2, 4.0))
    ax = _axis(fig.add_axes([.085, .265, .855, .515]))
    if data.empty:
        ax.set_axis_off()
        ax.text(.5, .5, 'Insufficient common-event support\nNo comparable provider bars are available.',
                ha='center', va='center', transform=ax.transAxes, color=SLATE, fontsize=12)
        save(fig, 'provider_bias')
        return
    x = np.arange(len(data))
    ax.bar(x, data.bias_pp, color=NAVY, width=.52, zorder=3, alpha=.94)
    ax.vlines(x, data.lower_95, data.upper_95, color=SLATE, lw=1.45, zorder=4)
    ax.hlines(data.lower_95, x-.06, x+.06, color=SLATE, lw=1.45, zorder=4)
    ax.hlines(data.upper_95, x-.06, x+.06, color=SLATE, lw=1.45, zorder=4)
    ax.scatter(x, data.bias_pp, s=24, facecolor='white', edgecolor=NAVY, lw=1.15, zorder=5)
    ax.axhline(0, color=SLATE, lw=1, zorder=2)
    labels = data.provider.map(lambda value: value.replace('Fox ', 'Fox\n').replace('Wall Street Journal', 'Wall Street\nJournal'))
    ax.set_xticks(x, labels, fontsize=10.8, color=NAVY)
    ax.tick_params(axis='x', pad=9)
    ax.set_xlim(-.55, len(data)-.37)
    ax.set_xlabel('News provider', labelpad=32)
    ax.set_ylabel('Relative negativity bias proxy\n(percentage points vs same-release peers)', labelpad=13)
    low = min(0, float(data.lower_95.min()), float(data.bias_pp.min()))
    high = max(0, float(data.upper_95.max()), float(data.bias_pp.max()))
    span = max(high-low, 10)
    ax.set_ylim(low-.12*span, high+.13*span)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5, steps=[1,2,2.5,5,10]))
    for i, row in enumerate(data.itertuples()):
        displacement = .04*span if row.bias_pp>=0 else -.04*span
        ax.text(i+.115, row.bias_pp+displacement, f'{row.bias_pp:+.1f}',
                ha='left', va='center', fontsize=11.3, weight='bold', color=NAVY,
                bbox={'facecolor':WARM, 'edgecolor':'none', 'pad':1.1}, zorder=6)
        ax.text(i, -.30, f'n = {int(row.n_titles)}', transform=ax.get_xaxis_transform(),
                ha='center', va='center', fontsize=9.8, color=SLATE)
    save(fig, 'provider_bias')


if __name__ == '__main__':
    build()
