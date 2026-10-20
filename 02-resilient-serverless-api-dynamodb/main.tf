# ==============================================================================
# SRE Resilient Serverless Transaction Engine
# Target: AWS / Floci
# ==============================================================================

# ------------------------------------------------------------------------------
# STEP 1: SECURITY & CRYPTOGRAPHY (KMS CMK)
# ------------------------------------------------------------------------------
# Production compliance mandates customer-managed encryption keys with
# automated rotation for persistent database storage.
#
# Requirements:
# 1. Resource "aws_kms_key" named "dynamo_key":
#    - description: "CMK for DynamoDB transaction table"
#    - deletion_window_in_days: 7
#    - enable_key_rotation: true
#    - tags: Map with Name = "${var.project_name}-kms-${var.environment}" and Environment = var.environment
#
# 2. Resource "aws_kms_alias" named "dynamo_key_alias":
#    - name: "alias/${var.project_name}-key"
#    - target_key_id: reference the id of aws_kms_key.dynamo_key
#
# TODO 1: Implement "aws_kms_key" resource named "dynamo_key" below:
resource "aws_kms_key" "dynamo_key" {
  description             = "CMK key for dymano transaction"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  tags = {
    Name        = "${var.project_name}-kms-${var.environment}"
    Environment = var.environment
  }
}



# TODO 2: Implement "aws_kms_alias" resource named "dynamo_key_alias" below:
resource "aws_kms_alias" "dynamo_key_alias" {
  name          = "alias/${var.project_name}-key"
  target_key_id = aws_kms_key.dynamo_key.key_id
}

# ------------------------------------------------------------------------------
# STEP 2: RESILIENT NoSQL DATABASE (DYNAMODB TABLE)
# ------------------------------------------------------------------------------
# Requirements:
# - Resource "aws_dynamodb_table" named "transactions_table":
#   - name: "${var.project_name}-transactions-${var.environment}"
#   - billing_mode: var.table_billing_mode ("PAY_PER_REQUEST")
#   - hash_key: "transaction_id"
#   - attribute blocks:
#       - name: "transaction_id", type: "S"
#       - name: "customer_id",    type: "S"
#   - global_secondary_index block:
#       - name: "customer_id-index"
#       - hash_key: "customer_id"
#       - projection_type: "ALL"
#   - ttl block:
#       - attribute_name: "ttl"
#       - enabled: true
#   - server_side_encryption block:
#       - enabled: true
#       - kms_key_arn: aws_kms_key.dynamo_key.arn
#   - tags: Map with Name and Environment
#
# TODO 3: Implement "aws_dynamodb_table" resource named "transactions_table" below:
resource "aws_dynamodb_table" "transactions_table" {
  name         = "${var.project_name}-transactions-${var.environment}"
  billing_mode = var.table_billing_mode
  hash_key     = "transaction_id"

  attribute {
    name = "transaction_id"
    type = "S"
  }

  attribute {
    name = "customer_id"
    type = "S"
  }

  global_secondary_index {
    name            = "customer_id-index"
    hash_key        = "customer_id"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamo_key.arn
  }

  tags = {
    Name        = "${var.project_name}-transactions-${var.environment}"
    Environment = var.environment
  }
}




