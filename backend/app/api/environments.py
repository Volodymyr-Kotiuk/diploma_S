from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import EnvironmentCreate, EnvironmentRead, EnvironmentUpdate

router = APIRouter(prefix="/environments", tags=["environments"])


@router.get("", response_model=list[EnvironmentRead])
def list_environments(db: Session = Depends(get_db)):
    return db.scalars(select(models.Environment).order_by(models.Environment.created_at.desc())).all()


@router.post("", response_model=EnvironmentRead)
def create_environment(payload: EnvironmentCreate, db: Session = Depends(get_db)):
    env = models.Environment(**payload.model_dump())
    db.add(env)
    db.commit()
    db.refresh(env)
    return env


@router.get("/{environment_id}", response_model=EnvironmentRead)
def get_environment(environment_id: int, db: Session = Depends(get_db)):
    env = db.get(models.Environment, environment_id)
    if not env:
        raise HTTPException(status_code=404, detail="Середовище не знайдено")
    return env


@router.put("/{environment_id}", response_model=EnvironmentRead)
def update_environment(environment_id: int, payload: EnvironmentUpdate, db: Session = Depends(get_db)):
    env = db.get(models.Environment, environment_id)
    if not env:
        raise HTTPException(status_code=404, detail="Середовище не знайдено")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(env, key, value)
    db.commit()
    db.refresh(env)
    return env


@router.delete("/{environment_id}")
def delete_environment(environment_id: int, db: Session = Depends(get_db)):
    env = db.get(models.Environment, environment_id)
    if not env:
        raise HTTPException(status_code=404, detail="Середовище не знайдено")
    db.delete(env)
    db.commit()
    return {"status": "deleted"}
