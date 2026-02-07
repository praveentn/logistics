"""Business logic for shipment tracking management."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Shipment, TrackingEvent
from app.schemas import ShipmentCreate, TrackingEventCreate
import structlog

logger = structlog.get_logger()


def generate_tracking_number() -> str:
    """Generate a unique tracking number.

    Returns:
        Tracking number string
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"TRK-{timestamp}"


def create_shipment(db: Session, shipment_data: ShipmentCreate) -> Shipment:
    """Create a new shipment.

    Args:
        db: Database session
        shipment_data: Shipment creation data

    Returns:
        Created Shipment instance
    """
    # Generate tracking number
    tracking_number = generate_tracking_number()

    # Create shipment
    db_shipment = Shipment(
        tracking_number=tracking_number,
        order_number=shipment_data.order_number,
        carrier=shipment_data.carrier,
        current_location=shipment_data.current_location,
        status="in_transit"
    )

    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)

    logger.info(
        "shipment_created",
        tracking_number=tracking_number,
        order_number=shipment_data.order_number,
        carrier=shipment_data.carrier
    )

    return db_shipment


def get_shipment_by_id(db: Session, shipment_id: int) -> Optional[Shipment]:
    """Get shipment by ID.

    Args:
        db: Database session
        shipment_id: Shipment ID

    Returns:
        Shipment instance or None
    """
    return db.query(Shipment).filter(Shipment.id == shipment_id).first()


def get_shipment_by_tracking_number(db: Session, tracking_number: str) -> Optional[Shipment]:
    """Get shipment by tracking number.

    Args:
        db: Database session
        tracking_number: Tracking number

    Returns:
        Shipment instance or None
    """
    return db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()


def get_shipment_by_order_number(db: Session, order_number: str) -> Optional[Shipment]:
    """Get shipment by order number.

    Args:
        db: Database session
        order_number: Order number

    Returns:
        Shipment instance or None
    """
    return db.query(Shipment).filter(Shipment.order_number == order_number).first()


def get_shipments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
) -> tuple[List[Shipment], int]:
    """Get list of shipments with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status (optional)

    Returns:
        Tuple of (shipments list, total count)
    """
    query = db.query(Shipment)

    if status:
        query = query.filter(Shipment.status == status)

    total = query.count()
    shipments = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()

    return shipments, total


def update_shipment_status(
    db: Session,
    shipment: Shipment,
    new_status: str,
    location: Optional[str] = None
) -> Shipment:
    """Update shipment status.

    Args:
        db: Database session
        shipment: Shipment instance
        new_status: New status value
        location: Optional location update

    Returns:
        Updated Shipment instance
    """
    old_status = shipment.status
    shipment.status = new_status
    shipment.updated_at = datetime.utcnow()

    if location:
        shipment.current_location = location

    db.commit()
    db.refresh(shipment)

    logger.info(
        "shipment_status_updated",
        tracking_number=shipment.tracking_number,
        old_status=old_status,
        new_status=new_status
    )

    return shipment


def create_tracking_event(
    db: Session,
    shipment: Shipment,
    event_data: TrackingEventCreate
) -> TrackingEvent:
    """Create a tracking event for a shipment.

    Args:
        db: Database session
        shipment: Shipment instance
        event_data: Event data

    Returns:
        Created TrackingEvent instance
    """
    db_event = TrackingEvent(
        shipment_id=shipment.id,
        location=event_data.location,
        event_type=event_data.event_type,
        description=event_data.description
    )

    db.add(db_event)

    # Update shipment's current location
    shipment.current_location = event_data.location
    shipment.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_event)

    logger.info(
        "tracking_event_created",
        tracking_number=shipment.tracking_number,
        event_type=event_data.event_type,
        location=event_data.location
    )

    return db_event


def get_tracking_events(
    db: Session,
    shipment_id: int
) -> List[TrackingEvent]:
    """Get all tracking events for a shipment.

    Args:
        db: Database session
        shipment_id: Shipment ID

    Returns:
        List of tracking events
    """
    return db.query(TrackingEvent).filter(
        TrackingEvent.shipment_id == shipment_id
    ).order_by(TrackingEvent.timestamp.desc()).all()


def get_shipment_statistics(db: Session) -> dict:
    """Get shipment statistics.

    Args:
        db: Database session

    Returns:
        Dictionary with statistics
    """
    total_shipments = db.query(Shipment).count()
    in_transit = db.query(Shipment).filter(Shipment.status == "in_transit").count()
    out_for_delivery = db.query(Shipment).filter(Shipment.status == "out_for_delivery").count()
    delivered = db.query(Shipment).filter(Shipment.status == "delivered").count()

    return {
        "total": total_shipments,
        "in_transit": in_transit,
        "out_for_delivery": out_for_delivery,
        "delivered": delivered
    }
