# =============================================================================
# Phase 5 — Lambda Telemetry Validator
# =============================================================================
# Flow: Kinesis → Lambda → S3 Raw | S3 Quarantine
# =============================================================================

# --- CloudWatch Log Group (pre-create so retention is set before Lambda runs) ---
resource "aws_cloudwatch_log_group" "lambda_validator" {
  name              = "/aws/lambda/${var.project}-telemetry-validator"
  retention_in_days = 14

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "5"
  }
}

# --- Package the Lambda function code into a zip ---
data "archive_file" "lambda_validator" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/validator"
  output_path = "${path.module}/.build/validator.zip"
}

# --- Lambda Function ---
resource "aws_lambda_function" "telemetry_validator" {
  function_name    = "${var.project}-telemetry-validator"
  description      = "Validates Kinesis telemetry and routes to S3 raw or quarantine"
  role             = aws_iam_role.lambda_validator.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_validator.output_path
  source_code_hash = data.archive_file.lambda_validator.output_base64sha256
  timeout          = var.lambda_timeout_seconds
  memory_size      = var.lambda_memory_mb

  environment {
    variables = {
      DATA_LAKE_BUCKET  = aws_s3_bucket.data_lake.bucket
      QUARANTINE_BUCKET = aws_s3_bucket.quarantine.bucket
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_validator,
    aws_iam_role_policy.lambda_validator,
  ]

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "5"
  }
}

# --- Kinesis Event Source Mapping ---
# Triggers Lambda on each batch of Kinesis records
resource "aws_lambda_event_source_mapping" "kinesis_to_lambda" {
  event_source_arn  = aws_kinesis_stream.telemetry.arn
  function_name     = aws_lambda_function.telemetry_validator.arn
  starting_position = var.lambda_starting_position
  batch_size        = var.lambda_batch_size

  # Retry configuration
  maximum_retry_attempts             = 3
  bisect_batch_on_function_error     = true  # split batch on error to isolate bad records
  maximum_record_age_in_seconds      = 3600  # discard records older than 1 hour

  # Destination for records that fail all retries
  destination_config {
    on_failure {
      destination_arn = aws_sqs_queue.lambda_dlq.arn
    }
  }

  depends_on = [aws_iam_role_policy.lambda_validator]
}

# --- Dead-Letter Queue for Lambda failures ---
resource "aws_sqs_queue" "lambda_dlq" {
  name                      = "${var.project}-validator-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "5"
    Purpose     = "lambda-dlq"
  }
}

# IAM: allow Lambda to send messages to the DLQ
data "aws_iam_policy_document" "lambda_dlq_policy" {
  statement {
    sid    = "AllowSQSSendMessage"
    effect = "Allow"
    actions = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.lambda_dlq.arn]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_sqs_queue_policy" "lambda_dlq" {
  queue_url = aws_sqs_queue.lambda_dlq.id
  policy    = data.aws_iam_policy_document.lambda_dlq_policy.json
}

# Add SQS permission to the Lambda IAM role
data "aws_iam_policy_document" "lambda_sqs" {
  statement {
    sid     = "AllowSQSWrite"
    effect  = "Allow"
    actions = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.lambda_dlq.arn]
  }
}

resource "aws_iam_role_policy" "lambda_sqs" {
  name   = "${var.project}-lambda-sqs-policy"
  role   = aws_iam_role.lambda_validator.id
  policy = data.aws_iam_policy_document.lambda_sqs.json
}

# =============================================================================
# Outputs
# =============================================================================
output "lambda_function_name" {
  description = "Lambda Validator function name"
  value       = aws_lambda_function.telemetry_validator.function_name
}

output "lambda_function_arn" {
  description = "Lambda Validator function ARN"
  value       = aws_lambda_function.telemetry_validator.arn
}

output "lambda_dlq_url" {
  description = "Dead-Letter Queue URL for Lambda failures"
  value       = aws_sqs_queue.lambda_dlq.id
}
