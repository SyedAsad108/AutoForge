from typing import Dict, Any, List
from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.schemas import WeldingUnitTelemetry
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.helpers import get_current_timestamp, random_fluctuation

class WeldingUnit(BaseMachine):
    def __init__(self, machine_id: str):
        super().__init__(machine_id)
        self.arc_stability = 98.0 # %
        self.temperature = 150.0
        self.energy_usage = 12.0 # kW

    @property
    def machine_type(self) -> str:
        return "welding_unit"

    @property
    def possible_anomalies(self) -> List[AnomalyType]:
        return [AnomalyType.UNSTABLE_ARC, AnomalyType.ENERGY_SPIKE]

    def _update_telemetry_state(self):
        self.arc_stability = random_fluctuation(98.0, 0.01)
        self.temperature = random_fluctuation(150.0, 0.05)
        self.energy_usage = random_fluctuation(12.0, 0.02)

        self.temperature += self.degradation_level * 50.0
        self.arc_stability -= self.degradation_level * 10.0

        if self.current_anomaly == AnomalyType.UNSTABLE_ARC:
            self.arc_stability = random_fluctuation(98.0, 0.1 + self.anomaly_severity * 0.3)
            self.temperature += self.anomaly_severity * 30.0
        elif self.current_anomaly == AnomalyType.ENERGY_SPIKE:
            self.energy_usage += self.anomaly_severity * 8.0
            self.temperature += self.anomaly_severity * 40.0

    def generate_telemetry(self) -> Dict[str, Any]:
        payload = WeldingUnitTelemetry(
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            status=self.status,
            timestamp=get_current_timestamp(),
            arc_stability=round(self.arc_stability, 2),
            temperature=round(self.temperature, 2),
            energy_usage=round(self.energy_usage, 2)
        )
        return payload.to_dict()
