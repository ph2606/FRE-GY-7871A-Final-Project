"""Meaningful accounting checks for observed multi-fund leveraged ETF paths."""
import numpy as np
import pandas as pd
import pytest
from src.bias_trading import simulate_funds,ASSETS


def prices():
    return pd.DataFrame(100.,index=pd.to_datetime(['2021-02-02','2021-02-03','2021-02-04']),columns=ASSETS)


def test_observed_leveraged_fund_return_is_not_multiplied_again():
    p=prices();p.UPRO=[100,110,110]
    r=simulate_funds(p,p.index[:1],[[1,0,0,0]],p.index[-1],0)
    assert r.wealth.iloc[-1]==pytest.approx(1.1)


def test_new_fund_does_not_receive_return_into_its_execution_close():
    p=prices();p.UPRO=[100,200,220]
    r=simulate_funds(p,p.index[:2],[[0,0,0,1],[1,0,0,0]],p.index[-1],0)
    assert r.wealth.iloc[1]==pytest.approx(1.)
    assert r.wealth.iloc[-1]==pytest.approx(1.1)


def test_full_fund_switch_pays_both_legs_plus_entry_and_exit():
    p=prices();c=.001
    r=simulate_funds(p,p.index[:2],[[1,0,0,0],[0,1,0,0]],p.index[-1],10)
    expected=1/(1+c)*(1-c)/(1+c)*(1-c)
    assert r.wealth.iloc[-1]==pytest.approx(expected)
    assert r.orders.sum()==4


def test_monthly_two_sided_funds_drift_between_rebalances():
    p=prices();p.UPRO=[100,200,200]
    r=simulate_funds(p,p.index[:1],[[.5,.5,0,0]],p.index[-1],0)
    assert r.wealth.iloc[1]==pytest.approx(1.5)
    assert r.weight_UPRO.iloc[1]==pytest.approx(2/3)
    assert r.weight_SPXU.iloc[1]==pytest.approx(1/3)


@pytest.mark.parametrize('target',[[1,-1,1,0],[.5,0,0,0],[np.nan,0,0,1]])
def test_rejects_borrowed_or_incomplete_fund_allocations(target):
    p=prices()
    with pytest.raises(ValueError):simulate_funds(p,p.index[:1],[target],p.index[-1])
