# Real browser verification

Verified: 2026-11-15T15:55:47.962065+00:00. Driver: gstack browse / real headless Chromium; viewport 1600x1200. Target: local Streamlit at http://127.0.0.1:8501.

- **Executive Dashboard — PASS:** 25 products, holdout WAPE 70.5%, base C cost reduction -2.4%; two rendered Plotly charts
- **Demand Forecasting — PASS:** Historical product/holdout plot and model-error table; changed to 7 days and future refit; forecast traces start 2011-12-09 and contain seven dates
- **Inventory Recommendations — PASS:** Editable assumption grid rendered, Apply assumptions submitted, recommendation KPIs/table and CSV export visible. Cell-change behavior separately checked by Streamlit AppTest.
- **Budget Optimization — PASS:** OR-Tools OPTIMAL at 3000, 1500 and zero GBP; budget edit invalidates prior plan, allocation within budget, simulated accept and reject confirmations; no purchase submitted
- **Business Impact — PASS:** Base A/B/C costs, service table and three-scenario chart rendered; switched to slow_supply; simulation disclaimer visible
- **Evaluation & Deployment Readiness — PASS:** Development/holdout comparison, frozen cutoff, acceptance/risk explanation and separate readiness levels rendered; no console errors

All six screenshots are genuine rendered application captures in `screenshots/`. No console errors were reported. This evidence verifies local UI behavior; it does not validate production integration, supplier inputs or real savings.

Reproduce after starting Streamlit: `python -m scripts.browser_verify --browser-bin /path/to/gstack/browse/dist/browse`. The browser driver is optional development tooling, not a required application dependency.
