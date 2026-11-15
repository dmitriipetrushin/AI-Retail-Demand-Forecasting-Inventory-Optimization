"""Retail Intelligence: local, evidence-based inventory decision support."""
from __future__ import annotations

import hashlib
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.common import ROOT, read_json
from src.dashboard_data import load_dashboard
from src.inventory import assumptions, recommend, constrain_fifo
from src.optimization import optimize

st.set_page_config(page_title="Retail Intelligence | Dmitry Petrushin", page_icon="📊", layout="wide")
st.markdown("""<style>
.block-container {padding-top:3.8rem; padding-bottom:3rem; max-width:1520px}
h1 {font-size:2.2rem!important; letter-spacing:-.055rem; font-weight:750!important}
h2 {font-size:1.4rem!important; letter-spacing:-.02rem}
h3 {font-size:1.08rem!important}
[data-testid="stMetric"] {background:white;border:1px solid #dde5eb;border-radius:10px;padding:15px 18px;min-height:115px}
[data-testid="stMetricLabel"] {font-size:.8rem;color:#526478}
[data-testid="stMetricLabel"] p {white-space:normal!important;overflow:visible!important;text-overflow:clip!important}
[data-testid="stMetricValue"] {font-size:1.75rem}
[data-testid="stSidebar"] {border-right:1px solid #dbe3ea}
.eyebrow {color:#087F8C;font-size:.74rem;font-weight:800;letter-spacing:.14rem;margin:0 0 5px}
.subline {color:#607389;font-size:.93rem;margin-top:-8px;margin-bottom:25px}
.note {border-left:3px solid #087F8C;background:#e8f3f3;padding:14px 18px;border-radius:4px;color:#274a55;margin:16px 0}
.brand {background:#142b3b;color:white;padding:18px 20px;border-radius:10px;margin-bottom:20px}
.brand span {color:#81d2ce;font-size:.73rem;letter-spacing:.12rem}
</style>""", unsafe_allow_html=True)

PAGES = ["Executive Dashboard", "Demand Forecasting", "Inventory Recommendations", "Budget Optimization", "Business Impact", "Evaluation & Deployment Readiness"]
COLORS = ["#087F8C", "#EB9C46", "#395D86", "#AD5C72"]
px.defaults.color_discrete_sequence = COLORS
px.defaults.template = "plotly_white"


@st.cache_data(show_spinner=False)
def artifacts(signature):
    return load_dashboard()


def money(value):
    return f"£{value:,.0f}"


def chart(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=15, t=30, b=10), font=dict(family="Arial", color="#30485c"),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=1.12, x=0))
    st.plotly_chart(fig, use_container_width=True)


def table(df, **kwargs):
    st.dataframe(df.rename(columns=lambda c: str(c).replace("_", " ").capitalize()), hide_index=True, use_container_width=True, **kwargs)


with st.sidebar:
    st.markdown('<div class="brand"><span>RETAIL INTELLIGENCE</span><br><b>Demand & inventory<br>control tower</b></div>', unsafe_allow_html=True)
    page = st.radio("Workspace", PAGES)
    st.divider()
    st.caption("INDEPENDENT PORTFOLIO PROJECT")
    st.write("Dmitry Petrushin")
    st.caption("Historical sales • UCI Online Retail\n\nLocal execution • No purchasing connection")

try:
    signature = tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for folder in [ROOT / "reports", ROOT / "data/processed"] for p in sorted(folder.glob("*")) if p.is_file())
    d = artifacts(signature)
except (FileNotFoundError, ValueError, KeyError) as exc:
    st.title("Retail Intelligence")
    st.error(f"Project evidence is not ready: {exc}")
    st.code("python -m scripts.download_data\npython -m scripts.prepare_data\npython -m scripts.train_models\npython -m scripts.run_evaluation\npython -m scripts.run_simulation\npython -m scripts.generate_reports")
    st.stop()

