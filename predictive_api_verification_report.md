# AutoForge Smart Manufacturing Analytics — Predictive Maintenance API Verification Report

This report documents the verification of the FastAPI Predictive Maintenance endpoints connecting live to the Athena analytics views and executing machine learning predictions using the production XGBoost model.

## API Key Authentication Security
All endpoints are secured via the `X-API-Key` header. Requests without valid keys are blocked with a `403 Forbidden` response.

---

## 1. Endpoint Verification Summary

| Endpoint Description | Request URL | Verification Status | Code |
| :--- | :--- | :---: | :---: |
| Fleet Predictive Summary | `GET http://127.0.0.1:8000/analytics/predictive-maintenance` | **SUCCESS** | 200 |
| Failure Forecast List | `GET http://127.0.0.1:8000/analytics/failure-forecast` | **SUCCESS** | 200 |
| Maintenance Priority Queue | `GET http://127.0.0.1:8000/analytics/maintenance-priority` | **SUCCESS** | 200 |
| Single Machine Risk Analysis (M007) | `GET http://127.0.0.1:8000/analytics/machine/M007/risk` | **SUCCESS** | 200 |

---
## 2. Sample Response Payloads

### Fleet Predictive Summary
* **Request**: `GET http://127.0.0.1:8000/analytics/predictive-maintenance`
**JSON Response**:
```json
{
  "total_machines_monitored": 24,
  "high_risk_count": 11,
  "warning_count": 2,
  "stable_count": 11,
  "average_fleet_risk_pct": 57.7,
  "total_potential_savings_usd": 55600.0,
  "total_downtime_hours_avoided": 84.0
}
```

