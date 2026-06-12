"""
Correlated Failure Engine for the AutoForge factory simulator.

Models industrial causality chains where the degradation or anomaly state
of one machine influences the telemetry and health of other machines.

Correlation rules implemented:
  1. Cooling System failure → rises in temperature of CNC, Robotic Arm,
     and Turbine machines.
  2. Turbine vibration anomaly → energy output drops, nearby machines
     see elevated heat.
  3. CNC tool-wear progression → vibration and spindle instability.
  4. Robotic Arm overload → motor heat rises, accuracy drops.
"""

from typing import List

from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.constants import CORRELATION_ENABLED
from simulator.utils.logger import setup_logger

logger = setup_logger("CorrelationEngine")


class CorrelationEngine:
    """
    Evaluates cross-machine dependencies every simulation tick.

    The engine is given the full machine fleet and applies correlation
    rules that propagate effects from degraded/failing machines to
    their neighbours.
    """

    def __init__(self, machines: List[BaseMachine]):
        self._machines = machines
        self._enabled = CORRELATION_ENABLED

        # Pre-index machines by type for O(1) look-ups
        self._by_type: dict[str, List[BaseMachine]] = {}
        for m in machines:
            self._by_type.setdefault(m.machine_type, []).append(m)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def apply_correlations(self) -> None:
        """Run all correlation rules against the current machine fleet."""
        if not self._enabled:
            return
        self._cooling_failure_propagation()
        self._turbine_vibration_chain()
        self._cnc_tool_wear_chain()
        self._robotic_arm_overload_chain()

    # ------------------------------------------------------------------
    # Correlation rules
    # ------------------------------------------------------------------
    def _cooling_failure_propagation(self) -> None:
        """
        If any cooling system is degraded or anomalous, nearby machines
        (CNC, Robotic Arm, Turbine) receive a temperature bump.
        """
        cooling_machines = self._by_type.get("cooling_system", [])
        affected_types = ("cnc_machine", "robotic_arm", "industrial_turbine")

        for cs in cooling_machines:
            if cs.current_anomaly == AnomalyType.NONE and cs.degradation_level < 0.3:
                continue

            severity = max(cs.anomaly_severity, cs.degradation_level)
            temp_bump = severity * 8.0  # up to +8 °C per tick at max severity

            for atype in affected_types:
                for target in self._by_type.get(atype, []):
                    if hasattr(target, "temperature"):
                        target.temperature += temp_bump
                    if hasattr(target, "motor_temperature"):
                        target.motor_temperature += temp_bump

            if severity > 0.5:
                logger.warning(
                    f"[CORRELATION] Cooling failure ({cs.machine_id}) "
                    f"affecting CNC/Arm/Turbine cluster  temp_bump=+{temp_bump:.1f}°C"
                )

    def _turbine_vibration_chain(self) -> None:
        """
        High turbine vibration → energy-output loss + elevated heat
        on welding units and conveyor motors (power-grid dependency).
        """
        turbines = self._by_type.get("industrial_turbine", [])
        power_dependents = ("welding_unit", "conveyor_motor")

        for turb in turbines:
            if turb.current_anomaly != AnomalyType.VIBRATION_ANOMALY:
                continue
            sev = turb.anomaly_severity
            for dtype in power_dependents:
                for dep in self._by_type.get(dtype, []):
                    if hasattr(dep, "temperature"):
                        dep.temperature += sev * 4.0
                    if hasattr(dep, "power_consumption"):
                        dep.power_consumption += sev * 1.5
                    if hasattr(dep, "energy_usage"):
                        dep.energy_usage += sev * 2.0

            if sev > 0.4:
                logger.warning(
                    f"[CORRELATION] Turbine vibration ({turb.machine_id}) "
                    f"degrading power grid  severity={sev:.2f}"
                )

    def _cnc_tool_wear_chain(self) -> None:
        """
        Excessive CNC tool wear → vibration increases → spindle
        instability → machining accuracy impact on downstream
        assembly robots.
        """
        cnc_machines = self._by_type.get("cnc_machine", [])
        assembly_robots = self._by_type.get("assembly_robot", [])

        for cnc in cnc_machines:
            if cnc.current_anomaly != AnomalyType.EXCESSIVE_TOOL_WEAR:
                continue
            sev = cnc.anomaly_severity
            # Feed-through to assembly accuracy
            for ar in assembly_robots:
                if hasattr(ar, "alignment_accuracy"):
                    ar.alignment_accuracy -= sev * 1.5
                if hasattr(ar, "cycle_efficiency"):
                    ar.cycle_efficiency -= sev * 2.0

            if sev > 0.5:
                logger.warning(
                    f"[CORRELATION] CNC tool-wear ({cnc.machine_id}) "
                    f"impacting assembly robot accuracy  severity={sev:.2f}"
                )

    def _robotic_arm_overload_chain(self) -> None:
        """
        Overloaded robotic arms → motor heat → movement-delay increase
        → positional accuracy drop (self-cascading within the machine).
        Also affects conveyor throughput when arms are misaligned.
        """
        arms = self._by_type.get("robotic_arm", [])
        conveyors = self._by_type.get("conveyor_motor", [])

        for arm in arms:
            if arm.degradation_level < 0.4 and arm.current_anomaly == AnomalyType.NONE:
                continue
            sev = max(arm.anomaly_severity, arm.degradation_level)
            # Slight RPM dip on conveyors awaiting parts
            for conv in conveyors:
                if hasattr(conv, "rpm"):
                    conv.rpm -= sev * 30.0

            if sev > 0.6:
                logger.warning(
                    f"[CORRELATION] Robotic arm overload ({arm.machine_id}) "
                    f"throttling conveyor throughput  severity={sev:.2f}"
                )