model = d["protocol"]["selected_model"]
daily, catalog = d["daily"], d["catalog"]
sim = d["simulation"]
base_sim = sim.loc[sim.scenario.eq("base")].set_index("strategy")
future = d["future"].copy()
future["forecast_date"] = pd.to_datetime(future.forecast_date)
selected_future = future.loc[future.model.eq(model)]
base_scenario = read_json(ROOT / "config/scenarios.json")["base"]

st.markdown('<p class="eyebrow">DECISION SUPPORT / HISTORICAL STUDY</p>', unsafe_allow_html=True)
st.title("Retail Intelligence")
st.markdown('<p class="subline"><b>AI Demand & Inventory Control Tower</b><br>Independent AI Implementation Portfolio Project · Real historical sales. Explicitly simulated inventory decisions.</p>', unsafe_allow_html=True)


def inputs_for_ui():
    if "inventory_inputs" not in st.session_state:
        st.session_state.inventory_inputs = assumptions(catalog, daily, base_scenario)
    return st.session_state.inventory_inputs.copy()


def safe_plan(inputs):
    try:
        return recommend(selected_future, inputs)
    except (ValueError, TypeError, OverflowError) as exc:
        st.error(f"Cannot build plan: {exc}. Check nonnegative inventory, integer lead/review days, and a protection period of at most 28 days.")
        st.stop()


if page == "Executive Dashboard":
    st.subheader("Executive overview")
    st.caption(f"Sales history: {d['quality']['date_start']} → {d['quality']['date_end']} · Holdout: {d['protocol']['holdout_start']} → {d['protocol']['holdout_end']}")
    c = st.columns(4)
    c[0].metric("Products analyzed · observed", len(catalog))
    c[1].metric("Forecast horizon", "28 days")
    c[2].metric("Selected model · development", model.upper())
    c[3].metric("Final holdout WAPE · observed", f"{d['selected_holdout']['wape']:.1%}")
    plan = safe_plan(inputs_for_ui())
    c = st.columns(4)
    c[0].metric("Assumed inventory value", money((plan.current_inventory * plan.unit_cost).sum()))
    c[1].metric("Modeled unmet sales · Strategy C", f"{base_sim.loc['C', 'unmet_units']:,.0f} units")
    c[2].metric("Purchase budget · per review", money(base_scenario["budget_per_review"]))
    c[3].metric("Modeled cost reduction · C vs A", f"{base_sim.loc['C', 'cost_reduction_vs_A']:.1%}")
    left, right = st.columns([1.65, 1])
    with left:
        st.subheader("Observed sales and final holdout forecast")
        actual = daily.groupby("date", as_index=False).units.sum().tail(84)
        pred = d["holdout"].loc[d["holdout"].model.eq(model)].groupby("forecast_date", as_index=False).predicted_units.sum()
        fig = go.Figure(go.Scatter(x=actual.date, y=actual.units, name="Observed unit sales", line=dict(color=COLORS[2])))
        fig.add_trace(go.Scatter(x=pred.forecast_date, y=pred.predicted_units, name=f"{model} holdout", line=dict(color=COLORS[0], dash="dash")))
        fig.update_yaxes(title="Units / day")
        chart(fig)
    with right:
        st.subheader("Modeled operating costs")
        plot = base_sim.reset_index().rename(columns={"purchase_expenditure": "Purchases", "holding_cost": "Holding", "shortage_cost": "Shortages"}).melt(id_vars="strategy", value_vars=["Purchases", "Holding", "Shortages"], var_name="Cost", value_name="GBP")
        chart(px.bar(plot, x="strategy", y="GBP", color="Cost", labels={"strategy": "Strategy"}))
    st.markdown('<div class="note"><b>Decision boundary:</b> observed sales support the forecasting metrics. Inventory, supplier constraints and all financial outcomes are simulated. Recommendations require human review; the application cannot place orders.</div>', unsafe_allow_html=True)
    st.write(f"**Local demonstration:** {d['decisions']['local_demo']} · **Controlled business pilot:** {d['decisions']['business_pilot']} · **Production:** {d['decisions']['production']}")

