from typing import Dict, Any, List
from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.schemas import ConveyorMotorTelemetry
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.helpers import get_current_timestamp, random_fluctuation

class ConveyorMotor(BaseMachine):
    def __init__(self, machine_id: str):
        super().__init__(machine_id)
        self.rpm = 1500.0
        self.temperature = 45.0
        self.power_consumption = 5.0

    @property
    def machine_type(self) -> str:
        return "conveyor_motor"

    @property
    def possible_anomalies(self) -> List[AnomalyType]:
        return [AnomalyType.OVERHEATING, AnomalyType.UNSTABLE_RPM]

    def _update_telemetry_state(self):
        # Base fluctuations
        self.rpm = random_fluctuation(1500.0, 0.02)
        self.temperature = random_fluctuation(45.0, 0.05)
        self.power_consumption = random_fluctuation(5.0, 0.05)

        # Degradation effects
        self.temperature += self.degradation_level * 20.0
        self.power_consumption += self.degradation_level * 2.0

        # Anomaly effects
        if self.current_anomaly == AnomalyType.OVERHEATING:
            self.temperature += self.anomaly_severity * 60.0
            self.power_consumption += self.anomaly_severity * 3.0
        elif self.current_anomaly == AnomalyType.UNSTABLE_RPM:
            self.rpm = random_fluctuation(1500.0 - (self.anomaly_severity * 500), 0.1 + self.anomaly_severity * 0.2)
            self.temperature += self.anomaly_severity * 20.0

    def generate_telemetry(self) -> Dict[str, Any]:
        payload = ConveyorMotorTelemetry(
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            status=self.status,
            timestamp=get_current_timestamp(),
            rpm=round(self.rpm, 2),
            temperature=round(self.temperature, 2),
            power_consumption=round(self.power_consumption, 2)
        )
        return payload.to_dict()
