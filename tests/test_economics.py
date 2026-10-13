"""Tests target substantive measurement/timing mistakes rather than file layout."""
import numpy as np
import pandas as pd
import pytest

from src.economics import exact_growth, parse_alfred, rolling_forecasts, vintage_features


def test_vintage_identity_rejects_wrong_date():
    with pytest.raises(ValueError, match="Vintage mismatch"):
        parse_alfred("observation_date,UNRATE_20261013\n2026-09-01,4.2\n", "UNRATE", "2018-01-01")


def test_yoy_uses_twelve_calendar_months_and_missing_month_not_bridged():
    series = pd.Series([100., 105., 110.], index=pd.to_datetime(["2024-01-01", "2024-12-01", "2025-01-01"]))
    assert exact_growth(series, 12) == pytest.approx(10.)
    assert np.isnan(exact_growth(series.drop(pd.Timestamp("2024-01-01")), 12))


def test_gdp_annualized_distinct_from_yoy():
    gdp = pd.Series([100., 101., 102., 103., 104.], index=pd.date_range("2024-01-01", periods=5, freq="QS"))
    assert exact_growth(gdp, 3, 4) == pytest.approx(100 * ((104 / 103) ** 4 - 1))
    assert exact_growth(gdp, 12) == pytest.approx(4.)


def test_features_use_only_vintage_available_quarter():
    month = pd.date_range("2022-01-01", periods=40, freq="MS")
    monthly = pd.Series(np.arange(100., 140.), index=month)
    gdp = pd.Series([100., 101., 102., 103., 104.], index=pd.date_range("2024-01-01", periods=5, freq="QS"))
    out = vintage_features({"UNRATE": monthly, "PCEPI": monthly, "GDPC1": gdp, "DSPIC96": monthly}, "2025-05-01")
    assert out["gdpc1_period"] == "2025-01-01"
    assert out["gdp_qoq_annualized"] == pytest.approx(100 * ((104 / 103) ** 4 - 1))


def test_rolling_forecast_cannot_use_future_outcomes():
    rng = np.random.default_rng(123)
    frame = pd.DataFrame({"month": pd.date_range("2010-01-01", periods=30, freq="MS"),
                          "prediction_date": pd.date_range("2010-01-01", periods=30, freq="MS"),
                          "x": rng.normal(size=30), "sentiment": rng.normal(size=30)})
    one, _ = rolling_forecasts(frame, ["x"], "test", min_train=12)
    frame.loc[frame.month > "2011-06-01", "sentiment"] += 10000
    two, _ = rolling_forecasts(frame, ["x"], "test", min_train=12)
    a = one.loc[one.month <= "2011-06-01", "prediction"].to_numpy()
    b = two.loc[two.month <= "2011-06-01", "prediction"].to_numpy()
    np.testing.assert_allclose(a, b)
    assert (one.training_end < one.month).all()
