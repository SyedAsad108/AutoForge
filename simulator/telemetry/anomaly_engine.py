"""
Expanded Anomaly Engine for Phase 2 of the AutoForge factory simulator.

Builds on top of the Phase 1 anomaly types (defined in ``anomalies.py``)
to add:
  • duration tracking
  • severity escalation curves
  • intermittent behaviour (anomalies that come and go)
  • cascading anomaly triggers (one anomaly can spawn another)
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.logger import setup_logger

logger = setup_logger("AnomalyEngine")


# ----- Cascading rules ----- #
# Maps an anomaly type to the secondary anomaly it can trigger, with a
# threshold severity and probability.
@dataclass
class CascadeRule:
    """Describes when one anomaly may trigger a secondary anomaly."""
    source: AnomalyType
    target: AnomalyType
    severity_threshold: float  # source severity at which cascade becomes possible
    probability: float         # per-tick probability once threshold is met


CASCADE_RULES: List[CascadeRule] = [
    CascadeRule(AnomalyType.OVERHEATING, AnomalyType.UNSTABLE_RPM, 0.6, 0.03),
    CascadeRule(AnomalyType.VIBRATION_ANOMALY, AnomalyType.EXCESSIVE_TOOL_WEAR, 0.5, 0.04),
    CascadeRule(AnomalyType.PRESSURE_DROP, AnomalyType.OVERHEATING, 0.55, 0.03),
    CascadeRule(AnomalyType.MOTOR_OVERHEATING, AnomalyType.MOVEMENT_DELAY_SPIKE, 0.5, 0.05),
    CascadeRule(AnomalyType.COOLANT_REDUCTION, AnomalyType.PRESSURE_FLUCTUATION, 0.4, 0.04),
    CascadeRule(AnomalyType.UNSTABLE_ARC, AnomalyType.ENERGY_SPIKE, 0.5, 0.04),
    CascadeRule(AnomalyType.ALIGNMENT_DEGRADATION, AnomalyType.EFFICIENCY_DROP, 0.45, 0.05),
]


@dataclass
class AnomalyState:
    """Tracks per-machine anomaly metadata for the engine."""
    duration_ticks: int = 0
    intermittent: bool = False
    cascaded_from: Optional[AnomalyType] = None


class AnomalyEngine:
    """
    Manages anomaly lifecycles across the entire machine fleet.

    Responsibilities:
      - Track anomaly duration for each machine
      - Apply intermittent behaviour (anomalies temporarily suppress then resurge)
      - Trigger cascade rules when severity thresholds are met
    """

    def __init__(self, machines: List[BaseMachine]):
        self._machines = machines
        # Per-machine anomaly tracking
        self._states: Dict[str, AnomalyState] = {
            m.machine_id: AnomalyState() for m in machines
        }

    def tick(self) -> None:
        """Advance the anomaly model by one tick for every machine."""
        for machine in self._machines:
            state = self._states[machine.machine_id]
            if machine.current_anomaly == AnomalyType.NONE:
                state.duration_ticks = 0
                state.intermittent = False
                continue

            state.duration_ticks += 1

            # ----- Intermittent behaviour ----- #
            # After 20+ ticks, anomalies can "flicker" (drop severity briefly)
            if state.duration_ticks > 20 and random.random() < 0.08:
                if not state.intermittent:
                    state.intermittent = True
                    machine.anomaly_severity = max(0.05, machine.anomaly_severity * 0.6)
                    logger.info(
                        f"[ANOMALY] {machine.machine_id} anomaly "
                        f"'{machine.current_anomaly.value}' entering intermittent phase"
                    )
                else:
                    state.intermittent = False
                    machine.anomaly_severity = min(1.0, machine.anomaly_severity * 1.4)
                    logger.info(
                        f"[ANOMALY] {machine.machine_id} anomaly resurging  "
                        f"severity={machine.anomaly_severity:.2f}"
                    )

            # ----- Cascade evaluation ----- #
            self._evaluate_cascades(machine)

    def _evaluate_cascades(self, machine: BaseMachine) -> None:
        """Check if the machine's current anomaly should cascade."""
        for rule in CASCADE_RULES:
            if machine.current_anomaly != rule.source:
                continue
            if machine.anomaly_severity < rule.severity_threshold:
                continue
            if rule.target not in machine.possible_anomalies:
                continue
            if random.random() > rule.probability:
                continue

            # Cascade triggers: replace current anomaly with the target
            old = machine.current_anomaly
            machine.current_anomaly = rule.target
            machine.anomaly_severity = max(0.15, machine.anomaly_severity * 0.5)
            self._states[machine.machine_id].cascaded_from = old
            logger.warning(
                f"[CASCADE] {machine.machine_id} anomaly cascaded: "
                f"{old.value} → {rule.target.value}  "
                f"severity={machine.anomaly_severity:.2f}"
            )
            break  # Only one cascade per tick
