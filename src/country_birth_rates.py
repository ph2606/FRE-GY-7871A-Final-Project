"""Rank 2023 WDI crude birth rates; five readable 20-economy chart pages.

Scope follows World Bank countries/economies, including separately reported
territories. Regional/income aggregates are excluded using official metadata.
The indicator measures annual births per1000 people, not births per woman.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd

from .part_b_demography import cached_json, theme, NAVY, TEAL, SLATE, PALE, WARM

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/processed'
OUT=ROOT/'outputs'
TABLES=OUT/'tables'
YEAR=2023
INDICATOR='SP.DYN.CBRT.IN'
TOP_N=100
ROWS_PER_PAGE=20
FIGURE_NAMES=tuple(f'country_birth_rates_{i:02d}' for i in range(1,6))
SHORT_NAMES={'COD':'DR Congo','CAF':'Central African Republic','FSM':'Micronesia (FSM)',
             'PSE':'West Bank & Gaza','EGY':'Egypt','YEM':'Yemen','IRN':'Iran',
             'VEN':'Venezuela','LAO':'Lao PDR','SYR':'Syria','KOR':'South Korea',
             'PRK':'North Korea','STP':'São Tomé & Príncipe','COG':'Republic of Congo'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def rank_observations(values_payload,country_payload):
    """Use official country metadata; sort unrounded estimates before display."""
    meta=country_payload[1]
    if len({row['id'] for row in meta})!=len(meta):
        raise ValueError('Country metadata contains duplicate IDs')
    by_iso2={row['iso2Code']:row for row in meta}
    records=[];excluded=[];seen=set()
    for row in values_payload[1]:
        if row['indicator']['id']!=INDICATOR or int(row['date'])!=YEAR:
            raise ValueError('Unexpected indicator/year in birth-rate response')
        country=by_iso2.get(row['country']['id'])
        if country is None:
            raise ValueError(f'Birth-rate entity absent from country metadata: {row["country"]}')
        code=country['id']
        if code in seen:
            raise ValueError('Duplicate country/economy observation')
        seen.add(code)
        base={'iso3':code,'country':country['name'],'year':YEAR}
        if country['region']['id']=='NA' or country['region']['value']=='Aggregates':
            excluded.append({**base,'reason':'World Bank aggregate'})
            continue
        value=row['value']
        if value is None:
            excluded.append({**base,'reason':'Missing2023value'})
            continue
        if not np.isfinite(value) or value<0:
            raise ValueError(f'Invalid birth rate for {code}')
        if row.get('countryiso3code') and row['countryiso3code']!=code:
            raise ValueError('Indicator and metadata country codes disagree')
        records.append({**base,'display_country':SHORT_NAMES.get(code,country['name']),
                        'births_per_1000_people':float(value),
                        'region':country['region']['value'],
                        'income_group':country['incomeLevel']['value']})
    for country in meta:
        if country['region']['id']!='NA' and country['region']['value']!='Aggregates' and country['id'] not in seen:
            excluded.append({'iso3':country['id'],'country':country['name'],'year':YEAR,
                             'reason':'No2023observationreturned'})
    qualified=pd.DataFrame(records).sort_values(
        ['births_per_1000_people','country','iso3'],ascending=[False,True,True],kind='mergesort').reset_index(drop=True)
    qualified.insert(0,'rank',np.arange(1,len(qualified)+1))
    if len(qualified)<TOP_N:
        raise ValueError('Fewer than100 qualified countries/economies')
    return qualified,pd.DataFrame(excluded)


def acquire():
    jobs=[('indicator_values',f'https://api.worldbank.org/v2/country/all/indicator/{INDICATOR}',
           {'format':'json','date':str(YEAR),'per_page':20000,'source':2}),
          ('country_metadata','https://api.worldbank.org/v2/country',
           {'format':'json','per_page':400}),
          ('indicator_metadata',f'https://api.worldbank.org/v2/indicator/{INDICATOR}',
           {'format':'json','per_page':100,'source':2})]
    with ThreadPoolExecutor(max_workers=3) as executor:
        responses=list(executor.map(lambda job:cached_json(job[1],job[2]),jobs))
    qualified,excluded=rank_observations(responses[0][0],responses[1][0])
    DATA.mkdir(parents=True,exist_ok=True)
    TABLES.mkdir(parents=True,exist_ok=True)
    panel_path=DATA/f'country_birth_rates_{YEAR}.csv'
    excluded_path=DATA/'country_birth_rates_exclusions.csv'
    top_path=TABLES/'country_birth_rates_top100.csv'
    qualified.to_csv(panel_path,index=False)
    excluded.to_csv(excluded_path,index=False)
    qualified.head(TOP_N).to_csv(top_path,index=False)
    reasons=excluded.reason.value_counts().to_dict()
    summary={
        'indicator':INDICATOR,'indicator_name':'Birth rate, crude (per 1,000 people)',
        'year':YEAR,'unit':'Live births during the year per 1,000 people in the population',
        'scope':'World Bank countries and economies, including separately reported territories; not a sovereign-states-only list',
        'aggregate_rule':'Exclude official country metadata entries whose region is Aggregates (region ID NA)',
        'missing_rule':'Exclude missing2023observations; never fill from another year or substitute zero',
        'ranking_rule':'Descending unrounded2023rate, then official country name and ISO3 code ascending for exact ties',
        'data_rows_returned':len(responses[0][0][1]),'metadata_rows':len(responses[1][0][1]),
        'qualified_nonmissing_n':len(qualified),'exclusion_counts':reasons,
        'missing_nonaggregate_n':sum(value for key,value in reasons.items() if key!='World Bank aggregate'),
        'top_n':TOP_N,'chart_pages':5,'panels_per_page':2,'countries_per_panel':10,
        'indicator_metadata':responses[2][0][1][0],
        'sources':[{'kind':job[0],**response[1]} for job,response in zip(jobs,responses)],
        'license':'CC BY4.0 identified on the World Bank indicator page',
        'source_page':'https://data.worldbank.org/indicator/SP.DYN.CBRT.IN',
        'country_metadata_reference':'https://datahelpdesk.worldbank.org/knowledgebase/articles/898590-country-api-queries',
        'table_path':top_path.relative_to(ROOT).as_posix(),
        'qualified_path':panel_path.relative_to(ROOT).as_posix(),
        'excluded_path':excluded_path.relative_to(ROOT).as_posix(),
        'hashes':{path.relative_to(ROOT).as_posix():sha(path) for path in [panel_path,excluded_path,top_path]},
        'limitations':[
            'Crude birth rate also reflects population age structure; it is not total fertility, birth counts or an individual-family measure.',
            'Current-vintage historical estimates may be revised;2023 is a fixed common comparison year, not the latest available year for every economy.',
            'A point-estimate ranking does not measure whether small differences are statistically meaningful; no uncertainty intervals are supplied here.',
            'World Bank economy labels do not assert sovereign status, and this chart makes no intelligence or ability inference.'],
    }
    save_json(TABLES/'country_birth_rates_summary.json',summary)
    print(f'Qualified:{len(qualified)}; excluded:{reasons}; top100 cutoff:{qualified.iloc[99].country} {qualified.iloc[99].births_per_1000_people:.6f}')
    return qualified,summary


def page_figure(rows,page,axis_max):
    theme()
    fig=plt.figure(figsize=(12.6,6.0),facecolor='white')
    low,high=int(rows['rank'].min()),int(rows['rank'].max())
    fig.text(.055,.963,f'Highest birth rates in 2023 · ranks {low}–{high}',
             fontsize=21,weight='bold',color=NAVY,va='top')
    fig.text(.055,.905,'World Bank countries/economies · births per 1,000 people in a year · descending unrounded estimates',
             fontsize=11.8,color=SLATE,va='top')
    for column in range(2):
        data=rows.iloc[column*10:(column+1)*10]
        ax=fig.add_axes([.245+.5*column,.21,.235,.575],facecolor=WARM)
        y=np.arange(len(data))
        ax.barh(y,data.births_per_1000_people,height=.62,color=TEAL,zorder=2)
        labels=[f'{row.rank:>3}  {row.display_country}' for row in data.itertuples()]
        ax.set_yticks(y,labels,fontsize=15.8)
        ax.set_ylim(len(data)-.5,-.5)
        ax.set_xlim(0,axis_max)
        ax.set_xticks(np.arange(0,axis_max+1,10))
        ax.tick_params(axis='both',length=0,pad=8,labelcolor=SLATE)
        ax.tick_params(axis='x',labelsize=12)
        ax.grid(axis='x',color='#DFE8EC',lw=.7)
        for position,value in zip(y,data.births_per_1000_people):
            ax.text(value+.7,position,f'{value:.1f}',va='center',ha='left',
                    fontsize=14.2,weight='bold',color=NAVY)
        ax.set_xlabel('Births per 1,000 people',fontsize=12.2,labelpad=10)
        ax.set_title(f'Ranks {int(data["rank"].min())}–{int(data["rank"].max())}',
                     loc='left',fontsize=12.5,color=SLATE,pad=13)
    fig.text(.055,.078,'Same zero-based scale on all five pages. World Bank scope includes separately reported territories; regional/income aggregates excluded.',
             fontsize=9.9,color=SLATE)
    fig.text(.055,.035,'Source: World Bank WDI, SP.DYN.CBRT.IN · 2023 common year · CC BY 4.0 · Not births per woman or a measure of intelligence.',
             fontsize=9.6,color=SLATE)
    return fig


def split_top100(ranked):
    """Retain exactly100 distinct ranked economies, split into five20-row groups."""
    if len(ranked)<TOP_N:
        raise ValueError('At least100 ranked economies are required')
    top=ranked.head(TOP_N).copy()
    if top['rank'].tolist()!=list(range(1,TOP_N+1)) or top.iso3.duplicated().any():
        raise ValueError('Top100 needs unique economies and global ranks1–100')
    if not top.births_per_1000_people.is_monotonic_decreasing:
        raise ValueError('Birth-rate data are not descending')
    return [top.iloc[start:start+ROWS_PER_PAGE].copy() for start in range(0,TOP_N,ROWS_PER_PAGE)]


def common_axis_max(ranked):
    """One rounded ceiling with label room; never rescale an individual panel."""
    values=ranked.head(TOP_N).births_per_1000_people
    if not len(values) or not np.isfinite(values).all() or values.lt(0).any():
        raise ValueError('Axis limits require nonnegative finite birth rates')
    return 10*math.ceil((values.max()+4)/10)


def build():
    summary_path=TABLES/'country_birth_rates_summary.json'
    summary=json.loads(summary_path.read_text(encoding='utf-8'))
    for name,digest in summary['hashes'].items():
        if sha(ROOT/name)!=digest:
            raise ValueError('Birth-rate input changed: '+name)
    ranked=pd.read_csv(TABLES/'country_birth_rates_top100.csv')
    if len(ranked)!=TOP_N:
        raise ValueError('Top100 rank grid changed')
    groups=split_top100(ranked)
    axis_max=common_axis_max(ranked)
    OUT.mkdir(parents=True,exist_ok=True)
    combined=OUT/'Country_Birth_Rates_Top_100.pdf'
    paths=[]
    with PdfPages(combined,metadata={'CreationDate':None,'ModDate':None}) as pdf:
        for page,name in enumerate(FIGURE_NAMES):
            fig=page_figure(groups[page],page+1,axis_max)
            for suffix in ['png','pdf']:
                path=OUT/f'{name}.{suffix}'
                metadata={'CreationDate':None,'ModDate':None} if suffix=='pdf' else None
                fig.savefig(path,dpi=220,metadata=metadata)
                paths.append(path)
            pdf.savefig(fig)
            plt.close(fig)
    paths.append(combined)
    summary['common_x_axis']=[0,axis_max]
    summary['figure_paths']=[path.relative_to(ROOT).as_posix() for path in paths]
    summary['figure_sha256']={path.relative_to(ROOT).as_posix():sha(path) for path in paths}
    summary['combined_pdf']=combined.relative_to(ROOT).as_posix()
    summary['first_rank']=json.loads(ranked.head(1).to_json(orient='records'))[0]
    summary['hundredth_rank']=json.loads(ranked.tail(1).to_json(orient='records'))[0]
    save_json(summary_path,summary)
    print(f'Built5chartpairs and {combined.name}; common xaxis0–{axis_max:g}')
    return summary


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['acquire','build','all'],nargs='?',default='all')
    args=parser.parse_args()
    if args.command in ['acquire','all']:
        acquire()
    if args.command in ['build','all']:
        build()


if __name__=='__main__':
    main()
