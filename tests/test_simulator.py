import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.machines.conveyor_motor import ConveyorMotor
from simulator.utils.constants import STATUS_HEALTHY, STATUS_WARNING, STATUS_CRITICAL
from simulator.telemetry.anomalies import AnomalyType

def test_machine_initialization():
    motor = ConveyorMotor("M001")
    assert motor.machine_id == "M001"
    assert motor.status == STATUS_HEALTHY
    assert motor.degradation_level == 0.0

def test_telemetry_schema():
    motor = ConveyorMotor("M001")
    telemetry = motor.generate_telemetry()
    assert "machine_id" in telemetry
    assert "rpm" in telemetry
    assert telemetry["machine_id"] == "M001"

def test_anomaly_injection():
    motor = ConveyorMotor("M001")
    motor.current_anomaly = AnomalyType.OVERHEATING
    motor.anomaly_severity = 0.5
    
    # State update should apply anomaly effects
    motor.update_state()
    
    assert motor.anomaly_severity > 0.5 # Severity increases
    
    telemetry = motor.generate_telemetry()
    assert telemetry["temperature"] > 45.0 # Base temperature was 45.0

def test_status_transition():
    motor = ConveyorMotor("M001")
    
    # Force degradation to trigger warning
    motor.degradation_level = 0.50
    motor._evaluate_status()
    assert motor.status == STATUS_WARNING
    
    # Force degradation to trigger critical
    motor.degradation_level = 0.85
    motor._evaluate_status()
    assert motor.status == STATUS_CRITICAL

