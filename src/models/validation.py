# src/models/validation.py
from pydantic import ValidationError
from typing import Tuple, Optional, Any


def validate_model(model_cls, data) -> Tuple[Optional[Any], Optional[str]]:
    try:
        validated_model = model_cls(**data)
        return validated_model, None
    except ValidationError as e:
        return None, e.json()
