# tests/unit/test_kafka_adapter.py
from unittest.mock import Mock, patch

import pytest

from src.adapters.kafka_adapter import KafkaAdapter
from src.models.payload_models import (CreateItemRequest, ItemCreatedEvent,
                                       KafkaMessage)


class TestKafkaAdapter:

    @pytest.fixture
    def mock_kafka_config(self):
        """Mock Kafka configuration"""
        with patch("src.adapters.kafka_adapter.get_secret") as mock_secret, patch(
            "src.adapters.kafka_adapter.get_env_variable"
        ) as mock_env:

            mock_env.return_value = "test"
            mock_secret.return_value = "localhost:9092,localhost:9093"

            yield mock_secret, mock_env

    @pytest.fixture
    def kafka_adapter_instance(self, mock_kafka_config):
        """Create a fresh KafkaAdapter instance for testing"""
        adapter = KafkaAdapter()
        return adapter

    def test_initialize_kafka_config_success(self, mock_kafka_config):
        """Test successful Kafka configuration initialization"""
        mock_secret, mock_env = mock_kafka_config

        adapter = KafkaAdapter()

        mock_env.assert_called_with("ENVIRONMENT", "dev")
        mock_secret.assert_called_with("/kafka/test/bootstrap-servers")
        assert adapter.bootstrap_servers == "localhost:9092,localhost:9093"

    def test_initialize_kafka_config_failure(self):
        """Test Kafka configuration initialization failure"""
        with patch(
            "src.adapters.kafka_adapter.get_secret", side_effect=Exception("SSM error")
        ):
            with pytest.raises(Exception, match="SSM error"):
                KafkaAdapter()

    @patch("src.adapters.kafka_adapter.KafkaProducer")
    def test_get_producer_success(self, mock_producer_class, kafka_adapter_instance):
        """Test successful producer creation"""
        mock_producer = Mock()
        mock_producer_class.return_value = mock_producer

        producer = kafka_adapter_instance._get_producer()

        assert producer == mock_producer
        mock_producer_class.assert_called_once_with(
            bootstrap_servers=["localhost:9092", "localhost:9093"],
            value_serializer=mock_producer_class.call_args[1]["value_serializer"],
            key_serializer=mock_producer_class.call_args[1]["key_serializer"],
            retries=3,
            retry_backoff_ms=100,
            request_timeout_ms=30000,
        )

    @patch("src.adapters.kafka_adapter.KafkaConsumer")
    def test_get_consumer_success(self, mock_consumer_class, kafka_adapter_instance):
        """Test successful consumer creation"""
        mock_consumer = Mock()
        mock_consumer_class.return_value = mock_consumer

        consumer = kafka_adapter_instance._get_consumer("test-topic", "test-group")

        assert consumer == mock_consumer
        mock_consumer_class.assert_called_once()

    def test_send_message_success(self, kafka_adapter_instance):
        """Test successful message sending"""
        # Mock producer
        mock_producer = Mock()
        mock_future = Mock()
        mock_record_metadata = Mock()
        mock_record_metadata.topic = "test-topic"
        mock_record_metadata.partition = 0
        mock_record_metadata.offset = 123

        mock_future.get.return_value = mock_record_metadata
        mock_producer.send.return_value = mock_future

        with patch.object(
            kafka_adapter_instance, "_get_producer", return_value=mock_producer
        ):
            # Create test message
            message_data = {
                "event_type": "test.event",
                "source_service": "test-service",
                "entity_id": "test-123",
                "payload": {"test": "data"},
            }

            result = kafka_adapter_instance.send_message(
                "test-topic", message_data, "test-key"
            )

            # Verify result
            assert result["topic"] == "test-topic"
            assert result["partition"] == 0
            assert result["offset"] == 123

            # Verify producer was called correctly
            mock_producer.send.assert_called_once()
            call_args = mock_producer.send.call_args
            assert call_args[1]["topic"] == "test-topic"
            assert call_args[1]["key"] == "test-key"

    def test_send_message_validation_error(self, kafka_adapter_instance):
        """Test message sending with validation error"""
        invalid_message = {"invalid": "message"}

        with pytest.raises(ValueError, match="Invalid Kafka message format"):
            kafka_adapter_instance.send_message("test-topic", invalid_message)

    def test_consume_messages_success(self, kafka_adapter_instance):
        """Test successful message consumption"""
        # Mock consumer and messages
        mock_consumer = Mock()
        mock_message1 = Mock()
        mock_message1.topic = "test-topic"
        mock_message1.partition = 0
        mock_message1.offset = 100
        mock_message1.key = "key1"
        mock_message1.value = {"event": "data1"}
        mock_message1.timestamp = 1640995200000

        mock_message2 = Mock()
        mock_message2.topic = "test-topic"
        mock_message2.partition = 1
        mock_message2.offset = 101
        mock_message2.key = "key2"
        mock_message2.value = {"event": "data2"}
        mock_message2.timestamp = 1640995201000

        mock_consumer.__iter__ = Mock(return_value=iter([mock_message1, mock_message2]))

        with patch.object(
            kafka_adapter_instance, "_get_consumer", return_value=mock_consumer
        ):
            messages = kafka_adapter_instance.consume_messages(
                "test-topic", "test-group", 2
            )

            assert len(messages) == 2
            assert messages[0]["topic"] == "test-topic"
            assert messages[0]["offset"] == 100
            assert messages[0]["value"] == {"event": "data1"}
            assert messages[1]["offset"] == 101

            mock_consumer.close.assert_called_once()

    def test_consume_messages_max_limit(self, kafka_adapter_instance):
        """Test message consumption respects max_messages limit"""
        mock_consumer = Mock()
        # Create more messages than the limit
        mock_messages = []
        for i in range(20):
            msg = Mock()
            msg.topic = "test-topic"
            msg.partition = 0
            msg.offset = i
            msg.key = f"key{i}"
            msg.value = {"event": f"data{i}"}
            msg.timestamp = 1640995200000 + i
            mock_messages.append(msg)

        mock_consumer.__iter__ = Mock(return_value=iter(mock_messages))

        with patch.object(
            kafka_adapter_instance, "_get_consumer", return_value=mock_consumer
        ):
            messages = kafka_adapter_instance.consume_messages(
                "test-topic", "test-group", 5
            )

            # Should only return 5 messages despite having 20 available
            assert len(messages) == 5
            mock_consumer.close.assert_called_once()

    def test_close(self, kafka_adapter_instance):
        """Test closing Kafka connections"""
        mock_producer = Mock()
        mock_consumer = Mock()

        kafka_adapter_instance.producer = mock_producer
        kafka_adapter_instance.consumer = mock_consumer

        kafka_adapter_instance.close()

        mock_producer.close.assert_called_once()
        mock_consumer.close.assert_called_once()
        assert kafka_adapter_instance.producer is None
        assert kafka_adapter_instance.consumer is None


