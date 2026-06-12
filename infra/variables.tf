variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Project prefix used in all resource names"
  type        = string
  default     = "autoforge"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

# --- Kinesis ---
variable "kinesis_stream_name" {
  description = "Name of the existing Kinesis telemetry stream"
  type        = string
  default     = "autoforge-telemetry-stream"
}

variable "kinesis_shard_count" {
  description = "Number of shards for the Kinesis stream"
  type        = number
  default     = 1
}

# --- Lambda ---
variable "lambda_batch_size" {
  description = "Maximum number of Kinesis records per Lambda invocation"
  type        = number
  default     = 100
}

variable "lambda_starting_position" {
  description = "Kinesis shard iterator position for Lambda trigger"
  type        = string
  default     = "LATEST"
}

variable "lambda_timeout_seconds" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_mb" {
  description = "Lambda function memory allocation in MB"
  type        = number
  default     = 256
}

# --- S3 Data Lake ---
variable "data_lake_bucket" {
  description = "Name of the S3 data lake bucket"
  type        = string
  default     = "autoforge-data-lake"
}

variable "quarantine_bucket" {
  description = "Name of the S3 quarantine bucket for invalid records"
  type        = string
  default     = "autoforge-quarantine"
}

variable "lifecycle_transition_days" {
  description = "Days before transitioning objects to Intelligent-Tiering"
  type        = number
  default     = 30
}

# --- Phase 7: Glue ETL ---
variable "glue_version" {
  description = "AWS Glue version"
  type        = string
  default     = "4.0"
}

variable "glue_worker_type" {
  description = "Glue worker type (G.1X is smallest for batch ETL jobs)"
  type        = string
  default     = "G.1X"
}

variable "glue_num_workers" {
  description = "Number of Glue workers"
  type        = number
  default     = 2
}

variable "glue_job_timeout_minutes" {
  description = "Maximum Glue job execution time in minutes"
  type        = number
  default     = 60
}

variable "etl_schedule_expression" {
  description = "EventBridge schedule expression for the ETL fallback trigger"
  type        = string
  default     = "rate(5 minutes)"
}
