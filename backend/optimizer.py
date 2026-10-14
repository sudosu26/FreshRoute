import hashlib
import json
import math
from typing import Any, Dict, List, Optional, Tuple, Union


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Safe attribute/key retriever across dicts and ORM instances."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _num(val: Any, default: float = 0.0) -> float:
    """Safe numeric parser with finite validation."""
    try:
        n = float(val)
        return n if math.isfinite(n) else default
    except (TypeError, ValueError):
        return default


def _format_days(days: float) -> str:
    """Format days cleanly."""
    return f"{days:+.1f}d" if abs(days) >= 0.05 else "0.0d"


def _discount_pct(margin_days: float) -> float:
    """
    Recommend clearance discount percentage when remaining shelf life < transport time + 1 day.
    Scales smoothly from 10% (at 0.9d margin) to 35% (at tight margin).
    """
    if margin_days >= 1.0:
        return 0.0
    return round(min(35.0, max(10.0, (1.0 - max(0.0, margin_days)) * 35.0)), 1)


def plan_hash(plan: List[Dict[str, Any]], seed: Optional[int]) -> str:
    """Compute deterministic SHA1 hash of the dispatch allocation for engineering audit."""
    canonical = json.dumps(
        {"seed": seed, "dispatches": [
            {"b": d.get("batch_id"), "d": d.get("destination_name"), "q": d.get("quantity_kg"), "disc": d.get("discount_pct")}
            for d in plan
        ]},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:12]


