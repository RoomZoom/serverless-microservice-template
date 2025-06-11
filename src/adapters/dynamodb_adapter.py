# src/adapters/dynamodb_adapter.py
import boto3
from models.payload_models import CreateItemRequest
from models.validation import validate_model

dynamodb = boto3.resource("dynamodb")


def get_item(table_name, key):
    table = dynamodb.Table(table_name)
    response = table.get_item(Key=key)
    return response.get("Item")


def put_item(table_name, item_dict):
    validated, errors = validate_model(CreateItemRequest, item_dict)
    if errors:
        raise ValueError(f"Invalid item format: {errors}")
    if validated is None:
        raise ValueError("Validation failed but no errors returned")
    table = dynamodb.Table(table_name)
    return table.put_item(Item=validated.dict())
