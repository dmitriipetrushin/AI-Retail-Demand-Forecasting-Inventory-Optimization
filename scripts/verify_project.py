"""Read-only final evidence audit (writes its own audit result only)."""
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import pandas as pd

from src.common import ROOT, read_json, sha256, utc_now, write_json
from src.dashboard_data import load_dashboard
from src.evaluation import verify_freeze, evaluate_holdout


def main():
    required = [
        "README.md", "LICENSE", "requirements.txt", "requirements-lock.txt", "pyproject.toml", "app.py",
        "data/source-manifest.json", "data/README.md", "portfolio/case-study.md", "portfolio/demo-guide.md",
        "reports/data-quality-report.md", "reports/data-quality-summary.json", "reports/forecast-evaluation.md",
        "reports/model-comparison.csv", "reports/forecast-failure-analysis.md", "reports/business-impact-analysis.md",
        "reports/optimization-methodology.md", "reports/browser-verification.json", "reports/test-results.xml",
        "reports/reproduction-verification.json", "CLAUDE.md", ".github/workflows/ci.yml",
    ]
    pm = sorted((ROOT / "project-management").glob("*"))
    assert len(pm) == 12, "Expected all twelve project-management deliverables"
    assert all((ROOT / p).is_file() for p in required)
    risks = pd.read_csv(ROOT / "project-management/05_risk_register.csv")
    assert len(risks) >= 15 and not risks.isna().any().any()
    for name in ["daily_sales.csv", "products.csv"]:
        frame = pd.read_csv(ROOT / "data/processed" / name)
        assert not any("customer" in c.lower() or "invoice" in c.lower() for c in frame.columns)
    daily = pd.read_csv(ROOT / "data/processed/daily_sales.csv", dtype={"product_id": str}, parse_dates=["date"])
    assert daily.product_id.nunique() == 25
    for _, group in daily.groupby("product_id"):
        assert group.date.nunique() == (group.date.max() - group.date.min()).days + 1
    verify_freeze()
    evaluate_holdout()
    load_dashboard()
    for path, digest in read_json(ROOT / "reports/simulation-manifest.json")["sha256"].items():
        assert sha256(ROOT / path) == digest, f"Simulation artifact changed: {path}"
    assert read_json(ROOT / "reports/browser-verification.json")["passed"]
    assert read_json(ROOT / "reports/reproduction-verification.json")["passed"]
    suite = ET.parse(ROOT / "reports/test-results.xml").getroot().find("testsuite")
    assert all(int(suite.attrib[k]) == 0 for k in ["failures", "errors", "skipped"])
    screenshots = sorted((ROOT / "screenshots").glob("*.png"))
    assert len(screenshots) == 6 and all(p.read_bytes().startswith(b"\x89PNG") for p in screenshots)
    broken = []
    for document in [ROOT / "README.md", *(ROOT / "portfolio").glob("*.md"), *(ROOT / "project-management").glob("*.md"), *(ROOT / "reports").glob("*.md")]:
        for link in re.findall(r'\]\(([^)]+)\)', document.read_text()):
            if "://" in link or link.startswith("#"):
                continue
            if not (document.parent / link.split("#")[0]).exists():
                broken.append({"document": str(document.relative_to(ROOT)), "link": link})
    assert not broken, broken
    proc = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout
    ignored = subprocess.run(["git", "check-ignore", "data/raw/Online Retail.xlsx", "data/raw/online-retail.zip", ".venv/bin/python"], cwd=ROOT, capture_output=True, text=True)
    assert ignored.returncode == 0 and len(ignored.stdout.splitlines()) == 3
    report = {"passed": True, "verified_at_utc": utc_now(), "pm_documents": len(pm), "risk_count": len(risks),
              "tests": int(suite.attrib["tests"]), "test_failures": 0, "test_skips": 0,
              "screenshots": len(screenshots), "broken_document_links": broken,
              "customer_or_invoice_ids_in_derivatives": False, "daily_continuity_pass": True,
              "frozen_and_holdout_integrity_pass": True, "simulation_integrity_pass": True,
              "dependencies_compatible": True, "raw_and_venv_ignored": True,
              "remote_ci_verified": False, "production_integration_verified": False}
    write_json(ROOT / "reports/final-verification.json", report)
    print(report)


if __name__ == "__main__":
    main()
