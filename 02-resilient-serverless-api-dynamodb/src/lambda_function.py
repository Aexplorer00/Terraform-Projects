import json
import os
import time
import boto3
from botocore.exceptions import ClientError

# Production Practice: Determine endpoint for local emulator vs real AWS
endpoint_url = os.environ.get("AWS_ENDPOINT_URL", "http://host.containers.internal:4566")

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=endpoint_url,
    region_name="us-east-1",
    aws_access_key_id="mock_access_key",
    aws_secret_access_key="mock_secret_key"
)

table_name = os.environ.get("TABLE_NAME", "sre-serverless-engine-transactions-prod")
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        # Parse body from API Gateway proxy integration
        raw_body = event.get("body", "{}")
        body = json.loads(raw_body) if isinstance(raw_body, str) else (raw_body or {})

        transaction_id = body.get("transaction_id")
        customer_id = body.get("customer_id")
        amount = body.get("amount")

        if not transaction_id or not customer_id or amount is None:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing required fields: transaction_id, customer_id, amount"}),
            }

        # 90 days retention for audit compliance
        ttl_seconds = int(time.time()) + (90 * 24 * 60 * 60)

        item = {
            "transaction_id": str(transaction_id),
            "customer_id": str(customer_id),
            "amount": str(amount),
            "status": "PROCESSED",
            "created_at": int(time.time()),
            "ttl": ttl_seconds,
        }

        # Idempotent write: Fail if transaction_id already exists
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(transaction_id)"
        )

        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "message": "Transaction recorded successfully",
                "transaction_id": transaction_id,
                "status": "PROCESSED"
            }),
        }

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {
                "statusCode": 409,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Conflict: Transaction already exists (Idempotency check)",
                    "transaction_id": transaction_id
                }),
            }
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }
