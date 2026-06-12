from typing import Dict, Any, List
from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.schemas import AssemblyRobotTelemetry
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.helpers import get_current_timestamp, random_fluctuation

class AssemblyRobot(BaseMachine):
    def __init__(self, machine_id: str):
        super().__init__(machine_id)
        self.task_completion_rate = 100.0 # units/hr
        self.alignment_accuracy = 99.5 # %
        self.cycle_efficiency = 98.0 # %
        self.temperature = 35.0

    @property
    def machine_type(self) -> str:
        return "assembly_robot"

    @property
    def possible_anomalies(self) -> List[AnomalyType]:
        return [AnomalyType.ALIGNMENT_DEGRADATION, AnomalyType.EFFICIENCY_DROP]

    def _update_telemetry_state(self):
        self.task_completion_rate = random_fluctuation(100.0, 0.01)
        self.alignment_accuracy = random_fluctuation(99.5, 0.002)
        self.cycle_efficiency = random_fluctuation(98.0, 0.01)
        self.temperature = random_fluctuation(35.0, 0.02)

        self.temperature += self.degradation_level * 15.0
        self.alignment_accuracy -= self.degradation_level * 5.0
        self.cycle_efficiency -= self.degradation_level * 10.0

        if self.current_anomaly == AnomalyType.ALIGNMENT_DEGRADATION:
            self.alignment_accuracy -= self.anomaly_severity * 15.0
            self.task_completion_rate -= self.anomaly_severity * 20.0
        elif self.current_anomaly == AnomalyType.EFFICIENCY_DROP:
            self.cycle_efficiency -= self.anomaly_severity * 30.0
            self.task_completion_rate -= self.anomaly_severity * 40.0
            self.temperature += self.anomaly_severity * 20.0

    def generate_telemetry(self) -> Dict[str, Any]:
        payload = AssemblyRobotTelemetry(
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            status=self.status,
            timestamp=get_current_timestamp(),
            task_completion_rate=round(self.task_completion_rate, 2),
            alignment_accuracy=round(self.alignment_accuracy, 2),
            cycle_efficiency=round(self.cycle_efficiency, 2),
            temperature=round(self.temperature, 2)
        )
        return payload.to_dict()
