import itertools
import numpy as np
import pytest

from src.inventory import assumptions, recommend, order_quantity, constrain_fifo, validate_plan, validate_scenario
from src.optimization import optimize
from src.simulation import historical_average_panel, simulate


def plan_for(toy_data):
    daily, catalog, scenario = toy_data
    history = daily.loc[daily.date.lt("2020-04-22")]
    return recommend(historical_average_panel(history, catalog, "2020-04-21"), assumptions(catalog, history, scenario))


@pytest.mark.parametrize("target,position,pack,moq,expected", [(20, 25, 6, 12, 0), (20, 19, 6, 12, 12), (20, 1, 6, 12, 24), (20, 8, 6, 12, 12), (10, 9, 6, 13, 18)])
def test_reorder_formula(target, position, pack, moq, expected):
    assert order_quantity(target, position, pack, moq) == expected


def test_invalid_scenario(toy_data):
    _, _, s = toy_data
    with pytest.raises(ValueError):
        validate_scenario({**s, "lead_days": 28})
    with pytest.raises(ValueError):
        order_quantity(1, 0, 0, 1)


def test_forecast_requirement_and_inventory_position(toy_data):
    daily, catalog, scenario = toy_data
    inputs = assumptions(catalog, daily, scenario)
    inputs["on_order"] = 10000
    forecasts = historical_average_panel(daily, catalog, daily.date.max())
    assert recommend(forecasts, inputs).order_qty.sum() == 0
    with pytest.raises(ValueError, match="Insufficient"):
        recommend(forecasts.head(1), inputs)


@pytest.mark.parametrize("budget", [0., .01, 5., 24.49, 1000.])
def test_budget_pack_moq_constraints(toy_data, budget):
    plan = plan_for(toy_data)
    for result in [optimize(plan, budget), optimize(plan, budget, force_fallback=True)]:
        assert validate_plan(result.plan, budget)
        assert result.plan.purchase_cost.sum() <= budget + 1e-8
    assert validate_plan(constrain_fifo(plan, budget), budget)


def test_infeasible_required_product_detected(toy_data):
    result = optimize(plan_for(toy_data), 0, required_products=["10001"])
    assert result.status == "INFEASIBLE"
    assert result.plan.order_qty.sum() == 0


def test_fallback_cannot_prove_required_plan_infeasible(toy_data):
    plan = plan_for(toy_data)
    heuristic = optimize(plan, 6, force_fallback=True, required_products=["10002"])
    exact = optimize(plan, 6, required_products=["10002"])
    assert heuristic.status == "FALLBACK_UNSATISFIED"
    assert exact.status == "OPTIMAL"
    assert exact.plan.loc[exact.plan.product_id.eq("10002"), "order_qty"].iloc[0] == 4


def test_optimizer_matches_bruteforce(toy_data):
    plan = plan_for(toy_data)
    budget = 30.
    result = optimize(plan, budget)
    values = []
    for quantities in itertools.product(*[range(0, int(p.recommended_qty) + 1, int(p.pack_size)) for p in plan.itertuples()]):
        if any(q and q < p.moq for p, q in zip(plan.itertuples(), quantities)):
            continue
        cost = sum(q * p.unit_cost for p, q in zip(plan.itertuples(), quantities))
        if cost > budget:
            continue
        value = cost + sum(max(p.target_inventory - p.inventory_position - q, 0) * p.shortage_cost_per_unit
                           + max(p.inventory_position + q - p.target_inventory, 0) * p.holding_cost_per_unit_day * p.review_days
                           for p, q in zip(plan.itertuples(), quantities))
        values.append(value)
    assert result.method == "OR-Tools SCIP MILP"
    assert result.status == "OPTIMAL"
    assert result.objective == pytest.approx(min(values))


@pytest.mark.parametrize("strategy", ["A", "B", "C"])
def test_simulation_costs_and_conservation(toy_data, strategy):
    daily, catalog, scenario = toy_data
    summary, ledger, orders = simulate(daily, catalog, "2020-04-22", "2020-05-19", scenario, strategy, "moving_average")
    assert summary["total_operating_cost"] == pytest.approx(ledger[["purchase_cost", "holding_cost", "shortage_cost"]].sum().sum())
    assert summary["sales_proxy_units"] == 280
    assert summary["unmet_units"] > 0  # Lead-time stockout, initial cover only one day.
    assert ledger.closing_inventory.min() >= 0
    assert (orders.groupby("date").purchase_cost.sum() <= scenario["budget_per_review"]).all()
    assert (orders.forecast_train_end < orders.date).all()


def test_simulation_first_order_cannot_see_future(toy_data):
    daily, catalog, scenario = toy_data
    _, _, original = simulate(daily, catalog, "2020-04-22", "2020-05-19", scenario, "B", "moving_average")
    poisoned = daily.copy()
    poisoned.loc[poisoned.date.ge("2020-04-22"), "units"] = 100
    _, _, changed = simulate(poisoned, catalog, "2020-04-22", "2020-05-19", scenario, "B", "moving_average")
    np.testing.assert_array_equal(original.loc[original.date.eq("2020-04-22"), "order_qty"].to_numpy(), changed.loc[changed.date.eq("2020-04-22"), "order_qty"].to_numpy())
