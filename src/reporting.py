"""Generate factual evaluation/business reports from saved experiment artifacts."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.common import ROOT, read_json, write_json, utc_now
from src.evaluation import verify_freeze, evaluate_holdout


def save(path, text):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.strip() + "\n")


def measured_context():
    frozen = verify_freeze()
    evaluate_holdout()
    comparison = pd.read_csv(ROOT / "reports/model-comparison.csv")
    primary = comparison.loc[comparison.horizon.eq(28)]
    selected = frozen["selected_model"]
    dev = primary.loc[primary.phase.eq("development") & primary.model.eq(selected)].iloc[0]
    hold = primary.loc[primary.phase.eq("holdout") & primary.model.eq(selected)].iloc[0]
    naive = primary.loc[primary.phase.eq("holdout") & primary.model.eq("seasonal_naive")].iloc[0]
    sim = pd.read_csv(ROOT / "reports/simulation-summary.csv")
    base = sim.loc[sim.scenario.eq("base")].set_index("strategy")
    quality = read_json(ROOT / "reports/data-quality-summary.json")
    return frozen, primary, dev, hold, naive, sim, base, quality


def generate_reports():
    f, primary, dev, hold, naive, sim, base, q = measured_context()
    selected = f["selected_model"]
    hold_improvement = 1 - hold.wape / naive.wape
    tests = None
    if (ROOT / "reports/test-results.xml").exists():
        suite = ET.parse(ROOT / "reports/test-results.xml").getroot().find("testsuite")
        tests = {k: int(suite.attrib.get(k, 0)) for k in ["tests", "failures", "errors", "skipped"]}
    browser = read_json(ROOT / "reports/browser-verification.json") if (ROOT / "reports/browser-verification.json").exists() else None
    mandatory = q["quality_pass"] and not primary.fallback_rows.any() and sim.constraints_pass.all()
    test_pass = bool(tests and tests["tests"] > 0 and tests["failures"] == tests["errors"] == tests["skipped"] == 0)
    browser_pass = bool(browser and browser.get("passed"))
    decisions = {"local_demo": "GO" if mandatory and test_pass and browser_pass else "CONDITIONAL GO",
                 "business_pilot": "CONDITIONAL GO" if mandatory and f["forecast_quality_gate_pass"] else "NO-GO",
                 "production": "NO-GO", "forecast_quality_gate_pass": f["forecast_quality_gate_pass"],
                 "constraint_gate_pass": bool(sim.constraints_pass.all()), "test_evidence": tests, "browser_verified": browser_pass,
                 "rationale": "Development forecast target passed, but base-scenario forecast/optimized policies cost more than the traditional baseline and service is weak. Observed sales are censored demand proxies and operational costs/stock are assumed. Retain the baseline for purchasing; consider only a conditional analytical shadow pilot with real operational inputs and monitoring. Production purchasing is not supported."}
    write_json(ROOT / "reports/readiness.json", decisions)
    folds = pd.read_csv(ROOT / "reports/development-fold-metrics.csv")
    prod = pd.read_csv(ROOT / "reports/holdout-product-metrics.csv", dtype={"product_id": str})
    selected_prod = prod.loc[prod.model.eq(selected) & prod.horizon.eq(28)].copy()
    naive_prod = prod.loc[prod.model.eq("seasonal_naive") & prod.horizon.eq(28)].set_index("product_id")
    selected_prod["naive_wape"] = selected_prod.product_id.map(naive_prod.wape)
    selected_prod["wape_difference_vs_naive"] = selected_prod.wape - selected_prod.naive_wape
    selected_prod.sort_values("wape", ascending=False).to_csv(ROOT / "reports/product-error-analysis.csv", index=False)
    worse = selected_prod.loc[selected_prod.wape_difference_vs_naive.gt(0)]
    save("reports/forecast-evaluation.md", f"""# Forecast evaluation

Measured from real UCI transactions. All figures below are calculated by `src/evaluation.py`; no random split or holdout-driven tuning is used.

## Protocol and selection

