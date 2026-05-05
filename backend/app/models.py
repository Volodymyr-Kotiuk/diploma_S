from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    environment_type: Mapped[str] = mapped_column(String(32), default="simulated", index=True)
    status: Mapped[str] = mapped_column(String(32), default="healthy", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    nodes: Mapped[list["Node"]] = relationship(back_populates="environment", cascade="all, delete-orphan")
    simulation_scenarios: Mapped[list["SimulationScenario"]] = relationship(back_populates="environment", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="environment")


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    environment_id: Mapped[int | None] = mapped_column(ForeignKey("environments.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    hostname: Mapped[str | None] = mapped_column(String(255))
    node_type: Mapped[str] = mapped_column(String(48), default="virtual_node", index=True)
    role: Mapped[str] = mapped_column(String(48), default="unknown", index=True)
    status: Mapped[str] = mapped_column(String(32), default="waiting", index=True)
    os_name: Mapped[str | None] = mapped_column(String(120))
    os_version: Mapped[str | None] = mapped_column(String(180))
    agent_version: Mapped[str | None] = mapped_column(String(40))
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime)
    allocated_cpu_cores: Mapped[int | None] = mapped_column(Integer)
    allocated_ram_mb: Mapped[int | None] = mapped_column(Integer)
    max_cpu_cores: Mapped[int | None] = mapped_column(Integer)
    max_ram_mb: Mapped[int | None] = mapped_column(Integer)
    disk_total_gb: Mapped[float | None] = mapped_column(Float)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    environment: Mapped[Environment | None] = relationship(back_populates="nodes")
    tokens: Mapped[list["AgentToken"]] = relationship(back_populates="node", cascade="all, delete-orphan")
    metrics: Mapped[list["ResourceMetric"]] = relationship(back_populates="node", cascade="all, delete-orphan")
    diagnostics: Mapped[list["Diagnostic"]] = relationship(back_populates="node", cascade="all, delete-orphan")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="node", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="node", cascade="all, delete-orphan")
    capacity_forecasts: Mapped[list["CapacityForecast"]] = relationship(back_populates="node", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="node")


class AgentToken(Base):
    __tablename__ = "agent_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    token_preview: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime)

    node: Mapped[Node] = relationship(back_populates="tokens")


class ResourceMetric(Base):
    __tablename__ = "resource_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    cpu_usage_percent: Mapped[float | None] = mapped_column(Float)
    cpu_core_count: Mapped[int | None] = mapped_column(Integer)
    load_average_1m: Mapped[float | None] = mapped_column(Float)
    load_average_5m: Mapped[float | None] = mapped_column(Float)
    load_average_15m: Mapped[float | None] = mapped_column(Float)
    ram_total_mb: Mapped[float | None] = mapped_column(Float)
    ram_used_mb: Mapped[float | None] = mapped_column(Float)
    ram_usage_percent: Mapped[float | None] = mapped_column(Float)
    ram_available_mb: Mapped[float | None] = mapped_column(Float)
    swap_total_mb: Mapped[float | None] = mapped_column(Float)
    swap_used_mb: Mapped[float | None] = mapped_column(Float)
    swap_usage_percent: Mapped[float | None] = mapped_column(Float)
    disk_total_gb: Mapped[float | None] = mapped_column(Float)
    disk_used_gb: Mapped[float | None] = mapped_column(Float)
    disk_usage_percent: Mapped[float | None] = mapped_column(Float)
    disk_read_bytes: Mapped[float | None] = mapped_column(Float)
    disk_write_bytes: Mapped[float | None] = mapped_column(Float)
    disk_read_rate: Mapped[float | None] = mapped_column(Float)
    disk_write_rate: Mapped[float | None] = mapped_column(Float)
    network_bytes_sent: Mapped[float | None] = mapped_column(Float)
    network_bytes_recv: Mapped[float | None] = mapped_column(Float)
    network_sent_rate: Mapped[float | None] = mapped_column(Float)
    network_recv_rate: Mapped[float | None] = mapped_column(Float)
    process_count: Mapped[int | None] = mapped_column(Integer)
    uptime_seconds: Mapped[float | None] = mapped_column(Float)
    temperature_celsius: Mapped[float | None] = mapped_column(Float)
    service_latency_ms: Mapped[float | None] = mapped_column(Float)
    service_error_rate: Mapped[float | None] = mapped_column(Float)
    custom_json: Mapped[dict | None] = mapped_column(JSON)

    node: Mapped[Node] = relationship(back_populates="metrics")


class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    diagnosis_type: Mapped[str] = mapped_column(String(80), index=True)
    root_cause: Mapped[str] = mapped_column(String(160))
    severity: Mapped[str] = mapped_column(String(32), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    risk_score: Mapped[float] = mapped_column(Float, default=0)
    explanation: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[dict | list | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)

    node: Mapped[Node] = relationship(back_populates="diagnostics")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="diagnostic")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="diagnostic")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    diagnostic_id: Mapped[int | None] = mapped_column(ForeignKey("diagnostics.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    incident_type: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    root_cause: Mapped[str | None] = mapped_column(String(160))
    evidence_json: Mapped[dict | list | None] = mapped_column(JSON)

    node: Mapped[Node] = relationship(back_populates="incidents")
    diagnostic: Mapped[Diagnostic | None] = relationship(back_populates="incidents")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    diagnostic_id: Mapped[int | None] = mapped_column(ForeignKey("diagnostics.id", ondelete="SET NULL"), index=True)
    recommendation_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(32), index=True)
    current_cpu_cores: Mapped[int | None] = mapped_column(Integer)
    recommended_cpu_cores: Mapped[int | None] = mapped_column(Integer)
    current_ram_mb: Mapped[int | None] = mapped_column(Integer)
    recommended_ram_mb: Mapped[int | None] = mapped_column(Integer)
    expected_effect: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    action_steps_json: Mapped[list | dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)

    node: Mapped[Node] = relationship(back_populates="recommendations")
    diagnostic: Mapped[Diagnostic | None] = relationship(back_populates="recommendations")


class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    environment_id: Mapped[int] = mapped_column(ForeignKey("environments.id", ondelete="CASCADE"), index=True)
    target_node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(80), index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=300)
    intensity: Mapped[float] = mapped_column(Float, default=0.8)
    status: Mapped[str] = mapped_column(String(32), default="created", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    config_json: Mapped[dict | None] = mapped_column(JSON)

    environment: Mapped[Environment] = relationship(back_populates="simulation_scenarios")


class CapacityForecast(Base):
    __tablename__ = "capacity_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    metric_name: Mapped[str] = mapped_column(String(80), index=True)
    current_value: Mapped[float | None] = mapped_column(Float)
    predicted_value: Mapped[float | None] = mapped_column(Float)
    predicted_threshold_time: Mapped[datetime | None] = mapped_column(DateTime)
    trend_direction: Mapped[str] = mapped_column(String(32))
    recommendation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    node: Mapped[Node] = relationship(back_populates="capacity_forecasts")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    environment_id: Mapped[int | None] = mapped_column(ForeignKey("environments.id", ondelete="SET NULL"), index=True)
    node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id", ondelete="SET NULL"), index=True)
    report_type: Mapped[str] = mapped_column(String(60), index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    environment: Mapped[Environment | None] = relationship(back_populates="reports")
    node: Mapped[Node | None] = relationship(back_populates="reports")
