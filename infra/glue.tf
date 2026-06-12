# =============================================================================
# Phase 7 — AWS Glue ETL: Raw JSON → Curated Parquet
# =============================================================================
# Resources:
#   - Glue Catalog Database
#   - Glue Job (PySpark, Glue 4.0, G.025X)
#   - Glue Crawler (auto-discovers curated schema for Athena)
#   - IAM Role for Glue
#   - S3 object for ETL script
# =============================================================================

# --- IAM: Glue Assume Role ---
data "aws_iam_policy_document" "glue_assume_role" {
  statement {
    sid     = "AllowGlueAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue_etl" {
  name               = "${var.project}-glue-etl-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume_role.json

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "7"
  }
}

# Attach AWS managed Glue service role (CloudWatch, Glue catalog access)
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_etl.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# S3 access: read raw/, write curated/ & processed/, read scripts/, write temp/ & spark-logs/
data "aws_iam_policy_document" "glue_s3" {
  statement {
    sid    = "GlueS3ReadRaw"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.data_lake.arn,
      "${aws_s3_bucket.data_lake.arn}/raw/*",
      "${aws_s3_bucket.data_lake.arn}/scripts/*",
    ]
  }

  statement {
    sid    = "GlueS3WriteCurated"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.data_lake.arn,
      "${aws_s3_bucket.data_lake.arn}/curated/*",
      "${aws_s3_bucket.data_lake.arn}/processed/*",
      "${aws_s3_bucket.data_lake.arn}/temp/*",
      "${aws_s3_bucket.data_lake.arn}/spark-logs/*",
    ]
  }
}

resource "aws_iam_role_policy" "glue_s3" {
  name   = "${var.project}-glue-s3-policy"
  role   = aws_iam_role.glue_etl.id
  policy = data.aws_iam_policy_document.glue_s3.json
}

# --- Glue Catalog Database ---
resource "aws_glue_catalog_database" "autoforge" {
  name        = "autoforge_telemetry"
  description = "AutoForge Smart Manufacturing telemetry data lake"

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "7"
  }
}

# --- Upload ETL script to S3 ---
resource "aws_s3_object" "etl_script" {
  bucket = aws_s3_bucket.data_lake.id
  key    = "scripts/etl_raw_to_curated.py"
  source = "${path.module}/../glue/etl_raw_to_curated.py"
  etag   = filemd5("${path.module}/../glue/etl_raw_to_curated.py")

  tags = {
    Project = var.project
    Phase   = "7"
  }
}

# --- Glue Job ---
resource "aws_glue_job" "raw_to_curated" {
  name         = "${var.project}-etl-raw-to-curated"
  description  = "Converts raw JSON telemetry to partitioned Parquet in curated/"
  role_arn     = aws_iam_role.glue_etl.arn
  glue_version = "4.0"

  # G.1X = smallest worker type for batch ETL jobs (G.025X is streaming-only)
  worker_type       = "G.1X"
  number_of_workers = 2

  # Maximum job execution time: 60 minutes
  timeout = 60

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.data_lake.bucket}/${aws_s3_object.etl_script.key}"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"              = "python"
    "--job-bookmark-option"       = "job-bookmark-enable"
    "--enable-metrics"            = "true"
    "--enable-spark-ui"           = "true"
    "--spark-event-logs-path"     = "s3://${aws_s3_bucket.data_lake.bucket}/spark-logs/"
    "--enable-job-insights"       = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                   = "s3://${aws_s3_bucket.data_lake.bucket}/temp/"
    "--SOURCE_BUCKET"             = aws_s3_bucket.data_lake.bucket
    "--DEST_BUCKET"               = aws_s3_bucket.data_lake.bucket
    "--GLUE_DATABASE"             = aws_glue_catalog_database.autoforge.name
  }

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "7"
  }

  depends_on = [aws_s3_object.etl_script]
}

# --- Glue Crawler: auto-discover curated/ schema for Athena ---
resource "aws_glue_crawler" "curated" {
  name          = "${var.project}-curated-crawler"
  description   = "Crawls curated/ Parquet to update Glue catalog for Athena"
  role          = aws_iam_role.glue_etl.arn
  database_name = aws_glue_catalog_database.autoforge.name
  table_prefix  = "curated_"

  s3_target {
    path = "s3://${aws_s3_bucket.data_lake.bucket}/curated/"
  }

  schema_change_policy {
    # CRAWL_NEW_FOLDERS_ONLY requires both behaviors to be LOG
    delete_behavior = "LOG"
    update_behavior = "LOG"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_NEW_FOLDERS_ONLY"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "7"
  }

  depends_on = [aws_glue_catalog_database.autoforge]
}

# =============================================================================
# Outputs
# =============================================================================
output "glue_job_name" {
  description = "Glue ETL job name"
  value       = aws_glue_job.raw_to_curated.name
}

output "glue_database_name" {
  description = "Glue Catalog database name"
  value       = aws_glue_catalog_database.autoforge.name
}

output "glue_crawler_name" {
  description = "Glue Crawler name for curated/ data"
  value       = aws_glue_crawler.curated.name
}

output "etl_script_s3_path" {
  description = "S3 path to the PySpark ETL script"
  value       = "s3://${aws_s3_bucket.data_lake.bucket}/${aws_s3_object.etl_script.key}"
}
