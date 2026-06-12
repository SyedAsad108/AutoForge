# AutoForge Smart Manufacturing Analytics — API Verification Report

This report documents the verification of the FastAPI Analytics endpoints connecting live to the Athena analytics views.

## API Key Authentication Security
All endpoints are secured via the `X-API-Key` header. Requests without valid keys are blocked with a `403 Forbidden` response.

---

## 1. Endpoint Verification Summary

| Endpoint Description | Request URL | Verification Status | Code |
| :--- | :--- | :---: | :---: |
| Factory Status Summary | `GET http://127.0.0.1:8000/analytics/factory-summary` | **SUCCESS** | 200 |
| Recent Alerts List | `GET http://127.0.0.1:8000/analytics/alerts?limit=3` | **SUCCESS** | 200 |
| Machine Inventory List | `GET http://127.0.0.1:8000/analytics/machines` | **SUCCESS** | 200 |
| Single Machine Analytics (M017) | `GET http://127.0.0.1:8000/analytics/machine/M017` | **SUCCESS** | 200 |
| Aggregated Historical Analytics | `GET http://127.0.0.1:8000/analytics` | **SUCCESS** | 200 |

---
## 2. Sample Response Payloads

### Factory Status Summary
* **Request**: `GET http://127.0.0.1:8000/analytics/factory-summary`
**JSON Response**:
```json
{
  "total_machines": 24,
  "healthy": 16,
  "warning": 4,
  "critical": 4
}
```

### Recent Alerts List
* **Request**: `GET http://127.0.0.1:8000/analytics/alerts?limit=3`
**JSON Response**:
```json
[
  {
    "event_id": "5f2b8dbd-823e-4c83-82b1-708644e3da20",
    "machine_id": "M017",
    "machine_type": "cooling_system",
    "timestamp": "2026-06-03T22:09:11Z",
    "anomaly_type": "coolant_reduction",
    "severity": 0.0457,
    "status": "healthy"
  },
  {
    "event_id": "534f9304-0f0f-462d-92be-ab6a96adabe8",
    "machine_id": "M019",
    "machine_type": "welding_unit",
    "timestamp": "2026-06-03T22:09:11Z",
    "anomaly_type": "energy_spike",
    "severity": 0.086,
    "status": "healthy"
  },
  {
    "event_id": "d928f674-fa74-4855-b323-33185ca1e4f1",
    "machine_id": "M004",
    "machine_type": "conveyor_motor",
    "timestamp": "2026-06-03T22:09:11Z",
    "anomaly_type": "overheating",
    "severity": 0.0,
    "status": "healthy"
  }
]
```

