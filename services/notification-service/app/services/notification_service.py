"""Business logic for notification management."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Notification, NotificationTemplate
from app.schemas import NotificationCreate
import structlog

logger = structlog.get_logger()


def send_notification(db: Session, notification_data: NotificationCreate) -> Notification:
    """Send a notification (simulated - saves to DB and logs).

    Args:
        db: Database session
        notification_data: Notification data

    Returns:
        Created Notification instance
    """
    # Create notification record
    db_notification = Notification(
        notification_type=notification_data.notification_type,
        recipient=notification_data.recipient,
        subject=notification_data.subject,
        message=notification_data.message,
        channel=notification_data.channel,
        order_number=notification_data.order_number,
        tracking_number=notification_data.tracking_number,
        status="pending"
    )

    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    # Simulate sending (just log it)
    try:
        logger.info(
            "notification_sending",
            notification_id=db_notification.id,
            notification_type=notification_data.notification_type,
            recipient=notification_data.recipient,
            channel=notification_data.channel
        )

        # Simulate successful send
        db_notification.status = "sent"
        db_notification.sent_at = datetime.utcnow()
        db.commit()
        db.refresh(db_notification)

        logger.info(
            "notification_sent",
            notification_id=db_notification.id,
            recipient=notification_data.recipient,
            channel=notification_data.channel
        )
    except Exception as e:
        logger.error(
            "notification_send_failed",
            notification_id=db_notification.id,
            error=str(e)
        )
        db_notification.status = "failed"
        db.commit()
        db.refresh(db_notification)

    return db_notification


def render_template(template: NotificationTemplate, data: Dict[str, Any]) -> tuple[str, str]:
    """Render notification template with provided data.

    Args:
        template: NotificationTemplate instance
        data: Dictionary with template variables

    Returns:
        Tuple of (rendered_subject, rendered_body)
    """
    # Simple template rendering (replace {{variable}} with values)
    subject = template.subject_template
    body = template.body_template

    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        subject = subject.replace(placeholder, str(value))
        body = body.replace(placeholder, str(value))

    return subject, body


def create_from_event(
    db: Session,
    event_type: str,
    event_data: Dict[str, Any]
) -> Optional[Notification]:
    """Create notification from event data.

    Args:
        db: Database session
        event_type: Type of event (e.g., 'order.created')
        event_data: Event payload data

    Returns:
        Created Notification instance or None
    """
    # Map event types to template names
    template_mapping = {
        "order.created": "order_confirmation",
        "order.status_changed": "order_status_update",
        "shipment.created": "shipment_created",
        "shipment.updated": "shipment_tracking_update",
        "inventory.low_stock": "inventory_low_stock_alert"
    }

    template_name = template_mapping.get(event_type)
    if not template_name:
        logger.warning("no_template_for_event", event_type=event_type)
        return None

    # Get template
    template = get_template_by_name(db, template_name)
    if not template:
        logger.warning("template_not_found", template_name=template_name)
        return None

    # Prepare template data
    template_data = _prepare_template_data(event_type, event_data)

    # Render template
    subject, body = render_template(template, template_data)

    # Get recipient email
    recipient = event_data.get("customer_email") or event_data.get("recipient")
    if not recipient:
        logger.warning("no_recipient_in_event", event_type=event_type)
        return None

    # Create notification
    notification_data = NotificationCreate(
        notification_type=event_type,
        recipient=recipient,
        subject=subject,
        message=body,
        channel=template.channel,
        order_number=event_data.get("order_number"),
        tracking_number=event_data.get("tracking_number")
    )

    return send_notification(db, notification_data)


def _prepare_template_data(event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare template data from event data.

    Args:
        event_type: Type of event
        event_data: Event payload

    Returns:
        Dictionary with template variables
    """
    # Common fields
    data = {
        "customer_name": event_data.get("customer_name", "Customer"),
        "customer_email": event_data.get("customer_email", ""),
        "order_number": event_data.get("order_number", "N/A"),
        "tracking_number": event_data.get("tracking_number", "N/A"),
    }

    # Event-specific fields
    if event_type == "order.created":
        data.update({
            "origin_address": event_data.get("origin_address", ""),
            "destination_address": event_data.get("destination_address", ""),
        })
    elif event_type == "order.status_changed":
        data.update({
            "old_status": event_data.get("old_status", ""),
            "new_status": event_data.get("new_status", ""),
        })
    elif event_type in ["shipment.created", "shipment.updated"]:
        data.update({
            "carrier": event_data.get("carrier", ""),
            "current_location": event_data.get("current_location", ""),
            "estimated_delivery": event_data.get("estimated_delivery", ""),
        })
    elif event_type == "inventory.low_stock":
        data.update({
            "sku": event_data.get("sku", ""),
            "product_name": event_data.get("product_name", ""),
            "current_quantity": event_data.get("current_quantity", 0),
            "threshold": event_data.get("threshold", 0),
        })

    return data


