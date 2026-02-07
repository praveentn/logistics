"""Pydantic schemas for Inventory Service."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Warehouse schemas
class WarehouseBase(BaseModel):
    """Base schema for warehouses."""

    warehouse_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    location: str = Field(..., min_length=1, max_length=255)
    capacity: int = Field(..., gt=0)


class WarehouseCreate(WarehouseBase):
    """Schema for creating warehouses."""

    pass


class WarehouseResponse(WarehouseBase):
    """Schema for warehouse responses."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Inventory Item schemas
class InventoryItemBase(BaseModel):
    """Base schema for inventory items."""

    sku: str = Field(..., min_length=1, max_length=100)
    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., ge=0)
    reorder_level: Optional[int] = Field(10, ge=0)


class InventoryItemCreate(InventoryItemBase):
    """Schema for creating inventory items."""

    warehouse_id: int


class InventoryItemResponse(InventoryItemBase):
    """Schema for inventory item responses."""

    id: int
    warehouse_id: int
    reserved_quantity: int
    available_quantity: int
    updated_at: datetime

    class Config:
        from_attributes = True


# Inventory check schemas
class ItemCheck(BaseModel):
    """Schema for checking item availability."""

    sku: Optional[str] = None
    quantity: int = Field(..., gt=0)


class InventoryCheckRequest(BaseModel):
    """Schema for inventory check request."""

    items: List[ItemCheck]


class InventoryCheckResponse(BaseModel):
    """Schema for inventory check response."""

    available: bool
    details: List[dict]


# Inventory operation schemas
class InventoryReserveRequest(BaseModel):
    """Schema for reserving inventory."""

    order_number: str
    items: List[dict]  # [{"sku": "SKU-001", "quantity": 2}]


class InventoryAdjustRequest(BaseModel):
    """Schema for adjusting inventory."""

    sku: str
    warehouse_code: str
    quantity: int
    notes: Optional[str] = None


# Transaction schemas
class InventoryTransactionResponse(BaseModel):
    """Schema for transaction responses."""

    id: int
    inventory_item_id: int
    transaction_type: str
    quantity: int
    order_number: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Health check schema
class HealthResponse(BaseModel):
    """Schema for health check responses."""

    status: str
    service: str
    timestamp: datetime
    database: str
    messaging: str
