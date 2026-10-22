output "vpc_id" {
  description = "The ID of the custom VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "The IDs of the multi-AZ private subnets"
  value       = aws_subnet.private[*].id
}

output "alb_arn" {
  description = "The ARN of the internal Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "The internal DNS name of the ALB"
  value       = aws_lb.main.dns_name
}

output "target_group_arn" {
  description = "The ARN of the backend target group"
  value       = aws_lb_target_group.app.arn
}

output "alb_security_group_id" {
  description = "The security group ID of the ALB"
  value       = aws_security_group.alb.id
}

output "app_security_group_id" {
  description = "The chained security group ID of the backend app"
  value       = aws_security_group.app.id
}
