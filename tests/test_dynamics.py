"""Substantive timing and calendar invariants for exploratory change models."""
import numpy as np
import pandas as pd
import pytest

from src.dynamics import DELTA_MACRO, common_pool, differenced_forecasts, longest_complete_run, prepare_grid


def synthetic_frame(n=60):
    rng = np.random.default_rng(872)
    frame = pd.DataFrame({"month": pd.date_range("2020-01-01", periods=n, freq="MS"),
                          "sentiment": 80 + np.cumsum(rng.normal(size=n)),
                          "unemployment": rng.normal(size=n), "pce_yoy": rng.normal(size=n),
                          "gdp_qoq_annualized": rng.normal(size=n), "price_36m": rng.normal(size=n),
                          "real_income_yoy": rng.normal(size=n), "media_tone_lag1": rng.normal(size=n)})
    frame["sentiment_lag1"] = frame.sentiment.shift(1)
    frame["media_source_month"] = frame.month - pd.DateOffset(months=1)
    frame["partial_month"] = False
    return frame


def test_missing_calendar_month_is_not_bridged_by_differences():
    frame = synthetic_frame(8).drop(index=3)
    grid = prepare_grid(frame)
    assert pd.Timestamp("2020-04-01") in set(grid.month)
    after_hole = grid.loc[grid.month == "2020-05-01"].iloc[0]
    assert np.isnan(after_hole.delta_sentiment)
    assert after_hole[DELTA_MACRO].isna().all()
    with pytest.raises(ValueError, match="calendar hole"):
        common_pool(grid)


def test_differenced_forecasts_use_known_lag_and_only_earlier_training_targets():
    grid = prepare_grid(synthetic_frame())
    # Exclude startup rows where exact lagged changes cannot be formed.
    pool = grid.iloc[2:].copy()
    one, _ = differenced_forecasts(pool, min_train=24)
    changed = pool.copy()
    cutoff = pd.Timestamp("2023-05-01")
    changed.loc[changed.month > cutoff, "delta_sentiment"] += 10000
    two, _ = differenced_forecasts(changed, min_train=24)
    a = one.loc[one.month <= cutoff, "prediction"].to_numpy()
    b = two.loc[two.month <= cutoff, "prediction"].to_numpy()
    np.testing.assert_allclose(a, b)
    np.testing.assert_allclose(one.prediction, one.known_sentiment_lag1 + one.prediction_change)
    assert (one.training_end < one.month).all()
    assert one.groupby("month").training_n.nunique().eq(1).all()
    assert one.groupby("model").month.apply(tuple).nunique() == 1


def test_sensitivity_refuses_to_silently_shorten_requested_main_holdout():
    pool = prepare_grid(synthetic_frame(20)).iloc[2:]
    with pytest.raises(ValueError, match="preserve all main holdout"):
        differenced_forecasts(pool, min_train=24, test_months=pool.month.tail(3))


def test_media_calendar_alignment_is_verified():
    frame = synthetic_frame(8)
    frame.loc[4, "media_source_month"] = frame.loc[4, "month"]
    with pytest.raises(ValueError, match="previous calendar month"):
        prepare_grid(frame)


def test_unit_root_input_keeps_longest_contiguous_span_not_concatenated_gaps():
    values = pd.Series([1., 2., np.nan, 4., 5., 6.], index=pd.date_range("2020-01-01", periods=6, freq="MS"))
    complete = longest_complete_run(values)
    assert complete.index.min() == pd.Timestamp("2020-04-01")
    assert complete.to_list() == [4., 5., 6.]