Product catalog and price/name metadata use data through **{f['selection_cutoff']}**, before any validation. Three expanding-history origins: 2011-08-18, 2011-09-15, 2011-10-13. Each predicts the next 28 days. The final holdout is **{f['holdout_start']} to {f['holdout_end']}** (700 product-days), evaluated after freezing rules, metrics, model configuration, catalog and input checksums at **{f['frozen_at_utc']}**. Forecasts for 7/14 days are leading portions of the same 28-day point forecast. They are reported, not used for selection.

Predeclared selection: {f['selection_rule']} The criterion is pooled product-day WAPE, not an average of product percentages. Selected **{selected}**, development WAPE **{dev.wape:.4%}** versus seasonal naive **{primary.loc[primary.phase.eq('development') & primary.model.eq('seasonal_naive'), 'wape'].iloc[0]:.4%}**; relative reduction **{f['development_wape_improvement']:.2%}**. Acceptance hypothesis: at least 5% relative development reduction. **{'PASS' if f['forecast_quality_gate_pass'] else 'FAIL'}**; this threshold was not changed after evaluation.

Seasonal naive repeats the latest seven daily values. Moving average repeats the latest 28-day mean. StatsForecast AutoETS searches its ZZZ error/trend/seasonal family with weekly period 7. Croston SBA is a statistical intermittent-demand candidate. AutoARIMA was omitted to keep this small CPU study bounded; no large neural model or LLM is needed. Insufficient histories/model failures use an explicitly flagged mean fallback, or zero when no history exists. Measured fallback rows: **{int(primary.fallback_rows.sum())}** across primary development and holdout comparison. Negative predictions are clamped to zero.

## Model comparison (primary 28-day horizon)

{primary[['phase','model','mae','rmse','wape','bias','mase','fallback_rows']].to_markdown(index=False, floatfmt='.6f')}

Selected final holdout: MAE **{hold.mae:.4f} units/product-day**, RMSE **{hold.rmse:.4f}**, WAPE **{hold.wape:.4%}**, bias **{hold.bias:.4%}**, MASE **{hold.mase:.4f}**. Relative holdout WAPE reduction versus seasonal naive: **{hold_improvement:.2%}**. This is a single post-selection diagnostic; it does not alter the chosen model.

## Definitions and aggregation

For error e = prediction − observed units: MAE = mean(|e|); RMSE = sqrt(mean(e²)); WAPE = sum(|e|)/sum(|actual|); bias = sum(e)/sum(|actual|), with positive bias meaning overprediction. Mean signed unit error is also exported. All pooled metrics treat every product-day equally; WAPE's denominator is all recorded units in those rows. They do not cancel errors across products. Product-level metrics and each fold are exported separately. Aggregate calendar-day totals are plotted for interpretation, not substituted for pooled product-level accuracy.

MASE divides each absolute error by the corresponding product/fold training-only mean absolute seasonal difference |y[t]−y[t−7]|. Aggregate MASE averages defined scaled errors and reports `mase_defined_rows`. With fewer than eight training days or zero seasonal scale it is undefined. WAPE/bias are undefined if the actual-unit denominator is zero. CSV blanks and JSON null preserve undefined values; they are never replaced with zero.

## Rolling origins, 28-day horizon

{folds.loc[folds.horizon.eq(28), ['fold','train_end','model','mae','wape','bias','mase']].to_markdown(index=False, floatfmt='.5f')}

## Evidence and limits

`frozen-protocol.json` records pre-holdout hashes and versions. `holdout-manifest.json` protects initial predictions/metrics from overwrite; repeated commands verify rather than retune. `future-forecasts.csv` refits all model configurations on the full prepared history only for demonstration of future inference. No future actuals are available. Point forecasts have no calibrated intervals. One annual cycle, wholesale spikes, calendar closures and stockout censoring limit transferability.

![Aggregate holdout forecast](figures/holdout-forecast.png)
""")
    save("reports/forecast-failure-analysis.md", f"""# Forecast failure analysis

