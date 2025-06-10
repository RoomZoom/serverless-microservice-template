# tests/unit/test_dynamodb_adapter.py
from src.adapters import dynamodb_adapter


def test_get_item_returns_none_for_missing():
    item = dynamodb_adapter.get_item("fake-table", {"id": "nonexistent"})
    assert item is None
