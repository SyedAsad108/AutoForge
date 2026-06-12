"""
Degradation Engine for the AutoForge factory simulator.

Iterates over machines to handle broader state transitions.
"""

import random
from typing import List

from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.constants import (
    STATUS_HEALTHY,
    STATUS_WARNING,
    STATUS_CRITICAL,
    STATUS_OFFLINE,
)
from simulator.utils.logger import setup_logger

logger = setup_logger("DegradationEngine")


class DegradationEngine:
    """
    Runs once per simulation tick to evolve machine degradation curves.
    """

    def __init__(self, machines: List[BaseMachine]):
        self._machines = machines
        self._tick_count: int = 0

    def tick(self) -> None:
        """Advance the degradation model for all machines by one tick."""
        self._tick_count += 1
        
        for machine in self._machines:
            self._process_machine(machine)

    def _process_machine(self, machine: BaseMachine) -> None:
        # Critical -> Offline transition
        if machine.status == STATUS_CRITICAL:
            if machine.degradation_level >= 0.95 or random.random() < 0.05:
                machine.status = STATUS_OFFLINE
                logger.info(f"[DEGRADATION] Critical machine {machine.machine_id} went offline")
                return

        # Offline -> Warning transition (simulated restart/repair)
        if machine.status == STATUS_OFFLINE:
            if random.random() < 0.10:
                machine.status = STATUS_WARNING
                machine.degradation_level = max(0.0, machine.degradation_level - 0.5)
                machine.anomaly_severity = 0.0
                machine.current_anomaly = AnomalyType.NONE
                logger.info(f"[RESTART] Offline machine {machine.machine_id} restarted")
