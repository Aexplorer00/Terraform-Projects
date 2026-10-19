# ==============================================================================
# SRE Resilient Event-Driven Ingestion Pipeline
# Target: AWS / Floci
# ==============================================================================

# ------------------------------------------------------------------------------
# STEP 1: SECURITY & CRYPTOGRAPHY (KMS CMK)
# ------------------------------------------------------------------------------
# In production SRE architectures, relying on default AWS-managed keys (aws/s3)
# restricts cross-account access and disables custom key rotation audits.
# Here we provision a Customer Managed Key (CMK) with automated key rotation.
#
# Requirements:
# 1. Resource "aws_kms_key" named "pipeline_key":
#    - description: "CMK for S3 ingestion bucket and SQS queues"
#    - deletion_window_in_days: 7
#    - enable_key_rotation: true
#    - tags: Map with Name = "${var.project_name}-kms-${var.environment}" and Environment = var.environment
#
# 2. Resource "aws_kms_alias" named "pipeline_key_alias":
#    - name: "alias/${var.project_name}-key"
#    - target_key_id: reference the id of the pipeline_key resource created above
#
# TODO 1: Implement the "aws_kms_key" resource named "pipeline_key" below:
resource "aws_kms_key" "pipeline_key" {
  description             = "CMK for S3 Ingestion bucket and SQS queue"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  tags = {
    Name        = "${var.project_name}-kms-${var.environment}"
    Environment = var.environment
  }
}


# TODO 2: Implement the "aws_kms_alias" resource named "pipeline_key_alias" below:

resource "aws_kms_alias" "pipeline_key_alias" {
  name          = "alias/${var.project_name}-key"
  target_key_id = aws_kms_key.pipeline_key.key_id
}

# ------------------------------------------------------------------------------
# STEP 2: RESILIENT STORAGE LAYER (S3 INGESTION BUCKET)
# ------------------------------------------------------------------------------
# In enterprise architectures, raw ingestion data needs two critical safeguards:
# 1. Versioning: Protects against accidental object overwrites and ransomware deletes.
# 2. Enforced CMK Encryption: Uses our KMS key so all stored objects are encrypted
#    using SSE-KMS rather than unmanaged default encryption.
#
# Requirements:
# 1. Resource "aws_s3_bucket" named "ingestion_vault":
#    - bucket: "${var.project_name}-vault-${var.environment}"
#    - tags: Map with Name = "${var.project_name}-vault-${var.environment}" and Environment = var.environment
#
# 2. Resource "aws_s3_bucket_versioning" named "vault_versioning":
#    - bucket: reference the id of aws_s3_bucket.ingestion_vault
#    - versioning_configuration: status = "Enabled"
#
# 3. Resource "aws_s3_bucket_server_side_encryption_configuration" named "vault_crypto":
#    - bucket: reference the id of aws_s3_bucket.ingestion_vault
#    - rule block containing:
#        apply_server_side_encryption_by_default:
#          - sse_algorithm     = "aws:kms"
#          - kms_master_key_id = aws_kms_key.pipeline_key.arn
#
# TODO 3: Implement the "aws_s3_bucket" resource named "ingestion_vault" below:
resource "aws_s3_bucket" "ingestion_bucket" {
  bucket = "${var.project_name}-vault-${var.environment}"
  tags = {
    Name        = "${var.project_name}-vault-${var.environment}"
    Environment = var.environment
  }
}



# TODO 4: Implement the "aws_s3_bucket_versioning" resource named "vault_versioning" below:
resource "aws_s3_bucket_versioning" "vault_versioning" {
  bucket = aws_s3_bucket.ingestion_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# TODO 5: Implement the "aws_s3_bucket_server_side_encryption_configuration" resource named "vault_crypto" below:
resource "aws_s3_bucket_server_side_encryption_configuration" "vault_crypto" {
  bucket = aws_s3_bucket.ingestion_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.pipeline_key.arn
    }
  }
}

