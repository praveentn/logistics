"""Inventory Service - Main FastAPI application."""

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

from app.database import init_db, get_db_status
from app.api import inventory
from app.messaging.consumer import get_inventory_consumer, start_consumer

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("inventory_service_starting")

    try:
        # Initialize database
        init_db()
        logger.info("database_initialized")

        # Connect to RabbitMQ consumer
        consumer = await get_inventory_consumer()
        logger.info("messaging_consumer_initialized")

        # Start consumer in background task
        consumer_task = asyncio.create_task(start_consumer())
        logger.info("consumer_task_started")

        service_up.set(1)
        logger.info("inventory_service_started")
    except Exception as e:
        logger.error("service_startup_failed", error=str(e))
        service_up.set(0)
        raise

    yield

    # Shutdown
    logger.info("inventory_service_shutting_down")

    # Cancel consumer task
    if 'consumer_task' in locals():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    # Close consumer connection
    if 'consumer' in locals():
        await consumer.close()

    service_up.set(0)
    logger.info("inventory_service_shutdown_complete")


# Create FastAPI app
app = FastAPI(
    title="Inventory Service",
    description="Manages warehouse inventory and stock levels for the logistics platform",
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
app.include_router(inventory.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes.

    Returns:
        Health status
    """
    db_status = get_db_status()

    try:
        consumer = await get_inventory_consumer()
        messaging_status = consumer.get_status()
    except Exception as e:
        logger.error("health_check_messaging_error", error=str(e))
        messaging_status = "unhealthy"

    healthy = db_status == "healthy" and messaging_status == "healthy"

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "healthy" if healthy else "unhealthy",
            "service": "inventory-service",
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
    return {"status": "ready", "service": "inventory-service"}


# Root endpoint
@app.get("/")
def root():
    """Root endpoint.

    Returns:
        Service information
    """
    return {
        "service": "inventory-service",
        "version": "1.0.0",
        "status": "running"
    }


# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
