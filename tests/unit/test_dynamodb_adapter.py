# tests/unit/test_dynamodb_adapter.py
from unittest.mock import Mock, patch

from src.adapters import dynamodb_adapter


@patch("src.adapters.dynamodb_adapter._get_dynamodb")
def test_get_item_returns_none_for_missing(mock_get_dynamodb):
    """Test that get_item returns None for missing items"""
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_table.get_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    mock_dynamodb.Table.return_value = mock_table
    mock_get_dynamodb.return_value = mock_dynamodb

    item = dynamodb_adapter.get_item("fake-table", {"id": "nonexistent"})

    mock_get_dynamodb.assert_called_once()
    mock_dynamodb.Table.assert_called_once_with("fake-table")
    mock_table.get_item.assert_called_once_with(Key={"id": "nonexistent"})

    assert item is None