def run_optimized(
    batches: List[Any],
    destinations: List[Any],
    trucks: Optional[List[Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Optimized Heuristic Dispatch Planner:
    1. Sorts batches by remaining shelf life ascending (urgent batches first).
    2. Filters out infeasible transit routes where produce would spoil before arrival.
    3. Recommends dynamic clearance markdowns if shelf life < transport time + 1 day.
    4. Matches urgent batches to nearby high-demand markets to preserve quality.
    5. Optimizes net revenue (allocatable revenue - prorated freight cost).
    6. Respects truck fleet capacity constraints.
    """
    if not batches:
        return [], []

    remaining_demand = {
        _get(d, "id"): max(0.0, _num(_get(d, "demand_kg", 0.0)))
        for d in destinations
    }

    truck_capacities = (
        [{"id": str(_get(t, "id", f"TRK-{i+1}")), "remaining": max(0.0, _num(_get(t, "capacity", 0.0)))}
         for i, t in enumerate(trucks)]
        if trucks else None
    )

    # Sort batches by urgency (shortest shelf life first), deterministic tie-break by ID
    sorted_batches = sorted(
        batches,
        key=lambda b: (_num(_get(b, "remaining_shelf_life_days", 999.0)), int(_num(_get(b, "id", 0))))
    )
    min_shelf_life = min(_num(_get(b, "remaining_shelf_life_days", 999.0)) for b in batches)

    dispatches: List[Dict[str, Any]] = []
    unallocated: List[Dict[str, Any]] = []

    for b in sorted_batches:
        b_id = int(_num(_get(b, "id", 0)))
        commodity = str(_get(b, "commodity", "Produce"))
        shelf_life = _num(_get(b, "remaining_shelf_life_days", 1.0))
        qty_remaining = max(0.0, _num(_get(b, "quantity_kg", 0.0)))

        while qty_remaining > 0.001:
            total_truck_remaining = (
                sum(t["remaining"] for t in truck_capacities)
                if truck_capacities is not None else float("inf")
            )
            if total_truck_remaining <= 0.001:
                rec = {
                    "batch_id": b_id,
                    "commodity": commodity,
                    "destination_name": "None",
                    "quantity_kg": round(qty_remaining, 2),
                    "discount_pct": 0.0,
                    "revenue": 0.0,
                    "cost": 0.0,
                    "net_profit": 0.0,
                    "reason": "Fleet capacity exhausted — awaiting next logistics dispatch",
                    "is_spoiled": False,
                    "allocated": False,
                    "truck_id": None,
                    "viability_days": 0.0,
                }
                dispatches.append(rec)
                unallocated.append(rec)
                break

            candidates = []
            for d in destinations:
                d_id = _get(d, "id")
                rem_demand = remaining_demand.get(d_id, 0.0)
                if rem_demand <= 0.001:
                    continue

                dist_km = max(0.1, _num(_get(d, "distance_km", 100.0)))
                cost_per_km = _num(_get(d, "transport_cost_per_km", 10.0))
                market_price = _num(_get(d, "market_price_per_kg", 30.0))
                dest_name = str(_get(d, "name", "Market"))

                # Travel time at 500 km/day
                transport_time = dist_km / 500.0
                urgency_margin = shelf_life - transport_time

                # Feasibility constraint: prevent transit decay
                if urgency_margin < 0:
                    continue

                disc_pct = _discount_pct(urgency_margin)
                effective_price = market_price * (1.0 - disc_pct / 100.0)

                alloc_qty = min(qty_remaining, rem_demand, total_truck_remaining)
                if alloc_qty <= 0.001:
                    continue

                # Fair freight allocation per cargo share
                est_truck_cap = 400.0
                freight_cost = (dist_km * cost_per_km) * (alloc_qty / max(est_truck_cap, alloc_qty))
                revenue = alloc_qty * effective_price
                net_profit = revenue - freight_cost

                # Score heuristic: economic margin per kg with urgency steering
                unit_margin = net_profit / alloc_qty
                # Steer critically urgent produce (< 2.5d) toward closer transit routes
                if shelf_life <= 2.5:
                    unit_margin += (1.0 / (transport_time + 0.1)) * 4.0

                shelf_str = f"{shelf_life:g}d"
                if disc_pct > 0:
                    reason = f"Clearance discount ({disc_pct:.0f}%) — tight shelf life ({shelf_str}) vs transit ({transport_time:.1f}d)"
                elif shelf_life <= 2.0 or shelf_life == min_shelf_life:
                    reason = f"Priority dispatch — shortest shelf life ({shelf_str}), routed to nearby {dest_name}"
                else:
                    reason = f"Optimal match — max net margin to {dest_name} (₹{net_profit:,.0f} net, viability +{urgency_margin:.1f}d)"

                candidates.append({
                    "dest_id": d_id,
                    "dest_name": dest_name,
                    "score": unit_margin,
                    "alloc_qty": alloc_qty,
                    "disc_pct": disc_pct,
                    "revenue": revenue,
                    "freight_cost": freight_cost,
                    "net_profit": net_profit,
                    "reason": reason,
                    "urgency_margin": urgency_margin,
                })

            if not candidates:
                reason = (
                    f"Held at depot — shelf life ({shelf_life:g}d) insufficient for any open route"
                    if any(rem_d > 0.001 for rem_d in remaining_demand.values())
                    else "Held at depot — all destination demand fulfilled"
                )
                rec = {
                    "batch_id": b_id,
                    "commodity": commodity,
                    "destination_name": "None",
                    "quantity_kg": round(qty_remaining, 2),
                    "discount_pct": 0.0,
                    "revenue": 0.0,
                    "cost": 0.0,
                    "net_profit": 0.0,
                    "reason": reason,
                    "is_spoiled": False,
                    "allocated": False,
                    "truck_id": None,
                    "viability_days": 0.0,
                }
                dispatches.append(rec)
                unallocated.append(rec)
                break

            best = max(candidates, key=lambda c: c["score"])
            chosen_dest_id = best["dest_id"]
            alloc_qty = best["alloc_qty"]

            # Assign truck
            truck_id = None
            if truck_capacities is not None:
                for t in truck_capacities:
                    if t["remaining"] > 0.001:
                        truck_id = t["id"]
                        t["remaining"] = max(0.0, t["remaining"] - alloc_qty)
                        break

            remaining_demand[chosen_dest_id] = max(0.0, remaining_demand[chosen_dest_id] - alloc_qty)
            qty_remaining = max(0.0, qty_remaining - alloc_qty)

            dispatches.append({
                "batch_id": b_id,
                "commodity": commodity,
                "destination_name": best["dest_name"],
                "quantity_kg": round(alloc_qty, 2),
                "discount_pct": best["disc_pct"],
                "revenue": round(best["revenue"], 2),
                "cost": round(best["freight_cost"], 2),
                "net_profit": round(best["net_profit"], 2),
                "reason": best["reason"],
                "is_spoiled": False,
                "allocated": True,
                "truck_id": truck_id,
                "viability_days": round(best["urgency_margin"], 2),
            })

    return dispatches, unallocated


def run_baseline(
    batches: List[Any],
    destinations: List[Any],
    trucks: Optional[List[Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Naive FIFO Baseline Allocation:
    1. Allocates batches in sequential ID order without shelf life sorting.
    2. Allocates to destination in sequential ID order without transit distance check.
    3. Produce arriving after shelf life expires is marked spoiled (revenue = 0).
    4. No proactive clearance markdowns applied.
    """
    if not batches:
        return [], []

    remaining_demand = {
        _get(d, "id"): max(0.0, _num(_get(d, "demand_kg", 0.0)))
        for d in destinations
    }

    truck_capacities = (
        [{"id": str(_get(t, "id", f"TRK-{i+1}")), "remaining": max(0.0, _num(_get(t, "capacity", 0.0)))}
         for i, t in enumerate(trucks)]
        if trucks else None
    )

    ordered_batches = sorted(batches, key=lambda b: int(_num(_get(b, "id", 0))))
    ordered_destinations = sorted(destinations, key=lambda d: int(_num(_get(d, "id", 0))))

    dispatches: List[Dict[str, Any]] = []
    unallocated: List[Dict[str, Any]] = []

    for b in ordered_batches:
        b_id = int(_num(_get(b, "id", 0)))
        commodity = str(_get(b, "commodity", "Produce"))
        shelf_life = _num(_get(b, "remaining_shelf_life_days", 1.0))
        qty_remaining = max(0.0, _num(_get(b, "quantity_kg", 0.0)))

        while qty_remaining > 0.001:
            total_truck_remaining = (
                sum(t["remaining"] for t in truck_capacities)
                if truck_capacities is not None else float("inf")
            )
            if total_truck_remaining <= 0.001:
                rec = {
                    "batch_id": b_id,
                    "commodity": commodity,
                    "destination_name": "None",
                    "quantity_kg": round(qty_remaining, 2),
                    "discount_pct": 0.0,
                    "revenue": 0.0,
                    "cost": 0.0,
                    "net_profit": 0.0,
                    "reason": "unallocated: no remaining truck capacity",
                    "is_spoiled": False,
                    "allocated": False,
                    "truck_id": None,
                    "viability_days": 0.0,
                }
                dispatches.append(rec)
                unallocated.append(rec)
                break

            target_dest = None
            for d in ordered_destinations:
                d_id = _get(d, "id")
                if remaining_demand.get(d_id, 0.0) > 0.001:
                    target_dest = d
                    break

            if not target_dest:
                rec = {
                    "batch_id": b_id,
                    "commodity": commodity,
                    "destination_name": "None",
                    "quantity_kg": round(qty_remaining, 2),
                    "discount_pct": 0.0,
                    "revenue": 0.0,
                    "cost": 0.0,
                    "net_profit": 0.0,
                    "reason": "unallocated: no remaining destination demand",
                    "is_spoiled": False,
                    "allocated": False,
                    "truck_id": None,
                    "viability_days": 0.0,
                }
                dispatches.append(rec)
                unallocated.append(rec)
                break

            target_id = _get(target_dest, "id")
            dest_name = str(_get(target_dest, "name", "Market"))
            dist_km = max(0.1, _num(_get(target_dest, "distance_km", 100.0)))
            cost_per_km = _num(_get(target_dest, "transport_cost_per_km", 10.0))
            market_price = _num(_get(target_dest, "market_price_per_kg", 30.0))

            alloc_qty = min(qty_remaining, remaining_demand[target_id], total_truck_remaining)
            if alloc_qty <= 0.001:
                break

            truck_id = None
            if truck_capacities is not None:
                for t in truck_capacities:
                    if t["remaining"] > 0.001:
                        truck_id = t["id"]
                        t["remaining"] = max(0.0, t["remaining"] - alloc_qty)
                        break

            remaining_demand[target_id] = max(0.0, remaining_demand[target_id] - alloc_qty)
            qty_remaining = max(0.0, qty_remaining - alloc_qty)

            transport_time = dist_km / 500.0
            is_spoiled = shelf_life < transport_time
            est_truck_cap = 400.0
            freight_cost = (dist_km * cost_per_km) * (alloc_qty / max(est_truck_cap, alloc_qty))

            shelf_str = f"{shelf_life:g}d"
            if is_spoiled:
                revenue = 0.0
                reason = f"Spoiled in transit — shelf life ({shelf_str}) < transport time ({transport_time:.1f}d to {dest_name})"
            else:
                revenue = alloc_qty * market_price
                reason = f"Baseline FIFO dispatch to {dest_name} (viability +{shelf_life - transport_time:.1f}d)"

            net_profit = revenue - freight_cost

            dispatches.append({
                "batch_id": b_id,
                "commodity": commodity,
                "destination_name": dest_name,
                "quantity_kg": round(alloc_qty, 2),
                "discount_pct": 0.0,
                "revenue": round(revenue, 2),
                "cost": round(freight_cost, 2),
                "net_profit": round(net_profit, 2),
                "reason": reason,
                "is_spoiled": is_spoiled,
                "allocated": True,
                "truck_id": truck_id,
                "viability_days": round(shelf_life - transport_time, 2),
            })

    return dispatches, unallocated


def compare_plans(
    optimized_result: Union[Tuple[List[Dict[str, Any]], List[Dict[str, Any]]], List[Dict[str, Any]]],
    baseline_result: Union[Tuple[List[Dict[str, Any]], List[Dict[str, Any]]], List[Dict[str, Any]]],
    batches: Optional[List[Any]] = None,
    destinations: Optional[List[Any]] = None,
    trucks: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Computes comparative metrics between optimized and baseline dispatch plans.
    """
    opt_dispatches = optimized_result[0] if isinstance(optimized_result, tuple) else optimized_result
    base_dispatches = baseline_result[0] if isinstance(baseline_result, tuple) else baseline_result

    opt_revenue = sum(d["revenue"] for d in opt_dispatches if not d["is_spoiled"])
    base_revenue = sum(d["revenue"] for d in base_dispatches if not d["is_spoiled"])

    opt_net = sum(d["net_profit"] for d in opt_dispatches if not d["is_spoiled"])
    base_net = sum(d["net_profit"] for d in base_dispatches if not d["is_spoiled"])

    opt_spoilage = sum(d["quantity_kg"] for d in opt_dispatches if d["is_spoiled"])
    base_spoilage = sum(d["quantity_kg"] for d in base_dispatches if d["is_spoiled"])

    total_quantity = sum(_num(_get(b, "quantity_kg", 0.0)) for b in batches or [])
    if total_quantity <= 0:
        total_quantity = sum(d["quantity_kg"] for d in opt_dispatches)

    # Spoilage reduction percentage
    if base_spoilage > 0:
        spoilage_reduction_pct = max(0.0, ((base_spoilage - opt_spoilage) / base_spoilage) * 100.0)
    elif opt_spoilage == 0:
        spoilage_reduction_pct = 0.0
    else:
        spoilage_reduction_pct = 0.0

    # Revenue increase percentage
    if base_revenue > 0:
        revenue_increase_pct = ((opt_revenue - base_revenue) / base_revenue) * 100.0
    elif opt_revenue > 0:
        revenue_increase_pct = 100.0
    else:
        revenue_increase_pct = 0.0

    # Demand fulfillment
    total_demand = sum(_num(_get(d, "demand_kg", 0.0)) for d in destinations or [])
    opt_delivered = sum(d["quantity_kg"] for d in opt_dispatches if not d["is_spoiled"] and d.get("allocated", True))
    base_delivered = sum(d["quantity_kg"] for d in base_dispatches if not d["is_spoiled"] and d.get("allocated", True))

    opt_demand_fulfilled_pct = (opt_delivered / total_demand * 100.0) if total_demand > 0 else 0.0
    base_demand_fulfilled_pct = (base_delivered / total_demand * 100.0) if total_demand > 0 else 0.0

    # Truck capacity utilization
    total_truck_cap = sum(_num(_get(t, "capacity", 0.0)) for t in trucks or [])
    opt_truck_used_pct = (opt_delivered / total_truck_cap * 100.0) if total_truck_cap > 0 else 0.0

    return {
        "optimized_spoilage_kg": round(opt_spoilage, 2),
        "baseline_spoilage_kg": round(base_spoilage, 2),
        "spoilage_reduction_pct": round(spoilage_reduction_pct, 1),
        "optimized_revenue": round(opt_revenue, 2),
        "baseline_revenue": round(base_revenue, 2),
        "revenue_increase_pct": round(revenue_increase_pct, 1),
        "optimized_net_revenue": round(opt_net, 2),
        "baseline_net_revenue": round(base_net, 2),
        "total_batches": len(batches or []),
        "total_quantity_kg": round(total_quantity, 1),
        "optimized_demand_fulfilled_pct": round(opt_demand_fulfilled_pct, 1),
        "baseline_demand_fulfilled_pct": round(base_demand_fulfilled_pct, 1),
        "optimized_demand_fulfilled_kg": round(opt_delivered, 1),
        "truck_capacity_kg": round(total_truck_cap, 1),
        "truck_capacity_used_pct": round(opt_truck_used_pct, 1),
    }
