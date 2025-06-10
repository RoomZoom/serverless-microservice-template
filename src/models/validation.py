# src/models/validation.py
from pydantic import ValidationError


def validate_model(model_cls, data):
    try:
        return model_cls(**data), None
    except ValidationError as e:
        return None, e.json()
