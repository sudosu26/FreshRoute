from typing import List, Dict, Any, Tuple, Union, Optional


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to access attributes on either dicts or SQLAlchemy objects safely."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _format_days(days: float) -> str:
    """Format day numbers cleanly (e.g. 1.0 -> '1', 1.5 -> '1.5')."""
    if isinstance(days, (int, float)):
        return f"{days:g}"
    return str(days)


def run_optimized(
    batches: List[Any],
    destinations: List[Any],
    trucks: Optional[List[Any]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Smart heuristic optimizer:
    1. Sort batches by remaining_shelf_life_days ascending (most urgent first)
    2. Track remaining demand per destination (start with dest.demand_kg)
    3. If trucks fleet capacity is provided, track remaining fleet capacity
    4. For each batch:
       a. For each destination with remaining_demand > 0:
          - transport_time_days = max(0.1, distance_km) / 500 (500 km/day)
          - If shelf_life < transport_time: INFEASIBLE, skip this dest
          - urgency_margin = shelf_life - transport_time
          - discount_pct = 0
          - If urgency_margin < 1.0: discount_pct = max(10, min(50, int((1.0 - urgency_margin) * 60)))
          - allocatable_qty = min(batch.quantity_remaining, dest.remaining_demand)
          - effective_price = market_price_per_kg * (1 - discount_pct / 100)
          - revenue = allocatable_qty * effective_price
          - cost = distance_km * transport_cost_per_km
          - net_profit = revenue - cost
          - score = net_profit
       b. Pick destination with highest score
       c. Create dispatch record, reduce remaining demand and batch quantity
       d. Generate reason string
       e. If NO feasible destination: mark as spoilage / shortfall
    5. Return list of dispatch dicts and spoilage list
    """
    if not batches:
        return [], []

    remaining_demand = {
        _get(d, "id"): float(_get(d, "demand_kg", 0.0)) for d in destinations
    }

    # Total truck capacity limit if specified
    remaining_truck_capacity: Optional[float] = None
    if trucks:
        remaining_truck_capacity = float(sum(float(_get(t, "capacity", 0.0)) for t in trucks))

    # Sort batches by shelf life ascending, secondary sort by id for determinism
    sorted_batches = sorted(
        batches,
        key=lambda b: (float(_get(b, "remaining_shelf_life_days", 999.0)), int(_get(b, "id", 0)))
    )

    min_shelf_life = (
        min(float(_get(b, "remaining_shelf_life_days", 999.0)) for b in batches)
        if batches else 0.0
    )

    dispatches: List[Dict[str, Any]] = []
    spoilage: List[Dict[str, Any]] = []

    for b in sorted_batches:
        b_id = int(_get(b, "id", 0))
        commodity = str(_get(b, "commodity", "Produce"))
        shelf_life = float(_get(b, "remaining_shelf_life_days", 1.0))
        quantity_remaining = float(_get(b, "quantity_kg", 0.0))

        while quantity_remaining > 0.001:
            # Check fleet capacity constraint
            if remaining_truck_capacity is not None and remaining_truck_capacity <= 0.001:
                spoilage_record = {
                    "batch_id": b_id,
                    "commodity": commodity,
                    "destination_name": "None",
                    "quantity_kg": round(quantity_remaining, 2),
                    "discount_pct": 0.0,
                    "revenue": 0.0,
                    "cost": 0.0,
                    "net_profit": 0.0,
                    "reason": "Fleet capacity shortfall — truck capacity exhausted for this batch",
                    "is_spoiled": True,
                }
                dispatches.append(spoilage_record)
                spoilage.append(spoilage_record)
                break

            candidates = []
            for d in destinations:
                d_id = int(_get(d, "id"))
                rem_demand = remaining_demand.get(d_id, 0.0)
                if rem_demand <= 0.001:
                    continue

                dist_km = float(_get(d, "distance_km", 100.0))
                cost_per_km = float(_get(d, "transport_cost_per_km", 10.0))
                market_price = float(_get(d, "market_price_per_kg", 30.0))
                dest_name = str(_get(d, "name", "Market"))

                transport_time = max(0.1, dist_km) / 500.0
                if shelf_life < transport_time:
                    # Infeasible: spoils during transit
                    continue

                urgency_margin = shelf_life - transport_time
                discount_pct = 0.0
                if urgency_margin < 1.0:
                    discount_pct = float(max(10, min(50, int((1.0 - max(0.0, urgency_margin)) * 60))))

                allocatable_qty = min(quantity_remaining, rem_demand)
                if remaining_truck_capacity is not None:
                    allocatable_qty = min(allocatable_qty, remaining_truck_capacity)

                if allocatable_qty <= 0.001:
                    continue

                effective_price = market_price * (1.0 - discount_pct / 100.0)
                revenue = allocatable_qty * effective_price
                cost = dist_km * cost_per_km
                net_profit = revenue - cost
                score = net_profit

                # Determine explainable reason string
                shelf_str = _format_days(shelf_life)
                if discount_pct > 0:
                    reason = f"Discount applied ({int(discount_pct)}%) — tight shelf life ({shelf_str}d) vs transport time ({transport_time:.1f}d)"
                elif shelf_life == min_shelf_life:
                    reason = f"Priority dispatch — shortest shelf life ({shelf_str}d), routed to high-value {dest_name}"
                else:
                    reason = f"Optimal match — best profit margin to {dest_name} (₹{net_profit:,.0f} net)"

                candidates.append({
                    "dest_id": d_id,
                    "dest_name": dest_name,
                    "score": score,
                    "discount_pct": discount_pct,
                    "allocatable_qty": allocatable_qty,
                    "revenue": revenue,
                    "cost": cost,
                    "net_profit": net_profit,
                    "reason": reason,
                })

            if not candidates:
                # No feasible destination found (or remaining demand/trucks 0)
                spoilage_record = {
                    "batch_id": b_id,
                    "commodity": commodity,
                    "destination_name": "None",
                    "quantity_kg": round(quantity_remaining, 2),
                    "discount_pct": 0.0,
                    "revenue": 0.0,
                    "cost": 0.0,
                    "net_profit": 0.0,
                    "reason": "No feasible route — shelf life too short or market demand saturated",
                    "is_spoiled": True,
                }
                dispatches.append(spoilage_record)
                spoilage.append(spoilage_record)
                break

            # Pick candidate with highest score
            best = max(candidates, key=lambda c: c["score"])
            chosen_dest_id = best["dest_id"]
            alloc_qty = best["allocatable_qty"]

            remaining_demand[chosen_dest_id] -= alloc_qty
            quantity_remaining -= alloc_qty
            if remaining_truck_capacity is not None:
                remaining_truck_capacity -= alloc_qty

            dispatch_record = {
                "batch_id": b_id,
                "commodity": commodity,
                "destination_name": best["dest_name"],
                "quantity_kg": round(alloc_qty, 2),
                "discount_pct": round(best["discount_pct"], 2),
                "revenue": round(best["revenue"], 2),
                "cost": round(best["cost"], 2),
                "net_profit": round(best["net_profit"], 2),
                "reason": best["reason"],
                "is_spoiled": False,
            }
            dispatches.append(dispatch_record)

    return dispatches, spoilage


def run_baseline(
    batches: List[Any],
    destinations: List[Any],
    trucks: Optional[List[Any]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Naive FIFO allocation:
    1. Process batches in order of ID (no shelf-life sorting)
    2. For each batch, iterate destinations in order of ID
    3. Allocate to first destination with remaining demand
    4. NO discounts applied ever
    5. Evaluate if transit time exceeds shelf life; mark as spoiled (revenue = 0)
    """
    if not batches:
        return [], []

    remaining_demand = {
        _get(d, "id"): float(_get(d, "demand_kg", 0.0)) for d in destinations
    }

    remaining_truck_capacity: Optional[float] = None
    if trucks:
        remaining_truck_capacity = float(sum(float(_get(t, "capacity", 0.0)) for t in trucks))

    ordered_batches = sorted(batches, key=lambda b: int(_get(b, "id", 0)))
    ordered_destinations = sorted(destinations, key=lambda d: int(_get(d, "id", 0)))

    dispatches: List[Dict[str, Any]] = []
    spoilage: List[Dict[str, Any]] = []

    for b in ordered_batches:
        b_id = int(_get(b, "id", 0))
        commodity = str(_get(b, "commodity", "Produce"))
        shelf_life = float(_get(b, "remaining_shelf_life_days", 1.0))
        quantity_remaining = float(_get(b, "quantity_kg", 0.0))

        while quantity_remaining > 0.001:
            if remaining_truck_capacity is not None and remaining_truck_capacity <= 0.001:
                spoilage_record = {
                    "batch_id": b_id,
                    "commodity": commodity,
                    "destination_name": "None",
                    "quantity_kg": round(quantity_remaining, 2),
                    "discount_pct": 0.0,
                    "revenue": 0.0,
                    "cost": 0.0,
                    "net_profit": 0.0,
                    "reason": "Fleet capacity shortfall — truck capacity exhausted in FIFO queue",
                    "is_spoiled": True,
                }
                dispatches.append(spoilage_record)
                spoilage.append(spoilage_record)
                break

            target_dest = None
            for d in ordered_destinations:
                d_id = int(_get(d, "id"))
                if remaining_demand.get(d_id, 0.0) > 0.001:
                    target_dest = d
                    break

            if not target_dest:
                spoilage_record = {
                    "batch_id": b_id,
                    "commodity": commodity,
                    "destination_name": "None",
                    "quantity_kg": round(quantity_remaining, 2),
                    "discount_pct": 0.0,
                    "revenue": 0.0,
                    "cost": 0.0,
                    "net_profit": 0.0,
                    "reason": "No demand remaining at any destination",
                    "is_spoiled": True,
                }
                dispatches.append(spoilage_record)
                spoilage.append(spoilage_record)
                break

            target_id = int(_get(target_dest, "id"))
            dest_name = str(_get(target_dest, "name", "Market"))
            dist_km = float(_get(target_dest, "distance_km", 100.0))
            cost_per_km = float(_get(target_dest, "transport_cost_per_km", 10.0))
            market_price = float(_get(target_dest, "market_price_per_kg", 30.0))

            alloc_qty = min(quantity_remaining, remaining_demand[target_id])
            if remaining_truck_capacity is not None:
                alloc_qty = min(alloc_qty, remaining_truck_capacity)

            if alloc_qty <= 0.001:
                break

            remaining_demand[target_id] -= alloc_qty
            quantity_remaining -= alloc_qty
            if remaining_truck_capacity is not None:
                remaining_truck_capacity -= alloc_qty

            transport_time = max(0.1, dist_km) / 500.0
            is_spoiled = shelf_life < transport_time
            cost = dist_km * cost_per_km

            shelf_str = _format_days(shelf_life)
            if is_spoiled:
                revenue = 0.0
                reason = f"Spoiled in transit — shelf life ({shelf_str}d) < transport time ({transport_time:.1f}d)"
            else:
                revenue = alloc_qty * market_price
                reason = f"Baseline FIFO match to {dest_name}"

            net_profit = revenue - cost

            dispatch_record = {
                "batch_id": b_id,
                "commodity": commodity,
                "destination_name": dest_name,
                "quantity_kg": round(alloc_qty, 2),
                "discount_pct": 0.0,
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "net_profit": round(net_profit, 2),
                "reason": reason,
                "is_spoiled": is_spoiled,
            }
            dispatches.append(dispatch_record)
            if is_spoiled:
                spoilage.append(dispatch_record)

    return dispatches, spoilage


def compare_plans(
    optimized_result: Union[Tuple[List[Dict[str, Any]], List[Dict[str, Any]]], List[Dict[str, Any]]],
    baseline_result: Union[Tuple[List[Dict[str, Any]], List[Dict[str, Any]]], List[Dict[str, Any]]],
    batches: Union[List[Any], None] = None
) -> Dict[str, Any]:
    """
    Computes comparative metrics between optimized and baseline dispatch plans with zero-division guards.
    """
    if isinstance(optimized_result, tuple):
        opt_dispatches, opt_spoilage = optimized_result
    else:
        opt_dispatches = optimized_result

    if isinstance(baseline_result, tuple):
        base_dispatches, base_spoilage = baseline_result
    else:
        base_dispatches = baseline_result

    optimized_revenue = sum(d["revenue"] for d in opt_dispatches if not d["is_spoiled"])
    baseline_revenue = sum(d["revenue"] for d in base_dispatches if not d["is_spoiled"])

    optimized_spoilage_kg = sum(d["quantity_kg"] for d in opt_dispatches if d["is_spoiled"])
    baseline_spoilage_kg = sum(d["quantity_kg"] for d in base_dispatches if d["is_spoiled"])

    # Robust Spoilage Reduction Calculation
    if baseline_spoilage_kg > 0:
        spoilage_reduction_pct = (
            (baseline_spoilage_kg - optimized_spoilage_kg) / baseline_spoilage_kg
        ) * 100.0
    elif optimized_spoilage_kg == 0:
        spoilage_reduction_pct = 0.0
    else:
        spoilage_reduction_pct = 0.0

    # Robust Revenue Increase Calculation
    if baseline_revenue > 0:
        revenue_increase_pct = (
            (optimized_revenue - baseline_revenue) / baseline_revenue
        ) * 100.0
    elif optimized_revenue > 0:
        revenue_increase_pct = 100.0
    else:
        revenue_increase_pct = 0.0

    if batches is not None and len(batches) > 0:
        total_batches = len(batches)
        total_quantity_kg = sum(float(_get(b, "quantity_kg", 0.0)) for b in batches)
    else:
        unique_batch_ids = set(d["batch_id"] for d in opt_dispatches)
        total_batches = len(unique_batch_ids)
        total_quantity_kg = sum(d["quantity_kg"] for d in opt_dispatches)

    return {
        "optimized_spoilage_kg": round(optimized_spoilage_kg, 2),
        "baseline_spoilage_kg": round(baseline_spoilage_kg, 2),
        "spoilage_reduction_pct": round(max(0.0, spoilage_reduction_pct), 2),
        "optimized_revenue": round(optimized_revenue, 2),
        "baseline_revenue": round(baseline_revenue, 2),
        "revenue_increase_pct": round(revenue_increase_pct, 2),
        "total_batches": total_batches,
        "total_quantity_kg": round(total_quantity_kg, 2),
    }
