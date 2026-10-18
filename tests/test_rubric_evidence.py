"""Evidence packaging must preserve samples and prospective design assumptions."""
import numpy as np
import pandas as pd
import pytest
from scipy.stats import nct, t

from src.rubric_evidence import CONTRASTS, loss_contrasts, power_plan


def forecasts():
    rows=[]
    months=pd.date_range('2020-01-01',periods=12,freq='MS')
    for pair,(augmented,baseline) in enumerate(CONTRASTS):
        for i,month in enumerate(months):
            rows += [{'month':month,'model':baseline,'error':1+i/10+pair},
                     {'month':month,'model':augmented,'error':.7+i/8+pair}]
    return pd.DataFrame(rows)


def test_loss_packaging_refuses_a_silently_changed_comparison_sample():
    data=forecasts()
    missing=data.loc[~((data.model==CONTRASTS[0][0])&(data.month==data.month.min()))]
    with pytest.raises(ValueError,match='identical evaluation months'):
        loss_contrasts(missing)


def test_loss_units_and_hac_interval_match_an_independent_sandwich():
    data=forecasts();row=loss_contrasts(data,maxlags=1).iloc[0]
    base=data[data.model.eq(CONTRASTS[0][1])].error.to_numpy()
    augmented=data[data.model.eq(CONTRASTS[0][0])].error.to_numpy()
    difference=augmented**2-base**2;resid=difference-difference.mean();n=len(resid)
    # Bartlett lag-one covariance of the sample mean, with no finite-n correction.
    variance=(resid@resid+resid[1:]@resid[:-1])/n**2
    assert row.mean_squared_loss_difference==pytest.approx(difference.mean())
    assert row.hac_se_mean_loss_difference==pytest.approx(np.sqrt(variance))
    assert row.loss_difference_lower_95 < row.mean_squared_loss_difference < row.loss_difference_upper_95


def test_power_count_is_smallest_complete_n_meeting_target_and_inflates_by_arm():
    plan=power_plan(.25)
    assert plan['complete_outcomes_per_arm']==253
    assert plan['randomized_total']==951
    def achieved(n):
        critical=t.ppf(.975,2*n-2);noncentrality=.25*np.sqrt(n/2)
        return nct.sf(critical,2*n-2,noncentrality)+nct.cdf(-critical,2*n-2,noncentrality)
    assert achieved(252)<.80<=achieved(253)
    assert plan['randomized_per_arm']*.8 >= plan['complete_outcomes_per_arm']


@pytest.mark.parametrize('effect,attrition',[(0,.2),(-.1,.2),(np.nan,.2),(.25,1)])
def test_invalid_power_assumptions_are_not_published(effect,attrition):
    with pytest.raises(ValueError):
        power_plan(effect,attrition=attrition)
