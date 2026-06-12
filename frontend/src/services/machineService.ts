import { apiRequest } from "./api";

export interface MachineHealthRecord {
  machine_id: string;
  machine_type: string;
  total_events: number;
  anomaly_events: number;
  anomaly_rate_percent: number;
  avg_temperature: number | null;
  max_degradation_level: number;
  health_status: "healthy" | "warning" | "critical" | "offline";
  health_score: number;
}

export interface MachineHistoryRecord {
  timestamp: string;
  temperature: number | null;
  degradation_level: number;
  anomaly_detected: boolean;
  status: string;
  pressure: number | null;
  power_consumption: number | null;
  vibration: number | null;
  cycle_efficiency: number | null;
}

export interface MachineExplanationDetail {
  problem: string;
  confidence: number;
  possible_causes: string[];
  operational_impact: string;
  recommended_action: string;
}

export interface RootCauseItem {
  cause: string;
  confidence: number;
  explanation: string;
}

export interface PredictiveMaintenanceDetail {
  failure_risk_pct: number;
  maintenance_recommendation: string;
  remaining_useful_life_days: number;
  health_trend: string;
}

export interface LiveOperatingConditions {
  temperature: number | null;
  pressure: number | null;
  power_consumption: number | null;
  vibration: number | null;
  degradation: number;
}

export interface RiskTimelineEvent {
  timestamp: string;
  event_type: "anomaly" | "warning" | "critical";
  description: string;
  severity: number;
}

export interface MachineAnalyticsResponse {
  machine_id: string;
  machine_type: string;
  total_events: number;
  anomaly_events: number;
  anomaly_rate_percent: number;
  avg_temperature: number | null;
  max_degradation_level: number;
  health_status: "healthy" | "warning" | "critical";
  history: MachineHistoryRecord[];
  health_score: number;
  last_updated: string;
  current_conditions: LiveOperatingConditions;
  predictive_maintenance: PredictiveMaintenanceDetail;
  active_anomaly: MachineExplanationDetail | null;
  root_cause_analysis: RootCauseItem[];
  risk_timeline: RiskTimelineEvent[];
}

export const machineService = {
  async getMachines(): Promise<MachineHealthRecord[]> {
    return apiRequest<MachineHealthRecord[]>("/analytics/machines");
  },

  async getMachineDetails(machineId: string, window?: string): Promise<MachineAnalyticsResponse> {
    const query = window ? `?window=${window}` : "";
    return apiRequest<MachineAnalyticsResponse>(`/analytics/machine/${machineId}${query}`);
  }
};
