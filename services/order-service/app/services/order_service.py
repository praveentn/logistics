"""Business logic for order management."""

import os
import httpx
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Order, OrderItem
from app.schemas import OrderCreate, OrderUpdate
import structlog

logger = structlog.get_logger()

INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8003")


async def check_inventory_availability(items: List[dict]) -> bool:
    """Check if items are available in inventory.

    Args:
        items: List of items to check

    Returns:
        True if all items available, False otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INVENTORY_SERVICE_URL}/api/v1/inventory/check",
                json={"items": items},
                timeout=5.0
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("available", False)
            else:
                logger.warning(
                    "inventory_check_failed",
                    status_code=response.status_code
                )
                return False
    except Exception as e:
        logger.error("inventory_service_unavailable", error=str(e))
        # For demo purposes, allow order creation even if inventory check fails
        return True


def generate_order_number() -> str:
    """Generate a unique order number.

    Returns:
        Order number string
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"ORD-{timestamp}"


def create_order(db: Session, order_data: OrderCreate) -> Order:
    """Create a new order.

    Args:
        db: Database session
        order_data: Order creation data

    Returns:
        Created Order instance
    """
    # Generate order number
    order_number = generate_order_number()

    # Create order
    db_order = Order(
        order_number=order_number,
        customer_name=order_data.customer_name,
        customer_email=order_data.customer_email,
        origin_address=order_data.origin_address,
        destination_address=order_data.destination_address,
        package_weight=order_data.package_weight,
        package_dimensions=order_data.package_dimensions,
        status="pending",
        estimated_delivery=datetime.utcnow() + timedelta(days=3)
    )

    db.add(db_order)
    db.flush()  # Get the order ID

    # Create order items
    for item_data in order_data.items:
        db_item = OrderItem(
            order_id=db_order.id,
            item_name=item_data.item_name,
            quantity=item_data.quantity,
            sku=item_data.sku
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_order)

    logger.info(
        "order_created",
        order_number=order_number,
        customer=order_data.customer_name,
        items_count=len(order_data.items)
    )

    return db_order


def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
    """Get order by ID.

    Args:
        db: Database session
        order_id: Order ID

    Returns:
        Order instance or None
    """
    return db.query(Order).filter(Order.id == order_id).first()


def get_order_by_number(db: Session, order_number: str) -> Optional[Order]:
    """Get order by order number.

    Args:
        db: Database session
        order_number: Order number

    Returns:
        Order instance or None
    """
    return db.query(Order).filter(Order.order_number == order_number).first()


def get_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
) -> tuple[List[Order], int]:
    """Get list of orders with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status (optional)

    Returns:
        Tuple of (orders list, total count)
    """
    query = db.query(Order)

    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    return orders, total


def update_order_status(
    db: Session,
    order: Order,
    new_status: str
) -> Order:
    """Update order status.

    Args:
        db: Database session
        order: Order instance
        new_status: New status value

    Returns:
        Updated Order instance
    """
    old_status = order.status
    order.status = new_status
    order.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    logger.info(
        "order_status_updated",
        order_number=order.order_number,
        old_status=old_status,
        new_status=new_status
    )

    return order


def delete_order(db: Session, order: Order):
    """Delete an order (cancel).

    Args:
        db: Database session
        order: Order instance
    """
    order.status = "cancelled"
    order.updated_at = datetime.utcnow()
    db.commit()

    logger.info("order_cancelled", order_number=order.order_number)


def get_order_statistics(db: Session) -> dict:
    """Get order statistics.

    Args:
        db: Database session

    Returns:
        Dictionary with statistics
    """
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == "pending").count()
    processing_orders = db.query(Order).filter(Order.status == "processing").count()
    shipped_orders = db.query(Order).filter(Order.status == "shipped").count()
    delivered_orders = db.query(Order).filter(Order.status == "delivered").count()
    cancelled_orders = db.query(Order).filter(Order.status == "cancelled").count()

    return {
        "total": total_orders,
        "pending": pending_orders,
        "processing": processing_orders,
        "shipped": shipped_orders,
        "delivered": delivered_orders,
        "cancelled": cancelled_orders
    }
