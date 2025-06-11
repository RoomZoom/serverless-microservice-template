# src/adapters/sqs_adapter.py
import json

import boto3

from src.models.payload_models import QueueMessage
from src.models.validation import validate_model

_sqs = None


def _get_sqs():
    """Get or create SQS client"""
    global _sqs
    if _sqs is None:
        _sqs = boto3.client("sqs")
    return _sqs


def send_message(queue_url, message_body):
    validated, errors = validate_model(QueueMessage, message_body)
    if errors:
        raise ValueError(f"Invalid queue message: {errors}")
    if validated is None:
        raise ValueError("Validation failed but no errors returned")
    sqs = _get_sqs()
    return sqs.send_message(
        QueueUrl=queue_url, MessageBody=json.dumps(validated.dict())
    )
