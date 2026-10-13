"""Economic measurement and chronological, vintage-aware forecasting utilities.

All percentage transformations are computed within one ALFRED vintage. GDP is
quarterly and only the most recently published quarterly observation is carried
as a predictor; no artificial monthly GDP observations are created.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = pd.Timestamp("2026-10-13")
# Manually transcribed from the official page using the web-access tool on the
# cutoff date. The directly downloaded historical CSV ends at September final.
# This record is preliminary and never enters final-only forecast evaluation.
OCTOBER_PRELIMINARY = {
    "observation_month": "2026-10-01", "release_date": "2026-10-09",
    "status": "preliminary", "sentiment": 46.3, "current_conditions": 44.7,
    "expectations": 47.3, "next_final_release": "2026-10-23 10:00 America/New_York",
    "source_url": "https://www.sca.isr.umich.edu/",
    "release_calendar_url": "https://data.sca.isr.umich.edu/fetchdoc.php?docid=79628",
    "verified_on": "2026-10-13",
    "acquisition_method": "manual numerical transcription from official page opened by web tool; not a downloaded CSV/PDF",
}
SERIES = {
    "UNRATE": {"owner": "BLS", "name": "U-3 unemployment", "units": "percent, seasonally adjusted", "source": "https://www.bls.gov/cps/"},
    "PCEPI": {"owner": "BEA", "name": "Headline PCE price index", "units": "index, seasonally adjusted", "source": "https://www.bea.gov/data/personal-consumption-expenditures-price-index"},
    "GDPC1": {"owner": "BEA", "name": "Real GDP", "units": "chained dollars, seasonally adjusted annual rate", "source": "https://www.bea.gov/data/gdp/gross-domestic-product"},
    "DSPIC96": {"owner": "BEA", "name": "Real disposable personal income", "units": "chained dollars, seasonally adjusted annual rate", "source": "https://www.bea.gov/data/income-saving/personal-income"},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_alfred(data: str, series_id: str, vintage: str) -> pd.Series:
    frame = pd.read_csv(io.StringIO(data))
    if len(frame.columns) != 2 or frame.columns[0] not in ("observation_date", "DATE"):
        raise ValueError(f"Invalid ALFRED response: {series_id} {vintage}")
    expected = f"{series_id}_{vintage.replace('-', '')}"
    if frame.columns[1] != expected:
        raise ValueError(f"Vintage mismatch: expected {expected}; received {frame.columns[1]}")
    dates = pd.to_datetime(frame.iloc[:, 0])
    values = pd.to_numeric(frame.iloc[:, 1], errors="coerce")
    result = pd.Series(values.to_numpy(), index=dates, name=series_id).dropna().sort_index()
    if len(result) and result.index.max() > pd.Timestamp(vintage):
        raise ValueError("Observation after vintage")
    if result.index.duplicated().any():
        raise ValueError("Duplicate observation dates")
    return result


def exact_growth(values: pd.Series, periods: int, annual_power: int = 1) -> float:
    """Growth over exact calendar periods; never bridge a missing month/quarter."""
    if values.empty:
        return np.nan
    period = values.index[-1]
    lag = period - pd.DateOffset(months=periods)
    if lag not in values.index:
        return np.nan
    return float(100.0 * ((values.iloc[-1] / values.loc[lag]) ** annual_power - 1.0))


def vintage_features(vintages: dict[str, pd.Series], as_of: str) -> dict:
    result = {"month": as_of, "prediction_date": as_of, "macro_vintage": as_of,
              "timing_basis": "actual ALFRED vintage snapshot on prediction date"}
    for key, values in vintages.items():
        if values.empty:
            continue
        result[f"{key.lower()}_period"] = values.index[-1].strftime("%Y-%m-%d")
        result[f"{key.lower()}_value"] = float(values.iloc[-1])
        result[f"{key.lower()}_age_days"] = (pd.Timestamp(as_of) - values.index[-1]).days
    result["unemployment"] = result.get("unrate_value", np.nan)
    result["pce_yoy"] = exact_growth(vintages["PCEPI"], 12)
    result["price_36m"] = exact_growth(vintages["PCEPI"], 36)
    result["gdp_qoq_annualized"] = exact_growth(vintages["GDPC1"], 3, 4)
    result["gdp_yoy"] = exact_growth(vintages["GDPC1"], 12)
    result["real_income_yoy"] = exact_growth(vintages["DSPIC96"], 12)
    return result


def parse_michigan(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path).dropna(how="all")
    frame["month"] = pd.to_datetime(frame["Month"] + " " + frame["YYYY"].astype(int).astype(str), format="%B %Y")
    return frame.drop(columns=["Month", "YYYY"]).set_index("month").sort_index()


def model_matrix(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    return sm.add_constant(frame[features].astype(float), has_constant="add")


def rolling_forecasts(frame: pd.DataFrame, features: list[str], name: str,
                      min_train: int = 60, window: int | None = None,
                      target: str = "sentiment", start: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Expanding/rolling origin OLS; HAC(3) inference and past-error intervals.

    Targets must predate each prediction month. A conservative extra month is
    applied to empirical interval calibration so final-month publication timing
    cannot allow the current outcome to enter its own interval.
    """
    clean = frame.dropna(subset=features + [target]).sort_values("month").copy()
    forecasts, coefficients = [], []
    for _, row in clean.iterrows():
        train = clean.loc[clean["month"] < row["month"]]
        if window:
            train = train.tail(window)
        if len(train) < min_train or (start and row["month"] < pd.Timestamp(start)):
            continue
        fit = sm.OLS(train[target], model_matrix(train, features)).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        point = model_matrix(pd.DataFrame([row]), features)
        prediction = float(fit.predict(point).iloc[0])
        # HAC coefficient uncertainty plus residual variance; this is approximate,
        # so empirically calibrated past OOS residual intervals are also supplied.
        var_mean = float(point.to_numpy()[0] @ fit.cov_params().to_numpy() @ point.to_numpy()[0])
        half = norm.ppf(.975) * np.sqrt(max(var_mean, 0) + float(np.mean(fit.resid ** 2)))
        old = [x for x in forecasts if pd.Timestamp(x["month"]) < row["month"] - pd.DateOffset(months=1)]
        empirical_half = float(np.quantile(np.abs([x["error"] for x in old]), .95, method="higher")) if len(old) >= 24 else np.nan
        forecasts.append({"month": row["month"], "prediction_date": row["prediction_date"], "target": target,
                          "model": name, "observed": float(row[target]), "prediction": prediction,
                          "gap": float(row[target] - prediction), "error": float(row[target] - prediction),
                          "lower_95": prediction - half, "upper_95": prediction + half,
                          "empirical_lower_95": prediction - empirical_half,
                          "empirical_upper_95": prediction + empirical_half,
                          "training_n": len(train), "training_end": train["month"].max(),
                          "interval_method": "normal approximation; HAC(3) parameter variance + training residual variance"})
        for variable in fit.params.index:
            coefficients.append({"month": row["month"], "target": target, "model": name,
                                 "variable": variable, "coefficient": float(fit.params[variable]),
                                 "hac_se": float(fit.bse[variable]), "hac_pvalue": float(fit.pvalues[variable]),
                                 "training_n": len(train)})
    return pd.DataFrame(forecasts), pd.DataFrame(coefficients)


