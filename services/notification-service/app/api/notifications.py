"""Notification API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationTemplateCreate,
    NotificationTemplateResponse,
    NotificationTemplateListResponse
)
from app.services import notification_service
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1", tags=["notifications"])


@router.post("/notifications", response_model=NotificationResponse, status_code=201)
def send_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db)
):
    """Send a notification manually.

    Args:
        notification_data: Notification data
        db: Database session

    Returns:
        Created notification
    """
    try:
        notification = notification_service.send_notification(db, notification_data)
        return notification
    except Exception as e:
        logger.error("notification_send_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to send notification")


@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(pending|sent|failed)$"),
    db: Session = Depends(get_db)
):
    """List notifications with pagination and optional status filter.

    Args:
        page: Page number
        page_size: Number of items per page
        status: Filter by status (optional)
        db: Database session

    Returns:
        Paginated notification list
    """
    skip = (page - 1) * page_size
    notifications, total = notification_service.get_notifications(
        db, skip=skip, limit=page_size, status=status
    )

    return NotificationListResponse(
        notifications=notifications,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Get notification details by ID.

    Args:
        notification_id: Notification ID
        db: Database session

    Returns:
        Notification details
    """
    notification = notification_service.get_notification_by_id(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification


@router.get("/templates", response_model=NotificationTemplateListResponse)
def list_templates(
    db: Session = Depends(get_db)
):
    """List all notification templates.

    Args:
        db: Database session

    Returns:
        List of notification templates
    """
    templates = notification_service.get_templates(db)

    return NotificationTemplateListResponse(
        templates=templates,
        total=len(templates)
    )


@router.post("/templates", response_model=NotificationTemplateResponse, status_code=201)
def create_template(
    template_data: NotificationTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new notification template.

    Args:
        template_data: Template data
        db: Database session

    Returns:
        Created template
    """
    try:
        # Check if template already exists
        existing = notification_service.get_template_by_name(db, template_data.template_name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Template with name '{template_data.template_name}' already exists"
            )

        template = notification_service.create_template(
            db,
            template_data.template_name,
            template_data.subject_template,
            template_data.body_template,
            template_data.channel
        )
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error("template_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create template")