### Failure Forecast List
* **Request**: `GET http://127.0.0.1:8000/analytics/failure-forecast`
**JSON Response**:
```json
[
  {
    "machine_id": "M007",
    "machine_type": "hydraulic_press",
    "failure_risk": 1.0,
    "risk_level": "CRITICAL",
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "hydraulic seal leakage / valve decay"
  },
  {
    "machine_id": "M014",
    "machine_type": "industrial_turbine",
    "failure_risk": 0.9800000190734863,
    "risk_level": "CRITICAL",
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "vibration wear / shaft misalignment"
  },
  {
    "machine_id": "M015",
    "machine_type": "industrial_turbine",
    "failure_risk": 0.9800000190734863,
    "risk_level": "CRITICAL",
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "vibration wear / shaft misalignment"
  },
  {
    "machine_id": "M008",
    "machine_type": "cnc_machine",
    "failure_risk": 0.9599999785423279,
    "risk_level": "CRITICAL",
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "spindle bit fracture / tool breakage"
  },
  {
    "machine_id": "M009",
    "machine_type": "cnc_machine",
    "failure_risk": 0.9599999785423279,
    "risk_level": "CRITICAL",
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "spindle bit fracture / tool breakage"
  },
  {
    "machine_id": "M010",
    "machine_type": "cnc_machine",
    "failure_risk": 0.9599999785423279,
    "risk_level": "CRITICAL",
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "spindle bit fracture / tool breakage"
  },
  {
    "machine_id": "M004",
    "machine_type": "conveyor_motor",
    "failure_risk": 0.9100000262260437,
    "risk_level": "CRITICAL",
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "drive belt slippage / bearing friction"
  },
  {
    "machine_id": "M019",
    "machine_type": "welding_unit",
    "failure_risk": 0.8999999761581421,
    "risk_level": "HIGH",
    "predicted_failure_window": "3-5 days",
    "likely_failure_mode": "electrode tip contamination / power surge"
  },
  {
    "machine_id": "M002",
    "machine_type": "conveyor_motor",
    "failure_risk": 0.8500000238418579,
    "risk_level": "HIGH",
    "predicted_failure_window": "3-5 days",
    "likely_failure_mode": "drive belt slippage / bearing friction"
  },
  {
    "machine_id": "M003",
    "machine_type": "conveyor_motor",
    "failure_risk": 0.8500000238418579,
    "risk_level": "HIGH",
    "predicted_failure_window": "3-5 days",
    "likely_failure_mode": "drive belt slippage / bearing friction"
  },
  {
    "machine_id": "M020",
    "machine_type": "welding_unit",
    "failure_risk": 0.7599999904632568,
    "risk_level": "HIGH",
    "predicted_failure_window": "3-5 days",
    "likely_failure_mode": "electrode tip contamination / power surge"
  },
  {
    "machine_id": "M001",
    "machine_type": "conveyor_motor",
    "failure_risk": 0.6800000071525574,
    "risk_level": "MEDIUM",
    "predicted_failure_window": "7-10 days",
    "likely_failure_mode": "drive belt slippage / bearing friction"
  },
  {
    "machine_id": "M005",
    "machine_type": "hydraulic_press",
    "failure_risk": 0.47999998927116394,
    "risk_level": "MEDIUM",
    "predicted_failure_window": "7-10 days",
    "likely_failure_mode": "hydraulic seal leakage / valve decay"
  },
  {
    "machine_id": "M006",
    "machine_type": "hydraulic_press",
    "failure_risk": 0.38999998569488525,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "hydraulic seal leakage / valve decay"
  },
  {
    "machine_id": "M018",
    "machine_type": "cooling_system",
    "failure_risk": 0.38999998569488525,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "coolant pump impeller blockage / seal failure"
  },
  {
    "machine_id": "M012",
    "machine_type": "robotic_arm",
    "failure_risk": 0.36000001430511475,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "joint backlash / electrical actuator failure"
  },
  {
    "machine_id": "M013",
    "machine_type": "robotic_arm",
    "failure_risk": 0.36000001430511475,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "joint backlash / electrical actuator failure"
  },
  {
    "machine_id": "M023",
    "machine_type": "assembly_robot",
    "failure_risk": 0.23000000417232513,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "end-effector bracket expansion / axis motor stall"
  },
  {
    "machine_id": "M022",
    "machine_type": "assembly_robot",
    "failure_risk": 0.20999999344348907,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "end-effector bracket expansion / axis motor stall"
  },
  {
    "machine_id": "M024",
    "machine_type": "assembly_robot",
    "failure_risk": 0.20999999344348907,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "end-effector bracket expansion / axis motor stall"
  },
  {
    "machine_id": "M016",
    "machine_type": "cooling_system",
    "failure_risk": 0.20000000298023224,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "coolant pump impeller blockage / seal failure"
  },
  {
    "machine_id": "M011",
    "machine_type": "robotic_arm",
    "failure_risk": 0.12999999523162842,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "joint backlash / electrical actuator failure"
  },
  {
    "machine_id": "M017",
    "machine_type": "cooling_system",
    "failure_risk": 0.07000000029802322,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "coolant pump impeller blockage / seal failure"
  },
  {
    "machine_id": "M021",
    "machine_type": "welding_unit",
    "failure_risk": 0.029999999329447746,
    "risk_level": "LOW",
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "electrode tip contamination / power surge"
  }
]
```

