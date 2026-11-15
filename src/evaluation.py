"""Chronological development, preregistered selection, immutable initial holdout."""
from __future__ import annotations

from pathlib import Path
import importlib.metadata
import platform

import numpy as np
import pandas as pd

from src.common import ROOT, config, read_json, sha256, utc_now, write_json
from src.forecasting import forecast_panel

FREEZE_PATHS = ["config/project.json", "config/scenarios.json", "src/preprocessing.py", "src/forecasting.py",
                "src/evaluation.py", "data/processed/daily_sales.csv", "data/processed/products.csv"]


def load_prepared():
    daily = pd.read_csv(ROOT / "data/processed/daily_sales.csv", dtype={"product_id": str}, parse_dates=["date"])
    catalog = pd.read_csv(ROOT / "data/processed/products.csv", dtype={"product_id": str}, parse_dates=["first_sale"])
    quality = read_json(ROOT / "reports/data-quality-summary.json")
    if not quality["quality_pass"]:
        raise ValueError("Data quality gates failed")
    return daily, catalog, quality


def metrics(actual, predicted, scale=None):
    y, p = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if y.shape != p.shape or y.size == 0 or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("Metric inputs must have equal nonempty shapes and finite values")
    error = p - y
    denom = float(np.abs(y).sum())
    mase = None
    if scale is not None:
        scales = np.broadcast_to(np.asarray(scale, dtype=float), y.shape)
        valid = np.isfinite(scales) & (scales > 0)
        if valid.any():
            mase = float(np.mean(np.abs(error[valid]) / scales[valid]))
    else:
        valid = np.zeros(y.shape, dtype=bool)
    return {"mae": float(np.abs(error).mean()), "rmse": float(np.sqrt(np.mean(error ** 2))),
            "wape": float(np.abs(error).sum() / denom) if denom else None,
            "bias": float(error.sum() / denom) if denom else None, "mean_error": float(error.mean()),
            "mase": mase, "mase_defined_rows": int(valid.sum()), "observations": y.size, "actual_units": float(y.sum())}


def summarize(predictions, horizons=(7, 14, 28)):
    summary, product_rows, folds = [], [], []
    for horizon in horizons:
        subset = predictions.loc[predictions.step.le(horizon)]
        for (phase, model), group in subset.groupby(["phase", "model"], sort=False):
            base = {"phase": phase, "model": model, "horizon": horizon}
            summary.append({**base, **metrics(group.actual_units, group.predicted_units, group.mase_scale),
                            "fallback_rows": int(group.fallback_reason.notna().sum())})
            for product_id, sub in group.groupby("product_id"):
                product_rows.append({**base, "product_id": product_id, **metrics(sub.actual_units, sub.predicted_units, sub.mase_scale)})
            for fold, sub in group.groupby("fold"):
                folds.append({**base, "fold": fold, "train_end": str(sub.train_end.iloc[0]),
                              **metrics(sub.actual_units, sub.predicted_units, sub.mase_scale)})
    return pd.DataFrame(summary), pd.DataFrame(product_rows), pd.DataFrame(folds)


def current_fingerprint():
    return {name: sha256(ROOT / name) for name in FREEZE_PATHS}


