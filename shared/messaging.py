"""RabbitMQ messaging utilities for event-driven communication.

This module provides base classes for publishing and consuming messages
using RabbitMQ, enabling asynchronous inter-service communication.
"""

import json
import asyncio
from typing import Callable, Dict, Any, Optional
from datetime import datetime
import aio_pika
from aio_pika import Message, ExchangeType, DeliveryMode
from aio_pika.abc import AbstractIncomingMessage
import structlog

logger = structlog.get_logger()


class MessagePublisher:
    """Async RabbitMQ message publisher."""

    def __init__(self, rabbitmq_url: str):
        """Initialize publisher.

        Args:
            rabbitmq_url: RabbitMQ connection URL (e.g., 'amqp://guest:guest@localhost/')
        """
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None

    async def connect(self, exchange_name: str = "logistics.events"):
        """Establish connection to RabbitMQ and declare exchange.

        Args:
            exchange_name: Name of the topic exchange
        """
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()

            # Declare topic exchange for event routing
            self.exchange = await self.channel.declare_exchange(
                exchange_name,
                ExchangeType.TOPIC,
                durable=True
            )

            logger.info(
                "rabbitmq_publisher_connected",
                exchange=exchange_name,
                url=self.rabbitmq_url.split('@')[-1]  # Hide credentials
            )
        except Exception as e:
            logger.error(
                "rabbitmq_publisher_connection_failed",
                error=str(e),
                url=self.rabbitmq_url.split('@')[-1]
            )
            raise

    async def publish(
        self,
        routing_key: str,
        message: Dict[str, Any],
        exchange_name: Optional[str] = None
    ):
        """Publish a message to the exchange.

        Args:
            routing_key: Routing key for the message (e.g., 'order.created')
            message: Message payload as dictionary
            exchange_name: Override default exchange (optional)
        """
        if not self.exchange:
            raise RuntimeError("Publisher not connected. Call connect() first.")

        try:
            # Add timestamp and metadata
            enriched_message = {
                **message,
                "_timestamp": datetime.utcnow().isoformat(),
                "_routing_key": routing_key
            }

            # Serialize to JSON
            body = json.dumps(enriched_message).encode()

            # Create message with persistent delivery
            msg = Message(
                body,
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json"
            )

            # Publish to exchange
            await self.exchange.publish(msg, routing_key=routing_key)

            logger.info(
                "message_published",
                routing_key=routing_key,
                message_size=len(body)
            )
        except Exception as e:
            logger.error(
                "message_publish_failed",
                routing_key=routing_key,
                error=str(e)
            )
            raise

    async def close(self):
        """Close RabbitMQ connection."""
        if self.connection:
            await self.connection.close()
            logger.info("rabbitmq_publisher_closed")


