from typing import Dict, Any, List
from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.schemas import TurbineTelemetry
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.helpers import get_current_timestamp, random_fluctuation

class IndustrialTurbine(BaseMachine):
    def __init__(self, machine_id: str):
        super().__init__(machine_id)
        self.rpm = 12000.0
        self.vibration = 1.0 # mm/s
        self.temperature = 80.0
        self.energy_output = 500.0 # kW

    @property
    def machine_type(self) -> str:
        return "industrial_turbine"

    @property
    def possible_anomalies(self) -> List[AnomalyType]:
        return [AnomalyType.UNSTABLE_RPM, AnomalyType.VIBRATION_ANOMALY]

    def _update_telemetry_state(self):
        self.rpm = random_fluctuation(12000.0, 0.01)
        self.vibration = random_fluctuation(1.0, 0.05)
        self.temperature = random_fluctuation(80.0, 0.02)
        self.energy_output = random_fluctuation(500.0, 0.01)

        self.temperature += self.degradation_level * 40.0
        self.vibration += self.degradation_level * 2.0
        self.energy_output -= self.degradation_level * 50.0

        if self.current_anomaly == AnomalyType.UNSTABLE_RPM:
            self.rpm = random_fluctuation(12000.0, 0.1 + self.anomaly_severity * 0.1)
            self.energy_output -= self.anomaly_severity * 100.0
        elif self.current_anomaly == AnomalyType.VIBRATION_ANOMALY:
            self.vibration += self.anomaly_severity * 5.0
            self.temperature += self.anomaly_severity * 30.0

    def generate_telemetry(self) -> Dict[str, Any]:
        payload = TurbineTelemetry(
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            status=self.status,
            timestamp=get_current_timestamp(),
            rpm=round(self.rpm, 2),
            vibration=round(self.vibration, 2),
            temperature=round(self.temperature, 2),
            energy_output=round(self.energy_output, 2)
        )
        return payload.to_dict()
