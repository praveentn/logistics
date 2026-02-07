"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# Tracking Event schemas
class TrackingEventBase(BaseModel):
    """Base schema for tracking events."""

    location: str = Field(..., min_length=1, max_length=500)
    event_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)


class TrackingEventCreate(TrackingEventBase):
    """Schema for creating tracking events."""

    pass


class TrackingEventResponse(TrackingEventBase):
    """Schema for tracking event responses."""

    id: int
    shipment_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# Shipment schemas
class ShipmentBase(BaseModel):
    """Base schema for shipments."""

    order_number: str = Field(..., min_length=1, max_length=50)
    carrier: str = Field(..., min_length=1, max_length=100)
    current_location: Optional[str] = Field(None, max_length=500)


class ShipmentCreate(ShipmentBase):
    """Schema for creating shipments."""

    pass


class ShipmentUpdate(BaseModel):
    """Schema for updating shipments."""

    carrier: Optional[str] = Field(None, min_length=1, max_length=100)
    current_location: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern="^(in_transit|out_for_delivery|delivered)$")


class ShipmentResponse(ShipmentBase):
    """Schema for shipment responses."""

    id: int
    tracking_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    events: List[TrackingEventResponse]

    class Config:
        from_attributes = True


class ShipmentListResponse(BaseModel):
    """Schema for paginated shipment list responses."""

    shipments: List[ShipmentResponse]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    """Schema for health check responses."""

    status: str
    service: str
    timestamp: datetime
    database: str
    messaging: str
