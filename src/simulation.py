"""Daily lost-sales simulation, with no future sales used by purchasing policies."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.common import ROOT, read_json, write_json, sha256
from src.evaluation import load_prepared, verify_freeze
from src.forecasting import forecast_panel
from src.inventory import assumptions, constrain_fifo, recommend, validate_scenario, validate_plan
from src.optimization import optimize

STRATEGIES = {"A": "Historical-average + FIFO", "B": "Selected forecast + FIFO", "C": "Selected forecast + optimization"}


def historical_average_panel(history, catalog, origin):
    rows = []
    for p in catalog.itertuples():
        mean = history.loc[history.product_id.eq(p.product_id), "units"].mean()
        rows.append(pd.DataFrame({"product_id": p.product_id, "forecast_date": pd.date_range(pd.Timestamp(origin) + pd.Timedelta(days=1), periods=28), "predicted_units": float(mean)}))
    return pd.concat(rows, ignore_index=True)


def simulate(daily, catalog, start, end, scenario, strategy, model, forecast_cache=None):
    validate_scenario(scenario)
    if strategy not in STRATEGIES:
        raise ValueError("Unknown strategy")
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if start > end:
        raise ValueError("Simulation start must precede end")
    past = daily.loc[daily.date.lt(start)]
    inputs = assumptions(catalog, past, scenario).set_index("product_id")
    stock = inputs.current_inventory.astype(float).to_dict()
    initial_stock = dict(stock)
    pipeline, ledger, orders = [], [], []
    forecast_cache = {} if forecast_cache is None else forecast_cache
    demand_map = daily.set_index(["date", "product_id"]).units
    for day_idx, date in enumerate(pd.date_range(start, end)):
        receipts = {p: 0 for p in stock}
        for arriving, product, qty in pipeline:
            if arriving == date:
                stock[product] += qty
                receipts[product] += qty
        pipeline = [item for item in pipeline if item[0] > date]
        day_orders = {p: 0 for p in stock}
        if day_idx % scenario["review_days"] == 0:
            origin = date - pd.Timedelta(days=1)
            history = daily.loc[daily.date.le(origin)].copy()
            # Forecast cache contains only model/date predictions, never inventory state.
            key = (str(origin.date()), "historical_average" if strategy == "A" else model)
            if key not in forecast_cache:
                forecast_cache[key] = (historical_average_panel(history, catalog, origin) if strategy == "A"
                                       else forecast_panel(history, catalog, origin, [model], phase="simulation"))
            current = assumptions(catalog, history, scenario).set_index("product_id")
            current["current_inventory"] = pd.Series(stock)
            current["on_order"] = [sum(q for _, pid, q in pipeline if pid == product) for product in current.index]
            plan = recommend(forecast_cache[key], current.reset_index())
            if strategy == "C":
                optimization = optimize(plan, scenario["budget_per_review"])
                if optimization.status not in ("OPTIMAL", "FEASIBLE", "FALLBACK"):
                    raise ValueError("Simulation optimization has no feasible allocation")
                allocated, method, status = optimization.plan, optimization.method, optimization.status
            else:
                allocated = constrain_fifo(plan, scenario["budget_per_review"])
                method, status = "Product-code FIFO heuristic", "VALID"
            validate_plan(allocated, scenario["budget_per_review"])
            for row in allocated.itertuples():
                qty = int(row.order_qty)
                if qty:
                    pipeline.append((date + pd.Timedelta(days=int(row.lead_days)), row.product_id, qty))
                day_orders[row.product_id] = qty
                orders.append({"date": date, "strategy": strategy, "product_id": row.product_id,
                               "order_qty": qty, "pack_size": row.pack_size, "moq": row.moq,
                               "recommended_qty": row.recommended_qty, "purchase_cost": row.purchase_cost,
                               "unit_cost_cents": row.unit_cost_cents, "method": method, "status": status,
                               "forecast_train_end": origin, "budget": scenario["budget_per_review"]})
        for product in stock:
            if (date, product) not in demand_map:
                raise ValueError("Missing realized sales; zero must be represented explicitly")
            demand = float(demand_map[(date, product)])
            if not np.isfinite(demand) or demand < 0:
                raise ValueError("Invalid realized sales")
            fulfilled = min(stock[product], demand)
            unmet = demand - fulfilled
            stock[product] -= fulfilled
            p = inputs.loc[product]
            ledger.append({"date": date, "product_id": product, "strategy": strategy,
                           "sales_proxy": demand, "fulfilled_units": fulfilled, "unmet_units": unmet,
                           "received_units": receipts[product], "closing_inventory": stock[product],
                           "holding_cost": stock[product] * p.holding_cost_per_unit_day,
                           "shortage_cost": unmet * p.shortage_cost_per_unit,
                           "purchase_cost": day_orders[product] * p.unit_cost})
    ledger, orders = pd.DataFrame(ledger), pd.DataFrame(orders)
    purchase, holding, shortage = (float(ledger[col].sum()) for col in ["purchase_cost", "holding_cost", "shortage_cost"])
    average = float(ledger.groupby("date").closing_inventory.sum().mean())
    terminal_value = sum(stock[p] * inputs.loc[p, "unit_cost"] for p in stock)
    transit_value = sum(q * inputs.loc[p, "unit_cost"] for _, p, q in pipeline)
    initial_value = sum(q * inputs.loc[p, "unit_cost"] for p, q in initial_stock.items())
    for product in stock:
        sub = ledger.loc[ledger.product_id.eq(product)]
        if not math.isclose(initial_stock[product] + sub.received_units.sum() - sub.fulfilled_units.sum(), stock[product], abs_tol=1e-7):
            raise ValueError("Stock conservation failed")
    summary = {"strategy": strategy, "description": STRATEGIES[strategy], "purchase_expenditure": purchase,
               "average_inventory": average, "holding_cost": holding, "shortage_cost": shortage,
               "unmet_units": float(ledger.unmet_units.sum()), "fulfilled_units": float(ledger.fulfilled_units.sum()),
               "sales_proxy_units": float(ledger.sales_proxy.sum()),
               "fill_rate": float(ledger.fulfilled_units.sum() / ledger.sales_proxy.sum()) if ledger.sales_proxy.sum() else None,
               "period_unit_turnover": float(ledger.fulfilled_units.sum() / average) if average else None,
               "total_operating_cost": purchase + holding + shortage,
               "initial_inventory_value": initial_value, "terminal_inventory_value": float(terminal_value),
               "outstanding_order_value": float(transit_value),
               "asset_adjusted_cost": purchase + holding + shortage + initial_value - terminal_value - transit_value,
               "budget_per_review": scenario["budget_per_review"],
               "optimization_methods": sorted(orders.method.unique().tolist()), "constraints_pass": True}
    return summary, ledger, orders


def run_scenarios():
    frozen = verify_freeze()
    daily, catalog, _ = load_prepared()
    scenarios = read_json(ROOT / "config/scenarios.json")
    summaries, ledgers, orders, cache = [], [], [], {}
    for name, scenario in scenarios.items():
        for strategy in STRATEGIES:
            summary, ledger, order = simulate(daily, catalog, frozen["holdout_start"], frozen["holdout_end"], scenario, strategy, frozen["selected_model"], cache)
            summaries.append({"scenario": name, **summary})
            ledgers.append(ledger.assign(scenario=name))
            orders.append(order.assign(scenario=name))
    result = pd.DataFrame(summaries)
    for name, group in result.groupby("scenario"):
        base = float(group.loc[group.strategy.eq("A"), "total_operating_cost"].iloc[0])
        result.loc[result.scenario.eq(name), "cost_reduction_vs_A"] = 1 - group.total_operating_cost / base
    result.to_csv(ROOT / "reports/simulation-summary.csv", index=False)
    pd.concat(ledgers).to_csv(ROOT / "reports/simulation-ledger.csv", index=False)
    pd.concat(orders).to_csv(ROOT / "reports/simulation-orders.csv", index=False)
    write_json(ROOT / "reports/simulation-manifest.json", {"config": scenarios, "selected_model": frozen["selected_model"],
                "start": frozen["holdout_start"], "end": frozen["holdout_end"], "seed": 42,
                "sha256": {p: sha256(ROOT / p) for p in ["config/scenarios.json", "src/inventory.py", "src/optimization.py", "src/simulation.py",
                  "reports/simulation-summary.csv", "reports/simulation-ledger.csv", "reports/simulation-orders.csv"]}})
    return result
