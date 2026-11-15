"""Small CPU forecasting models with explicit, auditable fallbacks."""
from __future__ import annotations

from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd


@dataclass
class Forecast:
    values: np.ndarray
    requested_model: str
    effective_model: str
    fallback_reason: str | None = None


def predict(history, horizon=28, model="seasonal_naive", season=7, moving_days=28):
    y = np.asarray(history, dtype=float)
    if horizon not in (7, 14, 28):
        raise ValueError("Supported horizons are 7, 14 and 28 days")
    if model not in ("seasonal_naive", "moving_average", "auto_ets", "croston_sba"):
        raise ValueError(f"Unknown model: {model}")
    if y.ndim != 1 or not np.isfinite(y).all() or (y < 0).any():
        raise ValueError("History must be finite, one-dimensional, nonnegative recorded sales")
    if len(y) == 0:
        return Forecast(np.zeros(horizon), model, "zero_fallback", "No observed history")
    effective, reason = model, None
    try:
        if model == "seasonal_naive":
            if len(y) < season:
                raise ValueError("Fewer than seven daily observations")
            values = np.resize(y[-season:], horizon)
        elif model == "moving_average":
            values = np.full(horizon, y[-moving_days:].mean())
        else:
            if len(y) < 2 * season:
                raise ValueError("Statistical model requires at least two seasons")
            from statsforecast.models import AutoETS, CrostonSBA
            fitted = AutoETS(season_length=season, model="ZZZ") if model == "auto_ets" else CrostonSBA()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                values = np.asarray(fitted.forecast(y=y, h=horizon)["mean"], dtype=float)
        if len(values) != horizon or not np.isfinite(values).all():
            raise ValueError("Model returned invalid forecast")
    except (ImportError, ValueError, RuntimeError, ArithmeticError, IndexError, np.linalg.LinAlgError) as exc:
        values = np.full(horizon, y[-moving_days:].mean())
        effective, reason = "moving_average_fallback", f"{type(exc).__name__}: {exc}"
    return Forecast(np.maximum(values, 0), model, effective, reason)


def forecast_panel(daily, catalog, origin, models, horizon=28, phase="future", fold=0):
    origin = pd.Timestamp(origin)
    rows = []
    for product in catalog.itertuples():
        series = daily.loc[daily.product_id.eq(product.product_id)].sort_values("date")
        history = series.loc[series.date.le(origin), "units"].to_numpy(dtype=float)
        dates = pd.date_range(origin + pd.Timedelta(days=1), periods=horizon)
        actual = series.set_index("date").units.reindex(dates).to_numpy()
        scale = float(np.mean(np.abs(history[7:] - history[:-7]))) if len(history) > 7 else np.nan
        for model in models:
            result = predict(history, horizon, model)
            block = pd.DataFrame({"product_id": product.product_id, "product_name": product.product_name,
                                  "forecast_date": dates, "predicted_units": result.values, "actual_units": actual,
                                  "model": model, "effective_model": result.effective_model,
                                  "fallback_reason": result.fallback_reason, "train_end": origin,
                                  "train_days": len(history), "mase_scale": scale, "phase": phase, "fold": fold,
                                  "forecast_horizon": horizon, "step": np.arange(1, horizon + 1)})
            rows.append(block)
    return pd.concat(rows, ignore_index=True)
