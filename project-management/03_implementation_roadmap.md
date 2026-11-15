# Hypothetical six-week implementation roadmap

This is a proposed company adoption schedule, **not actual development history**. This portfolio was implemented independently in a local coding session; machine timestamps in manifests and test/browser evidence record actual execution.

| Week | Work | Proposed accountable role | Exit evidence / dependency |
|---|---|---|---|
| 1 — Discovery | Map decisions, costs, data availability, budget authority and baseline; agree sales-vs-demand caveat | Sponsor / Operations | Charter, data contract, fixed quality gates; identify a real inventory owner |
| 2 — Data preparation | Acquire and validate transactions; remove returns; define calendar, training catalog and holdout | Data Analyst | Quality report, privacy review, leakage tests; operational stock data requested |
| 3 — Model development | Build naive baselines and CPU statistical candidates; rolling backtests; freeze protocol | ML Engineer | Development comparison and signed frozen protocol before opening holdout |
| 4 — Decision support | Build inventory policies, pack/MOQ budget solver, editable dashboard and human review | Inventory Manager | Explainable recommendations; budget tests; operational workflow walkthrough |
| 5 — Validation | Run untouched holdout, cost scenarios, independent QA and shadow process rehearsals | QA / Finance | Preserved results, constraint audit, browser evidence, scenario review |
| 6 — Pilot assessment | Train users, agree monitoring/rollback and assess go/no-go | Sponsor / Operations | Separate demo/pilot/production decisions, unresolved-risk owners, pilot authorization |

Critical dependencies: usable stock/availability history before any service-level claim; verified supplier price and lead-time contracts before real purchasing advice; frozen evaluation before final holdout; operational owner and incident plan before live integration. If the model misses its gate, retain the baseline and investigate in a separately labeled experiment.

Suggested pilot checkpoints: weekly quality/service review, fortnightly Finance cost reconciliation, explicit review after promotion periods, and a formal end-of-pilot decision. These are proposed ceremonies, not meetings that occurred.
