variable "aws_region" {
  type        = string
  description = "AWS deployment region"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Project identifier for naming and tagging"
  default     = "private-microservice"
}

variable "environment" {
  type        = string
  description = "Environment tier (prod/stage/dev)"
  default     = "prod"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the custom VPC"
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of AZs for multi-AZ high availability"
  default     = ["us-east-1a", "us-east-1b"]
}

variable "app_port" {
  type        = number
  description = "The port on which the private backend microservice listens"
  default     = 8080
}
