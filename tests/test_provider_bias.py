"""Matched provider comparison: support, weights, screening and clustered uncertainty."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import provider_bias as pb

def example_row(text,family='employment',domain='foxnews.com',source_url='https://www.foxnews.com',date='2026-01-09'):
    return {'text':text,'family':family,'domain':domain,'source_url':source_url,
            'published_at':date+'T15:00:00Z','release_date':date,'window_stop_exclusive':str((pd.Timestamp(date)+pd.Timedelta(days=2)).date())}

def test_events_are_release_months_not_observation_months():
    e=pb.events().set_index('event_id')
    assert len(e)==18
    assert e.loc['employment_2026-02-11','observation_month']=='2026-01'
    assert e.loc['employment_2026-01-09','observation_month']=='2025-12'
    assert e.loc['employment_2026-01-09','release_at_ny'].endswith('-05:00')
    assert e.loc['cpi_2026-03-11','release_at_ny'].endswith('-04:00')

def test_domains_keep_fox_brands_separate():
    assert pb.title_exclusion(example_row('US unemployment rate rises to4.2%'))==''
    assert pb.title_exclusion(example_row('US unemployment rate rises to4.2%',source_url='https://www.foxbusiness.com'))=='publisher_domain_mismatch'


def test_canonical_input_removes_branding_but_preserves_report_content():
    assert pb.canonical_title('Watch US job growth slows | CNN Business')=='US job growth slows'
    assert pb.canonical_title('US adds 162,000 jobs - WSJ Podcasts')=='US adds 162,000 jobs'
    assert pb.canonical_title('The Fed watches inflation closely')=='The Fed watches inflation closely'


def test_primary_screen_accepts_us_punctuation_and_rejects_currency_response():
    assert pb.primary_exclusion(example_row('U.S. Adds 162,000 Jobs'))==''
    assert pb.primary_exclusion(example_row('Dollar rises after US jobs data'))=='primary_asset_market_response_not_release_centric'

@pytest.mark.parametrize('title,family,excluded',[
    ('US employers added50,000 jobs as unemployment rose','employment',False),
    ('US jobs report beats forecasts as payrolls grow','employment',False),
    ('US jobs report expected to show200,000 new jobs','employment',True),
    ('US private payrolls rise by100,000 ADP says','employment',True),
    ('US weekly unemployment claims rise','employment',True),
    ('CPI inflation cooled to2.5% in December','cpi',False),
    ('Inflation unexpectedly rises in new CPI report','cpi',False),
    ('PCE inflation rises to2.5%','cpi',True),
    ('Chinese inflation rises to2.5%','cpi',True),
    ('Balloon inflation set for Thanksgiving','cpi',True),
])
def test_result_topic_screen(title,family,excluded):
    row=example_row(title,family=family,date='2026-01-13' if family=='cpi' else '2026-01-09')
    assert bool(pb.title_exclusion(row)) is excluded

def test_common_panel_is_identical_and_not_tone_selected():
    rows=[]
    for provider in pb.CORE:
        rows.extend({'provider':provider,'event_id':f'e{i}'} for i in range(1,8))
    for provider,ids in [('NPR',range(1,7)),('Bloomberg',range(2,8)),('Wall Street Journal',range(3,8))]:
        rows.extend({'provider':provider,'event_id':f'e{i}'} for i in ids)
    panel,common=pb.choose_common_panel(pd.DataFrame(rows))
    assert panel==pb.CORE+['NPR']
    assert common==[f'e{i}' for i in range(1,7)]
    assert pb.choose_common_panel(pd.DataFrame(rows)[lambda d:~d.provider.eq('Fox News')])==([],[])

def test_equal_event_weight_peer_benchmark_zero_sum():
    matrix=np.array([[1,0,0],[0,.5,1.]])
    result=pb.paired_differences(matrix)
    assert np.allclose(result.sum(axis=1),0)
    assert result.mean(axis=0)==pytest.approx([12.5,-25.,12.5])
    with pytest.raises(ValueError):pb.paired_differences([[1,np.nan]])

def test_month_cluster_bootstrap_retains_release_pairs():
    differences=np.array([[80,-80],[-80,80],[20,-20],[-20,20]])
    # Each two-release month sums tozero, so resampling entire months stayszero.
    lower,upper=pb.intervals(differences,['m1','m1','m2','m2'],replicates=200)
    assert np.allclose(lower,0) and np.allclose(upper,0)
    elo,ehi=pb.intervals(differences,['a','b','c','d'],replicates=200)
    assert (ehi-elo>0).all()
