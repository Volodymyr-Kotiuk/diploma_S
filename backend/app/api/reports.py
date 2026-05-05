from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import ReportRead
from app.services.report_generator import generate_environment_report, generate_node_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/environment/{environment_id}", response_model=ReportRead)
def create_environment_report(environment_id: int, db: Session = Depends(get_db)):
    return generate_environment_report(db, environment_id)


@router.post("/node/{node_id}", response_model=ReportRead)
def create_node_report(node_id: int, db: Session = Depends(get_db)):
    return generate_node_report(db, node_id)


@router.get("", response_model=list[ReportRead])
def list_reports(db: Session = Depends(get_db)):
    return db.scalars(select(models.Report).order_by(desc(models.Report.created_at), desc(models.Report.id))).all()


@router.get("/{report_id}", response_model=ReportRead)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(models.Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
