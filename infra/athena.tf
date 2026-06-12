# =============================================================================
# Phase 8 — Athena Analytics Layer
# =============================================================================
# Resources:
#   - Athena Query Results Bucket (autoforge-athena-query-results)
#   - Athena Workgroup (autoforge-analytics)
#   - Glue Catalog Database (autoforge_analytics)
#   - Glue Catalog Table (telemetry_curated)
# =============================================================================

# --- Athena Query Results Bucket ---
resource "aws_s3_bucket" "athena_results" {
  bucket        = "${var.project}-athena-query-results"
  force_destroy = true # dev-friendly

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "8"
    Purpose     = "athena-query-results"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  bucket                  = aws_s3_bucket.athena_results.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- Athena Workgroup ---
resource "aws_athena_workgroup" "analytics" {
  name = "${var.project}-analytics"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }

  force_destroy = true

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "8"
  }
}

# --- Glue Catalog Database ---
resource "aws_glue_catalog_database" "autoforge_analytics" {
  name        = "autoforge_analytics"
  description = "AutoForge Smart Manufacturing analytics layer"

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "8"
  }
}

# --- Glue Catalog Table ---
resource "aws_glue_catalog_table" "telemetry_curated" {
  name          = "telemetry_curated"
  database_name = aws_glue_catalog_database.autoforge_analytics.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "EXTERNAL"              = "TRUE"
    "parquet.compression"   = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/curated/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "parquet-serde"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"

      parameters = {
        "serialization.format" = "1"
      }
    }

    columns {
      name = "event_id"
      type = "string"
    }
    columns {
      name = "machine_id"
      type = "string"
    }
    columns {
      name = "factory_id"
      type = "string"
    }
    columns {
      name = "timestamp"
      type = "string"
    }
    columns {
      name = "status"
      type = "string"
    }
    columns {
      name = "anomaly_detected"
      type = "boolean"
    }
    columns {
      name = "anomaly_type"
      type = "string"
    }
    columns {
      name = "anomaly_severity"
      type = "double"
    }
    columns {
      name = "degradation_level"
      type = "double"
    }
    columns {
      name = "anomaly_reason"
      type = "string"
    }
    columns {
      name = "trigger_metric"
      type = "string"
    }
    columns {
      name = "trigger_value"
      type = "double"
    }
    columns {
      name = "expected_range"
      type = "string"
    }
    columns {
      name = "root_cause_candidates"
      type = "string"
    }
    columns {
      name = "recommended_actions"
      type = "string"
    }
    columns {
      name = "diagnostic_confidence"
      type = "double"
    }
    columns {
      name = "spindle_speed"
      type = "double"
    }
    columns {
      name = "tool_wear"
      type = "double"
    }
    columns {
      name = "vibration"
      type = "double"
    }
    columns {
      name = "rpm"
      type = "double"
    }
    columns {
      name = "power_consumption"
      type = "double"
    }
    columns {
      name = "hydraulic_pressure"
      type = "double"
    }
    columns {
      name = "cycle_time"
      type = "double"
    }
    columns {
      name = "joint_load"
      type = "double"
    }
    columns {
      name = "movement_delay"
      type = "double"
    }
    columns {
      name = "motor_temperature"
      type = "double"
    }
    columns {
      name = "positional_accuracy"
      type = "double"
    }
    columns {
      name = "energy_output"
      type = "double"
    }
    columns {
      name = "coolant_flow_rate"
      type = "double"
    }
    columns {
      name = "pressure"
      type = "double"
    }
    columns {
      name = "arc_stability"
      type = "double"
    }
    columns {
      name = "energy_usage"
      type = "double"
    }
    columns {
      name = "task_completion_rate"
      type = "double"
    }
    columns {
      name = "alignment_accuracy"
      type = "double"
    }
    columns {
      name = "cycle_efficiency"
      type = "double"
    }
    columns {
      name = "temperature"
      type = "double"
    }
  }

  partition_keys {
    name = "machine_type"
    type = "string"
  }
  partition_keys {
    name = "year"
    type = "int"
  }
  partition_keys {
    name = "month"
    type = "int"
  }
  partition_keys {
    name = "day"
    type = "int"
  }
}

# =============================================================================
# Outputs
# =============================================================================
output "athena_results_bucket" {
  description = "Athena query results bucket name"
  value       = aws_s3_bucket.athena_results.bucket
}

output "athena_workgroup_name" {
  description = "Athena workgroup name"
  value       = aws_athena_workgroup.analytics.name
}

output "glue_analytics_database_name" {
  description = "Glue Catalog database name for analytics"
  value       = aws_glue_catalog_database.autoforge_analytics.name
}

output "glue_analytics_table_name" {
  description = "Glue Catalog table name for analytics"
  value       = aws_glue_catalog_table.telemetry_curated.name
}