Selected model: {selected}. **{len(worse)} of 25** products have higher final-holdout WAPE than seasonal naive. All 25 remain in evaluation. This analysis is descriptive and does not retune or remove products.

## Highest product-level WAPE (selected model)

{selected_prod.sort_values('wape', ascending=False)[['product_id','mae','rmse','wape','bias','mase','naive_wape']].head(10).to_markdown(index=False, floatfmt='.5f')}

## Products where seasonal naive is better

{worse[['product_id','wape','naive_wape','wape_difference_vs_naive']].to_markdown(index=False, floatfmt='.5f') if len(worse) else 'None in this holdout; this does not guarantee future dominance.'}

Large single-day quantities are retained because many customers are wholesalers. A smooth statistical forecast cannot anticipate individual bulk purchases. Zero recorded sales also include closed days and unknown stockouts; neither model sees stock availability. The Christmas-period holdout may differ from earlier development windows. Positive/negative bias can coexist across products; aggregate bias alone hides that problem.

No products were excluded after seeing these results. Next separately labeled experiments could test holiday indicators, forecast intervals, hierarchy pooling, longer histories, and intermittent-product segmentation. Initial holdout artifacts must remain unchanged.
""")
    scenarios = read_json(ROOT / "config/scenarios.json")
    save("reports/business-impact-analysis.md", business_report(sim, base, scenarios, f))
    save("project-management/08_model_evaluation_report.md", f"""# Measured model evaluation

Owner: Dmitry Petrushin. Independent implementation; no fictional role is claimed as an actual reviewer.

Selected **{selected}** using three chronological development windows. Development WAPE **{dev.wape:.2%}**, a **{f['development_wape_improvement']:.2%}** relative reduction versus weekly seasonal naive. The predeclared 5% development gate **{'passed' if f['forecast_quality_gate_pass'] else 'failed'}**.

Final untouched holdout {f['holdout_start']}–{f['holdout_end']}: MAE **{hold.mae:.3f}**, RMSE **{hold.rmse:.3f}**, WAPE **{hold.wape:.2%}**, bias **{hold.bias:.2%}**, MASE **{hold.mase:.3f}**. {len(worse)} products have higher holdout WAPE than seasonal naive; no products were removed. Holdout improvement against naive is {hold_improvement:.2%}. This result did not drive model reselection.

{primary[['phase','model','wape','mae','rmse','bias','mase']].to_markdown(index=False, floatfmt='.5f')}

Detailed formulas, undefined-metric handling, fold results, artifact integrity and limits: [forecast evaluation](../reports/forecast-evaluation.md). Product errors: [failure analysis](../reports/forecast-failure-analysis.md). Test status is recorded in the readiness decision rather than assumed from forecasting success.
""")
    save("project-management/09_business_case_and_roi.md", f"""# Business case and modeled financial outcomes

Decision question: is further operational validation justified, given forecast performance and scenario sensitivity? This is a fictional retailer, with no measured real-world savings or actual stakeholder participation.

{business_report(sim, base, scenarios, f)}

## Investment and ROI boundary

No real implementation expenditure, license invoice, labor rate, supplier cost or realized margin was collected. Therefore an observed ROI or payback period cannot be calculated. The differences above are modeled operating-cost differences, not cash benefits available to fund the project.

For a future pilot, Finance would validate costs and terminal valuation; Operations would collect stock/availability and lead-time data. A valid future ROI = (verified attributable benefit − full implementation and operating cost) / full implementation and operating cost. Do not annualize this 28-day period through the Christmas peak. Approval should depend on out-of-sample operational evidence and adoption, not a hypothetical ROI multiple.
""")
    save("project-management/10_go_no_go_decision.md", f"""# GO / NO-GO decision

## Local portfolio demonstration: {decisions['local_demo']}