elif page == "Demand Forecasting":
    st.subheader("Demand forecasting")
    names = dict(zip(catalog.product_id, catalog.product_name))
    c = st.columns([3, 1, 1])
    product = c[0].selectbox("Product", catalog.product_id.tolist(), format_func=lambda x: f"{x} · {names[x]}")
    horizon = c[1].selectbox("Forecast horizon (days)", [7, 14, 28], index=2)
    view = c[2].selectbox("Forecast view", ["Final holdout", "Future refit"])
    models = st.multiselect("Compare models", d["protocol"]["configuration"]["models"], default=[model, "seasonal_naive"])
    hist = daily.loc[daily.product_id.eq(product)].tail(112)
    fig = go.Figure(go.Scatter(x=hist.date, y=hist.units, name="Observed sales", line=dict(color=COLORS[2])))
    source = d["holdout"] if view == "Final holdout" else future
    chosen = source.loc[source.product_id.eq(product) & source.model.isin(models) & source.step.le(horizon)]
    for idx, (name, sub) in enumerate(chosen.groupby("model", sort=False)):
        fig.add_trace(go.Scatter(x=sub.forecast_date, y=sub.predicted_units, name=name, line=dict(color=COLORS[idx % 4], dash="dash")))
    fig.update_yaxes(title="Units / day")
    chart(fig, 410)
    st.caption("Future refit starts 2011-12-09, after the historical study. It is not a forecast for today's retail market. The model choice remains frozen; future actuals are unavailable.")
    if view == "Final holdout":
        m = pd.read_csv(ROOT / "reports/holdout-product-metrics.csv", dtype={"product_id": str})
        table(m.loc[m.product_id.eq(product) & m.horizon.eq(horizon), ["model", "mae", "rmse", "wape", "bias", "mase"]])
        st.caption("WAPE and bias are fractions; positive bias means overforecasting. Blank metrics are mathematically undefined. Forecasts are point estimates, not uncertainty intervals.")
    table(chosen[["forecast_date", "model", "predicted_units", "actual_units", "train_end", "effective_model"]], height=230)

elif page == "Inventory Recommendations":
    st.subheader("Inventory recommendations")
    st.caption("Assumed state for the post-history refit. Changes are local to this session and shared with Budget Optimization. They do not rewrite the fixed business-impact experiments.")
    inputs = inputs_for_ui()
    edit_cols = ["product_id", "product_name", "current_inventory", "on_order", "lead_days", "review_days", "safety_stock", "pack_size", "moq", "unit_cost"]
    with st.form("inventory_assumptions"):
        edited = st.data_editor(inputs[edit_cols], key="inventory_grid", hide_index=True, use_container_width=True, height=300,
                                disabled=["product_id", "product_name", "pack_size", "moq", "unit_cost"],
                                column_config={name: st.column_config.NumberColumn(min_value=0, step=1) for name in ["current_inventory", "on_order", "safety_stock"]} |
                                {name: st.column_config.NumberColumn(min_value=1, max_value=21, step=1) for name in ["lead_days", "review_days"]})
        if st.form_submit_button("Apply assumptions", type="primary"):
            candidate = inputs.copy()
            for name in ["current_inventory", "on_order", "lead_days", "review_days", "safety_stock"]:
                candidate[name] = edited[name].to_numpy()
            safe_plan(candidate)
            st.session_state.inventory_inputs = candidate
            inputs = candidate
            st.session_state.pop("optimization", None)
            st.success("Assumptions applied. Recalculate budget allocation to review a new plan.")
    plan = safe_plan(inputs)
    c = st.columns(3)
    c[0].metric("Unconstrained proposed purchase", money(plan.purchase_cost.sum()))
    c[1].metric("Proposed units", f"{plan.order_qty.sum():,}")
    c[2].metric("Products below modeled demand", int(plan.risk.eq("Elevated").sum()))
    table(plan[["product_id", "product_name", "current_inventory", "forecast_demand", "safety_stock", "lead_days", "recommended_qty", "purchase_cost", "risk"]])
    st.caption("Target = forecast over lead + review days + safety stock. Inventory position = on hand + on order. Round positive need up to a pack multiple and at least MOQ. Lead-time changes retain the displayed safety-stock assumption; edit it explicitly if needed.")
    st.download_button("Download recommendation CSV", plan.to_csv(index=False), "simulated-recommendations.csv", "text/csv")

