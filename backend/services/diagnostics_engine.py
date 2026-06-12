"""
Rule-based Industrial Diagnostics Engine.
Phase 9.5 - AutoForge Smart Manufacturing Platform
"""

from typing import Dict, Any, List
from backend.services.diagnostic_rules import get_anomaly_rules

def diagnose_telemetry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates telemetry payloads to enrich them with diagnostic metadata if an anomaly is detected.
    Ensures zero machine learning dependencies.
    """
    # 1. Initialize empty diagnostic fields by default
    diag_fields = {
        "anomaly_reason": None,
        "trigger_metric": None,
        "trigger_value": None,
        "expected_range": None,
        "root_cause_candidates": None,
        "recommended_actions": None,
        "diagnostic_confidence": 0.0
    }

    # If no anomaly is active, return payload with empty diagnostics
    if not payload.get("anomaly_detected"):
        return {**payload, **diag_fields}

    anomaly_type = payload.get("anomaly_type") or "unknown"
    telemetry = payload.get("telemetry", {})

    # 2. Get rule template
    rules = get_anomaly_rules(anomaly_type)
    trigger_metric = rules["trigger_metric"]
    trigger_value = telemetry.get(trigger_metric)

    # Fallback to check other fields if the configured metric is missing
    if trigger_value is None and telemetry:
        # Get first numeric value as fallback
        for k, v in telemetry.items():
            if isinstance(v, (int, float)):
                trigger_metric = k
                trigger_value = v
                break

    # 3. Apply correlation-based diagnostics rules
    temp = float(telemetry.get("temperature") or telemetry.get("motor_temperature") or 0.0)
    vib = float(telemetry.get("vibration") or 0.0)
    pressure = float(telemetry.get("pressure") or telemetry.get("hydraulic_pressure") or 0.0)
    flow = float(telemetry.get("coolant_flow_rate") or 100.0)  # assume nominal if not exists
    rpm_val = float(telemetry.get("rpm") or telemetry.get("spindle_speed") or 5000.0)
    power = float(telemetry.get("power_consumption") or telemetry.get("energy_usage") or 0.0)

    causes = list(rules["default_causes"])
    actions = list(rules["default_actions"])
    confidence = 0.60  # baseline confidence

    # RULE 1: High Temperature + High Vibration -> Bearing Wear
    if temp > 75.0 and vib > 15.0:
        causes = [
            {"cause": "Severe Bearing Wear & Lubrication Loss", "prob": 0.70},
            {"cause": "Spindle Shaft Misalignment", "prob": 0.20},
            {"cause": "Cooling System Degradation", "prob": 0.10}
        ]
        actions = [
            "Initiate immediate bearing grease injection",
            "Schedule dial-indicator laser shaft alignment check",
            "Verify fans and clean dust filters"
        ]
        confidence = 0.85

    # RULE 2: High Temperature + Low Pressure/Flow -> Cooling Failure
    elif temp > 75.0 and (pressure < 4.0 or flow < 15.0 or (anomaly_type == "pressure_drop" and pressure < 1800.0)):
        causes = [
            {"cause": "Cooling Subsystem Failure / Impeller Blockage", "prob": 0.75},
            {"cause": "Hydraulic Line Fluid Leakage", "prob": 0.15},
            {"cause": "Ambient Over-temperature Load", "prob": 0.10}
        ]
        actions = [
            "Shut down system, check impeller current and flush tubes",
            "Perform pressure decay test on line connections",
            "Verify coolant control valve opening ratio"
        ]
        confidence = 0.90

    # RULE 3: Low RPM + High Power Consumption -> Motor Degradation
    elif rpm_val < 900.0 and power > 120.0:
        causes = [
            {"cause": "Motor Coil Winding Short / Motor Degradation", "prob": 0.70},
            {"cause": "Mechanical Gear Binding / High Friction Load", "prob": 0.20},
            {"cause": "Electrical Ingress Grid Invariance", "prob": 0.10}
        ]
        actions = [
            "Perform motor winding resistance inspection",
            "Inspect mechanical gears for wear debris and alignment",
            "Verify transformer input relay voltage levels"
        ]
        confidence = 0.80

    # 4. Serialize list structures into queryable CSV strings for database/Athena compat
    cause_strings = [f"{c['cause']} ({int(c['prob'] * 100)}%)" for c in causes]
    root_cause_candidates_str = ", ".join(cause_strings)
    recommended_actions_str = ", ".join([f"{i+1}. {act}" for i, act in enumerate(actions)])

    # 5. Populate and return enriched payload
    diag_fields = {
        "anomaly_reason": rules["reason"],
        "trigger_metric": trigger_metric,
        "trigger_value": float(trigger_value) if trigger_value is not None else None,
        "expected_range": rules["expected_range"],
        "root_cause_candidates": root_cause_candidates_str,
        "recommended_actions": recommended_actions_str,
        "diagnostic_confidence": float(confidence)
    }

    return {**payload, **diag_fields}
