# src/main.py
import json
import logging
import uuid
from adapters import dynamodb_adapter, sqs_adapter, kafka_adapter
from models.payload_models import CreateItemRequest, ItemCreatedEvent
from utils.config import get_env_variable

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
        result = process_item_creation(item, correlation_id)

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
            f"Error processing API Gateway event: {str(e)}, correlation_id: {correlation_id}"
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
        result = process_item_creation(item, correlation_id)

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


def process_item_creation(item: CreateItemRequest, correlation_id: str):
    """
    Core business logic for item creation
    Handles DynamoDB storage, SQS messaging, and Kafka event publishing
    """
    try:
        logger.info(
            f"Processing item creation: {item.id}, correlation_id: {correlation_id}"
        )

        # Store in DynamoDB
        dynamodb_adapter.put_item(TABLE_NAME, item.dict())
        logger.info(f"Item stored in DynamoDB: {item.id}")

        # Send to SQS for async processing
        sqs_adapter.send_message(
            QUEUE_URL,
            {"id": item.id, "action": "created", "correlation_id": correlation_id},
        )
        logger.info(f"Message sent to SQS: {item.id}")

        # Publish event to Kafka
        event = ItemCreatedEvent.from_create_request(item, SERVICE_NAME, correlation_id)
        kafka_adapter.send_message(KAFKA_TOPIC, event.dict(), key=item.id)
        logger.info(f"Event published to Kafka: {item.id}")

        return {
            "message": "Item created and events published successfully",
            "item_id": item.id,
            "correlation_id": correlation_id,
            "services": {"dynamodb": "success", "sqs": "success", "kafka": "success"},
        }

    except Exception as e:
        logger.error(
            f"Error in process_item_creation: {str(e)}, correlation_id: {correlation_id}"
        )
        raise


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
