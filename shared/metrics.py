"""Prometheus metrics utilities for all services.

This module provides shared Prometheus metrics definitions that can be used
across all microservices for consistent monitoring and observability.
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Optional


class ServiceMetrics:
    """Centralized metrics for microservices."""

    def __init__(self, service_name: str, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics for a service.

        Args:
            service_name: Name of the service (e.g., 'order-service')
            registry: Optional custom registry (default: global registry)
        """
        self.service_name = service_name
        self.registry = registry

        # HTTP request metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=registry
        )

        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint'],
            registry=registry
        )

        # Service health
        self.service_up = Gauge(
            'service_up',
            'Service health status (1=up, 0=down)',
            registry=registry
        )

        # Database connection pool
        self.database_connections_active = Gauge(
            'database_connections_active',
            'Active database connections',
            registry=registry
        )

        self.database_connections_idle = Gauge(
            'database_connections_idle',
            'Idle database connections',
            registry=registry
        )

        # Message queue metrics
        self.messages_published_total = Counter(
            'messages_published_total',
            'Total messages published to RabbitMQ',
            ['exchange', 'routing_key'],
            registry=registry
        )

        self.messages_consumed_total = Counter(
            'messages_consumed_total',
            'Total messages consumed from RabbitMQ',
            ['queue'],
            registry=registry
        )

        self.message_processing_duration_seconds = Histogram(
            'message_processing_duration_seconds',
            'Message processing duration',
            ['queue'],
            registry=registry
        )

        # Initialize service as up
        self.service_up.set(1)


# Business-specific metrics (Order Service)
class OrderMetrics(ServiceMetrics):
    """Metrics specific to Order Service."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        super().__init__('order-service', registry)

        self.orders_created_total = Counter(
            'orders_created_total',
            'Total orders created',
            registry=registry
        )

        self.orders_by_status = Gauge(
            'orders_by_status',
            'Number of orders by status',
            ['status'],
            registry=registry
        )

        self.order_processing_duration_seconds = Histogram(
            'order_processing_duration_seconds',
            'Order processing duration',
            registry=registry
        )

        self.order_value_total = Counter(
            'order_value_total',
            'Total value of orders (for demo)',
            registry=registry
        )


# Business-specific metrics (Inventory Service)
class InventoryMetrics(ServiceMetrics):
    """Metrics specific to Inventory Service."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        super().__init__('inventory-service', registry)

        self.inventory_items_count = Gauge(
            'inventory_items_count',
            'Total inventory items',
            ['warehouse_code'],
            registry=registry
        )

        self.inventory_items_reserved = Gauge(
            'inventory_items_reserved',
            'Reserved inventory items',
            ['warehouse_code', 'sku'],
            registry=registry
        )

        self.inventory_transactions_total = Counter(
            'inventory_transactions_total',
            'Total inventory transactions',
            ['transaction_type'],
            registry=registry
        )

        self.low_stock_items = Gauge(
            'low_stock_items',
            'Number of items below reorder level',
            ['warehouse_code'],
            registry=registry
        )


# Business-specific metrics (Tracking Service)
class TrackingMetrics(ServiceMetrics):
    """Metrics specific to Tracking Service."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        super().__init__('tracking-service', registry)

        self.shipments_created_total = Counter(
            'shipments_created_total',
            'Total shipments created',
            registry=registry
        )

        self.shipments_by_status = Gauge(
            'shipments_by_status',
            'Number of shipments by status',
            ['status'],
            registry=registry
        )

        self.tracking_events_total = Counter(
            'tracking_events_total',
            'Total tracking events created',
            ['event_type'],
            registry=registry
        )

        self.shipments_in_transit = Gauge(
            'shipments_in_transit',
            'Number of shipments currently in transit',
            registry=registry
        )


# Business-specific metrics (Notification Service)
class NotificationMetrics(ServiceMetrics):
    """Metrics specific to Notification Service."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        super().__init__('notification-service', registry)

        self.notifications_sent_total = Counter(
            'notifications_sent_total',
            'Total notifications sent',
            ['notification_type', 'channel', 'status'],
            registry=registry
        )

        self.notification_queue_size = Gauge(
            'notification_queue_size',
            'Number of pending notifications',
            registry=registry
        )

        self.notification_send_duration_seconds = Histogram(
            'notification_send_duration_seconds',
            'Notification send duration',
            ['notification_type'],
            registry=registry
        )
