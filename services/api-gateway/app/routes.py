"""Routes module for the API Gateway."""

import time
import httpx
import structlog
from typing import Optional
from fastapi import APIRouter, Request, Response, HTTPException
from prometheus_client import Counter, Histogram

from app.config import settings

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'gateway_requests_total',
    'Total number of requests through the gateway',
    ['service', 'method', 'status']
)

REQUEST_DURATION = Histogram(
    'gateway_request_duration_seconds',
    'Request duration in seconds',
    ['service', 'method']
)

BACKEND_HEALTH = Counter(
    'gateway_backend_health_checks_total',
    'Total number of backend health checks',
    ['service', 'status']
)

router = APIRouter()

# Global HTTP client
http_client: Optional[httpx.AsyncClient] = None


async def startup_http_client():
    """Initialize the HTTP client on startup."""
    global http_client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.REQUEST_TIMEOUT),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
    )
    logger.info("HTTP client initialized")


async def shutdown_http_client():
    """Close the HTTP client on shutdown."""
    global http_client
    if http_client:
        await http_client.aclose()
        logger.info("HTTP client closed")


# Service URL mappings
SERVICE_URLS = {
    "orders": settings.ORDER_SERVICE_URL,
    "shipments": settings.TRACKING_SERVICE_URL,
    "warehouses": settings.INVENTORY_SERVICE_URL,
    "inventory": settings.INVENTORY_SERVICE_URL,
    "notifications": settings.NOTIFICATION_SERVICE_URL,
    "templates": settings.NOTIFICATION_SERVICE_URL,
}


async def proxy_request(
    request: Request,
    service_name: str,
    service_url: str,
    path: str
) -> Response:
    """
    Proxy a request to a backend service with retry logic.

    Args:
        request: The incoming FastAPI request
        service_name: Name of the service for logging/metrics
        service_url: Base URL of the backend service
        path: Path to append to the service URL

    Returns:
        Response from the backend service
    """
    start_time = time.time()

    # Build the target URL
    target_url = f"{service_url}{path}"

    # Get request body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()

    # Prepare headers (exclude host header)
    headers = dict(request.headers)
    headers.pop("host", None)

    # Log the request
    logger.info(
        "Proxying request",
        service=service_name,
        method=request.method,
        path=path,
        target_url=target_url,
        query_params=str(request.query_params)
    )

    # Retry logic
    last_exception = None
    for attempt in range(settings.MAX_RETRIES):
        try:
            # Make the request to the backend service
            response = await http_client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                headers=headers,
                content=body
            )

            # Record metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(
                service=service_name,
                method=request.method,
                status=response.status_code
            ).inc()
            REQUEST_DURATION.labels(
                service=service_name,
                method=request.method
            ).observe(duration)

            # Log the response
            logger.info(
                "Request completed",
                service=service_name,
                method=request.method,
                path=path,
                status_code=response.status_code,
                duration=f"{duration:.3f}s",
                attempt=attempt + 1
            )

            # Return the response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except httpx.TimeoutException as e:
            last_exception = e
            logger.warning(
                "Request timeout",
                service=service_name,
                method=request.method,
                path=path,
                attempt=attempt + 1,
                max_retries=settings.MAX_RETRIES
            )
            if attempt < settings.MAX_RETRIES - 1:
                await asyncio.sleep(settings.RETRY_BACKOFF * (attempt + 1))
                continue

        except httpx.ConnectError as e:
            last_exception = e
            logger.error(
                "Connection error",
                service=service_name,
                method=request.method,
                path=path,
                attempt=attempt + 1,
                error=str(e)
            )
            if attempt < settings.MAX_RETRIES - 1:
                await asyncio.sleep(settings.RETRY_BACKOFF * (attempt + 1))
                continue

        except Exception as e:
            last_exception = e
            logger.error(
                "Unexpected error",
                service=service_name,
                method=request.method,
                path=path,
                attempt=attempt + 1,
                error=str(e)
            )
            break

    # All retries failed
    REQUEST_COUNT.labels(
        service=service_name,
        method=request.method,
        status=503
    ).inc()

    logger.error(
        "Request failed after retries",
        service=service_name,
        method=request.method,
        path=path,
        max_retries=settings.MAX_RETRIES,
        error=str(last_exception)
    )

    raise HTTPException(
        status_code=503,
        detail=f"Service {service_name} unavailable: {str(last_exception)}"
    )


# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint that verifies the gateway and all backend services.

    Returns:
        Aggregated health status of all services
    """
    health_status = {
        "gateway": "healthy",
        "services": {}
    }

    all_healthy = True

    # Check each backend service
    for service_name, service_url in SERVICE_URLS.items():
        try:
            response = await http_client.get(
                f"{service_url}/health",
                timeout=5.0
            )

            if response.status_code == 200:
                health_status["services"][service_name] = {
                    "status": "healthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
                BACKEND_HEALTH.labels(service=service_name, status="healthy").inc()
            else:
                health_status["services"][service_name] = {
                    "status": "unhealthy",
                    "status_code": response.status_code
                }
                BACKEND_HEALTH.labels(service=service_name, status="unhealthy").inc()
                all_healthy = False

        except Exception as e:
            health_status["services"][service_name] = {
                "status": "unreachable",
                "error": str(e)
            }
            BACKEND_HEALTH.labels(service=service_name, status="unreachable").inc()
            all_healthy = False

    # Remove duplicate service names (some services handle multiple routes)
    unique_services = {}
    for service_name, service_url in SERVICE_URLS.items():
        if service_url not in [v.get("url") for v in unique_services.values()]:
            unique_services[service_name] = health_status["services"].get(service_name, {})
            unique_services[service_name]["url"] = service_url

    health_status["services"] = unique_services
    health_status["overall_status"] = "healthy" if all_healthy else "degraded"

    return health_status


# Route proxying endpoints
@router.api_route("/api/v1/orders", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_orders_base(request: Request):
    """Proxy requests to the Order Service (base path)."""
    return await proxy_request(
        request,
        "orders",
        settings.ORDER_SERVICE_URL,
        "/api/v1/orders"
    )


@router.api_route("/api/v1/orders/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_orders(request: Request, path: str):
    """Proxy requests to the Order Service."""
    return await proxy_request(
        request,
        "orders",
        settings.ORDER_SERVICE_URL,
        f"/api/v1/orders/{path}"
    )


@router.api_route("/api/v1/shipments", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_shipments_base(request: Request):
    """Proxy requests to the Tracking Service (base path)."""
    return await proxy_request(
        request,
        "shipments",
        settings.TRACKING_SERVICE_URL,
        "/api/v1/shipments"
    )


@router.api_route("/api/v1/shipments/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_shipments(request: Request, path: str):
    """Proxy requests to the Tracking Service."""
    return await proxy_request(
        request,
        "shipments",
        settings.TRACKING_SERVICE_URL,
        f"/api/v1/shipments/{path}"
    )


@router.api_route("/api/v1/warehouses", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_warehouses_base(request: Request):
    """Proxy requests to the Inventory Service (warehouses base path)."""
    return await proxy_request(
        request,
        "warehouses",
        settings.INVENTORY_SERVICE_URL,
        "/api/v1/warehouses"
    )


@router.api_route("/api/v1/warehouses/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_warehouses(request: Request, path: str):
    """Proxy requests to the Inventory Service (warehouses)."""
    return await proxy_request(
        request,
        "warehouses",
        settings.INVENTORY_SERVICE_URL,
        f"/api/v1/warehouses/{path}"
    )


@router.api_route("/api/v1/inventory", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_inventory_base(request: Request):
    """Proxy requests to the Inventory Service (inventory base path)."""
    return await proxy_request(
        request,
        "inventory",
        settings.INVENTORY_SERVICE_URL,
        "/api/v1/inventory"
    )


@router.api_route("/api/v1/inventory/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_inventory(request: Request, path: str):
    """Proxy requests to the Inventory Service (inventory)."""
    return await proxy_request(
        request,
        "inventory",
        settings.INVENTORY_SERVICE_URL,
        f"/api/v1/inventory/{path}"
    )


@router.api_route("/api/v1/notifications", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_notifications_base(request: Request):
    """Proxy requests to the Notification Service (notifications base path)."""
    return await proxy_request(
        request,
        "notifications",
        settings.NOTIFICATION_SERVICE_URL,
        "/api/v1/notifications"
    )


@router.api_route("/api/v1/notifications/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_notifications(request: Request, path: str):
    """Proxy requests to the Notification Service (notifications)."""
    return await proxy_request(
        request,
        "notifications",
        settings.NOTIFICATION_SERVICE_URL,
        f"/api/v1/notifications/{path}"
    )


@router.api_route("/api/v1/templates", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_templates_base(request: Request):
    """Proxy requests to the Notification Service (templates base path)."""
    return await proxy_request(
        request,
        "templates",
        settings.NOTIFICATION_SERVICE_URL,
        "/api/v1/templates"
    )


@router.api_route("/api/v1/templates/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_templates(request: Request, path: str):
    """Proxy requests to the Notification Service (templates)."""
    return await proxy_request(
        request,
        "templates",
        settings.NOTIFICATION_SERVICE_URL,
        f"/api/v1/templates/{path}"
    )


# Import asyncio for sleep in retry logic
import asyncio
