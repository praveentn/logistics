"""Message consumer for notification events."""

import os
import json
import asyncio
from typing import Callable
import aio_pika
from aio_pika import IncomingMessage, ExchangeType
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services import notification_service
import structlog

logger = structlog.get_logger()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin_password_123@rabbitmq:5672/")
EXCHANGE_NAME = "logistics.events"


class NotificationConsumer:
    """Consumer for notification events."""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        self.running = False

    async def connect(self):
        """Connect to RabbitMQ and set up queue."""
        try:
            self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                EXCHANGE_NAME,
                ExchangeType.TOPIC,
                durable=True
            )

            # Declare queue
            self.queue = await self.channel.declare_queue(
                "notification_service_queue",
                durable=True
            )

            # Bind queue to events
            event_patterns = [
                "order.created",
                "order.status_changed",
                "shipment.created",
                "shipment.updated",
                "inventory.low_stock"
            ]

            for pattern in event_patterns:
                await self.queue.bind(self.exchange, routing_key=pattern)
                logger.info("queue_bound", routing_key=pattern)

            logger.info("rabbitmq_consumer_connected", queue="notification_service_queue")
        except Exception as e:
            logger.error("rabbitmq_consumer_connection_failed", error=str(e))
            raise

    async def start_consuming(self):
        """Start consuming messages."""
        if not self.queue:
            raise RuntimeError("Consumer not connected")

        self.running = True
        await self.queue.consume(self._process_message)
        logger.info("consumer_started")

    async def _process_message(self, message: IncomingMessage):
        """Process incoming message.

        Args:
            message: Incoming message from RabbitMQ
        """
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode())
                routing_key = body.get("_routing_key", message.routing_key)

                logger.info(
                    "message_received",
                    routing_key=routing_key,
                    message_id=message.message_id
                )

                # Get database session
                db = SessionLocal()
                try:
                    # Handle different event types
                    if routing_key == "order.created":
                        await self._handle_order_created(db, body)
                    elif routing_key == "order.status_changed":
                        await self._handle_order_status_changed(db, body)
                    elif routing_key == "shipment.created":
                        await self._handle_shipment_created(db, body)
                    elif routing_key == "shipment.updated":
                        await self._handle_shipment_updated(db, body)
                    elif routing_key == "inventory.low_stock":
                        await self._handle_inventory_low_stock(db, body)
                    else:
                        logger.warning("unknown_event_type", routing_key=routing_key)

                    logger.info("message_processed", routing_key=routing_key)
                finally:
                    db.close()

            except json.JSONDecodeError as e:
                logger.error("message_decode_failed", error=str(e))
            except Exception as e:
                logger.error("message_processing_failed", error=str(e))

    async def _handle_order_created(self, db: Session, event_data: dict):
        """Handle order.created event - send order confirmation.

        Args:
            db: Database session
            event_data: Event payload
        """
        logger.info("handling_order_created", order_number=event_data.get("order_number"))
        notification_service.create_from_event(db, "order.created", event_data)

    async def _handle_order_status_changed(self, db: Session, event_data: dict):
        """Handle order.status_changed event - send status update.

        Args:
            db: Database session
            event_data: Event payload
        """
        logger.info(
            "handling_order_status_changed",
            order_number=event_data.get("order_number"),
            new_status=event_data.get("new_status")
        )
        notification_service.create_from_event(db, "order.status_changed", event_data)

    async def _handle_shipment_created(self, db: Session, event_data: dict):
        """Handle shipment.created event - send shipment notification.

        Args:
            db: Database session
            event_data: Event payload
        """
        logger.info("handling_shipment_created", tracking_number=event_data.get("tracking_number"))
        notification_service.create_from_event(db, "shipment.created", event_data)

    async def _handle_shipment_updated(self, db: Session, event_data: dict):
        """Handle shipment.updated event - send tracking update.

        Args:
            db: Database session
            event_data: Event payload
        """
        logger.info("handling_shipment_updated", tracking_number=event_data.get("tracking_number"))
        notification_service.create_from_event(db, "shipment.updated", event_data)

    async def _handle_inventory_low_stock(self, db: Session, event_data: dict):
        """Handle inventory.low_stock event - send low stock alert.

        Args:
            db: Database session
            event_data: Event payload
        """
        logger.info("handling_inventory_low_stock", sku=event_data.get("sku"))
        notification_service.create_from_event(db, "inventory.low_stock", event_data)

    async def stop(self):
        """Stop the consumer."""
        self.running = False
        if self.connection:
            await self.connection.close()
            logger.info("consumer_stopped")

    def get_status(self) -> str:
        """Get consumer status.

        Returns:
            Status string
        """
        return "healthy" if self.connection and not self.connection.is_closed else "unhealthy"


# Global consumer instance
consumer: NotificationConsumer = None


async def get_consumer() -> NotificationConsumer:
    """Get the global consumer instance.

    Returns:
        NotificationConsumer instance
    """
    global consumer
    if consumer is None:
        consumer = NotificationConsumer()
        await consumer.connect()
    return consumer


async def start_consumer():
    """Start the notification consumer."""
    consumer = await get_consumer()
    await consumer.start_consuming()

    # Keep running
    while consumer.running:
        await asyncio.sleep(1)
