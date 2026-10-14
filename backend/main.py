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
    from .optimizer import run_optimized, run_baseline, compare_plans
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
    from optimizer import run_optimized, run_baseline, compare_plans
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
    description="Perishable produce distribution decision-support dashboard API with dynamic random scenario generation",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS (allow all origins for development)
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
        "message": "FreshRoute Dynamic Decision-Support API is operational",
        "current_scenario": CURRENT_SCENARIO_META.get("scenario_name", "Default"),
    }


@app.get("/api/scenario", response_model=ScenarioResponse)
def get_scenario(
    seed: Optional[int] = Query(None, description="Optional integer seed for reproducible generation"),
    db: Session = Depends(get_db),
):
    """
    Generate a dynamic produce distribution scenario based on random archetypes.
    Guarantees exact reproducibility if an integer seed is provided.
    Also synchronizes the generated scenario to the SQLite database.
    """
    scenario = generate_scenario(seed=seed)

    # Synchronize database with the new scenario
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

    CURRENT_SCENARIO_META.clear()
    CURRENT_SCENARIO_META.update({
        "scenario_id": scenario["scenario_id"],
        "scenario_name": scenario["scenario_name"],
        "scenario_description": scenario["scenario_description"],
        "modifier_text": scenario["modifier_text"],
        "seed": scenario["seed"],
        "archetype": scenario["archetype"],
    })

    return scenario


@app.get("/api/batches", response_model=List[BatchResponse])
def get_batches(db: Session = Depends(get_db)):
    """Return all batches from the active scenario database."""
    batches = db.query(Batch).all()
    return batches


@app.get("/api/destinations", response_model=List[DestinationResponse])
def get_destinations(db: Session = Depends(get_db)):
    """Return all destinations from the active scenario database."""
    destinations = db.query(Destination).all()
    return destinations


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


@app.post("/api/optimize", response_model=OptimizationResponse)
def optimize(
    payload: Optional[Dict[str, Any]] = Body(None),
    db: Session = Depends(get_db),
):
    """
    Run heuristic optimization.
    Can operate on a dynamic scenario payload sent from the client or on the active scenario in SQLite.
    """
    batches = []
    destinations = []
    trucks = []
    scenario_meta = None

    if payload:
        if "scenario" in payload and isinstance(payload["scenario"], dict):
            sc = payload["scenario"]
            batches = sc.get("batches", [])
            destinations = sc.get("destinations", [])
            trucks = sc.get("trucks", [])
            scenario_meta = {
                "scenario_id": sc.get("scenario_id"),
                "scenario_name": sc.get("scenario_name"),
                "scenario_description": sc.get("scenario_description"),
                "modifier_text": sc.get("modifier_text"),
                "seed": sc.get("seed"),
            }
        else:
            batches = payload.get("batches", [])
            destinations = payload.get("destinations", [])
            trucks = payload.get("trucks", [])
            if "scenario_name" in payload:
                scenario_meta = {
                    "scenario_id": payload.get("scenario_id"),
                    "scenario_name": payload.get("scenario_name"),
                    "scenario_description": payload.get("scenario_description"),
                    "modifier_text": payload.get("modifier_text"),
                    "seed": payload.get("seed"),
                }

    if not batches or not destinations:
        # Fall back to database
        batches = db.query(Batch).all()
        destinations = db.query(Destination).all()

    if not batches or not destinations:
        raise HTTPException(
            status_code=400,
            detail="Insufficient batches or destinations to optimize. Generate a scenario first.",
        )

    opt_dispatches, opt_spoilage = run_optimized(batches, destinations, trucks=trucks)
    base_dispatches, base_spoilage = run_baseline(batches, destinations, trucks=trucks)

    summary = compare_plans(
        (opt_dispatches, opt_spoilage),
        (base_dispatches, base_spoilage),
        batches=batches,
    )

    return {
        "optimized_plan": opt_dispatches,
        "baseline_plan": base_dispatches,
        "summary": summary,
        "scenario": scenario_meta or CURRENT_SCENARIO_META,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
