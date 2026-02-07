"""Order API endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    OrderCreate,
    OrderResponse,
    OrderListResponse,
    OrderUpdate
)
from app.services import order_service
from app.messaging.publisher import get_event_publisher
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new order.

    Args:
        order_data: Order creation data
        db: Database session

    Returns:
        Created order
    """
    try:
        # Check inventory availability
        items_check = [
            {"sku": item.sku, "quantity": item.quantity}
            for item in order_data.items
            if item.sku
        ]

        if items_check:
            available = await order_service.check_inventory_availability(items_check)
            if not available:
                logger.warning("inventory_not_available", items=items_check)
                # For demo, we still create the order

        # Create order
        order = order_service.create_order(db, order_data)

        # Publish order.created event
        publisher = await get_event_publisher()
        await publisher.publish_order_created({
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "items": [
                {
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "sku": item.sku
                }
                for item in order.items
            ],
            "origin_address": order.origin_address,
            "destination_address": order.destination_address,
            "package_weight": float(order.package_weight)
        })

        return order
    except Exception as e:
        logger.error("order_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create order")


@router.get("", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List orders with pagination.

    Args:
        page: Page number
        page_size: Number of items per page
        status: Filter by status
        db: Database session

    Returns:
        Paginated order list
    """
    skip = (page - 1) * page_size
    orders, total = order_service.get_orders(db, skip=skip, limit=page_size, status=status)

    return OrderListResponse(
        orders=orders,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get order by ID.

    Args:
        order_id: Order ID
        db: Database session

    Returns:
        Order details
    """
    order = order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    update_data: OrderUpdate,
    db: Session = Depends(get_db)
):
    """Update order status.

    Args:
        order_id: Order ID
        update_data: Update data
        db: Database session

    Returns:
        Updated order
    """
    order = order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if update_data.status:
        old_status = order.status
        order = order_service.update_order_status(db, order, update_data.status)

        # Publish status change event
        publisher = await get_event_publisher()
        await publisher.publish_order_status_changed(
            {
                "order_number": order.order_number,
                "customer_email": order.customer_email,
                "customer_name": order.customer_name
            },
            old_status,
            update_data.status
        )

    return order


@router.delete("/{order_id}", status_code=204)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Cancel an order.

    Args:
        order_id: Order ID
        db: Database session
    """
    order = order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_service.delete_order(db, order)


@router.get("/{order_id}/items")
def get_order_items(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get order items.

    Args:
        order_id: Order ID
        db: Database session

    Returns:
        Order items list
    """
    order = order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order.items
