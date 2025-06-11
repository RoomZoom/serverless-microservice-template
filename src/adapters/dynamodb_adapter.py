# src/adapters/dynamodb_adapter.py
import boto3

from src.models.payload_models import CreateItemRequest
from src.models.validation import validate_model

_dynamodb = None


def _get_dynamodb():
    """Get or create DynamoDB resource"""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb


def get_item(table_name, key):
    dynamodb = _get_dynamodb()
    table = dynamodb.Table(table_name)
    response = table.get_item(Key=key)
    return response.get("Item")


def put_item(table_name, item_dict):
    validated, errors = validate_model(CreateItemRequest, item_dict)
    if errors:
        raise ValueError(f"Invalid item format: {errors}")
    if validated is None:
        raise ValueError("Validation failed but no errors returned")
    dynamodb = _get_dynamodb()
    table = dynamodb.Table(table_name)
    return table.put_item(Item=validated.dict())
