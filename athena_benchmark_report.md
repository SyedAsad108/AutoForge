# AutoForge Smart Manufacturing Analytics — Athena Cost & Performance Benchmark Report

This document records the cost and performance benchmarking of the Athena Analytics Layer, demonstrating execution efficiency, data scans, and query partition pruning benefits.

## Cost Visibility & Billing Model
Athena is billed on a decimal TB scale at **$5.00 per TB scanned** ($0.000000000005 per byte), subject to a **10MB minimum charge per query** ($0.00000005) to account for metadata overhead.

---

## 1. Summary of Benchmark Runs

| Query Label | Execution Time (ms) | Data Scanned (bytes) | Billed Volume (bytes) | Est. Cost (USD) |
| :--- | :---: | :---: | :---: | :---: |
| MSCK REPAIR TABLE telemetry_curated | 2389 | 0 | 10,000,000 | $0.00005000 |
| Deploy View: autoforge_analytics.machine_health_view | 331 | 0 | 10,000,000 | $0.00005000 |
| Deploy View: autoforge_analytics.anomaly_summary_view | 311 | 0 | 10,000,000 | $0.00005000 |
| Deploy View: autoforge_analytics.daily_factory_summary_view | 323 | 0 | 10,000,000 | $0.00005000 |
| Deploy View: autoforge_analytics.hourly_factory_summary_view | 343 | 0 | 10,000,000 | $0.00005000 |
| Deploy View: autoforge_analytics.telemetry_timeseries_view | 331 | 0 | 10,000,000 | $0.00005000 |
| Required Query: Machine Count by Type | 1664 | 0 | 10,000,000 | $0.00005000 |
| Required Query: Machine Health (Avg Temperature) | 1102 | 2,314,668 | 10,000,000 | $0.00005000 |
| Required Query: Anomaly Trends | 1217 | 741,466 | 10,000,000 | $0.00005000 |
| Analytical Query: Most Active Machines | 1459 | 728,635 | 10,000,000 | $0.00005000 |
| Analytical Query: Average Temperature by Machine Type | 2190 | 1,586,033 | 10,000,000 | $0.00005000 |
| Analytical Query: Highest Anomaly Rate Machines | 1131 | 1,046,596 | 10,000,000 | $0.00005000 |
| Analytical Query: Daily Telemetry Volume | 2192 | 0 | 10,000,000 | $0.00005000 |
| Analytical Query: Energy Consumption by Machine Type | 1380 | 1,356,620 | 10,000,000 | $0.00005000 |
| Query View: machine_health_view | 1340 | 3,842,209 | 10,000,000 | $0.00005000 |
| Query View: anomaly_summary_view | 1520 | 2,001,168 | 10,000,000 | $0.00005000 |
| Query View: daily_factory_summary_view | 3469 | 2,256,176 | 10,000,000 | $0.00005000 |
| Query View: hourly_factory_summary_view | 1285 | 4,557,318 | 10,000,000 | $0.00005000 |
| Query View: telemetry_timeseries_view | 1439 | 7,664,352 | 10,000,000 | $0.00005000 |
| Full Table Scan Query | 1306 | 1,586,033 | 10,000,000 | $0.00005000 |
| Pruned Partition Query | 614 | 18,346 | 10,000,000 | $0.00005000 |

---

### Partition Pruning Optimization Gains
* **Full Table Scan**: `1,586,033 bytes` scanned
* **Pruned Partition Scan (Single-Day & Machine Type)**: `18,346 bytes` scanned
* **Data Reduction**: **98.84% less data scanned**
* **Optimization Summary**: Partitioning by `machine_type`, `year`, `month`, and `day` successfully filters out irrelevant directories at the S3 bucket level. In production, this directly translates to **98.84% cost savings** and faster query runtimes.

---
## 2. Detailed Query Library Definitions & Sample Outputs

### MSCK REPAIR TABLE telemetry_curated
**SQL Statement**:
```sql
MSCK REPAIR TABLE telemetry_curated;
```

* **Engine Execution Time**: `2389 ms`
* **Actual Data Scanned**: `0 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Deploy View: autoforge_analytics.machine_health_view
**SQL Statement**:
```sql
CREATE OR REPLACE VIEW autoforge_analytics.machine_health_view AS
SELECT machine_id,
       machine_type,
       COUNT(*) AS total_events,
       SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS anomaly_events,
       (CAST(SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*)) * 100.0 AS anomaly_rate_percent,
       AVG(temperature) AS avg_temperature,
       MAX(degradation_level) AS max_degradation_level
