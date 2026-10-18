"""World Bank fertility/birth-rate context with immutable public-source caches.

These are demographic aggregates, not measurements of intelligence, ability or
individual behavior. No inference about those traits is made from income/place.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/part_b_demography'
DATA=ROOT/'data/processed'
OUT=ROOT/'outputs'
TABLES=OUT/'tables'
FIRST_YEAR,LAST_YEAR=1990,2023
ENTITIES=('USA','GBR','DEU','FRA','ITA','CHN','IND','BGD','KOR','JPN','NGA','NER','COD',
          'WLD','LIC','LMC','UMC','HIC')
LABELS=dict(zip(ENTITIES,('United States','United Kingdom','Germany','France','Italy','China',
    'India','Bangladesh','South Korea','Japan','Nigeria','Niger','DR Congo',
    'World','Low income','Lower middle income','Upper middle income','High income')))
AGGREGATE_IDS={'XM':'LIC','XN':'LMC','XT':'UMC','XD':'HIC'}
INDICATORS={'SP.DYN.TFRT.IN':'fertility_births_per_woman',
            'SP.DYN.CBRT.IN':'births_per_1000_people'}
NAVY,TEAL,CORAL,SLATE,PALE,WARM='#172F43','#167D8D','#C77B68','#657787','#EAF1F4','#FCFBF8'


def save_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def cached_json(url,params):
    """Store response bytes by content hash; reuse only matching request/hash pairs."""
    request={'url':url,'params':params}
    key=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
    metadata_path=RAW/'requests'/f'{key}.json'
    if metadata_path.exists():
        meta=json.loads(metadata_path.read_text(encoding='utf-8'))
        if meta['request']!=request:
            raise ValueError('Cached World Bank request differs from its key')
        payload=ROOT/meta['raw_path']
        body=payload.read_bytes()
        if hashlib.sha256(body).hexdigest()!=meta['sha256']:
            raise ValueError('Immutable World Bank response hash mismatch')
        return json.loads(body),meta
    for attempt in range(3):
        try:
            response=requests.get(url,params=params,timeout=(20,70))
            response.raise_for_status()
            result=response.json()
            if not isinstance(result,list) or len(result)!=2 or not isinstance(result[0],dict):
                raise ValueError('Unexpected World Bank API response')
            if int(result[0].get('pages',1))!=1:
                raise ValueError('Increase per_page or explicitly acquire all pages')
            body=response.content
            digest=hashlib.sha256(body).hexdigest()
            payload=RAW/'responses'/f'{digest}.json'
            payload.parent.mkdir(parents=True,exist_ok=True)
            if payload.exists():
                if payload.read_bytes()!=body:
                    raise ValueError('Content-addressed response collision')
            else:
                payload.write_bytes(body)
            meta={'request':request,'resolved_url':response.url,'sha256':digest,'bytes':len(body),
                  'raw_path':payload.relative_to(ROOT).as_posix(),'http_status':response.status_code,
                  'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
                  'api_metadata':result[0]}
            save_json(metadata_path,meta)
            return result,meta
        except (requests.RequestException,ValueError):
            if attempt==2:
                raise
            time.sleep(attempt+1)


def parse_indicator(payload,indicator):
    records=[]
    for item in payload[1]:
        if item['indicator']['id']!=indicator:
            raise ValueError('Unexpected indicator in response')
        # WDI leaves ISO3 blank for income aggregates; retain their official IDs.
        code=item.get('countryiso3code') or AGGREGATE_IDS.get(item['country']['id'])
        if code not in ENTITIES:
            raise ValueError(f'Unexpected country/aggregate: {item["country"]}')
        year=int(item['date'])
        if not FIRST_YEAR<=year<=LAST_YEAR:
            raise ValueError('Out-of-window observation')
        value=item['value']
        if value is not None and (not np.isfinite(value) or value<0):
            raise ValueError('Invalid demographic observation')
        records.append({'entity':code,'entity_name':LABELS[code],
                        'official_entity_name':item['country']['value'],
                        'entity_type':'country' if code not in ('WLD','LIC','LMC','UMC','HIC') else 'aggregate',
                        'year':year,INDICATORS[indicator]:value})
    frame=pd.DataFrame(records)
    if frame.duplicated(['entity','year']).any():
        raise ValueError('Duplicate entity/year')
    expected=pd.MultiIndex.from_product([ENTITIES,range(FIRST_YEAR,LAST_YEAR+1)],names=['entity','year'])
    actual=pd.MultiIndex.from_frame(frame[['entity','year']])
    if set(actual)!=set(expected):
        raise ValueError('World Bank response does not cover the full fixed grid')
    return frame


def acquire():
    codes=';'.join(ENTITIES)
    jobs=[]
    for indicator in INDICATORS:
        jobs.append(('data',indicator,f'https://api.worldbank.org/v2/country/{codes}/indicator/{indicator}',
                     {'format':'json','date':f'{FIRST_YEAR}:{LAST_YEAR}','per_page':20000,'source':2}))
        jobs.append(('metadata',indicator,f'https://api.worldbank.org/v2/indicator/{indicator}',
                     {'format':'json','source':2,'per_page':100}))
    with ThreadPoolExecutor(max_workers=4) as executor:
        results=list(executor.map(lambda job:cached_json(job[2],job[3]),jobs))
    frames=[];provenance=[];definitions={}
    for (kind,indicator,_,_),(payload,meta) in zip(jobs,results):
        provenance.append({'kind':kind,'indicator':indicator,**meta})
        if kind=='data':
            frames.append(parse_indicator(payload,indicator))
        else:
            details=payload[1][0]
            if details['id']!=indicator:
                raise ValueError('Unexpected indicator metadata')
            definitions[indicator]=details
    keys=['entity','entity_name','official_entity_name','entity_type','year']
    panel=frames[0].merge(frames[1],on=keys,validate='one_to_one')
    panel['entity']=pd.Categorical(panel.entity,categories=ENTITIES,ordered=True)
    panel=panel.sort_values(['entity','year']).reset_index(drop=True)
    DATA.mkdir(parents=True,exist_ok=True)
    panel.to_csv(DATA/'part_b_demography.csv',index=False)
    missing={column:int(panel[column].isna().sum()) for column in INDICATORS.values()}
    summary={'status':'observed_WDI_demographic_context','first_year':FIRST_YEAR,'last_year':LAST_YEAR,
             'entities':list(ENTITIES),'country_count':13,'aggregate_count':5,'panel_rows':len(panel),
             'missing_values':missing,'indicator_metadata':definitions,'sources':provenance,
             'license':'CC BY 4.0 as identified on both official indicator pages',
             'license_reference':'https://datacatalog.worldbank.org/public-licenses',
             'indicator_pages':[f'https://data.worldbank.org/indicator/{code}' for code in INDICATORS],
             'income_groups_reference':'https://datahelpdesk.worldbank.org/knowledgebase/articles/906519-world-bank-country-and-lending-groups',
             'interpretation':[
                 'Total fertility is a period rate implied by age-specific fertility, not observed completed lifetime family size.',
                 'Crude birth rate counts annual births per1000 people and also depends on population age structure.',
                 'A lower birth rate is not necessarily a lower total number of births, because population size may change.',
                 'These are current-vintage published WDI estimates for1990–2023, not historical real-time vintages.',
                 'Income aggregates are World Bank published groups; membership and aggregation may change across data vintages.',
                 'Selected countries are illustrative rather than a probability sample; world/income aggregates are not unweighted averages of these13 countries.',
                 'Income and national origin do not measure individual ability, IQ, preferences or moral worth; no such inference is made.',
                 'No fertility trend alone forecasts population decline: mortality, migration and age structure also matter.']}
    summary['panel_sha256']=hashlib.sha256((DATA/'part_b_demography.csv').read_bytes()).hexdigest()
    save_json(TABLES/'part_b_demography_summary.json',summary)
    return panel,summary


def comparison_table(panel):
    columns=['fertility_births_per_woman','births_per_1000_people']
    parts=[]
    for year in [FIRST_YEAR,LAST_YEAR]:
        subset=panel.loc[panel.year.eq(year),['entity','entity_name','entity_type']+columns]
        subset=subset.rename(columns={column:f'{column}_{year}' for column in columns})
        parts.append(subset)
    result=parts[0].merge(parts[1],on=['entity','entity_name','entity_type'],validate='one_to_one')
    for column in columns:
        result[column+'_change']=result[f'{column}_{LAST_YEAR}']-result[f'{column}_{FIRST_YEAR}']
    return result.set_index('entity').reindex(ENTITIES).reset_index()


def theme():
    # Isolate the figure from style settings left by other report exhibits.
    plt.rcdefaults()
    names={font.name for font in font_manager.fontManager.ttflist}
    font=next((name for name in ['Aptos','Calibri'] if name in names),'DejaVu Sans')
    plt.rcParams.update({'font.family':font,'font.size':11,'pdf.fonttype':42,'ps.fonttype':42,
                         'figure.facecolor':'white','axes.facecolor':WARM,'text.color':NAVY,
                         'axes.labelcolor':SLATE,'xtick.color':SLATE,'ytick.color':SLATE,
                         'axes.spines.top':False,'axes.spines.right':False,
                         'axes.spines.left':False,'axes.spines.bottom':False,
                         'axes.axisbelow':True,'savefig.facecolor':'white'})


def save_figure(fig,name):
    OUT.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUT/f'{name}.png',dpi=220)
    fig.savefig(OUT/f'{name}.pdf',metadata={'CreationDate':None,'ModDate':None})
    plt.close(fig)


def paired_figure(table):
    theme()
    # Keep the country/world chart readable on one slide. Income aggregates
    # appear in the dedicated trend figure and all18 remain in the data table.
    table=table.loc[~table.entity.isin(['LIC','LMC','UMC','HIC'])].copy()
    fig,axes=plt.subplots(1,2,figsize=(12.6,6.4),sharey=True)
    fig.subplots_adjust(left=.19,right=.96,bottom=.21,top=.78,wspace=.18)
    fig.text(.055,.965,'Fertility and birth rates: 1990 to 2023',fontsize=20,weight='bold',va='top')
    fig.text(.055,.902,'Selected countries and the world · 1990 and 2023 · endpoint labels show 2023',
             fontsize=11,color=SLATE,va='top')
    fig.legend(handles=[Line2D([],[],marker='o',ls='',mfc='white',mec=SLATE,ms=7,label='1990'),
                        Line2D([],[],marker='o',ls='',mfc=TEAL,mec=TEAL,ms=7,label='2023')],
               loc='upper right',bbox_to_anchor=(.96,.878),ncol=2,frameon=False,handletextpad=.5,columnspacing=2.2)
    settings=[('fertility_births_per_woman','Fertility rate','Births per woman',2),
              ('births_per_1000_people','Crude birth rate','Births per 1,000 people in a year',1)]
    positions=np.arange(len(table))
    for ax,(column,title,unit,decimals) in zip(axes,settings):
        ax.axhspan(12.5,13.5,color=PALE,alpha=.7,zorder=0)
        ax.axhline(12.5,color='#D9E3E8',lw=1)
        ax.axhline(13.5,color='#D9E3E8',lw=1)
        for position,row in zip(positions,table.itertuples(index=False)):
            old=getattr(row,f'{column}_{FIRST_YEAR}')
            new=getattr(row,f'{column}_{LAST_YEAR}')
            if not np.isfinite(old) or not np.isfinite(new):
                continue
            ax.plot([old,new],[position,position],color='#B7CCD4',lw=2.5,zorder=1)
            ax.scatter([old],[position],s=43,fc='white',ec=SLATE,lw=1.3,zorder=3)
            ax.scatter([new],[position],s=43,fc=TEAL,ec='white',lw=.8,zorder=4)
            ax.text(.985,position,f'{new:.{decimals}f}',transform=ax.get_yaxis_transform(),
                    va='center',ha='right',fontsize=14.6,color=NAVY,weight='bold',
                    bbox={'facecolor':WARM,'edgecolor':'none','pad':.5},zorder=5)
        values=table[[f'{column}_{FIRST_YEAR}',f'{column}_{LAST_YEAR}']].to_numpy()
        ax.set_xlim(0,float(np.nanmax(values))*1.15)
        ax.set_title(title,loc='left',fontsize=14,weight='bold',pad=12)
        ax.text(.985,1.035,'2023',transform=ax.transAxes,ha='right',va='bottom',
                fontsize=10.5,color=SLATE)
        ax.set_xlabel(unit,labelpad=12,fontsize=13)
        ax.grid(axis='x',color='#E1E9ED',lw=.7)
        ax.tick_params(length=0,pad=8,labelsize=14.6)
        ax.set_yticks(positions,table.entity_name)
        ax.set_ylim(len(table)-.5,-.5)
    axes[0].get_yticklabels()[13].set_weight('bold')
    fig.text(.055,.070,'Fertility is a period estimate, not completed family size. Birth rate also reflects the population’s age structure.',
             fontsize=10,color=SLATE)
    fig.text(.055,.035,'Source: World Bank WDI / UN and national sources · CC BY4.0 · Current-vintage estimates; 2023 is the fixed comparison year.',
             fontsize=9.4,color=SLATE)
    save_figure(fig,'part_b_demography_comparison')


def income_figure(panel):
    theme()
    fig,ax=plt.subplots(figsize=(12.6,4.8))
    fig.subplots_adjust(left=.075,right=.79,bottom=.23,top=.73)
    fig.text(.055,.962,'Fertility has fallen across the world’s income groups',fontsize=20,weight='bold',va='top')
    fig.text(.055,.865,'Births per woman · published World Bank aggregates, 1990–2023 · direct labels show 2023',
             fontsize=11,color=SLATE,va='top')
    styles=[('WLD',NAVY,2.9,'solid'),('LIC',CORAL,2.1,'solid'),('LMC',TEAL,2.2,'solid'),
            ('UMC',SLATE,2.0,'dashdot'),('HIC','#967A69',2.0,'dashed')]
    endpoints=[]
    for code,color,width,dash in styles:
        data=panel.loc[panel.entity.eq(code)].sort_values('year')
        ax.plot(data.year,data.fertility_births_per_woman,color=color,lw=width,ls=dash)
        last=data.loc[data.year.eq(LAST_YEAR),'fertility_births_per_woman'].iloc[0]
        if np.isfinite(last):
            endpoints.append([last,last,color,LABELS[code]])
            ax.scatter([LAST_YEAR],[last],s=21,color=color,zorder=4)
    endpoints.sort(key=lambda x:x[0])
    for j in range(1,len(endpoints)):
        endpoints[j][1]=max(endpoints[j][1],endpoints[j-1][1]+.50)
    for value,y,color,label in endpoints:
        ax.plot([LAST_YEAR,LAST_YEAR+.6],[value,y],color=color,lw=.75,clip_on=False)
        ax.text(LAST_YEAR+.85,y,f'{label}  {value:.2f}',color=NAVY,fontsize=14,
                va='center',weight='bold',clip_on=False)
    ax.set_xlim(FIRST_YEAR-.5,LAST_YEAR+.7)
    ax.set_xticks([1990,2000,2010,2020,2023])
    ax.set_ylim(bottom=0)
    ax.set_ylabel('Births per woman',labelpad=13,fontsize=13)
    ax.tick_params(length=0,pad=7,labelsize=13)
    ax.grid(axis='y',color='#E1E9ED',lw=.7)
    fig.text(.055,.087,'Income groups describe economies, not individual people. Group differences do not identify causes or individual traits.',
             fontsize=10,color=SLATE)
    fig.text(.055,.040,'Source: World Bank WDI · Published aggregates, not averages of the 13 selected countries · Estimates and group membership may be revised.',
             fontsize=9.3,color=SLATE)
    save_figure(fig,'part_b_fertility_trends')


def build():
    panel=pd.read_csv(DATA/'part_b_demography.csv')
    summary=json.loads((TABLES/'part_b_demography_summary.json').read_text(encoding='utf-8'))
    if hashlib.sha256((DATA/'part_b_demography.csv').read_bytes()).hexdigest()!=summary['panel_sha256']:
        raise ValueError('Derived demographic panel differs from recorded acquisition')
    table=comparison_table(panel)
    table.to_csv(TABLES/'part_b_demography_comparison.csv',index=False)
    display=table[['entity_name','fertility_births_per_woman_1990','fertility_births_per_woman_2023',
                   'births_per_1000_people_1990','births_per_1000_people_2023']].copy()
    display.columns=['Country / aggregate','Fertility1990','Fertility2023','Birth rate1990','Birth rate2023']
    lines=['| '+' | '.join(display.columns)+' |','| '+' | '.join(['---']+['---:']*4)+' |']
    lines += ['| '+row[0]+' | '+' | '.join(f'{value:.2f}' for value in row[1:])+' |'
              for row in display.itertuples(index=False,name=None)]
    (TABLES/'part_b_demography_comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paired_figure(table)
    income_figure(panel)
    summary['comparison_1990_2023']=json.loads(table.to_json(orient='records'))
    summary['figures']=['outputs/part_b_demography_comparison.png','outputs/part_b_demography_comparison.pdf',
                        'outputs/part_b_fertility_trends.png','outputs/part_b_fertility_trends.pdf']
    summary['comparison_chart_entities']=[code for code in ENTITIES if code not in ('LIC','LMC','UMC','HIC')]
    summary['income_trend_entities']=['WLD','LIC','LMC','UMC','HIC']
    summary['figure_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in summary['figures']}
    save_json(TABLES/'part_b_demography_summary.json',summary)
    print(display.to_string(index=False,float_format=lambda x:f'{x:.3f}'))
    return table


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['acquire','build','all'],default='all',nargs='?')
    args=parser.parse_args()
    if args.command in ['acquire','all']:
        acquire()
    if args.command in ['build','all']:
        build()


if __name__=='__main__':
    main()
