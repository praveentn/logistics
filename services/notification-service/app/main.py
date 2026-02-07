"""Notification Service - Main FastAPI application."""

import time
import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import structlog

from app.database import init_db, get_db_status, SessionLocal
from app.api import notifications
from app.messaging.consumer import get_consumer, start_consumer
from app.services import notification_service

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

service_up = Gauge('service_up', 'Service health status')
service_up.set(1)

notifications_sent_total = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['channel', 'type']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("notification_service_starting")

    try:
        # Initialize database
        init_db()
        logger.info("database_initialized")

        # Seed notification templates
        db = SessionLocal()
        try:
            notification_service.seed_templates(db)
            logger.info("templates_seeded")
        finally:
            db.close()

        # Start RabbitMQ consumer in background
        consumer = await get_consumer()
        logger.info("messaging_consumer_initialized")

        # Start consuming in background task
        consumer_task = asyncio.create_task(start_consumer())
        logger.info("consumer_task_started")

        service_up.set(1)
        logger.info("notification_service_started")
    except Exception as e:
        logger.error("service_startup_failed", error=str(e))
        service_up.set(0)
        raise

    yield

    # Shutdown
    logger.info("notification_service_shutting_down")
    consumer = await get_consumer()
    await consumer.stop()
    service_up.set(0)


# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="Handles notifications for the logistics platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Record metrics for each HTTP request.

    Args:
        request: HTTP request
        call_next: Next middleware/endpoint

    Returns:
        HTTP response
    """
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response


# Logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log each HTTP request.

    Args:
        request: HTTP request
        call_next: Next middleware/endpoint

    Returns:
        HTTP response
    """
    start_time = time.time()

    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None
    )

    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_seconds=round(duration, 3)
    )

    return response


# Include routers
app.include_router(notifications.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes.

    Returns:
        Health status
    """
    db_status = get_db_status()
    consumer = await get_consumer()
    messaging_status = consumer.get_status()

    healthy = db_status == "healthy" and messaging_status == "healthy"

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "healthy" if healthy else "unhealthy",
            "service": "notification-service",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "messaging": messaging_status
        }
    )


# Readiness check endpoint
@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint.

    Returns:
        Readiness status
    """
    return {"status": "ready", "service": "notification-service"}


# Root endpoint
@app.get("/")
def root():
    """Root endpoint.

    Returns:
        Service information
    """
    return {
        "service": "notification-service",
        "version": "1.0.0",
        "status": "running"
    }


# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
