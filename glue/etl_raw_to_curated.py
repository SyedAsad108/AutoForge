"""
AutoForge ETL — Phase 7
Glue PySpark Job: Raw JSON → Curated Parquet

Flow:
  s3://autoforge-data-lake/raw/machine_type=<t>/year=YYYY/month=MM/day=DD/<event_id>.json
      ↓  flatten + normalise schema
  s3://autoforge-data-lake/curated/machine_type=<t>/year=YYYY/month=MM/day=DD/

Design decisions:
  - mergeSchema=True  → tolerates heterogeneous machine telemetry fields
  - Glue job bookmark → avoids re-processing already-seen files on each run
  - Union schema      → all 20 telemetry fields across 8 machine types become
                        nullable top-level columns in the Parquet output
  - Snappy compression → good balance of speed and size for Athena queries
  - append mode       → safe to run repeatedly without losing data
"""

import sys
import logging

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType, DoubleType, IntegerType, StringType, TimestampType
)

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "SOURCE_BUCKET", "DEST_BUCKET", "GLUE_DATABASE"],
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SOURCE_PATH = f"s3://{args['SOURCE_BUCKET']}/raw/"
DEST_PATH   = f"s3://{args['DEST_BUCKET']}/curated/"
DATABASE    = args["GLUE_DATABASE"]
TABLE_NAME  = "curated_telemetry"

# ---------------------------------------------------------------------------
# Union schema: all possible telemetry fields across all 8 machine types.
# Fields that don't exist for a given record become null automatically.
# ---------------------------------------------------------------------------
TELEMETRY_FIELDS = [
    # CNC Machine
    ("spindle_speed",       DoubleType()),
    ("tool_wear",           DoubleType()),
    ("vibration",           DoubleType()),
    # Conveyor Motor (rpm shared with Turbine)
    ("rpm",                 DoubleType()),
    ("power_consumption",   DoubleType()),
    # Hydraulic Press
    ("hydraulic_pressure",  DoubleType()),
    ("cycle_time",          DoubleType()),
    # Robotic Arm
    ("joint_load",          DoubleType()),
    ("movement_delay",      DoubleType()),
    ("motor_temperature",   DoubleType()),
    ("positional_accuracy", DoubleType()),
    # Industrial Turbine
    ("energy_output",       DoubleType()),
    # Cooling System
    ("coolant_flow_rate",   DoubleType()),
    ("pressure",            DoubleType()),
    # Welding Unit
    ("arc_stability",       DoubleType()),
    ("energy_usage",        DoubleType()),
    # Assembly Robot
    ("task_completion_rate",DoubleType()),
    ("alignment_accuracy",  DoubleType()),
    ("cycle_efficiency",    DoubleType()),
    # Shared across most types
    ("temperature",         DoubleType()),
]

# ---------------------------------------------------------------------------
# ETL
# ---------------------------------------------------------------------------
try:
    logger.info(f"Reading raw JSON from: {SOURCE_PATH}")

    raw_df = (
        spark.read
        .option("mergeSchema", "true")
        .option("recursiveFileLookup", "true")
        .json(SOURCE_PATH)
    )

    total = raw_df.count()
    logger.info(f"Loaded {total:,} records from raw/")

    if total == 0:
        logger.warning("No records found — nothing to process. Committing bookmark.")
        job.commit()
        sys.exit(0)

    # ------------------------------------------------------------------
    # 1. Flatten telemetry nested struct → individual top-level columns
    # ------------------------------------------------------------------
    curated_df = raw_df

    for field_name, field_type in TELEMETRY_FIELDS:
        curated_df = curated_df.withColumn(
            field_name,
            F.col(f"telemetry.{field_name}").cast(field_type),
        )

    # Drop the original nested struct
    curated_df = curated_df.drop("telemetry")

    # ------------------------------------------------------------------
    # 2. Normalise envelope columns
    # ------------------------------------------------------------------
    curated_df = (
        curated_df
        .withColumn("anomaly_detected",  F.col("anomaly_detected").cast(BooleanType()))
        .withColumn("anomaly_severity",  F.col("anomaly_severity").cast(DoubleType()))
        .withColumn("degradation_level", F.col("degradation_level").cast(DoubleType()))
        .withColumn("status",            F.col("status").cast(StringType()))
        .withColumn("machine_type",      F.col("machine_type").cast(StringType()))
        .withColumn("anomaly_reason",    F.col("anomaly_reason").cast(StringType()))
        .withColumn("trigger_metric",    F.col("trigger_metric").cast(StringType()))
        .withColumn("trigger_value",     F.col("trigger_value").cast(DoubleType()))
        .withColumn("expected_range",    F.col("expected_range").cast(StringType()))
        .withColumn("root_cause_candidates", F.col("root_cause_candidates").cast(StringType()))
        .withColumn("recommended_actions", F.col("recommended_actions").cast(StringType()))
        .withColumn("diagnostic_confidence", F.col("diagnostic_confidence").cast(DoubleType()))
    )

    # ------------------------------------------------------------------
    # 3. Derive partition columns from ISO-8601 timestamp string
    # ------------------------------------------------------------------
    curated_df = (
        curated_df
        .withColumn("_ts",  F.to_timestamp(F.col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss'Z'"))
        .withColumn("year",  F.year(F.col("_ts")).cast(IntegerType()))
        .withColumn("month", F.month(F.col("_ts")).cast(IntegerType()))
        .withColumn("day",   F.dayofmonth(F.col("_ts")).cast(IntegerType()))
        .drop("_ts")
    )

    # ------------------------------------------------------------------
    # 4. Data quality — drop records that could not be parsed
    # ------------------------------------------------------------------
    before_drop = curated_df.count()
    curated_df = curated_df.filter(
        F.col("machine_id").isNotNull() &
        F.col("machine_type").isNotNull() &
        F.col("year").isNotNull()
    )
    dropped = before_drop - curated_df.count()
    if dropped > 0:
        logger.warning(f"Dropped {dropped} unparseable records during DQ check")

    logger.info(f"Writing {curated_df.count():,} records to: {DEST_PATH}")
    logger.info(f"Schema: {curated_df.schema.simpleString()}")

    # ------------------------------------------------------------------
    # 5. Write Parquet — partitioned by machine_type / year / month / day
    # ------------------------------------------------------------------
    (
        curated_df.write
        .partitionBy("machine_type", "year", "month", "day")
        .mode("append")
        .option("compression", "snappy")
        .parquet(DEST_PATH)
    )

    logger.info("ETL complete — raw → curated Parquet conversion successful.")

except Exception as exc:
    logger.error(f"ETL job failed: {exc}", exc_info=True)
    raise

finally:
    job.commit()