class TestKafkaMessageModels:

    def test_kafka_message_creation(self):
        """Test KafkaMessage model creation"""
        message_data = {
            "event_type": "item.created",
            "source_service": "test-service",
            "entity_id": "test-123",
            "payload": {"id": "test-123", "name": "Test Item"},
        }

        message = KafkaMessage(**message_data)

        assert message.event_type == "item.created"
        assert message.source_service == "test-service"
        assert message.entity_id == "test-123"
        assert message.version == "1.0"  # default value
        assert message.payload == {"id": "test-123", "name": "Test Item"}

    def test_item_created_event_from_request(self):
        """Test ItemCreatedEvent creation from CreateItemRequest"""
        create_request = CreateItemRequest(
            id="test-123", name="Test Item", description="Test Description"
        )

        event = ItemCreatedEvent.from_create_request(
            create_request, "test-service", "correlation-123"
        )

        assert event.event_type == "item.created"
        assert event.source_service == "test-service"
        assert event.entity_id == "test-123"
        assert event.correlation_id == "correlation-123"
        assert event.payload == create_request.dict()


class TestKafkaAdapterIntegration:
    """Integration tests that test the full flow"""

    @patch("src.adapters.kafka_adapter.KafkaProducer")
    @patch("src.adapters.kafka_adapter.get_secret")
    @patch("src.adapters.kafka_adapter.get_env_variable")
    def test_full_send_flow(self, mock_env, mock_secret, mock_producer_class):
        """Test the complete send message flow"""
        # Setup mocks
        mock_env.return_value = "test"
        mock_secret.return_value = "localhost:9092"

        mock_producer = Mock()
        mock_future = Mock()
        mock_metadata = Mock()
        mock_metadata.topic = "test-topic"
        mock_metadata.partition = 0
        mock_metadata.offset = 100

        mock_future.get.return_value = mock_metadata
        mock_producer.send.return_value = mock_future
        mock_producer_class.return_value = mock_producer

        # Create adapter and send message
        adapter = KafkaAdapter()

        create_request = CreateItemRequest(
            id="test-123", name="Test Item", description="Test Description"
        )

        event = ItemCreatedEvent.from_create_request(
            create_request, "test-service", "correlation-123"
        )

        result = adapter.send_message("test-topic", event.dict(), "test-123")

        # Verify the result
        assert result["topic"] == "test-topic"
        assert result["partition"] == 0
        assert result["offset"] == 100

        # Verify producer was called
        mock_producer.send.assert_called_once()


# Test convenience functions
class TestConvenienceFunctions:

    @patch("src.adapters.kafka_adapter.get_kafka_adapter")
    def test_send_message_function(self, mock_get_adapter):
        """Test the convenience send_message function"""
        from src.adapters.kafka_adapter import send_message

        mock_adapter = Mock()
        mock_adapter.send_message.return_value = {"status": "success"}
        mock_get_adapter.return_value = mock_adapter

        result = send_message("test-topic", {"test": "data"}, "test-key")

        mock_adapter.send_message.assert_called_once_with(
            "test-topic", {"test": "data"}, "test-key"
        )
        assert result == {"status": "success"}

    @patch("src.adapters.kafka_adapter.get_kafka_adapter")
    def test_consume_messages_function(self, mock_get_adapter):
        """Test the convenience consume_messages function"""
        from src.adapters.kafka_adapter import consume_messages

        mock_adapter = Mock()
        mock_adapter.consume_messages.return_value = [{"message": "data"}]
        mock_get_adapter.return_value = mock_adapter

        result = consume_messages("test-topic", "test-group", 5)

        mock_adapter.consume_messages.assert_called_once_with(
            "test-topic", "test-group", 5
        )
        assert result == [{"message": "data"}]
