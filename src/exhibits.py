"""Publication figures drawn only from acquired, computed observations."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
TABLES = OUT / 'tables'
NAVY, TEAL, RED = '#18354B', '#087E83', '#C05252'


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / f'{name}.png', dpi=190, bbox_inches='tight', facecolor='white')
    fig.savefig(OUT / f'{name}.pdf', bbox_inches='tight', facecolor='white')
    plt.close(fig)


def build():
    plt.rcParams.update({'font.family': 'Calibri', 'font.size': 10,
                         'pdf.fonttype':42,'ps.fonttype':42,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.labelcolor': NAVY, 'text.color': NAVY,
                         'axes.titleweight': 'bold', 'grid.alpha': .16})
    forecasts = pd.read_csv(TABLES / 'forecasts.csv')
    p = forecasts[(forecasts.target == 'sentiment') & (forecasts.model == 'M1_economic')].copy()
    p['month'] = pd.to_datetime(p.month)
    p = p[p.month >= '2018-01-01'].sort_values('month')
    fig, ax = plt.subplots(figsize=(9.4,3.2))
    lower, upper = 'empirical_lower_95', 'empirical_upper_95'
    ax.fill_between(p.month, p[lower], p[upper], color=TEAL, alpha=.13, label='Empirical 95% interval')
    ax.plot(p.month, p.prediction, color=TEAL, lw=1.6, label='M1 economic prediction')
    ax.plot(p.month, p.observed, color=NAVY, lw=1.6, label='Observed sentiment')
    ax.set_ylabel('Michigan index'); ax.grid(axis='y')
    ax.legend(loc='upper center', bbox_to_anchor=(.5,1.17), ncol=3, frameon=False, fontsize=9)
    save(fig, 'economic_forecast')
    recent = p[p.month >= '2024-01-01']
    fig, ax = plt.subplots(figsize=(9.4,2.9))
    ax.bar(recent.month, recent.gap, width=20, color=np.where(recent.gap < 0, RED, TEAL))
    ax.axhline(0,color=NAVY,lw=.8); ax.set_ylabel('Observed − M1 prediction'); ax.grid(axis='y')
    save(fig, 'recent_gap')
    metrics = pd.read_csv(TABLES / 'model_metrics.csv')
    subset = metrics[(metrics.target == 'sentiment') & metrics.model.isin(['M1_economic','M2_economic_media','M3_economic_media_controls','M1_controls','AR1','AR_macro','AR_macro_media','Persistence'])]
    if 'common' in ' '.join(subset['sample'].astype(str)):
        subset = subset[subset['sample'].str.contains('common')]
    if subset['sample'].nunique() > 1:
        chosen = subset.groupby('sample').model.nunique().idxmax()
        subset = subset[subset['sample'] == chosen]
    fig, ax = plt.subplots(figsize=(9.4,3.2))
    subset = subset.drop_duplicates('model').sort_values('rmse',ascending=False)
    ax.barh(subset.model.str.replace('_',' '), subset.rmse, color=[TEAL if 'media' in x else NAVY for x in subset.model])
    ax.set_xlabel('Out-of-sample RMSE, Michigan index points'); ax.grid(axis='x')
    save(fig, 'model_accuracy')
    monthly_path = ROOT / 'data' / 'processed' / 'media_monthly.csv'
    if monthly_path.exists():
        m = pd.read_csv(monthly_path)
        m['month'] = pd.to_datetime(m.month)
        fig, ax = plt.subplots(figsize=(9.4,3.1))
        tone = [c for c in m if any(x in c for x in ['tone','valence']) and pd.api.types.is_numeric_dtype(m[c])]
        for col in tone[:4]:
            ax.plot(m.month, m[col], label=col.replace('_',' '), lw=1.4)
        ax.axhline(0, color=NAVY,lw=.7); ax.grid(axis='y'); ax.set_ylabel('Mean wording score')
        if tone: ax.legend(ncol=2,fontsize=9,frameon=False)
        save(fig, 'media_tone')
        counts = [c for c in ['item_count','source_count','group_count'] if c in m]
        fig, ax = plt.subplots(figsize=(9.4,2.9))
        for col in counts[:4]:
            ax.plot(m.month,m[col],label=col.replace('_',' '),lw=1.2)
        if counts: ax.legend(ncol=2,fontsize=9,frameon=False)
        ax.grid(axis='y'); ax.set_ylabel('Sample / source count')
        save(fig, 'media_coverage')
    provider_path = TABLES / 'provider_bias.csv'
    if provider_path.exists():
        d=pd.read_csv(provider_path)
        if 'comparison_status' in d:
            d=d.loc[d.comparison_status.eq('main_common_event_panel')]
        provider_bias_figure(d)
    print('Publication figures rebuilt.')


def provider_bias_figure(data):
    """Vertical provider bars: user-requested axes and explicit peer benchmark."""
    data = data.sort_values('provider').reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10.2,4.2))
    x = np.arange(len(data))
    ax.bar(x,data.bias_pp,color=NAVY,width=.62,zorder=3)
    ax.vlines(x,data.lower_95,data.upper_95,color='#536977',lw=1.25,zorder=4)
    ax.hlines(data.lower_95,x-.065,x+.065,color='#536977',lw=1.25,zorder=4)
    ax.hlines(data.upper_95,x-.065,x+.065,color='#536977',lw=1.25,zorder=4)
    ax.axhline(0,color='#657782',lw=1,zorder=2)
    ax.set_xticks(x,labels=data.provider.str.replace(' ','\n'))
    ax.set_xlabel('News provider',labelpad=8)
    ax.set_ylabel('Relative negativity bias proxy\n(percentage points vs same-release peers)',labelpad=9)
    ax.grid(axis='y',zorder=0)
    ax.set_title('Economic headlines: same releases, different emphasis',loc='left',pad=28,fontsize=13)
    ax.text(0,1.025,'Matched 2026 releases · 95% month-resampling ranges · zero = peer reference',
            transform=ax.transAxes,fontsize=9,color='#536977')
    lo = min(0,data.lower_95.min());hi=max(0,data.upper_95.max())
    span = max(hi-lo,10)
    ax.set_ylim(lo-.18*span,hi+.18*span)
    for i,r in enumerate(data.itertuples()):
        ax.text(i,lo-.10*span,f'n={int(r.n_titles)}',ha='center',va='center',fontsize=8.5,color='#536977')
    save(fig,'provider_bias')