# ------------------------------------------------------------------------------
# STEP 3: SERVERLESS COMPUTE (LAMBDA & IAM EXECUTION ROLE)
# ------------------------------------------------------------------------------
# Requirements:
# 1. Data source "archive_file" named "lambda_zip":
#    - type: "zip"
#    - source_file: "${path.module}/src/lambda_function.py"
#    - output_path: "${path.module}/lambda_function.zip"
#
# 2. Resource "aws_iam_role" named "lambda_exec_role":
#    - name: "${var.project_name}-lambda-role-${var.environment}"
#    - assume_role_policy: jsonencode policy allowing "lambda.amazonaws.com" to "sts:AssumeRole"
#
# 3. Resource "aws_iam_role_policy" named "lambda_dynamo_policy":
#    - name: "${var.project_name}-dynamo-policy"
#    - role: aws_iam_role.lambda_exec_role.id
#    - policy: jsonencode policy allowing "dynamodb:PutItem", "dynamodb:GetItem" on aws_dynamodb_table.transactions_table.arn
#              and "kms:GenerateDataKey", "kms:Decrypt" on aws_kms_key.dynamo_key.arn
#
# 4. Resource "aws_lambda_function" named "transaction_processor":
#    - function_name: "${var.project_name}-processor-${var.environment}"
#    - filename: data.archive_file.lambda_zip.output_path
#    - source_code_hash: data.archive_file.lambda_zip.output_base64sha256
#    - handler: "lambda_function.lambda_handler"
#    - runtime: "python3.11"
#    - role: aws_iam_role.lambda_exec_role.arn
#    - environment: { TABLE_NAME = aws_dynamodb_table.transactions_table.name, AWS_ENDPOINT_URL = "http://localhost:4566" }
#
# TODO 4: Implement Lambda packaging, IAM Role/Policy, and Lambda Function below:
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/src/lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-lambda_role-${var.environment}"
  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Action" : "sts:AssumeRole",
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_dynamo_policy" {
  name = "${var.project_name}-dynamo-policy"
  role = aws_iam_role.lambda_exec_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ],
        "Effect" : "Allow",
        "Resource" : aws_dynamodb_table.transactions_table.arn
      },
      {
        "Action" : [
          "kms:GenerateDataKey",
          "kms:Decrypt"
        ],
        "Effect" : "Allow",
        "Resource" : aws_kms_key.dynamo_key.arn
      }
    ]
  })
}

resource "aws_lambda_function" "transaction_processor" {
  function_name    = "${var.project_name}-processor-${var.environment}"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  role             = aws_iam_role.lambda_exec_role.arn
  timeout          = 15

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.transactions_table.name
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_dynamo_policy
  ]
}



# ------------------------------------------------------------------------------
# STEP 4: FRONT DOOR & INGRESS (API GATEWAY REST API)
# ------------------------------------------------------------------------------
# Requirements:
# 1. Resource "aws_api_gateway_rest_api" named "api":
#    - name: "${var.project_name}-api-${var.environment}"
#
# 2. Resource "aws_api_gateway_resource" named "transactions_resource":
#    - rest_api_id: aws_api_gateway_rest_api.api.id
#    - parent_id: aws_api_gateway_rest_api.api.root_resource_id
#    - path_part: "transactions"
#
# 3. Resource "aws_api_gateway_method" named "post_method":
#    - rest_api_id: aws_api_gateway_rest_api.api.id
#    - resource_id: aws_api_gateway_resource.transactions_resource.id
#    - http_method: "POST"
#    - authorization: "NONE"
#
# 4. Resource "aws_api_gateway_integration" named "lambda_integration":
#    - rest_api_id: aws_api_gateway_rest_api.api.id
#    - resource_id: aws_api_gateway_resource.transactions_resource.id
#    - http_method: aws_api_gateway_method.post_method.http_method
#    - integration_http_method: "POST"
#    - type: "AWS_PROXY"
#    - uri: aws_lambda_function.transaction_processor.invoke_arn
#
# 5. Resource "aws_api_gateway_deployment" named "api_deployment":
#    - rest_api_id: aws_api_gateway_rest_api.api.id
#    - depends_on: [aws_api_gateway_integration.lambda_integration]
#
# 6. Resource "aws_api_gateway_stage" named "api_stage":
#    - deployment_id: aws_api_gateway_deployment.api_deployment.id
#    - rest_api_id: aws_api_gateway_rest_api.api.id
#    - stage_name: var.environment
#
# 7. Resource "aws_lambda_permission" named "api_gateway_permission":
#    - statement_id: "AllowAPIGatewayInvoke"
#    - action: "lambda:InvokeFunction"
#    - function_name: aws_lambda_function.transaction_processor.function_name
#    - principal: "apigateway.amazonaws.com"
#    - source_arn: "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
#
# TODO 5: Implement API Gateway Ingress, Deployment, and Lambda Permission below:
resource "aws_api_gateway_rest_api" "api" {
  name        = "${var.project_name}-api-${var.environment}"
  description = "API for processing transactions"
}

resource "aws_api_gateway_resource" "transactions_resource" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "transactions"
}

resource "aws_api_gateway_method" "post_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.transactions_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.transactions_resource.id
  http_method             = aws_api_gateway_method.post_method.http_method
  integration_http_method = "POST"
  uri                     = aws_lambda_function.transaction_processor.invoke_arn
  type                    = "AWS_PROXY"


}

resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  depends_on  = [aws_api_gateway_integration.lambda_integration]
}

resource "aws_api_gateway_stage" "api_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.environment
}

resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.transaction_processor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}
