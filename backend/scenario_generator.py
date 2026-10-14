import random
from typing import Optional, Dict, Any, List

COMMODITY_SPECS = {
    "Tomato": {"shelf_life": (3, 6), "base_price": 38.0},
    "Spinach": {"shelf_life": (2, 3), "base_price": 32.0},
    "Mango": {"shelf_life": (4, 8), "base_price": 85.0},
    "Banana": {"shelf_life": (4, 7), "base_price": 42.0},
    "Onion": {"shelf_life": (9, 14), "base_price": 30.0},
    "Potato": {"shelf_life": (10, 14), "base_price": 25.0},
    "Grapes": {"shelf_life": (3, 7), "base_price": 75.0},
    "Cauliflower": {"shelf_life": (4, 7), "base_price": 35.0},
}

LOCATIONS = [
    "Warehouse Alpha",
    "Farm Hub North",
    "Central Cold Storage",
    "Green Valley Depot",
    "Sunrise Orchards",
    "Kisan Logistics Hub",
]

DESTINATION_NAMES = [
    "Mumbai Central",
    "Delhi NCR",
    "Pune Metro",
    "Bangalore Hub",
    "Chennai Port",
    "Hyderabad City",
    "Kolkata Depot",
    "Ahmedabad Market",
    "Jaipur Center",
    "Lucknow Terminal",
]

ARCHETYPES = [
    {
        "name": "Normal Week",
        "description": "Typical operational conditions across distribution corridors with balanced supply and steady demand.",
        "modifier_text": "Standard baseline parameters without disruptions.",
        "type": "NORMAL",
    },
    {
        "name": "Peak Harvest Glut",
        "description": "Bumper harvest creates massive produce surplus across farms, flooding logistics and depressing market prices.",
        "modifier_text": "Batch quantities ×1.6, market prices ×0.7",
        "type": "HARVEST_GLUT",
    },
    {
        "name": "Festival Demand Surge",
        "description": "High festive seasonal demand in urban centers pulls inventory faster at premium market pricing.",
        "modifier_text": "Destination demand ×1.7, market prices ×1.3",
        "type": "FESTIVAL_SURGE",
    },
    {
        "name": "Fuel Price Spike",
        "description": "Sudden crude oil inflation surges diesel freight rates, severely penalizing long-haul transits.",
        "modifier_text": "Transport cost per km ×2.0",
        "type": "FUEL_SPIKE",
    },
    {
        "name": "Monsoon Road Delays",
        "description": "Heavy rain and waterlogged highways force detours, increasing travel distances and transit decay risk.",
        "modifier_text": "Route distances ×1.4 (transport times increased)",
        "type": "MONSOON_DELAYS",
    },
    {
        "name": "Cold Chain Failure",
        "description": "Refrigeration breakdown at transit storage accelerates ripening and cuts shelf life dramatically on affected batches.",
        "modifier_text": "40% of batches suffer 50% shelf-life cut",
        "type": "COLD_CHAIN_FAIL",
    },
]


