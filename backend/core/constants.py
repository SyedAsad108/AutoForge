"""
Constants for the AutoForge Backend Ingestion API.
"""

# Valid machine types matching the simulator
VALID_MACHINE_TYPES = frozenset({
    "conveyor_motor",
    "hydraulic_press",
    "cnc_machine",
    "robotic_arm",
    "industrial_turbine",
    "cooling_system",
    "welding_unit",
    "assembly_robot",
})

# Valid status values
VALID_STATUSES = frozenset({"healthy", "warning", "critical", "offline"})

# Valid anomaly types (from Phase 1 AnomalyType enum)
VALID_ANOMALY_TYPES = frozenset({
    None,
    "none",
    "overheating",
    "unstable_rpm",
    "pressure_drop",
    "excessive_tool_wear",
    "vibration_anomaly",
    "motor_overheating",
    "movement_delay_spike",
    "pressure_fluctuation",
    "coolant_reduction",
    "unstable_arc",
    "energy_spike",
    "alignment_degradation",
    "efficiency_drop",
})

# ---------------------------------------------------------------------------
# Per-machine-type telemetry range constraints
# Each entry: {field_name: (min, max)}
# ---------------------------------------------------------------------------
TELEMETRY_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    "conveyor_motor": {
        "rpm": (0, 5000),
        "temperature": (-10, 250),
        "power_consumption": (0, 50),
    },
    "hydraulic_press": {
        "hydraulic_pressure": (0, 6000),
        "temperature": (-10, 250),
        "cycle_time": (0, 120),
    },
    "cnc_machine": {
        "spindle_speed": (0, 20000),
        "temperature": (-10, 250),
        "tool_wear": (0, 100),
        "vibration": (0, 50),
    },
    "robotic_arm": {
        "joint_load": (0, 200),
        "movement_delay": (0, 10),
        "motor_temperature": (-10, 250),
        "positional_accuracy": (0, 100),
    },
    "industrial_turbine": {
        "rpm": (0, 25000),
        "vibration": (0, 50),
        "temperature": (-10, 400),
        "energy_output": (0, 2000),
    },
    "cooling_system": {
        "coolant_flow_rate": (0, 500),
        "temperature": (-30, 100),
        "pressure": (0, 200),
    },
    "welding_unit": {
        "arc_stability": (0, 100),
        "temperature": (0, 500),
        "energy_usage": (0, 100),
    },
    "assembly_robot": {
        "task_completion_rate": (0, 200),
        "alignment_accuracy": (0, 100),
        "cycle_efficiency": (0, 100),
        "temperature": (-10, 200),
    },
}