FROM autoforge_analytics.telemetry_curated
GROUP BY machine_id, machine_type;
```

* **Engine Execution Time**: `331 ms`
* **Actual Data Scanned**: `0 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Deploy View: autoforge_analytics.anomaly_summary_view
**SQL Statement**:
```sql
CREATE OR REPLACE VIEW autoforge_analytics.anomaly_summary_view AS
SELECT anomaly_type,
       machine_type,
       COUNT(*) AS anomaly_count,
       AVG(anomaly_severity) AS avg_anomaly_severity
FROM autoforge_analytics.telemetry_curated
WHERE anomaly_detected = true
GROUP BY anomaly_type, machine_type;
```

* **Engine Execution Time**: `311 ms`
* **Actual Data Scanned**: `0 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Deploy View: autoforge_analytics.daily_factory_summary_view
**SQL Statement**:
```sql
CREATE OR REPLACE VIEW autoforge_analytics.daily_factory_summary_view AS
SELECT year,
       month,
       day,
       COUNT(*) AS total_events,
       COUNT(DISTINCT machine_id) AS active_machines,
       SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS total_anomalies,
       AVG(degradation_level) AS avg_degradation_level
FROM autoforge_analytics.telemetry_curated
GROUP BY year, month, day;
```

* **Engine Execution Time**: `323 ms`
* **Actual Data Scanned**: `0 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Deploy View: autoforge_analytics.hourly_factory_summary_view
**SQL Statement**:
```sql
CREATE OR REPLACE VIEW autoforge_analytics.hourly_factory_summary_view AS
SELECT SUBSTR(timestamp, 1, 13) AS hour_bucket,
       COUNT(*) AS total_events,
       COUNT(DISTINCT machine_id) AS active_machines,
       SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS total_anomalies,
       AVG(degradation_level) AS avg_degradation_level
FROM autoforge_analytics.telemetry_curated
GROUP BY SUBSTR(timestamp, 1, 13);
```

* **Engine Execution Time**: `343 ms`
* **Actual Data Scanned**: `0 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Deploy View: autoforge_analytics.telemetry_timeseries_view
**SQL Statement**:
```sql
CREATE OR REPLACE VIEW autoforge_analytics.telemetry_timeseries_view AS
SELECT machine_id,
       machine_type,
       SUBSTR(timestamp, 1, 16) AS minute_bucket,
       COUNT(*) AS event_count,
       AVG(temperature) AS avg_temperature,
       AVG(pressure) AS avg_pressure,
       AVG(power_consumption) AS avg_power_consumption,
       AVG(vibration) AS avg_vibration,
       AVG(degradation_level) AS avg_degradation_level,
       SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS anomaly_count
FROM autoforge_analytics.telemetry_curated
GROUP BY machine_id, machine_type, SUBSTR(timestamp, 1, 16);
```

* **Engine Execution Time**: `331 ms`
* **Actual Data Scanned**: `0 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Required Query: Machine Count by Type
**SQL Statement**:
```sql
SELECT machine_type, COUNT(*) AS count
    FROM telemetry_curated
    GROUP BY machine_type
    ORDER BY count DESC;
```

* **Engine Execution Time**: `1664 ms`
* **Actual Data Scanned**: `0 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Required Query: Machine Health (Avg Temperature)
**SQL Statement**:
```sql
SELECT machine_id,
           AVG(CAST(temperature AS DOUBLE)) AS avg_temp
    FROM telemetry_curated
    GROUP BY machine_id
    ORDER BY avg_temp DESC;
```

* **Engine Execution Time**: `1102 ms`
* **Actual Data Scanned**: `2,314,668 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Required Query: Anomaly Trends
**SQL Statement**:
```sql
SELECT anomaly_type,
           COUNT(*) AS anomaly_count
    FROM telemetry_curated
    WHERE anomaly_detected = true
    GROUP BY anomaly_type
    ORDER BY anomaly_count DESC;
```