def forecast_metrics(forecasts: pd.DataFrame, sample: str) -> pd.DataFrame:
    rows = []
    for (target, model), group in forecasts.groupby(["target", "model"]):
        error = group["observed"] - group["prediction"]
        empirical = group.dropna(subset=["empirical_lower_95", "empirical_upper_95"])
        rows.append({"sample": sample, "target": target, "model": model, "n": len(group),
                     "start": group["month"].min(), "end": group["month"].max(),
                     "rmse": float(np.sqrt(np.mean(error ** 2))), "mae": float(np.mean(np.abs(error))),
                     "mean_error": float(error.mean()),
                     "coverage_95": float(((group.observed >= group.lower_95) & (group.observed <= group.upper_95)).mean()),
                     "empirical_coverage_95": float(((empirical.observed >= empirical.empirical_lower_95) & (empirical.observed <= empirical.empirical_upper_95)).mean()) if len(empirical) else np.nan,
                     "empirical_interval_n": len(empirical)})
    return pd.DataFrame(rows)


def bh_adjust(pvalues: np.ndarray) -> np.ndarray:
    order = np.argsort(pvalues)
    n = len(pvalues)
    ranked = np.minimum.accumulate((pvalues[order] * n / np.arange(1, n + 1))[::-1])[::-1]
    adjusted = np.empty(n)
    adjusted[order] = np.minimum(ranked, 1)
    return adjusted


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str, allow_nan=False), encoding="utf-8")
