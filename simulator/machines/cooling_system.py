from typing import Dict, Any, List
from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.schemas import CoolingSystemTelemetry
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.helpers import get_current_timestamp, random_fluctuation

class CoolingSystem(BaseMachine):
    def __init__(self, machine_id: str):
        super().__init__(machine_id)
        self.coolant_flow_rate = 100.0 # L/min
        self.temperature = 20.0
        self.pressure = 50.0 # PSI

    @property
    def machine_type(self) -> str:
        return "cooling_system"

    @property
    def possible_anomalies(self) -> List[AnomalyType]:
        return [AnomalyType.PRESSURE_FLUCTUATION, AnomalyType.COOLANT_REDUCTION]

    def _update_telemetry_state(self):
        self.coolant_flow_rate = random_fluctuation(100.0, 0.02)
        self.temperature = random_fluctuation(20.0, 0.05)
        self.pressure = random_fluctuation(50.0, 0.02)

        self.temperature += self.degradation_level * 15.0
        self.coolant_flow_rate -= self.degradation_level * 10.0

        if self.current_anomaly == AnomalyType.PRESSURE_FLUCTUATION:
            self.pressure = random_fluctuation(50.0, 0.1 + self.anomaly_severity * 0.2)
            self.temperature += self.anomaly_severity * 10.0
        elif self.current_anomaly == AnomalyType.COOLANT_REDUCTION:
            self.coolant_flow_rate -= self.anomaly_severity * 40.0
            self.temperature += self.anomaly_severity * 25.0

    def generate_telemetry(self) -> Dict[str, Any]:
        payload = CoolingSystemTelemetry(
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            status=self.status,
            timestamp=get_current_timestamp(),
            coolant_flow_rate=round(self.coolant_flow_rate, 2),
            temperature=round(self.temperature, 2),
            pressure=round(self.pressure, 2)
        )
        return payload.to_dict()
