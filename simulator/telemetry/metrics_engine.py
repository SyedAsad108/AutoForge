"""
Real-time factory-wide metrics engine for AutoForge.

Continuously computes aggregate KPIs from the live machine fleet:
  • Average factory temperature
  • Active anomaly count
  • Machine-health distribution
  • Total energy consumption
  • Operational efficiency index
  • Number of critical / offline machines
"""

from typing import Any, Dict, List

from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.constants import STATUS_HEALTHY, STATUS_WARNING, STATUS_CRITICAL, STATUS_OFFLINE
from simulator.utils.logger import setup_logger

logger = setup_logger("MetricsEngine")


class MetricsEngine:
    """
    Evaluates factory-wide aggregate metrics every simulation tick.
    """

    def __init__(self, machines: List[BaseMachine]):
        self._machines = machines
        self._tick_count: int = 0

    def compute(self) -> Dict[str, Any]:
        """
        Compute and return the current factory-wide metrics snapshot.
        """
        self._tick_count += 1
        total = len(self._machines)
        if total == 0:
            return {}

        temps: List[float] = []
        energy: float = 0.0
        anomaly_count: int = 0
        health_dist = {STATUS_HEALTHY: 0, STATUS_WARNING: 0, STATUS_CRITICAL: 0, STATUS_OFFLINE: 0}

        for m in self._machines:
            # Temperature (grab whichever attribute exists)
            for attr in ("temperature", "motor_temperature"):
                val = getattr(m, attr, None)
                if val is not None:
                    temps.append(val)
                    break

            # Energy proxies
            energy += getattr(m, "power_consumption", 0.0)
            energy += getattr(m, "energy_usage", 0.0)
            energy += getattr(m, "energy_output", 0.0)

            # Anomaly tally
            if m.current_anomaly != AnomalyType.NONE:
                anomaly_count += 1

            # Health distribution
            if m.status in health_dist:
                health_dist[m.status] += 1

        active_machines = total - health_dist[STATUS_OFFLINE]
        operational_efficiency = (
            (health_dist[STATUS_HEALTHY] / active_machines * 100.0) if active_machines > 0 else 0.0
        )

        metrics: Dict[str, Any] = {
            "tick": self._tick_count,
            "total_machines": total,
            "avg_temperature": round(sum(temps) / len(temps), 2) if temps else 0.0,
            "active_anomalies": anomaly_count,
            "health_distribution": health_dist,
            "total_energy_consumption": round(energy, 2),
            "operational_efficiency_pct": round(operational_efficiency, 2),
            "critical_machines": health_dist[STATUS_CRITICAL],
            "offline_machines": health_dist[STATUS_OFFLINE],
        }
        return metrics
