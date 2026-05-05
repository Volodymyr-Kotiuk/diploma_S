from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import DiagnosticRead
from app.services.diagnosis_engine import run_diagnostics_for_node

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


@router.post("/run/{node_id}", response_model=DiagnosticRead)
def run_diagnostics(node_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Node, node_id):
        raise HTTPException(status_code=404, detail="Node not found")
    return run_diagnostics_for_node(db, node_id)


@router.get("", response_model=list[DiagnosticRead])
def list_diagnostics(db: Session = Depends(get_db)):
    return db.scalars(select(models.Diagnostic).order_by(desc(models.Diagnostic.created_at), desc(models.Diagnostic.id))).all()


@router.get("/{diagnostic_id}", response_model=DiagnosticRead)
def get_diagnostic(diagnostic_id: int, db: Session = Depends(get_db)):
    diagnostic = db.get(models.Diagnostic, diagnostic_id)
    if not diagnostic:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    return diagnostic


@router.post("/{diagnostic_id}/acknowledge", response_model=DiagnosticRead)
def acknowledge(diagnostic_id: int, db: Session = Depends(get_db)):
    return _set_status(db, diagnostic_id, "acknowledged")


@router.post("/{diagnostic_id}/resolve", response_model=DiagnosticRead)
def resolve(diagnostic_id: int, db: Session = Depends(get_db)):
    return _set_status(db, diagnostic_id, "resolved")


def _set_status(db: Session, diagnostic_id: int, status: str):
    diagnostic = db.get(models.Diagnostic, diagnostic_id)
    if not diagnostic:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    diagnostic.status = status
    db.commit()
    db.refresh(diagnostic)
    return diagnostic
