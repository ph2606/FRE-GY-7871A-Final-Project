"""Estimate specified chronological macro/media comparisons and diagnostics.

Run after economics and media collection. If media is unavailable, economic
models still run and the missing comparison is explicitly recorded.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.economics import ROOT, OCTOBER_PRELIMINARY, bh_adjust, forecast_metrics, model_matrix, rolling_forecasts, write_json

warnings.filterwarnings("ignore", category=RuntimeWarning)
TABLES = ROOT / "outputs/tables"
FIGURES = ROOT / "outputs/figures"
MACRO = ["unemployment", "pce_yoy", "gdp_qoq_annualized"]
CONTROLS = ["price_36m", "real_income_yoy"]


def persistence(frame: pd.DataFrame) -> pd.DataFrame:
    d = frame.dropna(subset=["sentiment", "sentiment_lag1"]).copy()
    d = d.loc[d.month >= "2015-01-01"]
    return pd.DataFrame({"month": d.month, "prediction_date": d.prediction_date, "target": "sentiment", "model": "Persistence",
                         "observed": d.sentiment, "prediction": d.sentiment_lag1, "gap": d.sentiment - d.sentiment_lag1,
                         "error": d.sentiment - d.sentiment_lag1, "lower_95": np.nan, "upper_95": np.nan,
                         "empirical_lower_95": np.nan, "empirical_upper_95": np.nan, "training_n": 0,
                         "training_end": d.month - pd.DateOffset(months=1), "interval_method": "No interval for simple persistence benchmark"})


def diagnostic(frame: pd.DataFrame, features: list[str], model: str, sample: str) -> tuple[dict, list]:
    d = frame.dropna(subset=features + ["sentiment"])
    fit = sm.OLS(d.sentiment, model_matrix(d, features)).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    lb = acorr_ljungbox(fit.resid, lags=[min(12, max(1, len(d) // 5))], return_df=True)
    result = {"sample": sample, "model": model, "n": len(d), "adjusted_r2_in_sample": float(fit.rsquared_adj),
              "durbin_watson": float(durbin_watson(fit.resid)), "ljung_box_lag": int(lb.index[0]),
              "ljung_box_pvalue": float(lb.lb_pvalue.iloc[0]), "inference": "HAC(3); association, not causal effect"}
    coefficients = [{"sample": sample, "model": model, "variable": p, "coefficient": float(fit.params[p]),
                     "hac_se": float(fit.bse[p]), "hac_pvalue": float(fit.pvalues[p]),
                     "lower_95": float(fit.conf_int().loc[p, 0]), "upper_95": float(fit.conf_int().loc[p, 1])} for p in fit.params.index]
    return result, coefficients


def figures(frame: pd.DataFrame, forecasts: pd.DataFrame, metrics: pd.DataFrame) -> None:
    plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 180, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
    baseline = forecasts.loc[(forecasts.model == "M1_economic") & (forecasts.target == "sentiment")]
    fig, (a, b) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    a.plot(frame.month, frame.sentiment, color="#16324f", label="Michigan final sentiment")
    a.plot(baseline.month, baseline.prediction, color="#c27230", label="M1 expanding economic forecast")
    a.fill_between(baseline.month, baseline.lower_95, baseline.upper_95, color="#c27230", alpha=.15, label="Approximate 95% prediction interval")
    a.set_ylabel("Index points"); a.legend(loc="upper left", fontsize=8, ncol=2)
    a.set_title("Observed sentiment and forecasts from actual macro vintages")
    b.plot(baseline.month, baseline.gap, color="#9b3633"); b.axhline(0, color="black", linewidth=.8)
    b.set_ylabel("Observed − forecast"); b.set_xlabel("Target month; forecasts made on first calendar day")
    fig.tight_layout(); fig.savefig(FIGURES / "economic_sentiment_gap.png"); plt.close(fig)
    last = baseline.loc[baseline.month >= "2024-01-01"]
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    ax.plot(last.month, last.observed, marker="o", color="#16324f", label="Observed final")
    ax.plot(last.month, last.prediction, color="#c27230", label="Economic forecast")
    ax.fill_between(last.month, last.lower_95, last.upper_95, color="#c27230", alpha=.16)
    ax.set_title("Pre-election monitoring: unexplained pessimism under M1")
    ax.set_ylabel("Michigan index points"); ax.legend(); fig.tight_layout(); fig.savefig(FIGURES / "monitoring_2026.png"); plt.close(fig)
    common = metrics.loc[(metrics["sample"] == "common_media_oos") & (metrics.target == "sentiment")]
    if len(common):
        fig, ax = plt.subplots(figsize=(9, 4.2))
        ax.barh(common.model, common.rmse, color=["#16324f" if "media" not in x else "#c27230" for x in common.model])
        ax.set_xlabel("Out-of-sample RMSE (Michigan index points; lower is better)")
        ax.set_title(f"Same chronological holdout: {common.iloc[0]['start']:%b %Y}–{common.iloc[0]['end']:%b %Y}")
        fig.tight_layout(); fig.savefig(FIGURES / "model_comparison.png"); plt.close(fig)
    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
    for ax, y, label in zip(axes, ["unemployment", "pce_yoy", "gdp_qoq_annualized"], ["U-3 (%)", "Headline PCE YoY (%)", "Latest quarterly GDP SAAR (%)"]):
        ax.plot(frame.month, frame[y], color="#16324f"); ax.set_ylabel(label)
    axes[0].set_title("Economic information actually available at each forecast origin")
    axes[-1].set_xlabel("Forecast origin month; GDP held only as released quarterly information")
    fig.tight_layout(); fig.savefig(FIGURES / "macro_asof_information.png"); plt.close(fig)


def main():
    TABLES.mkdir(parents=True, exist_ok=True); FIGURES.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(ROOT / "data/processed/monthly_dataset.csv", parse_dates=["month", "prediction_date", "macro_vintage"])
    forecasts, coefficients, diagnostics, full_coefficients = [], [], [], []
    specs = {"M1_economic": MACRO, "M1_controls": MACRO + CONTROLS,
             "AR1": ["sentiment_lag1"], "AR_macro": ["sentiment_lag1"] + MACRO,
             "M1_seasonality": MACRO + ["month_sin", "month_cos"],
             "M1_GDP_yoy": ["unemployment", "pce_yoy", "gdp_yoy"],
             "M1_method_control": MACRO + ["web_mode_share"]}
    # Known design ramp, not estimated from outcomes: April 25%, May 50%,
    # June 75%, July onward 100% web. This is a sensitivity control.
    frame["web_mode_share"] = np.clip(((frame.month.dt.year - 2024) * 12 + frame.month.dt.month - 3) / 4, 0, 1)
    for model, features in specs.items():
        fc, coef = rolling_forecasts(frame, features, model, min_train=60)
        forecasts.append(fc); coefficients.append(coef)
        diag, fullcoef = diagnostic(frame, features, model, "historical_2010_2026")
        diagnostics.append(diag); full_coefficients += fullcoef
    fc, coef = rolling_forecasts(frame, MACRO, "M1_rolling60", min_train=60, window=60)
    forecasts.append(fc); coefficients.append(coef)
    # Current Conditions and Expectations are separate outcomes; headline is main.
    for target in ["current_conditions", "expectations"]:
        fc, coef = rolling_forecasts(frame, MACRO, "M1_economic", min_train=60, target=target)
        forecasts.append(fc); coefficients.append(coef)
    forecasts.append(persistence(frame))
    all_forecasts = pd.concat(forecasts, ignore_index=True)
    all_coefficients = pd.concat(coefficients, ignore_index=True)
    metrics = [forecast_metrics(all_forecasts, "historical_oos")]
    # One fair historical score period for all headline baselines.
    baseline_models = ["M1_economic", "M1_controls", "AR1", "AR_macro", "Persistence", "M1_rolling60", "M1_seasonality", "M1_GDP_yoy", "M1_method_control"]
    candidates = all_forecasts.loc[(all_forecasts.target == "sentiment") & all_forecasts.model.isin(baseline_models)]
    counts = candidates.groupby("month").model.nunique()
    common_months = counts.index[counts == len(baseline_models)]
    metrics.append(forecast_metrics(candidates.loc[candidates.month.isin(common_months)], "common_historical_oos"))
    media_path = ROOT / "data/processed/media_monthly.csv"
    media_status = "No media_monthly.csv available; media predictive comparison not estimated."
    media_summary = {}
    compare_specs = {}
    if media_path.exists():
        media = pd.read_csv(media_path, parse_dates=["month"])
        if "media_tone" not in media:
            raise ValueError("media_monthly.csv must have media_tone")
        media = media.loc[~media.month.duplicated()].copy()
        # Prior completed month only, no same-month or October partial contamination.
        media["media_source_month"] = media["month"]
        media["month"] = media.month + pd.DateOffset(months=1)
        media = media.rename(columns={"media_tone": "media_tone_lag1"})
        merged = frame.merge(media, on="month", how="left", suffixes=("", "_media"))
        merged.to_csv(ROOT / "data/processed/monthly_analysis.csv", index=False)
        shared = merged.dropna(subset=["sentiment", "sentiment_lag1", "media_tone_lag1"] + MACRO + CONTROLS).copy()
        compare_specs = {"M1_economic": MACRO, "M2_economic_media": MACRO + ["media_tone_lag1"],
                         "M3_economic_media_controls": MACRO + ["media_tone_lag1"] + CONTROLS,
                         "M1_controls": MACRO + CONTROLS, "AR1": ["sentiment_lag1"],
                         "AR_macro": MACRO + ["sentiment_lag1"],
                         "AR_macro_media": MACRO + ["sentiment_lag1", "media_tone_lag1"]}
        media_forecasts, media_coefficients = [], []
        for model, features in compare_specs.items():
            fc, coef = rolling_forecasts(shared, features, model, min_train=36)
            media_forecasts.append(fc); media_coefficients.append(coef)
            if len(shared) > len(features) + 12:
                diag, fullcoef = diagnostic(shared, features, model, "common_media_history")
                diagnostics.append(diag); full_coefficients += fullcoef
        media_fc = pd.concat(media_forecasts, ignore_index=True)
        if len(media_fc):
            persist = persistence(shared)
            persist = persist.loc[persist.month.isin(media_fc.month)]
            media_fc = pd.concat([media_fc, persist], ignore_index=True)
            media_fc["sample"] = "common_media_oos"
            media_fc.to_csv(TABLES / "media_forecasts.csv", index=False)
            media_coef = pd.concat(media_coefficients, ignore_index=True)
            media_coef.to_csv(TABLES / "media_rolling_coefficients.csv", index=False)
            metrics.append(forecast_metrics(media_fc, "common_media_oos"))
            media_status = "Estimated common chronological expanding-origin comparison with at least 36 prior complete monthly observations; media is lagged one month."
            common_metrics = metrics[-1].set_index("model")
            media_summary = {"complete_history_n": len(shared), "holdout_n": int(common_metrics.loc["M1_economic", "n"]),
                             "start": str(common_metrics.loc["M1_economic", "start"].date()), "end": str(common_metrics.loc["M1_economic", "end"].date()),
                             "m2_rmse_improvement_percent": float(100 * (1 - common_metrics.loc["M2_economic_media", "rmse"] / common_metrics.loc["M1_economic", "rmse"])),
                             "m3_vs_controls_rmse_improvement_percent": float(100 * (1 - common_metrics.loc["M3_economic_media_controls", "rmse"] / common_metrics.loc["M1_controls", "rmse"])),
                             "ar_media_rmse_improvement_percent": float(100 * (1 - common_metrics.loc["AR_macro_media", "rmse"] / common_metrics.loc["AR_macro", "rmse"]))}
            # Loss-difference HAC test is exploratory with few OOS months.
            wide = media_fc.pivot(index="month", columns="model", values="error")
            tests = []
            for lhs, rhs in [("M2_economic_media", "M1_economic"), ("M3_economic_media_controls", "M1_controls"), ("AR_macro_media", "AR_macro")]:
                difference = wide[lhs] ** 2 - wide[rhs] ** 2
                fit = sm.OLS(difference, np.ones((len(difference), 1))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
                tests.append({"augmented": lhs, "baseline": rhs, "n": len(difference),
                              "mean_squared_loss_difference": float(difference.mean()), "hac_pvalue_two_sided": float(fit.pvalues.iloc[0]),
                              "interpretation": "Exploratory predictive loss comparison; nested model and small-sample caveats; not causality"})
            adjusted = bh_adjust(np.array([x["hac_pvalue_two_sided"] for x in tests]))
            for record, value in zip(tests, adjusted): record["bh_qvalue"] = float(value)
            pd.DataFrame(tests).to_csv(TABLES / "predictive_loss_tests.csv", index=False)
            # Prespecified diagnostic sensitivities: dictionary alternative,
            # two/three-month lags, source composition and post-2022 history.
            # Each candidate is compared against M1 refit on its identical pool.
            sensitivity_base = merged.copy()
            for lag in (2, 3):
                extra = pd.read_csv(media_path, parse_dates=["month"])[["month", "media_tone"]]
                extra["month"] += pd.DateOffset(months=lag)
                extra = extra.rename(columns={"media_tone": f"media_tone_lag{lag}"})
                sensitivity_base = sensitivity_base.merge(extra, on="month", how="left")
            sensitivity_base["news_only_tone_lag1"] = sensitivity_base[["national_tone", "local_tone"]].mean(axis=1)
            sensitivities = {"dictionary_lag1": "vader_tone", "contextual_lag2": "media_tone_lag2", "contextual_lag3": "media_tone_lag3",
                             "exclude_social_lag1": "news_only_tone_lag1", "national_only_lag1": "national_tone", "local_only_lag1": "local_tone",
                             "price_frame_lag1": "price_level_minus_inflation_frame",
                             "post2022_contextual_lag1": "media_tone_lag1"}
            sensitivity_metrics, sensitivity_forecasts = [], []
            for sensitivity, tone_col in sensitivities.items():
                if tone_col not in sensitivity_base:
                    continue
                pool = sensitivity_base.dropna(subset=["sentiment", tone_col] + MACRO).copy()
                if sensitivity.startswith("post2022"):
                    pool = pool.loc[pool.month >= "2023-01-01"]
                base_fc, _ = rolling_forecasts(pool, MACRO, "M1_economic", min_train=36)
                extra_fc, _ = rolling_forecasts(pool, MACRO + [tone_col], "M2_sensitivity", min_train=36)
                if not len(base_fc):
                    continue
                records = forecast_metrics(pd.concat([base_fc, extra_fc]), sensitivity)
                reference = float(records.loc[records.model == "M1_economic", "rmse"].iloc[0])
                records["rmse_improvement_percent_vs_same_pool_macro"] = 100 * (1 - records.rmse / reference)
                sensitivity_metrics.append(records)
                extra_fc["sensitivity"] = sensitivity
                sensitivity_forecasts.append(extra_fc)
            if sensitivity_metrics:
                pd.concat(sensitivity_metrics).to_csv(TABLES / "media_sensitivity_metrics.csv", index=False)
                pd.concat(sensitivity_forecasts).to_csv(TABLES / "media_sensitivity_forecasts.csv", index=False)
            # Negative-control lead deliberately uses future tone: diagnostic only,
            # never included in the predictive comparison or dashboard forecasts.
            original_media = pd.read_csv(media_path, parse_dates=["month"])
            if "partial_month" in original_media:
                original_media = original_media.loc[~original_media.partial_month.astype(bool)]
            future = original_media[["month", "media_tone"]].copy()
            future["month"] -= pd.DateOffset(months=1)
            future = future.rename(columns={"media_tone": "future_media_tone_placebo"})
            placebo = frame.merge(future, on="month").dropna(subset=MACRO + ["sentiment", "future_media_tone_placebo"])
            if len(placebo) > 20:
                _, pcoef = diagnostic(placebo, MACRO + ["future_media_tone_placebo"], "Future_media_placebo_NOT_predictive", "diagnostic_only")
                pd.DataFrame(pcoef).to_csv(TABLES / "future_tone_placebo.csv", index=False)
        else:
            media_status = f"Only {len(shared)} complete historical media months; at least 37 are required for a 36-month training plus one test month."
    metrics = pd.concat(metrics, ignore_index=True)
    metrics.loc[metrics.model == "Persistence", ["coverage_95", "empirical_coverage_95"]] = np.nan
    all_forecasts.to_csv(TABLES / "forecasts.csv", index=False)
    all_coefficients.to_csv(TABLES / "rolling_coefficients.csv", index=False)
    metrics.to_csv(TABLES / "model_metrics.csv", index=False)
    pd.DataFrame(diagnostics).to_csv(TABLES / "model_diagnostics.csv", index=False)
    full = pd.DataFrame(full_coefficients)
    # BH adjustment across reported non-intercept in-sample association tests.
    selected = full.variable != "const"
    full.loc[selected, "bh_qvalue"] = bh_adjust(full.loc[selected, "hac_pvalue"].to_numpy())
    full.to_csv(TABLES / "association_coefficients.csv", index=False)
    stability = all_coefficients.groupby(["target", "model", "variable"]).agg(n=("coefficient", "size"),
                 median=("coefficient", "median"), minimum=("coefficient", "min"), maximum=("coefficient", "max"),
                 positive_fraction=("coefficient", lambda x: float((x > 0).mean()))).reset_index()
    stability.to_csv(TABLES / "coefficient_stability.csv", index=False)
    monitoring = []
    origin = frame.loc[frame.month == "2026-10-01"]
    for model, features in specs.items():
        training = frame.loc[frame.month < "2026-10-01"].dropna(subset=features + ["sentiment"])
        fit = sm.OLS(training.sentiment, model_matrix(training, features)).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        point = model_matrix(origin, features)
        pred = float(fit.predict(point).iloc[0])
        var_mean = float(point.to_numpy()[0] @ fit.cov_params().to_numpy() @ point.to_numpy()[0])
        half = 1.959963984540054 * np.sqrt(max(0, var_mean) + float(np.mean(fit.resid ** 2)))
        past = all_forecasts.loc[(all_forecasts.model == model) & (all_forecasts.target == "sentiment") & (all_forecasts.month < "2026-09-01")]
        empirical_half = float(np.quantile(abs(past.error), .95, method="higher")) if len(past) >= 24 else np.nan
        monitoring.append({"month": "2026-10-01", "prediction_date": "2026-10-01", "model": model,
                           "prediction": pred, "lower_95": pred - half, "upper_95": pred + half,
                           "empirical_lower_95": pred - empirical_half, "empirical_upper_95": pred + empirical_half,
                           "observed_preliminary": OCTOBER_PRELIMINARY["sentiment"], "gap_preliminary": OCTOBER_PRELIMINARY["sentiment"] - pred,
                           "observed_status": "preliminary", "observed_release_date": "2026-10-09",
                           "training_n": len(training), "evaluation_included": False})
    pd.DataFrame(monitoring).to_csv(TABLES / "monitoring_forecasts.csv", index=False)
    baseline = all_forecasts.loc[(all_forecasts.model == "M1_economic") & (all_forecasts.target == "sentiment")].sort_values("month")
    latest = baseline.iloc[-1]
    summary = {"cutoff": "2026-10-13", "macro_timing": "Actual ALFRED historical vintages on the first calendar day of every forecast month; within-day release time not resolved, interpret origin as end of that day.",
               "target_limitation": "Official Michigan final historical tables, not historical target vintages; partial target revision leakage cannot be excluded.",
               "gdp_treatment": "No interpolation: predictor is growth of last quarterly real GDP observation present in each vintage.",
               "interval_caution": "Approximate HAC parameter + residual intervals; empirical past-OOS-error intervals after 24 calibration observations. Report realized coverage; no guarantee under structural breaks.",
               "latest_final_forecast": {k: (str(v.date()) if isinstance(v, pd.Timestamp) else float(v) if isinstance(v, (float, np.floating)) else int(v) if isinstance(v, np.integer) else v) for k, v in latest.items() if pd.notna(v)},
               "latest_preliminary_forecast": monitoring[0], "october_preliminary_source": OCTOBER_PRELIMINARY,
               "recent_gap_mean_2026": float(baseline.loc[baseline.month >= "2026-01-01", "gap"].mean()),
               "media_comparison_status": media_status, "media_comparison": media_summary,
               "media_realtime_limitation": "Media was retrospectively sampled from present search results and scored using a model released in 2022; chronological tests condition on this corpus and are not a fully deployable historical real-time backtest.",
               "historical_common_oos_months": len(common_months),
               "interpretation": "Negative residuals are unexplained pessimism under a specified model, not proof of bias. Media associations cannot establish exposure or causal impact.",
               "controls": {"price_36m": "Cumulative headline PCE price change over prior 36 calendar months, computed in the same vintage", "real_income_yoy": "Real aggregate disposable personal income YoY, computed in same vintage; not representative household income"},
               "model_specs": specs, "media_model_specs": compare_specs, "media_min_train": 36,
               "missingness": frame[["sentiment"] + MACRO + CONTROLS].isna().sum().astype(int).to_dict()}
    write_json(TABLES / "economic_summary.json", summary)
    figures(frame, all_forecasts, metrics)
    print(json.dumps(summary, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
