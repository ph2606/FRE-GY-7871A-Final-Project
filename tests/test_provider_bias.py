"""Matched provider comparison: support, weights, screening and clustered uncertainty."""
from pathlib import Path
import sys
import hashlib
import json
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


def test_screen_hash_tracks_saved_titles_and_preserves_initial_draw(tmp_path,monkeypatch):
    data=tmp_path/'data/processed';tables=tmp_path/'outputs/tables'
    data.mkdir(parents=True);tables.mkdir(parents=True)
    monkeypatch.setattr(pb,'ROOT',tmp_path);monkeypatch.setattr(pb,'DATA',data);monkeypatch.setattr(pb,'TABLES',tables)
    row=example_row('US employers added 50,000 jobs as unemployment rose')
    row.update(id='test_title',provider='CNBC',event_id='employment_2026-01-09',observation_month='2025-12')
    pd.DataFrame([row]).to_csv(data/'provider_bias_titles.csv',index=False)
    initial_hash=hashlib.sha256((data/'provider_bias_titles.csv').read_bytes()).hexdigest()
    acquisition_path=tables/'provider_bias_acquisition.json'
    acquisition_path.write_text(json.dumps({'input_titles_sha256':initial_hash,'seed':pb.SEED}),encoding='utf-8')
    pb.screen()
    screened_hash=hashlib.sha256((data/'provider_bias_titles.csv').read_bytes()).hexdigest()
    metadata=json.loads(acquisition_path.read_text(encoding='utf-8'))
    assert screened_hash!=initial_hash
    assert metadata['input_titles_sha256']==screened_hash
    assert metadata['pre_screen_input_titles_sha256']==initial_hash
    assert metadata['input_titles_stage']=='after_primary_screen_and_canonicalization'
    # A score-only refresh invokes screen() again and must not relabel the
    # previous screened digest as the original unscreened draw.
    pb.screen()
    repeated=json.loads(acquisition_path.read_text(encoding='utf-8'))
    assert repeated['pre_screen_input_titles_sha256']==initial_hash
    assert repeated['input_titles_sha256']==hashlib.sha256((data/'provider_bias_titles.csv').read_bytes()).hexdigest()


def test_insufficient_support_refresh_clears_old_matched_outputs(tmp_path,monkeypatch):
    data=tmp_path/'data/processed';tables=tmp_path/'outputs/tables';docs=tmp_path/'docs'
    for directory in [data,tables,docs]:directory.mkdir(parents=True)
    monkeypatch.setattr(pb,'ROOT',tmp_path);monkeypatch.setattr(pb,'DATA',data);monkeypatch.setattr(pb,'TABLES',tables)
    for name in ['PROVIDER_COMPARISON_PROTOCOL.md','PROVIDER_PROTOCOL_AMENDMENT.md']:(docs/name).write_text('test protocol',encoding='utf-8')
    (tables/'provider_bias_acquisition.json').write_text('{}',encoding='utf-8')
    for name in ['provider_bias_common_cells.csv','provider_bias_family_sensitivity.csv']:
        pd.DataFrame([{'provider':'stale_provider','event_id':'stale_event','bias_pp':99}]).to_csv(tables/name,index=False)
    # Only one provider/event remains: a previously successful comparison is
    # now impossible. Reuse frozen fake probabilities; no model/network call.
    row={'id':'test_title','text':'US added 50,000 jobs','model_text':'US added 50,000 jobs',
         'provider':'CNBC','event_id':'employment_2026-01-09','release_month':'2026-01','family':'employment',
         'sampling_hash':'a','primary_eligible':True,'same_text_provider_count':1,
         'publication_hour_utc':15,'rss_time_before_release':False,'independent_relevance_decision':'include',
         'model_revision':pb.media.REVISION,'scoring_protocol':pb.SCORING_PROTOCOL,
         'contextual_negative':.1,'contextual_neutral':.8,'contextual_positive':.1,'contextual_class':'neutral'}
    pd.DataFrame([row]).to_csv(data/'provider_bias_scored.csv',index=False)
    input_row={key:value for key,value in row.items() if not key.startswith('contextual_')}
    monkeypatch.setattr(pb,'screen',lambda:pd.DataFrame([input_row]))
    monkeypatch.setattr(pb.media,'copy_model',lambda:[])
    def unexpected_inference(*args,**kwargs):raise AssertionError('The fake unchanged cache should avoid model inference')
    monkeypatch.setattr(pb.media,'contextual',unexpected_inference)
    comparison,summary=pb.score()
    assert summary['status']=='insufficient_common_core_events'
    assert summary['n_common_events']==summary['n_main_titles']==summary['n_month_clusters']==0
    assert summary['main_providers']==summary['common_event_ids']==[]
    assert comparison.bias_pp.isna().all()
    assert pd.read_csv(tables/'provider_bias_common_cells.csv').empty
    assert pd.read_csv(tables/'provider_bias_family_sensitivity.csv').empty
