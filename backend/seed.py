from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

try:
    from .models import Batch, Destination
    from .scenario_generator import generate_scenario
except ImportError:
    from models import Batch, Destination
    from scenario_generator import generate_scenario


def seed_database(db: Session, seed: Optional[int] = 42) -> Dict[str, Any]:
    """
    Clears existing data and populates the database with a dynamically generated scenario.
    Removes all hardcoded batch and destination lists from the codebase.
    """
    scenario = generate_scenario(seed=seed)

    db.query(Batch).delete()
    db.query(Destination).delete()
    db.commit()

    for batch_data in scenario["batches"]:
        batch = Batch(
            commodity=batch_data["commodity"],
            quantity_kg=batch_data["quantity_kg"],
            remaining_shelf_life_days=batch_data["remaining_shelf_life_days"],
            current_location=batch_data["current_location"],
        )
        db.add(batch)

    for dest_data in scenario["destinations"]:
        dest = Destination(
            name=dest_data["name"],
            demand_kg=dest_data["demand_kg"],
            distance_km=dest_data["distance_km"],
            transport_cost_per_km=dest_data["transport_cost_per_km"],
            market_price_per_kg=dest_data["market_price_per_kg"],
        )
        db.add(dest)

    db.commit()

    batch_count = db.query(Batch).count()
    dest_count = db.query(Destination).count()

    return {
        "status": "ok",
        "batches": batch_count,
        "destinations": dest_count,
        "scenario_id": scenario["scenario_id"],
        "scenario_name": scenario["scenario_name"],
        "scenario_description": scenario["scenario_description"],
        "modifier_text": scenario["modifier_text"],
        "seed": scenario["seed"],
    }