Real data processed: {q['raw_transactions']:,} raw / {q['valid_transactions']:,} retained records, 25 selected products. Baselines and candidates ran. Chronology and initial holdout are hash-verified. Development improvement is {f['development_wape_improvement']:.2%} against a fixed 5% target. Simulation constraints pass for all nine strategy/scenario runs. Automated test evidence: {tests if tests else 'pending; do not claim passed'}. Browser evidence: {'passed; see reports/browser-verification.json' if browser_pass else 'pending; do not claim verified'}.

## Controlled business analytical pilot: {decisions['business_pilot']}

The technical hypothesis warrants a shadow-mode study, conditional on validated purchasing prices, stock records, supplier lead times, budget authority, demand availability/censoring, a named operational owner and fictional-role approvals becoming real organizational decisions. Use human review and baseline fallback. No autonomous procurement.

## Production inventory deployment: NO-GO

No stock truth, live supplier integration, multi-year history, calibrated uncertainty, SLOs, role-based authorization, durable audit trail or drift/incident response integration has been validated. A working portfolio app does not satisfy these requirements.

{decisions['rationale']}

Decision criteria were specified before the final holdout. Readiness is generated from current evidence; it is not an assertion that any business sponsor approved a deployment. Scope: one independent project, not an actual company rollout.
""")
    make_figures(selected)
    return decisions


def business_report(sim, base, scenarios, f):
    columns = ['scenario','strategy','purchase_expenditure','average_inventory','holding_cost','shortage_cost','unmet_units','period_unit_turnover','total_operating_cost','cost_reduction_vs_A']
    losses = sim.loc[sim.cost_reduction_vs_A.lt(0), ['scenario','strategy','cost_reduction_vs_A']]
    return f"""# Business impact analysis (simulation only)

Observed transaction sales are the realized demand proxy, not proof of unconstrained customer demand. All inventory, supplier, purchasing cost, holding and shortage inputs below are **assumptions**. No orders or financial transactions are executed.

## Fixed experiment

25 identical products; {f['holdout_start']}–{f['holdout_end']} inclusive. All strategies start from identical stock, with no initial pipeline, and see only the same recorded history through the day before each review. A uses the expanding historical average; B uses the development-selected {f['selected_model']}; both allocate budget by ascending product code. C uses the same forecast as B and an OR-Tools integer-pack allocation. Every strategy obeys the same review budget. Product-code FIFO is simple but arbitrary, so C's improvement must not be attributed solely to predictive AI.

Receipts occur at the start of the day, then the review/order, then realized sales and end-of-day holding. A lead L order arrives at day t+L. Unmet proxy sales are lost, not backlogged. Forecasts update at weekly reviews using actual recorded sales, even when the simulated strategy could not fill them; this assumes all strategies observe the same exogenous sales proxy. The static final-holdout forecast evaluation remains separate from this updating policy simulation.

## Exact cost and inventory assumptions

Purchase price = max(£0.01, round(training-only median retail price × 0.50, to pennies)); **retail prices are not observed supplier costs**. Initial units = ceil(latest 28-day training mean × cover days). Safety stock = z × sample standard deviation of latest 28 recorded daily sales × sqrt(lead + review days). This is an illustrative independence/normal-style buffer, not a calibrated service-level guarantee. Inventory position = on hand + outstanding orders; target = forecast demand over lead + review days + safety. Round positive need up to pack size and MOQ. No capacity cap or supplier delay distribution is assumed.

{pd.DataFrame(scenarios).T.to_markdown()}

Daily holding = end-of-day units × assumed unit purchase cost × annual holding rate / 365. Shortage cost = unfilled sales-proxy units × assumed purchase cost × shortage multiple. Total modeled operating cost = purchasing expenditure + holding + shortage. Unit turnover = fulfilled units / mean daily total closing inventory, over these 28 days only, undefined when average stock is zero. Initial stock is not an order expenditure. Purchases due beyond the horizon are included in expenditure and separately reported as outstanding assets.

## Measured simulation outputs

{sim[columns].to_markdown(index=False, floatfmt='.3f')}

