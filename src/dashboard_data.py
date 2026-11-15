"""Single artifact-loading boundary for dashboard and consistency tests."""
import pandas as pd

from src.common import ROOT, read_json
from src.evaluation import load_prepared, verify_freeze, evaluate_holdout


def load_dashboard():
    frozen = verify_freeze()
    manifest_path = ROOT / "reports/holdout-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("Run run_evaluation explicitly before opening the dashboard")
    from src.common import sha256
    manifest = read_json(manifest_path)
    if manifest["protocol_sha256"] != sha256(ROOT / "reports/frozen-protocol.json"):
        raise ValueError("Initial holdout protocol manifest mismatch")
    evaluate_holdout()  # Verifies existing immutable holdout; does not rerun it.
    daily, catalog, quality = load_prepared()
    result = {"daily": daily, "catalog": catalog, "quality": quality, "protocol": frozen}
    for key, path in {"comparison": "model-comparison.csv", "holdout": "holdout-predictions.csv",
                      "future": "future-forecasts.csv", "simulation": "simulation-summary.csv",
                      "folds": "development-fold-metrics.csv"}.items():
        result[key] = pd.read_csv(ROOT / "reports" / path, dtype={"product_id": str})
    result["decisions"] = read_json(ROOT / "reports/readiness.json")
    selected = result["comparison"].loc[
        result["comparison"].phase.eq("holdout") & result["comparison"].horizon.eq(28) & result["comparison"].model.eq(frozen["selected_model"])]
    if len(selected) != 1 or set(result["future"].product_id) != set(catalog.product_id):
        raise ValueError("Dashboard artifact consistency failed")
    result["selected_holdout"] = selected.iloc[0].to_dict()
    return result
