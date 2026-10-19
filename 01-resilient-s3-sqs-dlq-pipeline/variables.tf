variable "aws_region" {
  description = "AWS region for provisioning"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (e.g. prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Base project name used for resource naming"
  type        = string
  default     = "sre-ingestion-pipeline"
}

variable "sqs_message_retention_seconds" {
  description = "Retention period for primary SQS queue messages in seconds (default: 4 days)"
  type        = number
  default     = 345600
}

variable "dlq_message_retention_seconds" {
  description = "Retention period for DLQ messages in seconds (default: 14 days for forensics)"
  type        = number
  default     = 1209600
}

variable "max_receive_count" {
  description = "Number of times a message can be delivered before routing to DLQ"
  type        = number
  default     = 3
}
