"""Render recruiter-facing summaries from the measured, preserved experiment."""
from src.common import ROOT, read_json
from src.reporting import measured_context, save


def write_portfolio():
    f, primary, dev, hold, naive, sim, base, q = measured_context()
    readiness = read_json(ROOT / "reports/readiness.json")
    test_counts = readiness.get("test_evidence") or {}
    test_evidence = f"Measured local run: **{test_counts.get('tests', 'pending')} tests, {test_counts.get('failures', 'pending')} failures, {test_counts.get('skipped', 'pending')} skips**. See the XML for duration and dependency deprecation warnings."
    comparison = primary[['phase','model','mae','rmse','wape','bias','mase']].to_markdown(index=False, floatfmt='.4f')
    arch = """```mermaid
flowchart LR
    A[Official UCI workbook + license/checksum] --> B[Validation + positive-sales cleaning]
    B --> C[Training-only catalog + zero-padded daily sales]
    C --> D[3 rolling origins + baseline/candidate models]
    D --> E[Frozen global model and configuration]
    E --> F[Preserved final 28-day holdout]
    E --> G[Post-history forecast refit]
    G --> H[Assumed stock, costs and supplier rules]
    H --> I[Replenishment + OR-Tools allocation]
    C --> J[Daily A/B/C strategy simulation]
    E --> J
    F --> K[Local Streamlit decision dashboard]
    I --> K
    J --> K
    K --> L[Human simulated accept / reject]
```"""
    save("README.md", f"""# AI Retail Demand Forecasting & Inventory Decision Support

**Retail Intelligence — AI Demand & Inventory Control Tower**

**Dmitry Petrushin · Independent AI Implementation Portfolio Project**

> This is a self-directed AI implementation portfolio project. The transaction dataset contains historical retail records, while inventory policies, supplier constraints, stakeholder roles, and business scenarios are simulated. The application is not a production inventory management system.

## Executive summary

A working CPU-only forecasting and inventory decision-support application with a measured, deliberately cautious business case. It processes **{q['raw_transactions']:,} real UCI records**, retains **{q['valid_transactions']:,} positive-sales transactions**, selects **25 products using training data only**, compares four forecasting methods and uses OR-Tools to allocate an assumed purchasing budget. Six dashboard pages expose forecasts, configurable inventory assumptions, optimization, simulation and readiness evidence.

**Measured outcome:** AutoETS reduced development WAPE by **{f['development_wape_improvement']:.2%}** relative to seasonal naive. Final holdout WAPE was **{hold.wape:.2%}** (seasonal naive: {naive.wape:.2%}). Yet in the base simulation Strategy B cost **{abs(base.loc['B','cost_reduction_vs_A']):.2%} higher** and optimized C **{abs(base.loc['C','cost_reduction_vs_A']):.2%} higher** than A. Better forecasting did not establish better purchasing outcomes. The baseline should be retained pending operational validation.

## Business problem

A fictional retailer must balance unavailable stock, slow-moving inventory and a limited budget. Historical averages and manual judgment provide little visibility into forecast error or purchasing tradeoffs. The project turns that problem into explicit requirements, testable hypotheses and separate decisions for a demonstration, analytical pilot and production system. No fictional stakeholder is described as an actual collaborator.

## Solution overview

- Official source acquisition with license/provenance/checksums and a reproducible quality report.
- Weekly seasonal naive, 28-day moving average, StatsForecast AutoETS and Croston SBA; 7/14/28-day forecasts.
- Three rolling development windows, training-only catalog/price metadata, frozen selection and preserved holdout.
- Explainable order-up-to policy, integer-pack OR-Tools allocation and labeled deterministic fallback.
- Daily lost-sales simulation with A/B/C comparators and three assumption scenarios.
- Local human review with editable assumptions, budget changes, accept/reject and CSV exports; no real orders.

## Architecture

{arch}

Modules live in `src/`, reproducible entry points in `scripts/`, fixed configuration in `config/`, small evidence in `reports/`, and business/PM materials in `project-management/` and `portfolio/`. No remote inference, paid API, database or Docker is required.

## Screenshots

Genuine local Chromium captures; see [capture details](screenshots/README.md).

![Executive dashboard](screenshots/01-executive-dashboard.png)

| Forecasting | Budget optimization |
|---|---|
| ![Demand forecast](screenshots/02-demand-forecasting.png) | ![Budget allocation](screenshots/04-budget-optimization.png) |

Additional captures: [inventory](screenshots/03-inventory-recommendations.png), [business impact](screenshots/05-business-impact.png), [evaluation/readiness](screenshots/06-evaluation-readiness.png).

## Technology stack

Python 3.11+ (verified on {f['python']}), pandas/NumPy, StatsForecast, OR-Tools SCIP, Streamlit, Plotly, matplotlib and pytest. Statistical models are sufficient for this small predictive-analytics study; no LLM or GPU is used. Direct dependencies are pinned in `requirements.txt`; the exact tested environment is pinned in `requirements-lock.txt` and recorded in the protocol. AutoARIMA was omitted to keep CPU work bounded.

## Dataset source and attribution

[UCI Online Retail, dataset 352](https://archive.ics.uci.edu/dataset/352/online+retail). Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. [DOI: 10.24432/C5BW33](https://doi.org/10.24432/C5BW33). Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Real source history: 2010-12-01 through 2011-12-09 12:50. Prepared study ends **{q['date_end']}**, excluding the final partial calendar day. Cancellation/negative sales, invalid prices/codes/dates and exact duplicates are excluded; returns never become positive demand. All countries are retained. Daily series preserve zero recorded sales from first training-observed sale onward. Customer and invoice IDs are omitted from exports. Modified derivatives retain CC BY attribution; project code/original docs are MIT.

[Data documentation](data/README.md) · [Source manifest/checksums](data/source-manifest.json) · [Measured quality report](reports/data-quality-report.md). Raw workbook/archive are ignored by Git. The prepared derivative contains {q['daily_rows']:,} rows, and {q['zero_sales_fraction']:.1%} have zero recorded sales. Sales are not unconstrained demand: stockout availability is unknown.

## Forecasting methodology

Selection cutoff **{f['selection_cutoff']}** precedes every validation window. Require 90 active days and 180 calendar days of history; rank by active days, unit volume, then code; retain 25. Product names and median retail-price proxies are also training-only. No weak products are excluded after evaluation.

Development origins are 2011-08-18, 2011-09-15 and 2011-10-13; each predicts 28 days. Select one global model by pooled development WAPE, ties by configured model order. Freeze processing/model/evaluation/configuration/data hashes before the final holdout **{f['holdout_start']}–{f['holdout_end']}**. Leading 7/14-day results are also exported. The ≥5% development improvement gate is predeclared and was not changed after seeing the holdout.

MAE and RMSE use product-day errors; WAPE is total absolute error / total actual units; bias is signed total error / total actual units. MASE uses each training prefix's seven-day seasonal absolute-difference scale, averaging defined scaled errors. Zero denominators remain undefined/blank, with coverage counts. These pooled metrics do not cancel errors across products. Fallbacks and effective models are explicit; measured development/holdout fallback rows: {int(primary.fallback_rows.sum())}.

## Model comparison and evaluation results

Primary 28-day horizon; WAPE/bias values in the table are fractions, not percentages.

{comparison}

Selected final holdout MAE **{hold.mae:.3f}**, RMSE **{hold.rmse:.3f}**, WAPE **{hold.wape:.2%}**, bias **{hold.bias:.2%}**, MASE **{hold.mase:.3f}**. All models actually ran. No holdout tuning was performed. A later full-history refit produces forecasts for 2011-12-09–2012-01-05 for the historical demonstration, not today's market. Its future actuals are unavailable.

![Model comparison](reports/figures/model-comparison.png)

[Full evaluation](reports/forecast-evaluation.md) · [Product failures](reports/forecast-failure-analysis.md) · [Machine-readable comparison](reports/model-comparison.csv) · [Frozen protocol](reports/frozen-protocol.json) · [Initial holdout manifest](reports/holdout-manifest.json).

## Inventory optimization

Target = forecast units over lead + review days + safety stock. Inventory position = on hand + on order. Positive purchase need is rounded up to a pack multiple and MOQ. The optional integer-pack MILP minimizes purchase plus target-shortage/excess cost while enforcing a hard budget in pennies. It reports optimal/feasible/infeasible status; allocation is independently validated. Zero orders are feasible under a zero budget. Required-product tests demonstrate actual infeasibility; inability to fund every target is otherwise a soft shortfall.

A uses an expanding historical average + product-code FIFO budget allocation; B uses the selected forecast + the same FIFO; C uses the selected forecast + optimization. [Mathematical formulation and constraints](reports/optimization-methodology.md). If OR-Tools is unavailable, the app labels a FIFO fallback and makes no optimality claim. OR-Tools SCIP was used for the recorded results.

## Business impact simulation

All policies see identical realized sales-proxy histories and costs under each scenario, with no future sales exposed at ordering time. Base assumptions: 7-day lead, 7-day review, initial 7-day stock cover, z=1.28 safety buffer, six-unit packs, MOQ 12, **£3,000 per review**. Purchase unit cost is **assumed 50% of training median retail price**, rounded to pennies; annual holding 25%; shortage penalty twice assumed purchase cost. Tight budget uses £1,500; slow supply uses a 14-day lead and higher buffer/penalties. See [exact JSON](config/scenarios.json).

Base modeled operating costs: A **£{base.loc['A','total_operating_cost']:,.2f}**, B **£{base.loc['B','total_operating_cost']:,.2f}**, C **£{base.loc['C','total_operating_cost']:,.2f}**. Base modeled fill rates are {base.loc['A','fill_rate']:.1%}, {base.loc['B','fill_rate']:.1%}, {base.loc['C','fill_rate']:.1%}; these stressed budgets do not produce acceptable service. C's modeled cost reductions versus A in tight-budget/slow-supply scenarios are **{sim.loc[sim.scenario.eq('tight_budget') & sim.strategy.eq('C'),'cost_reduction_vs_A'].iloc[0]:.2%} / {sim.loc[sim.scenario.eq('slow_supply') & sim.strategy.eq('C'),'cost_reduction_vs_A'].iloc[0]:.2%}**. These are not verified savings or ROI.

Total modeled operating cost = purchases + daily closing-stock holding + unfilled-sales penalties. Average inventory, unmet units, period turnover, fill rate, terminal stock and in-transit assets are also reported. Asset-adjusted cost includes initial inventory value and credits closing/in-transit assets, exposing short-horizon accounting sensitivity. The single-review optimizer does not guarantee the best realized multi-period outcome.

[Business analysis](reports/business-impact-analysis.md) · [Summary CSV](reports/simulation-summary.csv) · [Assumption/cost caveats](project-management/09_business_case_and_roi.md).

## Project management

The [12-document PM set](project-management/) includes a charter, traceable requirements, explicitly hypothetical six-week roadmap, fictional stakeholder communication/RACI, 21-risk register, fixed acceptance gates, test strategy, measured model report, financial case, readiness decision, adoption/rollback plan and genuine lessons. [Recruiter case study](portfolio/case-study.md) · [Two-minute demo](portfolio/demo-guide.md).

## Installation

```bash
cd /path/to/PortfolioProject3
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip check
```

Python 3.11/3.12 is recommended; this run used Python 3.12.3 on Linux. Internet is needed only for installing packages and the official data download. Inference, optimization and the dashboard run locally. No secrets or cloud setup are needed. Direct pinned dependencies can instead be installed with `-r requirements.txt`; the lock is preferred for exact reproduction.

## Running the application

The checked-in small processed data/reports support immediate dashboard review after installation:

```bash
streamlit run app.py
```

Open **http://127.0.0.1:8501**. Use the sidebar for all six pages. Edit stock/lead/safety assumptions under Inventory Recommendations; Budget Optimization uses those session inputs. Changing inputs invalidates an earlier approval. Accept/reject is session-only and submits nothing. The fixed Business Impact experiments do not change when editing a live proposal.

## Reproducing experiments

```bash
python -m scripts.download_data
python -m scripts.prepare_data
python -m scripts.train_models
python -m scripts.run_evaluation
python -m scripts.run_simulation
python -m scripts.generate_reports
python -m scripts.write_portfolio
```

Or run `bash scripts/reproduce.sh` after activation. Seed: 42; statistical inference and the one-thread solver are deterministic in the tested environment. Source/version/checksum metadata are retained. Existing initial development/holdout artifacts are verified rather than overwritten. This intentionally prevents accidental tuning against a known holdout. To rerun model fitting independently from scratch, copy the **tracked source/config and the same downloaded raw workbook** into a separate experiment directory, omit generated `reports/` files there (keep the empty `reports/figures/` directory), and run preparation/training/evaluation in that separate directory. Compare its numerical outputs to the preserved initial results. Never delete/replace initial holdout evidence in the main project to bypass a changed protocol.

An automated clean refit in an isolated temporary directory is also available: `python -m scripts.verify_reproduction`. The completed run reproduced prepared-data checksums and development/holdout/simulation metrics exactly (maximum numeric difference 0) in the same Python environment. [Clean reproduction evidence](reports/reproduction-verification.json). Run `python -m scripts.verify_project` to audit document links, privacy, manifests and required deliverables.

If the official source is temporarily unavailable, the checked-in real-data derivatives still support artifact review and the dashboard. A fresh raw-data reproduction remains incomplete until the official file is available. No synthetic data was substituted for the measured study.

## Testing

```bash
python -m pytest --junitxml=reports/test-results.xml
```

The completed local run includes real workbook/model integration, leakage tests, exact metrics, inventory arithmetic, budget/pack/MOQ/infeasibility, brute-force solver comparison, cost/conservation and sensitivity checks, dashboard consistency and Streamlit AppTest. Real-data integration tests skip explicitly if the raw workbook is absent, so download it for a full zero-skip run. [Actual test XML](reports/test-results.xml) · [Browser evidence](reports/browser-verification.md). CI installs pinned dependencies and downloads the same official source; this workflow is provided but has not been run on GitHub because nothing was published.

{test_evidence}

## Deployment recommendation

Local portfolio demonstration: **{readiness['local_demo']}**. Controlled analytical business pilot: **{readiness['business_pilot']}**, contingent on real stock/cost/supplier data, human ownership and shadow-mode validation. Production inventory deployment: **NO-GO**. Retain the traditional policy until actual operational benefit is established. [Evidence-based decision](project-management/10_go_no_go_decision.md).

## Limitations

One year of historical wholesale-influenced sales is not current demand. Zero sales are ambiguous; availability and lost demand are unknown. Prices are nominal GBP and costs are assumed. AutoETS has high absolute errors and no calibrated uncertainty intervals. The 28-day simulation has stressed budgets and terminal-value effects; it does not validate ROI or service levels. There is no live integration, authentication, durable approval trail, production monitoring or supplier execution. Live edits illustrate scenarios and do not update the original study. Screenshots and tests establish local behavior, not production readiness.

## Future development

Collect real stock/availability, purchasing price and supplier arrival histories; validate multiple annual cycles; add calendar/holiday features and calibrated intervals in separately labeled experiments; evaluate service and working-capital tradeoffs with multi-period stochastic policies; add durable authorization/audit and operational monitoring only after a real pilot decision. Preserve the original holdout as evidence.
""")
    save("portfolio/case-study.md", f"""# AI Retail Demand Forecasting & Inventory Decision Support

**Dmitry Petrushin**

**Independent Project Owner — AI Implementation & Project Management**

## 1. Executive summary

I built and validated a local decision-support application that connects real historical retail transactions to sales forecasts, explainable inventory recommendations and budget allocation. I treated forecast quality and modeled business value as separate hypotheses. AutoETS reduced development WAPE by {f['development_wape_improvement']:.2%} relative to seasonal naive, but base-scenario optimized purchasing cost {abs(base.loc['C','cost_reduction_vs_A']):.2%} more than the traditional comparator. That evidence supports a local demonstration and further conditional analytical validation, not production procurement.

This is a self-directed portfolio project. All company roles and operating scenarios are fictional. I did not claim interviews, team participation, realized savings or a live rollout.

## 2. Business problem

A fictional retailer needs to balance stock availability, overstock and limited purchasing funds. A historical average is easy to use but gives little evidence about forecast quality or how to allocate money among products. The decision problem is broader than choosing the lowest-error model: stock, lead times, safety buffers, order packs and costs interact with forecasts.

## 3. Project objectives

Build an auditable data pipeline; compare statistical models to clear baselines; enforce purchasing constraints; quantify cost/service sensitivity; support human review; and define separate demonstration, pilot and production decisions. The forecast hypothesis was a fixed ≥5% development WAPE reduction, not a guaranteed benefit.

## 4. My role

I translated the brief into requirements and acceptance gates, selected and attributed the dataset, designed leakage controls and evaluation, implemented Python/Streamlit/OR-Tools components, investigated test failures, validated the application and wrote the decision case. The hypothetical Sponsor, Operations, Inventory, Analyst, ML, Finance and QA roles describe how a real organization could govern adoption; they were not actual collaborators.

## 5. Requirements and scope

The implementation covers 25 products, daily sales, 7/14/28-day forecasts, three development windows, one final holdout, three purchasing strategies and three financial scenarios. It runs locally on CPU with open-source packages, without a paid API or mandatory cloud. It cannot place orders. Customer identifiers are absent from processed/demo exports. Real stock reconstruction, procurement integration and production operations are outside scope.

## 6. Implementation approach

I downloaded the official UCI Online Retail workbook under CC BY 4.0, recorded checksums and checked all {q['raw_transactions']:,} records. The cleaning policy retains {q['valid_transactions']:,} positive-sales records through {q['date_end']}; it excludes returns/cancellations and invalid adjustments instead of converting them to demand. The final partial calendar date is excluded. The catalog uses only data through {f['selection_cutoff']}, before every validation window. Product names and cost proxies use the same historical boundary.

The hypothetical six-week roadmap separates discovery, preparation, modeling, decision support, validation and pilot assessment. Actual work was independent; manifests, JUnit XML and browser evidence document executed work rather than invented project meetings.

## 7. Technical architecture

{arch}

Data/configuration and initial evaluation artifacts are hash-verified. The dashboard reads the same measured evidence used by reports. Live assumption edits affect proposed plans, while fixed simulation evidence remains separate. No service holds purchasing credentials or sends orders.

## 8. Model selection

Weekly seasonal naive and a 28-day moving average provide practical reference points. StatsForecast AutoETS adds automatic statistical model fitting, while Croston SBA covers an intermittent-demand approach. Three 28-day rolling-origin windows determine one global model by pooled WAPE, with deterministic tie order. No final-holdout product filtering or tuning is allowed. AutoETS won; the fixed development improvement gate passed. Model errors/short histories use an explicit flagged fallback, not a silently relabeled prediction.

## 9. Forecast evaluation

Final holdout: {f['holdout_start']}–{f['holdout_end']}. Selected MAE {hold.mae:.3f}, RMSE {hold.rmse:.3f}, WAPE {hold.wape:.2%}, bias {hold.bias:.2%}, MASE {hold.mase:.3f}. Seasonal naive holdout WAPE was {naive.wape:.2%}. These are actual measured results; high absolute error and some product-level regressions remain visible.

{comparison}

WAPE/bias table values are fractions. Metrics use pooled product-day errors, while MASE uses each product's training-only seasonal scale. Undefined denominators remain blank/null. The initial holdout is preserved and verified on repeat runs; later full-history forecasts are labeled refits with unavailable future actuals.

## 10. Business optimization

The replenishment target covers forecast lead plus review demand and an explicit safety buffer. On-hand plus outstanding orders determine inventory position; MOQ and packs round positive needs. A uses an expanding average plus FIFO allocation, B the selected forecast plus the same FIFO, and C the same forecast plus an integer-pack OR-Tools model. Every plan is independently checked against the hard budget and product rules. This comparison avoids attributing an allocation effect entirely to predictive AI. The optimizer's single-review objective does not guarantee the lowest realized multi-period cost.

## 11. Risk management

I maintained 21 risks with fictional owner roles, including leakage, sales censoring, model volatility, supplier assumptions, budget errors, misleading ROI, user overreliance and missing operational monitoring. Technical mitigations include frozen selection, schema/constraint guards, explicit provenance, no customer-ID exports, product failure analysis and human review. Production risks remain open and influence the decision. A proposed RACI, training/monitoring plan and rollback to the baseline describe future governance without pretending that it already exists.

## 12. Simulated financial impact

The base scenario assumes 7-day lead/review cycles, initial seven-day cover, £3,000 per review, six-unit packs and MOQ 12. Unit purchase cost is an assumed 50% of training median retail price. Modeled operating cost includes purchases, closing-stock holding and lost-sales penalties. Historical observed sales may already be stockout-censored, so the simulation cannot estimate true lost customer demand.

Base cost: A £{base.loc['A','total_operating_cost']:,.2f}; B £{base.loc['B','total_operating_cost']:,.2f}; C £{base.loc['C','total_operating_cost']:,.2f}. B is {abs(base.loc['B','cost_reduction_vs_A']):.2%} more costly and C {abs(base.loc['C','cost_reduction_vs_A']):.2%} more costly than A. The optimized strategy improves modeled cost in the two stress scenarios, but base fill rates are only {base.loc['A','fill_rate']:.1%}/{base.loc['B','fill_rate']:.1%}/{base.loc['C','fill_rate']:.1%}. This is evidence against claiming a ready-to-use inventory benefit. Terminal/in-transit assets and asset-adjusted cost are reported to expose short-horizon accounting effects. No real savings, implementation costs, ROI or payback were measured.

## 13. GO / NO-GO decision

**Local demonstration: {readiness['local_demo']}. Controlled analytical pilot: {readiness['business_pilot']}. Production: NO-GO.** The pilot would stay in shadow mode until real cost, stock/availability and supplier data, an operational owner and monitoring are validated. I would keep the traditional purchasing policy rather than deploy the candidate based only on lower forecast error. See [formal decision](../project-management/10_go_no_go_decision.md).

## 14. Lessons learned

The file itself, not metadata alone, reveals missing values. Product selection and price proxies require the same leakage discipline as forecasting. A single partial day can distort daily evaluation. Better forecast accuracy does not guarantee better service or costs. Short-horizon purchase accounting needs terminal-asset visibility. Reproducible negative business results make a more credible implementation decision than a forced savings narrative. A local approval button is an illustration, not an enterprise approval trail.

Tests cover genuine model fitting, real data, chronological poisoning checks, metrics, inventory arithmetic, exhaustive small optimization, simulated conservation/costs and the actual Streamlit script. Real Chromium captures document the six-page application. The provided CI workflow has not been executed remotely because the repository has not been published.

## 15. Future roadmap

Acquire multi-year stock/availability and supplier-cost/arrival data; validate event and holiday features plus uncertainty in a new experiment; compare allocation policies with less arbitrary baselines; test multi-period service/cash objectives; run a governed shadow pilot. Production authorization, durable approval logging, integrations, drift monitoring and incident response follow only after operational benefit is established.

## Review evidence

[README and commands](../README.md) · [Forecast report](../reports/forecast-evaluation.md) · [Business analysis](../reports/business-impact-analysis.md) · [Two-minute demo](demo-guide.md) · [PM documents](../project-management/) · [Genuine screenshots](../screenshots/)

Dataset attribution: Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33. CC BY 4.0. This project filters and aggregates the source; no customer-level derivative is distributed.
""")


if __name__ == "__main__":
    write_portfolio()
    print("README and case study generated from measured artifacts")
