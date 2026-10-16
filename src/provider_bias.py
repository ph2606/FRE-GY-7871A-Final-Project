"""Separate, event-matched provider negative-framing diagnostic; no bias ground truth.

python src/provider_bias.py all
Does not write original media corpora, forecasts, annotation sheets or summaries.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
import hashlib
import itertools
import json
from pathlib import Path
import re
import time
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import requests

if __package__:
    from . import media
else:
    import media

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/provider_bias'
DATA=ROOT/'data/processed'
TABLES=ROOT/'outputs/tables'
SEED=78712615
REPLICATES=5000
MIN_COMMON_EVENTS=6
MAX_TITLES_PER_CELL=20
SCORING_PROTOCOL='provider-title-v2-canonical-branding'
PROVIDERS=[('CNBC','cnbc.com'),('Fox News','foxnews.com'),('Fox Business','foxbusiness.com'),
           ('CNN','cnn.com'),('Reuters','reuters.com'),('Associated Press','apnews.com'),
           ('NPR','npr.org'),('Bloomberg','bloomberg.com'),('Wall Street Journal','wsj.com')]
# Required brands come from the user's request. Other providers enter only on
# adequate identical-event support. The initial six-brand core failed after
# relevance review; the coverage-only amendment is documented explicitly.
CORE=['CNBC','Fox News']
OPTIONAL=[name for name,domain in PROVIDERS if name not in CORE]
FAMILY_QUERIES={'employment':'(jobs OR hiring OR employment OR payroll OR unemployment OR "jobs report" OR "job growth" OR "job gains")',
               'cpi':'("consumer price" OR CPI OR inflation)'}
RELEASE_DAYS={'employment':['2026-01-09','2026-02-11','2026-03-06','2026-04-03','2026-05-08','2026-06-05','2026-07-02','2026-08-07','2026-09-04'],
              'cpi':['2026-01-13','2026-02-13','2026-03-11','2026-04-10','2026-05-12','2026-06-10','2026-07-14','2026-08-12','2026-09-11']}
CALENDAR_URL='https://www.bls.gov/schedule/2026/home.htm'
PREVIEW=re.compile(r'\b(ahead of|preview|what to expect|expected to|likely to|forecast to|set to (?:report|release)|due (?:out|today)|before (?:the |a )?(?:jobs|inflation|CPI))\b',re.I)
RESULT=re.compile(r'\b(rose|rises?|fell|falls?|falling|drop\w*|cool\w*|eas\w*|slow\w*|jump\w*|accelerat\w*|decelerat\w*|added|adds?|gained|gains?|lost|loses?|shed|grew|growth|unchanged|held|holds?|higher|lower|climbs?|climbed|ticks?|ticked|up|down|increased|decreased|changed|changes|comes in|came in|stalls?|stalled|sinks?|sank|hiring|beats?|misses?|surpris\w*|report shows|reports? show|heat\w*|hot|stubborn|steady|stable|worse|better|warmed|warm|surged|surges|weaken\w*)\b',re.I)
NUMERIC=re.compile(r'\d[\d,.]*\s*(?:%|percent|k\b|million|thousand)|\b\d[\d,]{2,}\b',re.I)
EMPLOYMENT=re.compile(r'\b(unemployment|payrolls?|jobs?|job growth|labor market|employment|hiring)\b',re.I)
EMPLOYMENT_AGGREGATE=re.compile(r'\b(U\.?S\.?|United States|Americans?|economy|national|unemployment rate|payrolls?|jobs report|job growth|job gains?|job market|labor market|employment report|employers?|added|adds?|hiring)\b',re.I)
CPI=re.compile(r'\b(inflation|CPI|consumer prices?|consumer price index)\b',re.I)


def canonical_title(text):
    """Remove administrative title branding without altering economic wording."""
    text=re.sub(r'^Watch\s+','',str(text).strip(),flags=re.I)
    brand=r'(?:CNN(?:\s+Business)?|CNBC|Fox\s*(?:News|Business)|Reuters|AP\s*News|Associated\s+Press|NPR|Bloomberg|WSJ(?:\s+Podcasts)?|Wall\s+Street\s+Journal)'
    return re.sub(r'\s+[|\-\u2013\u2014]\s*'+brand+r'\s*$','',text,flags=re.I).strip()

def write_json(path,value):
    def clean(obj):
        if isinstance(obj,dict):return {str(k):clean(v) for k,v in obj.items()}
        if isinstance(obj,(list,tuple)):return [clean(x) for x in obj]
        if isinstance(obj,(np.integer,)):return int(obj)
        if isinstance(obj,(float,np.floating)) and not np.isfinite(obj):return None
        if isinstance(obj,(np.bool_,)):return bool(obj)
        return obj
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(clean(value),indent=2,ensure_ascii=False,allow_nan=False,default=str),encoding='utf-8')

def events():
    rows=[]
    for family,days in RELEASE_DAYS.items():
        for day in days:
            date=pd.Timestamp(day)
            rows.append({'event_id':family+'_'+day,'family':family,'release_date':day,
              'release_month':day[:7],'observation_month':str(date.to_period('M')-1),
              'window_stop_exclusive':str((date+pd.Timedelta(days=2)).date()),'official_calendar_url':CALENDAR_URL,
              'official_archive_url':'https://www.bls.gov/news.release/archives/'+('empsit_' if family=='employment' else 'cpi_')+date.strftime('%m%d%Y')+'.htm'})
    frame=pd.DataFrame(rows).sort_values('release_date').reset_index(drop=True)
    # Use the timezone database for correct DST conversion; no host-timezone assumptions.
    frame['release_at_ny']=pd.to_datetime(frame.release_date).dt.tz_localize('America/New_York').add(pd.Timedelta(hours=8,minutes=30)).astype(str)
    return frame

def fetch(params):
    key=hashlib.sha256(json.dumps(params,sort_keys=True).encode()).hexdigest()
    path=RAW/(key+'.xml');meta_path=RAW/(key+'.metadata.json');RAW.mkdir(parents=True,exist_ok=True)
    if path.exists() and meta_path.exists():
        meta=json.loads(meta_path.read_text(encoding='utf-8'))
        if media.sha(path)!=meta['sha256']:raise ValueError('Supplemental raw-response hash mismatch')
        if meta['http_status']==200:return path.read_bytes(),meta
    payload=b'';errors=[];status=0;url=''
    for attempt in range(3):
        try:
            response=requests.get('https://news.google.com/rss/search',params=params,timeout=(15,40),headers={'User-Agent':'Academic economic headline comparison/1.0'})
            payload=response.content;status=response.status_code;url=response.url
            if status==200:break
            errors.append('HTTP'+str(status))
        except requests.RequestException as exc:errors.append(str(exc))
        time.sleep(attempt+1)
    path.write_bytes(payload)
    meta={'request_url':url,'params':params,'http_status':status,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
      'retrieved_client_date':'2026-10-15','sha256':media.sha(path),'bytes':len(payload),'raw_path':path.relative_to(ROOT).as_posix(),'errors':errors}
    write_json(meta_path,meta);return payload,meta

def provider_event_job(provider,domain,event):
    query=f'site:{domain} {FAMILY_QUERIES[event["family"]]} after:{event["release_date"]} before:{event["window_stop_exclusive"]}'
    body,meta=fetch({'q':query,'hl':'en-US','gl':'US','ceid':'US:en'})
    audit={**meta,'provider':provider,'domain':domain,**event,'returned':0,'capped':False}
    rows=[]
    if meta['http_status']==200:
        try:
            items=ET.fromstring(body).findall('./channel/item');audit.update(returned=len(items),capped=len(items)>=100)
            for item in items:
                title=media.clean(item.findtext('title'));source=media.clean(item.findtext('source'));element=item.find('source')
                source_url=element.attrib.get('url','') if element is not None else ''
                if source and title.endswith(' - '+source):title=title[:-len(source)-3]
                try:published=parsedate_to_datetime(item.findtext('pubDate')).astimezone(timezone.utc).isoformat()
                except (ValueError,TypeError):published=''
                url=item.findtext('link') or ''
                rows.append({'id':'pb_'+hashlib.sha256((provider+':'+url).encode()).hexdigest()[:24],
                  'provider':provider,'domain':domain,**event,'text':title,'url':url,'feed_source':source,'source_url':source_url,
                  'published_at':published,**meta})
        except ET.ParseError as exc:audit['parse_error']=str(exc)
    return rows,audit

def title_exclusion(row):
    text=row['text'];family=row['family']
    if len(text)<8:return 'empty_or_short'
    hostname=(urlparse(row['source_url']).hostname or '').lower()
    if hostname not in [row['domain'],'www.'+row['domain']]:return 'publisher_domain_mismatch'
    published=pd.to_datetime(row['published_at'],utc=True,errors='coerce')
    if pd.isna(published):return 'missing_publication_date'
    day=published.tz_convert('America/New_York').strftime('%Y-%m-%d')
    if day<row['release_date'] or day>=row['window_stop_exclusive']:return 'outside_release_result_dates'
    reason=media.strict_screen_reason(text)
    if reason:return reason
    us_text=re.sub(r'\b(?:South|Latin) American\w*\b','',text,flags=re.I)
    if media.FOREIGN.search(text) and not media.US.search(us_text):return 'explicit_foreign_without_us'
    if PREVIEW.search(text):return 'explicit_preview_or_future_forecast'
    if re.search(r'\b(sponsored|advertisement|promo code)\b',text,re.I):return 'advertising_proxy'
    if family=='employment':
        if not EMPLOYMENT.search(text) or not EMPLOYMENT_AGGREGATE.search(text):return 'not_aggregate_employment_result'
        if re.search(r'\b(ADP|private payrolls?|private sector|jobless claims|unemployment claims|weekly claims|benefit claims|layoffs?|laid off)\b',text,re.I):return 'different_labor_measure_or_single_firm_layoff'
    else:
        if not CPI.search(text):return 'not_cpi_or_consumer_inflation'
        if re.search(r'\b(PCE|PPI|producer prices?|personal consumption|Fed.s (?:favorite|preferred)|wholesale inflation)\b',text,re.I):return 'different_inflation_measure'
    if not RESULT.search(text) and not NUMERIC.search(text):return 'no_completed_result_or_numeric_signal'
    return ''

def primary_exclusion(row):
    text=row['text'];family=row['family']
    if re.search(r'\b(await\w*|brace\w* for|data looms?|payrolls? loom|eyes on payroll|before .*CPI|before .*jobs|(?:job growth|payrolls?|inflation|CPI|economy|hiring) (?:\w+ ){0,2}likely)\b',text,re.I):return 'primary_preview_or_unreported_future_result'
    if re.search(r'\b(wholesale price|wholesale prices|producer price|producer inflation)\b',text,re.I):return 'primary_different_inflation_measure'
    if re.search(r'\b(America In Focus|Morning Squawk|Daily Open|Morning Briefing|Businessweek|Opening Trade|Bloomberg Brief|Open Interest|The Close|Markets P\.M\.|Heated Hearing|electric.shock gloves|ICE plans|payroll software)\b',text,re.I):return 'primary_multitopic_roundup_or_unrelated_subject'
    # Main comparison concerns wording about the economic release, not asset-price responses.
    if re.search(r'\b(stocks?|bonds?|Treasur\w*|yields?|futures?|shares?|S&P|Nasdaq|Dow|FTSE|gold|rupee|yen|rand|equities)\b',text,re.I):return 'primary_asset_market_response_not_release_centric'
    if re.search(r'\b(dollar|STOXX|currencies|forex)\b',text,re.I):return 'primary_asset_market_response_not_release_centric'
    if family=='employment':
        if re.search(r'\b(jobs? report|jobs data|payrolls?|nonfarm|employment report|job report)\b',text,re.I):
            if re.search(r'\b(software|Paycom|Workday)\b',text,re.I):return 'primary_software_company_not_labor_release'
            return ''
        if NUMERIC.search(text) and re.search(r'\b(jobs?|unemployment|hiring|hires|employment)\b',text,re.I) and re.search(r'\b(US|U\.S\.?|United States|Americans?|economy|employers?|unemployment|January|February|March|April|May|June|July|August|September|October|November|December)\b',text,re.I):return ''
        if re.search(r'\b(revised|revision|revisions|lower than reported|far worse than we thought)\b',text,re.I) and re.search(r'\b(hiring|employment|job growth|Labor Department)\b',text,re.I):return ''
        return 'primary_no_specific_current_release_result_anchor'
    if re.search(r'\b(CPI|consumer prices?|inflation (?:report|data|reading|breakdown)|consumer price index)\b',text,re.I):return ''
    month=pd.Period(row['observation_month'],freq='M').strftime('%B')
    if re.search(r'\b'+month+r'\b',text,re.I) and CPI.search(text):return ''
    if re.search(r'^(?:(?:U\.?S\.?|American|Consumer|Headline|Core|Annual)\s+)?Inflation\s+(?:cooled|cools|eased|eases|slowed|slows|rose|rises|fell|falls|held|holds|accelerated|accelerates|dropped|drops|jumped|jumps|heated|heats|surged|surges|moderated|moderates)\b',text,re.I):return ''
    return 'primary_no_specific_current_release_result_anchor'

def screen():
    titles=pd.read_csv(DATA/'provider_bias_titles.csv',keep_default_na=False)
    titles['primary_exclusion_reason']=titles.apply(primary_exclusion,axis=1)
    audit_path=ROOT/'data/annotations/provider_relevance_review.csv'
    if audit_path.exists():
        audit=pd.read_csv(audit_path,keep_default_na=False)
        if 'decision' not in audit:raise ValueError('Provider relevance audit requires id, decision')
        lookup=audit.drop_duplicates('id').set_index('id').decision.str.lower()
        titles['independent_relevance_decision']=titles.id.map(lookup).fillna('not_reviewed')
        # A documented title-only review can confirm a direct release result
        # whose wording lacks a narrow regex phrase. It never overrides a
        # preview, market-response, other-metric or multi-topic exclusion.
        confirmed=titles.independent_relevance_decision.eq('include') & titles.primary_exclusion_reason.eq('primary_no_specific_current_release_result_anchor')
        titles.loc[confirmed,'primary_exclusion_reason']=''
        titles.loc[titles.independent_relevance_decision.isin(['exclude','review','uncertain']),'primary_exclusion_reason']='independent_relevance_review_exclude_or_ambiguous'
    else:titles['independent_relevance_decision']='not_reviewed'
    titles['primary_eligible']=titles.primary_exclusion_reason.eq('')
    titles['model_text']=titles.text.map(canonical_title)
    key=titles.model_text.str.lower().str.replace(r'[^a-z0-9]+',' ',regex=True).str.strip()
    eligible=titles[titles.primary_eligible].copy()
    duplicate=eligible.assign(canonical_key=key.loc[eligible.index]).duplicated(['provider','event_id','canonical_key'])
    duplicate_ids=eligible.index[duplicate]
    titles.loc[duplicate_ids,'primary_eligible']=False
    titles.loc[duplicate_ids,'primary_exclusion_reason']='duplicate_canonical_title_within_provider_event'
    titles.to_csv(DATA/'provider_bias_titles.csv',index=False)
    acquisition_path=TABLES/'provider_bias_acquisition.json'
    if acquisition_path.exists():
        acquisition=json.loads(acquisition_path.read_text(encoding='utf-8'))
        # Acquisition records the unscreened draw first. Keep that stage's digest,
        # but bind input_titles_sha256 to the file that screen() actually saves.
        acquisition.setdefault('pre_screen_input_titles_sha256',acquisition.get('input_titles_sha256'))
        acquisition['input_titles_sha256']=media.sha(DATA/'provider_bias_titles.csv')
        acquisition['input_titles_path']='data/processed/provider_bias_titles.csv'
        acquisition['input_titles_stage']='after_primary_screen_and_canonicalization'
        write_json(acquisition_path,acquisition)
    review=titles[titles.primary_eligible][['id','event_id','provider','text','release_date']].copy()
    review.to_csv(DATA/'provider_bias_primary_review.csv',index=False)
    titles[~titles.primary_eligible][['id','event_id','provider','text','primary_exclusion_reason']].to_csv(TABLES/'provider_bias_primary_exclusions.csv',index=False)
    print(f'Primary release-centric titles {int(titles.primary_eligible.sum())}/{len(titles)}; review file written without scores',flush=True)
    return titles

def acquire(workers=10):
    RAW.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True);TABLES.mkdir(parents=True,exist_ok=True)
    calendar=events();calendar.to_csv(TABLES/'provider_bias_events.csv',index=False)
    rows=[];audits=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(provider_event_job,provider,domain,event) for provider,domain in PROVIDERS for event in calendar.to_dict('records')]
        for i,future in enumerate(as_completed(futures)):
            records,audit=future.result();rows+=records;audits.append(audit)
            if (i+1)%30==0 or i+1==len(futures):print(f'Provider collection {i+1}/{len(futures)}: {len(rows)} candidate titles',flush=True)
    write_json(RAW/'request_audit.json',audits)
    frame=pd.DataFrame(rows)
    if frame.empty:raise ValueError('No provider titles; no scores or empty-source values fabricated')
    frame['normalized_title']=frame.text.str.lower().str.replace(r'[^a-z0-9]+',' ',regex=True).str.strip()
    frame['exclusion_reason']=frame.apply(title_exclusion,axis=1)
    frame['publication_date_ny']=pd.to_datetime(frame.published_at,utc=True,errors='coerce').dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d')
    frame['publication_hour_utc']=pd.to_datetime(frame.published_at,utc=True,errors='coerce').dt.hour
    frame['rss_time_before_release']=pd.to_datetime(frame.published_at,utc=True,errors='coerce')<pd.to_datetime(frame.release_at_ny,utc=True)
    frame['sampling_hash']=frame.id.map(lambda x:hashlib.sha256(f'{SEED}:{x}'.encode()).hexdigest())
    frame=frame.sort_values(['provider','event_id','sampling_hash'])
    duplicate=frame.duplicated(['provider','event_id','normalized_title'])
    frame.loc[duplicate,'exclusion_reason']='duplicate_normalized_title_within_provider_event'
    frame['eligible']=frame.exclusion_reason.eq('')
    eligible=frame[frame.eligible]
    selected=eligible.groupby(['provider','event_id'],sort=True).head(MAX_TITLES_PER_CELL).index
    frame['selected']=frame.index.isin(selected)
    frame['title_cluster']=frame.normalized_title.map(lambda x:hashlib.sha256(x.encode()).hexdigest()[:20])
    frame['same_text_provider_count']=frame.groupby(['event_id','title_cluster']).provider.transform('nunique')
    frame.to_csv(DATA/'provider_bias_candidates.csv',index=False)
    titles=frame[frame.selected].sort_values(['event_id','provider','id']).copy();titles.to_csv(DATA/'provider_bias_titles.csv',index=False)
    write_json(TABLES/'provider_bias_acquisition.json',{'window_releases':'2026-01-01 through2026-09-30','publication_window':'release day and next day, NewYork dates','original_project_cutoff':'2026-10-13','retrieved_client_date':'2026-10-15',
      'providers':PROVIDERS,'events':len(calendar),'query_jobs':len(audits),'failed_requests':sum(a['http_status']!=200 for a in audits),
      'capped_queries':sum(a['capped'] for a in audits),'candidate_rows':len(frame),'eligible_before_cell_limit':int(frame.eligible.sum()),'selected_titles':len(titles),
      'exclusions':frame.exclusion_reason.value_counts().to_dict(),'cell_limit':MAX_TITLES_PER_CELL,'source_title_counts':titles.provider.value_counts().to_dict(),
      'protocol_sha256':media.sha(ROOT/'docs/PROVIDER_COMPARISON_PROTOCOL.md'),'calendar_source':CALENDAR_URL,'raw_audit_sha256':media.sha(RAW/'request_audit.json'),
      'input_titles_sha256':media.sha(DATA/'provider_bias_titles.csv'),'seed':SEED})
    print(titles.groupby('provider').agg(titles=('id','size'),events=('event_id','nunique')).to_string(),flush=True)
    return screen()

def choose_common_panel(cells,min_events=MIN_COMMON_EVENTS):
    support={provider:set(g.event_id) for provider,g in cells.groupby('provider')}
    if any(provider not in support for provider in CORE):return [],[]
    for count in range(len(OPTIONAL),-1,-1):
        for extra in itertools.combinations(OPTIONAL,count):
            panel=CORE+list(extra);common=sorted(set.intersection(*(support[provider] for provider in panel if provider in support)))
            if len(panel)!=sum(provider in support for provider in panel):continue
            if len(common)>=min_events:return panel,common
    return [],[]

def paired_differences(matrix):
    values=np.asarray(matrix,dtype=float)
    if values.ndim!=2 or values.shape[1]<2 or not np.isfinite(values).all():raise ValueError('Complete common-event provider matrix required')
    return 100*(values-(values.sum(axis=1,keepdims=True)-values)/(values.shape[1]-1))

def intervals(differences,months,replicates=REPLICATES,seed=SEED):
    differences=np.asarray(differences,dtype=float);months=np.asarray(months)
    rng=np.random.default_rng(seed);unique=np.unique(months)
    if len(unique)<2:return np.full(differences.shape[1],np.nan),np.full(differences.shape[1],np.nan)
    grouped=[np.flatnonzero(months==m) for m in unique]
    draws=[]
    for _ in range(replicates):
        indices=np.concatenate([grouped[i] for i in rng.integers(0,len(grouped),len(grouped))])
        draws.append(differences[indices].mean(axis=0))
    bounds=np.quantile(np.asarray(draws),[.025,.975],axis=0)
    # Small/discrete bootstrap distributions can place the mean outside percentile bounds.
    # Keep raw bounds: plots must draw the point and interval independently if needed.
    return bounds[0],bounds[1]

def score():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    titles=screen()
    media.copy_model()
    path=DATA/'provider_bias_scored.csv'
    fields=['contextual_negative','contextual_neutral','contextual_positive','contextual_class']
    if path.exists():
        previous=pd.read_csv(path)
        if 'scoring_protocol' in previous and 'model_text' in previous:
            previous=previous[previous.model_revision.eq(media.REVISION)&previous.scoring_protocol.eq(SCORING_PROTOCOL)]
            titles=titles.merge(previous[['id','text','event_id','model_text']+fields],on=['id','text','event_id','model_text'],how='left',validate='one_to_one')
        else:
            for field in fields:titles[field]=np.nan
    else:
        for field in fields:titles[field]=np.nan
    missing=titles.contextual_negative.isna()
    if missing.any():
        titles['contextual_class']=titles['contextual_class'].astype(object)
        probabilities=media.contextual(titles.loc[missing,'model_text'].tolist())
        for i,field in enumerate(fields[:3]):titles.loc[missing,field]=probabilities[:,i]
        titles.loc[missing,'contextual_class']=np.array(['negative','neutral','positive'])[probabilities.argmax(axis=1)]
    vader=SentimentIntensityAnalyzer();titles['vader_compound']=titles.model_text.map(lambda x:vader.polarity_scores(x)['compound'])
    titles['negative']=titles.contextual_class.eq('negative').astype(float)
    titles['vader_negative']=titles.vader_compound.le(-.05).astype(float)
    titles['p_negative']=titles.contextual_negative
    titles['model_revision']=media.REVISION;titles['scoring_protocol']=SCORING_PROTOCOL
    titles['input_text_sha256']=titles.model_text.map(lambda x:hashlib.sha256(x.encode()).hexdigest())
    titles.to_csv(path,index=False)
    broad_cells=titles.groupby(['provider','event_id','release_month','family']).agg(negative_share=('negative','mean'),p_negative=('p_negative','mean'),vader_negative_share=('vader_negative','mean'),n_titles=('id','size')).reset_index()
    broad_cells.to_csv(TABLES/'provider_bias_broad_window_cells.csv',index=False)
    primary=titles[titles.primary_eligible].copy() if 'primary_eligible' in titles else titles.copy()
    cells=primary.groupby(['provider','event_id','release_month','family']).agg(negative_share=('negative','mean'),p_negative=('p_negative','mean'),vader_negative_share=('vader_negative','mean'),n_titles=('id','size')).reset_index()
    single=primary.sort_values('sampling_hash').groupby(['provider','event_id']).head(1)
    cells=cells.merge(single[['provider','event_id','negative']].rename(columns={'negative':'one_hash_title_negative'}),on=['provider','event_id'],validate='one_to_one')
    cells.to_csv(TABLES/'provider_bias_cells.csv',index=False)
    panel,common=choose_common_panel(cells)
    result=[];details={'main_providers':[],'common_event_ids':[],
                       'n_common_events':0,'n_month_clusters':0,'n_main_titles':0}
    if panel:
        selected=cells[cells.provider.isin(panel)&cells.event_id.isin(common)]
        matrix=selected.pivot(index='event_id',columns='provider',values='negative_share').reindex(index=common,columns=panel)
        months=selected.drop_duplicates('event_id').set_index('event_id').release_month.reindex(common).to_numpy()
        differences=paired_differences(matrix.to_numpy());estimate=differences.mean(axis=0)
        raw_lower,raw_upper=intervals(differences,months)
        event_lower,event_upper=intervals(differences,np.array(common),seed=SEED+1)
        sensitivities={}
        for metric in ['p_negative','vader_negative_share','one_hash_title_negative']:
            mat=selected.pivot(index='event_id',columns='provider',values=metric).reindex(index=common,columns=panel)
            sensitivities[metric]=paired_differences(mat.to_numpy()).mean(axis=0)
        for i,provider in enumerate(panel):
            group=selected[selected.provider.eq(provider)]
            result.append({'provider':provider,'bias_pp':estimate[i],
              'lower_95':raw_lower[i],'upper_95':raw_upper[i],
              'raw_percentile_lower_95':raw_lower[i],'raw_percentile_upper_95':raw_upper[i],
              'n_titles':int(group.n_titles.sum()),'n_events':len(common),'n_month_clusters':len(np.unique(months)),
              'raw_negative_share':float(group.negative_share.mean()),'p_negative_bias_pp':sensitivities['p_negative'][i],
              'vader_bias_pp':sensitivities['vader_negative_share'][i],'one_hash_title_bias_pp':sensitivities['one_hash_title_negative'][i],
              'event_bootstrap_lower_95':event_lower[i],'event_bootstrap_upper_95':event_upper[i],
              'coverage':len(common)/18,'same_common_events':True,'comparison_status':'main_common_event_panel',
              'ci_contains_zero':bool(raw_lower[i]<=0<=raw_upper[i])})
        family_specific=[]
        for family,g in selected.groupby('family'):
            fm=g.pivot(index='event_id',columns='provider',values='negative_share').reindex(columns=panel)
            for provider,value in zip(panel,paired_differences(fm.to_numpy()).mean(axis=0)):
                family_specific.append({'family':family,'provider':provider,'bias_pp':float(value),'n_events':len(fm)})
        pd.DataFrame(family_specific).to_csv(TABLES/'provider_bias_family_sensitivity.csv',index=False)
        event_provider=selected.copy();event_provider['relative_negative_pp']=np.nan
        for j,event in enumerate(common):
            for i,provider in enumerate(panel):event_provider.loc[event_provider.event_id.eq(event)&event_provider.provider.eq(provider),'relative_negative_pp']=differences[j,i]
        event_provider.to_csv(TABLES/'provider_bias_common_cells.csv',index=False)
        details={'mode':'identical_common_events_equal_weight','main_providers':panel,'common_event_ids':common,
          'n_common_events':len(common),'n_month_clusters':len(np.unique(months)),'n_main_titles':int(selected.n_titles.sum()),
          'interval_method':'95% conditional month-resampling stability interval:5000 fixed-seed month-cluster percentile draws; both releases from the same sampled month stay together',
          'bootstrap_replicates':REPLICATES,'raw_percentile_interval_contains_estimate':bool(((raw_lower<=estimate)&(raw_upper>=estimate)).all()),
          'plotted_interval_adjustment':'None: raw percentile bounds retained; plot independent interval lines if bounds do not straddle point estimate',
          'event_family_counts':selected.drop_duplicates('event_id').family.value_counts().to_dict()}
    else:
        # A failed-support refresh must not leave successful prior-run evidence
        # alongside a new insufficient-support summary.
        pd.DataFrame(columns=list(cells.columns)+['relative_negative_pp']).to_csv(TABLES/'provider_bias_common_cells.csv',index=False)
        pd.DataFrame(columns=['family','provider','bias_pp','n_events']).to_csv(TABLES/'provider_bias_family_sensitivity.csv',index=False)
    for provider,domain in PROVIDERS:
        if provider in panel:continue
        g=cells[cells.provider.eq(provider)]
        result.append({'provider':provider,'bias_pp':np.nan,'lower_95':np.nan,'upper_95':np.nan,
           'n_titles':int(g.n_titles.sum()),'n_events':int(g.event_id.nunique()),'n_month_clusters':int(g.release_month.nunique()),
           'raw_negative_share':float(g.negative_share.mean()) if len(g) else np.nan,'coverage':float(g.event_id.nunique()/18),
           'same_common_events':False,'comparison_status':'outside_main_common_support_no_comparable_bar' if len(g) else 'no_eligible_content'})
    comparison=pd.DataFrame(result).sort_values('provider');comparison.to_csv(TABLES/'provider_bias.csv',index=False)
    coverage=cells.groupby('provider').agg(available_events=('event_id','nunique'),all_eligible_titles=('n_titles','sum')).reset_index()
    coverage.to_csv(TABLES/'provider_bias_coverage.csv',index=False)
    acquisition=json.loads((TABLES/'provider_bias_acquisition.json').read_text(encoding='utf-8'))
    summary={'status':'complete' if panel else 'insufficient_common_core_events','metric_name':'same-event relative negative framing (percentage points)',
      'formula':'100 * mean_e[negative-title share(provider,e) - mean_other_providers negative-title share(other,e)] over an identical common event set',
      'interpretation':'Higher means more sampled titles classified negative than same-event peers; zero is a peer benchmark, not objective neutrality or absence of bias.',
      'interval_interpretation':'Conditional95% month-resampling stability ranges for this fixed sampled release calendar, not guaranteed population confidence intervals, significance tests or provider rankings. Shared framing by all providers can produce a zero relative score.',
      'affiliation_note':'Fox News and Fox Business are separate queried brands with shared corporate ownership; they are not independent owner-level observations.',
      'not_measured':['factual inaccuracy','partisan or ideological bias','intent','audience exposure','causal effect on consumer sentiment'],
      **details,'core_required':CORE,'minimum_common_events':MIN_COMMON_EVENTS,'all_queried_providers':[x[0] for x in PROVIDERS],
      'provider_rows':comparison.to_dict('records'),'acquisition':acquisition,'calendar_source':CALENDAR_URL,
      'date_scope':'Release dates January–September2026; two-calendar-day result windows; observation periods December2025–August2026',
      'publication_timing':{'default_hour_07_or_08_utc_share':float(titles.publication_hour_utc.isin([7,8]).mean()),
        'rss_time_before_embargo_share':float(titles.rss_time_before_release.mean()),
        'warning':'RSS times are often date defaults. Result-wording filters cannot prove intraday post-release publication; results are retrospective, date-level matched.'},
      'shared_exact_title_rows':int(primary.same_text_provider_count.gt(1).sum()),'n_primary_titles':len(primary),'n_broad_window_titles':len(titles),
      'primary_relevance_audit':primary.independent_relevance_decision.value_counts().to_dict() if 'independent_relevance_decision' in primary else {},
      'classifier':{'model_id':media.MODEL_ID,'revision':media.REVISION,'scoring_protocol':SCORING_PROTOCOL,'input':'Canonical title only; administrative suffix branding and Watch prefix removed; raw text retained',
       'class_rule':'Argmax negative/neutral/positive; binary negative-share primary; uncalibrated Pnegative sensitivity',
       'dictionary':'VADER compound <= -0.05 negative','supplement_human_validation':'not available'},
      'files':{'table':'outputs/tables/provider_bias.csv','scored_titles':'data/processed/provider_bias_scored.csv','all_candidates':'data/processed/provider_bias_candidates.csv',
       'events':'outputs/tables/provider_bias_events.csv','cells':'outputs/tables/provider_bias_cells.csv','common_cells':'outputs/tables/provider_bias_common_cells.csv','protocol':'docs/PROVIDER_COMPARISON_PROTOCOL.md'},
      'hashes':{'protocol_sha256':media.sha(ROOT/'docs/PROVIDER_COMPARISON_PROTOCOL.md'),'amendment_sha256':media.sha(ROOT/'docs/PROVIDER_PROTOCOL_AMENDMENT.md'),
                'relevance_review_sha256':media.sha(ROOT/'data/annotations/provider_relevance_review.csv') if (ROOT/'data/annotations/provider_relevance_review.csv').exists() else None,
                'script_sha256':media.sha(__file__),'scored_titles_sha256':media.sha(path)},
      'limitations':['Retrospective ranked Google RSS convenience sampling and possible100-result query caps.',
       'At most9month clusters; pointwise bootstrap intervals omit measurement, selection and within-cell uncertainty.',
       'Headlines can cover different valid components/angles of the same mixed economic release; residual framing is not established bias.',
       'Date/family matching cannot fully verify event identity, original headline vintage or intraday publication.',
       'No supplemental human validation; classifier domain errors can differ across publishers; dictionary/continuous sensitivities supplied.',
       'Identical cross-provider wording is retained as content supply but not independent exposure; genres and publisher audience composition differ.',
       'Missing provider/event cells are not zeros; providers outside identical common support receive no comparable main bar.']}
    write_json(TABLES/'provider_bias_summary.json',summary)
    print(comparison[['provider','bias_pp','lower_95','upper_95','n_titles','n_events','comparison_status']].to_string(index=False),flush=True)
    print(json.dumps({k:summary.get(k) for k in ['status','main_providers','n_common_events','n_month_clusters','n_main_titles']},indent=2),flush=True)
    return comparison,summary

def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['acquire','screen','score','all'],default='all',nargs='?');parser.add_argument('--workers',type=int,default=10)
    args=parser.parse_args()
    if args.command in ['acquire','all']:acquire(args.workers)
    if args.command=='screen':screen()
    if args.command in ['score','all']:score()

if __name__=='__main__':main()
