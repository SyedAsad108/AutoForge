-- =============================================================================
-- AutoForge Athena Analytics Layer — DDL Schema Definition
-- Database: autoforge_analytics
-- Table: telemetry_curated
-- =============================================================================

-- 1. Create Analytics Database
CREATE DATABASE IF NOT EXISTS autoforge_analytics;

-- 2. Create Curated Telemetry Table (External Parquet)
CREATE EXTERNAL TABLE IF NOT EXISTS autoforge_analytics.telemetry_curated (
  event_id STRING,
  machine_id STRING,
  factory_id STRING,
  timestamp STRING,
  status STRING,
  anomaly_detected BOOLEAN,
  anomaly_type STRING,
  anomaly_severity DOUBLE,
  degradation_level DOUBLE,
  anomaly_reason STRING,
  trigger_metric STRING,
  trigger_value DOUBLE,
  expected_range STRING,
  root_cause_candidates STRING,
  recommended_actions STRING,
  diagnostic_confidence DOUBLE,
  spindle_speed DOUBLE,
  tool_wear DOUBLE,
  vibration DOUBLE,
  rpm DOUBLE,
  power_consumption DOUBLE,
  hydraulic_pressure DOUBLE,
  cycle_time DOUBLE,
  joint_load DOUBLE,
  movement_delay DOUBLE,
  motor_temperature DOUBLE,
  positional_accuracy DOUBLE,
  energy_output DOUBLE,
  coolant_flow_rate DOUBLE,
  pressure DOUBLE,
  arc_stability DOUBLE,
  energy_usage DOUBLE,
  task_completion_rate DOUBLE,
  alignment_accuracy DOUBLE,
  cycle_efficiency DOUBLE,
  temperature DOUBLE
)
PARTITIONED BY (
  machine_type STRING,
  year INT,
  month INT,
  day INT
)
STORED AS PARQUET
LOCATION 's3://autoforge-data-lake/curated/'
TBLPROPERTIES (
  'classification'='parquet',
  'parquet.compression'='SNAPPY'
);

-- 3. Discover and Load Partitions
MSCK REPAIR TABLE autoforge_analytics.telemetry_curated;
