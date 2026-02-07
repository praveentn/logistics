"""Message publisher for order events."""

import os
import json
from datetime import datetime
from typing import Optional
import aio_pika
from aio_pika import Message, ExchangeType, DeliveryMode
import structlog

logger = structlog.get_logger()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin_password_123@rabbitmq:5672/")
EXCHANGE_NAME = "logistics.events"


class OrderEventPublisher:
    """Publisher for order-related events."""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None

    async def connect(self):
        """Connect to RabbitMQ and declare exchange."""
        try:
            self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                EXCHANGE_NAME,
                ExchangeType.TOPIC,
                durable=True
            )
            logger.info("rabbitmq_connected", exchange=EXCHANGE_NAME)
        except Exception as e:
            logger.error("rabbitmq_connection_failed", error=str(e))
            raise

    async def publish_order_created(self, order_data: dict):
        """Publish order.created event.

        Args:
            order_data: Order information
        """
        await self._publish("order.created", order_data)

    async def publish_order_status_changed(self, order_data: dict, old_status: str, new_status: str):
        """Publish order.status_changed event.

        Args:
            order_data: Order information
            old_status: Previous status
            new_status: New status
        """
        event_data = {
            **order_data,
            "old_status": old_status,
            "new_status": new_status
        }
        await self._publish("order.status_changed", event_data)

    async def _publish(self, routing_key: str, data: dict):
        """Publish event to RabbitMQ.

        Args:
            routing_key: Event routing key
            data: Event payload
        """
        if not self.exchange:
            logger.warning("publisher_not_connected", routing_key=routing_key)
            return

        try:
            message_body = {
                **data,
                "_timestamp": datetime.utcnow().isoformat(),
                "_routing_key": routing_key
            }

            body = json.dumps(message_body).encode()
            message = Message(
                body,
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json"
            )

            await self.exchange.publish(message, routing_key=routing_key)
            logger.info("event_published", routing_key=routing_key)
        except Exception as e:
            logger.error("event_publish_failed", routing_key=routing_key, error=str(e))

    async def close(self):
        """Close RabbitMQ connection."""
        if self.connection:
            await self.connection.close()
            logger.info("rabbitmq_connection_closed")

    def get_status(self) -> str:
        """Get connection status.

        Returns:
            Status string
        """
        return "healthy" if self.connection and not self.connection.is_closed else "unhealthy"


# Global publisher instance
event_publisher: Optional[OrderEventPublisher] = None


async def get_event_publisher() -> OrderEventPublisher:
    """Get the global event publisher instance.

    Returns:
        OrderEventPublisher instance
    """
    global event_publisher
    if event_publisher is None:
        event_publisher = OrderEventPublisher()
        await event_publisher.connect()
    return event_publisher
