"""SQLAlchemy database models for Tracking Service."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Shipment(Base):
    """Shipment model representing a tracked shipment."""

    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(50), unique=True, nullable=False, index=True)
    order_number = Column(String(50), nullable=False, index=True)
    carrier = Column(String(100), nullable=False)
    current_location = Column(String(500))
    status = Column(String(50), nullable=False, default="in_transit", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to tracking events
    events = relationship("TrackingEvent", back_populates="shipment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Shipment {self.tracking_number} - {self.status}>"


class TrackingEvent(Base):
    """Tracking event model representing shipment status updates."""

    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    location = Column(String(500), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship to shipment
    shipment = relationship("Shipment", back_populates="events")

    def __repr__(self):
        return f"<TrackingEvent {self.event_type} at {self.location}>"


# Create indexes for better query performance
Index("idx_shipments_status_created", Shipment.status, Shipment.created_at)
Index("idx_events_shipment_timestamp", TrackingEvent.shipment_id, TrackingEvent.timestamp)
