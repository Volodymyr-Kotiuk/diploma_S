from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import DemoEnvironmentRequest, EnvironmentRead, NodeScenarioRunRequest, SimulationScenarioCreate, SimulationScenarioRead
from app.services.simulation_engine import create_demo_environment, create_scenario, run_node_scenario, run_scenario, stop_scenario

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/environments/demo", response_model=EnvironmentRead)
def demo_environment(payload: DemoEnvironmentRequest | None = None, db: Session = Depends(get_db)):
    name = payload.name if payload else "Демонстраційний віртуальний кластер"
    return create_demo_environment(db, name)


@router.post("/scenarios", response_model=SimulationScenarioRead)
def create_simulation_scenario(payload: SimulationScenarioCreate, db: Session = Depends(get_db)):
    return create_scenario(db, payload.model_dump())


@router.post("/scenarios/{scenario_id}/run", response_model=SimulationScenarioRead)
def run_simulation_scenario(scenario_id: int, db: Session = Depends(get_db)):
    return run_scenario(db, scenario_id)


@router.post("/nodes/{node_id}/run", response_model=SimulationScenarioRead)
def run_virtual_node_scenario(node_id: int, payload: NodeScenarioRunRequest, db: Session = Depends(get_db)):
    return run_node_scenario(db, node_id, payload.scenario_type, payload.duration_seconds, payload.intensity)


@router.post("/scenarios/{scenario_id}/stop", response_model=SimulationScenarioRead)
def stop_simulation_scenario(scenario_id: int, db: Session = Depends(get_db)):
    return stop_scenario(db, scenario_id)


@router.get("/scenarios", response_model=list[SimulationScenarioRead])
def list_scenarios(db: Session = Depends(get_db)):
    return db.scalars(select(models.SimulationScenario).order_by(desc(models.SimulationScenario.id))).all()


@router.get("/scenarios/{scenario_id}", response_model=SimulationScenarioRead)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scenario = db.get(models.SimulationScenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарій не знайдено")
    return scenario
