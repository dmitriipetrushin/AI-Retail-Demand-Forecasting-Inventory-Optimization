# Final verification

Completed locally on 2026-11-15 for Dmitry Petrushin. See the JSON evidence alongside this document for machine-readable outcomes. No repository was published or pushed.

| Area | Actual evidence |
|---|---|
| Official dataset | UCI 352 workbook loaded: 541,909 source records; archive/workbook checksums recorded |
| Preparation | 520,893 retained positive-sales records; 25 training-selected products; 9,323 daily rows; no customer/invoice IDs exported |
| Chronology | Catalog cutoff 2011-08-18; three rolling 28-day development windows; untouched final holdout 2011-11-11–2011-12-08 |
| Model fitting | Seasonal naive, moving average, AutoETS and Croston SBA actually ran; zero fallback rows in development/holdout |
| Forecast hypothesis | AutoETS development WAPE 79.1512% versus seasonal naive 95.2979%; 16.9434% relative reduction; fixed 5% gate passed |
| Final holdout | AutoETS MAE 50.0104, RMSE 156.5523, WAPE 70.5423%, bias -20.8508%, MASE 0.9220 |
| Inventory / optimization | OR-Tools SCIP actually used; budget, integer packs, MOQ, caps and stock conservation validated across nine strategy/scenario runs |
| Business result | Base costs A £75,697.39, B £76,682.09, C £77,481.13; B/C worse than A. No real savings or ROI claimed |
| Sensitivity | C modeled cost 3.3543% below A in tight budget, 3.9786% below A with slower supply; all assumptions fixed before holdout |
| Automated QA | 55 passed, 0 failed, 0 skipped in 24.91 seconds; 17 upstream OR-Tools/matplotlib/pyparsing deprecation warnings |
| Browser | Real headless Chromium, 1600×1200; all six pages, forecast controls, assumption form, optimization budgets and simulated accept/reject; fresh-run console errors: 0 |
| Clean reproduction | Separate temporary source/config study refitted all models and reran simulation; prepared hashes identical; all three comparison tables' maximum numerical difference: 0.0 |
| Documentation | Twelve PM documents, 21 risks, README, case study, demo guide, six genuine screenshots; no broken checked document links |
| Dependency/source audit | Pinned tested lock; pip check passed; Python compiled; no detected secret patterns in source/config; raw files and venv ignored; no review artifact larger than 5 MB |
| Remote/production scope | GitHub Actions supplied but not executed remotely; no real stock/supplier data, production monitoring or purchasing integration verified |

The clean reproduction took 43.303 seconds in the same local Python environment while other checks ran. This is an execution observation, not a benchmark on the target user's CPU or an independent platform validation. The raw-file acquisition step reused checksum-verified official bytes; the initial official network download was separately completed and recorded in `data/source-manifest.json`.

Root causes corrected during verification: NumPy generic equality on pandas Series in two test assertions; report output-directory creation in a clean isolated copy; stale simulated approval state after a budget change; and an incorrect infeasibility label for a heuristic's failure to satisfy mandatory products. No forecasting rules, thresholds or initial holdout results were changed to achieve a pass. The improved approval and fallback behavior has dedicated regression coverage.

Deployment decision: **GO** for the local portfolio demonstration; **CONDITIONAL GO** for considering a governed analytical shadow pilot with real operational inputs; **NO-GO** for production inventory purchasing. Base-scenario financial/service results do not support replacing the traditional policy.

Git was initialized on `main`; no author name/email was configured during verification. The project files are staged for review. A commit requires a real author identity; no identity was invented. No remote is configured and nothing was pushed. Check `git status` for the current state if an author is supplied later.

Evidence: `test-results.xml`, `browser-verification.json`, `reproduction-verification.json`, `final-verification.json`, `frozen-protocol.json`, `holdout-manifest.json`, `simulation-manifest.json`.
