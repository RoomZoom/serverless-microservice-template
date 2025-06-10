# src/models/payload_models.py
from pydantic import BaseModel


class CreateItemRequest(BaseModel):
    id: str
    name: str
    description: str


class QueueMessage(BaseModel):
    id: str
    action: str
