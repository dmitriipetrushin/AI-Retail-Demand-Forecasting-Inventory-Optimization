# Business, functional and nonfunctional requirements

Priority M = mandatory for demonstration; P = prerequisite for a real pilot, outside delivered integration scope.

| ID | Requirement | Priority | Implementation / verification |
|---|---|---|---|
| BR-01 | Support human inventory decisions without executing orders | M | Six-page app; no procurement/network purchase code |
| BR-02 | Quantify forecast and inventory-policy performance separately | M | Comparison CSV, simulation A/B/C |
| BR-03 | Distinguish observed transactions and modeled financial outcomes | M | Dashboard labels, reports, README disclaimer |
| BR-04 | Compare outcomes under constrained budgets and sensitivity | M | Three fixed scenarios, cost and service metrics |
| FR-01 | Download official UCI 352 data with provenance/license/checksum | M | download_data, manifest, source integration test |
| FR-02 | Clean cancellations, returns, missing/invalid fields and duplicates | M | preprocessing, data quality report and tests |
| FR-03 | Select 25 products before all validation windows | M | Frozen catalog, poisoning test |
| FR-04 | Aggregate nonnegative daily sales with explicit zeros | M | Daily key/continuity and aggregation tests |
| FR-05 | Fit seasonal naive, moving average and genuine candidates | M | StatsForecast model tests and real-data run |
| FR-06 | Support 7, 14 and 28-day horizons | M | Forecast API and UI selector |
| FR-07 | Use three rolling origins and untouched final 28 days | M | Split tests, frozen/holdout manifests |
| FR-08 | Report MAE/RMSE/WAPE/bias/defined MASE at product/pooled levels | M | Metric tests, CSV/report outputs |
| FR-09 | Flag short-history/model failures and prohibit negative forecasts | M | Explicit fallback metadata, clamp tests |
| FR-10 | Apply on-hand/on-order, lead/review, safety, packs and MOQ | M | Inventory engine and arithmetic tests |
| FR-11 | Allocate within budget using OR-Tools or labeled fallback | M | MILP, brute force, edge-budget tests |
| FR-12 | Detect mandatory-order infeasibility | M | Required-product zero-budget test |
| FR-13 | Simulate daily receipts, lost sales and all modeled costs | M | Ledger conservation and cost reconciliation |
| FR-14 | Edit assumptions, optimize, accept/reject simulated plans | M | Session state, browser interactions and AppTest |
| FR-15 | Export reviewable CSV recommendations and allocations | M | Streamlit download actions |
| NFR-01 | Local CPU execution; no paid/cloud dependencies | M | Local venv, no external model services |
| NFR-02 | Reproduce with pinned software/configuration and deterministic seed | M | Requirements lock, JSON configs, pipeline commands |
| NFR-03 | Fail visibly when essential data/artifacts are absent or modified | M | Input guards and checksum verification |
| NFR-04 | Omit customer identifiers from demo exports | M | Prepared schema and tests |
| NFR-05 | Preserve initial holdout and distinguish later experiments | M | Immutable manifest guard |
| NFR-06 | Provide professional evidence and honest limitations | M | PM set, case study, screenshots, README |
| PIL-01 | Validate real stock, supplier costs and availability | P | Pilot data contract and Finance/Operations signoff |
| PIL-02 | Establish monitoring, incident response and ownership | P | Change plan; production remains NO-GO |

Traceability: pytest modules map to data, forecasting, inventory, integration and dashboard. [07_test_strategy.md](07_test_strategy.md) defines verification layers. [06_acceptance_criteria.md](06_acceptance_criteria.md) contains fixed pass/fail gates. Functional acceptance does not imply the forecast quality or business value hypothesis must succeed.
