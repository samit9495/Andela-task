export interface Metrics {
  total_events: number;
  events_by_level: Record<string, number>;
  monitored_services: number;
  total_incidents: number;
  total_alerts: number;
  risk_score: number;
}

export interface RiskScore {
  score: number;
  status: string;
  error_penalty: number;
  alert_penalty: number;
  incident_penalty: number;
}

export interface Anomaly {
  id: number;
  strategy: string;
  service: string;
  signature: string | null;
  score: number;
  baseline_value: number;
  current_value: number;
  window_start: string;
  window_end: string;
  created_at: string;
}

export interface RunbookReference {
  slug: string;
  title: string;
}

export interface Incident {
  id: number;
  title: string;
  service: string | null;
  category: string | null;
  severity: string;
  status: string;
  root_cause: string | null;
  summary: string | null;
  confidence_score: number | null;
  recommended_actions: string[] | null;
  runbook_references: RunbookReference[] | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  anomalies: Anomaly[];
}

export interface Alert {
  id: number;
  incident_id: number;
  channel: string;
  status: string;
  dedup_key: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface TopologyNode {
  service: string;
  depends_on: string[];
  impacted: boolean;
}

export interface TopologyEdge {
  source: string;
  target: string;
}

export interface Topology {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}
