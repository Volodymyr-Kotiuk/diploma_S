from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app import models
from app.database import get_db
from app.schemas import DashboardSummary, IncidentRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)) -> DashboardSummary:
    env_count = db.scalar(select(func.count(models.Environment.id))) or 0
    node_filter = models.Node.node_type != "local_host"
    node_count = db.scalar(select(func.count(models.Node.id)).where(node_filter)) or 0
    online_nodes = db.scalar(select(func.count(models.Node.id)).where(node_filter, models.Node.status.in_(["online", "healthy", "warning", "critical"]))) or 0
    offline_nodes = db.scalar(select(func.count(models.Node.id)).where(node_filter, models.Node.status == "offline")) or 0
    active_incidents = db.scalar(select(func.count(models.Incident.id)).where(models.Incident.status == "open")) or 0
    critical_recs = db.scalar(select(func.count(models.Recommendation.id)).where(models.Recommendation.priority == "critical", models.Recommendation.status == "new")) or 0
    latest_metrics = []
    nodes = db.scalars(select(models.Node).where(node_filter)).all()
    for node in nodes:
        metric = db.scalar(
            select(models.ResourceMetric)
            .where(models.ResourceMetric.node_id == node.id)
            .order_by(desc(models.ResourceMetric.timestamp), desc(models.ResourceMetric.id))
            .limit(1)
        )
        if metric:
            latest_metrics.append(metric)
    avg_cpu = round(sum(m.cpu_usage_percent or 0 for m in latest_metrics) / len(latest_metrics), 2) if latest_metrics else 0
    avg_ram = round(sum(m.ram_usage_percent or 0 for m in latest_metrics) / len(latest_metrics), 2) if latest_metrics else 0
    latest_diagnostics = []
    for node in nodes:
        diagnostic = db.scalar(
            select(models.Diagnostic)
            .where(models.Diagnostic.node_id == node.id)
            .order_by(desc(models.Diagnostic.created_at), desc(models.Diagnostic.id))
            .limit(1)
        )
        if diagnostic:
            latest_diagnostics.append(diagnostic)
    risk = round(sum(d.risk_score for d in latest_diagnostics) / len(latest_diagnostics), 2) if latest_diagnostics else 0
    return DashboardSummary(
        environments=env_count,
        nodes=node_count,
        online_nodes=online_nodes,
        offline_nodes=offline_nodes,
        active_incidents=active_incidents,
        critical_recommendations=critical_recs,
        average_cpu=avg_cpu,
        average_ram=avg_ram,
        overall_risk=risk,
    )


@router.get("/recent-incidents", response_model=list[IncidentRead])
def recent_incidents(db: Session = Depends(get_db), limit: int = 8):
    return db.scalars(select(models.Incident).order_by(desc(models.Incident.started_at)).limit(limit)).all()


@router.get("/risk-overview")
def risk_overview(db: Session = Depends(get_db)):
    nodes = db.scalars(select(models.Node).where(models.Node.node_type != "local_host")).all()
    rows = []
    for node in nodes:
        diagnostic = db.scalar(
            select(models.Diagnostic)
            .where(models.Diagnostic.node_id == node.id)
            .order_by(desc(models.Diagnostic.created_at), desc(models.Diagnostic.id))
            .limit(1)
        )
        rows.append({"node_id": node.id, "node": node.name, "status": node.status, "risk_score": diagnostic.risk_score if diagnostic else 0, "root_cause": diagnostic.root_cause if diagnostic else "No data"})
    return rows
