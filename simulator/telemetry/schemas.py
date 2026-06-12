from dataclasses import dataclass, asdict
from typing import Any, Dict

@dataclass
class TelemetryPayload:
    machine_id: str
    machine_type: str
    status: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ConveyorMotorTelemetry(TelemetryPayload):
    rpm: float
    temperature: float
    power_consumption: float

@dataclass
class HydraulicPressTelemetry(TelemetryPayload):
    hydraulic_pressure: float
    temperature: float
    cycle_time: float

@dataclass
class CNCMachineTelemetry(TelemetryPayload):
    spindle_speed: float
    temperature: float
    tool_wear: float
    vibration: float

@dataclass
class RoboticArmTelemetry(TelemetryPayload):
    joint_load: float
    movement_delay: float
    motor_temperature: float
    positional_accuracy: float

@dataclass
class TurbineTelemetry(TelemetryPayload):
    rpm: float
    vibration: float
    temperature: float
    energy_output: float

@dataclass
class CoolingSystemTelemetry(TelemetryPayload):
    coolant_flow_rate: float
    temperature: float
    pressure: float

@dataclass
class WeldingUnitTelemetry(TelemetryPayload):
    arc_stability: float
    temperature: float
    energy_usage: float

@dataclass
class AssemblyRobotTelemetry(TelemetryPayload):
    task_completion_rate: float
    alignment_accuracy: float
    cycle_efficiency: float
    temperature: float
