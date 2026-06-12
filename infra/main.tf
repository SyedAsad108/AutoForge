# =============================================================================
# AutoForge Smart Manufacturing Data Intelligence Platform
# Terraform Root Configuration
# =============================================================================
# Phase 4  — Kinesis Data Streams
# Phase 5  — Lambda Validation Layer
# Phase 6  — S3 Layered Data Lake
# =============================================================================

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      ManagedBy   = "terraform"
    }
  }
}

# =============================================================================
# Phase 4 — Kinesis Data Stream
# =============================================================================

resource "aws_kinesis_stream" "telemetry" {
  name             = "${var.project}-telemetry-stream"
  shard_count      = var.kinesis_shard_count
  retention_period = 24

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  tags = {
    Phase   = "4"
    Purpose = "telemetry-ingestion"
  }
}

# =============================================================================
# Outputs
# =============================================================================

output "stream_name" {
  description = "Kinesis telemetry stream name"
  value       = aws_kinesis_stream.telemetry.name
}

output "stream_arn" {
  description = "Kinesis telemetry stream ARN"
  value       = aws_kinesis_stream.telemetry.arn
}