from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.utils.token_utils import generate_token, hash_token, preview_token


def normalize_server_url(server_url: str) -> str:
    server = server_url.strip().rstrip("/")
    if server.endswith("/api"):
        server = server.removesuffix("/api").rstrip("/")
    return server


def create_token_for_node(db: Session, node_id: int, server_url: str = "http://localhost:8000") -> dict:
    node = db.get(models.Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Вузол не знайдено")
    token = generate_token()
    record = models.AgentToken(node_id=node_id, token_hash=hash_token(token), token_preview=preview_token(token), is_active=True)
    db.add(record)
    db.commit()
    db.refresh(record)
    command = install_command(server_url, node_id, token)
    return {"node": node, "token": token, "token_preview": record.token_preview, "install_command": command}


def validate_agent_token(db: Session, node_id: int, token: str) -> models.AgentToken:
    token_hash = hash_token(token)
    record = db.scalar(
        select(models.AgentToken).where(
            models.AgentToken.node_id == node_id,
            models.AgentToken.token_hash == token_hash,
            models.AgentToken.is_active.is_(True),
        )
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недійсний токен агента")
    record.last_used_at = datetime.utcnow()
    return record


def register_agent_node(db: Session, payload: dict, server_url: str = "http://localhost:8000") -> dict:
    environment_id = payload.get("environment_id")
    if not environment_id:
        env = db.scalar(select(models.Environment).where(models.Environment.environment_type == "remote").limit(1))
        if not env:
            env = models.Environment(name="Віддалені агенти", description="Вузли, які надсилають метрики через агент AutoInfraDiag.", environment_type="remote", status="healthy")
            db.add(env)
            db.commit()
            db.refresh(env)
        environment_id = env.id
    node = models.Node(
        environment_id=environment_id,
        name=payload["name"],
        description=payload.get("description"),
        hostname=payload.get("hostname"),
        node_type="remote_agent",
        role=payload.get("role") or "unknown",
        status="waiting",
        os_name=payload.get("os_name"),
        os_version=payload.get("os_version"),
        agent_version=get_settings().agent_version,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return create_token_for_node(db, node.id, server_url)


def heartbeat(db: Session, payload: dict) -> models.Node:
    validate_agent_token(db, payload["node_id"], payload["token"])
    node = db.get(models.Node, payload["node_id"])
    if not node:
        raise HTTPException(status_code=404, detail="Вузол не знайдено")
    node.status = "online"
    node.last_heartbeat_at = datetime.utcnow()
    node.hostname = payload.get("hostname") or node.hostname
    node.os_name = payload.get("os_name") or node.os_name
    node.os_version = payload.get("os_version") or node.os_version
    node.agent_version = payload.get("agent_version") or node.agent_version
    db.commit()
    db.refresh(node)
    return node


def install_command(server_url: str, node_id: int, token: str = "TOKEN") -> str:
    server = normalize_server_url(server_url)
    return f"python agent.py --server {server} --node-id {node_id} --token {token} --interval 5"