### Machine Inventory List
* **Request**: `GET http://127.0.0.1:8000/analytics/machines`
**JSON Response**:
```json
[
  {
    "machine_id": "M017",
    "machine_type": "cooling_system",
    "total_events": 152,
    "anomaly_events": 8,
    "anomaly_rate_percent": 5.263157894736842,
    "avg_temperature": 19.97421052631579,
    "max_degradation_level": 0.0132,
    "health_status": "warning"
  },
  {
    "machine_id": "M018",
    "machine_type": "cooling_system",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 20.16473684210527,
    "max_degradation_level": 0.0052,
    "health_status": "healthy"
  },
  {
    "machine_id": "M020",
    "machine_type": "welding_unit",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 149.68236842105262,
    "max_degradation_level": 0.0054,
    "health_status": "healthy"
  },
  {
    "machine_id": "M021",
    "machine_type": "welding_unit",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 151.24894736842109,
    "max_degradation_level": 0.0128,
    "health_status": "healthy"
  },
  {
    "machine_id": "M003",
    "machine_type": "conveyor_motor",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 44.98473684210528,
    "max_degradation_level": 0.005,
    "health_status": "healthy"
  },
  {
    "machine_id": "M004",
    "machine_type": "conveyor_motor",
    "total_events": 152,
    "anomaly_events": 8,
    "anomaly_rate_percent": 5.263157894736842,
    "avg_temperature": 45.25342105263157,
    "max_degradation_level": 0.0064,
    "health_status": "warning"
  },
  {
    "machine_id": "M010",
    "machine_type": "cnc_machine",
    "total_events": 152,
    "anomaly_events": 4,
    "anomaly_rate_percent": 2.631578947368421,
    "avg_temperature": 40.125526315789465,
    "max_degradation_level": 0.0028,
    "health_status": "healthy"
  },
  {
    "machine_id": "M015",
    "machine_type": "industrial_turbine",
    "total_events": 152,
    "anomaly_events": 84,
    "anomaly_rate_percent": 55.26315789473685,
    "avg_temperature": 81.6578947368421,
    "max_degradation_level": 0.1584,
    "health_status": "critical"
  },
  {
    "machine_id": "M019",
    "machine_type": "welding_unit",
    "total_events": 152,
    "anomaly_events": 12,
    "anomaly_rate_percent": 7.894736842105263,
    "avg_temperature": 151.41447368421055,
    "max_degradation_level": 0.0228,
    "health_status": "warning"
  },
  {
    "machine_id": "M013",
    "machine_type": "robotic_arm",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": null,
    "max_degradation_level": 0.0069,
    "health_status": "healthy"
  },
  {
    "machine_id": "M005",
    "machine_type": "hydraulic_press",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 50.050789473684205,
    "max_degradation_level": 0.0059,
    "health_status": "healthy"
  },
  {
    "machine_id": "M011",
    "machine_type": "robotic_arm",
    "total_events": 152,
    "anomaly_events": 64,
    "anomaly_rate_percent": 42.10526315789473,
    "avg_temperature": null,
    "max_degradation_level": 0.1745,
    "health_status": "critical"
  },
  {
    "machine_id": "M012",
    "machine_type": "robotic_arm",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": null,
    "max_degradation_level": 0.0082,
    "health_status": "healthy"
  },
  {
    "machine_id": "M007",
    "machine_type": "hydraulic_press",
    "total_events": 152,
    "anomaly_events": 32,
    "anomaly_rate_percent": 21.052631578947366,
    "avg_temperature": 50.255789473684196,
    "max_degradation_level": 0.0855,
    "health_status": "critical"
  },
  {
    "machine_id": "M006",
    "machine_type": "hydraulic_press",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 50.11657894736843,
    "max_degradation_level": 0.0056,
    "health_status": "healthy"
  },
  {
    "machine_id": "M001",
    "machine_type": "conveyor_motor",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 44.97947368421052,
    "max_degradation_level": 0.0057,
    "health_status": "healthy"
  },
  {
    "machine_id": "M008",
    "machine_type": "cnc_machine",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 40.13421052631579,
    "max_degradation_level": 0.0042,
    "health_status": "healthy"
  },
  {
    "machine_id": "M014",
    "machine_type": "industrial_turbine",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 80.23789473684212,
    "max_degradation_level": 0.0146,
    "health_status": "healthy"
  },
  {
    "machine_id": "M024",
    "machine_type": "assembly_robot",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 35.105,
    "max_degradation_level": 0.0172,
    "health_status": "healthy"
  },
  {
    "machine_id": "M022",
    "machine_type": "assembly_robot",
    "total_events": 152,
    "anomaly_events": 4,
    "anomaly_rate_percent": 2.631578947368421,
    "avg_temperature": 35.025,
    "max_degradation_level": 0.0138,
    "health_status": "healthy"
  },
  {
    "machine_id": "M016",
    "machine_type": "cooling_system",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 20.046052631578945,
    "max_degradation_level": 0.0106,
    "health_status": "healthy"
  },
  {
    "machine_id": "M002",
    "machine_type": "conveyor_motor",
    "total_events": 152,
    "anomaly_events": 0,
    "anomaly_rate_percent": 0.0,
    "avg_temperature": 44.78447368421052,
    "max_degradation_level": 0.0093,
    "health_status": "healthy"
  },
  {
    "machine_id": "M009",
    "machine_type": "cnc_machine",
    "total_events": 152,
    "anomaly_events": 72,
    "anomaly_rate_percent": 47.368421052631575,
    "avg_temperature": 40.86842105263159,
    "max_degradation_level": 0.1703,
    "health_status": "critical"
  },
  {
    "machine_id": "M023",
    "machine_type": "assembly_robot",
    "total_events": 152,
    "anomaly_events": 28,
    "anomaly_rate_percent": 18.421052631578945,
    "avg_temperature": 35.103157894736846,
    "max_degradation_level": 0.0585,
    "health_status": "warning"
  }
]
```

