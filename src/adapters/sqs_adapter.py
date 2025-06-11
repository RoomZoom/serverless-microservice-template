# src/adapters/sqs_adapter.py
import json

import boto3

from src.models.payload_models import QueueMessage
from src.models.validation import validate_model

sqs = boto3.client("sqs")


def send_message(queue_url, message_body):
    validated, errors = validate_model(QueueMessage, message_body)
    if errors:
        raise ValueError(f"Invalid queue message: {errors}")
    if validated is None:
        raise ValueError("Validation failed but no errors returned")
    return sqs.send_message(
        QueueUrl=queue_url, MessageBody=json.dumps(validated.dict())
    )
