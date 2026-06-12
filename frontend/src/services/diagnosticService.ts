import { apiRequest } from "./api";

export interface DiagnosticRecord {
  event_id: string;
  machine_id: string;
  machine_type: string;
  timestamp: string;
  anomaly_type: string;
  explanation: string;
  evidence: string;
  probable_causes: string[];
  recommendations: string[];
  confidence: number;
}

export interface RootCauseDistribution {
  cause: string;
  count: number;
  avg_confidence: number;
}

export const diagnosticService = {
  async getDiagnostics(limit: number = 50): Promise<DiagnosticRecord[]> {
    return apiRequest<DiagnosticRecord[]>(`/analytics/diagnostics?limit=${limit}`);
  },

  async getMachineDiagnostics(machineId: string, limit: number = 20): Promise<DiagnosticRecord[]> {
    return apiRequest<DiagnosticRecord[]>(`/analytics/diagnostics/${machineId}?limit=${limit}`);
  },

  async getRootCauses(): Promise<RootCauseDistribution[]> {
    return apiRequest<RootCauseDistribution[]>("/analytics/root-causes");
  }
};
