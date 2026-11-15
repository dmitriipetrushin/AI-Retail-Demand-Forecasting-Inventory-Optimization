# Test strategy

Testing distinguishes correct implementation from useful prediction and from production readiness. Numerical success cannot substitute for reliable constraints or honest accounting.

Unit tests cover schema and missing file handling, missing descriptions/IDs, cancellation/negative quantity removal, exact duplicates, invalid prices/codes/dates/nonfinite quantities, zero-day aggregation, training-only selection, chronological cutoffs, seasonal alignment, genuine AutoETS/Croston inference, supported horizons, short/absent history, negative-output clamping and hand-calculated forecast metrics. Undefined WAPE, bias and MASE remain undefined.

Inventory tests use arithmetic examples for target/position, MOQ and pack rounding, protection-period completeness, zero/tiny/large budgets, nonnegative allocations, deterministic fallback, mandatory-order infeasibility and an exhaustive two-product optimization comparison. Simulation tests verify receipt timing, lost sales, daily inventory conservation, cost sums, identical realized history across strategies and that a changed future cannot affect the first order.

Integration tests load the actual 541,909-row workbook (when the documented download has been run), execute real models against prepared products, recompute saved holdout metrics, verify frozen artifact hashes, verify all nine sensitivity runs, inspect every review budget/pack/MOQ and check dashboard data against the same artifacts. These are not solely mocked model outputs. Synthetic fixtures isolate edge cases; they never supply reported real-data performance.

Chronological evidence: expanding development origins followed by one final 28-day holdout. The development catalog cannot access later data. The selected model and metrics are frozen before the holdout. Repeated holdout commands verify preserved results, rather than overwriting them. Future refit inference is a separate output with no available actuals.

UI verification uses Streamlit AppTest for all pages and budget/human-review interactions, plus real headless Chromium for rendered navigation, chart/table visibility, budget changes, plan acceptance/rejection, editable assumptions, console errors and screenshots. Browser artifacts document checks actually performed; a missing browser is reported rather than simulated.

Run `python -m pytest --junitxml=reports/test-results.xml`. Download and prepare data first to avoid optional real-data skips. The CI workflow installs pinned dependencies, downloads the official dataset and reruns the same complete pipeline, using preserved protocol/holdout evidence if inputs match. A code/config change that violates frozen hashes must use a new experiment directory and preserve the initial evidence; do not bypass integrity checks.

Severity: a leak, wrong cost formula, illegal order or invented measured result is critical; a blocked page or silently missing artifact is high; minor visual defects are lower. Critical/high defects block technical acceptance until reproduced, fixed at root cause and reverified. Current actual counts are in JUnit XML and the final verification report; this plan does not invent a test outcome.
