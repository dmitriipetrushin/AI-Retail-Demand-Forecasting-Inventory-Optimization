"""OR-Tools integer-pack replenishment; explicit deterministic fallback."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from src.inventory import constrain_fifo, validate_plan


@dataclass
class OptimizationResult:
    plan: object
    method: str
    status: str
    objective: float | None
    budget_binding: bool
    full_plan_affordable: bool
    message: str


def optimize(plan, budget, force_fallback=False, required_products=()):
    if not np.isfinite(budget) or budget < 0:
        raise ValueError("Budget must be finite and nonnegative")
    budget_cents = math.floor(budget * 100 + 1e-7)
    required = set(required_products)
    if required - set(plan.product_id):
        raise ValueError("Required products absent from plan")
    if force_fallback:
        solver = None
    else:
        try:
            from ortools.linear_solver import pywraplp
            solver = pywraplp.Solver.CreateSolver("SCIP")
        except ImportError:
            solver = None
    if solver is None:
        allocation = constrain_fifo(plan, budget)
        unmet_required = allocation.loc[allocation.product_id.isin(required), "order_qty"].eq(0).any()
        return OptimizationResult(allocation, "deterministic_fifo_fallback", "FALLBACK_UNSATISFIED" if unmet_required else "FALLBACK", None,
                                  False, bool(plan.purchase_cost.sum() <= budget), "OR-Tools unavailable/disabled. Product-code FIFO heuristic; no mathematical optimality claim. Unsatisfied required products mean this heuristic did not produce an acceptable plan, not proof of infeasibility.")
    solver.SetNumThreads(1)
    solver.SetTimeLimit(10000)
    objective = solver.Objective()
    costs, packs_vars = [], []
    for p in plan.itertuples():
        max_packs = int(p.recommended_qty // p.pack_size)
        min_packs = max(1, math.ceil(p.moq / p.pack_size))
        packs = solver.IntVar(0, max_packs, f"packs_{p.product_id}")
        active = solver.BoolVar(f"active_{p.product_id}")
        solver.Add(packs <= max_packs * active)
        solver.Add(packs >= min_packs * active)
        if p.product_id in required:
            solver.Add(active == 1)
        qty = p.pack_size * packs
        shortage = solver.NumVar(0, solver.infinity(), f"shortage_{p.product_id}")
        excess = solver.NumVar(0, solver.infinity(), f"excess_{p.product_id}")
        solver.Add(shortage >= p.target_inventory - p.inventory_position - qty)
        solver.Add(excess >= p.inventory_position + qty - p.target_inventory)
        objective.SetCoefficient(packs, p.unit_cost_cents / 100 * p.pack_size)
        objective.SetCoefficient(shortage, p.shortage_cost_per_unit)
        objective.SetCoefficient(excess, p.holding_cost_per_unit_day * p.review_days)
        costs.append(qty * int(p.unit_cost_cents))
        packs_vars.append((packs, int(p.pack_size)))
    solver.Add(solver.Sum(costs) <= budget_cents)
    objective.SetMinimization()
    status_code = solver.Solve()
    status = {pywraplp.Solver.OPTIMAL: "OPTIMAL", pywraplp.Solver.FEASIBLE: "FEASIBLE", pywraplp.Solver.INFEASIBLE: "INFEASIBLE"}.get(status_code, "NO_SOLUTION")
    allocated = plan.copy()
    if status not in ("OPTIMAL", "FEASIBLE"):
        allocated["order_qty"] = 0
        allocated["purchase_cost"] = 0.0
        return OptimizationResult(allocated, "OR-Tools SCIP MILP", status, None, False, False,
                                  "No feasible solution: inspect required products, MOQ, caps and budget. No plan accepted.")
    allocated["order_qty"] = [int(round(v.solution_value())) * size for v, size in packs_vars]
    allocated["purchase_cost"] = allocated.order_qty * allocated.unit_cost_cents / 100
    validate_plan(allocated, budget)
    spend_cents = int((allocated.order_qty * allocated.unit_cost_cents).sum())
    # Binding is exact equality in this integer model, distinct from merely budget-limited.
    return OptimizationResult(allocated, "OR-Tools SCIP MILP", status, objective.Value(), spend_cents == budget_cents,
                              bool(int((plan.recommended_qty * plan.unit_cost_cents).sum()) <= budget_cents),
                              "Optimal for a deterministic single-review surrogate; simulated multi-period outcomes can be worse.")
