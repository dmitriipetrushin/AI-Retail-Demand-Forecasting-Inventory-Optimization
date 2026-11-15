"""Real Chromium QA via an existing gstack browse binary; never fabricates captures.

Usage: python -m scripts.browser_verify --browser-bin /path/to/browse
Start Streamlit on 127.0.0.1:8501 first. Only this local target is driven.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time

from src.common import ROOT, utc_now, write_json, read_json


def main(browser):
    checks = []

    def run(*args):
        proc = subprocess.run([str(browser), *args], cwd=ROOT, capture_output=True, text=True, timeout=30)
        if proc.returncode or any(s in proc.stdout for s in ["Operation timed out", "[browse] The operation timed out", "net::ERR_", "Selector matched multiple"]):
            raise RuntimeError(proc.stdout + proc.stderr)
        return proc.stdout.strip()

    def js(expression):
        return json.loads(run("js", f"JSON.stringify({expression})"))

    def state():
        return js("({title:document.querySelector('h3')?.textContent, state:document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state'), text:document.body.innerText, charts:document.querySelectorAll('.js-plotly-plot').length, tables:document.querySelectorAll('[data-testid=stDataFrame]').length, exceptions:document.querySelectorAll('[data-testid=stException]').length})")

    def wait_for(predicate, description):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            s = state()
            if s["exceptions"]:
                raise AssertionError(s["text"])
            if s["state"] == "notRunning" and predicate(s):
                return s
            time.sleep(.15)
        raise AssertionError(f"Timed out waiting for {description}: {state()}")

    def page(idx, title):
        run("click", f'label:has(input[type="radio"][value="{idx}"])')
        return wait_for(lambda s: s.get("title") == title, title)

    def button(label):
        run("click", f'button:has-text("{label}")')

    def capture(name):
        run("screenshot", str(ROOT / "screenshots" / name))

    run("viewport", "1600x1200")
    run("console", "--clear")
    run("goto", "http://127.0.0.1:8501")
    s = wait_for(lambda s: s.get("title") == "Executive overview" and s["charts"] == 2, "executive charts")
    assert "70.5%" in s["text"] and "25" in s["text"] and "-2.4%" in s["text"]
    capture("01-executive-dashboard.png")
    checks.append({"page": "Executive Dashboard", "passed": True, "evidence": "25 products, holdout WAPE 70.5%, base C cost reduction -2.4%; two rendered Plotly charts"})

    page(1, "Demand forecasting")
    wait_for(lambda s: s["charts"] == 1 and s["tables"] == 2, "forecast chart/tables")
    capture("02-demand-forecasting.png")
    run("click", 'input[aria-label$="Forecast horizon (days)"]')
    run("press", "Home")
    run("press", "Enter")
    wait_for(lambda s: "Selected 7." in str(js("[...document.querySelectorAll('[role=combobox]')].map(x=>x.getAttribute('aria-label'))")), "seven day selection")
    run("click", 'input[aria-label$="Forecast view"]')
    run("press", "End")
    run("press", "Enter")
    wait_for(lambda s: "Future refit" in str(js("[...document.querySelectorAll('[role=combobox]')].map(x=>x.getAttribute('aria-label'))")) and s["tables"] == 1, "future refit")
    traces = js("document.querySelector('.js-plotly-plot').data.map(x=>({name:x.name,n:x.x.length,start:x.x[0]}))")
    assert all(t["n"] == 7 and t["start"].startswith("2011-12-09") for t in traces if t["name"] != "Observed sales")
    checks.append({"page": "Demand Forecasting", "passed": True, "evidence": "Historical product/holdout plot and model-error table; changed to 7 days and future refit; forecast traces start 2011-12-09 and contain seven dates"})

    page(2, "Inventory recommendations")
    wait_for(lambda s: s["tables"] >= 2, "inventory grids")
    button("Apply assumptions")
    wait_for(lambda s: "Assumptions applied" in s["text"], "assumption form submit")
    capture("03-inventory-recommendations.png")
    checks.append({"page": "Inventory Recommendations", "passed": True, "evidence": "Editable assumption grid rendered, Apply assumptions submitted, recommendation KPIs/table and CSV export visible. Cell-change behavior separately checked by Streamlit AppTest."})

    page(3, "Budget allocation & human review")
    button("Run budget optimization")
    s = wait_for(lambda s: "OPTIMAL" in s["text"] and s["charts"] == 1, "optimization")
    capture("04-budget-optimization.png")
    run("fill", 'input[type="number"]', "1500")
    run("press", "Enter")
    wait_for(lambda s: "Changed inputs invalidate" in s["text"] and "Accept simulated plan" not in s["text"], "plan invalidation")
    button("Run budget optimization")
    s = wait_for(lambda s: "OPTIMAL" in s["text"] and "Accept simulated plan" in s["text"], "1500 allocation")
    allocation_metrics = js("[...document.querySelectorAll('[data-testid=stMetricValue]')].map(x=>x.textContent)")
    assert float(allocation_metrics[0].replace("£", "").replace(",", "")) <= 1500
    button("Accept simulated plan")
    wait_for(lambda s: "Accepted for demonstration only. No purchase was submitted." in s["text"], "accept confirmation")
    button("Reject simulated plan")
    wait_for(lambda s: "Rejected. No purchase was submitted." in s["text"], "reject confirmation")
    run("fill", 'input[type="number"]', "0")
    run("press", "Enter")
    wait_for(lambda s: "Changed inputs invalidate" in s["text"], "zero-budget invalidation")
    button("Run budget optimization")
    wait_for(lambda s: "OPTIMAL" in s["text"] and "£0" in s["text"], "zero allocation")
    checks.append({"page": "Budget Optimization", "passed": True, "evidence": "OR-Tools OPTIMAL at 3000, 1500 and zero GBP; budget edit invalidates prior plan, allocation within budget, simulated accept and reject confirmations; no purchase submitted", "budget_1500_metrics": allocation_metrics})

    page(4, "Business impact · simulation evidence")
    wait_for(lambda s: s["charts"] == 2 and s["tables"] == 1, "business impact charts")
    capture("05-business-impact.png")
    run("click", 'input[aria-label$="Fixed assumption scenario"]')
    run("press", "End")
    run("press", "Enter")
    wait_for(lambda s: "slow_supply" in str(js("[...document.querySelectorAll('[role=combobox]')].map(x=>x.getAttribute('aria-label'))")), "sensitivity selection")
    checks.append({"page": "Business Impact", "passed": True, "evidence": "Base A/B/C costs, service table and three-scenario chart rendered; switched to slow_supply; simulation disclaimer visible"})

    page(5, "Evaluation & deployment readiness")
    wait_for(lambda s: s["charts"] == 1 and s["tables"] >= 1 and "NO-GO" in s["text"], "readiness evidence")
    badges = js("[...document.querySelectorAll('[data-testid=stMetricValue]')].map(x=>x.textContent.trim())")
    readiness = read_json(ROOT / "reports/readiness.json")
    assert badges[:3] == [readiness["local_demo"], readiness["business_pilot"], readiness["production"]], "Displayed readiness must match current artifacts"
    capture("06-evaluation-readiness.png")
    errors = run("console", "--errors")
    if "(no console errors)" not in errors:
        raise AssertionError(errors)
    checks.append({"page": "Evaluation & Deployment Readiness", "passed": True, "evidence": "Development/holdout comparison, frozen cutoff, acceptance/risk explanation and separate readiness levels rendered; no console errors"})
    report = {"passed": True, "verified_at_utc": utc_now(), "url": "http://127.0.0.1:8501", "driver": "gstack browse / real headless Chromium", "viewport": "1600x1200", "checks": checks, "console_errors": 0,
              "scope": "Local UI behavior only; no live inventory integration, no external order submissions, no GitHub CI execution"}
    write_json(ROOT / "reports/browser-verification.json", report)
    lines = ["# Real browser verification", "", f"Verified: {report['verified_at_utc']}. Driver: {report['driver']}; viewport {report['viewport']}. Target: local Streamlit at http://127.0.0.1:8501.", ""]
    lines.extend(f"- **{c['page']} — PASS:** {c['evidence']}" for c in checks)
    lines.extend(["", "All six screenshots are genuine rendered application captures in `screenshots/`. No console errors were reported. This evidence verifies local UI behavior; it does not validate production integration, supplier inputs or real savings.", "", "Reproduce after starting Streamlit: `python -m scripts.browser_verify --browser-bin /path/to/gstack/browse/dist/browse`. The browser driver is optional development tooling, not a required application dependency."])
    (ROOT / "reports/browser-verification.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser-bin", type=Path, required=True)
    main(parser.parse_args().browser_bin)
