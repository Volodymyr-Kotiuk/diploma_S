export interface Environment {
  id: number;
  name: string;
  description?: string | null;
  environment_type: 'simulated' | 'local' | 'remote' | string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Node {
  id: number;
  environment_id?: number | null;
  name: string;
  description?: string | null;
  hostname?: string | null;
  node_type: string;
  role?: string | null;
  status: string;
  os_name?: string | null;
  os_version?: string | null;
  agent_version?: string | null;
  last_heartbeat_at?: string | null;
  allocated_cpu_cores?: number | null;
  allocated_ram_mb?: number | null;
  max_cpu_cores?: number | null;
  max_ram_mb?: number | null;
  disk_total_gb?: number | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ResourceMetric {
  id: number;
  node_id: number;
  timestamp: string;
  cpu_usage_percent?: number | null;
  cpu_core_count?: number | null;
  load_average_1m?: number | null;
  load_average_5m?: number | null;
  load_average_15m?: number | null;
  ram_total_mb?: number | null;
  ram_used_mb?: number | null;
  ram_usage_percent?: number | null;
  ram_available_mb?: number | null;
  swap_total_mb?: number | null;
  swap_used_mb?: number | null;
  swap_usage_percent?: number | null;
  disk_total_gb?: number | null;
  disk_used_gb?: number | null;
  disk_usage_percent?: number | null;
  disk_read_rate?: number | null;
  disk_write_rate?: number | null;
  network_sent_rate?: number | null;
  network_recv_rate?: number | null;
  process_count?: number | null;
  uptime_seconds?: number | null;
  temperature_celsius?: number | null;
}

export interface Diagnostic {
  id: number;
  node_id: number;
  created_at: string;
  diagnosis_type: string;
  root_cause: string;
  severity: string;
  confidence: number;
  risk_score: number;
  explanation: string;
  evidence_json?: { evidence?: Evidence[]; anomaly?: Record<string, unknown> };
  status: string;
}

export interface Evidence {
  metric: string;
  current_value: unknown;
  threshold: unknown;
  explanation: string;
}

export interface Incident {
  id: number;
  node_id: number;
  diagnostic_id?: number | null;
  title: string;
  description: string;
  incident_type: string;
  severity: string;
  started_at: string;
  ended_at?: string | null;
  status: string;
  root_cause?: string | null;
}

export interface Recommendation {
  id: number;
  node_id: number;
  diagnostic_id?: number | null;
  recommendation_type: string;
  title: string;
  description: string;
  priority: string;
  current_cpu_cores?: number | null;
  recommended_cpu_cores?: number | null;
  current_ram_mb?: number | null;
  recommended_ram_mb?: number | null;
  expected_effect?: string | null;
  reason?: string | null;
  action_steps_json?: string[] | Record<string, unknown> | null;
  created_at: string;
  status: string;
}

export interface CapacityForecast {
  id: number;
  node_id: number;
  metric_name: string;
  current_value?: number | null;
  predicted_value?: number | null;
  predicted_threshold_time?: string | null;
  trend_direction: string;
  recommendation: string;
  created_at: string;
}

export interface DashboardSummary {
  environments: number;
  nodes: number;
  online_nodes: number;
  offline_nodes: number;
  active_incidents: number;
  critical_recommendations: number;
  average_cpu: number;
  average_ram: number;
  overall_risk: number;
}

export interface SimulationScenario {
  id: number;
  environment_id: number;
  target_node_id?: number | null;
  name: string;
  scenario_type: string;
  duration_seconds: number;
  intensity: number;
  status: string;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface Report {
  id: number;
  environment_id?: number | null;
  node_id?: number | null;
  report_type: string;
  file_path: string;
  created_at: string;
}
