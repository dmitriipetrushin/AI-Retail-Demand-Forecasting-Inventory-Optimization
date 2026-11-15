import numpy as np
import pandas as pd
import pytest

from src.common import ROOT, config, read_json, sha256
from src.data_loader import load_raw
from src.evaluation import load_prepared, verify_freeze, metrics, evaluate_holdout
from src.forecasting import forecast_panel
from src.dashboard_data import load_dashboard

pytestmark = pytest.mark.integration


def require(path):
    if not (ROOT / path).exists():
        pytest.skip(f"Run the documented pipeline first: missing {path}")


def test_official_workbook_loaded_and_provenance_matches():
    require("data/raw/Online Retail.xlsx")
    raw = load_raw()
    manifest = read_json(ROOT / "data/source-manifest.json")
    assert len(raw) == 541909
    assert not manifest["synthetic"]
    assert sha256(ROOT / "data/raw/Online Retail.xlsx") == manifest["workbook_sha256"]


def test_prepared_real_data_and_real_model_pipeline():
    require("data/processed/daily_sales.csv")
    daily, catalog, quality = load_prepared()
    assert quality["raw_transactions"] == quality["valid_transactions"] + quality["removed_transactions"]
    assert len(catalog) == 25
    assert not daily.duplicated(["product_id", "date"]).any()
    result = forecast_panel(daily, catalog.head(2), "2011-11-10", ["auto_ets", "seasonal_naive"])
    assert len(result) == 112
    assert result.fallback_reason.isna().all()
    assert result.actual_units.notna().all()
    assert (result.train_end < result.forecast_date).all()


def test_frozen_development_and_holdout_metrics_recompute():
    require("reports/holdout-manifest.json")
    frozen = verify_freeze()
    before = sha256(ROOT / "reports/holdout-predictions.csv")
    evaluate_holdout()
    assert before == sha256(ROOT / "reports/holdout-predictions.csv")
    dev = pd.read_csv(ROOT / "reports/development-predictions.csv", parse_dates=["train_end", "forecast_date"])
    assert dev.fold.nunique() == 3
    assert dev.forecast_date.max() < pd.Timestamp(frozen["holdout_start"])
    assert (dev.forecast_date > dev.train_end).all()
    predictions = pd.read_csv(ROOT / "reports/holdout-predictions.csv")
    comparison = pd.read_csv(ROOT / "reports/holdout-comparison.csv")
    for model in config()["models"]:
        p = predictions.loc[predictions.model.eq(model)]
        saved = comparison.loc[comparison.model.eq(model) & comparison.horizon.eq(28)].iloc[0]
        actual = metrics(p.actual_units, p.predicted_units, p.mase_scale)
        for key in ["mae", "rmse", "wape", "bias", "mase"]:
            assert saved[key] == pytest.approx(actual[key])


def test_sensitivity_constraints_and_costs():
    require("reports/simulation-summary.csv")
    summary = pd.read_csv(ROOT / "reports/simulation-summary.csv")
    orders = pd.read_csv(ROOT / "reports/simulation-orders.csv")
    assert summary.scenario.nunique() == 3 and len(summary) == 9
    assert summary.constraints_pass.all()
    np.testing.assert_allclose(summary.total_operating_cost, summary.purchase_expenditure + summary.holding_cost + summary.shortage_cost)
    for (_, _, _), group in orders.groupby(["scenario", "strategy", "date"]):
        assert group.purchase_cost.sum() <= group.budget.iloc[0] + 1e-8
        assert group.order_qty.mod(group.pack_size).eq(0).all()
        assert ((group.order_qty == 0) | (group.order_qty >= group.moq)).all()
    for _, group in summary.groupby("scenario"):
        assert group.sales_proxy_units.nunique() == 1
        assert group.initial_inventory_value.nunique() == 1


def test_dashboard_uses_measured_artifacts():
    require("reports/readiness.json")
    d = load_dashboard()
    assert d["selected_holdout"]["model"] == d["protocol"]["selected_model"]
    assert d["quality"]["raw_transactions"] == 541909
    assert len(d["catalog"]) == 25
    assert set(d["future"].product_id) == set(d["catalog"].product_id)
