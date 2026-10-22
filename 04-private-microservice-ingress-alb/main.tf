# ==============================================================================
# PROJECT 04: Private Microservice Ingress with Internal ALB & SG Chaining
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Base VPC & Multi-AZ Subnets
# ------------------------------------------------------------------------------
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Multi-AZ Private Subnets for Internal ALB & Microservices
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 11)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
  }
}

# ------------------------------------------------------------------------------
# 2. Security Group Chaining (Zero-Trust Tier Separation)
# ------------------------------------------------------------------------------

# TODO 1: Create the ALB Security Group (Front Door)
# Requirements:
# - name: "${var.project_name}-alb-sg"
# - vpc_id: aws_vpc.main.id
# - ingress: Port 80 (TCP) from within the VPC (var.vpc_cidr)
# - egress: Port var.app_port (8080) to 0.0.0.0/0 (or restricted to VPC)
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Controls ingress to internal Application Load Balancer"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  egress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

}

# TODO 2: Create the Backend Microservice Security Group (Chained to ALB!)
# Requirements:
# - name: "${var.project_name}-app-sg"
# - vpc_id: aws_vpc.main.id
# - ingress: Port var.app_port (8080) ALLOWED ONLY FROM aws_security_group.alb.id
#   (Use 'security_groups = [aws_security_group.alb.id]' - NO CIDR BLOCKS!)
# - egress: Port 443 (HTTPS) to 0.0.0.0/0 for AWS API / Endpoint traffic
resource "aws_security_group" "app" {
  name        = "${var.project_name}-app-sg"
  description = "Chained security group allowing ingress strictly from ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

}
# ------------------------------------------------------------------------------
# 3. Target Group with Production Health Checks
# ------------------------------------------------------------------------------

# TODO 3: Create the Target Group for backend microservices
# Requirements:
# - name: "${var.project_name}-tg"
# - port: var.app_port (8080)
# - protocol: "HTTP"
# - vpc_id: aws_vpc.main.id
# - target_type: "instance" (or "ip")
# - health_check block:
#     enabled             = true
#     path                = "/health"
#     port                = var.app_port
#     protocol            = "HTTP"
#     matcher             = "200"
#     interval            = 15
#     timeout             = 5
#     healthy_threshold   = 2
#     unhealthy_threshold = 3
resource "aws_lb_target_group" "app" {
  name        = "${var.project_name}-tg"
  port        = var.app_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "instance"
  health_check {
    enabled             = true
    path                = "/health"
    port                = var.app_port
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

}

# ------------------------------------------------------------------------------
# 4. Internal Application Load Balancer
# ------------------------------------------------------------------------------

# TODO 4: Create the Internal ALB
# Requirements:
# - name: "${var.project_name}-alb"
# - internal: true (Crucial for private microservice architecture!)
# - load_balancer_type: "application"
# - security_groups: [aws_security_group.alb.id]
# - subnets: aws_subnet.private[*].id
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# ------------------------------------------------------------------------------
# 5. HTTP Listener with Default Forward Action
# ------------------------------------------------------------------------------

# TODO 5: Create the ALB Listener on port 80
# Requirements:
# - load_balancer_arn: aws_lb.main.arn
# - port: 80
# - protocol: "HTTP"
# - default_action: type = "forward", target_group_arn = aws_lb_target_group.app.arn
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# ------------------------------------------------------------------------------
# 6. Layer 7 Path-Based Routing & Edge Fixed-Response Rules
# ------------------------------------------------------------------------------

# TODO 6: Create Layer 7 Path Routing Rule for API traffic (/api/v1/*)
# Requirements:
# - listener_arn: aws_lb_listener.http.arn
# - priority: 10 (Lower number = evaluated first)
# - action block: type = "forward", target_group_arn = aws_lb_target_group.app.arn
# - condition block: path_pattern block with values = ["/api/v1/*"]
resource "aws_lb_listener_rule" "api_route" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
  condition {
    path_pattern {
      values = ["/api/v1/*"]
    }
  }
}

# TODO 7: Create Layer 7 Edge Health Rule (/health)
# SRE Best Practice: Respond directly from ALB edge without hitting backend!
# Requirements:
# - listener_arn: aws_lb_listener.http.arn
# - priority: 20
# - action block:
#     type = "fixed-response"
#     fixed_response block:
#       content_type = "text/plain"
#       message_body = "HEALTHY-ALB-EDGE"
#       status_code  = "200"
# - condition block: path_pattern block with values = ["/health"]
resource "aws_lb_listener_rule" "edge_health" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20
  action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "HEALTHY-ALB-EDGE"
      status_code  = "200"
    }
  }
  condition {
    path_pattern {
      values = ["/health"]
    }
  }
}
