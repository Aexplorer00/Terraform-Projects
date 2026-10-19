output "kms_key_arn" {
  description = "ARN of the Customer Managed KMS Key"
  value       = aws_kms_key.pipeline_key.arn
}

output "kms_key_alias" {
  description = "Alias of the Customer Managed KMS Key"
  value       = aws_kms_alias.pipeline_key_alias.name
}

output "s3_bucket_name" {
  description = "Name of the S3 Ingestion Bucket"
  value       = aws_s3_bucket.ingestion_bucket.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 Ingestion Bucket"
  value       = aws_s3_bucket.ingestion_bucket.arn
}

output "primary_queue_url" {
  description = "URL of the primary SQS ingestion queue"
  value       = aws_sqs_queue.ingestion_queue.id
}

output "primary_queue_arn" {
  description = "ARN of the primary SQS ingestion queue"
  value       = aws_sqs_queue.ingestion_queue.arn
}

output "dlq_url" {
  description = "URL of the Dead-Letter Queue"
  value       = aws_sqs_queue.ingestion_dlq.id
}

output "dlq_arn" {
  description = "ARN of the Dead-Letter Queue"
  value       = aws_sqs_queue.ingestion_dlq.arn
}
