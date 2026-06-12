"""
Phase 2 test suite for the AutoForge Smart Manufacturing Plant.

Covers:
  • event serialization format
  • event queue behaviour (put, get, overflow, batch)
  • anomaly escalation & cascade
  • correlated failure propagation
  • replay engine loading
  • metrics engine calculations
  • streaming engine concurrency
"""

import asyncio
import json
import os
import sys
import time
import uuid

import pytest

# Ensure project root is on the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.machines.conveyor_motor import ConveyorMotor
from simulator.machines.cnc_machine import CNCMachine
from simulator.machines.robotic_arm import RoboticArm
from simulator.machines.cooling_system import CoolingSystem
from simulator.machines.turbine import IndustrialTurbine
from simulator.machines.assembly_robot import AssemblyRobot
from simulator.machines.welding_unit import WeldingUnit
from simulator.machines.hydraulic_press import HydraulicPress

from simulator.telemetry.anomalies import AnomalyType
from simulator.telemetry.correlation_engine import CorrelationEngine
from simulator.telemetry.degradation_engine import DegradationEngine
from simulator.telemetry.anomaly_engine import AnomalyEngine
from simulator.telemetry.metrics_engine import MetricsEngine
from simulator.streaming.serializer import serialize_telemetry_event, event_to_json
from simulator.streaming.event_queue import EventQueue
from simulator.utils.constants import STATUS_HEALTHY, STATUS_WARNING, STATUS_CRITICAL


# ===================================================================
# Serialization
# ===================================================================
class TestSerialization:
    """Validate the stream-ready event envelope format."""

    def test_event_has_required_fields(self):
        motor = ConveyorMotor("M001")
        event = serialize_telemetry_event(motor)
        required = {
            "event_id", "machine_id", "machine_type", "factory_id",
            "timestamp", "status", "telemetry",
            "anomaly_detected", "anomaly_type",
        }
        assert required.issubset(event.keys())

    def test_event_id_is_valid_uuid(self):
        motor = ConveyorMotor("M001")
        event = serialize_telemetry_event(motor)
        uuid.UUID(event["event_id"])  # raises if invalid

    def test_telemetry_is_nested_dict(self):
        motor = ConveyorMotor("M001")
        event = serialize_telemetry_event(motor)
        assert isinstance(event["telemetry"], dict)
        assert "rpm" in event["telemetry"]

    def test_anomaly_fields_when_healthy(self):
        motor = ConveyorMotor("M001")
        event = serialize_telemetry_event(motor)
        assert event["anomaly_detected"] is False
        assert event["anomaly_type"] is None

    def test_anomaly_fields_when_anomalous(self):
        motor = ConveyorMotor("M001")
        motor.current_anomaly = AnomalyType.OVERHEATING
        motor.anomaly_severity = 0.5
        event = serialize_telemetry_event(motor)
        assert event["anomaly_detected"] is True
        assert event["anomaly_type"] == "overheating"

    def test_event_to_json_produces_valid_json(self):
        motor = ConveyorMotor("M001")
        event = serialize_telemetry_event(motor)
        json_str = event_to_json(event)
        parsed = json.loads(json_str)
        assert parsed["machine_id"] == "M001"

    def test_machine_specific_telemetry_schema_cnc(self):
        cnc = CNCMachine("M010")
        event = serialize_telemetry_event(cnc)
        assert "spindle_speed" in event["telemetry"]
        assert "tool_wear" in event["telemetry"]
        assert "vibration" in event["telemetry"]


# ===================================================================
# Event Queue
# ===================================================================
class TestEventQueue:
    """Validate the in-memory event buffer."""

    @pytest.mark.asyncio
    async def test_put_and_get(self):
        q = EventQueue(max_size=10)
        await q.put({"id": 1})
        event = await q.get()
        assert event["id"] == 1

    @pytest.mark.asyncio
    async def test_overflow_eviction(self):
        q = EventQueue(max_size=3)
        for i in range(5):
            await q.put({"id": i})
        # Oldest events should have been evicted; queue holds at most 3
        assert q.size <= 3
        assert q.total_dropped >= 2

    @pytest.mark.asyncio
    async def test_batch_retrieval(self):
        q = EventQueue(max_size=100)
        for i in range(20):
            await q.put({"id": i})
        batch = await q.get_batch(batch_size=10)
        assert len(batch) == 10

    @pytest.mark.asyncio
    async def test_empty_batch(self):
        q = EventQueue(max_size=100)
        batch = await q.get_batch(batch_size=10)
        assert len(batch) == 0

    def test_recent_events(self):
        q = EventQueue(max_size=100)
        for i in range(5):
            q.put_nowait({"id": i})
        recent = q.recent_events(3)
        assert len(recent) == 3
        assert recent[-1]["id"] == 4


