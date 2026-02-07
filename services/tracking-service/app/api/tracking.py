"""Tracking API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentListResponse,
    TrackingEventCreate,
    TrackingEventResponse
)
from app.services import tracking_service
from app.messaging.publisher import get_event_publisher
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/shipments", tags=["shipments"])


@router.post("", response_model=ShipmentResponse, status_code=201)
async def create_shipment(
    shipment_data: ShipmentCreate,
    db: Session = Depends(get_db)
):
    """Create a new shipment.

    Args:
        shipment_data: Shipment creation data
        db: Database session

    Returns:
        Created shipment
    """
    try:
        # Create shipment
        shipment = tracking_service.create_shipment(db, shipment_data)

        # Publish shipment.created event
        publisher = await get_event_publisher()
        await publisher.publish_shipment_created({
            "tracking_number": shipment.tracking_number,
            "order_number": shipment.order_number,
            "carrier": shipment.carrier,
            "status": shipment.status,
            "current_location": shipment.current_location
        })

        return shipment
    except Exception as e:
        logger.error("shipment_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create shipment")


@router.get("", response_model=ShipmentListResponse)
def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List shipments with pagination.

    Args:
        page: Page number
        page_size: Number of items per page
        status: Filter by status
        db: Database session

    Returns:
        Paginated shipment list
    """
    skip = (page - 1) * page_size
    shipments, total = tracking_service.get_shipments(db, skip=skip, limit=page_size, status=status)

    return ShipmentListResponse(
        shipments=shipments,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{tracking_number}", response_model=ShipmentResponse)
def get_shipment(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """Get shipment by tracking number.

    Args:
        tracking_number: Tracking number
        db: Database session

    Returns:
        Shipment details
    """
    shipment = tracking_service.get_shipment_by_tracking_number(db, tracking_number)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return shipment


@router.post("/{tracking_number}/events", response_model=TrackingEventResponse, status_code=201)
async def add_tracking_event(
    tracking_number: str,
    event_data: TrackingEventCreate,
    db: Session = Depends(get_db)
):
    """Add a tracking event to a shipment.

    Args:
        tracking_number: Tracking number
        event_data: Event data
        db: Database session

    Returns:
        Created tracking event
    """
    shipment = tracking_service.get_shipment_by_tracking_number(db, tracking_number)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    try:
        event = tracking_service.create_tracking_event(db, shipment, event_data)

        # Publish tracking.event_added event
        publisher = await get_event_publisher()
        await publisher.publish_tracking_event({
            "tracking_number": shipment.tracking_number,
            "order_number": shipment.order_number,
            "event_type": event.event_type,
            "location": event.location,
            "description": event.description,
            "timestamp": event.timestamp.isoformat()
        })

        return event
    except Exception as e:
        logger.error("tracking_event_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to add tracking event")


@router.get("/order/{order_number}", response_model=ShipmentResponse)
def get_shipment_by_order(
    order_number: str,
    db: Session = Depends(get_db)
):
    """Get shipment by order number.

    Args:
        order_number: Order number
        db: Database session

    Returns:
        Shipment details
    """
    shipment = tracking_service.get_shipment_by_order_number(db, order_number)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found for this order")

    return shipment
