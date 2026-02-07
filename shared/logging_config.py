"""Structured logging configuration for all services.

This module configures structured JSON logging using structlog,
making logs easy to parse and aggregate in Kubernetes environments.
"""

import logging
import sys
from typing import Any
import structlog
from structlog.types import EventDict, Processor


def add_service_name(service_name: str) -> Processor:
    """Add service name to all log entries.

    Args:
        service_name: Name of the service

    Returns:
        Structlog processor function
    """
    def processor(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
        event_dict["service"] = service_name
        return event_dict
    return processor


def configure_logging(
    service_name: str,
    log_level: str = "INFO",
    json_logs: bool = True
) -> None:
    """Configure structured logging for a service.

    Args:
        service_name: Name of the service (e.g., 'order-service')
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Output logs as JSON (True) or human-readable (False)
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )

    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        add_service_name(service_name),
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add appropriate renderer
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Get logger and log initialization
    logger = structlog.get_logger()
    logger.info(
        "logging_configured",
        service=service_name,
        log_level=log_level,
        json_logs=json_logs
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Optional logger name (typically module name)

    Returns:
        Configured structlog logger

    Example:
        logger = get_logger(__name__)
        logger.info("order_created", order_id=123, customer="John")
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


# Context managers for request tracking
class LogContext:
    """Context manager for adding context to logs."""

    def __init__(self, **kwargs):
        """Initialize log context.

        Args:
            **kwargs: Key-value pairs to add to log context
        """
        self.context = kwargs

    def __enter__(self):
        """Enter context and bind variables."""
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and clear variables."""
        structlog.contextvars.clear_contextvars()


def log_request_id(request_id: str):
    """Add request ID to log context.

    Args:
        request_id: Unique request identifier

    Returns:
        LogContext instance
    """
    return LogContext(request_id=request_id)
