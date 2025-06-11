# src/api/api_handler.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from models.payload_models import CreateItemRequest
from adapters import dynamodb_adapter, kafka_adapter
from services.core_logic import process_item_creation
from utils.config import get_env_variable
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Serverless Microservice API",
    description="A reusable serverless microservice template",
    version="1.0.0",
)

# Configuration
ENVIRONMENT = get_env_variable("ENVIRONMENT", "dev")
SERVICE_NAME = get_env_variable("SERVICE_NAME", "microservice-template")
TABLE_NAME = get_env_variable("DYNAMODB_TABLE_NAME", f"my-table-{ENVIRONMENT}")
QUEUE_URL = get_env_variable(
    "SQS_QUEUE_URL",
    f"https://sqs.us-east-1.amazonaws.com/123456789012/my-queue-{ENVIRONMENT}",
)
KAFKA_TOPIC = get_env_variable("KAFKA_TOPIC", f"microservice-events-{ENVIRONMENT}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": SERVICE_NAME, "environment": ENVIRONMENT}


@app.post("/create")
async def create_item(request: Request):
    """Create an item with full event publishing pipeline"""
    correlation_id = str(uuid.uuid4())

    try:
        # Parse and validate request
        data = await request.json()
        item = CreateItemRequest(**data)

        logger.info(
            f"Processing create request for item {item.id}, correlation_id: {correlation_id}"
        )

        table_name = TABLE_NAME or f"my-table-{ENVIRONMENT}"
        queue_url = QUEUE_URL or f"https://sqs.us-east-1.amazonaws.com/123456789012/my-queue-{ENVIRONMENT}"
        kafka_topic = KAFKA_TOPIC or f"microservice-events-{ENVIRONMENT}"
        service_name = SERVICE_NAME or "microservice-template"
        
        result = process_item_creation(
            item, table_name, queue_url, kafka_topic, service_name, correlation_id
        )

        return JSONResponse(
            status_code=201,
            content=result,
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}, correlation_id: {correlation_id}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}, correlation_id: {correlation_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/item/{item_id}")
async def get_item(item_id: str):
    """Retrieve an item from DynamoDB"""
    try:
        item = dynamodb_adapter.get_item(TABLE_NAME, {"id": item_id})

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        return JSONResponse(status_code=200, content={"item": item})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving item {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/events")
async def get_recent_events(limit: int = 10):
    """Consume recent events from Kafka (for debugging/monitoring)"""
    try:
        messages = kafka_adapter.consume_messages(
            KAFKA_TOPIC, group_id=f"{SERVICE_NAME}-api-consumer", max_messages=limit
        )

        return JSONResponse(
            status_code=200, content={"events": messages, "count": len(messages)}
        )

    except Exception as e:
        logger.error(f"Error consuming Kafka events: {str(e)}")
        raise HTTPException(status_code=500, detail="Error consuming events")


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        kafka_adapter.kafka_adapter.close()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
