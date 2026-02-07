"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# Order Item schemas
class OrderItemBase(BaseModel):
    """Base schema for order items."""

    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0)
    sku: Optional[str] = Field(None, max_length=100)


class OrderItemCreate(OrderItemBase):
    """Schema for creating order items."""

    pass


class OrderItemResponse(OrderItemBase):
    """Schema for order item responses."""

    id: int
    order_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Order schemas
class OrderBase(BaseModel):
    """Base schema for orders."""

    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: EmailStr
    origin_address: str = Field(..., min_length=1, max_length=500)
    destination_address: str = Field(..., min_length=1, max_length=500)
    package_weight: float = Field(..., gt=0, description="Weight in kg")
    package_dimensions: Optional[str] = Field(None, max_length=50, description="LxWxH in cm")


class OrderCreate(OrderBase):
    """Schema for creating orders."""

    items: List[OrderItemCreate] = Field(..., min_length=1)

    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError('Order must have at least one item')
        return v


class OrderUpdate(BaseModel):
    """Schema for updating orders."""

    status: Optional[str] = Field(None, pattern="^(pending|processing|shipped|delivered|cancelled)$")
    estimated_delivery: Optional[datetime] = None


class OrderResponse(OrderBase):
    """Schema for order responses."""

    id: int
    order_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    estimated_delivery: Optional[datetime]
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Schema for paginated order list responses."""

    orders: List[OrderResponse]
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