elif page == "Budget Optimization":
    st.subheader("Budget allocation & human review")
    st.caption("Single-review deterministic allocation using OR-Tools. All costs and inventory are assumed. A valid solution may leave money unspent when marginal purchases do not improve the modeled objective.")
    plan = safe_plan(inputs_for_ui())
    budget = st.number_input("Purchasing budget (£ per review)", min_value=0.0, max_value=1000000.0, value=3000.0, step=250.0)
    fingerprint = hashlib.sha256((plan.to_csv(index=False) + str(budget)).encode()).hexdigest()
    if st.button("Run budget optimization", type="primary"):
        result = optimize(plan, budget)
        st.session_state.optimization = (fingerprint, result)
        st.session_state.pop("plan_decision", None)
    saved = st.session_state.get("optimization")
    if saved and saved[0] != fingerprint:
        st.session_state.pop("optimization", None)
        st.session_state.pop("plan_decision", None)
        saved = None
    if saved and saved[0] == fingerprint:
        result = saved[1]
        allocated = result.plan
        traditional = constrain_fifo(plan, budget)
        c = st.columns(4)
        c[0].metric("Allocated purchase", money(allocated.purchase_cost.sum()))
        c[1].metric("Budget remaining", money(budget - allocated.purchase_cost.sum()))
        c[2].metric("Solver status", result.status)
        c[3].metric("Allocated units", f"{allocated.order_qty.sum():,}")
        st.write(f"**Method:** {result.method}. **Budget exactly binding:** {result.budget_binding}. **Full recommended plan affordable:** {result.full_plan_affordable}.")
        st.caption(result.message)
        allocation = allocated[["product_id", "product_name", "recommended_qty", "order_qty", "purchase_cost"]].copy()
        allocation["FIFO_qty"] = traditional.order_qty.to_numpy()
        allocation["reduced_by_cap_or_economics"] = allocation.order_qty.lt(allocation.recommended_qty)
        chart(px.bar(allocation.melt(id_vars="product_id", value_vars=["FIFO_qty", "order_qty"], var_name="Allocation", value_name="Units"), x="product_id", y="Units", color="Allocation", barmode="group"), 330)
        table(allocation, height=260)
        st.caption("Hard constraints: integer packs, zero or at least MOQ, no more than the rounded recommendation, and spend ≤ budget in integer pennies. A zero budget admits a zero-order plan; unmet targets remain visible.")
        if result.status in ("OPTIMAL", "FEASIBLE", "FALLBACK"):
            c = st.columns(2)
            if c[0].button("Accept simulated plan", type="primary"):
                st.session_state.plan_decision = "Accepted for demonstration only. No purchase was submitted."
            if c[1].button("Reject simulated plan"):
                st.session_state.plan_decision = "Rejected. No purchase was submitted."
            if "plan_decision" in st.session_state:
                st.success(st.session_state.plan_decision)
        st.download_button("Download allocation CSV", allocated.to_csv(index=False), "simulated-allocation.csv", "text/csv")
    else:
        st.info("Set a budget and run optimization to generate a reviewable plan. Changed inputs invalidate an earlier decision.")

