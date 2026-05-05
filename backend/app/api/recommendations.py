from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import RecommendationRead

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationRead])
def list_recommendations(db: Session = Depends(get_db), status: str | None = None):
    stmt = select(models.Recommendation).join(models.Node).where(models.Node.node_type != "local_host").order_by(desc(models.Recommendation.created_at), desc(models.Recommendation.id))
    if status:
        stmt = stmt.where(models.Recommendation.status == status)
    return db.scalars(stmt).all()


@router.get("/{recommendation_id}", response_model=RecommendationRead)
def get_recommendation(recommendation_id: int, db: Session = Depends(get_db)):
    rec = db.get(models.Recommendation, recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec


@router.post("/{recommendation_id}/accept", response_model=RecommendationRead)
def accept(recommendation_id: int, db: Session = Depends(get_db)):
    return _set_status(db, recommendation_id, "accepted")


@router.post("/{recommendation_id}/ignore", response_model=RecommendationRead)
def ignore(recommendation_id: int, db: Session = Depends(get_db)):
    return _set_status(db, recommendation_id, "ignored")


@router.post("/{recommendation_id}/resolve", response_model=RecommendationRead)
def resolve(recommendation_id: int, db: Session = Depends(get_db)):
    return _set_status(db, recommendation_id, "resolved")


def _set_status(db: Session, recommendation_id: int, status: str):
    rec = db.get(models.Recommendation, recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.status = status
    db.commit()
    db.refresh(rec)
    return rec
