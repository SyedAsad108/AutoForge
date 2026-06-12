import { apiRequest } from "./api";

export interface AlertEvent {
  event_id: string;
  machine_id: string;
  machine_type: string;
  timestamp: string;
  anomaly_type: string;
  severity: number;
  status: string;
}

export const getSeverityLabel = (severity: number): "Low" | "Medium" | "High" | "Critical" => {
  if (severity >= 0.75) return "Critical";
  if (severity >= 0.40) return "High";
  if (severity >= 0.10) return "Medium";
  return "Low";
};

export const getAnomalyExplanation = (anomalyType: string): string => {
  const normalized = anomalyType.toLowerCase().replace(/_/g, " ");
  if (normalized.includes("overheating") || normalized.includes("temperature")) {
    return "Coil temperature exceeded safe thermal operating limits.";
  }
  if (normalized.includes("rpm") || normalized.includes("speed")) {
    return "Rotational velocity fluctuated outside nominal safety limits.";
  }
  if (normalized.includes("energy") || normalized.includes("power") || normalized.includes("spike")) {
    return "Electric current load exceeded maximum peak safety index.";
  }
  if (normalized.includes("pressure")) {
    return "System pressure dropped below minimum active operating threshold.";
  }
  if (normalized.includes("vibration") || normalized.includes("shake")) {
    return "Vibrational harmonics indicate structural mechanical imbalance.";
  }
  if (normalized.includes("leak")) {
    return "Coolant or fluid level decay rate is higher than normal limits.";
  }
  return `Machine parameters deviate from typical baselines (${anomalyType}).`;
};

export const getAnomalyAction = (anomalyType: string): string => {
  const normalized = anomalyType.toLowerCase().replace(/_/g, " ");
  if (normalized.includes("overheating") || normalized.includes("temperature")) {
    return "Clean cooling vents, check airflow path, and inspect heat exchanger.";
  }
  if (normalized.includes("rpm") || normalized.includes("speed")) {
    return "Verify structural alignment and inspect motor shaft lubrication.";
  }
  if (normalized.includes("energy") || normalized.includes("power") || normalized.includes("spike")) {
    return "Inspect electrical relay breakers and check load distribution panels.";
  }
  if (normalized.includes("pressure")) {
    return "Check fluid levels, inspect pump valves, and search for hose leaks.";
  }
  if (normalized.includes("vibration") || normalized.includes("shake")) {
    return "Tighten mounting bolts, schedule re-alignment, and check bearings.";
  }
  if (normalized.includes("leak")) {
    return "Check mechanical seals, inspect safety gaskets, and tighten valves.";
  }
  return "Perform standard diagnostic inspect run and verify telemetry feed.";
};

export const alertService = {
  async getAlerts(limit: number = 50): Promise<AlertEvent[]> {
    return apiRequest<AlertEvent[]>(`/analytics/alerts?limit=${limit}`);
  }
};
