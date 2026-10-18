"""Fixed, dated SPY/BIL research allocation; no orders or parameter search."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import time

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
import exchange_calendars as xcals

from .economics import ROOT, parse_alfred, bh_adjust, sha256

RAW=ROOT/'data/raw/investing'
DATA=ROOT/'data/processed'
OUT=ROOT/'outputs/tables'
PROTOCOL=ROOT/'docs/INVESTMENT_PROTOCOL.md'
FIRST='2015-01-01'
LAST='2026-09-01'
FETCH_START='2009-01-01'
FETCH_STOP='2026-10-07'
PRIMARY='Macro_trend_80_20'
LABELS={PRIMARY:'Macro + trend allocation','SPY_hold':'SPY buy-and-hold',
        'BIL_hold':'Treasury-bill ETF','Static_60_40':'Fixed 60/40',
        'Gap_overlay':'Exploratory gap tilt','Media_overlay':'Exploratory media tilt'}


def save_json(path,value):
    def clean(x):
        if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)):return [clean(v) for v in x]
        if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
        if isinstance(x,(int,np.integer)):return int(x)
        return x
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(clean(value),indent=2,allow_nan=False,default=str),encoding='utf-8',newline='\n')


def calendar(start=FETCH_START,stop=FETCH_STOP):
    exchange=xcals.get_calendar('XNYS',start=pd.Timestamp(start)-pd.Timedelta(days=7),
                               end=pd.Timestamp(stop)+pd.Timedelta(days=7))
    return pd.DatetimeIndex(exchange.sessions_in_range(start,stop)).tz_localize(None)


def parse_prices(payload,ticker,start=FETCH_START,stop=FETCH_STOP):
    chart=payload['chart'];assert not chart.get('error'),chart.get('error')
    item=chart['result'][0];meta=item['meta']
    assert meta['symbol']==ticker and meta['currency']=='USD'
    assert meta['exchangeTimezoneName']=='America/New_York'
    dates=pd.to_datetime(item['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
    values=item['indicators']
    frame=pd.DataFrame({'date':dates,'close':values['quote'][0]['close'],
                        'adjusted_close':values['adjclose'][0]['adjclose']})
    frame=frame.loc[frame.date.ge(start)&frame.date.lt(stop)].set_index('date').sort_index()
    if frame.index.duplicated().any() or frame.isna().any().any() or not frame.gt(0).all().all():
        raise ValueError(f'Invalid/missing daily prices for {ticker}')
    return frame,item.get('events',{})


def acquire():
    RAW.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    protocol_hash=sha256(PROTOCOL);parts=[];provenance=[]
    for ticker in ['SPY','BIL']:
        url=f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
        params={'period1':int(pd.Timestamp(FETCH_START,tz='America/New_York').timestamp()),
                'period2':int(pd.Timestamp(FETCH_STOP,tz='America/New_York').timestamp()),
                'interval':'1d','events':'div,splits','includeAdjustedClose':'true'}
        path=RAW/f'{ticker}_{FETCH_START}_{FETCH_STOP}.json';meta_path=path.with_suffix('.meta.json')
        if path.exists():
            meta=json.loads(meta_path.read_text())
            assert meta['sha256']==sha256(path) and meta['params']==params and meta['base_url']==url
            payload=json.loads(path.read_text())
        else:
            for attempt in range(4):
                try:
                    response=requests.get(url,params=params,headers={'User-Agent':'Mozilla/5.0 (academic research)'},timeout=60)
                    response.raise_for_status();payload=response.json();parse_prices(payload,ticker)
                    break
                except (requests.RequestException,ValueError,KeyError,AssertionError):
                    if attempt==3:raise
                    time.sleep(1+attempt)
            path.write_bytes(response.content)
            meta={'base_url':url,'url':response.url,'params':params,'sha256':sha256(path),
                  'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256_before_performance':protocol_hash,
                  'http_status':response.status_code,'bytes':len(response.content)}
            save_json(meta_path,meta)
        prices,events=parse_prices(payload,ticker)
        expected=calendar(FETCH_START,pd.Timestamp(FETCH_STOP)-pd.Timedelta(days=1))
        assert prices.index.equals(expected),f'{ticker}: missing or extra exchange sessions'
        parts.append(prices.adjusted_close.rename(ticker))
        provenance.append({**meta,'ticker':ticker,'sessions':len(prices),
                           'dividend_events':len(events.get('dividends',{})),'split_events':len(events.get('splits',{}))})
    joined=pd.concat(parts,axis=1);assert joined.notna().all().all()
    joined.to_csv(DATA/'investment_prices.csv',index_label='date')
    save_json(OUT/'investment_acquisition.json',{'sources':provenance,'calendar':'XNYS',
              'calendar_version':xcals.__version__,'no_missing_exchange_sessions':True,
              'adjustment_reference':'https://help.yahoo.com/kb/SLN28256.html',
              'price_treatment':'Latest retrospective split/distribution adjusted close; total-return proxy, not executable quote',
              'prices_sha256':sha256(DATA/'investment_prices.csv')})


def labor_guard(series):
    """Exact month grid prevents a shutdown gap becoming a three-observation mean."""
    grid=series.reindex(pd.date_range(series.index.min(),series.index.max(),freq='MS'))
    rolling=grid.rolling(3,min_periods=3).mean()
    current=rolling.iloc[-1];history=rolling.iloc[-12:]
    if not np.isfinite(current) or history.notna().sum()<9:return np.nan
    return float(current-history.min())


def next_session(sessions,origin):
    index=sessions.searchsorted(pd.Timestamp(origin),side='right')
    if index>=len(sessions):raise ValueError('Missing execution boundary')
    return sessions[index]


def trend_history(prices,origin):
    origin=pd.Timestamp(origin);prior=origin-pd.DateOffset(months=1)
    monthly=prices.resample('MS').last()
    ten=monthly.reindex(pd.date_range(origin-pd.DateOffset(months=10),prior,freq='MS'))
    assert ten.notna().all() and len(ten)==10
    return float(ten.iloc[-1]),float(ten.mean()),bool(ten.iloc[-1]>ten.mean())


def signals(prices):
    records=[]
    forecasts=pd.read_csv(OUT/'forecasts.csv',parse_dates=['month'])
    gap=forecasts.loc[(forecasts.model=='M1_economic')&forecasts.target.eq('sentiment')].set_index('month').gap
    media=pd.read_csv(DATA/'media_monthly.csv',parse_dates=['month']).set_index('month')
    for origin in pd.date_range(FIRST,LAST,freq='MS'):
        prior=origin-pd.DateOffset(months=1)
        reference,sma,trend=trend_history(prices.SPY,origin)
        path=ROOT/'data/raw/economics/vintages/UNRATE'/f'{origin:%Y-%m-%d}.csv'
        meta=json.loads(path.with_suffix('.csv.meta.json').read_text())
        assert meta['sha256']==sha256(path)
        unemployment=parse_alfred(path.read_text(encoding='utf-8-sig'),'UNRATE',f'{origin:%Y-%m-%d}')
        guard=labor_guard(unemployment)
        weight=.8 if trend and np.isfinite(guard) and guard<.5-1e-10 else .2
        prior_gap=float(gap.get(prior,np.nan));prior_tone=float(media.media_tone.get(prior,np.nan))
        if prior in media.index:assert not bool(media.loc[prior,'partial_month'])
        records.append({'month':origin,'execution_date':next_session(prices.index,origin),
          'trend_reference_month':prior,'trend_reference_close':reference,'sma_10':sma,
          'trend_positive':trend,'unrate_period':unemployment.index[-1],
          'labor_gap_pp':guard,'labor_missing':not np.isfinite(guard),'macro_vintage_sha256':sha256(path),
          'prior_gap':prior_gap,'prior_media_tone':prior_tone,PRIMARY:weight,
          'SPY_hold':1.,'BIL_hold':0.,'Static_60_40':.6,
          'Gap_overlay':min(1.,weight+.1*(prior_gap<0)) if np.isfinite(prior_gap) else np.nan,
          'Media_overlay':max(0.,weight-.1*(prior_tone<0)) if np.isfinite(prior_tone) else np.nan})
    return pd.DataFrame(records)


def fee_fraction(before,target,rate):
    """Solve fee = rate * gross notional traded, with targets after the fee."""
    before=np.asarray(before,dtype=float);target=np.asarray(target,dtype=float)
    if rate==0:return 0.,float(np.abs(target-before).sum())
    lo,hi=0.,2*rate
    for _ in range(50):
        fee=(lo+hi)/2
        if fee<rate*np.abs(target*(1-fee)-before).sum():lo=fee
        else:hi=fee
    fee=(lo+hi)/2
    return fee,fee/rate


def simulate(prices,schedule,weights,exit_date,cost_bps=10):
    if not weights.between(0,1).all() or not weights.notna().all():raise ValueError('Invalid long-only weights')
    targets=dict(zip(pd.to_datetime(schedule),weights))
    if len(targets)!=len(schedule):raise ValueError('Duplicate rebalance dates')
    p=prices.loc[min(targets):pd.Timestamp(exit_date),['SPY','BIL']]
    assert p.notna().all().all() and p.gt(0).all().all()
    holdings=np.zeros(2);previous=1.;rate=cost_bps/10000;rows=[]
    for i,(date,values) in enumerate(p.iterrows()):
        if i:holdings*=values.to_numpy()/p.iloc[i-1].to_numpy()
        value=float(holdings.sum()) if i else 1.
        fee_dollars=turnover=0.
        if date in targets:
            target=np.array([targets[date],1-targets[date]])
            before=holdings/value if i else np.zeros(2)
            fee,turnover=fee_fraction(before,target,rate)
            fee_dollars=value*fee;holdings=target*value*(1-fee)
        if date==p.index[-1]:
            fee_dollars+=holdings.sum()*rate;holdings*=1-rate;turnover+=1.
        wealth=float(holdings.sum())
        rows.append({'date':date,'wealth':wealth,'return':wealth/previous-1,
                     'equity_weight':float(holdings[0]/wealth),'traded_notional_fraction':turnover,
                     'fee_dollars_per_initial_dollar':fee_dollars})
        previous=wealth
    frame=pd.DataFrame(rows)
    peaks=np.maximum.accumulate(np.r_[1.,frame.wealth.to_numpy()])[1:]
    frame['drawdown']=frame.wealth/peaks-1
    return frame


def metrics(path,prices):
    years=(path.date.iloc[-1]-path.date.iloc[0]).days/365.25
    riskfree=prices.BIL.reindex(pd.DatetimeIndex(path.date)).pct_change(fill_method=None).fillna(0).to_numpy()
    excess=path['return'].to_numpy()-riskfree
    std=float(np.std(excess,ddof=1))
    return {'start':str(path.date.iloc[0].date()),'end':str(path.date.iloc[-1].date()),'sessions':len(path),
       'net_total_return':float(path.wealth.iloc[-1]-1),'net_cagr':float(path.wealth.iloc[-1]**(1/years)-1),
       'volatility':float(path['return'].std(ddof=1)*np.sqrt(252)),
       'max_drawdown':float(path.drawdown.min()),'average_equity_weight':float(path.equity_weight.iloc[:-1].mean()),
       'annual_gross_turnover':float(path.traded_notional_fraction.sum()/years),
       'bil_relative_sharpe':float(excess.mean()/std*np.sqrt(252)) if std>1e-12 else np.nan,
       'terminal_value_10000':float(10000*path.wealth.iloc[-1])}


def hac_test(y,x=None):
    design=np.ones((len(y),1)) if x is None else sm.add_constant(np.asarray(x))
    fit=sm.OLS(np.asarray(y),design).fit(cov_type='HAC',cov_kwds={'maxlags':21})
    ci=np.asarray(fit.conf_int())[0]
    return {'annualized_daily_intercept':float(fit.params[0]*252),'lower_95':float(ci[0]*252),
      'upper_95':float(ci[1]*252),'pvalue':float(fit.pvalues[0]),'n':len(y),
      'market_beta':float(fit.params[1]) if x is not None else None,'method':'OLS HAC(21); annualized arithmetic daily intercept'}


def analyze():
    OUT.mkdir(parents=True,exist_ok=True)
    acquisition=json.loads((OUT/'investment_acquisition.json').read_text())
    assert acquisition['prices_sha256']==sha256(DATA/'investment_prices.csv')
    prices=pd.read_csv(DATA/'investment_prices.csv',parse_dates=['date']).set_index('date')
    sig=signals(prices);sig.to_csv(DATA/'investment_signals.csv',index=False)
    exit_date=next_session(prices.index,pd.Timestamp(LAST)+pd.offsets.MonthBegin(1))
    assert exit_date<pd.Timestamp('2026-10-13')
    rows=[];paths={};overlay_tests=[]
    periods={'full':FIRST,'common_44':'2023-02-01','2015_2019':FIRST,'2020_2022':'2020-01-01','2023_2026':'2023-01-01'}
    for period,start in periods.items():
        stop={'2015_2019':'2019-12-01','2020_2022':'2022-12-01'}.get(period,LAST)
        sub=sig.loc[sig.month.between(start,stop)]
        terminal=next_session(prices.index,pd.Timestamp(stop)+pd.offsets.MonthBegin(1))
        models=list(LABELS) if period=='common_44' else list(LABELS)[:4]
        for cost in [0,10,25]:
            for model in models:
                path=simulate(prices,sub.execution_date,sub[model],terminal,cost)
                rows.append({'sample':period,'model':model,'label':LABELS[model],'cost_bps':cost,
                             'allocation_periods':len(sub),**metrics(path,prices)})
                if cost==10 and period in ['full','common_44']:
                    paths[(period,model)]=path
    result=pd.DataFrame(rows);result.to_csv(OUT/'investment_metrics.csv',index=False)
    for period in ['full','common_44']:
        combined=pd.concat([path.assign(model=model) for (sample,model),path in paths.items() if sample==period],ignore_index=True)
        combined.to_csv(OUT/f'investment_{period}_daily.csv',index=False)
    primary=paths[('full',PRIMARY)];static=paths[('full','Static_60_40')]
    market=prices.SPY.reindex(pd.DatetimeIndex(primary.date)).pct_change(fill_method=None).fillna(0).to_numpy()
    bills=prices.BIL.reindex(pd.DatetimeIndex(primary.date)).pct_change(fill_method=None).fillna(0).to_numpy()
    tests={'primary_minus_static':hac_test(primary['return'].to_numpy()-static['return'].to_numpy()),
           'bil_relative_market_model':hac_test(primary['return'].to_numpy()-bills,market-bills)}
    base=paths[('common_44',PRIMARY)]
    for model in ['Gap_overlay','Media_overlay']:
        overlay_tests.append({'model':model,**hac_test(paths[('common_44',model)]['return'].to_numpy()-base['return'].to_numpy())})
    q=bh_adjust(np.array([r['pvalue'] for r in overlay_tests]))
    for record,value in zip(overlay_tests,q):record['bh_qvalue']=float(value)
    common_sig=sig.loc[sig.month.between('2023-02-01',LAST)]
    common_market=prices.SPY.reindex(pd.DatetimeIndex(base.date)).pct_change(fill_method=None).fillna(0).to_numpy()
    common_bills=prices.BIL.reindex(pd.DatetimeIndex(base.date)).pct_change(fill_method=None).fillna(0).to_numpy()
    # Explanatory diagnostics added after results: do not change the fixed rules
    # or replace the original, two-test BH family with a more favorable test.
    exposure_diagnostics={
       'status':'post-result explanatory diagnostics; conditional HAC inference, not an additional confirmatory family',
       'gap_negative_origins':int(common_sig.prior_gap.lt(0).sum()),
       'media_negative_origins':int(common_sig.prior_media_tone.lt(0).sum()),
       'origins':len(common_sig),
       'beta_adjusted_overlay_differences':[
           {'model':model,**hac_test(paths[('common_44',model)]['return'].to_numpy()-base['return'].to_numpy(),
                                    common_market-common_bills)}
           for model in ['Gap_overlay','Media_overlay']],
       'interpretation':'All negative gaps produce a constant +10 percentage-point target equity shift; predominantly negative tone produces mainly -10 points. Mean-return tests do not identify useful timing or alpha.'}
    full=result.loc[(result['sample']=='full')&(result.cost_bps==10)]
    main=full.set_index('model').loc[PRIMARY]
    summary={'status':'retrospective_research_not_live_validation','primary_model':PRIMARY,
       'protocol_sha256':sha256(PROTOCOL),'script_sha256':sha256(Path(__file__)),
       'market_retrieval':acquisition['sources'],'rule':'80% SPY if prior-month price > 10-month SMA and as-of labor deterioration <0.50pp; otherwise 20%; remainder BIL',
       'cost_bps_per_dollar_traded':10,'entry_and_final_liquidation_charged':True,
       'full_metrics':full.to_dict('records'),'hac_tests':tests,'overlay_tests':overlay_tests,
       'exposure_diagnostics':exposure_diagnostics,
       'practical_conclusion':'Prefer the simple monthly 60% SPY / 40% BIL benchmark after this retrospective comparison; its positive historical profit is not validated media alpha or guaranteed future profit. This preference was not the preselected primary strategy.',
       'positive_historical_net_profit':bool(main.net_total_return>0),'primary_allocation_periods':len(sig),
       'common_allocation_periods':int(result.loc[result['sample'].eq('common_44'),'allocation_periods'].iloc[0]),
       'missing_labor_origins':sig.loc[sig.labor_missing,'month'].astype(str).tolist(),
       'selection':'Fixed protocol before calculating market/strategy performance; no threshold search; development after original findings; not untouched OOS',
       'limitations':['Retrospective adjusted prices, synthetic fractional total-return units and assumed frictions',
           'Taxes and nonlinear market impact omitted; BIL is not a guaranteed cash deposit',
           'Gap overlay uses revised survey targets; media overlay uses reconstructed wording and later representations',
           'Positive historical net return is not alpha or a promise of future profit'],
       'hashes':{name:sha256(ROOT/name) for name in ['data/processed/investment_prices.csv','data/processed/investment_signals.csv','outputs/tables/forecasts.csv','data/processed/media_monthly.csv']}}
    save_json(OUT/'investment_summary.json',summary)
    print(full[['label','net_total_return','net_cagr','max_drawdown','average_equity_weight']].to_string(index=False))
    print(json.dumps({'hac_tests':tests,'overlay_tests':overlay_tests},indent=2))
    return result,summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['acquire','analyze','all'])
    command=parser.parse_args().command
    if command in ['acquire','all']:acquire()
    if command in ['analyze','all']:analyze()


if __name__=='__main__':main()
