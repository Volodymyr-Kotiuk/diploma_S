from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import AgentHeartbeatRequest, AgentMetricsRequest, AgentRegisterRequest, AgentTokenResponse, NodeRead, ResourceMetricRead
from app.services.agent_service import create_token_for_node, heartbeat, install_command, normalize_server_url, register_agent_node, validate_agent_token
from app.services.metrics_service import create_metric

router = APIRouter(prefix="/agents", tags=["agents"])


def _server_url(request: Request) -> str:
    configured_url = get_settings().public_backend_url.strip()
    if configured_url:
        return normalize_server_url(configured_url)

    forwarded_host = request.headers.get("x-forwarded-host")
    host = forwarded_host or request.headers.get("host")
    if host:
        proto = request.headers.get("x-forwarded-proto") or request.url.scheme
        return normalize_server_url(f"{proto.split(',')[0].strip()}://{host.split(',')[0].strip()}")

    return normalize_server_url(str(request.base_url))


def _agent_file_path() -> Path:
    candidates = [
        Path(__file__).resolve().parents[3] / "agent" / "agent.py",
        Path(__file__).resolve().parents[2] / "agent.py",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise HTTPException(status_code=404, detail="agent.py не знайдено на сервері")


@router.post("/register", response_model=AgentTokenResponse)
def register(payload: AgentRegisterRequest, request: Request, db: Session = Depends(get_db)):
    return register_agent_node(db, payload.model_dump(), _server_url(request))


@router.post("/{node_id}/token", response_model=AgentTokenResponse)
def create_token(node_id: int, request: Request, db: Session = Depends(get_db)):
    return create_token_for_node(db, node_id, _server_url(request))


@router.post("/heartbeat", response_model=NodeRead)
def agent_heartbeat(payload: AgentHeartbeatRequest, db: Session = Depends(get_db)):
    return heartbeat(db, payload.model_dump())


@router.post("/metrics", response_model=ResourceMetricRead)
def agent_metrics(payload: AgentMetricsRequest, db: Session = Depends(get_db)):
    validate_agent_token(db, payload.node_id, payload.token)
    data = payload.model_dump(exclude={"token"})
    return create_metric(db, data, run_analysis=True)


@router.get("/download")
def download_agent():
    return FileResponse(
        path=str(_agent_file_path()),
        media_type="text/x-python",
        filename="agent.py",
        content_disposition_type="attachment",
    )


@router.get("/install-command/{node_id}")
def get_install_command(node_id: int, request: Request):
    return {"node_id": node_id, "install_command": install_command(_server_url(request), node_id)}
