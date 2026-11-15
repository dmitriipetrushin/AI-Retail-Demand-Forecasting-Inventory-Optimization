# Predeclared acceptance criteria

These thresholds mirror `config/project.json`, frozen before final holdout evaluation. This document explains verification; it does not redefine targets after seeing results.

| Gate | Fixed criterion | Evidence | Failure consequence |
|---|---|---|---|
| AC-01 Data | Official real dataset loads; provenance recorded; essential schema/daily checks pass | Source manifest, quality report, real-data integration test | NO-GO if missing/invalid |
| AC-02 Privacy | No customer IDs in processed/demo tables | Column assertions, artifact audit | Block export/demo until fixed |
| AC-03 Chronology | 25 products selected before earliest validation; three disjoint 28-day windows; final 28 days excluded from selection | Cutoffs, poisoning tests, frozen hashes | NO-GO, rebuild separate experiment |
| AC-04 Forecast quality | Selected model's pooled development WAPE ≥5% relatively below seasonal naive | Frozen decision and development comparison | Hypothesis fails; baseline retained, no model benefit claim |
| AC-05 Evaluation integrity | Preserve initial holdout; fixed metrics/config; no random split | Holdout manifest, idempotence test | NO-GO for performance claims |
| AC-06 Model reliability | Zero fallback rows in measured development/holdout experiment | Effective-model/fallback fields | Investigate candidate availability and lower readiness |
| AC-07 Inventory | 100% budget, nonnegative integer quantity, pack, MOQ, cap and stock-conservation compliance in tested scenarios | Runtime guards, tests, orders/ledger | NO-GO until repaired |
| AC-08 Financial model | Nine reproducible A/B/C × three-scenario comparisons; identical inputs per scenario; costs reconcile | Simulation manifest, integration assertions | No financial conclusion |
| AC-09 Operational safety | No orders/financial transactions sent | Architecture/source review and local browser checks | Immediate NO-GO |
| AC-10 QA | No unresolved critical test failures; all full-run tests pass without skips in completed local build | JUnit XML, test output, browser evidence | Demo conditional or blocked |
| AC-11 Evidence | All 12 PM docs, README, case study, demo guide and feasible genuine screenshots | Documentation audit | Incomplete portfolio |

The forecast target is a research hypothesis, not a guaranteed deliverable. Holdout performance is reported honestly but is not used for reselection or threshold revision. A strong relative reduction can still leave high absolute error. The initial stock/cost data limitations prevent production procurement even if every portfolio gate passes.

Local demonstration requires technical evidence. A controlled analytical pilot additionally requires real input validation, an operating owner and shadow-mode approval. Production requires operational integration, security, monitoring, calibrated uncertainty and broader validation. Current decisions are populated from actual outputs in `10_go_no_go_decision.md` and `reports/readiness.json`.
