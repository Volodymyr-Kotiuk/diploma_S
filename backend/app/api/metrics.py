from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import AgentHeartbeatRequest, AgentMetricsRequest, NodeRead, ResourceMetricRead
from app.services.agent_service import heartbeat, validate_agent_token
from app.services.metrics_service import create_metric

router = APIRouter(tags=["node-ingest"])


@router.post("/metrics", response_model=ResourceMetricRead)
def ingest_agent_metric(payload: AgentMetricsRequest, db: Session = Depends(get_db)):
    node = db.get(models.Node, payload.node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Вузол не знайдено")
    validate_agent_token(db, payload.node_id, payload.token)
    data = payload.model_dump(exclude={"token"})
    return create_metric(db, data, run_analysis=True)


@router.post("/heartbeat", response_model=NodeRead)
def ingest_agent_heartbeat(payload: AgentHeartbeatRequest, db: Session = Depends(get_db)):
    return heartbeat(db, payload.model_dump())
