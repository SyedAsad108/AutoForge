from typing import Dict, Any, List
from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.schemas import RoboticArmTelemetry
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.helpers import get_current_timestamp, random_fluctuation

class RoboticArm(BaseMachine):
    def __init__(self, machine_id: str):
        super().__init__(machine_id)
        self.joint_load = 50.0 # kg
        self.movement_delay = 0.5 # ms
        self.motor_temperature = 40.0
        self.positional_accuracy = 99.9 # %

    @property
    def machine_type(self) -> str:
        return "robotic_arm"

    @property
    def possible_anomalies(self) -> List[AnomalyType]:
        return [AnomalyType.MOTOR_OVERHEATING, AnomalyType.MOVEMENT_DELAY_SPIKE]

    def _update_telemetry_state(self):
        self.joint_load = random_fluctuation(50.0, 0.1)
        self.movement_delay = random_fluctuation(0.5, 0.05)
        self.motor_temperature = random_fluctuation(40.0, 0.05)
        self.positional_accuracy = random_fluctuation(99.9, 0.001)

        self.motor_temperature += self.degradation_level * 20.0
        self.movement_delay += self.degradation_level * 0.5
        self.positional_accuracy -= self.degradation_level * 2.0

        if self.current_anomaly == AnomalyType.MOTOR_OVERHEATING:
            self.motor_temperature += self.anomaly_severity * 50.0
            self.joint_load += self.anomaly_severity * 10.0
        elif self.current_anomaly == AnomalyType.MOVEMENT_DELAY_SPIKE:
            self.movement_delay += self.anomaly_severity * 2.0
            self.positional_accuracy -= self.anomaly_severity * 5.0

    def generate_telemetry(self) -> Dict[str, Any]:
        payload = RoboticArmTelemetry(
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            status=self.status,
            timestamp=get_current_timestamp(),
            joint_load=round(self.joint_load, 2),
            movement_delay=round(self.movement_delay, 3),
            motor_temperature=round(self.motor_temperature, 2),
            positional_accuracy=round(self.positional_accuracy, 2)
        )
        return payload.to_dict()
