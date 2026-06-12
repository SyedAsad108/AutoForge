# =============================================================================
# Phase 6 — Layered S3 Data Lake
# =============================================================================
# Bucket: autoforge-data-lake
# Prefixes: raw/ | processed/ | curated/ | quarantine/
# Lifecycle: 30 days → Intelligent-Tiering
# =============================================================================

# --- Data Lake bucket ---
resource "aws_s3_bucket" "data_lake" {
  bucket        = "${var.project}-data-lake"
  force_destroy = true # allow destroy for dev; remove in prod

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "6"
    Purpose     = "data-lake"
  }
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket                  = aws_s3_bucket.data_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle: transition to Intelligent-Tiering after 30 days
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "intelligent-tiering-raw"
    status = "Enabled"
    filter { prefix = "raw/" }
    transition {
      days          = var.lifecycle_transition_days
      storage_class = "INTELLIGENT_TIERING"
    }
  }

  rule {
    id     = "intelligent-tiering-processed"
    status = "Enabled"
    filter { prefix = "processed/" }
    transition {
      days          = var.lifecycle_transition_days
      storage_class = "INTELLIGENT_TIERING"
    }
  }

  rule {
    id     = "intelligent-tiering-curated"
    status = "Enabled"
    filter { prefix = "curated/" }
    transition {
      days          = var.lifecycle_transition_days
      storage_class = "INTELLIGENT_TIERING"
    }
  }
}

# --- Quarantine bucket (separate from data lake for blast-radius isolation) ---
resource "aws_s3_bucket" "quarantine" {
  bucket        = "${var.project}-quarantine"
  force_destroy = true

  tags = {
    Project     = var.project
    Environment = var.environment
    Phase       = "6"
    Purpose     = "quarantine"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "quarantine" {
  bucket = aws_s3_bucket.quarantine.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "quarantine" {
  bucket                  = aws_s3_bucket.quarantine.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle: expire quarantine records after 90 days
resource "aws_s3_bucket_lifecycle_configuration" "quarantine" {
  bucket = aws_s3_bucket.quarantine.id
  rule {
    id     = "expire-quarantine"
    status = "Enabled"
    filter { prefix = "" }
    expiration { days = 90 }
  }
}

# =============================================================================
# Outputs
# =============================================================================
output "data_lake_bucket" {
  description = "S3 Data Lake bucket name"
  value       = aws_s3_bucket.data_lake.bucket
}

output "quarantine_bucket" {
  description = "S3 Quarantine bucket name"
  value       = aws_s3_bucket.quarantine.bucket
}