class MessageConsumer:
    """Async RabbitMQ message consumer."""

    def __init__(self, rabbitmq_url: str, queue_name: str):
        """Initialize consumer.

        Args:
            rabbitmq_url: RabbitMQ connection URL
            queue_name: Name of the queue to consume from
        """
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.handlers: Dict[str, Callable] = {}

    async def connect(
        self,
        exchange_name: str = "logistics.events",
        routing_keys: list[str] = None
    ):
        """Establish connection and bind queue to exchange.

        Args:
            exchange_name: Name of the exchange to bind to
            routing_keys: List of routing keys to bind (e.g., ['order.*', 'shipment.updated'])
        """
        if routing_keys is None:
            routing_keys = ["#"]  # Subscribe to all messages

        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)  # Process 10 messages at a time

            # Declare exchange
            exchange = await self.channel.declare_exchange(
                exchange_name,
                ExchangeType.TOPIC,
                durable=True
            )

            # Declare queue
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )

            # Bind queue to exchange with routing keys
            for routing_key in routing_keys:
                await self.queue.bind(exchange, routing_key=routing_key)
                logger.info(
                    "queue_bound",
                    queue=self.queue_name,
                    exchange=exchange_name,
                    routing_key=routing_key
                )

            logger.info(
                "rabbitmq_consumer_connected",
                queue=self.queue_name,
                exchange=exchange_name
            )
        except Exception as e:
            logger.error(
                "rabbitmq_consumer_connection_failed",
                queue=self.queue_name,
                error=str(e)
            )
            raise

    def register_handler(self, routing_pattern: str, handler: Callable):
        """Register a handler for a routing pattern.

        Args:
            routing_pattern: Pattern to match (e.g., 'order.created')
            handler: Async function to handle the message
        """
        self.handlers[routing_pattern] = handler
        logger.info(
            "message_handler_registered",
            pattern=routing_pattern,
            queue=self.queue_name
        )

    async def _process_message(self, message: AbstractIncomingMessage):
        """Process incoming message.

        Args:
            message: Incoming message from RabbitMQ
        """
        async with message.process():
            try:
                # Decode and parse message
                body = json.loads(message.body.decode())
                routing_key = body.get("_routing_key", "unknown")

                logger.info(
                    "message_received",
                    queue=self.queue_name,
                    routing_key=routing_key
                )

                # Find matching handler
                handler = None
                for pattern, h in self.handlers.items():
                    if self._matches_pattern(routing_key, pattern):
                        handler = h
                        break

                if handler:
                    await handler(body)
                    logger.info(
                        "message_processed",
                        queue=self.queue_name,
                        routing_key=routing_key
                    )
                else:
                    logger.warning(
                        "no_handler_found",
                        queue=self.queue_name,
                        routing_key=routing_key
                    )
            except Exception as e:
                logger.error(
                    "message_processing_failed",
                    queue=self.queue_name,
                    error=str(e)
                )
                # Message will be requeued due to exception in process() context

    def _matches_pattern(self, routing_key: str, pattern: str) -> bool:
        """Check if routing key matches pattern.

        Args:
            routing_key: Actual routing key (e.g., 'order.created')
            pattern: Pattern to match (e.g., 'order.*' or '#')

        Returns:
            True if matches, False otherwise
        """
        if pattern == "#":
            return True

        key_parts = routing_key.split(".")
        pattern_parts = pattern.split(".")

        if len(key_parts) != len(pattern_parts):
            return False

        for k, p in zip(key_parts, pattern_parts):
            if p != "*" and p != k:
                return False

        return True

    async def start_consuming(self):
        """Start consuming messages from the queue."""
        if not self.queue:
            raise RuntimeError("Consumer not connected. Call connect() first.")

        logger.info("starting_message_consumption", queue=self.queue_name)
        await self.queue.consume(self._process_message)

    async def close(self):
        """Close RabbitMQ connection."""
        if self.connection:
            await self.connection.close()
            logger.info("rabbitmq_consumer_closed", queue=self.queue_name)


async def create_publisher(rabbitmq_url: str, exchange_name: str = "logistics.events") -> MessagePublisher:
    """Factory function to create and connect a message publisher.

    Args:
        rabbitmq_url: RabbitMQ connection URL
        exchange_name: Exchange name (default: 'logistics.events')

    Returns:
        Connected MessagePublisher instance
    """
    publisher = MessagePublisher(rabbitmq_url)
    await publisher.connect(exchange_name)
    return publisher


async def create_consumer(
    rabbitmq_url: str,
    queue_name: str,
    routing_keys: list[str],
    exchange_name: str = "logistics.events"
) -> MessageConsumer:
    """Factory function to create and connect a message consumer.

    Args:
        rabbitmq_url: RabbitMQ connection URL
        queue_name: Queue name
        routing_keys: List of routing key patterns to bind
        exchange_name: Exchange name (default: 'logistics.events')

    Returns:
        Connected MessageConsumer instance
    """
    consumer = MessageConsumer(rabbitmq_url, queue_name)
    await consumer.connect(exchange_name, routing_keys)
    return consumer
