"""Transparent order-up-to inventory rules. All inventory/cost inputs are assumed."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def validate_scenario(s):
    for field in ["lead_days", "review_days", "pack_size", "moq"]:
        if not isinstance(s[field], (int, np.integer)) or s[field] < (0 if field == "moq" else 1):
            raise ValueError(f"{field} must be an integer in its allowed range")
    if s["lead_days"] + s["review_days"] > 28:
        raise ValueError("Protection period must not exceed supported 28-day horizon")
    for key in ["safety_z", "initial_cover_days", "budget_per_review", "purchase_price_fraction", "annual_holding_rate", "shortage_cost_multiple"]:
        if not np.isfinite(s[key]) or s[key] < 0:
            raise ValueError(f"{key} must be finite and nonnegative")
    if s["purchase_price_fraction"] <= 0:
        raise ValueError("Purchase-price fraction must be positive")


def assumptions(catalog, history, scenario):
    validate_scenario(scenario)
    rows = []
    for p in catalog.itertuples():
        y = history.loc[history.product_id.eq(p.product_id)].sort_values("date").units.to_numpy(dtype=float)
        if not len(y):
            raise ValueError(f"No history for {p.product_id}")
        recent = y[-28:]
        cents = max(1, int(round(p.median_retail_price * scenario["purchase_price_fraction"] * 100)))
        rows.append({"product_id": p.product_id, "product_name": p.product_name,
                     "current_inventory": int(math.ceil(recent.mean() * scenario["initial_cover_days"])), "on_order": 0,
                     "lead_days": scenario["lead_days"], "review_days": scenario["review_days"],
                     "safety_stock": float(scenario["safety_z"] * recent.std(ddof=1) * math.sqrt(scenario["lead_days"] + scenario["review_days"])) if len(recent) > 1 else 0.0,
                     "unit_cost_cents": cents, "unit_cost": cents / 100,
                     "holding_cost_per_unit_day": cents / 100 * scenario["annual_holding_rate"] / 365,
                     "shortage_cost_per_unit": cents / 100 * scenario["shortage_cost_multiple"],
                     "pack_size": scenario["pack_size"], "moq": scenario["moq"]})
    return pd.DataFrame(rows)


def order_quantity(target, position, pack_size, moq):
    if not all(np.isfinite([target, position, pack_size, moq])) or pack_size < 1 or moq < 0 or int(pack_size) != pack_size or int(moq) != moq:
        raise ValueError("Invalid target, inventory position, MOQ, or integer pack size")
    need = max(0.0, target - position)
    return 0 if need == 0 else int(math.ceil(max(need, moq) / pack_size) * pack_size)


def recommend(forecasts, inputs):
    if inputs.product_id.duplicated().any():
        raise ValueError("Duplicate product inputs")
    rows = []
    for p in inputs.itertuples():
        fields = [p.current_inventory, p.on_order, p.safety_stock, p.unit_cost_cents, p.lead_days, p.review_days, p.pack_size, p.moq]
        if not np.isfinite(fields).all() or p.current_inventory < 0 or p.on_order < 0 or p.safety_stock < 0 or p.unit_cost_cents <= 0:
            raise ValueError("Inventory and safety stock must be nonnegative; cost must be positive")
        if any(int(v) != v for v in [p.lead_days, p.review_days, p.pack_size, p.moq, p.unit_cost_cents]) or min(p.lead_days, p.review_days, p.pack_size) < 1 or p.moq < 0:
            raise ValueError("Lead/review days, pack size, MOQ and pennies must be valid integers")
        period = int(p.lead_days + p.review_days)
        f = forecasts.loc[forecasts.product_id.eq(p.product_id)].sort_values("forecast_date").head(period)
        if len(f) != period or not np.isfinite(f.predicted_units).all() or f.predicted_units.lt(0).any():
            raise ValueError(f"Insufficient or invalid protection-period forecast for {p.product_id}")
        expected = float(f.predicted_units.sum())
        target = expected + p.safety_stock
        position = p.current_inventory + p.on_order
        qty = order_quantity(target, position, p.pack_size, p.moq)
        rows.append({**p._asdict(), "forecast_demand": expected, "target_inventory": target,
                     "inventory_position": position, "recommended_qty": qty, "order_qty": qty,
                     "purchase_cost": qty * p.unit_cost_cents / 100,
                     "risk": "Elevated" if position < expected else "Covered (modeled)"})
    return pd.DataFrame(rows)


def constrain_fifo(plan, budget):
    """Traditional deterministic allocation in product-code order; no optimality claim."""
    if not np.isfinite(budget) or budget < 0:
        raise ValueError("Budget must be finite and nonnegative")
    result = plan.copy()
    remaining = int(math.floor(budget * 100 + 1e-7))
    for idx in result.sort_values("product_id").index:
        p = result.loc[idx]
        packs = min(int(p.recommended_qty // p.pack_size), remaining // int(p.pack_size * p.unit_cost_cents))
        qty = packs * int(p.pack_size)
        if qty < p.moq:
            qty = 0
        result.loc[idx, "order_qty"] = qty
        remaining -= qty * int(p.unit_cost_cents)
    result["order_qty"] = result.order_qty.astype(int)
    result["purchase_cost"] = result.order_qty * result.unit_cost_cents / 100
    validate_plan(result, budget)
    return result


def validate_plan(plan, budget):
    q = plan.order_qty.to_numpy(dtype=float)
    valid = (np.isfinite(q).all() and (q >= 0).all() and (q == np.floor(q)).all()
             and (plan.order_qty.mod(plan.pack_size) == 0).all()
             and ((plan.order_qty == 0) | (plan.order_qty >= plan.moq)).all()
             and (plan.order_qty <= plan.recommended_qty).all()
             and int((plan.order_qty * plan.unit_cost_cents).sum()) <= math.floor(budget * 100 + 1e-7))
    if not valid:
        raise ValueError("Purchase plan violates budget, integer, MOQ, pack, or recommendation bounds")
    return True
