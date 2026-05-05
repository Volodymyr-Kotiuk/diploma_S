from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import IncidentRead

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentRead])
def list_incidents(db: Session = Depends(get_db), status: str | None = None, node_id: int | None = None):
    stmt = select(models.Incident).join(models.Node).where(models.Node.node_type != "local_host").order_by(desc(models.Incident.started_at), desc(models.Incident.id))
    if status:
        stmt = stmt.where(models.Incident.status == status)
    if node_id:
        stmt = stmt.where(models.Incident.node_id == node_id)
    return db.scalars(stmt).all()


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.get(models.Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