* **Engine Execution Time**: `1217 ms`
* **Actual Data Scanned**: `741,466 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Analytical Query: Most Active Machines
**SQL Statement**:
```sql
SELECT machine_id,
           machine_type,
           COUNT(*) AS event_count
    FROM telemetry_curated
    GROUP BY machine_id, machine_type
    ORDER BY event_count DESC
    LIMIT 5;
```

* **Engine Execution Time**: `1459 ms`
* **Actual Data Scanned**: `728,635 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Analytical Query: Average Temperature by Machine Type
**SQL Statement**:
```sql
SELECT machine_type,
           AVG(temperature) AS avg_temp
    FROM telemetry_curated
    GROUP BY machine_type
    ORDER BY avg_temp DESC;
```

* **Engine Execution Time**: `2190 ms`
* **Actual Data Scanned**: `1,586,033 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Analytical Query: Highest Anomaly Rate Machines
**SQL Statement**:
```sql
SELECT machine_id,
           machine_type,
           COUNT(*) AS total_events,
           SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS anomaly_events,
           (CAST(SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*)) * 100.0 AS anomaly_rate_percent
    FROM telemetry_curated
    GROUP BY machine_id, machine_type
    ORDER BY anomaly_rate_percent DESC, total_events DESC
    LIMIT 5;
```

* **Engine Execution Time**: `1131 ms`
* **Actual Data Scanned**: `1,046,596 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Analytical Query: Daily Telemetry Volume
**SQL Statement**:
```sql
SELECT year,
           month,
           day,
           COUNT(*) AS daily_volume
    FROM telemetry_curated
    GROUP BY year, month, day
    ORDER BY year DESC, month DESC, day DESC;
```

* **Engine Execution Time**: `2192 ms`
* **Actual Data Scanned**: `0 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Analytical Query: Energy Consumption by Machine Type
**SQL Statement**:
```sql
SELECT machine_type,
           SUM(COALESCE(power_consumption, 0.0) + COALESCE(energy_usage, 0.0) + COALESCE(energy_output, 0.0)) AS total_energy_units
    FROM telemetry_curated
    GROUP BY machine_type
    ORDER BY total_energy_units DESC;
```

* **Engine Execution Time**: `1380 ms`
* **Actual Data Scanned**: `1,356,620 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Query View: machine_health_view
**SQL Statement**:
```sql
SELECT * FROM machine_health_view ORDER BY anomaly_rate_percent DESC LIMIT 5;
```

* **Engine Execution Time**: `1340 ms`
* **Actual Data Scanned**: `3,842,209 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Query View: anomaly_summary_view
**SQL Statement**:
```sql
SELECT * FROM anomaly_summary_view ORDER BY anomaly_count DESC LIMIT 5;
```

* **Engine Execution Time**: `1520 ms`
* **Actual Data Scanned**: `2,001,168 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Query View: daily_factory_summary_view
**SQL Statement**:
```sql
SELECT * FROM daily_factory_summary_view ORDER BY total_events DESC;
```

* **Engine Execution Time**: `3469 ms`
* **Actual Data Scanned**: `2,256,176 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Query View: hourly_factory_summary_view
**SQL Statement**:
```sql
SELECT * FROM hourly_factory_summary_view ORDER BY hour_bucket DESC LIMIT 5;
```

* **Engine Execution Time**: `1285 ms`
* **Actual Data Scanned**: `4,557,318 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Query View: telemetry_timeseries_view
**SQL Statement**:
```sql
SELECT * FROM telemetry_timeseries_view ORDER BY minute_bucket DESC LIMIT 5;
```

* **Engine Execution Time**: `1439 ms`
* **Actual Data Scanned**: `7,664,352 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Full Table Scan Query
**SQL Statement**:
```sql
SELECT SUM(temperature) FROM telemetry_curated;
```

* **Engine Execution Time**: `1306 ms`
* **Actual Data Scanned**: `1,586,033 bytes`
* **Estimated Query Cost**: `$0.00005000`

### Pruned Partition Query
**SQL Statement**:
```sql
SELECT SUM(temperature) FROM telemetry_curated
    WHERE machine_type = 'assembly_robot'
      AND year = 2026
      AND month = 6
      AND day = 3;
```

* **Engine Execution Time**: `614 ms`
* **Actual Data Scanned**: `18,346 bytes`
* **Estimated Query Cost**: `$0.00005000`

