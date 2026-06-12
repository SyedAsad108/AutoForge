import { apiRequest } from "./api";

// --- Existing Types ---

export interface FactorySummaryResponse {
  total_machines: number;
  healthy: number;
  warning: number;
  critical: number;
}

export interface DailySummaryRecord {
  date: string;
  total_events: number;
  active_machines: number;
  total_anomalies: number;
  avg_degradation_level: number;
}

export interface AnomalyDistributionRecord {
  anomaly_type: string;
  machine_type: string;
  anomaly_count: number;
  avg_anomaly_severity: number;
}

export interface AggregatedAnalyticsResponse {
  daily_summaries: DailySummaryRecord[];
  anomaly_distribution: AnomalyDistributionRecord[];
}

// --- Phase 10.5 Types ---

export interface HourlyTrendRecord {
  time_label: string;
  total_events: number;
  anomaly_count: number;
  anomaly_rate_pct: number;
  healthy_count: number;
  warning_count: number;
  critical_count: number;
}

export interface EnergyProfileRecord {
  machine_type: string;
  total_energy: number;
  avg_power: number;
  event_count: number;
}

export interface BusinessKPIResponse {
  factory_health_score: number;
  production_efficiency_score: number;
  overall_anomaly_rate_pct: number;
  production_risk_score: number;
  most_affected_machine_id: string | null;
  most_affected_machine_type: string | null;
  most_affected_anomaly_rate: number;
  energy_leader_type: string | null;
  energy_leader_value: number;
  total_machines: number;
  healthy_count: number;
  warning_count: number;
  critical_count: number;
}

export interface OperationalRecommendation {
  priority: "critical" | "warning" | "info";
  machine_id: string | null;
  machine_type: string | null;
  recommendation: string;
  reason: string;
  metric_value: number | null;
  metric_name: string | null;
}


export interface TelemetryActivityKPIs {
  total_events: number;
  telemetry_rate_per_min: number;
  peak_rate_per_min: number;
  anomaly_rate_pct: number;
  trend_pct: number;
}

export interface TelemetryActivitySeriesRecord {
  time_label: string;
  total_events: number;
  anomaly_count: number;
  healthy_count: number;
  warning_count: number;
  critical_count: number;
}

export interface MachineActivityBreakdown {
  machine_type: string;
  event_count: number;
  percentage: number;
}

export interface TelemetryPipelineHealth {
  simulator: string;
  kinesis: string;
  lambda_validator: string;
  glue_etl: string;
  athena_engine: string;
  freshness_seconds: number;
}

export interface TelemetryActivityResponse {
  selected_window: string;
  auto_suggested_window: string;
  time_span_seconds: number;
  kpis: TelemetryActivityKPIs;
  series: TelemetryActivitySeriesRecord[];
  machine_breakdown: MachineActivityBreakdown[];
  pipeline_health: TelemetryPipelineHealth;
  insights: string[];
  collection_progress_pct: number;
  estimated_time_remaining_minutes: number;
}

// --- Service ---

export const analyticsService = {
  async getFactorySummary(): Promise<FactorySummaryResponse> {
    return apiRequest<FactorySummaryResponse>("/analytics/factory-summary");
  },

  async getAggregatedAnalytics(): Promise<AggregatedAnalyticsResponse> {
    return apiRequest<AggregatedAnalyticsResponse>("/analytics");
  },

  // Phase 10.5

  async getHourlyTrends(): Promise<HourlyTrendRecord[]> {
    return apiRequest<HourlyTrendRecord[]>("/analytics/hourly-trends");
  },

  async getEnergyProfile(): Promise<EnergyProfileRecord[]> {
    return apiRequest<EnergyProfileRecord[]>("/analytics/energy-profile");
  },

  async getBusinessKPIs(): Promise<BusinessKPIResponse> {
    return apiRequest<BusinessKPIResponse>("/analytics/business-kpis");
  },

  async getRecommendations(): Promise<OperationalRecommendation[]> {
    return apiRequest<OperationalRecommendation[]>("/analytics/recommendations");
  },

  async getTelemetryActivity(window?: string): Promise<TelemetryActivityResponse> {
    const query = window ? `?window=${window}` : "";
    return apiRequest<TelemetryActivityResponse>(`/analytics/telemetry-activity${query}`);
  },

  async getPipelineMetrics(): Promise<any> {
    return apiRequest<any>("/analytics/pipeline/realtime");
  },
};
