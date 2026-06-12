# =============================================================================
# Phase 5 — IAM Role for Lambda Validation Function
# =============================================================================

# --- Assume Role Policy (Lambda trust) ---
data "aws_iam_policy_document" "lambda_assume_role" {
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

resource "aws_iam_role" "lambda_validator" {
  name               = "${var.project}-lambda-validator-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "5"
  }
}

# --- Inline policy: least-privilege permissions ---
data "aws_iam_policy_document" "lambda_validator_policy" {

  # CloudWatch Logs
  statement {
    sid    = "AllowCloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/${var.project}-telemetry-validator:*"]
  }

  # Kinesis — read from stream
  statement {
    sid    = "AllowKinesisRead"
    effect = "Allow"
    actions = [
      "kinesis:GetRecords",
      "kinesis:GetShardIterator",
      "kinesis:DescribeStream",
      "kinesis:DescribeStreamSummary",
      "kinesis:ListShards",
      "kinesis:ListStreams",
    ]
    resources = [aws_kinesis_stream.telemetry.arn]
  }

  # S3 — write to data lake and quarantine
  statement {
    sid    = "AllowS3Write"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
    ]
    resources = [
      "${aws_s3_bucket.data_lake.arn}/raw/*",
      "${aws_s3_bucket.quarantine.arn}/*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_validator" {
  name   = "${var.project}-lambda-validator-policy"
  role   = aws_iam_role.lambda_validator.id
  policy = data.aws_iam_policy_document.lambda_validator_policy.json
}

# =============================================================================
# Outputs
# =============================================================================
output "lambda_role_arn" {
  description = "IAM Role ARN for the Lambda Validator"
  value       = aws_iam_role.lambda_validator.arn
}
