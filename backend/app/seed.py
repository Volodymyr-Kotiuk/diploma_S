from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.services.simulation_engine import create_demo_environment


def seed_demo_if_empty(db: Session) -> None:
    exists = db.scalar(select(models.Node.id).where(models.Node.node_type != "local_host").limit(1))
    if exists:
        return
    create_demo_environment(db, "Demo Virtual Cluster")
