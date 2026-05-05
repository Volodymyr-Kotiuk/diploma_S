from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.utils.time_utils import utc_now


def create_incident_from_diagnostic(db: Session, diagnostic: models.Diagnostic) -> models.Incident | None:
    if diagnostic.diagnosis_type == "healthy":
        return None
    existing = db.scalar(
        select(models.Incident)
        .where(
            models.Incident.node_id == diagnostic.node_id,
            models.Incident.incident_type == diagnostic.diagnosis_type,
            models.Incident.status == "open",
        )
        .order_by(desc(models.Incident.started_at))
        .limit(1)
    )
    if existing:
        existing.severity = diagnostic.severity
        existing.description = diagnostic.explanation
        existing.root_cause = diagnostic.root_cause
        existing.evidence_json = diagnostic.evidence_json
        db.commit()
        db.refresh(existing)
        return existing

    incident = models.Incident(
        node_id=diagnostic.node_id,
        diagnostic_id=diagnostic.id,
        title=f"{diagnostic.root_cause}",
        description=diagnostic.explanation,
        incident_type=diagnostic.diagnosis_type,
        severity=diagnostic.severity,
        started_at=utc_now(),
        status="open",
        root_cause=diagnostic.root_cause,
        evidence_json=diagnostic.evidence_json,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def resolve_open_incidents_for_node(db: Session, node_id: int) -> int:
    rows = db.scalars(
        select(models.Incident).where(models.Incident.node_id == node_id, models.Incident.status == "open")
    ).all()
    for row in rows:
        row.status = "resolved"
        row.ended_at = utc_now()
    db.commit()
    return len(rows)
