"""Configuration module for the API Gateway."""

import os
from typing import List


class Settings:
    """Application settings."""

    VERSION: str = "0.1.0"

    # Service URLs - using Kubernetes DNS or environment variables
    ORDER_SERVICE_URL: str = os.getenv(
        "ORDER_SERVICE_URL",
        "http://order-service:8001"
    )
    TRACKING_SERVICE_URL: str = os.getenv(
        "TRACKING_SERVICE_URL",
        "http://tracking-service:8002"
    )
    INVENTORY_SERVICE_URL: str = os.getenv(
        "INVENTORY_SERVICE_URL",
        "http://inventory-service:8003"
    )
    NOTIFICATION_SERVICE_URL: str = os.getenv(
        "NOTIFICATION_SERVICE_URL",
        "http://notification-service:8004"
    )

    # CORS settings
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")

    # Request timeout settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

    # Retry settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF: float = float(os.getenv("RETRY_BACKOFF", "0.5"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
