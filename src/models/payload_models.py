# src/models/payload_models.py
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class CreateItemRequest(BaseModel):
    id: str
    name: str
    description: str


class QueueMessage(BaseModel):
    id: str
    action: str


class KafkaMessage(BaseModel):
    """Standard Kafka message format for the microservice"""

    event_type: str = Field(
        ..., description="Type of event (e.g., 'item.created', 'item.updated')"
    )
    source_service: str = Field(
        ..., description="Name of the service that generated the event"
    )
    entity_id: str = Field(..., description="ID of the entity the event relates to")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    payload: Dict[str, Any] = Field(..., description="Event payload data")
    version: str = Field(default="1.0", description="Event schema version")
    correlation_id: Optional[str] = Field(
        None, description="Correlation ID for tracing"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ItemCreatedEvent(KafkaMessage):
    """Specific event for item creation"""

    event_type: Literal["item.created"] = Field(default="item.created")

    @classmethod
    def from_create_request(
        cls,
        request: CreateItemRequest,
        source_service: str,
        correlation_id: Optional[str] = None,
    ):
        return cls(
            source_service=source_service,
            entity_id=request.id,
            payload=request.dict(),
            correlation_id=correlation_id,
        )


class ItemUpdatedEvent(KafkaMessage):
    """Specific event for item updates"""

    event_type: Literal["item.updated"] = Field(default="item.updated")


class ItemDeletedEvent(KafkaMessage):
    """Specific event for item deletion"""

    event_type: Literal["item.deleted"] = Field(default="item.deleted")
