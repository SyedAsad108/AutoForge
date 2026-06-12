# AutoForge System Architecture Technical Reference

This document serves as the master architectural reference and system engineering blueprint for the AutoForge Smart Manufacturing Data Intelligence Platform.

---

## 1. System Components Deep Dive

AutoForge uses a decoupled, event-driven streaming architecture structured across three key boundaries: Ingestion, Processing/Big Data, and Analytics/Digital Twin.

### Ingestion Tier: Local Simulator & Kinesis Data Streams
* **Orchestrator (`FactorySimulator`)**: The Python simulator models $24$ machines across $8$ types. It runs on Python's `asyncio` loop, managing concurrent state machines.
* **Degradation Loop**: Each machine accumulates mechanical wear based on its workload. If degradation breaches $0.5$, it triggers warning conditions; if it breaches $0.8$, it is critical.
* **Amazon Kinesis Data Streams**: Receives continuous base64-encoded JSON telemetry payloads. A provisioned shard count of $1$ satisfies developer throughput SLAs (up to $1,000$ operations/sec).

### Processing Tier: AWS Lambda Validator & S3 Data Lake
* **Lambda Telemetry Validator**: Triggered directly by the Kinesis stream. It performs three stages of validation:
  1. **Envelope Validation**: Checks if critical tracking IDs (`event_id`, `machine_id`, `factory_id`, `timestamp`, `status`) exist.
  2. **Machine Schema Checks**: Verifies machine-specific metrics exist (e.g. `spindle_speed` for CNC, `coolant_flow_rate` for cooling).
  3. **Numeric Range Checks**: Verifies metrics fall within predefined physical bounds (e.g., temperatures between $-10$ and $500$°C).
* **Layered S3 Data Lake**:
  - `raw/`: Stores valid telemetry logs structured in raw JSON.
  - `curated/`: Partitioned, snappy-compressed Parquet files written by Glue Spark job.
  - `quarantine/`: Out-of-bounds or malformed JSON payloads isolated from the lake.

### Big Data & Analytics Tier: EventBridge, Glue, Athena, and FastAPI
* **AWS Glue ETL Job (PySpark)**: Read from S3 `raw/` partitions using Glue job bookmarks to process only new entries.
  - Flattens nested JSON telemetry metrics into top-level columns.
  - Derives SQL-compatible partition keys (`machine_type`, `year`, `month`, `day`) from the ISO timestamp.
  - Writes Parquet files using snappy compression to optimize disk size and query costs.
* **Amazon Athena**: Serverless engine querying partitioned tables under the `autoforge_analytics` Glue catalog.
* **FastAPI Backend (Analytics Service)**: Polls Athena asynchronously via `boto3`. Implements memory-based caching to satisfy sub-second dashboard SLAs and prevent repetitive Athena execution bills.

---

## 2. Ingestion-Time Diagnostics Heuristics

Rather than scanning databases dynamically to trigger warnings, the diagnostics engine computes failure root-causes *at ingestion time* inside the Lambda validator. 

### Diagnostic Logic
When `anomaly_detected` is flagged, the diagnostics engine evaluates the active telemetry payload against correlation rules:

```text
Rule 1: Bearing Wear & Lubrication Loss (CNC & Turbine)
Criteria: temperature > 75.0 AND vibration > 15.0
Diagnosed Root Causes: Severe Bearing Wear (70%), Spindle Shaft Misalignment (20%), Fans degradation (10%)
Confidence: 85%

Rule 2: Cooling Subsystem Failure (Cooling & Press)
Criteria: temperature > 75.0 AND (coolant_flow_rate < 15.0 OR pressure < 4.0 OR hydraulic_pressure < 1800)
Diagnosed Root Causes: Pump impeller degradation (75%), line leakage (15%), high thermal load (10%)
Confidence: 90%

Rule 3: Motor Coil Winding Short (Conveyor)
Criteria: rpm < 900.0 AND power_consumption > 120.0
Diagnosed Root Causes: Motor winding short (70%), mechanical binding (20%), power line fluctuation (10%)
Confidence: 80%
```

The resulting columns (`anomaly_reason`, `root_cause_candidates`, `recommended_actions`, `diagnostic_confidence`) are added directly to the raw JSON document written to S3 raw bucket.

---

## 3. Telemetry Schema Definitions

### Normalized Curated Table Schema (`telemetry_curated`)