def generate_scenario(
    seed: Optional[int] = None,
    archetype_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates a realistic, dynamic produce distribution scenario based on random archetypes.
    Guarantees exact reproducibility when an integer seed is provided.
    Optionally accepts a specific archetype_type for targeted demo scenarios.
    """
    if seed is None:
        seed = random.randint(10000, 99999)

    rng = random.Random(seed)
    scenario_id = f"SCN-{rng.randint(1000, 9999)}"

    # Select Archetype
    if archetype_type:
        matched = next((a for a in ARCHETYPES if a["type"] == archetype_type or a["name"].lower() == archetype_type.lower()), None)
        archetype = matched if matched else rng.choice(ARCHETYPES)
    else:
        archetype = rng.choice(ARCHETYPES)

    scenario_name = archetype["name"]
    scenario_description = archetype["description"]
    modifier_text = archetype["modifier_text"]
    selected_type = archetype["type"]

    # 1. Generate Trucks (2–4 trucks, capacity 150–500 units)
    num_trucks = rng.randint(2, 4)
    trucks = []
    for i in range(num_trucks):
        trucks.append({
            "id": f"TRK-{i + 1}",
            "truck_type": f"Reefer-{i + 1}",
            "capacity": float(rng.randint(150, 500)),
        })

    # 2. Generate Destinations (4–7 destinations)
    num_destinations = rng.randint(4, 7)
    selected_dest_names = rng.sample(DESTINATION_NAMES, num_destinations)
    destinations = []

    for i, name in enumerate(selected_dest_names):
        demand = float(rng.randint(100, 1200))
        distance = float(rng.randint(20, 800))
        transport_cost = round(rng.uniform(8.0, 25.0), 2)
        market_price = round(rng.uniform(35.0, 65.0) * rng.uniform(0.7, 1.3), 2)

        destinations.append({
            "id": i + 1,
            "name": name,
            "demand_kg": demand,
            "distance_km": distance,
            "transport_cost_per_km": transport_cost,
            "market_price_per_kg": market_price,
        })

    # 3. Generate Batches (6–12 batches)
    num_batches = rng.randint(6, 12)
    commodity_keys = list(COMMODITY_SPECS.keys())
    batches = []

    for i in range(num_batches):
        commodity = rng.choice(commodity_keys)
        spec = COMMODITY_SPECS[commodity]
        quantity = float(rng.randint(50, 600))
        min_shelf, max_shelf = spec["shelf_life"]
        shelf_life = round(rng.uniform(min_shelf, max_shelf), 1)
        location = rng.choice(LOCATIONS)

        batches.append({
            "id": i + 1,
            "commodity": commodity,
            "quantity_kg": quantity,
            "remaining_shelf_life_days": shelf_life,
            "current_location": location,
        })

    # 4. Apply Archetype Modifiers
    if selected_type == "HARVEST_GLUT":
        for b in batches:
            b["quantity_kg"] = round(b["quantity_kg"] * 1.6, 1)
        for d in destinations:
            d["market_price_per_kg"] = round(max(5.0, d["market_price_per_kg"] * 0.7), 2)

    elif selected_type == "FESTIVAL_SURGE":
        for d in destinations:
            d["demand_kg"] = round(d["demand_kg"] * 1.7, 1)
            d["market_price_per_kg"] = round(d["market_price_per_kg"] * 1.3, 2)

    elif selected_type == "FUEL_SPIKE":
        for d in destinations:
            d["transport_cost_per_km"] = round(d["transport_cost_per_km"] * 2.0, 2)

    elif selected_type == "MONSOON_DELAYS":
        for d in destinations:
            d["distance_km"] = round(d["distance_km"] * 1.4, 1)

    elif selected_type == "COLD_CHAIN_FAIL":
        k = max(1, int(len(batches) * 0.4))
        affected_indices = rng.sample(range(len(batches)), k)
        for idx in affected_indices:
            batches[idx]["remaining_shelf_life_days"] = max(
                0.5, round(batches[idx]["remaining_shelf_life_days"] * 0.5, 1)
            )

    # 5. Guarantee at least one batch with <= 2.0 days shelf life
    min_shelf = min(b["remaining_shelf_life_days"] for b in batches)
    if min_shelf > 2.0:
        fastest_expiring = min(batches, key=lambda b: b["remaining_shelf_life_days"])
        fastest_expiring["remaining_shelf_life_days"] = round(rng.uniform(1.0, 2.0), 1)

    total_truck_capacity = sum(t["capacity"] for t in trucks)
    total_batch_quantity = sum(b["quantity_kg"] for b in batches)
    total_dest_demand = sum(d["demand_kg"] for d in destinations)

    return {
        "scenario_id": scenario_id,
        "seed": seed,
        "scenario_name": scenario_name,
        "scenario_description": scenario_description,
        "modifier_text": modifier_text,
        "archetype": selected_type,
        "batches": batches,
        "destinations": destinations,
        "trucks": trucks,
        "stats": {
            "total_batches": len(batches),
            "total_destinations": len(destinations),
            "total_trucks": len(trucks),
            "total_batch_quantity_kg": round(total_batch_quantity, 1),
            "total_dest_demand_kg": round(total_dest_demand, 1),
            "total_truck_capacity_kg": round(total_truck_capacity, 1),
        },
    }
