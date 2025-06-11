# src/adapters/kafka_adapter.py
import json
import logging
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from models.payload_models import KafkaMessage
from models.validation import validate_model
from utils.config import get_secret, get_env_variable

logger = logging.getLogger(__name__)


class KafkaAdapter:
    def __init__(self):
        self.bootstrap_servers = None
        self.producer = None
        self.consumer = None
        self._initialize_kafka_config()

    def _initialize_kafka_config(self):
        """Initialize Kafka configuration from environment and SSM"""
        env = get_env_variable("ENVIRONMENT", "dev")

        try:
            # Get Kafka bootstrap servers from SSM
            ssm_key = f"/kafka/{env}/bootstrap-servers"
            self.bootstrap_servers = get_secret(ssm_key)
            logger.info(f"Initialized Kafka config for environment: {env}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka config: {str(e)}")
            raise

    def _get_producer(self):
        """Get or create Kafka producer"""
        if not self.producer:
            if not self.bootstrap_servers:
                raise ValueError("Bootstrap servers not configured")
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers.split(","),
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    key_serializer=lambda k: k.encode("utf-8") if k else None,
                    retries=3,
                    retry_backoff_ms=100,
                    request_timeout_ms=30000,
                )
                logger.info("Kafka producer initialized successfully")
            except Exception as e:
                logger.error(f"Failed to create Kafka producer: {str(e)}")
                raise
        return self.producer

    def _get_consumer(self, topic, group_id=None, auto_offset_reset="latest"):
        """Get or create Kafka consumer"""
        if not self.bootstrap_servers:
            raise ValueError("Bootstrap servers not configured")
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers.split(","),
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                consumer_timeout_ms=5000,  # 5 second timeout
            )
            logger.info(f"Kafka consumer initialized for topic: {topic}")
            return consumer
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {str(e)}")
            raise

    def send_message(self, topic, message_data, key=None):
        """Send message to Kafka topic with validation"""
        try:
            # Validate message format
            validated, errors = validate_model(KafkaMessage, message_data)
            if errors:
                raise ValueError(f"Invalid Kafka message format: {errors}")
            if validated is None:
                raise ValueError("Validation failed but no errors returned")

            producer = self._get_producer()

            # Send message
            future = producer.send(topic=topic, value=validated.dict(), key=key)

            # Wait for confirmation (optional - can be async)
            record_metadata = future.get(timeout=10)

            logger.info(
                f"Message sent to topic {topic}, partition {record_metadata.partition}, offset {record_metadata.offset}"
            )
            return {
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset,
            }

        except KafkaError as e:
            logger.error(f"Kafka error while sending message: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to send Kafka message: {str(e)}")
            raise

    def consume_messages(self, topic, group_id=None, max_messages=10):
        """Consume messages from Kafka topic"""
        messages = []
        try:
            consumer = self._get_consumer(topic, group_id)

            message_count = 0
            for message in consumer:
                if message_count >= max_messages:
                    break

                messages.append(
                    {
                        "topic": message.topic,
                        "partition": message.partition,
                        "offset": message.offset,
                        "key": message.key,
                        "value": message.value,
                        "timestamp": message.timestamp,
                    }
                )
                message_count += 1

            consumer.close()
            logger.info(f"Consumed {len(messages)} messages from topic: {topic}")
            return messages

        except Exception as e:
            logger.error(f"Failed to consume Kafka messages: {str(e)}")
            raise

    def close(self):
        """Close Kafka connections"""
        try:
            if self.producer:
                self.producer.close()
                self.producer = None
            if self.consumer:
                self.consumer.close()
                self.consumer = None
            logger.info("Kafka connections closed")
        except Exception as e:
            logger.error(f"Error closing Kafka connections: {str(e)}")


# Singleton instance for reuse
kafka_adapter = KafkaAdapter()


# Convenience functions for backward compatibility
def send_message(topic, message_data, key=None):
    return kafka_adapter.send_message(topic, message_data, key)


def consume_messages(topic, group_id=None, max_messages=10):
    return kafka_adapter.consume_messages(topic, group_id, max_messages)