def get_notification_by_id(db: Session, notification_id: int) -> Optional[Notification]:
    """Get notification by ID.

    Args:
        db: Database session
        notification_id: Notification ID

    Returns:
        Notification instance or None
    """
    return db.query(Notification).filter(Notification.id == notification_id).first()


def get_notifications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
) -> tuple[List[Notification], int]:
    """Get list of notifications with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status (optional)

    Returns:
        Tuple of (notifications list, total count)
    """
    query = db.query(Notification)

    if status:
        query = query.filter(Notification.status == status)

    total = query.count()
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    return notifications, total


def get_template_by_name(db: Session, template_name: str) -> Optional[NotificationTemplate]:
    """Get template by name.

    Args:
        db: Database session
        template_name: Template name

    Returns:
        NotificationTemplate instance or None
    """
    return db.query(NotificationTemplate).filter(
        NotificationTemplate.template_name == template_name
    ).first()


def create_template(
    db: Session,
    template_name: str,
    subject_template: str,
    body_template: str,
    channel: str = "email"
) -> NotificationTemplate:
    """Create a notification template.

    Args:
        db: Database session
        template_name: Unique template name
        subject_template: Subject template with placeholders
        body_template: Body template with placeholders
        channel: Notification channel (email/sms)

    Returns:
        Created NotificationTemplate instance
    """
    db_template = NotificationTemplate(
        template_name=template_name,
        subject_template=subject_template,
        body_template=body_template,
        channel=channel
    )

    db.add(db_template)
    db.commit()
    db.refresh(db_template)

    logger.info("template_created", template_name=template_name, channel=channel)

    return db_template


def get_templates(db: Session) -> List[NotificationTemplate]:
    """Get all notification templates.

    Args:
        db: Database session

    Returns:
        List of NotificationTemplate instances
    """
    return db.query(NotificationTemplate).order_by(NotificationTemplate.template_name).all()


def seed_templates(db: Session):
    """Seed default notification templates.

    Args:
        db: Database session
    """
    default_templates = [
        {
            "template_name": "order_confirmation",
            "subject_template": "Order Confirmation - {{order_number}}",
            "body_template": """Dear {{customer_name}},

Thank you for your order! Your order {{order_number}} has been received and is being processed.

Order Details:
- From: {{origin_address}}
- To: {{destination_address}}

We will notify you once your order is shipped.

Best regards,
Logistics Team""",
            "channel": "email"
        },
        {
            "template_name": "order_status_update",
            "subject_template": "Order Status Update - {{order_number}}",
            "body_template": """Dear {{customer_name}},

Your order {{order_number}} status has been updated.

Previous Status: {{old_status}}
New Status: {{new_status}}

You can track your order using the order number above.

Best regards,
Logistics Team""",
            "channel": "email"
        },
        {
            "template_name": "shipment_created",
            "subject_template": "Shipment Created - {{tracking_number}}",
            "body_template": """Dear {{customer_name}},

Your order {{order_number}} has been shipped!

Tracking Number: {{tracking_number}}
Carrier: {{carrier}}
Estimated Delivery: {{estimated_delivery}}

You can track your shipment using the tracking number.

Best regards,
Logistics Team""",
            "channel": "email"
        },
        {
            "template_name": "shipment_tracking_update",
            "subject_template": "Shipment Update - {{tracking_number}}",
            "body_template": """Dear {{customer_name}},

Your shipment {{tracking_number}} has been updated.

Current Location: {{current_location}}
Estimated Delivery: {{estimated_delivery}}

Best regards,
Logistics Team""",
            "channel": "email"
        },
        {
            "template_name": "inventory_low_stock_alert",
            "subject_template": "Low Stock Alert - {{product_name}}",
            "body_template": """Alert: Low Stock

Product: {{product_name}}
SKU: {{sku}}
Current Quantity: {{current_quantity}}
Threshold: {{threshold}}

Please reorder inventory as soon as possible.

Logistics System""",
            "channel": "email"
        }
    ]

    for template_data in default_templates:
        existing = get_template_by_name(db, template_data["template_name"])
        if not existing:
            create_template(
                db,
                template_data["template_name"],
                template_data["subject_template"],
                template_data["body_template"],
                template_data["channel"]
            )
            logger.info("template_seeded", template_name=template_data["template_name"])
