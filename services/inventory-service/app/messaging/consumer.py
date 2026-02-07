"""RabbitMQ consumer for inventory service."""

import os
import asyncio
from typing import Optional
import structlog

# Import the shared messaging utilities
from shared.messaging import MessageConsumer, create_consumer

from app.database import SessionLocal
from app.services import inventory_service

logger = structlog.get_logger()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin_password_123@rabbitmq:5672/")
QUEUE_NAME = "inventory.queue"
EXCHANGE_NAME = "logistics.events"


class InventoryEventConsumer:
    """Consumer for inventory-related events."""

    def __init__(self):
        """Initialize the inventory event consumer."""
        self.consumer: Optional[MessageConsumer] = None

    async def connect(self):
        """Connect to RabbitMQ and set up message handlers."""
        try:
            # Create consumer with routing keys for order events
            self.consumer = await create_consumer(
                rabbitmq_url=RABBITMQ_URL,
                queue_name=QUEUE_NAME,
                routing_keys=["order.created", "order.cancelled"],
                exchange_name=EXCHANGE_NAME
            )

            # Register event handlers
            self.consumer.register_handler("order.created", self.handle_order_created)
            self.consumer.register_handler("order.cancelled", self.handle_order_cancelled)

            logger.info(
                "inventory_consumer_connected",
                queue=QUEUE_NAME,
                routing_keys=["order.created", "order.cancelled"]
            )
        except Exception as e:
            logger.error("inventory_consumer_connection_failed", error=str(e))
            raise

    async def handle_order_created(self, message: dict):
        """Handle order.created event by reserving inventory.

        Args:
            message: Order created event data
        """
        try:
            order_number = message.get("order_number")
            items = message.get("items", [])

            if not order_number or not items:
                logger.warning(
                    "invalid_order_created_event",
                    order_number=order_number,
                    items_count=len(items)
                )
                return

            logger.info(
                "processing_order_created",
                order_number=order_number,
                items_count=len(items)
            )

            # Prepare items for reservation
            items_to_reserve = [
                {"sku": item.get("sku"), "quantity": item.get("quantity")}
                for item in items
                if item.get("sku")
            ]

            if not items_to_reserve:
                logger.info(
                    "no_items_to_reserve",
                    order_number=order_number
                )
                return

            # Reserve inventory
            db = SessionLocal()
            try:
                success = inventory_service.reserve_inventory(
                    db,
                    order_number,
                    items_to_reserve
                )

                if success:
                    logger.info(
                        "inventory_reserved_for_order",
                        order_number=order_number,
                        items_count=len(items_to_reserve)
                    )
                else:
                    logger.warning(
                        "inventory_reservation_failed",
                        order_number=order_number
                    )
            finally:
                db.close()

        except Exception as e:
            logger.error(
                "order_created_handler_error",
                order_number=message.get("order_number"),
                error=str(e)
            )
            raise

    async def handle_order_cancelled(self, message: dict):
        """Handle order.cancelled or order.status_changed event by releasing inventory.

        Args:
            message: Order cancelled event data
        """
        try:
            order_number = message.get("order_number")

            # Check if this is a cancellation
            new_status = message.get("new_status")
            if new_status and new_status != "cancelled":
                return

            if not order_number:
                logger.warning("invalid_order_cancelled_event")
                return

            logger.info(
                "processing_order_cancelled",
                order_number=order_number
            )

            # Release reserved inventory
            db = SessionLocal()
            try:
                success = inventory_service.release_inventory(db, order_number)

                if success:
                    logger.info(
                        "inventory_released_for_order",
                        order_number=order_number
                    )
                else:
                    logger.warning(
                        "inventory_release_failed",
                        order_number=order_number
                    )
            finally:
                db.close()

        except Exception as e:
            logger.error(
                "order_cancelled_handler_error",
                order_number=message.get("order_number"),
                error=str(e)
            )
            raise

    async def start_consuming(self):
        """Start consuming messages."""
        if not self.consumer:
            raise RuntimeError("Consumer not connected. Call connect() first.")

        logger.info("starting_inventory_event_consumption")
        await self.consumer.start_consuming()

    async def close(self):
        """Close the consumer connection."""
        if self.consumer:
            await self.consumer.close()
            logger.info("inventory_consumer_closed")

    def get_status(self) -> str:
        """Get consumer connection status.

        Returns:
            Status string ('healthy' or 'unhealthy')
        """
        if self.consumer and self.consumer.connection and not self.consumer.connection.is_closed:
            return "healthy"
        return "unhealthy"


# Global consumer instance
inventory_consumer: Optional[InventoryEventConsumer] = None


async def get_inventory_consumer() -> InventoryEventConsumer:
    """Get the global inventory consumer instance.

    Returns:
        InventoryEventConsumer instance
    """
    global inventory_consumer
    if inventory_consumer is None:
        inventory_consumer = InventoryEventConsumer()
        await inventory_consumer.connect()
    return inventory_consumer


async def start_consumer():
    """Start the inventory consumer in the background."""
    consumer = await get_inventory_consumer()
    await consumer.start_consuming()
