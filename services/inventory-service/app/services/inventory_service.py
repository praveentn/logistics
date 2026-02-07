"""Business logic for inventory management."""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Warehouse, InventoryItem, InventoryTransaction
from app.schemas import WarehouseCreate, InventoryItemCreate
import structlog

logger = structlog.get_logger()


def create_warehouse(db: Session, warehouse_data: WarehouseCreate) -> Warehouse:
    """Create a new warehouse.

    Args:
        db: Database session
        warehouse_data: Warehouse creation data

    Returns:
        Created Warehouse instance
    """
    db_warehouse = Warehouse(
        warehouse_code=warehouse_data.warehouse_code,
        name=warehouse_data.name,
        location=warehouse_data.location,
        capacity=warehouse_data.capacity
    )

    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)

    logger.info(
        "warehouse_created",
        warehouse_code=warehouse_data.warehouse_code,
        name=warehouse_data.name
    )

    return db_warehouse


def get_warehouses(db: Session, skip: int = 0, limit: int = 100) -> List[Warehouse]:
    """Get list of warehouses.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of warehouses
    """
    return db.query(Warehouse).offset(skip).limit(limit).all()


def get_warehouse_by_code(db: Session, warehouse_code: str) -> Optional[Warehouse]:
    """Get warehouse by code.

    Args:
        db: Database session
        warehouse_code: Warehouse code

    Returns:
        Warehouse instance or None
    """
    return db.query(Warehouse).filter(Warehouse.warehouse_code == warehouse_code).first()


