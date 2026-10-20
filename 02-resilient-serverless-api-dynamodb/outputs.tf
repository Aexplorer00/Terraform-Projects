output "kms_key_arn" {
  description = "ARN of the KMS Customer Managed Key"
  value       = aws_kms_key.dynamo_key.arn
}

output "kms_key_alias" {
  description = "Alias of the KMS Customer Managed Key"
  value       = aws_kms_alias.dynamo_key_alias.name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.transactions_table.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.transactions_table.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.transaction_processor.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.transaction_processor.arn
}

output "api_gateway_url" {
  description = "Invocation URL for the deployed API Gateway stage"
  value       = "${aws_api_gateway_stage.api_stage.invoke_url}/transactions"
}
