"""Three fixed, news-framing-only experiments using observed leveraged ETF paths."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import time

import numpy as np
import pandas as pd
import requests
from statsmodels.stats.multitest import multipletests

from .economics import ROOT, sha256
from .investing import calendar, parse_prices, next_session, fee_fraction, save_json, hac_test

RAW=ROOT/'data/raw/bias_trading'
DATA=ROOT/'data/processed'
OUT=ROOT/'outputs/tables'
PROTOCOL=ROOT/'docs/BIAS_TRADING_PROTOCOL.md'
START='2020-01-01'
STOP='2026-10-07'
FIRST='2021-02-01'
LAST='2026-09-01'
ASSETS=['UPRO','SPXU','SPY','BIL']
RULES=['Fade_gap','Follow_gap','Wait_turn']
LABELS={'Fade_gap':'Fade the gap','Follow_gap':'Follow the gap','Wait_turn':'Wait for a turn',
        'SPY_hold':'S&P 500 fund (SPY)','BIL_hold':'Treasury-bill fund (BIL)',
        'UPRO_hold':'Always 3x up (UPRO)','SPXU_hold':'Always 3x down (SPXU)',
        'Two_sided_50_50':'Half UPRO / half SPXU','Static_60_40':'60% SPY / 40% BIL'}


def acquire():
    RAW.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True)
    protocol_hash=sha256(PROTOCOL)
    old_meta=json.loads((OUT/'investment_acquisition.json').read_text())
    old_path=DATA/'investment_prices.csv'
    assert sha256(old_path)==old_meta['prices_sha256']
    old=pd.read_csv(old_path,parse_dates=['date']).set_index('date').loc[START:]
    old=old.loc[old.index<pd.Timestamp(STOP)]
    pieces=[old];sources=[]
    for ticker in ['UPRO','SPXU']:
        url=f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
        params={'period1':int(pd.Timestamp(START,tz='America/New_York').timestamp()),
                'period2':int(pd.Timestamp(STOP,tz='America/New_York').timestamp()),
                'interval':'1d','events':'div,splits','includeAdjustedClose':'true'}
        path=RAW/f'{ticker}_{START}_{STOP}.json';meta_path=path.with_suffix('.meta.json')
        if path.exists():
            meta=json.loads(meta_path.read_text())
            assert meta['sha256']==sha256(path) and meta['params']==params and meta['base_url']==url
            assert meta['protocol_sha256_before_performance']==protocol_hash
            payload=json.loads(path.read_text())
        else:
            for attempt in range(4):
                try:
                    response=requests.get(url,params=params,headers={'User-Agent':'Mozilla/5.0 (academic research)'},timeout=60)
                    response.raise_for_status();payload=response.json();parse_prices(payload,ticker,START,STOP)
                    break
                except (requests.RequestException,ValueError,KeyError,AssertionError):
                    if attempt==3:raise
                    time.sleep(1+attempt)
            path.write_bytes(response.content)
            meta={'ticker':ticker,'base_url':url,'url':response.url,'params':params,'sha256':sha256(path),
                  'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
                  'protocol_sha256_before_performance':protocol_hash,'http_status':response.status_code,
                  'bytes':len(response.content)}
            save_json(meta_path,meta)
        prices,events=parse_prices(payload,ticker,START,STOP)
        expected=calendar(START,pd.Timestamp(STOP)-pd.Timedelta(days=1))
        assert prices.index.equals(expected),f'Missing or extra exchange sessions: {ticker}'
        pieces.append(prices.adjusted_close.rename(ticker))
        sources.append({**meta,'sessions':len(prices),'dividend_events':len(events.get('dividends',{})),
                        'split_events':len(events.get('splits',{}))})
    combined=pd.concat(pieces,axis=1)[ASSETS]
    expected=calendar(START,pd.Timestamp(STOP)-pd.Timedelta(days=1))
    assert combined.index.equals(expected) and combined.notna().all().all() and combined.gt(0).all().all()
    combined.to_csv(DATA/'bias_trading_prices.csv',index_label='date')
    save_json(OUT/'bias_trading_acquisition.json',{
        'protocol_sha256_before_performance':protocol_hash,'sources':sources,
        'existing_spy_bil_prices_sha256':sha256(old_path),
        'existing_spy_bil_history_already_known':True,
        'prices_sha256':sha256(DATA/'bias_trading_prices.csv'),'calendar':'XNYS',
        'no_missing_exchange_sessions':True,
        'adjustment_reference':'https://help.yahoo.com/kb/SLN28256.html',
        'treatment':'Observed retrospective split/distribution-adjusted ETF prices; no multiplication of monthly returns'})
    print('Acquired complete UPRO/SPXU daily paths and joined frozen SPY/BIL reference prices.')


def simulate_funds(prices,schedule,targets,exit_date,cost_bps=10):
    """Hold observed fund units; the leverage and daily reset live inside the ETF."""
    columns=list(prices.columns)
    target_array=np.asarray(targets,dtype=float)
    if (target_array.shape!=(len(schedule),len(columns)) or not np.isfinite(target_array).all()
            or (target_array<0).any() or not np.allclose(target_array.sum(axis=1),1.,atol=1e-12)):
        raise ValueError('Each fund allocation must be finite, nonnegative and sum to one')
    schedule=pd.DatetimeIndex(schedule)
    if schedule.has_duplicates:raise ValueError('Duplicate execution dates')
    plan=dict(zip(schedule,target_array))
    p=prices.loc[schedule.min():pd.Timestamp(exit_date)]
    assert len(p)>1 and p.notna().all().all() and p.gt(0).all().all()
    assert set(schedule).issubset(set(p.index)) and p.index[-1]==pd.Timestamp(exit_date)
    holdings=np.zeros(len(columns));previous=1.;rate=cost_bps/10000;rows=[]
    for i,(date,values) in enumerate(p.iterrows()):
        if i:holdings*=values.to_numpy()/p.iloc[i-1].to_numpy()
        value=float(holdings.sum()) if i else 1.
        fee_dollars=turnover=0.;orders=0
        if date in plan:
            before=holdings/value if i else np.zeros(len(columns))
            fee,turnover=fee_fraction(before,plan[date],rate)
            after=plan[date]*value*(1-fee)
            orders=int((np.abs(after-holdings)>1e-12).sum())
            fee_dollars=value*fee;holdings=after
        if date==p.index[-1]:
            fee_dollars+=holdings.sum()*rate;turnover+=1.
            orders+=int((holdings>1e-12).sum());holdings*=1-rate
        wealth=float(holdings.sum());weights=holdings/wealth
        rows.append({'date':date,'wealth':wealth,'return':wealth/previous-1,
                     'traded_notional_fraction':turnover,'orders':orders,
                     'fee_dollars_per_initial_dollar':fee_dollars,
                     **{f'weight_{name}':float(weight) for name,weight in zip(columns,weights)}})
        previous=wealth
    frame=pd.DataFrame(rows)
    frame['drawdown']=frame.wealth/np.maximum.accumulate(np.r_[1.,frame.wealth.to_numpy()])[1:]-1
    return frame


def performance(path):
    years=(path.date.iloc[-1]-path.date.iloc[0]).days/365.25
    return {'start':str(path.date.iloc[0].date()),'end':str(path.date.iloc[-1].date()),'sessions':len(path),
            'net_total_return':float(path.wealth.iloc[-1]-1),
            'net_cagr':float(path.wealth.iloc[-1]**(1/years)-1),
            'max_drawdown':float(path.drawdown.min()),
            'volatility':float(path['return'].std(ddof=1)*np.sqrt(252)),
            'terminal_value_10000':float(10000*path.wealth.iloc[-1]),
            'annual_gross_turnover':float(path.traded_notional_fraction.sum()/years),
            'orders':int(path.orders.sum()),
            **{f'average_weight_{name}':float(path[f'weight_{name}'].iloc[:-1].mean()) for name in ASSETS}}


def targets_for(model,sub):
    if model in RULES:
        return np.array([[float(asset==fund) for asset in ASSETS] for fund in sub[model]])
    fixed={'SPY_hold':[0,0,1,0],'BIL_hold':[0,0,0,1],
           'UPRO_hold':[1,0,0,0],'SPXU_hold':[0,1,0,0],
           'Two_sided_50_50':[.5,.5,0,0],'Static_60_40':[0,0,.6,.4]}[model]
    return np.tile(fixed,(len(sub),1))


def analyze():
    from .bias_signal import monthly_spread, origin_signals
    acquisition=json.loads((OUT/'bias_trading_acquisition.json').read_text())
    assert acquisition['prices_sha256']==sha256(DATA/'bias_trading_prices.csv')
    assert acquisition['protocol_sha256_before_performance']==sha256(PROTOCOL)
    prices=pd.read_csv(DATA/'bias_trading_prices.csv',parse_dates=['date']).set_index('date')[ASSETS]
    scores_path=DATA/'media_scores.csv'
    monthly=monthly_spread(pd.read_csv(scores_path))
    monthly.to_csv(DATA/'bias_trading_monthly.csv',index=False)
    sig=origin_signals(monthly,pd.date_range(FIRST,LAST,freq='MS')).rename(columns={'origin':'month'})
    sig['execution_date']=[next_session(prices.index,month) for month in sig.month]
    sig.to_csv(DATA/'bias_trading_signals.csv',index=False)
    rows=[];paths={}
    periods={'full':(FIRST,LAST),'2021_2023':(FIRST,'2023-12-01'),
             '2024_2026':('2024-01-01',LAST)}
    for sample,(start,stop) in periods.items():
        sub=sig.loc[sig.month.between(start,stop)]
        terminal=next_session(prices.index,pd.Timestamp(stop)+pd.offsets.MonthBegin(1))
        assert terminal<pd.Timestamp('2026-10-13')
        for cost in [0,10,25]:
            for model,label in LABELS.items():
                path=simulate_funds(prices,sub.execution_date,targets_for(model,sub),terminal,cost)
                rows.append({'sample':sample,'model':model,'label':label,'cost_bps':cost,
                             'allocation_periods':len(sub),**performance(path)})
                if sample=='full' and cost==10:paths[model]=path
    metrics=pd.DataFrame(rows);metrics.to_csv(OUT/'bias_trading_metrics.csv',index=False)
    pd.concat([path.assign(model=model) for model,path in paths.items()],ignore_index=True).to_csv(OUT/'bias_trading_daily.csv',index=False)
    tests=[{'model':model,**hac_test(paths[model]['return'].to_numpy()-paths['SPY_hold']['return'].to_numpy())}
           for model in RULES]
    corrected=multipletests([row['pvalue'] for row in tests],method='holm')[1]
    for row,value in zip(tests,corrected):row['holm_pvalue']=float(value)
    main=metrics.loc[metrics['sample'].eq('full')&metrics.cost_bps.eq(10)]
    summary={'status':'retrospective_experiment_not_proven_bias_alpha','protocol_sha256':sha256(PROTOCOL),
             'script_sha256':sha256(Path(__file__)),'signal_script_sha256':sha256(ROOT/'src/bias_signal.py'),
             'rule_names':RULES,'allocation_periods':len(sig),'first_origin':FIRST,'last_origin':LAST,
             'cost_bps':10,'entry_and_liquidation_included':True,'full_metrics':main.to_dict('records'),
             'rule_fund_counts':{model:sig[model].value_counts().to_dict() for model in RULES},
             'signal_inputs_only':['Reuters negative-headline share','NPR negative-headline share','Colorado Sun negative-headline share','their previous calendar months'],
             'tests_vs_spy':tests,'test_family':'Three two-sided HAC(21) mean-daily-return contrasts versus SPY, Holm-adjusted; risk differs; these are not alpha tests',
             'daily_leverage':'UPRO +3x / SPXU -3x daily targets inside observed ETF prices, not 3x monthly return',
             'source_roster_selection':'Three continuously observed outlets selected for coverage before new strategy returns; different geography/topics confound measured relative framing',
             'limitations':['Relative negative wording is an unvalidated proxy, not verified factual or ideological bias',
                 'Retrospective titles, model availability and revised adjusted prices prevent a historical implementability claim',
                 'Rules were designed after earlier project/market findings; no untouched future test exists',
                 'Very aggressive products can lose nearly all capital; daily reset compounds and monthly holdings differ from 3x monthly market return',
                 'Assumed costs omit taxes, nonlinear impact and investor-specific commissions'],
             'acquisition':acquisition,
             'hashes':{name:sha256(ROOT/name) for name in ['data/processed/media_scores.csv','data/processed/bias_trading_prices.csv','data/processed/bias_trading_monthly.csv','data/processed/bias_trading_signals.csv']}}
    save_json(OUT/'bias_trading_summary.json',summary)
    print(main[['label','net_cagr','net_total_return','max_drawdown','terminal_value_10000']].to_string(index=False))
    print('Fund decisions:',json.dumps(summary['rule_fund_counts']))
    print('Primary conditional tests:',json.dumps(tests))
    return metrics,summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['acquire','analyze','all'])
    command=parser.parse_args().command
    if command in ['acquire','all']:acquire()
    if command in ['analyze','all']:analyze()


if __name__=='__main__':main()
