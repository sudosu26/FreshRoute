from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

try:
    from .database import engine, Base, get_db, SessionLocal
    from .models import (
        Batch,
        Destination,
        BatchResponse,
        DestinationResponse,
        OptimizationResponse,
        SeedResponse,
        ScenarioResponse,
        OptimizeRequest,
    )
    from .seed import seed_database
    from .optimizer import run_optimized, run_baseline, compare_plans, plan_hash
    from .scenario_generator import generate_scenario
except ImportError:
    from database import engine, Base, get_db, SessionLocal
    from models import (
        Batch,
        Destination,
        BatchResponse,
        DestinationResponse,
        OptimizationResponse,
        SeedResponse,
        ScenarioResponse,
        OptimizeRequest,
    )
    from seed import seed_database
    from optimizer import run_optimized, run_baseline, compare_plans, plan_hash
    from scenario_generator import generate_scenario

CURRENT_SCENARIO_META: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup
    Base.metadata.create_all(bind=engine)
    # Seed the database if batches table is empty
    db = SessionLocal()
    try:
        if db.query(Batch).count() == 0:
            result = seed_database(db, seed=42)
            CURRENT_SCENARIO_META.update(result)
    finally:
        db.close()
    yield


app = FastAPI(
    title="FreshRoute API",
    description="High-performance perishable produce distribution decision-support API",
    version="2.1.0",
    lifespan=lifespan,
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "status": "operational",
        "service": "FreshRoute Decision Support Engine",
        "active_scenario": CURRENT_SCENARIO_META.get("scenario_name", "Default"),
        "active_seed": CURRENT_SCENARIO_META.get("seed"),
    }


@app.get("/api/scenario")
def get_scenario(
    seed: Optional[int] = Query(None, description="Optional integer seed for reproducible generation"),
    archetype: Optional[str] = Query(None, description="Optional archetype filter for demo"),
    include_optimization: bool = Query(False, description="Optionally include optimization plan in single round-trip"),
    db: Session = Depends(get_db),
):
    """
    Generate a dynamic produce distribution scenario based on random archetypes.
    Guarantees exact reproducibility if an integer seed is provided.
    Synchronizes SQLite using fast bulk operations.
    """
    scenario = generate_scenario(seed=seed, archetype_type=archetype)

    # Bulk synchronize SQLite database with the new scenario
    db.query(Batch).delete()
    db.query(Destination).delete()

    batch_objects = [
        Batch(
            commodity=b["commodity"],
            quantity_kg=b["quantity_kg"],
            remaining_shelf_life_days=b["remaining_shelf_life_days"],
            current_location=b["current_location"],
        )
        for b in scenario["batches"]
    ]
    dest_objects = [
        Destination(
            name=d["name"],
            demand_kg=d["demand_kg"],
            distance_km=d["distance_km"],
            transport_cost_per_km=d["transport_cost_per_km"],
            market_price_per_kg=d["market_price_per_kg"],
        )
        for d in scenario["destinations"]
    ]

    db.bulk_save_objects(batch_objects)
    db.bulk_save_objects(dest_objects)
    db.commit()

    CURRENT_SCENARIO_META.clear()
    CURRENT_SCENARIO_META.update({
        "scenario_id": scenario["scenario_id"],
        "scenario_name": scenario["scenario_name"],
        "scenario_description": scenario["scenario_description"],
        "modifier_text": scenario["modifier_text"],
        "seed": scenario["seed"],
        "archetype": scenario["archetype"],
    })

    if include_optimization:
        opt_plan, opt_unallocated = run_optimized(scenario["batches"], scenario["destinations"], scenario["trucks"])
        base_plan, _ = run_baseline(scenario["batches"], scenario["destinations"], scenario["trucks"])
        summary = compare_plans(
            opt_plan,
            base_plan,
            batches=scenario["batches"],
            destinations=scenario["destinations"],
            trucks=scenario["trucks"],
        )
        scenario["optimization"] = {
            "optimized_plan": opt_plan,
            "baseline_plan": base_plan,
            "summary": summary,
            "unallocated": opt_unallocated,
            "plan_hash": plan_hash(opt_plan, scenario["seed"]),
        }

    return scenario


@app.get("/api/batches", response_model=List[BatchResponse])
def get_batches(db: Session = Depends(get_db)):
    """Return all batches from the active scenario database."""
    return db.query(Batch).all()


@app.get("/api/destinations", response_model=List[DestinationResponse])
def get_destinations(db: Session = Depends(get_db)):
    """Return all destinations from the active scenario database."""
    return db.query(Destination).all()


@app.post("/api/seed", response_model=SeedResponse)
def seed(
    seed: Optional[int] = Query(None, description="Optional seed for the dynamic generator"),
    db: Session = Depends(get_db),
):
    """Clear existing data and generate a new dynamic scenario into the database."""
    result = seed_database(db, seed=seed)
    CURRENT_SCENARIO_META.clear()
    CURRENT_SCENARIO_META.update(result)
    return result


@app.post("/api/optimize")
def optimize(
    payload: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db),
):
    """
    Run heuristic optimization.
    Operates directly on the scenario payload sent from the client or on the active scenario in SQLite.
    Guarantees deterministic output for identical inputs.
    """
    scenario_data = None
    if payload and isinstance(payload.get("scenario"), dict):
        scenario_data = payload["scenario"]
    elif payload and payload.get("batches") and payload.get("destinations"):
        scenario_data = payload

    if scenario_data:
        batches = scenario_data.get("batches", [])
        destinations = scenario_data.get("destinations", [])
        trucks = scenario_data.get("trucks", [])
        chosen_seed = scenario_data.get("seed")
    else:
        batches = db.query(Batch).all()
        destinations = db.query(Destination).all()
        trucks = []
        chosen_seed = CURRENT_SCENARIO_META.get("seed")

    if not batches or not destinations:
        raise HTTPException(
            status_code=400,
            detail="Insufficient batches or destinations to optimize. Generate a scenario first.",
        )

    opt_dispatches, opt_unallocated = run_optimized(batches, destinations, trucks=trucks)
    base_dispatches, _ = run_baseline(batches, destinations, trucks=trucks)

    summary = compare_plans(
        opt_dispatches,
        base_dispatches,
        batches=batches,
        destinations=destinations,
        trucks=trucks,
    )

    response_scenario = scenario_data or CURRENT_SCENARIO_META
    allocation_hash = plan_hash(opt_dispatches, chosen_seed)

    return {
        "optimized_plan": opt_dispatches,
        "baseline_plan": base_dispatches,
        "summary": summary,
        "scenario": response_scenario,
        "unallocated": opt_unallocated,
        "plan_hash": allocation_hash,
        "seed": chosen_seed,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
