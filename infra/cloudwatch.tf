# =============================================================================
# Phase 10.5 — Pipeline Observability (CloudWatch)
# =============================================================================

resource "aws_cloudwatch_dashboard" "pipeline_observability" {
  dashboard_name = "${var.project}-pipeline-observability"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Kinesis", "IncomingRecords", "StreamName", aws_kinesis_stream.telemetry.name]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "Kinesis Incoming Records"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Kinesis", "GetRecords.IteratorAgeMilliseconds", "StreamName", aws_kinesis_stream.telemetry.name]
          ]
          period = 60
          stat   = "Maximum"
          region = var.aws_region
          title  = "Kinesis Iterator Age (Lag)"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.telemetry_validator.function_name],
            [".", "Errors", ".", "."]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "Lambda Invocations & Errors"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["Glue", "JobRunsSucceeded", "JobName", aws_glue_job.raw_to_curated.name],
            [".", "JobRunsFailed", ".", "."]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "Glue Job Status"
        }
      }
    ]
  })
}

# --- Alarms ---

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.project}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Alarm if Lambda validation errors exceed threshold"
  
  dimensions = {
    FunctionName = aws_lambda_function.telemetry_validator.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "kinesis_iterator_age" {
  alarm_name          = "${var.project}-kinesis-iterator-age"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "GetRecords.IteratorAgeMilliseconds"
  namespace           = "AWS/Kinesis"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "30000" # 30 seconds
  alarm_description   = "Alarm if Kinesis consumer falls behind"
  
  dimensions = {
    StreamName = aws_kinesis_stream.telemetry.name
  }
}

resource "aws_cloudwatch_metric_alarm" "glue_failed" {
  alarm_name          = "${var.project}-glue-job-failure"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "JobRunsFailed"
  namespace           = "Glue"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Alarm if Glue ETL job fails"
  
  dimensions = {
    JobName = aws_glue_job.raw_to_curated.name
  }
}
