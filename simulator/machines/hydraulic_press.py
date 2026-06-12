from typing import Dict, Any, List
from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.schemas import HydraulicPressTelemetry
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.helpers import get_current_timestamp, random_fluctuation

class HydraulicPress(BaseMachine):
    def __init__(self, machine_id: str):
        super().__init__(machine_id)
        self.hydraulic_pressure = 3000.0 # PSI
        self.temperature = 50.0
        self.cycle_time = 12.0 # seconds

    @property
    def machine_type(self) -> str:
        return "hydraulic_press"

    @property
    def possible_anomalies(self) -> List[AnomalyType]:
        return [AnomalyType.PRESSURE_DROP, AnomalyType.OVERHEATING]

    def _update_telemetry_state(self):
        self.hydraulic_pressure = random_fluctuation(3000.0, 0.01)
        self.temperature = random_fluctuation(50.0, 0.02)
        self.cycle_time = random_fluctuation(12.0, 0.05)

        self.temperature += self.degradation_level * 25.0
        self.cycle_time += self.degradation_level * 3.0

        if self.current_anomaly == AnomalyType.PRESSURE_DROP:
            self.hydraulic_pressure -= self.anomaly_severity * 1000.0
            self.cycle_time += self.anomaly_severity * 5.0
        elif self.current_anomaly == AnomalyType.OVERHEATING:
            self.temperature += self.anomaly_severity * 50.0

    def generate_telemetry(self) -> Dict[str, Any]:
        payload = HydraulicPressTelemetry(
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            status=self.status,
            timestamp=get_current_timestamp(),
            hydraulic_pressure=round(self.hydraulic_pressure, 2),
            temperature=round(self.temperature, 2),
            cycle_time=round(self.cycle_time, 2)
        )
        return payload.to_dict()
