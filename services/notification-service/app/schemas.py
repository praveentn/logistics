"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


# Notification schemas
class NotificationBase(BaseModel):
    """Base schema for notifications."""

    notification_type: str = Field(..., min_length=1, max_length=100)
    recipient: EmailStr
    subject: str = Field(..., min_length=1, max_length=500)
    message: str = Field(..., min_length=1)
    channel: str = Field(default="email", pattern="^(email|sms)$")
    order_number: Optional[str] = Field(None, max_length=50)
    tracking_number: Optional[str] = Field(None, max_length=50)


class NotificationCreate(NotificationBase):
    """Schema for creating notifications."""

    pass


class NotificationResponse(NotificationBase):
    """Schema for notification responses."""

    id: int
    status: str
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for paginated notification list responses."""

    notifications: List[NotificationResponse]
    total: int
    page: int
    page_size: int


# NotificationTemplate schemas
class NotificationTemplateBase(BaseModel):
    """Base schema for notification templates."""

    template_name: str = Field(..., min_length=1, max_length=100)
    subject_template: str = Field(..., min_length=1, max_length=500)
    body_template: str = Field(..., min_length=1)
    channel: str = Field(default="email", pattern="^(email|sms)$")


class NotificationTemplateCreate(NotificationTemplateBase):
    """Schema for creating notification templates."""

    pass


class NotificationTemplateResponse(NotificationTemplateBase):
    """Schema for notification template responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationTemplateListResponse(BaseModel):
    """Schema for notification template list responses."""

    templates: List[NotificationTemplateResponse]
    total: int


class HealthResponse(BaseModel):
    """Schema for health check responses."""

    status: str
    service: str
    timestamp: datetime
    database: str
    messaging: str
