# src/main.py
import json
import logging
import uuid

from src.models.payload_models import CreateItemRequest
from src.services.core_logic import process_item_creation
from src.utils.config import get_env_variable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ENVIRONMENT = get_env_variable("ENVIRONMENT", "dev")
SERVICE_NAME = get_env_variable("SERVICE_NAME", "microservice-template")
TABLE_NAME = get_env_variable("DYNAMODB_TABLE_NAME", f"my-table-{ENVIRONMENT}")
QUEUE_URL = get_env_variable(
    "SQS_QUEUE_URL",
    f"https://sqs.us-east-1.amazonaws.com/123456789012/my-queue-{ENVIRONMENT}",
)
KAFKA_TOPIC = get_env_variable("KAFKA_TOPIC", f"microservice-events-{ENVIRONMENT}")


def handler(event, context):
    """
    Main Lambda handler for direct invocations
    Supports multiple event sources: API Gateway, SQS, EventBridge, etc.
    """
    correlation_id = str(uuid.uuid4())

    try:
        logger.info(
            f"Processing event: {json.dumps(event)}, correlation_id: {correlation_id}"
        )

        # Determine event source and route accordingly
        if "httpMethod" in event or "requestContext" in event:
            # API Gateway event
            return handle_api_gateway_event(event, context, correlation_id)
        elif "Records" in event:
            # SQS or other record-based event
            return handle_records_event(event, context, correlation_id)
        else:
            # Direct invocation or other event types
            return handle_direct_invocation(event, context, correlation_id)

    except Exception as e:
        logger.error(
            f"Error in main handler: {str(e)}, correlation_id: {correlation_id}"
        )
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": "Internal server error", "correlation_id": correlation_id}
            ),
        }


def handle_api_gateway_event(event, context, correlation_id):
    """Handle API Gateway events"""
    try:
        if "body" not in event or not event["body"]:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "Missing request body", "correlation_id": correlation_id}
                ),
            }

        body = json.loads(event["body"])

        # Validate request
        item = CreateItemRequest(**body)

        # Process the item creation
        result = process_item_creation_wrapper(item, correlation_id)

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-ID": correlation_id,
            },
            "body": json.dumps(result),
        }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}, correlation_id: {correlation_id}")
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": f"Validation error: {str(e)}",
                    "correlation_id": correlation_id,
                }
            ),
        }
    except Exception as e:
        logger.error(
            f"Error processing API Gateway event: {str(e)}, "
            f"correlation_id: {correlation_id}"
        )
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": "Internal server error", "correlation_id": correlation_id}
            ),
        }


def handle_records_event(event, context, correlation_id):
    """Handle SQS or other record-based events"""
    results = []

    try:
        for record in event["Records"]:
            record_result = process_record(record, correlation_id)
            results.append(record_result)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Processed {len(results)} records",
                    "results": results,
                    "correlation_id": correlation_id,
                }
            ),
        }

    except Exception as e:
        logger.error(
            f"Error processing records: {str(e)}, correlation_id: {correlation_id}"
        )
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": "Error processing records", "correlation_id": correlation_id}
            ),
        }


def handle_direct_invocation(event, context, correlation_id):
    """Handle direct Lambda invocation"""
    try:
        # Assume direct invocation contains item data
        item = CreateItemRequest(**event)
        result = process_item_creation_wrapper(item, correlation_id)

        return {"statusCode": 200, "body": json.dumps(result)}

    except Exception as e:
        logger.error(
            f"Error in direct invocation: {str(e)}, correlation_id: {correlation_id}"
        )
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": "Error processing direct invocation",
                    "correlation_id": correlation_id,
                }
            ),
        }


def process_item_creation_wrapper(item: CreateItemRequest, correlation_id: str):
    """Wrapper for the core business logic"""
    table_name = TABLE_NAME or f"my-table-{ENVIRONMENT}"
    queue_url = (
        QUEUE_URL
        or f"https://sqs.us-east-1.amazonaws.com/123456789012/my-queue-{ENVIRONMENT}"
    )
    kafka_topic = KAFKA_TOPIC or f"microservice-events-{ENVIRONMENT}"
    service_name = SERVICE_NAME or "microservice-template"

    return process_item_creation(
        item, table_name, queue_url, kafka_topic, service_name, correlation_id
    )


def process_record(record, correlation_id):
    """Process individual SQS record or similar"""
    try:
        # Extract message body
        if "body" in record:
            message_body = json.loads(record["body"])
        else:
            message_body = record

        logger.info(
            f"Processing record: {message_body}, correlation_id: {correlation_id}"
        )

        # Add your record processing logic here
        # For example, this could be processing messages from SQS

        return {
            "record_id": record.get("messageId", "unknown"),
            "status": "processed",
            "correlation_id": correlation_id,
        }

    except Exception as e:
        logger.error(
            f"Error processing record: {str(e)}, correlation_id: {correlation_id}"
        )
        return {
            "record_id": record.get("messageId", "unknown"),
            "status": "failed",
            "error": str(e),
            "correlation_id": correlation_id,
        }
