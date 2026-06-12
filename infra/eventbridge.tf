# =============================================================================
# Phase 7 — EventBridge + Glue Trigger Lambda
# =============================================================================
# Architecture:
#   Raw S3 (PutObject on raw/) → EventBridge (S3 Object Created)
#   EventBridge Scheduled Rule (every 5 min) → Glue Trigger Lambda
#   Glue Trigger Lambda → glue.start_job_run (idempotent)
# =============================================================================

# --- Enable S3 → EventBridge event notifications on the data lake bucket ---
# This sends all S3 events (PutObject, DeleteObject, etc.) to the
# default EventBridge event bus. Rules then filter what to act on.
resource "aws_s3_bucket_notification" "data_lake_eventbridge" {
  bucket      = aws_s3_bucket.data_lake.id
  eventbridge = true
}

# ---------------------------------------------------------------------------
# Glue Trigger Lambda Package
# ---------------------------------------------------------------------------
data "archive_file" "glue_trigger" {
  type        = "zip"
  source_file = "${path.module}/../lambda/glue_trigger/handler.py"
  output_path = "${path.module}/.build/glue_trigger.zip"
}

# IAM role for the Glue Trigger Lambda
data "aws_iam_policy_document" "glue_trigger_assume" {
  statement {
    sid     = "AllowLambdaAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue_trigger_lambda" {
  name               = "${var.project}-glue-trigger-role"
  assume_role_policy = data.aws_iam_policy_document.glue_trigger_assume.json

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "7"
  }
}

data "aws_iam_policy_document" "glue_trigger_policy" {
  # CloudWatch Logs
  statement {
    sid    = "Logs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/${var.project}-glue-trigger:*"
    ]
  }

  # Glue: start job run + read job status
  statement {
    sid    = "GlueJobControl"
    effect = "Allow"
    actions = [
      "glue:StartJobRun",
      "glue:GetJobRun",
      "glue:GetJobRuns",
      "glue:BatchStopJobRun",
    ]
    resources = [
      "arn:aws:glue:${var.aws_region}:*:job/${aws_glue_job.raw_to_curated.name}"
    ]
  }
}

resource "aws_iam_role_policy" "glue_trigger" {
  name   = "${var.project}-glue-trigger-policy"
  role   = aws_iam_role.glue_trigger_lambda.id
  policy = data.aws_iam_policy_document.glue_trigger_policy.json
}

# CloudWatch Log Group pre-created with retention
resource "aws_cloudwatch_log_group" "glue_trigger" {
  name              = "/aws/lambda/${var.project}-glue-trigger"
  retention_in_days = 14

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "7"
  }
}

# The Glue Trigger Lambda function
resource "aws_lambda_function" "glue_trigger" {
  function_name    = "${var.project}-glue-trigger"
  description      = "Triggered by EventBridge to start the Glue ETL job"
  role             = aws_iam_role.glue_trigger_lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.glue_trigger.output_path
  source_code_hash = data.archive_file.glue_trigger.output_base64sha256
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      GLUE_JOB_NAME = aws_glue_job.raw_to_curated.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.glue_trigger,
    aws_iam_role_policy.glue_trigger,
  ]

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "7"
  }
}

# ---------------------------------------------------------------------------
# EventBridge Rules
# ---------------------------------------------------------------------------

# Rule 1: S3 Object Created in raw/ prefix → trigger ETL
# (event-driven path — fires on each raw record landing)
resource "aws_cloudwatch_event_rule" "s3_raw_created" {
  name        = "${var.project}-s3-raw-object-created"
  description = "Fires when any object is created under raw/ in the data lake"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    "detail-type" = ["Object Created"]
    detail = {
      bucket = {
        name = [aws_s3_bucket.data_lake.bucket]
      }
      object = {
        key = [{ prefix = "raw/" }]
      }
    }
  })

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "7"
  }
}

resource "aws_cloudwatch_event_target" "s3_raw_to_glue" {
  rule      = aws_cloudwatch_event_rule.s3_raw_created.name
  target_id = "GlueTriggerLambda"
  arn       = aws_lambda_function.glue_trigger.arn
}

resource "aws_lambda_permission" "eventbridge_s3_invoke" {
  statement_id  = "AllowEventBridgeS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.glue_trigger.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.s3_raw_created.arn
}

# Rule 2: Scheduled fallback (every 5 minutes)
# Ensures curated data is always up-to-date even if S3 events are missed.
resource "aws_cloudwatch_event_rule" "etl_schedule" {
  name                = "${var.project}-etl-schedule"
  description         = "Scheduled ETL trigger — every 5 minutes fallback"
  schedule_expression = "rate(5 minutes)"

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "7"
  }
}

resource "aws_cloudwatch_event_target" "etl_schedule_to_glue" {
  rule      = aws_cloudwatch_event_rule.etl_schedule.name
  target_id = "ScheduledGlueTrigger"
  arn       = aws_lambda_function.glue_trigger.arn
}

resource "aws_lambda_permission" "eventbridge_schedule_invoke" {
  statement_id  = "AllowEventBridgeScheduleInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.glue_trigger.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.etl_schedule.arn
}

# =============================================================================
# Outputs
# =============================================================================
output "glue_trigger_function_name" {
  description = "Glue Trigger Lambda function name"
  value       = aws_lambda_function.glue_trigger.function_name
}

output "eventbridge_s3_rule" {
  description = "EventBridge rule ARN for S3 raw/ object created events"
  value       = aws_cloudwatch_event_rule.s3_raw_created.arn
}

output "eventbridge_schedule_rule" {
  description = "EventBridge scheduled rule ARN (every 5 minutes)"
  value       = aws_cloudwatch_event_rule.etl_schedule.arn
}
