from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.utils.risk_utils import status_from_risk


def latest_metric(db: Session, node_id: int) -> models.ResourceMetric | None:
    return db.scalar(
        select(models.ResourceMetric)
        .where(models.ResourceMetric.node_id == node_id)
        .order_by(desc(models.ResourceMetric.timestamp), desc(models.ResourceMetric.id))
        .limit(1)
    )


def list_metrics(db: Session, node_id: int, limit: int = 120) -> list[models.ResourceMetric]:
    rows = db.scalars(
        select(models.ResourceMetric)
        .where(models.ResourceMetric.node_id == node_id)
        .order_by(desc(models.ResourceMetric.timestamp), desc(models.ResourceMetric.id))
        .limit(limit)
    ).all()
    return list(reversed(rows))


def create_metric(db: Session, payload: dict, run_analysis: bool = True) -> models.ResourceMetric:
    data = dict(payload)
    if not data.get("timestamp"):
        data.pop("timestamp", None)
    node_id = data["node_id"]
    prev = latest_metric(db, node_id)
    metric = models.ResourceMetric(**data)
    _fill_rates(metric, prev)
    db.add(metric)
    node = db.get(models.Node, node_id)
    if node:
        node.status = _status_for_metric(metric)
        node.last_heartbeat_at = datetime.utcnow()
    db.commit()
    db.refresh(metric)

    if run_analysis:
        from app.services.diagnosis_engine import run_diagnostics_for_node

        run_diagnostics_for_node(db, node_id)
    return metric


def _fill_rates(metric: models.ResourceMetric, prev: models.ResourceMetric | None) -> None:
    if not prev:
        metric.disk_read_rate = metric.disk_read_rate or 0
        metric.disk_write_rate = metric.disk_write_rate or 0
        metric.network_sent_rate = metric.network_sent_rate or 0
        metric.network_recv_rate = metric.network_recv_rate or 0
        return
    now = metric.timestamp or datetime.utcnow()
    prev_ts = prev.timestamp or now
    elapsed = max((now - prev_ts).total_seconds(), 1)
    pairs = [
        ("disk_read_rate", "disk_read_bytes"),
        ("disk_write_rate", "disk_write_bytes"),
        ("network_sent_rate", "network_bytes_sent"),
        ("network_recv_rate", "network_bytes_recv"),
    ]
    for rate_attr, total_attr in pairs:
        if getattr(metric, rate_attr) is None:
            current = getattr(metric, total_attr) or 0
            previous = getattr(prev, total_attr) or 0
            setattr(metric, rate_attr, max((current - previous) / elapsed, 0))


def _status_for_metric(metric: models.ResourceMetric) -> str:
    risk = max(
        metric.cpu_usage_percent or 0,
        metric.ram_usage_percent or 0,
        metric.swap_usage_percent or 0,
        metric.disk_usage_percent or 0,
        90 if (metric.temperature_celsius or 0) > 85 else 0,
    )
    return status_from_risk(risk)
