from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EnvironmentBase(BaseModel):
    name: str
    description: str | None = None
    environment_type: str = "simulated"
    status: str = "healthy"


class EnvironmentCreate(EnvironmentBase):
    pass


class EnvironmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    environment_type: str | None = None
    status: str | None = None


class EnvironmentRead(EnvironmentBase, OrmModel):
    id: int
    created_at: datetime
    updated_at: datetime


class NodeBase(BaseModel):
    environment_id: int | None = None
    name: str
    description: str | None = None
    hostname: str | None = None
    node_type: str = "virtual_node"
    role: str = "unknown"
    status: str = "waiting"
    os_name: str | None = None
    os_version: str | None = None
    agent_version: str | None = None
    allocated_cpu_cores: int | None = None
    allocated_ram_mb: int | None = None
    max_cpu_cores: int | None = None
    max_ram_mb: int | None = None
    disk_total_gb: float | None = None
    metadata_json: dict[str, Any] | None = None


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    environment_id: int | None = None
    name: str | None = None
    description: str | None = None
    hostname: str | None = None
    node_type: str | None = None
    role: str | None = None
    status: str | None = None
    os_name: str | None = None
    os_version: str | None = None
    agent_version: str | None = None
    allocated_cpu_cores: int | None = None
    allocated_ram_mb: int | None = None
    max_cpu_cores: int | None = None
    max_ram_mb: int | None = None
    disk_total_gb: float | None = None
    metadata_json: dict[str, Any] | None = None


class NodeRead(NodeBase, OrmModel):
    id: int
    last_heartbeat_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AgentTokenRead(OrmModel):
    id: int
    node_id: int
    token_preview: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None


class AgentRegisterRequest(BaseModel):
    name: str
    description: str | None = None
    hostname: str | None = None
    environment_id: int | None = None
    role: str = "unknown"
    os_name: str | None = None
    os_version: str | None = None


class AgentTokenResponse(BaseModel):
    node: NodeRead
    token: str
    token_preview: str
    install_command: str


class AgentHeartbeatRequest(BaseModel):
    node_id: int
    token: str
    hostname: str | None = None
    os_name: str | None = None
    os_version: str | None = None
    agent_version: str | None = None


class ResourceMetricBase(BaseModel):
    node_id: int
    timestamp: datetime | None = None
    cpu_usage_percent: float | None = None
    cpu_core_count: int | None = None
    load_average_1m: float | None = None
    load_average_5m: float | None = None
    load_average_15m: float | None = None
    ram_total_mb: float | None = None
    ram_used_mb: float | None = None
    ram_usage_percent: float | None = None
    ram_available_mb: float | None = None
    swap_total_mb: float | None = None
    swap_used_mb: float | None = None
    swap_usage_percent: float | None = None
    disk_total_gb: float | None = None
    disk_used_gb: float | None = None
    disk_usage_percent: float | None = None
    disk_read_bytes: float | None = None
    disk_write_bytes: float | None = None
    disk_read_rate: float | None = None
    disk_write_rate: float | None = None
    network_bytes_sent: float | None = None
    network_bytes_recv: float | None = None
    network_sent_rate: float | None = None
    network_recv_rate: float | None = None
    process_count: int | None = None
    uptime_seconds: float | None = None
    temperature_celsius: float | None = None
    service_latency_ms: float | None = None
    service_error_rate: float | None = None
    custom_json: dict[str, Any] | None = None


class ResourceMetricCreate(ResourceMetricBase):
    pass


class AgentMetricsRequest(ResourceMetricBase):
    token: str


class ResourceMetricRead(ResourceMetricBase, OrmModel):
    id: int
    timestamp: datetime


class DiagnosticRead(OrmModel):
    id: int
    node_id: int
    created_at: datetime
    diagnosis_type: str
    root_cause: str
    severity: str
    confidence: float
    risk_score: float
    explanation: str
    evidence_json: Any = None
    status: str


class IncidentRead(OrmModel):
    id: int
    node_id: int
    diagnostic_id: int | None = None
    title: str
    description: str
    incident_type: str
    severity: str
    started_at: datetime
    ended_at: datetime | None = None
    status: str
    root_cause: str | None = None
    evidence_json: Any = None


class RecommendationRead(OrmModel):
    id: int
    node_id: int
    diagnostic_id: int | None = None
    recommendation_type: str
    title: str
    description: str
    priority: str
    current_cpu_cores: int | None = None
    recommended_cpu_cores: int | None = None
    current_ram_mb: int | None = None
    recommended_ram_mb: int | None = None
    expected_effect: str | None = None
    reason: str | None = None
    action_steps_json: Any = None
    created_at: datetime
    status: str


class SimulationScenarioCreate(BaseModel):
    environment_id: int
    target_node_id: int | None = None
    name: str
    scenario_type: str
    duration_seconds: int = Field(default=300, ge=10, le=86400)
    intensity: float = Field(default=0.8, ge=0.1, le=1.0)
    config_json: dict[str, Any] | None = None


class NodeScenarioRunRequest(BaseModel):
    scenario_type: str = "cpu_saturation"
    duration_seconds: int = Field(default=300, ge=10, le=86400)
    intensity: float = Field(default=0.85, ge=0.1, le=1.0)


class SimulationScenarioRead(OrmModel):
    id: int
    environment_id: int
    target_node_id: int | None = None
    name: str
    scenario_type: str
    duration_seconds: int
    intensity: float
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    config_json: Any = None


class DemoEnvironmentRequest(BaseModel):
    name: str = "Демонстраційний віртуальний кластер"


class CapacityForecastRead(OrmModel):
    id: int
    node_id: int
    metric_name: str
    current_value: float | None = None
    predicted_value: float | None = None
    predicted_threshold_time: datetime | None = None
    trend_direction: str
    recommendation: str
    created_at: datetime


class ReportRead(OrmModel):
    id: int
    environment_id: int | None = None
    node_id: int | None = None
    report_type: str
    file_path: str
    created_at: datetime


class DashboardSummary(BaseModel):
    environments: int
    nodes: int
    online_nodes: int
    offline_nodes: int
    active_incidents: int
    critical_recommendations: int
    average_cpu: float
    average_ram: float
    overall_risk: float


class StatusMessage(BaseModel):
    status: str
    message: str
