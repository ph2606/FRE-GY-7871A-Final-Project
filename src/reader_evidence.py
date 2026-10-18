"""Original figures from explicitly identified published summary statistics.

These are literature exhibits, not participant-level analyses or IQ forecasts.
Run ``python -m src.reader_evidence`` to regenerate the cached summary tables.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.exhibits import _theme, _axis, NAVY, TEAL, RED, SLATE, WARM

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
TABLES = OUT / 'tables'

SOURCES = [
    ('B1', 'Pietschnig & Voracek (2015)', 'Historical IQ-test gains; 271 samples, almost 4 million participants, 31 countries; not a representative annual world series.', 'https://doi.org/10.1177/1745691615577701'),
    ('B2', 'Bratsberg & Rogeberg (2018)', 'Norwegian male cohorts 1962-1991; within-family estimates recover both gains and reversal. Environmental interpretation is specific to that setting.', 'https://doi.org/10.1073/pnas.1718793115'),
    ('B3', 'Kong et al. (2017)', 'Icelandic educational-attainment polygenic score associated with later reproduction and fewer children. Not a global IQ estimate or a comparison of nationalities.', 'https://doi.org/10.1073/pnas.1612113114'),
    ('B4', 'Mani et al. (2013)', 'Experiments on financial concerns and within-farmer pre/post-harvest comparison suggest resource constraints can affect task performance. Not an innate-ability classification.', 'https://doi.org/10.1126/science.1238041'),
    ('B5', 'Bastani et al. (2025), Table 1', 'Classroom-randomized Turkish high-school mathematics study. Published normalized grade coefficients and classroom-clustered standard errors; short-term outcomes.', 'https://doi.org/10.1073/pnas.2422633122'),
    ('B6', 'Lorenz-Spreen et al. (2019)', 'Twitter top-50 hashtag residence time: 17.5 hours in 2013 and 11.9 in 2016. Collective topic turnover, not an individual attention-span measurement.', 'https://doi.org/10.1038/s41467-019-09311-w'),
    ('B7', 'Pennycook & Rand (2022)', '20 US accuracy-prompt experiments, N=26,863; false-news sharing intentions decreased about 10% relative to control. Not lifetime cognitive change.', 'https://doi.org/10.1038/s41467-022-30073-5'),
    ('B8', 'UNFPA (2025), State of World Population', '14-country survey: financial constraints affected desired family size. Survey average is not a census of all world adults.', 'https://www.unfpa.org/swp2025'),
    ('B9', 'UC Berkeley, Understanding Evolution (2020 update)', 'Evolution does not have a universal upward or downward direction defined by human intellectual values.', 'https://evolution.berkeley.edu/evolution-101/the-big-issues/trends-in-evolution/'),
    ('B10', 'World Bank, World Development Indicators', 'Country/world/income-aggregate fertility and crude birth rates. Frozen 1990-2023 observations, common comparison year 2023; separate acquisition manifest.', 'https://data.worldbank.org/indicator/SP.DYN.TFRT.IN'),
    ('B11', 'Nguyen et al. (2025)', 'Short-form video systematic review: 71 studies, 98,299 participants across all outcomes; attention association r=-.38 is not a causal effect or IQ change.', 'https://doi.org/10.1037/bul0000498'),
]


def build():
    OUT.mkdir(exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    plt.rcdefaults()
    _theme()
    ledger = pd.DataFrame(SOURCES, columns=['id', 'source', 'scope_and_boundary', 'primary_url'])
    ledger.to_csv(TABLES / 'reader_evidence_sources.csv', index=False)
    # Transcribed from the corrected published Table 1, not fitted to our data.
    effects = pd.DataFrame([
        ['Standard AI assistant', 'assisted_practice', .137, .031, .284],
        ['Hint-based AI tutor', 'assisted_practice', .361, .032, .284],
        ['Standard AI assistant', 'unassisted_test', -.054, .022, .321],
        ['Hint-based AI tutor', 'unassisted_test', -.004, .013, .321],
    ], columns=['tool', 'outcome', 'coefficient', 'clustered_se', 'control_mean'])
    effects['lower_normal_95'] = effects.coefficient - 1.96 * effects.clustered_se
    effects['upper_normal_95'] = effects.coefficient + 1.96 * effects.clustered_se
    effects['effect_relative_to_control_percent'] = 100 * effects.coefficient / effects.control_mean
    effects['source_id'] = 'B5'
    effects.to_csv(TABLES / 'reader_ai_published_effects.csv', index=False)
    attention = pd.DataFrame({'year': [2013, 2016], 'top50_hashtag_mean_hours': [17.5, 11.9], 'source_id': ['B6', 'B6']})
    attention.to_csv(TABLES / 'reader_attention_published.csv', index=False)
    fig = plt.figure(figsize=(9.4, 3.75), facecolor='white')
    fig.text(.075, .955, 'Using AI well means learning without it', fontsize=15, weight='bold', color=NAVY)
    fig.text(.075, .878, 'Published classroom-randomized mathematics study in one Turkish high school', fontsize=10, color=SLATE)
    ax = fig.add_axes([.25, .25, .67, .51], facecolor=WARM)
    data = effects.loc[effects.outcome.eq('unassisted_test')].reset_index(drop=True)
    for i, row in data.iterrows():
        ax.errorbar(100*row.coefficient, 1-i, xerr=196*row.clustered_se,
                    fmt='o', ms=9, capsize=4, lw=2, color=RED if i == 0 else TEAL)
    ax.axvline(0, color=SLATE, linewidth=1, linestyle='--')
    ax.set_yticks([1, 0], data.tool)
    ax.set_ylim(-.65, 1.65)
    ax.set_xlim(-11, 4)
    ax.set_xlabel('Unassisted test score: change versus no AI (percentage points)', labelpad=10)
    _axis(ax, grid='x')
    ax.text(-5.4, 1.35, '-5.4 points', ha='center', color=RED, weight='bold')
    ax.text(-.4, .35, '-0.4 points', ha='center', color=TEAL, weight='bold')
    fig.text(.075, .065, 'Bastani et al. (2025), Table 1. Lines: approximate 95% intervals = coefficient +/- 1.96 x classroom-clustered SE.\nThese are short-term grade effects, not IQ changes. The tutor estimate is statistically compatible with zero.', fontsize=8.7, color=SLATE)
    for suffix in ['pdf', 'png']:
        metadata = {'CreationDate': None, 'ModDate': None} if suffix == 'pdf' else None
        fig.savefig(OUT / f'reader_ai_learning.{suffix}', dpi=240, metadata=metadata)
    plt.close(fig)
    summary = {
        'status': 'Published summary-statistic transcription; not a new experiment',
        'review_date': '2026-10-18',
        'sources': ledger.to_dict('records'),
        'ai_interval_method': 'Normal approximation using reported classroom-clustered standard errors; no individual data or covariance reanalysis.',
        'attention_boundary': 'Topic turnover cannot identify individual attention-span decline or IQ change.',
        'part_b_status': 'Literature-based argument and prospective research proposal; not an estimated finding from the Michigan/media study.',
        'world_iq_decline_established': False,
        'demographic_data_measure_iq': False,
    }
    (TABLES / 'reader_evidence_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('Built literature ledger, published-effects table and original AI-learning figure.')
    return summary


if __name__ == '__main__':
    build()
