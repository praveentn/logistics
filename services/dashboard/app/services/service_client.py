"""Service client for aggregating data from backend services."""

import os
from typing import Dict, Any, Optional
import httpx
import structlog

logger = structlog.get_logger()

# Service URLs from environment variables with defaults
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8001")
TRACKING_SERVICE_URL = os.getenv("TRACKING_SERVICE_URL", "http://localhost:8002")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8004")

# Timeout for service calls
TIMEOUT = 5.0


async def get_service_health(service_name: str, url: str) -> Dict[str, Any]:
    """Get health status of a service.

    Args:
        service_name: Name of the service
        url: Service URL

    Returns:
        Health status information
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{url}/health")
            if response.status_code == 200:
                return {
                    "service": service_name,
                    "status": "healthy",
                    "data": response.json()
                }
            else:
                return {
                    "service": service_name,
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        logger.error(f"{service_name}_health_check_failed", error=str(e))
        return {
            "service": service_name,
            "status": "unreachable",
            "error": str(e)
        }


async def get_order_stats() -> Dict[str, Any]:
    """Get order statistics from order service.

    Returns:
        Order statistics or error information
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Get orders with pagination to count them
            response = await client.get(
                f"{ORDER_SERVICE_URL}/api/v1/orders",
                params={"page": 1, "page_size": 100}
            )

            if response.status_code == 200:
                data = response.json()
                total_orders = data.get("total", 0)

                # Get orders by status
                pending_response = await client.get(
                    f"{ORDER_SERVICE_URL}/api/v1/orders",
                    params={"page": 1, "page_size": 100, "status": "pending"}
                )
                pending_count = 0
                if pending_response.status_code == 200:
                    pending_count = pending_response.json().get("total", 0)

                delivered_response = await client.get(
                    f"{ORDER_SERVICE_URL}/api/v1/orders",
                    params={"page": 1, "page_size": 100, "status": "delivered"}
                )
                delivered_count = 0
                if delivered_response.status_code == 200:
                    delivered_count = delivered_response.json().get("total", 0)

                return {
                    "total_orders": total_orders,
                    "pending_orders": pending_count,
                    "delivered_orders": delivered_count,
                    "status": "success"
                }
            else:
                logger.warning("order_service_error", status=response.status_code)
                return {
                    "total_orders": 0,
                    "pending_orders": 0,
                    "delivered_orders": 0,
                    "status": "error",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        logger.error("order_stats_failed", error=str(e))
        return {
            "total_orders": 0,
            "pending_orders": 0,
            "delivered_orders": 0,
            "status": "error",
            "error": str(e)
        }


async def get_shipment_stats() -> Dict[str, Any]:
    """Get shipment statistics from tracking service.

    Returns:
        Shipment statistics or error information
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Get shipments with pagination
            response = await client.get(
                f"{TRACKING_SERVICE_URL}/api/v1/shipments",
                params={"page": 1, "page_size": 100}
            )

            if response.status_code == 200:
                data = response.json()
                total_shipments = data.get("total", 0)

                # Get shipments by status
                in_transit_response = await client.get(
                    f"{TRACKING_SERVICE_URL}/api/v1/shipments",
                    params={"page": 1, "page_size": 100, "status": "in_transit"}
                )
                in_transit_count = 0
                if in_transit_response.status_code == 200:
                    in_transit_count = in_transit_response.json().get("total", 0)

                delivered_response = await client.get(
                    f"{TRACKING_SERVICE_URL}/api/v1/shipments",
                    params={"page": 1, "page_size": 100, "status": "delivered"}
                )
                delivered_count = 0
                if delivered_response.status_code == 200:
                    delivered_count = delivered_response.json().get("total", 0)

                return {
                    "total_shipments": total_shipments,
                    "active_shipments": in_transit_count,
                    "delivered_shipments": delivered_count,
                    "status": "success"
                }
            else:
                logger.warning("tracking_service_error", status=response.status_code)
                return {
                    "total_shipments": 0,
                    "active_shipments": 0,
                    "delivered_shipments": 0,
                    "status": "error",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        logger.error("shipment_stats_failed", error=str(e))
        return {
            "total_shipments": 0,
            "active_shipments": 0,
            "delivered_shipments": 0,
            "status": "error",
            "error": str(e)
        }


async def get_inventory_stats() -> Dict[str, Any]:
    """Get inventory statistics from inventory service.

    Returns:
        Inventory statistics or error information
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Get low stock items
            low_stock_response = await client.get(
                f"{INVENTORY_SERVICE_URL}/api/v1/inventory/low-stock"
            )

            low_stock_count = 0
            if low_stock_response.status_code == 200:
                low_stock_items = low_stock_response.json()
                low_stock_count = len(low_stock_items) if isinstance(low_stock_items, list) else 0

            # Get warehouses to estimate total inventory items
            warehouses_response = await client.get(
                f"{INVENTORY_SERVICE_URL}/api/v1/warehouses",
                params={"page": 1, "page_size": 100}
            )

            total_items = 0
            if warehouses_response.status_code == 200:
                warehouses = warehouses_response.json()
                if isinstance(warehouses, list):
                    # Get inventory for each warehouse
                    for warehouse in warehouses[:5]:  # Limit to first 5 warehouses
                        warehouse_id = warehouse.get("id")
                        if warehouse_id:
                            inv_response = await client.get(
                                f"{INVENTORY_SERVICE_URL}/api/v1/warehouses/{warehouse_id}/inventory",
                                params={"page": 1, "page_size": 100}
                            )
                            if inv_response.status_code == 200:
                                items = inv_response.json()
                                if isinstance(items, list):
                                    total_items += len(items)

            return {
                "total_items": total_items,
                "low_stock_items": low_stock_count,
                "status": "success"
            }
    except Exception as e:
        logger.error("inventory_stats_failed", error=str(e))
        return {
            "total_items": 0,
            "low_stock_items": 0,
            "status": "error",
            "error": str(e)
        }


async def get_notification_stats() -> Dict[str, Any]:
    """Get notification statistics from notification service.

    Returns:
        Notification statistics or error information
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Try to get health status as notification service may not have stats endpoint
            response = await client.get(f"{NOTIFICATION_SERVICE_URL}/health")

            if response.status_code == 200:
                # Since notification service doesn't have a stats endpoint,
                # we return a placeholder
                return {
                    "notifications_sent_today": 0,
                    "status": "success",
                    "note": "Notification service doesn't expose detailed stats"
                }
            else:
                return {
                    "notifications_sent_today": 0,
                    "status": "error",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        logger.error("notification_stats_failed", error=str(e))
        return {
            "notifications_sent_today": 0,
            "status": "error",
            "error": str(e)
        }


async def get_all_service_health() -> Dict[str, Any]:
    """Get health status of all services.

    Returns:
        Health status of all services
    """
    services = [
        ("order-service", ORDER_SERVICE_URL),
        ("tracking-service", TRACKING_SERVICE_URL),
        ("inventory-service", INVENTORY_SERVICE_URL),
        ("notification-service", NOTIFICATION_SERVICE_URL),
    ]

    health_checks = []
    for service_name, service_url in services:
        health = await get_service_health(service_name, service_url)
        health_checks.append(health)

    return {
        "services": health_checks,
        "all_healthy": all(s["status"] == "healthy" for s in health_checks)
    }


async def get_overview_stats() -> Dict[str, Any]:
    """Get aggregated overview statistics from all services.

    Returns:
        Aggregated statistics
    """
    # Fetch stats from all services concurrently
    order_stats = await get_order_stats()
    shipment_stats = await get_shipment_stats()
    inventory_stats = await get_inventory_stats()
    notification_stats = await get_notification_stats()
    health_stats = await get_all_service_health()

    return {
        "orders": order_stats,
        "shipments": shipment_stats,
        "inventory": inventory_stats,
        "notifications": notification_stats,
        "service_health": health_stats
    }
