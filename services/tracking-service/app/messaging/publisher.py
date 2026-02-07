"""Message publisher for tracking events."""

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


class TrackingEventPublisher:
    """Publisher for tracking-related events."""

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

    async def publish_shipment_created(self, shipment_data: dict):
        """Publish shipment.created event.

        Args:
            shipment_data: Shipment information
        """
        await self._publish("shipment.created", shipment_data)

    async def publish_tracking_event(self, event_data: dict):
        """Publish tracking.event_added event.

        Args:
            event_data: Tracking event information
        """
        await self._publish("tracking.event_added", event_data)

    async def publish_shipment_status_changed(self, shipment_data: dict, old_status: str, new_status: str):
        """Publish shipment.status_changed event.

        Args:
            shipment_data: Shipment information
            old_status: Previous status
            new_status: New status
        """
        event_data = {
            **shipment_data,
            "old_status": old_status,
            "new_status": new_status
        }
        await self._publish("shipment.status_changed", event_data)

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
event_publisher: Optional[TrackingEventPublisher] = None


async def get_event_publisher() -> TrackingEventPublisher:
    """Get the global event publisher instance.

    Returns:
        TrackingEventPublisher instance
    """
    global event_publisher
    if event_publisher is None:
        event_publisher = TrackingEventPublisher()
        await event_publisher.connect()
    return event_publisher
