"""SQLAlchemy database models for Order Service."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Order(Base):
    """Order model representing a shipment order."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    origin_address = Column(String(500), nullable=False)
    destination_address = Column(String(500), nullable=False)
    package_weight = Column(Numeric(10, 2), nullable=False)
    package_dimensions = Column(String(50))
    status = Column(String(50), nullable=False, default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    estimated_delivery = Column(DateTime)

    # Relationship to order items
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_number} - {self.status}>"


class OrderItem(Base):
    """Order item model representing items in an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    sku = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to order
    order = relationship("Order", back_populates="items")

    def __repr__(self):
        return f"<OrderItem {self.item_name} x{self.quantity}>"


# Create indexes for better query performance
Index("idx_orders_status_created", Order.status, Order.created_at)
