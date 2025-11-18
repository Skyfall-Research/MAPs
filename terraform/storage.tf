# Storage Configuration - DynamoDB and S3
# NOTE: DynamoDB and S3 resources are commented out because they already exist
# TODO: Later we can add environment-specific resources or import existing ones

# ==============================================================================
# DynamoDB Table for Leaderboard (COMMENTED OUT - using existing)
# ==============================================================================

# # resource "aws_dynamodb_table" "leaderboard" {
#   name           = var.dynamodb_table_name
#   billing_mode   = var.dynamodb_billing_mode
#   read_capacity  = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_read_capacity : null
#   write_capacity = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_write_capacity : null
#   hash_key       = "parkId"
#
#   # Primary key attribute
#   attribute {
#     name = "parkId"
#     type = "S"
#   }
#
#   # Attributes for GSI
#   attribute {
#     name = "mode"
#     type = "S"
#   }
#
#   attribute {
#     name = "score"
#     type = "N"
#   }
#
#   # Global Secondary Index for querying by mode and score
#   global_secondary_index {
#     name            = "score-index"
#     hash_key        = "mode"
#     range_key       = "score"
#     projection_type = "ALL"
#     read_capacity   = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_read_capacity : null
#     write_capacity  = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_write_capacity : null
#   }
#
#   # Enable point-in-time recovery for data protection
#   point_in_time_recovery {
#     enabled = true
#   }
#
#   # Server-side encryption
#   server_side_encryption {
#     enabled = true
#   }
#
#   tags = {
#     Name = "${var.project_name}-leaderboard"
#   }
# }

# ==============================================================================
# S3 Bucket for Trajectory Storage (COMMENTED OUT - using existing)
# ==============================================================================

# # resource "aws_s3_bucket" "trajectories" {
#   bucket = var.s3_bucket_name
#
#   tags = {
#     Name = "${var.project_name}-trajectories"
#   }
# }
#
# # Enable versioning for data protection
# resource "aws_s3_bucket_versioning" "trajectories" {
#   bucket = aws_s3_bucket.trajectories.id
#
#   versioning_configuration {
#     status = "Enabled"
#   }
# }
#
# # Block all public access
# resource "aws_s3_bucket_public_access_block" "trajectories" {
#   bucket = aws_s3_bucket.trajectories.id
#
#   block_public_acls       = true
#   block_public_policy     = true
#   ignore_public_acls      = true
#   restrict_public_buckets = true
# }
#
# # Server-side encryption
# resource "aws_s3_bucket_server_side_encryption_configuration" "trajectories" {
#   bucket = aws_s3_bucket.trajectories.id
#
#   rule {
#     apply_server_side_encryption_by_default {
#       sse_algorithm = "AES256"
#     }
#   }
# }
#
# # Lifecycle policy to reduce storage costs
# resource "aws_s3_bucket_lifecycle_configuration" "trajectories" {
#   bucket = aws_s3_bucket.trajectories.id
#
#   rule {
#     id     = "archive-old-trajectories"
#     status = "Enabled"
#
#     # Transition to Glacier after 90 days
#     transition {
#       days          = 90
#       storage_class = "GLACIER"
#     }
#
#     # Expire (delete) after 365 days
#     expiration {
#       days = 365
#     }
#   }
#
#   rule {
#     id     = "delete-old-versions"
#     status = "Enabled"
#
#     # Delete non-current versions after 30 days
#     noncurrent_version_expiration {
#       noncurrent_days = 30
#     }
#   }
# }
#
# # CORS configuration for potential browser uploads
# resource "aws_s3_bucket_cors_configuration" "trajectories" {
#   bucket = aws_s3_bucket.trajectories.id
#
#   cors_rule {
#     allowed_headers = ["*"]
#     allowed_methods = ["GET", "PUT", "POST"]
#     allowed_origins = ["https://${var.domain_name}"]
#     expose_headers  = ["ETag"]
#     max_age_seconds = 3000
#   }
# }