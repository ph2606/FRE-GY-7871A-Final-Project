"""Exploratory persistence and differenced-forecast sensitivity analysis.

Run ``python -m src.dynamics`` after the frozen main analysis. This module does
not change its sample, forecasts, primary tests, or any provider comparison.

Differences in available macro features include both newly observed periods and
published revisions. They are not a pure measure of economic news or surprises.
ADF/KPSS diagnostics have opposing nulls and are sensitive to structural breaks;
they cannot establish that a short, disrupted series has a unit root.
"""
from __future__ import annotations

import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss

from src.economics import ROOT, bh_adjust, sha256, write_json

MACRO = ["unemployment", "pce_yoy", "gdp_qoq_annualized"]
CONTROLS = ["price_36m", "real_income_yoy"]
DELTA_MACRO = [f"d_{x}" for x in MACRO]
SPECS = {
    "D_macro": DELTA_MACRO,
    "D_macro_media": DELTA_MACRO + ["media_tone_lag1"],
    "D_macro_AR": DELTA_MACRO + ["delta_sentiment_lag1"],
    "D_macro_AR_media": DELTA_MACRO + ["delta_sentiment_lag1", "media_tone_lag1"],
}
DYNAMIC_CONTRASTS = [("D_macro_media", "D_macro"), ("D_macro_AR_media", "D_macro_AR")]
PRIMARY_CONTRASTS = [("M2_economic_media", "M1_economic"),
                     ("M3_economic_media_controls", "M1_controls"),
                     ("AR_macro_media", "AR_macro")]


def prepare_grid(frame: pd.DataFrame) -> pd.DataFrame:
    """Form lags/differences before complete-case filtering; preserve time holes."""
    frame = frame.copy()
    frame["month"] = pd.to_datetime(frame["month"])
    if frame.month.duplicated().any():
        raise ValueError("Duplicate calendar months in dynamics input")
    if not (frame.month.dt.day == 1).all():
        raise ValueError("Month labels must be first calendar days")
    grid = pd.date_range(frame.month.min(), frame.month.max(), freq="MS")
    frame = frame.set_index("month").reindex(grid).rename_axis("month").reset_index()
    frame["prediction_date"] = frame["month"]
    # Do not infer a one-month lag by shifting an already filtered panel.
    frame["sentiment_lag1_exact"] = frame.sentiment.shift(1)
    frame["delta_sentiment"] = frame.sentiment - frame.sentiment_lag1_exact
    frame["delta_sentiment_lag1"] = frame.delta_sentiment.shift(1)
    for column in MACRO:
        frame[f"d_{column}"] = frame[column].diff()
    if "media_source_month" in frame:
        source_month = pd.to_datetime(frame.media_source_month)
        valid = frame.media_tone_lag1.notna()
        if not (source_month[valid] == frame.loc[valid, "month"] - pd.DateOffset(months=1)).all():
            raise ValueError("Media feature is not exactly the previous calendar month")
    return frame


def common_pool(grid: pd.DataFrame) -> pd.DataFrame:
    """Use the original main model's complete training pool, plus valid deltas."""
    main = ["sentiment", "sentiment_lag1", "media_tone_lag1"] + MACRO + CONTROLS
    pool = grid.dropna(subset=main).copy()
    needed = ["sentiment_lag1_exact", "delta_sentiment", "delta_sentiment_lag1"] + DELTA_MACRO
    if pool[needed].isna().any().any():
        raise ValueError("A calendar hole prevents preserving the main common training pool")
    if not np.allclose(pool.sentiment_lag1_exact, pool.sentiment_lag1):
        raise ValueError("Reported lagged sentiment differs from its exact calendar lag")
    if "partial_month" in pool and pool.partial_month.astype("boolean").fillna(False).any():
        raise ValueError("Partial media month cannot enter the sensitivity pool")
    return pool.sort_values("month")


