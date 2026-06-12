"""
Knowledge base and rule definitions for rule-based industrial diagnostics.
Phase 9.5 - AutoForge Smart Manufacturing Platform
"""

from typing import Dict, Any, List

# Basic threshold expectations for each metric to calculate evidence
EXPECTED_RANGES = {
    "temperature": "10.0 - 75.0 °C",
    "motor_temperature": "10.0 - 75.0 °C",
    "rpm": "1000 - 5000 RPM",
    "spindle_speed": "1000 - 6000 RPM",
    "vibration": "0.0 - 5.0 mm/s",
    "tool_wear": "0.0 - 60.0 %",
    "hydraulic_pressure": "2000.0 - 5000.0 PSI",
    "pressure": "5.0 - 20.0 Bar",
    "coolant_flow_rate": "10.0 - 100.0 L/min",
    "power_consumption": "5.0 - 120.0 kW",
    "energy_usage": "10.0 - 150.0 kW",
    "arc_stability": "85.0 - 100.0 %",
    "movement_delay": "0.0 - 2.0 s",
    "alignment_accuracy": "95.0 - 100.0 %",
    "cycle_efficiency": "85.0 - 100.0 %",
    "task_completion_rate": "90.0 - 100.0 %"
}

# Mapping of raw anomaly types to human-readable details
DIAGNOSTIC_CATALOG = {
    "overheating": {
        "reason": "Machine temperature exceeded safe thermal operating threshold.",
        "trigger_metric": "temperature",
        "expected_range": EXPECTED_RANGES["temperature"],
        "default_causes": [
            {"cause": "Cooling System Degradation", "prob": 0.50},
            {"cause": "Blocked Vents / Airflow Path", "prob": 0.30},
            {"cause": "Mechanical Bearing Friction", "prob": 0.20}
        ],
        "default_actions": [
            "Inspect cooling subsystem fluid levels and pump",
            "Verify exhaust fans and clean air intake paths",
            "Perform thermal imaging on active motor shafts"
        ]
    },
    "motor_overheating": {
        "reason": "Robotic joint coil temperature breached safe thermal limits.",
        "trigger_metric": "motor_temperature",
        "expected_range": EXPECTED_RANGES["motor_temperature"],
        "default_causes": [
            {"cause": "Actuator Internal Short / Electrical Fault", "prob": 0.40},
            {"cause": "Joint Lubrication Starvation", "prob": 0.40},
            {"cause": "Excessive Joint Physical Overload", "prob": 0.20}
        ],
        "default_actions": [
            "Verify current draw on motor coils",
            "Apply high-pressure joint grease to active gears",
            "Audit robotic program payload weights"
        ]
    },
    "unstable_rpm": {
        "reason": "Rotational velocity fluctuated outside nominal safety limits.",
        "trigger_metric": "rpm",
        "expected_range": EXPECTED_RANGES["rpm"],
        "default_causes": [
            {"cause": "Drive Belt Slippage", "prob": 0.45},
            {"cause": "Tachometer Feedback Signal Noise", "prob": 0.35},
            {"cause": "VFD Regulator Failure", "prob": 0.20}
        ],
        "default_actions": [
            "Inspect and retension motor drive belts",
            "Clean rotary encoder optical sensor surfaces",
            "Verify VFD voltage output stability"
        ]
    },
    "pressure_drop": {
        "reason": "Hydraulic cylinder pressure dropped below minimum active thresholds.",
        "trigger_metric": "hydraulic_pressure",
        "expected_range": EXPECTED_RANGES["hydraulic_pressure"],
        "default_causes": [
            {"cause": "Hydraulic Line Fluid Leakage", "prob": 0.50},
            {"cause": "Main Pump Cavitation", "prob": 0.30},
            {"cause": "Manifold Pressure Relief Valve Failure", "prob": 0.20}
        ],
        "default_actions": [
            "Perform pressure decay leak test on high-pressure hoses",
            "Check hydraulic fluid tank levels and filter color",
            "Verify pilot-operated valve release spring tension"
        ]
    },
    "coolant_reduction": {
        "reason": "Coolant flow rate degraded below required cooling thresholds.",
        "trigger_metric": "coolant_flow_rate",
        "expected_range": EXPECTED_RANGES["coolant_flow_rate"],
        "default_causes": [
            {"cause": "Impeller / Pump Internal Blockage", "prob": 0.45},
            {"cause": "Flow Path Tube Blockage", "prob": 0.35},
            {"cause": "Gasket Failure at Valve Seals", "prob": 0.20}
        ],
        "default_actions": [
            "Flush cooling pipeline to clear calcification",
            "Verify coolant pump impeller current draw",
            "Inspect control valve seals for leakage"
        ]
    },
    "vibration_anomaly": {
        "reason": "Vibrational harmonics indicate structural mechanical imbalance.",
        "trigger_metric": "vibration",
        "expected_range": EXPECTED_RANGES["vibration"],
        "default_causes": [
            {"cause": "Spindle Shaft Misalignment", "prob": 0.45},
            {"cause": "Loose Base Mounting Anchor Bolts", "prob": 0.35},
            {"cause": "Internal Bearing Ball Pitting", "prob": 0.20}
        ],
        "default_actions": [
            "Perform dual-axis dial indicator laser alignment",
            "Retighten structural base anchor bolts to spec",
            "Conduct ultrasound acoustic bearing check"
        ]
    },
    "excessive_tool_wear": {
        "reason": "Spindle bit degradation exceeded nominal safety wear profiles.",
        "trigger_metric": "tool_wear",
        "expected_range": EXPECTED_RANGES["tool_wear"],
        "default_causes": [
            {"cause": "Sub-optimal Feed/Speed Ratio", "prob": 0.50},
            {"cause": "Part Material Hardness Out-of-Spec", "prob": 0.30},
            {"cause": "Micro-chipping from Insufficient Fluid", "prob": 0.20}
        ],
        "default_actions": [
            "Adjust cutting feed rate down by 15%",
            "Verify batch hardness certificate of raw stock",
            "Flush flood coolant nozzle path to clear chips"
        ]
    },
    "movement_delay_spike": {
        "reason": "Axis positioning delay exceeded path interpolation thresholds.",
        "trigger_metric": "movement_delay",
        "expected_range": EXPECTED_RANGES["movement_delay"],
        "default_causes": [
            {"cause": "Guideway Friction / Lack of Lubrication", "prob": 0.50},
            {"cause": "Servo Torque Current Limiting", "prob": 0.30},
            {"cause": "EtherCAT Bus Sync Packet Loss", "prob": 0.20}
        ],
        "default_actions": [
            "Run automated guideway lubricating sequence",
            "Inspect linear guide rails for physical debris",
            "Verify network cable shielding integrity"
        ]
    },
    "unstable_arc": {
        "reason": "Welding voltage current arc stability dropped below quality criteria.",
        "trigger_metric": "arc_stability",
        "expected_range": EXPECTED_RANGES["arc_stability"],
        "default_causes": [
            {"cause": "Electrode Tip Contamination", "prob": 0.45},
            {"cause": "Shielding Gas Flow Disruption", "prob": 0.35},
            {"cause": "Wire Feeder Tension Variance", "prob": 0.20}
        ],
        "default_actions": [
            "Perform automatic contact tip replacement",
            "Inspect gas nozzle for weld spatter buildup",
            "Check wire spool tension regulator setting"
        ]
    },
    "energy_spike": {
        "reason": "Welder power consumption peaked above maximum safety parameters.",
        "trigger_metric": "energy_usage",
        "expected_range": EXPECTED_RANGES["energy_usage"],
        "default_causes": [
            {"cause": "High-Resistance Short to Ground", "prob": 0.40},
            {"cause": "Transformer Inductance Overload", "prob": 0.40},
            {"cause": "Electrical Input Grid Surge", "prob": 0.20}
        ],
        "default_actions": [
            "Perform insulation megohmmeter wire test",
            "Inspect contactor relays for carbon arc pitting",
            "Install transient surge suppression module"
        ]
    },
    "alignment_degradation": {
        "reason": "Robotic end-effector alignment accuracy drifted outside tolerance.",
        "trigger_metric": "alignment_accuracy",
        "expected_range": EXPECTED_RANGES["alignment_accuracy"],
        "default_causes": [
            {"cause": "Joint Backlash Drift", "prob": 0.40},
            {"cause": "Thermal Expansion of Tool Bracket", "prob": 0.35},
            {"cause": "Gripper Mechanical Wear", "prob": 0.25}
        ],
        "default_actions": [
            "Execute robotic joint calibration sweep",
            "Verify bracket assembly bolt torque settings",
            "Replace worn rubber gripper pads"
        ]
    },
    "efficiency_drop": {
        "reason": "Robot assembly cycle efficiency dropped below required standards.",
        "trigger_metric": "cycle_efficiency",
        "expected_range": EXPECTED_RANGES["cycle_efficiency"],
        "default_causes": [
            {"cause": "Minor Stop Occurrences / Sensor Stalls", "prob": 0.50},
            {"cause": "Part Supply Starvation Delay", "prob": 0.30},
            {"cause": "Motor Friction Load Increase", "prob": 0.20}
        ],
        "default_actions": [
            "Audit photoelectric proximity sensor alignment",
            "Adjust line buffer feed queue parameters",
            "Conduct joint friction force diagnostic"
        ]
    }
}

def get_anomaly_rules(anomaly_type: str) -> Dict[str, Any]:
    """Retrieve diagnostic rules template for an anomaly type."""
    return DIAGNOSTIC_CATALOG.get(anomaly_type, {
        "reason": "Machine metrics drifted beyond safe operational envelopes.",
        "trigger_metric": "temperature",
        "expected_range": "N/A",
        "default_causes": [{"cause": "General Mechanical Degradation", "prob": 1.0}],
        "default_actions": ["Conduct general preventative inspection"]
    })
