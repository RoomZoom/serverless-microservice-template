# src/main.py
import json
from adapters import dynamodb_adapter, sqs_adapter


def handler(event, context):
    if "body" not in event:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing body"})}
    try:
        body = json.loads(event["body"])
        dynamodb_adapter.put_item("my-table-dev", body)
        sqs_adapter.send_message(
            "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue-dev", body
        )
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Item stored and message sent."}),
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