### Single Machine Analytics (M017)
* **Request**: `GET http://127.0.0.1:8000/analytics/machine/M017`
**JSON Response**:
```json
{
  "machine_id": "M017",
  "machine_type": "cooling_system",
  "total_events": 152,
  "anomaly_events": 8,
  "anomaly_rate_percent": 5.263157894736842,
  "avg_temperature": 19.974210526315787,
  "max_degradation_level": 0.0132,
  "health_status": "warning",
  "history": [
    {
      "timestamp": "2026-06-03T22:09:11Z",
      "temperature": 22.09,
      "degradation_level": 0.0132,
      "anomaly_detected": true,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:11Z",
      "temperature": 22.09,
      "degradation_level": 0.0132,
      "anomaly_detected": true,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:11Z",
      "temperature": 22.09,
      "degradation_level": 0.0132,
      "anomaly_detected": true,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:11Z",
      "temperature": 22.09,
      "degradation_level": 0.0132,
      "anomaly_detected": true,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:10Z",
      "temperature": 20.25,
      "degradation_level": 0.0034,
      "anomaly_detected": true,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:10Z",
      "temperature": 20.25,
      "degradation_level": 0.0034,
      "anomaly_detected": true,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:10Z",
      "temperature": 20.25,
      "degradation_level": 0.0034,
      "anomaly_detected": true,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:10Z",
      "temperature": 20.25,
      "degradation_level": 0.0034,
      "anomaly_detected": true,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:09Z",
      "temperature": 20.0,
      "degradation_level": 0.0034,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:09Z",
      "temperature": 20.0,
      "degradation_level": 0.0034,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:09Z",
      "temperature": 20.0,
      "degradation_level": 0.0034,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:09Z",
      "temperature": 20.0,
      "degradation_level": 0.0034,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:08Z",
      "temperature": 20.0,
      "degradation_level": 0.0013,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:08Z",
      "temperature": 20.0,
      "degradation_level": 0.0013,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:08Z",
      "temperature": 20.0,
      "degradation_level": 0.0013,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:08Z",
      "temperature": 20.0,
      "degradation_level": 0.0013,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:07Z",
      "temperature": 19.61,
      "degradation_level": 0.0013,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:07Z",
      "temperature": 19.61,
      "degradation_level": 0.0013,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:07Z",
      "temperature": 19.61,
      "degradation_level": 0.0013,
      "anomaly_detected": false,
      "status": "healthy"
    },
    {
      "timestamp": "2026-06-03T22:09:07Z",
      "temperature": 19.61,
      "degradation_level": 0.0013,
      "anomaly_detected": false,
      "status": "healthy"
    }
  ]
}
```

### Aggregated Historical Analytics
* **Request**: `GET http://127.0.0.1:8000/analytics`
**JSON Response**:
```json
{
  "daily_summaries": [
    {
      "date": "2026-06-03",
      "total_events": 3648,
      "active_machines": 24,
      "total_anomalies": 316,
      "avg_degradation_level": 0.008230482456140357
    }
  ],
  "anomaly_distribution": [
    {
      "anomaly_type": "unstable_rpm",
      "machine_type": "industrial_turbine",
      "anomaly_count": 84,
      "avg_anomaly_severity": 0.2513666666666666
    },
    {
      "anomaly_type": "vibration_anomaly",
      "machine_type": "cnc_machine",
      "anomaly_count": 72,
      "avg_anomaly_severity": 0.28523888888888893
    },
    {
      "anomaly_type": "motor_overheating",
      "machine_type": "robotic_arm",
      "anomaly_count": 64,
      "avg_anomaly_severity": 0.3383999999999999
    },
    {
      "anomaly_type": "pressure_drop",
      "machine_type": "hydraulic_press",
      "anomaly_count": 32,
      "avg_anomaly_severity": 0.1435875
    },
    {
      "anomaly_type": "alignment_degradation",
      "machine_type": "assembly_robot",
      "anomaly_count": 32,
      "avg_anomaly_severity": 0.0933
    },
    {
      "anomaly_type": "energy_spike",
      "machine_type": "welding_unit",
      "anomaly_count": 12,
      "avg_anomaly_severity": 0.050899999999999994
    },
    {
      "anomaly_type": "overheating",
      "machine_type": "conveyor_motor",
      "anomaly_count": 8,
      "avg_anomaly_severity": 0.0
    },
    {
      "anomaly_type": "coolant_reduction",
      "machine_type": "cooling_system",
      "anomaly_count": 8,
      "avg_anomaly_severity": 0.02285
    },
    {
      "anomaly_type": "excessive_tool_wear",
      "machine_type": "cnc_machine",
      "anomaly_count": 4,
      "avg_anomaly_severity": 0.0
    }
  ]
}
```

