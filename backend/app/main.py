from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, capacity, dashboard, diagnostics, environments, incidents, metrics, nodes, recommendations, reports, simulation
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.seed import seed_demo_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_demo_if_empty(db)
    finally:
        db.close()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{settings.api_prefix}/health")
def health():
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


for router in [
    dashboard.router,
    environments.router,
    nodes.router,
    agents.router,
    metrics.router,
    diagnostics.router,
    incidents.router,
    recommendations.router,
    simulation.router,
    capacity.router,
    reports.router,
]:
    app.include_router(router, prefix=settings.api_prefix)
