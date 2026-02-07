"""SQLAlchemy database models for Inventory Service."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Computed

Base = declarative_base()


class Warehouse(Base):
    """Warehouse model."""

    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    capacity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to inventory items
    inventory_items = relationship("InventoryItem", back_populates="warehouse", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Warehouse {self.warehouse_code} - {self.name}>"


class InventoryItem(Base):
    """Inventory item model."""

    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, default=10)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to warehouse
    warehouse = relationship("Warehouse", back_populates="inventory_items")

    # Relationship to transactions
    transactions = relationship("InventoryTransaction", back_populates="inventory_item", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InventoryItem {self.sku} - {self.item_name}>"

    @property
    def available_quantity(self):
        """Calculate available quantity."""
        return self.quantity - self.reserved_quantity


class InventoryTransaction(Base):
    """Inventory transaction model for audit trail."""

    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)  # reserve, release, adjust, restock
    quantity = Column(Integer, nullable=False)
    order_number = Column(String(50))
    notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to inventory item
    inventory_item = relationship("InventoryItem", back_populates="transactions")

    def __repr__(self):
        return f"<InventoryTransaction {self.transaction_type} - {self.quantity}>"


# Create indexes
Index("idx_inventory_warehouse_sku", InventoryItem.warehouse_id, InventoryItem.sku, unique=True)
Index("idx_transactions_created", InventoryTransaction.created_at)
