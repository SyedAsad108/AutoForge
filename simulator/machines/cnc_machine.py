from typing import Dict, Any, List
from simulator.machines.base_machine import BaseMachine
from simulator.telemetry.schemas import CNCMachineTelemetry
from simulator.telemetry.anomalies import AnomalyType
from simulator.utils.helpers import get_current_timestamp, random_fluctuation

class CNCMachine(BaseMachine):
    def __init__(self, machine_id: str):
        super().__init__(machine_id)
        self.spindle_speed = 8000.0 # RPM
        self.temperature = 40.0
        self.tool_wear = 0.0 # 0 to 100%
        self.vibration = 2.0 # mm/s

    @property
    def machine_type(self) -> str:
        return "cnc_machine"

    @property
    def possible_anomalies(self) -> List[AnomalyType]:
        return [AnomalyType.EXCESSIVE_TOOL_WEAR, AnomalyType.VIBRATION_ANOMALY]

    def _update_telemetry_state(self):
        self.spindle_speed = random_fluctuation(8000.0, 0.01)
        self.temperature = random_fluctuation(40.0, 0.03)
        self.tool_wear += 0.01 # natural wear
        self.vibration = random_fluctuation(2.0, 0.1)

        self.temperature += self.degradation_level * 30.0
        self.tool_wear += self.degradation_level * 5.0
        self.vibration += self.degradation_level * 4.0

        if self.current_anomaly == AnomalyType.EXCESSIVE_TOOL_WEAR:
            self.tool_wear += self.anomaly_severity * 20.0
            self.temperature += self.anomaly_severity * 15.0
        elif self.current_anomaly == AnomalyType.VIBRATION_ANOMALY:
            self.vibration += self.anomaly_severity * 15.0
            self.spindle_speed = random_fluctuation(8000.0, 0.05 + self.anomaly_severity * 0.1)

        self.tool_wear = min(100.0, self.tool_wear)

    def generate_telemetry(self) -> Dict[str, Any]:
        payload = CNCMachineTelemetry(
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            status=self.status,
            timestamp=get_current_timestamp(),
            spindle_speed=round(self.spindle_speed, 2),
            temperature=round(self.temperature, 2),
            tool_wear=round(self.tool_wear, 2),
            vibration=round(self.vibration, 2)
        )
        return payload.to_dict()
