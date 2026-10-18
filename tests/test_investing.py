"""Cash accounting, signal timing and missing-month regression checks."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest
from src.investing import fee_fraction,simulate,trend_history,labor_guard,next_session,parse_prices


def prices():
    return pd.DataFrame({'SPY':[100.,110.,121.],'BIL':[100.,100.,100.]},
                        index=pd.to_datetime(['2020-01-02','2020-01-03','2020-01-06']))


def test_new_allocation_never_receives_the_execution_days_return():
    p=prices()
    result=simulate(p,p.index[:2],pd.Series([0.,1.]),p.index[-1],0)
    assert result.wealth.iloc[1]==pytest.approx(1.)
    assert result.wealth.iloc[-1]==pytest.approx(1.1)


def test_entry_and_exit_are_charged_in_a_flat_market():
    p=prices()*0+100
    result=simulate(p,p.index[:1],pd.Series([.8]),p.index[-1],10)
    assert result.wealth.iloc[-1]==pytest.approx((1-.001)/(1+.001))
    assert result.fee_dollars_per_initial_dollar.sum()>0


def test_weights_drift_between_rebalances():
    p=prices();p.SPY=[100,200,200]
    result=simulate(p,p.index[:1],pd.Series([.6]),p.index[-1],0)
    assert result.wealth.iloc[1]==pytest.approx(1.6)
    assert result.equity_weight.iloc[1]==pytest.approx(.75)


def test_cost_is_self_financing_on_both_trade_legs():
    before=np.array([.75,.25]);target=np.array([.6,.4]);rate=.001
    fee,turnover=fee_fraction(before,target,rate)
    actual=np.abs(target*(1-fee)-before).sum()
    assert turnover==pytest.approx(actual)
    assert fee==pytest.approx(rate*actual)


def test_future_prices_do_not_change_an_origin_signal():
    p=pd.Series(np.arange(24)+100.,index=pd.date_range('2019-01-01',periods=24,freq='MS'))
    original=trend_history(p,'2020-01-01')
    p.loc[p.index>='2020-01-01']*=100
    assert trend_history(p,'2020-01-01')==original


def test_shutdown_month_cannot_be_bridged_in_labor_guard():
    p=pd.Series(4.,index=pd.date_range('2024-01-01','2025-11-01',freq='MS'))
    assert labor_guard(p)==pytest.approx(0.)
    assert np.isnan(labor_guard(p.drop(pd.Timestamp('2025-10-01'))))


def test_execution_is_strictly_after_first_calendar_day():
    sessions=pd.to_datetime(['2020-09-01','2020-09-02','2020-09-03'])
    assert next_session(sessions,'2020-09-01')==sessions[1]


def test_adjusted_prices_are_not_replaced_by_raw_close():
    payload={'chart':{'error':None,'result':[{'meta':{'symbol':'SPY','currency':'USD','exchangeTimezoneName':'America/New_York'},
        'timestamp':[1577975400,1578061800],'indicators':{'quote':[{'close':[100,101]}],
        'adjclose':[{'adjclose':[80,81]}]}}]}}
    frame,_=parse_prices(payload,'SPY')
    assert frame.adjusted_close.tolist()==[80,81]
    with pytest.raises(AssertionError):parse_prices(payload,'BIL')
