from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float
from pydantic import BaseModel, ConfigDict, Field
try:
    from .database import Base
except ImportError:
    from database import Base

# SQLAlchemy Models

class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    commodity = Column(String, nullable=False)
    quantity_kg = Column(Float, nullable=False)
    remaining_shelf_life_days = Column(Float, nullable=False)
    current_location = Column(String, nullable=False)


class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    demand_kg = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=False)
    transport_cost_per_km = Column(Float, nullable=False)
    market_price_per_kg = Column(Float, nullable=False)


# Pydantic Schemas

class BatchBase(BaseModel):
    commodity: str
    quantity_kg: float
    remaining_shelf_life_days: float
    current_location: str


class BatchCreate(BatchBase):
    pass


class BatchResponse(BatchBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DestinationBase(BaseModel):
    name: str
    demand_kg: float
    distance_km: float
    transport_cost_per_km: float
    market_price_per_kg: float


class DestinationCreate(DestinationBase):
    pass


class DestinationResponse(DestinationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TruckModel(BaseModel):
    id: str
    truck_type: Optional[str] = "Reefer"
    capacity: float


class ScenarioBatch(BaseModel):
    id: int
    commodity: str
    quantity_kg: float
    remaining_shelf_life_days: float
    current_location: str


class ScenarioDestination(BaseModel):
    id: int
    name: str
    demand_kg: float
    distance_km: float
    transport_cost_per_km: float
    market_price_per_kg: float


class ScenarioResponse(BaseModel):
    scenario_id: str
    seed: int
    scenario_name: str
    scenario_description: str
    modifier_text: str
    archetype: str
    batches: List[ScenarioBatch]
    destinations: List[ScenarioDestination]
    trucks: List[TruckModel]
    stats: Optional[Dict[str, Any]] = None


class OptimizeRequest(BaseModel):
    scenario: Optional[ScenarioResponse] = None
    batches: Optional[List[ScenarioBatch]] = None
    destinations: Optional[List[ScenarioDestination]] = None
    trucks: Optional[List[TruckModel]] = None


class DispatchItem(BaseModel):
    batch_id: int
    commodity: str
    destination_name: str
    quantity_kg: float
    discount_pct: float
    revenue: float
    cost: float
    net_profit: float
    reason: str
    is_spoiled: bool
    impact: float = 0.0
    allocated: bool = True
    truck_id: Optional[str] = None
    viability_days: Optional[float] = None


class OptimizationResponse(BaseModel):
    optimized_plan: List[DispatchItem]
    baseline_plan: List[DispatchItem]
    unallocated: List[DispatchItem] = Field(default_factory=list)
    summary: Dict[str, Any]
    scenario: Optional[Dict[str, Any]] = None
    plan_hash: str
    seed: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)


class SeedResponse(BaseModel):
    status: str
    batches: int
    destinations: int
    scenario_id: Optional[str] = None
    scenario_name: Optional[str] = None
    scenario_description: Optional[str] = None
    modifier_text: Optional[str] = None
    seed: Optional[int] = None
