from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import CapacityForecastRead
from app.services.capacity_planner import run_capacity_planning

router = APIRouter(prefix="/capacity", tags=["capacity"])


@router.post("/run/{node_id}", response_model=list[CapacityForecastRead])
def run_capacity(node_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Node, node_id):
        raise HTTPException(status_code=404, detail="Вузол не знайдено")
    return run_capacity_planning(db, node_id)


@router.get("/{node_id}", response_model=list[CapacityForecastRead])
def get_capacity(node_id: int, db: Session = Depends(get_db)):
    forecasts = db.scalars(select(models.CapacityForecast).where(models.CapacityForecast.node_id == node_id).order_by(desc(models.CapacityForecast.created_at))).all()
    return forecasts or run_capacity_planning(db, node_id)
