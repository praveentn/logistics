"""Inventory API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    WarehouseCreate,
    WarehouseResponse,
    InventoryItemResponse,
    InventoryCheckRequest,
    InventoryCheckResponse,
    InventoryReserveRequest,
    InventoryAdjustRequest
)
from app.services import inventory_service
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1", tags=["inventory"])


@router.post("/warehouses", response_model=WarehouseResponse, status_code=201)
def create_warehouse(
    warehouse_data: WarehouseCreate,
    db: Session = Depends(get_db)
):
    """Create a new warehouse.

    Args:
        warehouse_data: Warehouse creation data
        db: Database session

    Returns:
        Created warehouse
    """
    try:
        # Check if warehouse code already exists
        existing = inventory_service.get_warehouse_by_code(db, warehouse_data.warehouse_code)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Warehouse with code '{warehouse_data.warehouse_code}' already exists"
            )

        warehouse = inventory_service.create_warehouse(db, warehouse_data)
        return warehouse
    except HTTPException:
        raise
    except Exception as e:
        logger.error("warehouse_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create warehouse")


@router.get("/warehouses", response_model=list[WarehouseResponse])
def list_warehouses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all warehouses with pagination.

    Args:
        page: Page number
        page_size: Number of items per page
        db: Database session

    Returns:
        List of warehouses
    """
    skip = (page - 1) * page_size
    warehouses = inventory_service.get_warehouses(db, skip=skip, limit=page_size)
    return warehouses


@router.get("/warehouses/{warehouse_id}/inventory", response_model=list[InventoryItemResponse])
def get_warehouse_inventory(
    warehouse_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get inventory items for a specific warehouse.

    Args:
        warehouse_id: Warehouse ID
        page: Page number
        page_size: Number of items per page
        db: Database session

    Returns:
        List of inventory items
    """
    skip = (page - 1) * page_size
    items = inventory_service.get_inventory_items(
        db,
        warehouse_id=warehouse_id,
        skip=skip,
        limit=page_size
    )
    return items


@router.post("/inventory/check", response_model=InventoryCheckResponse)
def check_inventory_availability(
    request: InventoryCheckRequest,
    db: Session = Depends(get_db)
):
    """Check if items are available in inventory.

    Args:
        request: Inventory check request with list of items
        db: Database session

    Returns:
        Availability status and details for each item
    """
    try:
        items_to_check = [
            {"sku": item.sku, "quantity": item.quantity}
            for item in request.items
            if item.sku
        ]

        available, details = inventory_service.check_availability(db, items_to_check)

        return InventoryCheckResponse(
            available=available,
            details=details
        )
    except Exception as e:
        logger.error("inventory_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to check inventory")


@router.post("/inventory/reserve", status_code=200)
def reserve_inventory(
    request: InventoryReserveRequest,
    db: Session = Depends(get_db)
):
    """Reserve inventory items for an order.

    Args:
        request: Reservation request with order number and items
        db: Database session

    Returns:
        Success message
    """
    try:
        success = inventory_service.reserve_inventory(
            db,
            request.order_number,
            request.items
        )

        if success:
            return {
                "status": "success",
                "message": f"Inventory reserved for order {request.order_number}"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to reserve inventory"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("inventory_reservation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reserve inventory")


@router.post("/inventory/release", status_code=200)
def release_inventory(
    order_number: str = Query(..., description="Order number to release inventory for"),
    db: Session = Depends(get_db)
):
    """Release reserved inventory for a cancelled order.

    Args:
        order_number: Order number
        db: Database session

    Returns:
        Success message
    """
    try:
        success = inventory_service.release_inventory(db, order_number)

        if success:
            return {
                "status": "success",
                "message": f"Inventory released for order {order_number}"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No reservations found for order {order_number}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("inventory_release_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to release inventory")


@router.post("/inventory/adjust", status_code=200)
def adjust_inventory(
    request: InventoryAdjustRequest,
    db: Session = Depends(get_db)
):
    """Adjust inventory quantity for an item.

    Args:
        request: Adjustment request with SKU, warehouse, and quantity change
        db: Database session

    Returns:
        Success message
    """
    try:
        success = inventory_service.adjust_inventory(
            db,
            request.sku,
            request.warehouse_code,
            request.quantity,
            request.notes
        )

        if success:
            return {
                "status": "success",
                "message": f"Inventory adjusted for SKU {request.sku}"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Item with SKU '{request.sku}' not found in warehouse '{request.warehouse_code}'"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("inventory_adjustment_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to adjust inventory")


@router.get("/inventory/low-stock", response_model=list[InventoryItemResponse])
def get_low_stock_items(
    db: Session = Depends(get_db)
):
    """Get items with quantity below reorder level.

    Args:
        db: Database session

    Returns:
        List of low stock items
    """
    try:
        items = inventory_service.get_low_stock_items(db)
        return items
    except Exception as e:
        logger.error("low_stock_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve low stock items")
