import { apiRequest } from "./api";

export interface PredictiveSummaryResponse {
  total_machines_monitored: number;
  high_risk_count: number;
  warning_count: number;
  stable_count: number;
  average_fleet_risk_pct: number;
  total_potential_savings_usd: number;
  total_downtime_hours_avoided: number;
}

export interface MachineRiskResponse {
  machine_id: string;
  machine_type: string;
  failure_risk: number;
  risk_level: string;
  predicted_failure_window: string;
  likely_failure_mode: string;
  recommended_action: string;
  explanation: string[];
  downtime_avoided_hours: number;
  estimated_savings_usd: number;
}

export interface MachineForecastRecord {
  machine_id: string;
  machine_type: string;
  failure_risk: number;
  risk_level: string;
  predicted_failure_window: string;
  likely_failure_mode: string;
}

export interface PriorityRecord {
  machine_id: string;
  machine_type: string;
  priority_index: number;
  risk_level: string;
  failure_risk: number;
  predicted_failure_window: string;
  likely_failure_mode: string;
  downtime_avoided_hours: number;
  estimated_savings_usd: number;
  recommended_action: string;
  delay_impact_description: string;
}

export const predictiveService = {
  async getPredictiveSummary(): Promise<PredictiveSummaryResponse> {
    return apiRequest<PredictiveSummaryResponse>("/analytics/predictive-maintenance");
  },

  async getMachineRisk(machineId: string): Promise<MachineRiskResponse> {
    return apiRequest<MachineRiskResponse>(`/analytics/machine/${machineId}/risk`);
  },

  async getFailureForecast(): Promise<MachineForecastRecord[]> {
    return apiRequest<MachineForecastRecord[]>("/analytics/failure-forecast");
  },

  async getMaintenancePriority(): Promise<PriorityRecord[]> {
    return apiRequest<PriorityRecord[]>("/analytics/maintenance-priority");
  },
};
