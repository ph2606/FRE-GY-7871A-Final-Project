"""Check weighting, calendar timing and fixed rule decisions without market data."""
import numpy as np
import pandas as pd
import pytest

from src import bias_signal as bs


def sample_scores():
    return pd.DataFrame([
        ('2020-01-01','Reuters','negative'),
        ('2020-01-01','NPR','neutral'),
        ('2020-01-01','NPR','neutral'),
        ('2020-01-01','NPR','negative'),
        ('2020-01-01','Colorado Sun','neutral'),
        ('2020-01-01','Associated Press','negative'),
        ('2026-10-01','Reuters','negative'),
    ],columns=['month','source','contextual_class'])


def test_fixed_roster_equal_outlets_not_title_weighted_and_partial_october_excluded():
    monthly=bs.monthly_spread(sample_scores())
    assert len(monthly)==81
    first=monthly.iloc[0]
    assert first.bias_pp==pytest.approx(100*(1+1/3)/2)
    assert first.n_titles==5 and first.source_count==3
    assert first.reuters_n==1 and first.npr_n==3 and first.colorado_sun_n==1
    assert monthly.month.max()==pd.Timestamp('2026-09-01')
    assert pd.isna(monthly.iloc[1].bias_pp)
    assert not monthly.iloc[1].complete_roster


def test_absent_fixed_outlet_is_missing_not_zero_or_a_smaller_roster():
    data=sample_scores()
    monthly=bs.monthly_spread(data.loc[data.source.ne('Colorado Sun')])
    assert pd.isna(monthly.iloc[0].bias_pp)
    assert monthly.iloc[0].source_count==2
    assert monthly.iloc[0].colorado_sun_n==0


def history(current=10,previous=20):
    dates=pd.date_range('2020-01-01','2021-02-01',freq='MS')
    return pd.DataFrame({'month':dates,'bias_pp':[0.]*11+[previous,current,999.]})


@pytest.mark.parametrize('current,previous,fade,follow,wait',[
    (10,20,'UPRO','SPXU','UPRO'),
    (-10,-20,'SPXU','UPRO','SPXU'),
    (10,5,'UPRO','SPXU','BIL'),
    (10,10,'UPRO','SPXU','BIL'),
    (10,10-bs.EPS/2,'UPRO','SPXU','BIL'),
    (-10,-5,'SPXU','UPRO','BIL'),
    (0,0,'BIL','BIL','BIL'),
    (bs.EPS/2,0,'BIL','BIL','BIL'),
])
def test_three_rules_use_only_completed_month_and_prior12_excluding_current(current,previous,fade,follow,wait):
    row=bs.origin_signals(history(current,previous),['2021-02-01']).iloc[0]
    assert row.signal_month==pd.Timestamp('2021-01-01')
    assert row.prior12_median_pp==0
    assert row.baseline_n==12
    assert (row.Fade_gap,row.Follow_gap,row.Wait_turn)==(fade,follow,wait)


def test_future_month_cannot_change_current_decision():
    original=history()
    future=original.copy()
    future.loc[future.month.eq('2021-02-01'),'bias_pp']=-999.
    pd.testing.assert_frame_equal(bs.origin_signals(original,['2021-02-01']),
                                  bs.origin_signals(future,['2021-02-01']))


def test_calendar_gap_or_incomplete_baseline_is_neutral_never_bridged():
    missing=history().loc[lambda x:x.month.ne('2020-07-01')]
    row=bs.origin_signals(missing,['2021-02-01']).iloc[0]
    assert row.baseline_n==11 and not row.signal_usable
    assert row[['Fade_gap','Follow_gap','Wait_turn']].eq('BIL').all()
    missing_current=history()
    missing_current.loc[missing_current.month.eq('2021-01-01'),'bias_pp']=np.nan
    row=bs.origin_signals(missing_current,['2021-02-01']).iloc[0]
    assert not row.signal_usable
    assert row[['Fade_gap','Follow_gap','Wait_turn']].eq('BIL').all()


def test_duplicate_months_and_invalid_early_origins_are_rejected():
    with pytest.raises(ValueError,match='one spread'):
        bs.origin_signals(pd.concat([history(),history().iloc[[0]]]),['2021-02-01'])
    with pytest.raises(ValueError,match='frozen'):
        bs.origin_signals(history(),['2021-01-01'])


def test_invalid_classes_or_excluded_candidates_cannot_enter_the_denominator():
    invalid=sample_scores()
    invalid.loc[0,'contextual_class']='unreviewed'
    with pytest.raises(ValueError,match='frozen'):
        bs.monthly_spread(invalid)
    excluded=sample_scores()
    excluded['post_sample_exclusion_reason']=''
    excluded.loc[0,'post_sample_exclusion_reason']='off_topic'
    with pytest.raises(ValueError,match='final-eligible'):
        bs.monthly_spread(excluded)