Under the stated **base** simulation assumptions, Strategy B produced **{abs(base.loc['B','cost_reduction_vs_A']):.2%} {'lower' if base.loc['B','cost_reduction_vs_A'] >= 0 else 'higher'} modeled operating costs** than Strategy A; Strategy C produced **{abs(base.loc['C','cost_reduction_vs_A']):.2%} {'lower' if base.loc['C','cost_reduction_vs_A'] >= 0 else 'higher'} modeled operating costs** than Strategy A. Base costs: A **£{base.loc['A','total_operating_cost']:,.2f}**, B **£{base.loc['B','total_operating_cost']:,.2f}**, C **£{base.loc['C','total_operating_cost']:,.2f}**. These are not verified real-world savings. Base fill rates are A {base.loc['A','fill_rate']:.1%}, B {base.loc['B','fill_rate']:.1%}, C {base.loc['C','fill_rate']:.1%}; the assumed budget/initial stock are insufficient for good service. The base scenario does not support replacing the baseline policy.

## Terminal assets and alternative accounting

The primary cash-plus-penalties comparison can favor policies that buy less and penalize policies with useful closing inventory. Therefore also report asset-adjusted cost = total modeled operating cost + initial inventory value − terminal on-hand value − in-transit value. This values units at assumed purchase cost, without salvage discount; it is still a model, not profit. No revenue, margin, discounting, tax, financing or implementation costs are measured.

{sim[['scenario','strategy','initial_inventory_value','terminal_inventory_value','outstanding_order_value','asset_adjusted_cost','fill_rate']].to_markdown(index=False, floatfmt='.3f')}

## Sensitivity and failure conditions

Measured cases where a proposed strategy has **higher** total modeled cost than A:

{losses.to_markdown(index=False, floatfmt='.4f') if len(losses) else 'None among these three scenarios. This small scenario grid does not establish general dominance.'}

The optimizer minimizes a single-review target shortage/excess surrogate and does not optimize the full realized 28-day cost. It can underfund a product, carry unusable excess, miss lead-time sales, or lose to FIFO when forecasts are wrong. Longer lead times and a tighter budget reveal exposure; low shortage penalties can make buying less look financially attractive while service degrades. Bulk orders and holiday shifts are not forecastable from these inputs. The final period lacks terminal demand, and changing terminal valuation can change rankings. A cost decrease alone is insufficient: inspect fill rates, unmet units and working capital as well.

Every review budget, nonnegative integer order, pack multiple, MOQ and stock-conservation check is validated at runtime and in tests. `simulation-orders.csv` and `simulation-ledger.csv` contain reproducible evidence. This sensitivity analysis is descriptive; no parameter was selected to maximize the final-holdout benefit.
"""


def make_figures(selected):
    (ROOT / "reports/figures").mkdir(parents=True, exist_ok=True)
    pred = pd.read_csv(ROOT / "reports/holdout-predictions.csv", parse_dates=["forecast_date"])
    grouped = pred.loc[pred.model.eq(selected)].groupby("forecast_date")[["actual_units", "predicted_units"]].sum()
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(grouped.index, grouped.actual_units, color="#395D86", label="Observed sales proxy")
    ax.plot(grouped.index, grouped.predicted_units, color="#087F8C", linestyle="--", label=f"{selected} (frozen origin)")
    ax.set(title="Final 28-day holdout: aggregate daily units", ylabel="Units", xlabel="Historical date")
    ax.legend(frameon=False)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(ROOT / "reports/figures/holdout-forecast.png", dpi=140)
    plt.close(fig)
    comparison = pd.read_csv(ROOT / "reports/model-comparison.csv")
    pivot = comparison.loc[comparison.horizon.eq(28)].pivot(index="model", columns="phase", values="wape")
    fig, ax = plt.subplots(figsize=(9, 4))
    pivot.plot.bar(ax=ax, color=["#087F8C", "#EB9C46"], rot=0)
    ax.set(title="Pooled product-day forecast errors", ylabel="WAPE (fraction)", xlabel="Model")
    fig.tight_layout()
    fig.savefig(ROOT / "reports/figures/model-comparison.png", dpi=140)
    plt.close(fig)