| Column Name | Data Type | Partition Key | Description |
|---|---|---|---|
| `event_id` | `VARCHAR` | No | Unique UUID generated at the machine source. |
| `machine_id` | `VARCHAR` | No | Asset identifier (e.g. `M001`, `M002`). |
| `factory_id` | `VARCHAR` | No | ID of the origin factory (`AUTOFORGE_01`). |
| `timestamp` | `VARCHAR` | No | UTC timestamp in ISO-8601 format. |
| `status` | `VARCHAR` | No | Health state: `healthy`, `warning`, `critical`, `offline`. |
| `anomaly_detected` | `BOOLEAN` | No | True if diagnostics flagged anomalous conditions. |
| `anomaly_type` | `VARCHAR` | No | Code of the anomaly type. |
| `anomaly_severity` | `DOUBLE` | No | Severity metric $[0.0 - 1.0]$. |
| `degradation_level` | `DOUBLE` | No | Computed degradation index $[0.0 - 1.0]$. |
| `anomaly_reason` | `VARCHAR` | No | Plaintext diagnostic explanation. |
| `trigger_metric` | `VARCHAR` | No | Sensor metric that breached thresholds. |
| `trigger_value` | `DOUBLE` | No | Raw value of the breaching metric. |
| `expected_range` | `VARCHAR` | No | Expected nominal range bounds. |
| `root_cause_candidates` | `VARCHAR` | No | Comma-separated list of ranked root causes with percentages. |
| `recommended_actions` | `VARCHAR` | No | Comma-separated recommended checklist actions. |
| `diagnostic_confidence`| `DOUBLE` | No | Confidence probability $[0.0 - 1.0]$. |
| `temperature` | `DOUBLE` | No | Sensor reading (°C). Shared by CNC, Conveyor, Press, Welding, Assembly. |
| `spindle_speed` | `DOUBLE` | No | Spindle rotational speed (RPM). CNC only. |
| `tool_wear` | `DOUBLE` | No | CNC tool wear percentage $[0.0 - 100.0]$. |
| `vibration` | `DOUBLE` | No | CNC and Turbine vibration amplitude (mm/s). |
| `rpm` | `DOUBLE` | No | Conveyor and Turbine rotational speed. |
| `power_consumption` | `DOUBLE` | No | Conveyor power usage (kW). |
| `hydraulic_pressure` | `DOUBLE` | No | Press hydraulic pressure (PSI). |
| `cycle_time` | `DOUBLE` | No | Press execution cycle duration (seconds). |
| `joint_load` | `DOUBLE` | No | Robotic arm load weight (kg). |
| `movement_delay` | `DOUBLE` | No | Robotic arm lag latency (ms). |
| `motor_temperature` | `DOUBLE` | No | Robotic arm motor temperature (°C). |
| `positional_accuracy` | `DOUBLE` | No | Robotic arm precision check (%). |
| `energy_output` | `DOUBLE` | No | Turbine power output (kW). |
| `coolant_flow_rate` | `DOUBLE` | No | Cooling flow rate (L/min). |
| `pressure` | `DOUBLE` | No | Cooling system pressure (bar). |
| `arc_stability` | `DOUBLE` | No | Welding unit current stability metric (%). |
| `energy_usage` | `DOUBLE` | No | Welding unit energy consumption (kW). |
| `task_completion_rate`| `DOUBLE` | No | Assembly robot execution rate (items/min). |
| `alignment_accuracy` | `DOUBLE` | No | Assembly robot precision percentage (%). |
| `cycle_efficiency` | `DOUBLE` | No | Assembly robot effectiveness index (%). |
| `machine_type` | `VARCHAR` | Yes | CNC, Conveyor, Press, robotic arm, turbine, etc. |
| `year` | `INT` | Yes | Extracted year partition. |
| `month` | `INT` | Yes | Extracted month partition. |
| `day` | `INT` | Yes | Extracted day partition. |

---

## 4. Stale-While-Revalidate Caching Pattern

The FastAPI server caches expensive Athena analytical results to protect against high scan fees. It uses a custom memory caching engine (`cache_service.py`):

```python
# Caching decorator structure
def with_cache(key_pattern: str, ttl: float = 30.0):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = format_key(key_pattern, args, kwargs)
            cached_data = cache_service.get(cache_key)
            if cached_data:
                # If cached data exists but is past TTL, return it immediately 
                # but spawn background thread to execute fetch query in parallel
                if cached_data.is_stale():
                    asyncio.create_task(func(*args, **kwargs)) # background refresh
                return cached_data.value
            
            # Cold cache: wait for query completion
            fresh_value = await func(*args, **kwargs)
            cache_service.set(cache_key, fresh_value)
            return fresh_value
        return wrapper
    return decorator
```

This ensures sub-second dashboard loads ($<50$ms) on cache hits, while keeping backend queries highly optimized.