elif page == "Business Impact":
    st.subheader("Business impact · simulation evidence")
    scenario = st.selectbox("Fixed assumption scenario", sim.scenario.unique())
    results = sim.loc[sim.scenario.eq(scenario)]
    c = st.columns(3)
    for col, row in zip(c, results.itertuples()):
        col.metric(f"Strategy {row.strategy} · modeled cost", money(row.total_operating_cost), f"{row.cost_reduction_vs_A:.1%} reduction vs A", delta_color="normal")
    st.caption("A: historical average + product-code FIFO · B: selected forecast + FIFO · C: selected forecast + optimization. Negative reduction means higher modeled cost.")
    plot = results.rename(columns={"purchase_expenditure": "Purchases", "holding_cost": "Holding", "shortage_cost": "Shortages"}).melt(id_vars="strategy", value_vars=["Purchases", "Holding", "Shortages"], var_name="Component", value_name="Modeled cost (£)")
    chart(px.bar(plot, x="strategy", y="Modeled cost (£)", color="Component"), 350)
    table(results[["strategy", "purchase_expenditure", "average_inventory", "holding_cost", "shortage_cost", "unmet_units", "fill_rate", "period_unit_turnover", "total_operating_cost", "asset_adjusted_cost", "outstanding_order_value"]])
    st.subheader("Sensitivity across three assumption scenarios")
    chart(px.bar(sim, x="scenario", y="total_operating_cost", color="strategy", barmode="group", labels={"total_operating_cost": "Modeled operating cost (£)"}), 300)
    with st.expander("Exact scenario assumptions and accounting"):
        st.json(read_json(ROOT / "config/scenarios.json"))
        st.write("Purchasing cost = training-period median retail price × assumed 50%, rounded to pennies. Daily holding = closing units × unit cost × annual rate / 365. Shortage penalties apply to unfilled historical-sales proxy units. Total = purchases + holding + shortages. Asset-adjusted cost credits closing and in-transit inventory and includes the initial stock value. No revenue or verified ROI is measured.")
    st.warning("These are modeled outcomes, not verified business savings. Observed sales may already be censored by stockouts. A 28-day simulation and one year of historical data do not establish production value.")

else:
    st.subheader("Evaluation & deployment readiness")
    c = st.columns(3)
    c[0].metric("Local demonstration", d["decisions"]["local_demo"])
    c[1].metric("Controlled business pilot", d["decisions"]["business_pilot"])
    c[2].metric("Production deployment", d["decisions"]["production"])
    st.write(d["decisions"]["rationale"])
    c = st.columns(3)
    c[0].metric("Development WAPE reduction", f"{d['protocol']['development_wape_improvement']:.1%}", "Predeclared target ≥ 5%")
    c[1].metric("Final holdout WAPE", f"{d['selected_holdout']['wape']:.1%}")
    c[2].metric("Simulation constraint compliance", "100%" if sim.constraints_pass.all() else "FAILED")
    st.caption(f"Frozen at {d['protocol']['frozen_at_utc']}. Catalog selection uses data through {d['protocol']['selection_cutoff']}. Final holdout remains unchanged after model selection.")
    comparison = d["comparison"].loc[d["comparison"].horizon.eq(28)]
    chart(px.bar(comparison, x="model", y="wape", color="phase", barmode="group", labels={"wape": "WAPE (lower is better)"}), 340)
    table(comparison[["phase", "model", "mae", "rmse", "wape", "bias", "mase", "fallback_rows"]])
    with st.expander("Development rolling origins"):
        table(d["folds"].loc[d["folds"].horizon.eq(28), ["fold", "train_end", "model", "mae", "wape", "bias", "mase"]])
    with st.expander("Acceptance criteria and known risks", expanded=True):
        st.write("Data and chronology validated; ≥5% development WAPE improvement; all tested purchasing constraints satisfied; zero real orders; passing test suite and reproducible reports. These gates enable an analytical demonstration, not operational procurement.")
        st.write("Open risks: censored sales, sparse annual coverage, wholesale outliers, no observed stock or supplier costs, deterministic point forecasts, assumed lead times, no live monitoring or enterprise integration. A business pilot requires validated operational inputs, shadow-mode review and approved monitoring.")

st.divider()
st.caption("Dmitry Petrushin · Independent Project Owner — AI Implementation & Project Management · Historical transactions: Chen (2015), UCI Online Retail, CC BY 4.0. All inventory and financial scenarios are simulated.")
