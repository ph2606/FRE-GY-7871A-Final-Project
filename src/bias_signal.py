"""Fixed, retrospective wording-proxy signals; no prices or return calculations.

The word ``bias`` in this module's name denotes a proposed relative-framing
proxy. Negative wording is not a verified factual error or an investment edge.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NATIONAL_SOURCES = ('Reuters', 'NPR')
LOCAL_SOURCE = 'Colorado Sun'
ROSTER = NATIONAL_SOURCES + (LOCAL_SOURCE,)
FIRST_MONTH = pd.Timestamp('2020-01-01')
LAST_MONTH = pd.Timestamp('2026-09-01')
FIRST_ORIGIN = pd.Timestamp('2021-02-01')
LAST_ORIGIN = pd.Timestamp('2026-09-01')
BASELINE_MONTHS = 12
EPS = 1e-10
LONG_FUND, INVERSE_FUND, NEUTRAL_FUND = 'UPRO', 'SPXU', 'BIL'
SOURCE_KEYS = {'Reuters':'reuters', 'NPR':'npr', 'Colorado Sun':'colorado_sun'}


def _month_dates(values, name):
    dates = pd.DatetimeIndex(pd.to_datetime(values, errors='raise'))
    if dates.hasnans or dates.tz is not None:
        raise ValueError(f'{name} must contain nonmissing, timezone-naive calendar months')
    if not (dates == dates.to_period('M').to_timestamp()).all():
        raise ValueError(f'{name} must use the first calendar day at midnight')
    return dates


def monthly_spread(scores: pd.DataFrame) -> pd.DataFrame:
    """Aggregate final-eligible title classes on a fixed 81-month, three-outlet grid.

    Required columns: month, source, contextual_class. Optional id is checked
    for duplicates. Existing eligibility is retained; no new geographic,
    industry, macroeconomic, price or emotional-word filter is introduced.
    Any absent roster outlet makes that month's bias_pp missing, never zero.
    """
    required = {'month','source','contextual_class'}
    missing = required.difference(scores.columns)
    if missing:
        raise ValueError(f'Missing score columns: {sorted(missing)}')
    selected = scores.loc[scores.source.isin(ROSTER)].copy()
    selected['month'] = _month_dates(selected.month, 'month')
    selected = selected.loc[selected.month.between(FIRST_MONTH,LAST_MONTH)]
    if 'id' in selected and (selected.id.isna().any() or selected.id.duplicated().any()):
        raise ValueError('Final-eligible title IDs must be present and unique')
    for column in ['exclusion_reason','post_sample_exclusion_reason']:
        if column in selected and selected[column].fillna('').astype(str).str.strip().ne('').any():
            raise ValueError('Use final-eligible scores, not excluded candidates')
    classes = selected.contextual_class
    if not classes.isin(['negative','neutral','positive']).all():
        raise ValueError('Each retained title needs a frozen negative/neutral/positive class')
    selected['_negative'] = classes.eq('negative').astype(int)
    grouped = selected.groupby(['month','source'])['_negative'].agg(['sum','count'])
    result = pd.DataFrame(index=pd.date_range(FIRST_MONTH,LAST_MONTH,freq='MS',name='month'))
    for source in ROSTER:
        key = SOURCE_KEYS[source]
        if source in grouped.index.get_level_values('source'):
            counts = grouped.xs(source,level='source').reindex(result.index)
        else:
            counts = pd.DataFrame(index=result.index,columns=['sum','count'],dtype=float)
        result[f'{key}_n'] = counts['count'].fillna(0).astype(int)
        result[f'{key}_negative_share'] = counts['sum']/counts['count']
    count_columns = [f'{SOURCE_KEYS[source]}_n' for source in ROSTER]
    result['n_titles'] = result[count_columns].sum(axis=1)
    result['source_count'] = result[count_columns].gt(0).sum(axis=1)
    result['complete_roster'] = result.source_count.eq(len(ROSTER))
    result['national_negative_share'] = (
        result.reuters_negative_share+result.npr_negative_share)/2
    result['local_negative_share'] = result.colorado_sun_negative_share
    result['bias_pp'] = (100*(result.national_negative_share-result.local_negative_share)
                         ).where(result.complete_roster)
    return result.reset_index()


def origin_signals(monthly: pd.DataFrame, origins) -> pd.DataFrame:
    """Select funds using only completed-month wording and earlier calendar months.

    Origins are first calendar days in February 2021 through September 2026.
    For origin t, m=t-1 month. The reference is median(B[m-12],...,B[m-1]),
    excluding B[m]. Missing required months or equality within EPS means BIL.
    Calendar gaps are never bridged. This function does not model ETF returns.
    """
    if not {'month','bias_pp'}.issubset(monthly.columns):
        raise ValueError('monthly must contain month and bias_pp')
    months = _month_dates(monthly.month, 'month')
    if months.has_duplicates:
        raise ValueError('Only one spread value per calendar month is permitted')
    values = pd.Series(pd.to_numeric(monthly.bias_pp,errors='raise').to_numpy(),index=months)
    if 'complete_roster' in monthly:
        values = values.where(monthly.complete_roster.fillna(False).to_numpy())
    origin_dates = _month_dates(origins, 'origins')
    if origin_dates.has_duplicates:
        raise ValueError('Origins must be unique')
    if ((origin_dates<FIRST_ORIGIN)|(origin_dates>LAST_ORIGIN)).any():
        raise ValueError('Origins must be in the frozen February 2021–September 2026 window')
    rows=[]
    for origin in origin_dates:
        signal_month = origin-pd.DateOffset(months=1)
        earlier = pd.date_range(signal_month-pd.DateOffset(months=BASELINE_MONTHS),
                                periods=BASELINE_MONTHS,freq='MS')
        baseline = values.reindex(earlier)
        baseline_n = int(np.isfinite(baseline).sum())
        current = values.get(signal_month,np.nan)
        previous = values.get(signal_month-pd.DateOffset(months=1),np.nan)
        usable = bool(baseline_n==BASELINE_MONTHS and np.isfinite(current) and np.isfinite(previous))
        reference = float(baseline.median()) if baseline_n==BASELINE_MONTHS else np.nan
        surprise = float(current-reference) if usable else np.nan
        delta = float(current-previous) if usable else np.nan
        fade=follow=wait=NEUTRAL_FUND
        if usable and surprise>EPS:
            fade,follow=LONG_FUND,INVERSE_FUND
            if delta < -EPS:
                wait=LONG_FUND
        elif usable and surprise < -EPS:
            fade,follow=INVERSE_FUND,LONG_FUND
            if delta > EPS:
                wait=INVERSE_FUND
        rows.append({'origin':origin,'signal_month':signal_month,'bias_pp':current,
                     'previous_bias_pp':previous,'prior12_median_pp':reference,
                     'surprise_pp':surprise,'delta_pp':delta,'baseline_n':baseline_n,
                     'signal_usable':usable,'Fade_gap':fade,'Follow_gap':follow,'Wait_turn':wait})
    return pd.DataFrame(rows)