def create_inventory_item(db: Session, item_data: InventoryItemCreate) -> InventoryItem:
    """Create a new inventory item.

    Args:
        db: Database session
        item_data: Inventory item creation data

    Returns:
        Created InventoryItem instance
    """
    db_item = InventoryItem(
        warehouse_id=item_data.warehouse_id,
        sku=item_data.sku,
        item_name=item_data.item_name,
        quantity=item_data.quantity,
        reorder_level=item_data.reorder_level or 10
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    logger.info(
        "inventory_item_created",
        sku=item_data.sku,
        quantity=item_data.quantity
    )

    return db_item


def get_inventory_items(
    db: Session,
    warehouse_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[InventoryItem]:
    """Get inventory items with optional warehouse filter.

    Args:
        db: Database session
        warehouse_id: Optional warehouse ID to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of inventory items
    """
    query = db.query(InventoryItem)

    if warehouse_id:
        query = query.filter(InventoryItem.warehouse_id == warehouse_id)

    return query.offset(skip).limit(limit).all()


def get_inventory_by_sku(db: Session, sku: str, warehouse_code: Optional[str] = None) -> Optional[InventoryItem]:
    """Get inventory item by SKU.

    Args:
        db: Database session
        sku: Stock keeping unit
        warehouse_code: Optional warehouse code to filter by

    Returns:
        InventoryItem instance or None
    """
    query = db.query(InventoryItem).filter(InventoryItem.sku == sku)

    if warehouse_code:
        query = query.join(Warehouse).filter(Warehouse.warehouse_code == warehouse_code)

    return query.first()


def check_availability(db: Session, items: List[dict]) -> Tuple[bool, List[dict]]:
    """Check if items are available in inventory.

    Args:
        db: Database session
        items: List of items to check [{"sku": "SKU-001", "quantity": 2}]

    Returns:
        Tuple of (all_available: bool, details: List[dict])
    """
    all_available = True
    details = []

    for item in items:
        sku = item.get("sku")
        required_quantity = item.get("quantity", 0)

        if not sku:
            continue

        # Get total available across all warehouses
        inventory_items = db.query(InventoryItem).filter(InventoryItem.sku == sku).all()

        total_available = sum(item.available_quantity for item in inventory_items)

        item_available = total_available >= required_quantity

        details.append({
            "sku": sku,
            "required": required_quantity,
            "available": total_available,
            "sufficient": item_available
        })

        if not item_available:
            all_available = False

    return all_available, details


def reserve_inventory(db: Session, order_number: str, items: List[dict]) -> bool:
    """Reserve inventory for an order.

    Args:
        db: Database session
        order_number: Order number
        items: List of items to reserve

    Returns:
        True if successful
    """
    for item in items:
        sku = item.get("sku")
        quantity = item.get("quantity", 0)

        if not sku:
            continue

        # Find inventory with sufficient quantity
        inventory_item = db.query(InventoryItem).filter(
            InventoryItem.sku == sku
        ).filter(
            InventoryItem.quantity - InventoryItem.reserved_quantity >= quantity
        ).first()

        if not inventory_item:
            logger.warning(
                "insufficient_inventory",
                sku=sku,
                required=quantity
            )
            continue

        # Reserve the quantity
        inventory_item.reserved_quantity += quantity

        # Create transaction record
        transaction = InventoryTransaction(
            inventory_item_id=inventory_item.id,
            transaction_type="reserve",
            quantity=quantity,
            order_number=order_number,
            notes=f"Reserved for order {order_number}"
        )

        db.add(transaction)

        logger.info(
            "inventory_reserved",
            sku=sku,
            quantity=quantity,
            order_number=order_number
        )

    db.commit()
    return True


def release_inventory(db: Session, order_number: str) -> bool:
    """Release reserved inventory for a cancelled order.

    Args:
        db: Database session
        order_number: Order number

    Returns:
        True if successful
    """
    # Find all reservations for this order
    reservations = db.query(InventoryTransaction).filter(
        and_(
            InventoryTransaction.order_number == order_number,
            InventoryTransaction.transaction_type == "reserve"
        )
    ).all()

    for reservation in reservations:
        inventory_item = reservation.inventory_item
        inventory_item.reserved_quantity -= reservation.quantity

        # Create release transaction
        release_transaction = InventoryTransaction(
            inventory_item_id=inventory_item.id,
            transaction_type="release",
            quantity=reservation.quantity,
            order_number=order_number,
            notes=f"Released from cancelled order {order_number}"
        )

        db.add(release_transaction)

        logger.info(
            "inventory_released",
            sku=inventory_item.sku,
            quantity=reservation.quantity,
            order_number=order_number
        )

    db.commit()
    return True


def adjust_inventory(db: Session, sku: str, warehouse_code: str, quantity_change: int, notes: str = None) -> bool:
    """Adjust inventory quantity.

    Args:
        db: Database session
        sku: Stock keeping unit
        warehouse_code: Warehouse code
        quantity_change: Quantity to add (positive) or remove (negative)
        notes: Optional notes

    Returns:
        True if successful
    """
    warehouse = get_warehouse_by_code(db, warehouse_code)
    if not warehouse:
        logger.error("warehouse_not_found", warehouse_code=warehouse_code)
        return False

    inventory_item = db.query(InventoryItem).filter(
        and_(
            InventoryItem.sku == sku,
            InventoryItem.warehouse_id == warehouse.id
        )
    ).first()

    if not inventory_item:
        logger.error("inventory_item_not_found", sku=sku)
        return False

    inventory_item.quantity += quantity_change

    # Ensure quantity doesn't go negative
    if inventory_item.quantity < 0:
        inventory_item.quantity = 0

    # Create transaction
    transaction = InventoryTransaction(
        inventory_item_id=inventory_item.id,
        transaction_type="adjust" if quantity_change > 0 else "reduce",
        quantity=abs(quantity_change),
        notes=notes or f"Manual adjustment: {quantity_change:+d}"
    )

    db.add(transaction)
    db.commit()

    logger.info(
        "inventory_adjusted",
        sku=sku,
        warehouse=warehouse_code,
        change=quantity_change,
        new_quantity=inventory_item.quantity
    )

    return True


def get_low_stock_items(db: Session) -> List[InventoryItem]:
    """Get items with quantity below reorder level.

    Args:
        db: Database session

    Returns:
        List of low stock items
    """
    return db.query(InventoryItem).filter(
        InventoryItem.quantity - InventoryItem.reserved_quantity <= InventoryItem.reorder_level
    ).all()
