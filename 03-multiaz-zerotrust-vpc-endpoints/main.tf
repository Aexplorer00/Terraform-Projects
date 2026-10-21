# ==============================================================================
# PROJECT 03: Multi-AZ Zero-Trust VPC & Private Gateway Endpoints
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Custom VPC
# ------------------------------------------------------------------------------
# TODO 1: Define the custom VPC
# Requirements:
# - CIDR block from var.vpc_cidr
# - enable_dns_support = true
# - enable_dns_hostnames = true (Crucial for VPC endpoints & PrivateLink!)
# - Name tag formatted as "${var.project_name}-vpc"
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# ------------------------------------------------------------------------------
# 2. Internet Gateway (For Public Subnet Ingress/Egress)
# ------------------------------------------------------------------------------
# TODO 2: Create and attach the Internet Gateway
# Requirements:
# - vpc_id linked to aws_vpc.main.id
# - Name tag: "${var.project_name}-igw"
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# ------------------------------------------------------------------------------
# 3. Multi-AZ Public Subnets (Tier 1)
# ------------------------------------------------------------------------------
# TODO 3: Create public subnets using count or for_each across availability zones
# Requirements:
# - count = length(var.public_subnet_cidrs)
# - vpc_id = aws_vpc.main.id
# - cidr_block = var.public_subnet_cidrs[count.index]
# - availability_zone = var.availability_zones[count.index]
# - map_public_ip_on_launch = true
# - Name tag: "${var.project_name}-public-subnet-${count.index + 1}"
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  count                   = length(var.public_subnet_cidrs)
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
  }
}

# ------------------------------------------------------------------------------
# 4. Multi-AZ Private Subnets (Tier 2 - Zero Direct Internet Access)
# ------------------------------------------------------------------------------
# TODO 4: Create private subnets across the same availability zones
# Requirements:
# - count = length(var.private_subnet_cidrs)
# - vpc_id = aws_vpc.main.id
# - cidr_block = var.private_subnet_cidrs[count.index]
# - availability_zone = var.availability_zones[count.index]
# - map_public_ip_on_launch = false
# - Name tag: "${var.project_name}-private-subnet-${count.index + 1}"
resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  count                   = length(var.private_subnet_cidrs)
  cidr_block              = var.private_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
  }
}

# ------------------------------------------------------------------------------
# 5. Public Route Table & Default Route to Internet Gateway
# ------------------------------------------------------------------------------
# TODO 5: Create public route table with default 0.0.0.0/0 route via IGW
# Requirements:
# - vpc_id = aws_vpc.main.id
# - route block: cidr_block = "0.0.0.0/0", gateway_id = aws_internet_gateway.gw.id
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
  # TODO: Fill in Public Route Table
}


# TODO 6: Associate Public Subnets with Public Route Table
# Requirements:
# - count = length(aws_subnet.public)
# - subnet_id = aws_subnet.public[count.index].id
# - route_table_id = aws_route_table.public.id
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
  # TODO: Fill in Public Route Table Association
}

# ------------------------------------------------------------------------------
# 6. Private Route Table (Isolated from IGW)
# ------------------------------------------------------------------------------
# TODO 7: Create private route table
# Requirements:
# - vpc_id = aws_vpc.main.id
# - NO default route to Internet Gateway!
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  # No default route to IGW (isolated - zero internet trust!)
  # TODO: Fill in Private Route Table
}

# TODO 8: Associate Private Subnets with Private Route Table
# Requirements:
# - count = length(aws_subnet.private)
# - subnet_id = aws_subnet.private[count.index].id
# - route_table_id = aws_route_table.private.id
resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
  # TODO: Fill in Private Route Table Association
}

# ------------------------------------------------------------------------------
# 7. VPC Gateway Endpoints (S3 & DynamoDB) - The FinOps & Zero-Trust Superpower
# ------------------------------------------------------------------------------
# TODO 9: Create S3 Gateway Endpoint
# Requirements:
# - vpc_id = aws_vpc.main.id
# - service_name = "com.amazonaws.${var.aws_region}.s3"
# - vpc_endpoint_type = "Gateway"
# - route_table_ids = [aws_route_table.private.id]
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
  tags = {
    Name = "${var.project_name}-s3-endpoint"
  }
}

# TODO 10: Create DynamoDB Gateway Endpoint
# Requirements:
# - vpc_id = aws_vpc.main.id
# - service_name = "com.amazonaws.${var.aws_region}.dynamodb"
# - vpc_endpoint_type = "Gateway"
# - route_table_ids = [aws_route_table.private.id]
resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
  tags = {
    Name = "${var.project_name}-dynamodb-endpoint"
  }
  # TODO: Fill in DynamoDB Gateway Endpoint
}
