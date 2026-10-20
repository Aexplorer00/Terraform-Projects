variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (e.g., prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Base project name used for naming resources"
  type        = string
  default     = "sre-serverless-engine"
}

variable "table_billing_mode" {
  description = "Billing mode for DynamoDB: PAY_PER_REQUEST (On-Demand) or PROVISIONED"
  type        = string
  default     = "PAY_PER_REQUEST"
}