def verify_freeze():
    frozen = read_json(ROOT / "reports/frozen-protocol.json")
    if frozen["sha256"] != current_fingerprint():
        raise ValueError("Frozen protocol or data changed. Preserve initial results and use a separately named experiment.")
    for name, digest in frozen["development_artifacts"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError("Development evidence changed after model selection")
    return frozen


def develop():
    if (ROOT / "reports/frozen-protocol.json").exists():
        return verify_freeze()
    cfg = config()
    daily, catalog, quality = load_prepared()
    start = pd.Timestamp(quality["holdout_start"])
    windows = []
    for fold in range(cfg["backtest_windows"]):
        origin = start - pd.Timedelta(days=(cfg["backtest_windows"] - fold) * cfg["primary_horizon"] + 1)
        # Truncate even the input table: no final holdout or later development data is visible.
        past_and_validation = daily.loc[daily.date.le(origin + pd.Timedelta(days=28))]
        windows.append(forecast_panel(past_and_validation, catalog, origin, cfg["models"], phase="development", fold=fold + 1))
    predictions = pd.concat(windows, ignore_index=True)
    if predictions.actual_units.isna().any() or not (predictions.forecast_date > predictions.train_end).all():
        raise ValueError("Incomplete validation actuals or chronological split failure")
    comparison, products, folds = summarize(predictions, cfg["horizons"])
    candidates = comparison.loc[comparison.horizon.eq(28)].copy()
    candidates["tie_order"] = candidates.model.map({m: i for i, m in enumerate(cfg["models"])})
    best = candidates.sort_values(["wape", "tie_order"]).iloc[0]
    naive = candidates.loc[candidates.model.eq("seasonal_naive")].iloc[0]
    improvement = 1 - float(best.wape) / float(naive.wape) if naive.wape > 0 else 0.0
    paths = {"reports/development-predictions.csv": predictions, "reports/development-comparison.csv": comparison,
             "reports/development-product-metrics.csv": products, "reports/development-fold-metrics.csv": folds}
    for name, frame in paths.items():
        frame.to_csv(ROOT / name, index=False)
    frozen = {"frozen_at_utc": utc_now(), "selected_model": best.model, "selection_rule": cfg["selection_rule"],
              "development_wape_improvement": improvement, "forecast_quality_gate_pass": improvement >= cfg["acceptance"]["development_wape_improvement"],
              "holdout_start": quality["holdout_start"], "holdout_end": quality["date_end"], "selection_cutoff": quality["selection_cutoff"],
              "sha256": current_fingerprint(), "development_artifacts": {name: sha256(ROOT / name) for name in paths},
              "configuration": cfg, "python": platform.python_version(),
              "versions": {name: importlib.metadata.version(name) for name in ["numpy", "pandas", "statsforecast", "ortools", "streamlit"]}}
    write_json(ROOT / "reports/frozen-protocol.json", frozen)
    return frozen


def evaluate_holdout():
    frozen = verify_freeze()
    manifest = ROOT / "reports/holdout-manifest.json"
    if manifest.exists():
        recorded = read_json(manifest)
        if any(sha256(ROOT / path) != digest for path, digest in recorded["sha256"].items()):
            raise ValueError("Initial holdout evidence was modified")
        return recorded
    cfg = config()
    daily, catalog, _ = load_prepared()
    origin = pd.Timestamp(frozen["holdout_start"]) - pd.Timedelta(days=1)
    predictions = forecast_panel(daily, catalog, origin, cfg["models"], phase="holdout", fold=1)
    if predictions.actual_units.isna().any():
        raise ValueError("Holdout actuals incomplete")
    comparison, products, folds = summarize(predictions, cfg["horizons"])
    paths = {"reports/holdout-predictions.csv": predictions, "reports/holdout-comparison.csv": comparison,
             "reports/holdout-product-metrics.csv": products, "reports/holdout-fold-metrics.csv": folds}
    for path, frame in paths.items():
        frame.to_csv(ROOT / path, index=False)
    recorded = {"evaluated_at_utc": utc_now(), "protocol_sha256": sha256(ROOT / "reports/frozen-protocol.json"),
                "selected_model": frozen["selected_model"], "sha256": {path: sha256(ROOT / path) for path in paths}}
    write_json(manifest, recorded)
    pd.concat([pd.read_csv(ROOT / "reports/development-comparison.csv"), comparison], ignore_index=True).to_csv(ROOT / "reports/model-comparison.csv", index=False)
    future = forecast_panel(daily, catalog, daily.date.max(), cfg["models"], phase="future")
    future.to_csv(ROOT / "reports/future-forecasts.csv", index=False)
    return recorded
