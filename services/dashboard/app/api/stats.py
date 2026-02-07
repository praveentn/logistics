"""Statistics API endpoints."""

from fastapi import APIRouter
from app.services import service_client
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/stats", tags=["statistics"])


@router.get("/overview")
async def get_overview():
    """Get aggregated overview statistics from all services.

    Returns:
        Aggregated statistics including orders, shipments, inventory, and notifications
    """
    try:
        stats = await service_client.get_overview_stats()
        return stats
    except Exception as e:
        logger.error("overview_stats_failed", error=str(e))
        return {
            "error": str(e),
            "orders": {
                "total_orders": 0,
                "pending_orders": 0,
                "delivered_orders": 0,
                "status": "error"
            },
            "shipments": {
                "total_shipments": 0,
                "active_shipments": 0,
                "delivered_shipments": 0,
                "status": "error"
            },
            "inventory": {
                "total_items": 0,
                "low_stock_items": 0,
                "status": "error"
            },
            "notifications": {
                "notifications_sent_today": 0,
                "status": "error"
            },
            "service_health": {
                "services": [],
                "all_healthy": False
            }
        }


@router.get("/orders")
async def get_order_stats():
    """Get order statistics from order service.

    Returns:
        Order statistics including total, pending, and delivered orders
    """
    try:
        stats = await service_client.get_order_stats()
        return stats
    except Exception as e:
        logger.error("order_stats_endpoint_failed", error=str(e))
        return {
            "total_orders": 0,
            "pending_orders": 0,
            "delivered_orders": 0,
            "status": "error",
            "error": str(e)
        }


@router.get("/shipments")
async def get_shipment_stats():
    """Get shipment statistics from tracking service.

    Returns:
        Shipment statistics including total, active, and delivered shipments
    """
    try:
        stats = await service_client.get_shipment_stats()
        return stats
    except Exception as e:
        logger.error("shipment_stats_endpoint_failed", error=str(e))
        return {
            "total_shipments": 0,
            "active_shipments": 0,
            "delivered_shipments": 0,
            "status": "error",
            "error": str(e)
        }


@router.get("/inventory")
async def get_inventory_stats():
    """Get inventory statistics from inventory service.

    Returns:
        Inventory statistics including total items and low stock alerts
    """
    try:
        stats = await service_client.get_inventory_stats()
        return stats
    except Exception as e:
        logger.error("inventory_stats_endpoint_failed", error=str(e))
        return {
            "total_items": 0,
            "low_stock_items": 0,
            "status": "error",
            "error": str(e)
        }


@router.get("/notifications")
async def get_notification_stats():
    """Get notification statistics from notification service.

    Returns:
        Notification statistics including notifications sent today
    """
    try:
        stats = await service_client.get_notification_stats()
        return stats
    except Exception as e:
        logger.error("notification_stats_endpoint_failed", error=str(e))
        return {
            "notifications_sent_today": 0,
            "status": "error",
            "error": str(e)
        }


@router.get("/health")
async def get_service_health():
    """Get health status of all backend services.

    Returns:
        Health status of all services
    """
    try:
        health = await service_client.get_all_service_health()
        return health
    except Exception as e:
        logger.error("service_health_check_failed", error=str(e))
        return {
            "services": [],
            "all_healthy": False,
            "error": str(e)
        }
