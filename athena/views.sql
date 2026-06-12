-- =============================================================================
-- AutoForge Athena Analytics Layer — Reusable Views Definition
-- Database: autoforge_analytics
-- Views:
--   - machine_health_view
--   - anomaly_summary_view
--   - daily_factory_summary_view
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. View: Machine Health View
-- -----------------------------------------------------------------------------
-- Pre-calculates baseline health indices, averages, and event volumes per machine.
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

-- -----------------------------------------------------------------------------
-- 2. View: Anomaly Summary View
-- -----------------------------------------------------------------------------
-- Summarizes anomaly event occurrences, categories, and average severities.
CREATE OR REPLACE VIEW autoforge_analytics.anomaly_summary_view AS
SELECT anomaly_type,
       machine_type,
       COUNT(*) AS anomaly_count,
       AVG(anomaly_severity) AS avg_anomaly_severity
FROM autoforge_analytics.telemetry_curated
WHERE anomaly_detected = true
GROUP BY anomaly_type, machine_type;

-- -----------------------------------------------------------------------------
-- 3. View: Daily Factory Summary View
-- -----------------------------------------------------------------------------
-- Provides aggregated daily counts of events, active machines, active anomalies,
-- and average degradation for operational reporting.
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

-- -----------------------------------------------------------------------------
-- 4. View: Hourly Factory Summary View
-- -----------------------------------------------------------------------------
-- Groups telemetry by hour bucket for high-resolution operational reports.
CREATE OR REPLACE VIEW autoforge_analytics.hourly_factory_summary_view AS
SELECT SUBSTR(timestamp, 1, 13) AS hour_bucket,
       COUNT(*) AS total_events,
       COUNT(DISTINCT machine_id) AS active_machines,
       SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS total_anomalies,
       AVG(degradation_level) AS avg_degradation_level
FROM autoforge_analytics.telemetry_curated
GROUP BY SUBSTR(timestamp, 1, 13);

-- -----------------------------------------------------------------------------
-- 5. View: Telemetry Timeseries View
-- -----------------------------------------------------------------------------
-- Groups telemetry at minute level per machine type and ID for trend analyses.
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
