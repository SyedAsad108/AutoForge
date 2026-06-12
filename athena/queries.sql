-- =============================================================================
-- AutoForge Athena Analytics Layer — SQL Query Library
-- Database: autoforge_analytics
-- Table: telemetry_curated
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Required Query: Machine Count by Type
-- -----------------------------------------------------------------------------
-- Shows the distribution of telemetry records across different machine types.
SELECT machine_type, COUNT(*) AS count
FROM telemetry_curated
GROUP BY machine_type
ORDER BY count DESC;

-- -----------------------------------------------------------------------------
-- 2. Required Query: Machine Health (Average Temperature)
-- -----------------------------------------------------------------------------
-- Aggregates average operating temperature per machine.
SELECT machine_id,
       AVG(CAST(temperature AS DOUBLE)) AS avg_temp
FROM telemetry_curated
GROUP BY machine_id
ORDER BY avg_temp DESC;

-- -----------------------------------------------------------------------------
-- 3. Required Query: Anomaly Trends
-- -----------------------------------------------------------------------------
-- Groups active anomalies by their specific failure modes/types.
SELECT anomaly_type,
       COUNT(*) AS anomaly_count
FROM telemetry_curated
WHERE anomaly_detected = true
GROUP BY anomaly_type
ORDER BY anomaly_count DESC;

-- -----------------------------------------------------------------------------
-- 4. Analytical Query: Most Active Machines
-- -----------------------------------------------------------------------------
-- Lists the machines that have produced the highest volume of telemetry.
SELECT machine_id,
       machine_type,
       COUNT(*) AS event_count
FROM telemetry_curated
GROUP BY machine_id, machine_type
ORDER BY event_count DESC
LIMIT 10;

-- -----------------------------------------------------------------------------
-- 5. Analytical Query: Average Temperature by Machine Type
-- -----------------------------------------------------------------------------
-- Compares baseline heat profiles across various machine classes.
SELECT machine_type,
       AVG(temperature) AS avg_temp
FROM telemetry_curated
GROUP BY machine_type
ORDER BY avg_temp DESC;

-- -----------------------------------------------------------------------------
-- 6. Analytical Query: Machines with Highest Anomaly Rates
-- -----------------------------------------------------------------------------
-- Highlights problematic machinery by calculating anomaly ratios.
SELECT machine_id,
       machine_type,
       COUNT(*) AS total_events,
       SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS anomaly_events,
       (CAST(SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*)) * 100.0 AS anomaly_rate_percent
FROM telemetry_curated
GROUP BY machine_id, machine_type
ORDER BY anomaly_rate_percent DESC, total_events DESC;

-- -----------------------------------------------------------------------------
-- 7. Analytical Query: Daily Telemetry Volume
-- -----------------------------------------------------------------------------
-- Tracks overall data volume processed over time.
SELECT year,
       month,
       day,
       COUNT(*) AS daily_volume
FROM telemetry_curated
GROUP BY year, month, day
ORDER BY year DESC, month DESC, day DESC;

-- -----------------------------------------------------------------------------
-- 8. Analytical Query: Energy Consumption by Machine Type
-- -----------------------------------------------------------------------------
-- Aggregates energy usage metrics across CNCs, Conveyors, Welding, and Turbines.
SELECT machine_type,
       SUM(COALESCE(power_consumption, 0.0) + COALESCE(energy_usage, 0.0) + COALESCE(energy_output, 0.0)) AS total_energy_units
FROM telemetry_curated
GROUP BY machine_type
ORDER BY total_energy_units DESC;

-- -----------------------------------------------------------------------------
-- 9. Partition Pruning Verification Queries
-- -----------------------------------------------------------------------------

-- Query A: Full Table Scan (scans all partitioned directories)
SELECT SUM(temperature) FROM telemetry_curated;

-- Query B: Pruned Query (scans only a single day's partition for a specific machine type)
SELECT SUM(temperature) FROM telemetry_curated
WHERE machine_type = 'assembly_robot'
  AND year = 2026
  AND month = 6
  AND day = 3;

-- -----------------------------------------------------------------------------
-- 10. View-Based Queries (To be used by Phase 9 FastAPI Ingestion)
-- -----------------------------------------------------------------------------

-- Query V1: Get Machine Health from View
SELECT * FROM machine_health_view
ORDER BY anomaly_rate_percent DESC;

-- Query V2: Get Anomaly Summary from View
SELECT * FROM anomaly_summary_view
ORDER BY anomaly_count DESC;

-- Query V3: Get Daily Factory Summary from View
SELECT * FROM daily_factory_summary_view
ORDER BY year DESC, month DESC, day DESC;
