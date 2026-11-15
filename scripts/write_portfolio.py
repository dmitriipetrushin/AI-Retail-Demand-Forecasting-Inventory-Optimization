"""Refresh the measured case study; README.md is maintained separately."""
from src.common import ROOT, read_json
from src.reporting import measured_context, save


def write_portfolio():
    f, primary, dev, hold, naive, sim, base, q = measured_context()
    readiness = read_json(ROOT / "reports/readiness.json")
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
    print("Case study generated from measured artifacts; README maintained separately")