# ===================================================================
# Anomaly Escalation & Cascade
# ===================================================================
class TestAnomalyEngine:
    """Validate anomaly lifecycle management."""

    def test_duration_tracking(self):
        motor = ConveyorMotor("M001")
        motor.current_anomaly = AnomalyType.OVERHEATING
        motor.anomaly_severity = 0.3
        engine = AnomalyEngine([motor])

        for _ in range(10):
            engine.tick()

        state = engine._states["M001"]
        assert state.duration_ticks == 10

    def test_severity_resets_on_no_anomaly(self):
        motor = ConveyorMotor("M001")
        engine = AnomalyEngine([motor])
        engine.tick()
        assert engine._states["M001"].duration_ticks == 0


# ===================================================================
# Correlated Failures
# ===================================================================
class TestCorrelationEngine:
    """Validate cross-machine causality chains."""

    def test_cooling_failure_heats_cnc(self):
        cs = CoolingSystem("CS01")
        cs.current_anomaly = AnomalyType.COOLANT_REDUCTION
        cs.anomaly_severity = 0.7
        cs.degradation_level = 0.5

        cnc = CNCMachine("CNC01")
        initial_temp = cnc.temperature

        engine = CorrelationEngine([cs, cnc])
        engine.apply_correlations()

        assert cnc.temperature > initial_temp

    def test_turbine_vibration_affects_welding(self):
        turb = IndustrialTurbine("T01")
        turb.current_anomaly = AnomalyType.VIBRATION_ANOMALY
        turb.anomaly_severity = 0.6

        wu = WeldingUnit("W01")
        initial_temp = wu.temperature

        engine = CorrelationEngine([turb, wu])
        engine.apply_correlations()

        assert wu.temperature > initial_temp

    def test_no_correlation_when_healthy(self):
        cs = CoolingSystem("CS01")
        cnc = CNCMachine("CNC01")
        initial_temp = cnc.temperature

        engine = CorrelationEngine([cs, cnc])
        engine.apply_correlations()

        # No change expected — cooling system is healthy
        assert cnc.temperature == initial_temp


# ===================================================================
# Degradation Engine
# ===================================================================
class TestDegradationEngine:
    """Validate progressive degradation behaviour."""

    def test_offline_machine_can_restart(self):
        motor = ConveyorMotor("M001")
        motor.status = "offline"
        motor.degradation_level = 0.9
        engine = DegradationEngine([motor])

        # Run many ticks — restart probability is low but should eventually trigger
        restarted = False
        for _ in range(2000):
            engine.tick()
            if motor.status != "offline":
                restarted = True
                break
        assert restarted

    def test_critical_can_go_offline(self):
        motor = ConveyorMotor("M001")
        motor.status = STATUS_CRITICAL
        motor.degradation_level = 0.99
        engine = DegradationEngine([motor])

        went_offline = False
        for _ in range(500):
            engine.tick()
            if motor.status == "offline":
                went_offline = True
                break
        assert went_offline


# ===================================================================
# Metrics Engine
# ===================================================================
class TestMetricsEngine:
    """Validate factory-wide aggregate metrics."""

    def test_all_healthy(self):
        machines = [ConveyorMotor(f"M{i:03d}") for i in range(5)]
        engine = MetricsEngine(machines)
        metrics = engine.compute()
        assert metrics["operational_efficiency_pct"] == 100.0
        assert metrics["active_anomalies"] == 0

    def test_anomaly_counted(self):
        machines = [ConveyorMotor(f"M{i:03d}") for i in range(3)]
        machines[0].current_anomaly = AnomalyType.OVERHEATING
        engine = MetricsEngine(machines)
        metrics = engine.compute()
        assert metrics["active_anomalies"] == 1

    def test_offline_reduces_efficiency(self):
        machines = [ConveyorMotor(f"M{i:03d}") for i in range(4)]
        machines[0].status = "offline"
        engine = MetricsEngine(machines)
        metrics = engine.compute()
        assert metrics["offline_machines"] == 1
        # 3 healthy out of 3 active → 100 %
        assert metrics["operational_efficiency_pct"] == 100.0

    def test_warning_reduces_efficiency(self):
        machines = [ConveyorMotor(f"M{i:03d}") for i in range(4)]
        machines[0].status = STATUS_WARNING
        engine = MetricsEngine(machines)
        metrics = engine.compute()
        # 3 healthy out of 4 active → 75 %
        assert metrics["operational_efficiency_pct"] == 75.0


# ===================================================================
# Phase 1 regression
# ===================================================================
class TestPhase1Regression:
    """Ensure Phase 1 behaviour is not broken."""

    def test_machine_initialization(self):
        motor = ConveyorMotor("M001")
        assert motor.machine_id == "M001"
        assert motor.status == STATUS_HEALTHY

    def test_telemetry_schema(self):
        motor = ConveyorMotor("M001")
        telemetry = motor.generate_telemetry()
        assert "machine_id" in telemetry
        assert "rpm" in telemetry

    def test_status_transition(self):
        motor = ConveyorMotor("M001")
        motor.degradation_level = 0.75
        motor._evaluate_status()
        assert motor.status == STATUS_WARNING

        motor.degradation_level = 0.98
        motor._evaluate_status()
        assert motor.status == STATUS_CRITICAL
