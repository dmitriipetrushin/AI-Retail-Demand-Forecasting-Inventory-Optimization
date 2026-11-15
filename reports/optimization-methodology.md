# Replenishment and optimization formulation

This is a deterministic single-review allocation model. It recommends assumed orders; there is no procurement connector.

For product i, use protection period Lᵢ + Rᵢ, point forecast sum Dᵢ, safety stock Sᵢ, on-hand Hᵢ and outstanding orders Oᵢ. Target Tᵢ = Dᵢ + Sᵢ; position Iᵢ = Hᵢ + Oᵢ. The unconstrained recommendation is zero when Tᵢ ≤ Iᵢ, otherwise ceil(max(Tᵢ − Iᵢ, MOQᵢ)/pᵢ) × pᵢ, where pᵢ is the pack size. No backorders are assumed. Outstanding orders count in position; the simulator separately schedules their arrival dates.

Define integer packs kᵢ ≥ 0, binary order activation zᵢ, and order quantity qᵢ = pᵢ kᵢ. Let Kᵢ be the recommended maximum pack count and Mᵢ = max(1, ceil(MOQᵢ/pᵢ)). Auxiliary continuous variables uᵢ, vᵢ ≥ 0 represent target shortage and excess.

Minimize:

```
sum_i [c_i q_i + shortage_penalty_i u_i + daily_holding_i R_i v_i]
```

Subject to:

```
M_i z_i <= k_i <= K_i z_i             integer pack / optional MOQ
u_i >= T_i - I_i - q_i                target shortfall
v_i >= I_i + q_i - T_i                target excess
sum_i cost_pennies_i q_i <= floor(100 * budget_GBP)
```

All costs are in GBP except the hard budget constraint, which uses integer pennies. Quantities cannot exceed the rounded recommendation. Costs and penalties are nonnegative assumptions, so the epigraph variables take their minimal feasible values. Holding is charged on **excess above the target** in this surrogate; the daily simulation charges holding on all end-of-day inventory. Safety stock is included in the target shortfall penalty. These choices make the model transparent but do not make it a stochastic or globally optimal inventory policy.

Implementation: OR-Tools MPSolver with SCIP, one thread, ten-second limit per review. Report OPTIMAL versus FEASIBLE explicitly; a time-limited feasible solution is not called optimal. Returned allocations are independently checked against budget, nonnegativity, integer packs, MOQ and recommendation caps. A tiny exhaustive-enumeration test verifies the objective on a two-product instance.

By default, ordering nothing is feasible even with a zero budget. The target is a soft objective, so a budget insufficient for the full target is **not** mathematical infeasibility. `required_products` can impose zᵢ = 1 for testing mandatory scenarios; insufficient budget or an incompatible recommendation cap then returns INFEASIBLE and no accepted plan. The dashboard has no mandatory-order requirement.

If OR-Tools or its solver is unavailable, deterministic product-code FIFO allocates affordable packs. The method/status explicitly says fallback, with no optimality claim. Baseline A and forecast policy B use the same FIFO budget mechanism; C uses the optimization objective. This separates forecast and allocation effects, but the ordering of FIFO remains an arbitrary benchmark.

Budget exactly binding means equality of integer expenditure and the budget in pennies. “Full plan affordable” and “product reduced by cap or economics” are also shown; reduced quantity alone does not prove which mathematical constraint caused it. MOQ, packs, and recommendation bounds can prevent using the remaining budget. An optimal solution may spend less when the modeled purchase cost exceeds its marginal shortage/excess benefit.

Limitations: no storage capacity, supplier capacity, order fixed charge, correlated uncertainty, future budget carryover or stochastic lead times. The model uses inventory position, so it cannot remove stockouts before a new order arrives. Compare the realized multi-period simulation and service metrics before drawing business conclusions.
