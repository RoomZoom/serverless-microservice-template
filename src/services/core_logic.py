import logging
from models.payload_models import CreateItemRequest, ItemCreatedEvent
from adapters import dynamodb_adapter, sqs_adapter, kafka_adapter

logger = logging.getLogger(__name__)


def process_item_creation(item: CreateItemRequest, table_name: str, queue_url: str, 
                         kafka_topic: str, service_name: str, correlation_id: str):
    """
    Core business logic for item creation
    Handles DynamoDB storage, SQS messaging, and Kafka event publishing
    """
    try:
        logger.info(
            f"Processing item creation: {item.id}, correlation_id: {correlation_id}"
        )

        dynamodb_adapter.put_item(table_name, item.dict())
        logger.info(f"Item stored in DynamoDB: {item.id}")

        sqs_adapter.send_message(
            queue_url,
            {"id": item.id, "action": "created", "correlation_id": correlation_id},
        )
        logger.info(f"Message sent to SQS: {item.id}")

        event = ItemCreatedEvent.from_create_request(item, service_name, correlation_id)
        kafka_adapter.send_message(kafka_topic, event.dict(), key=item.id)
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
