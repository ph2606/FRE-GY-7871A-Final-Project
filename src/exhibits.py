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
        counts = [c for c in m if any(x in c for x in ['count','_n','n_','outlets']) and pd.api.types.is_numeric_dtype(m[c])]
        fig, ax = plt.subplots(figsize=(9.4,2.9))
        for col in counts[:4]:
            ax.plot(m.month,m[col],label=col.replace('_',' '),lw=1.2)
        if counts: ax.legend(ncol=2,fontsize=9,frameon=False)
        ax.grid(axis='y'); ax.set_ylabel('Sample / source count')
        save(fig, 'media_coverage')
    print('Publication figures rebuilt.')