def differenced_forecasts(pool: pd.DataFrame, min_train: int = 36,
                          test_months=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Forecast a change, then add the known lagged index to obtain its level."""
    pool = pool.sort_values("month").copy()
    desired = set(pd.to_datetime(test_months)) if test_months is not None else None
    rows, coefficients = [], []
    for _, origin in pool.iterrows():
        if desired is not None and origin.month not in desired:
            continue
        train = pool.loc[pool.month < origin.month]
        if len(train) < min_train:
            continue
        for model, features in SPECS.items():
            x = sm.add_constant(train[features].astype(float), has_constant="add")
            fit = sm.OLS(train.delta_sentiment, x).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
            point = sm.add_constant(pd.DataFrame([origin])[features].astype(float), has_constant="add")
            delta = float(fit.predict(point).iloc[0])
            level = float(origin.sentiment_lag1_exact + delta)
            rows.append({"month": origin.month, "prediction_date": origin.prediction_date,
                         "model": model, "observed": float(origin.sentiment),
                         "prediction": level, "error": float(origin.sentiment - level),
                         "observed_change": float(origin.delta_sentiment), "prediction_change": delta,
                         "known_sentiment_lag1": float(origin.sentiment_lag1_exact),
                         "training_n": len(train), "training_end": train.month.max(),
                         "analysis_status": "exploratory dynamic sensitivity; not a frozen primary model"})
            for variable in fit.params.index:
                coefficients.append({"month": origin.month, "model": model, "variable": variable,
                                     "coefficient": float(fit.params[variable]), "hac_se": float(fit.bse[variable]),
                                     "hac_pvalue": float(fit.pvalues[variable]), "training_n": len(train)})
    forecasts = pd.DataFrame(rows)
    if desired is not None:
        actual = set(forecasts.month) if len(forecasts) else set()
        if actual != desired:
            raise ValueError(f"Cannot preserve all main holdout months; missing {sorted(desired - actual)}")
    return forecasts, pd.DataFrame(coefficients)


def sensitivity_metrics(forecasts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model, group in forecasts.groupby("model"):
        rows.append({"model": model, "n": len(group), "start": group.month.min(), "end": group.month.max(),
                     "rmse": float(np.sqrt(np.mean(group.error ** 2))), "mae": float(np.mean(abs(group.error))),
                     "mean_error": float(group.error.mean()), "analysis_status": "exploratory"})
    result = pd.DataFrame(rows)
    lookup = result.set_index("model").rmse
    for augmented, baseline in DYNAMIC_CONTRASTS:
        result.loc[result.model == augmented, "rmse_gain_percent_vs_baseline"] = 100 * (1 - lookup[augmented] / lookup[baseline])
        result.loc[result.model == augmented, "comparison_baseline"] = baseline
    return result


def longest_complete_run(series: pd.Series) -> pd.Series:
    """Avoid pretending that observations either side of a gap are adjacent."""
    valid = series.notna()
    if not valid.any():
        return series.iloc[:0]
    groups = (~valid).cumsum()
    pieces = [values for _, values in series.loc[valid].groupby(groups.loc[valid])]
    return max(pieces, key=len)


def unit_root_diagnostics(grid: pd.DataFrame, pool: pd.DataFrame) -> pd.DataFrame:
    rows = []
    last_target = grid.loc[grid.sentiment.notna(), "month"].max()
    historical = grid.loc[grid.month <= last_target]
    variables = ["sentiment"] + MACRO + CONTROLS + ["media_tone_lag1", "delta_sentiment"]
    for sample, frame in [("historical", historical), ("common_media_pool", pool)]:
        for variable in variables:
            values = longest_complete_run(frame.set_index("month")[variable])
            if len(values) < 24 or values.nunique() < 4:
                continue
            adf = adfuller(values, regression="c", autolag="AIC")
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                result = kpss(values, regression="c", nlags="auto")
            boundary = "within tabulated range"
            for warning in caught:
                message = str(warning.message)
                if "smaller" in message:
                    boundary = f"p < {result[1]:.2f}"
                elif "greater" in message:
                    boundary = f"p > {result[1]:.2f}"
            rows.append({"sample": sample, "variable": variable, "n": len(values),
                         "start": values.index.min(), "end": values.index.max(),
                         "lag1_correlation": float(values.autocorr()), "adf_statistic": float(adf[0]),
                         "adf_pvalue": float(adf[1]), "adf_lags_aic": int(adf[2]),
                         "kpss_statistic": float(result[0]), "kpss_pvalue_tabulated": float(result[1]),
                         "kpss_pvalue_boundary": boundary, "kpss_lags_auto": int(result[2]),
                         "adf_null": "unit root", "kpss_null": "level stationarity",
                         "interpretation": "Exploratory diagnostics; structural breaks can invalidate a unit-root reading"})
    return pd.DataFrame(rows)


def loss_hac_diagnostics(forecasts: pd.DataFrame, contrasts, family: str) -> pd.DataFrame:
    wide = forecasts.pivot(index="month", columns="model", values="error").sort_index()
    rows = []
    for bandwidth in (3, 6, 12):
        family_rows = []
        for augmented, baseline in contrasts:
            paired = wide[[augmented, baseline]].dropna()
            difference = paired[augmented] ** 2 - paired[baseline] ** 2
            fit = sm.OLS(difference, np.ones((len(difference), 1))).fit(
                cov_type="HAC", cov_kwds={"maxlags": bandwidth})
            family_rows.append({"family": family, "augmented": augmented, "baseline": baseline,
                                "n": len(paired), "start": paired.index.min(), "end": paired.index.max(),
                                "hac_maxlags": bandwidth, "primary_bandwidth": bandwidth == 3,
                                "mean_squared_loss_difference": float(difference.mean()),
                                "hac_se_mean_loss_difference": float(fit.bse.iloc[0]),
                                "hac_pvalue_two_sided": float(fit.pvalues.iloc[0]),
                                "family_size": len(contrasts),
                                "interpretation": "Exploratory nested-model loss comparison; limited sample; not causal"})
        adjusted = bh_adjust(np.array([r["hac_pvalue_two_sided"] for r in family_rows]))
        for record, qvalue in zip(family_rows, adjusted):
            record["bh_qvalue_within_bandwidth_family"] = float(qvalue)
        rows += family_rows
    return pd.DataFrame(rows)


def main():
    input_path = ROOT / "data/processed/monthly_analysis.csv"
    reference_path = ROOT / "outputs/tables/media_forecasts.csv"
    out = ROOT / "outputs/tables"
    out.mkdir(parents=True, exist_ok=True)
    grid = prepare_grid(pd.read_csv(input_path))
    pool = common_pool(grid)
    reference = pd.read_csv(reference_path, parse_dates=["month"])
    test_months = sorted(reference.month.unique())
    forecasts, coefficients = differenced_forecasts(pool, test_months=test_months)
    expected_n = len(test_months)
    if not (forecasts.groupby("model").size() == expected_n).all():
        raise ValueError("Dynamic models do not share the main model's complete holdout")
    roots = unit_root_diagnostics(grid, pool)
    metrics = sensitivity_metrics(forecasts)
    losses = pd.concat([
        loss_hac_diagnostics(reference, PRIMARY_CONTRASTS, "original_three_contrasts_bandwidth_sensitivity"),
        loss_hac_diagnostics(forecasts, DYNAMIC_CONTRASTS, "exploratory_differenced_two_contrasts"),
    ], ignore_index=True)
    for name, table in [("unit_root", roots), ("differenced_forecasts", forecasts),
                        ("differenced_coefficients", coefficients), ("differenced_metrics", metrics), ("loss_hac", losses)]:
        table.to_csv(out / f"dynamics_{name}.csv", index=False)
    sentiment = roots.loc[(roots["sample"] == "historical") & (roots.variable == "sentiment")].iloc[0]
    summary = {
        "status": "exploratory sensitivity added after the frozen primary analysis; not preregistered",
        "input_sha256": {str(input_path.relative_to(ROOT)): sha256(input_path), str(reference_path.relative_to(ROOT)): sha256(reference_path)},
        "pool_n": len(pool), "pool_start": str(pool.month.min().date()), "pool_end": str(pool.month.max().date()),
        "holdout_n": expected_n, "holdout_start": str(pd.Timestamp(test_months[0]).date()),
        "holdout_end": str(pd.Timestamp(test_months[-1]).date()), "minimum_training_months": 36,
        "specifications": SPECS,
        "level_reconstruction": "forecast S[t] = known latest-final S[t-1] + forecast delta S[t]",
        "macro_difference_definition": "Month-to-month change in the information feature available at successive origins; includes new reference periods and revisions, not a surprise measure",
        "timing": "All changes and lags on full calendar grid before selecting the identical main training pool and holdout; no future outcomes enter training",
        "unit_root_caution": "ADF has a unit-root null; KPSS a stationarity null. Short samples, structural breaks and regime shifts prevent definitive integration or cointegration claims.",
        "historical_sentiment_diagnostics": {"n": int(sentiment.n), "lag1_correlation": float(sentiment.lag1_correlation),
                                             "adf_pvalue": float(sentiment.adf_pvalue), "kpss_pvalue_tabulated": float(sentiment.kpss_pvalue_tabulated)},
        "metrics": json.loads(metrics.to_json(orient="records", date_format="iso")),
        "dynamic_loss_tests_hac3": losses.loc[(losses.family == "exploratory_differenced_two_contrasts") & (losses.hac_maxlags == 3)].to_dict("records"),
        "multiple_testing": "Original three contrasts unchanged; new two contrasts form a separately identified exploratory BH family at each bandwidth. HAC6/12 are bandwidth diagnostics, not additional primary discoveries.",
        "limitations": ["Historical Michigan target/lag revisions are not vintaged", "Retrospective corpus and model representations",
                        "HAC does not cure nonstationarity, structural breaks or endogeneity", "Small nested-model loss tests do not prove equivalence or absence of useful effects"],
    }
    write_json(out / "dynamics_summary.json", summary)
    print(json.dumps({"pool_n": len(pool), "holdout_n": expected_n, "metrics": summary["metrics"],
                      "sentiment_diagnostics": summary["historical_sentiment_diagnostics"]}, indent=2))


if __name__ == "__main__":
    main()