# ------------------------------------------------------------------------------
# STEP 3: RESILIENT MESSAGING LAYER (DEAD-LETTER QUEUE & PRIMARY SQS QUEUE)
# ------------------------------------------------------------------------------
# In distributed systems, downstream consumer failures happen (code bugs, timeouts,
# invalid payloads). Without a Dead-Letter Queue (DLQ), failing messages loop
# indefinitely, clogging the queue (Head-of-Line Blocking) and driving up compute costs.
#
# Requirements:
# 1. Resource "aws_sqs_queue" named "ingestion_dlq":
#    - name: "${var.project_name}-dlq-${var.environment}"
#    - message_retention_seconds: var.dlq_message_retention_seconds (14 days for forensic debugging)
#    - kms_master_key_id: aws_kms_key.pipeline_key.arn
#    - tags: Map with Name = "${var.project_name}-dlq-${var.environment}" and Environment = var.environment
#
# 2. Resource "aws_sqs_queue" named "ingestion_queue":
#    - name: "${var.project_name}-queue-${var.environment}"
#    - visibility_timeout_seconds: 30
#    - message_retention_seconds: var.sqs_message_retention_seconds
#    - kms_master_key_id: aws_kms_key.pipeline_key.arn
#    - redrive_policy: jsonencode({
#        deadLetterTargetArn = aws_sqs_queue.ingestion_dlq.arn
#        maxReceiveCount     = var.max_receive_count
#      })
#    - tags: Map with Name = "${var.project_name}-queue-${var.environment}" and Environment = var.environment
#
# TODO 6: Implement the "aws_sqs_queue" resource named "ingestion_dlq" below:
resource "aws_sqs_queue" "ingestion_dlq" {
  name                      = "${var.project_name}-dlq-${var.environment}"
  message_retention_seconds = var.dlq_message_retention_seconds
  kms_master_key_id         = aws_kms_key.pipeline_key.arn
  tags = {
    Name        = "${var.project_name}-dlq-${var.environment}"
    Environment = var.environment
  }
}



# TODO 7: Implement the "aws_sqs_queue" resource named "ingestion_queue" below:
resource "aws_sqs_queue" "ingestion_queue" {
  name                       = "${var.project_name}-queue-${var.environment}"
  visibility_timeout_seconds = 30
  message_retention_seconds  = var.sqs_message_retention_seconds
  kms_master_key_id          = aws_kms_key.pipeline_key.arn
  redrive_policy = jsonencode({
    "deadLetterTargetArn" = aws_sqs_queue.ingestion_dlq.arn
    "maxReceiveCount"     = var.max_receive_count
  })
  tags = {
    Name        = "${var.project_name}-queue-${var.environment}"
    Environment = var.environment
  }
}

# ------------------------------------------------------------------------------
# STEP 4: LEAST-PRIVILEGE WIRING (SQS POLICY & S3 BUCKET NOTIFICATION)
# ------------------------------------------------------------------------------
# In AWS, S3 pushes events directly to SQS without using an IAM Role.
# Therefore, SQS must have a Resource-Based Policy allowing S3 to call SendMessage.
#
# Production Security Guardrail (Preventing "Confused Deputy"):
# Never use open wildcard permissions. The policy must contain a Condition block:
#   Condition = {
#     ArnEquals = {
#       "aws:SourceArn" = aws_s3_bucket.ingestion_bucket.arn
#     }
#   }
# This ensures ONLY our specific S3 bucket can publish messages to this queue.
#
# Requirements:
# 1. Resource "aws_sqs_queue_policy" named "allow_s3_ingestion":
#    - queue_url: aws_sqs_queue.ingestion_queue.id
#    - policy: jsonencode({
#        Version   = "2012-10-17"
#        Statement = [
#          {
#            Sid       = "AllowS3PublishEvents"
#            Effect    = "Allow"
#            Principal = { Service = "s3.amazonaws.com" }
#            Action    = "sqs:SendMessage"
#            Resource  = aws_sqs_queue.ingestion_queue.arn
#            Condition = {
#              ArnEquals = {
#                "aws:SourceArn" = aws_s3_bucket.ingestion_bucket.arn
#              }
#            }
#          }
#        ]
#      })
#
# 2. Resource "aws_s3_bucket_notification" named "bucket_notification":
#    - bucket: aws_s3_bucket.ingestion_bucket.id
#    - queue block:
#        queue_arn = aws_sqs_queue.ingestion_queue.arn
#        events    = ["s3:ObjectCreated:*"]
#    - depends_on: [aws_sqs_queue_policy.allow_s3_ingestion]
#      (Why? S3 verifies queue permissions on creation; without depends_on it would fail!)
#
# TODO 8: Implement the "aws_sqs_queue_policy" resource named "allow_s3_ingestion" below:
resource "aws_sqs_queue_policy" "allow_s3_ingestion" {
  queue_url = aws_sqs_queue.ingestion_queue.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowS3PublishEvents"
        Effect    = "Allow"
        Principal = { Service = "s3.amazonaws.com" }
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.ingestion_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_s3_bucket.ingestion_bucket.arn
          }
        }

      }
    ]
  })
}



# TODO 9: Implement the "aws_s3_bucket_notification" resource named "bucket_notification" below:
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.ingestion_bucket.id
  queue {
    queue_arn = aws_sqs_queue.ingestion_queue.arn
    events    = ["s3:ObjectCreated:*"]
  }
  depends_on = [aws_sqs_queue_policy.allow_s3_ingestion]
}