### Maintenance Priority Queue
* **Request**: `GET http://127.0.0.1:8000/analytics/maintenance-priority`
**JSON Response**:
```json
[
  {
    "machine_id": "M014",
    "machine_type": "industrial_turbine",
    "priority_index": 11760.0,
    "risk_level": "CRITICAL",
    "failure_risk": 0.9800000190734863,
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "vibration wear / shaft misalignment",
    "downtime_avoided_hours": 12.0,
    "estimated_savings_usd": 12000.0,
    "recommended_action": "Inspect spindle bearings, check shaft laser alignment, and verify anchor bolt torque specifications.",
    "delay_impact_description": "Delaying maintenance of M014 could trigger a catastrophic vibration wear / shaft misalignment failure, causing approximately 12.0 hours of downtime and costing an estimated $12,000 in emergency replacement penalties."
  },
  {
    "machine_id": "M015",
    "machine_type": "industrial_turbine",
    "priority_index": 11760.0,
    "risk_level": "CRITICAL",
    "failure_risk": 0.9800000190734863,
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "vibration wear / shaft misalignment",
    "downtime_avoided_hours": 12.0,
    "estimated_savings_usd": 12000.0,
    "recommended_action": "Inspect spindle bearings, check shaft laser alignment, and verify anchor bolt torque specifications.",
    "delay_impact_description": "Delaying maintenance of M015 could trigger a catastrophic vibration wear / shaft misalignment failure, causing approximately 12.0 hours of downtime and costing an estimated $12,000 in emergency replacement penalties."
  },
  {
    "machine_id": "M008",
    "machine_type": "cnc_machine",
    "priority_index": 4320.0,
    "risk_level": "CRITICAL",
    "failure_risk": 0.9599999785423279,
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "spindle bit fracture / tool breakage",
    "downtime_avoided_hours": 6.0,
    "estimated_savings_usd": 4500.0,
    "recommended_action": "Perform spindle drive belt retensioning and verify spindle velocity optical encoders.",
    "delay_impact_description": "Delaying maintenance of M008 could trigger a catastrophic spindle bit fracture / tool breakage failure, causing approximately 6.0 hours of downtime and costing an estimated $4,500 in emergency replacement penalties."
  },
  {
    "machine_id": "M009",
    "machine_type": "cnc_machine",
    "priority_index": 4320.0,
    "risk_level": "CRITICAL",
    "failure_risk": 0.9599999785423279,
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "spindle bit fracture / tool breakage",
    "downtime_avoided_hours": 6.0,
    "estimated_savings_usd": 4500.0,
    "recommended_action": "Perform spindle drive belt retensioning and verify spindle velocity optical encoders.",
    "delay_impact_description": "Delaying maintenance of M009 could trigger a catastrophic spindle bit fracture / tool breakage failure, causing approximately 6.0 hours of downtime and costing an estimated $4,500 in emergency replacement penalties."
  },
  {
    "machine_id": "M010",
    "machine_type": "cnc_machine",
    "priority_index": 4320.0,
    "risk_level": "CRITICAL",
    "failure_risk": 0.9599999785423279,
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "spindle bit fracture / tool breakage",
    "downtime_avoided_hours": 6.0,
    "estimated_savings_usd": 4500.0,
    "recommended_action": "Perform spindle drive belt retensioning and verify spindle velocity optical encoders.",
    "delay_impact_description": "Delaying maintenance of M010 could trigger a catastrophic spindle bit fracture / tool breakage failure, causing approximately 6.0 hours of downtime and costing an estimated $4,500 in emergency replacement penalties."
  },
  {
    "machine_id": "M007",
    "machine_type": "hydraulic_press",
    "priority_index": 4000.0,
    "risk_level": "CRITICAL",
    "failure_risk": 1.0,
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "hydraulic seal leakage / valve decay",
    "downtime_avoided_hours": 8.0,
    "estimated_savings_usd": 4000.0,
    "recommended_action": "Perform pressure decay leak test on high-pressure fluid lines and check main tank fluid levels.",
    "delay_impact_description": "Delaying maintenance of M007 could trigger a catastrophic hydraulic seal leakage / valve decay failure, causing approximately 8.0 hours of downtime and costing an estimated $4,000 in emergency replacement penalties."
  },
  {
    "machine_id": "M019",
    "machine_type": "welding_unit",
    "priority_index": 2025.0,
    "risk_level": "HIGH",
    "failure_risk": 0.8999999761581421,
    "predicted_failure_window": "3-5 days",
    "likely_failure_mode": "electrode tip contamination / power surge",
    "downtime_avoided_hours": 5.0,
    "estimated_savings_usd": 2250.0,
    "recommended_action": "Clean or replace contaminated electrode tip and verify shielding gas flow rates.",
    "delay_impact_description": "Delaying maintenance of M019 could trigger a catastrophic electrode tip contamination / power surge failure, causing approximately 5.0 hours of downtime and costing an estimated $2,250 in emergency replacement penalties."
  },
  {
    "machine_id": "M005",
    "machine_type": "hydraulic_press",
    "priority_index": 1920.0,
    "risk_level": "MEDIUM",
    "failure_risk": 0.47999998927116394,
    "predicted_failure_window": "7-10 days",
    "likely_failure_mode": "hydraulic seal leakage / valve decay",
    "downtime_avoided_hours": 8.0,
    "estimated_savings_usd": 4000.0,
    "recommended_action": "Perform pressure decay leak test on high-pressure fluid lines and check main tank fluid levels.",
    "delay_impact_description": "Delaying maintenance of M005 could trigger a catastrophic hydraulic seal leakage / valve decay failure, causing approximately 8.0 hours of downtime and costing an estimated $4,000 in emergency replacement penalties."
  },
  {
    "machine_id": "M020",
    "machine_type": "welding_unit",
    "priority_index": 1710.0,
    "risk_level": "HIGH",
    "failure_risk": 0.7599999904632568,
    "predicted_failure_window": "3-5 days",
    "likely_failure_mode": "electrode tip contamination / power surge",
    "downtime_avoided_hours": 5.0,
    "estimated_savings_usd": 2250.0,
    "recommended_action": "Clean or replace contaminated electrode tip and verify shielding gas flow rates.",
    "delay_impact_description": "Delaying maintenance of M020 could trigger a catastrophic electrode tip contamination / power surge failure, causing approximately 5.0 hours of downtime and costing an estimated $2,250 in emergency replacement penalties."
  },
  {
    "machine_id": "M006",
    "machine_type": "hydraulic_press",
    "priority_index": 1560.0,
    "risk_level": "LOW",
    "failure_risk": 0.38999998569488525,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "hydraulic seal leakage / valve decay",
    "downtime_avoided_hours": 8.0,
    "estimated_savings_usd": 4000.0,
    "recommended_action": "Perform pressure decay leak test on high-pressure fluid lines and check main tank fluid levels.",
    "delay_impact_description": "Delaying maintenance of M006 could trigger a catastrophic hydraulic seal leakage / valve decay failure, causing approximately 8.0 hours of downtime and costing an estimated $4,000 in emergency replacement penalties."
  },
  {
    "machine_id": "M004",
    "machine_type": "conveyor_motor",
    "priority_index": 1274.0,
    "risk_level": "CRITICAL",
    "failure_risk": 0.9100000262260437,
    "predicted_failure_window": "1-2 days",
    "likely_failure_mode": "drive belt slippage / bearing friction",
    "downtime_avoided_hours": 4.0,
    "estimated_savings_usd": 1400.0,
    "recommended_action": "Inspect spindle bearings, check shaft laser alignment, and verify anchor bolt torque specifications.",
    "delay_impact_description": "Delaying maintenance of M004 could trigger a catastrophic drive belt slippage / bearing friction failure, causing approximately 4.0 hours of downtime and costing an estimated $1,400 in emergency replacement penalties."
  },
  {
    "machine_id": "M002",
    "machine_type": "conveyor_motor",
    "priority_index": 1190.0,
    "risk_level": "HIGH",
    "failure_risk": 0.8500000238418579,
    "predicted_failure_window": "3-5 days",
    "likely_failure_mode": "drive belt slippage / bearing friction",
    "downtime_avoided_hours": 4.0,
    "estimated_savings_usd": 1400.0,
    "recommended_action": "Inspect spindle bearings, check shaft laser alignment, and verify anchor bolt torque specifications.",
    "delay_impact_description": "Delaying maintenance of M002 could trigger a catastrophic drive belt slippage / bearing friction failure, causing approximately 4.0 hours of downtime and costing an estimated $1,400 in emergency replacement penalties."
  },
  {
    "machine_id": "M003",
    "machine_type": "conveyor_motor",
    "priority_index": 1190.0,
    "risk_level": "HIGH",
    "failure_risk": 0.8500000238418579,
    "predicted_failure_window": "3-5 days",
    "likely_failure_mode": "drive belt slippage / bearing friction",
    "downtime_avoided_hours": 4.0,
    "estimated_savings_usd": 1400.0,
    "recommended_action": "Inspect spindle bearings, check shaft laser alignment, and verify anchor bolt torque specifications.",
    "delay_impact_description": "Delaying maintenance of M003 could trigger a catastrophic drive belt slippage / bearing friction failure, causing approximately 4.0 hours of downtime and costing an estimated $1,400 in emergency replacement penalties."
  },
  {
    "machine_id": "M001",
    "machine_type": "conveyor_motor",
    "priority_index": 952.0,
    "risk_level": "MEDIUM",
    "failure_risk": 0.6800000071525574,
    "predicted_failure_window": "7-10 days",
    "likely_failure_mode": "drive belt slippage / bearing friction",
    "downtime_avoided_hours": 4.0,
    "estimated_savings_usd": 1400.0,
    "recommended_action": "Inspect spindle bearings, check shaft laser alignment, and verify anchor bolt torque specifications.",
    "delay_impact_description": "Delaying maintenance of M001 could trigger a catastrophic drive belt slippage / bearing friction failure, causing approximately 4.0 hours of downtime and costing an estimated $1,400 in emergency replacement penalties."
  },
  {
    "machine_id": "M012",
    "machine_type": "robotic_arm",
    "priority_index": 864.0,
    "risk_level": "LOW",
    "failure_risk": 0.36000001430511475,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "joint backlash / electrical actuator failure",
    "downtime_avoided_hours": 4.0,
    "estimated_savings_usd": 2400.0,
    "recommended_action": "Apply high-pressure joint grease to active gears and verify current draw on motor coils.",
    "delay_impact_description": "Delaying maintenance of M012 could trigger a catastrophic joint backlash / electrical actuator failure failure, causing approximately 4.0 hours of downtime and costing an estimated $2,400 in emergency replacement penalties."
  },
  {
    "machine_id": "M013",
    "machine_type": "robotic_arm",
    "priority_index": 864.0,
    "risk_level": "LOW",
    "failure_risk": 0.36000001430511475,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "joint backlash / electrical actuator failure",
    "downtime_avoided_hours": 4.0,
    "estimated_savings_usd": 2400.0,
    "recommended_action": "Apply high-pressure joint grease to active gears and verify current draw on motor coils.",
    "delay_impact_description": "Delaying maintenance of M013 could trigger a catastrophic joint backlash / electrical actuator failure failure, causing approximately 4.0 hours of downtime and costing an estimated $2,400 in emergency replacement penalties."
  },
  {
    "machine_id": "M018",
    "machine_type": "cooling_system",
    "priority_index": 780.0,
    "risk_level": "LOW",
    "failure_risk": 0.38999998569488525,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "coolant pump impeller blockage / seal failure",
    "downtime_avoided_hours": 5.0,
    "estimated_savings_usd": 2000.0,
    "recommended_action": "Flush heat-exchanger pipeline to clear calcification and check coolant pump impeller current draw.",
    "delay_impact_description": "Delaying maintenance of M018 could trigger a catastrophic coolant pump impeller blockage / seal failure failure, causing approximately 5.0 hours of downtime and costing an estimated $2,000 in emergency replacement penalties."
  },
  {
    "machine_id": "M023",
    "machine_type": "assembly_robot",
    "priority_index": 575.0,
    "risk_level": "LOW",
    "failure_risk": 0.23000000417232513,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "end-effector bracket expansion / axis motor stall",
    "downtime_avoided_hours": 5.0,
    "estimated_savings_usd": 2500.0,
    "recommended_action": "Conduct preventative mechanical inspection and calibrate telemetry sensors.",
    "delay_impact_description": "Delaying maintenance of M023 could trigger a catastrophic end-effector bracket expansion / axis motor stall failure, causing approximately 5.0 hours of downtime and costing an estimated $2,500 in emergency replacement penalties."
  },
  {
    "machine_id": "M022",
    "machine_type": "assembly_robot",
    "priority_index": 525.0,
    "risk_level": "LOW",
    "failure_risk": 0.20999999344348907,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "end-effector bracket expansion / axis motor stall",
    "downtime_avoided_hours": 5.0,
    "estimated_savings_usd": 2500.0,
    "recommended_action": "Conduct preventative mechanical inspection and calibrate telemetry sensors.",
    "delay_impact_description": "Delaying maintenance of M022 could trigger a catastrophic end-effector bracket expansion / axis motor stall failure, causing approximately 5.0 hours of downtime and costing an estimated $2,500 in emergency replacement penalties."
  },
  {
    "machine_id": "M024",
    "machine_type": "assembly_robot",
    "priority_index": 525.0,
    "risk_level": "LOW",
    "failure_risk": 0.20999999344348907,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "end-effector bracket expansion / axis motor stall",
    "downtime_avoided_hours": 5.0,
    "estimated_savings_usd": 2500.0,
    "recommended_action": "Conduct preventative mechanical inspection and calibrate telemetry sensors.",
    "delay_impact_description": "Delaying maintenance of M024 could trigger a catastrophic end-effector bracket expansion / axis motor stall failure, causing approximately 5.0 hours of downtime and costing an estimated $2,500 in emergency replacement penalties."
  },
  {
    "machine_id": "M016",
    "machine_type": "cooling_system",
    "priority_index": 400.0,
    "risk_level": "LOW",
    "failure_risk": 0.20000000298023224,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "coolant pump impeller blockage / seal failure",
    "downtime_avoided_hours": 5.0,
    "estimated_savings_usd": 2000.0,
    "recommended_action": "Flush heat-exchanger pipeline to clear calcification and check coolant pump impeller current draw.",
    "delay_impact_description": "Delaying maintenance of M016 could trigger a catastrophic coolant pump impeller blockage / seal failure failure, causing approximately 5.0 hours of downtime and costing an estimated $2,000 in emergency replacement penalties."
  },
  {
    "machine_id": "M011",
    "machine_type": "robotic_arm",
    "priority_index": 312.0,
    "risk_level": "LOW",
    "failure_risk": 0.12999999523162842,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "joint backlash / electrical actuator failure",
    "downtime_avoided_hours": 4.0,
    "estimated_savings_usd": 2400.0,
    "recommended_action": "Apply high-pressure joint grease to active gears and verify current draw on motor coils.",
    "delay_impact_description": "Delaying maintenance of M011 could trigger a catastrophic joint backlash / electrical actuator failure failure, causing approximately 4.0 hours of downtime and costing an estimated $2,400 in emergency replacement penalties."
  },
  {
    "machine_id": "M017",
    "machine_type": "cooling_system",
    "priority_index": 140.0,
    "risk_level": "LOW",
    "failure_risk": 0.07000000029802322,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "coolant pump impeller blockage / seal failure",
    "downtime_avoided_hours": 5.0,
    "estimated_savings_usd": 2000.0,
    "recommended_action": "Flush heat-exchanger pipeline to clear calcification and check coolant pump impeller current draw.",
    "delay_impact_description": "Delaying maintenance of M017 could trigger a catastrophic coolant pump impeller blockage / seal failure failure, causing approximately 5.0 hours of downtime and costing an estimated $2,000 in emergency replacement penalties."
  },
  {
    "machine_id": "M021",
    "machine_type": "welding_unit",
    "priority_index": 67.5,
    "risk_level": "LOW",
    "failure_risk": 0.029999999329447746,
    "predicted_failure_window": "15+ days",
    "likely_failure_mode": "electrode tip contamination / power surge",
    "downtime_avoided_hours": 5.0,
    "estimated_savings_usd": 2250.0,
    "recommended_action": "Clean or replace contaminated electrode tip and verify shielding gas flow rates.",
    "delay_impact_description": "Delaying maintenance of M021 could trigger a catastrophic electrode tip contamination / power surge failure, causing approximately 5.0 hours of downtime and costing an estimated $2,250 in emergency replacement penalties."
  }
]
```

### Single Machine Risk Analysis (M007)
* **Request**: `GET http://127.0.0.1:8000/analytics/machine/M007/risk`
**JSON Response**:
```json
{
  "machine_id": "M007",
  "machine_type": "hydraulic_press",
  "failure_risk": 1.0,
  "risk_level": "CRITICAL",
  "predicted_failure_window": "1-2 days",
  "likely_failure_mode": "hydraulic seal leakage / valve decay",
  "recommended_action": "Perform pressure decay leak test on high-pressure fluid lines and check main tank fluid levels.",
  "explanation": [
    "Temperature increased to critical range (71.9\u00b0C)",
    "Pressure drop below normal operating range (0.0 bar)",
    "Structural degradation entered critical wear phase (85.4%)"
  ],
  "downtime_avoided_hours": 8.0,
  "estimated_savings_usd": 4000.0
}
```

