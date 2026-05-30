from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
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
        raise HTTPException(status_code=404, detail="Звіт не знайдено")
    return report


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(models.Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Звіт не знайдено")

    reports_dir = Path(get_settings().reports_dir).resolve()
    path = Path(report.file_path).resolve()
    try:
        path.relative_to(reports_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Недоступний шлях до звіту")

    if not path.exists() or path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF-файл звіту не знайдено")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=path.name,
        content_disposition_type="attachment",
    )
