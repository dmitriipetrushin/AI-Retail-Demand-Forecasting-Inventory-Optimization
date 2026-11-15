# Project charter

**Project:** AI Retail Demand Forecasting & Inventory Decision Support
**Owner:** Dmitry Petrushin
**Role:** Independent Project Owner — AI Implementation & Project Management
**Status:** Self-directed portfolio implementation. The company and stakeholder roles are fictional.

The business problem is uncertain replenishment based on historical averages and manual judgment. Overstock, shortages and constrained purchasing budgets create competing objectives. This study asks whether a reproducible sales forecast and transparent allocation policy justify further analytical validation.

Objectives are to process real historical retail transactions, compare lightweight forecasting methods fairly, recommend explainable simulated purchases, enforce budgets and pack rules, quantify scenario sensitivity, and make an evidence-based deployment decision. Expected value is better decision visibility and a testable pilot hypothesis; no real savings are promised.

In scope: 25 training-selected products, daily positive recorded sales, 7/14/28-day point forecasts, three rolling development windows, one preserved final holdout, three inventory strategies, three financial scenarios, local six-page dashboard, tests, provenance, PM records and recruiter materials. Out of scope: live ordering, real stock reconstruction, supplier integration, production service, cloud accounts and paid APIs.

Constraints: CPU-only Linux, roughly 15 GB RAM, Python 3.11+, open-source software and local execution. The source contains only about a year of history and lacks stock availability and supplier costs. Closed days, true zero demand and unavailable stock cannot be separated. Data exports must omit customer IDs.

Fictional stakeholders: Sponsor owns investment decisions; Operations owns process; Inventory Manager reviews plans; Data Analyst owns data interpretation; ML Engineer owns modeling; Finance validates costs; QA validates gates. They did not participate in this independent project.

Success criteria are fixed in [06_acceptance_criteria.md](06_acceptance_criteria.md). The forecast hypothesis is ≥5% relative development WAPE improvement over weekly seasonal naive. Missing the hypothesis must be reported. Local demonstration, controlled analytical pilot and production readiness are assessed separately. The final business recommendation is populated from measured evidence in [10_go_no_go_decision.md](10_go_no_go_decision.md).

Key assumptions: sales are a censored proxy for demand; no initial open orders; supplier costs equal an explicitly assumed fraction of training median retail price; all simulated strategies share the same initial state, budgets, costs and exogenous sales history. Real operational approval would require replacing these assumptions with validated inputs.
