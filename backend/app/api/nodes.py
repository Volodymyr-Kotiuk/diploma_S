import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import CapacityForecastRead, DiagnosticRead, NodeCreate, NodeRead, NodeUpdate, RecommendationRead, ResourceMetricRead
from app.services.capacity_planner import run_capacity_planning
from app.services.metrics_service import list_metrics

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("", response_model=list[NodeRead])
def list_nodes(db: Session = Depends(get_db), environment_id: int | None = None, status: str | None = None, node_type: str | None = None, search: str | None = None):
    stmt = select(models.Node).where(models.Node.node_type != "local_host").order_by(models.Node.created_at.desc())
    if environment_id:
        stmt = stmt.where(models.Node.environment_id == environment_id)
    if status:
        stmt = stmt.where(models.Node.status == status)
    if node_type:
        if node_type == "virtual_node":
            stmt = stmt.where(or_(models.Node.node_type == "virtual_node", models.Node.node_type == "simulated_vm"))
        else:
            stmt = stmt.where(models.Node.node_type == node_type)
    if search:
        stmt = stmt.where(models.Node.name.ilike(f"%{search}%"))
    return db.scalars(stmt).all()


@router.post("", response_model=NodeRead)
def create_node(payload: NodeCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if data.get("node_type") == "simulated_vm":
        data["node_type"] = "virtual_node"
    data["role"] = data.get("role") or "unknown"
    node = models.Node(**data)
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


@router.get("/{node_id}", response_model=NodeRead)
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = db.get(models.Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.put("/{node_id}", response_model=NodeRead)
def update_node(node_id: int, payload: NodeUpdate, db: Session = Depends(get_db)):
    node = db.get(models.Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(node, key, value)
    db.commit()
    db.refresh(node)
    return node


@router.delete("/{node_id}")
def delete_node(node_id: int, db: Session = Depends(get_db)):
    node = db.get(models.Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    db.delete(node)
    db.commit()
    return {"status": "deleted"}


@router.get("/{node_id}/metrics", response_model=list[ResourceMetricRead])
def node_metrics(node_id: int, db: Session = Depends(get_db), limit: int = 120):
    return list_metrics(db, node_id, limit)


@router.get("/{node_id}/diagnostics", response_model=list[DiagnosticRead])
def node_diagnostics(node_id: int, db: Session = Depends(get_db)):
    return db.scalars(select(models.Diagnostic).where(models.Diagnostic.node_id == node_id).order_by(desc(models.Diagnostic.created_at), desc(models.Diagnostic.id))).all()


@router.get("/{node_id}/recommendations", response_model=list[RecommendationRead])
def node_recommendations(node_id: int, db: Session = Depends(get_db)):
    return db.scalars(select(models.Recommendation).where(models.Recommendation.node_id == node_id).order_by(desc(models.Recommendation.created_at), desc(models.Recommendation.id))).all()


@router.get("/{node_id}/capacity", response_model=list[CapacityForecastRead])
def node_capacity(node_id: int, db: Session = Depends(get_db)):
    forecasts = db.scalars(select(models.CapacityForecast).where(models.CapacityForecast.node_id == node_id).order_by(desc(models.CapacityForecast.created_at))).all()
    return forecasts or run_capacity_planning(db, node_id)


@router.get("/{node_id}/export/csv")
def export_node_metrics_csv(node_id: int, db: Session = Depends(get_db)):
    metrics = list_metrics(db, node_id, limit=5000)
    output = io.StringIO()
    writer = csv.writer(output)
    fields = ["timestamp", "cpu_usage_percent", "ram_usage_percent", "swap_usage_percent", "disk_usage_percent", "disk_read_rate", "disk_write_rate", "network_sent_rate", "network_recv_rate", "temperature_celsius"]
    writer.writerow(fields)
    for metric in metrics:
        writer.writerow([getattr(metric, field) for field in fields])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=node_{node_id}_metrics.csv"})


@router.get("/{node_id}/export/json")
def export_node_json(node_id: int, db: Session = Depends(get_db)):
    node = db.get(models.Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    payload = {
        "node": node,
        "metrics": list_metrics(db, node_id, limit=5000),
        "diagnostics": db.scalars(select(models.Diagnostic).where(models.Diagnostic.node_id == node_id)).all(),
        "recommendations": db.scalars(select(models.Recommendation).where(models.Recommendation.node_id == node_id)).all(),
    }
    return JSONResponse(content=jsonable_encoder(payload))
