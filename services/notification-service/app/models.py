"""SQLAlchemy database models for Notification Service."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Notification(Base):
    """Notification model representing sent or pending notifications."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(String(100), nullable=False, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False, default="email", index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    order_number = Column(String(50), index=True)
    tracking_number = Column(String(50), index=True)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<Notification {self.id} - {self.notification_type} - {self.status}>"


class NotificationTemplate(Base):
    """NotificationTemplate model for storing reusable notification templates."""

    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), unique=True, nullable=False, index=True)
    subject_template = Column(String(500), nullable=False)
    body_template = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False, default="email")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<NotificationTemplate {self.template_name} - {self.channel}>"


# Create indexes for better query performance
Index("idx_notifications_status_created", Notification.status, Notification.created_at)
Index("idx_notifications_type_status", Notification.notification_type, Notification.status)
