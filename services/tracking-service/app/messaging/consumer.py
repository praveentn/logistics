"""Message consumer for order events."""

import os
import json
import asyncio
from typing import Optional
import aio_pika
from aio_pika import ExchangeType
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas import ShipmentCreate
from app.services import tracking_service
from app.messaging.publisher import get_event_publisher
import structlog

logger = structlog.get_logger()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin_password_123@rabbitmq:5672/")
EXCHANGE_NAME = "logistics.events"
QUEUE_NAME = "tracking.order_events"


class OrderEventConsumer:
    """Consumer for order-related events."""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.running = False

    async def connect(self):
        """Connect to RabbitMQ and set up queue."""
        try:
            self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange
            exchange = await self.channel.declare_exchange(
                EXCHANGE_NAME,
                ExchangeType.TOPIC,
                durable=True
            )

            # Declare queue
            self.queue = await self.channel.declare_queue(
                QUEUE_NAME,
                durable=True
            )

            # Bind queue to exchange with routing key
            await self.queue.bind(exchange, routing_key="order.created")

            logger.info(
                "consumer_connected",
                queue=QUEUE_NAME,
                exchange=EXCHANGE_NAME,
                routing_key="order.created"
            )
        except Exception as e:
            logger.error("consumer_connection_failed", error=str(e))
            raise

    async def process_order_created(self, message_body: dict):
        """Process order.created event.

        Args:
            message_body: Event payload
        """
        try:
            order_number = message_body.get("order_number")
            if not order_number:
                logger.warning("order_created_missing_order_number", data=message_body)
                return

            # Create database session
            db: Session = SessionLocal()
            try:
                # Check if shipment already exists
                existing = tracking_service.get_shipment_by_order_number(db, order_number)
                if existing:
                    logger.info(
                        "shipment_already_exists",
                        order_number=order_number,
                        tracking_number=existing.tracking_number
                    )
                    return

                # Create shipment from order
                shipment_data = ShipmentCreate(
                    order_number=order_number,
                    carrier="Standard Carrier",  # Default carrier
                    current_location=message_body.get("origin_address", "Warehouse")
                )

                shipment = tracking_service.create_shipment(db, shipment_data)

                logger.info(
                    "shipment_auto_created",
                    order_number=order_number,
                    tracking_number=shipment.tracking_number
                )

                # Publish shipment.created event
                publisher = await get_event_publisher()
                await publisher.publish_shipment_created({
                    "tracking_number": shipment.tracking_number,
                    "order_number": shipment.order_number,
                    "carrier": shipment.carrier,
                    "status": shipment.status,
                    "current_location": shipment.current_location
                })

            finally:
                db.close()

        except Exception as e:
            logger.error("order_created_processing_failed", error=str(e), data=message_body)

    async def on_message(self, message: aio_pika.IncomingMessage):
        """Handle incoming message.

        Args:
            message: Incoming message
        """
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                routing_key = body.get("_routing_key", message.routing_key)

                logger.info("message_received", routing_key=routing_key)

                if routing_key == "order.created":
                    await self.process_order_created(body)
                else:
                    logger.warning("unknown_routing_key", routing_key=routing_key)

            except json.JSONDecodeError as e:
                logger.error("message_decode_failed", error=str(e))
            except Exception as e:
                logger.error("message_processing_failed", error=str(e))

    async def start(self):
        """Start consuming messages."""
        if not self.queue:
            await self.connect()

        self.running = True
        logger.info("consumer_started", queue=QUEUE_NAME)

        try:
            await self.queue.consume(self.on_message)
            # Keep the consumer running
            while self.running:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error("consumer_error", error=str(e))
            raise

    async def stop(self):
        """Stop consuming messages."""
        self.running = False
        if self.connection:
            await self.connection.close()
            logger.info("consumer_stopped")


# Global consumer instance
order_consumer: Optional[OrderEventConsumer] = None


async def get_order_consumer() -> OrderEventConsumer:
    """Get the global order event consumer instance.

    Returns:
        OrderEventConsumer instance
    """
    global order_consumer
    if order_consumer is None:
        order_consumer = OrderEventConsumer()
        await order_consumer.connect()
    return order_consumer


async def start_consumer():
    """Start the message consumer."""
    consumer = await get_order_consumer()
    await consumer.start()
