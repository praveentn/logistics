# API Gateway Service

A lightweight FastAPI-based API Gateway for the logistics platform that routes requests to backend microservices.

## Features

- **Request Routing**: Routes incoming requests to appropriate backend services
- **Service Discovery**: Uses Kubernetes DNS or environment variables for service URLs
- **Request Proxying**: Forwards requests with headers, query params, and body using httpx
- **Health Checks**: Aggregated health status of all backend services
- **Retry Logic**: Automatic retry with exponential backoff for failed requests
- **CORS Support**: Configurable CORS middleware
- **Metrics**: Prometheus metrics for monitoring
- **Structured Logging**: JSON-formatted logs using structlog

## Routes

The gateway routes requests to the following services:

| Route Pattern | Backend Service | Port |
|--------------|-----------------|------|
| `/api/v1/orders/*` | Order Service | 8001 |
| `/api/v1/shipments/*` | Tracking Service | 8002 |
| `/api/v1/warehouses/*` | Inventory Service | 8003 |
| `/api/v1/inventory/*` | Inventory Service | 8003 |
| `/api/v1/notifications/*` | Notification Service | 8004 |
| `/api/v1/templates/*` | Notification Service | 8004 |

## Endpoints

- `GET /` - Root endpoint with service information
- `GET /health` - Health check endpoint (checks all backend services)
- `GET /metrics` - Prometheus metrics endpoint
- `{METHOD} /api/v1/*` - Proxied requests to backend services

## Configuration

Configuration is done via environment variables:

```env
# Service URLs
ORDER_SERVICE_URL=http://order-service:8001
TRACKING_SERVICE_URL=http://tracking-service:8002
INVENTORY_SERVICE_URL=http://inventory-service:8003
NOTIFICATION_SERVICE_URL=http://notification-service:8004

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Request settings
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_BACKOFF=0.5

# Logging
LOG_LEVEL=INFO
```

## Running Locally

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
```

### Running

```bash
# Development mode with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or run directly
python -m app.main
```

The gateway will be available at `http://localhost:8000`

## Running with Docker

### Build

```bash
docker build -t api-gateway:latest .
```

### Run

```bash
docker run -p 8000:8000 \
  -e ORDER_SERVICE_URL=http://order-service:8001 \
  -e TRACKING_SERVICE_URL=http://tracking-service:8002 \
  -e INVENTORY_SERVICE_URL=http://inventory-service:8003 \
  -e NOTIFICATION_SERVICE_URL=http://notification-service:8004 \
  api-gateway:latest
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Monitoring

### Metrics

Prometheus metrics are exposed at `/metrics`:

- `gateway_requests_total` - Total number of requests (labeled by service, method, status)
- `gateway_request_duration_seconds` - Request duration histogram (labeled by service, method)
- `gateway_backend_health_checks_total` - Backend health check counts (labeled by service, status)

### Health Checks

The `/health` endpoint returns the health status of the gateway and all backend services:

```json
{
  "gateway": "healthy",
  "overall_status": "healthy",
  "services": {
    "orders": {
      "status": "healthy",
      "response_time_ms": 15.2,
      "url": "http://order-service:8001"
    },
    "shipments": {
      "status": "healthy",
      "response_time_ms": 12.8,
      "url": "http://tracking-service:8002"
    }
  }
}
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│       API Gateway (Port 8000)       │
│  ┌──────────────────────────────┐   │
│  │   CORS Middleware            │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │   Request Routing            │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │   Retry Logic                │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │   Metrics & Logging          │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
       │
       ├─────────────┬──────────────┬──────────────┐
       ▼             ▼              ▼              ▼
┌─────────────┐ ┌──────────┐ ┌─────────────┐ ┌──────────────┐
│   Order     │ │ Tracking │ │ Inventory   │ │Notification  │
│  Service    │ │ Service  │ │  Service    │ │  Service     │
│  :8001      │ │  :8002   │ │   :8003     │ │   :8004      │
└─────────────┘ └──────────┘ └─────────────┘ └──────────────┘
```

## Error Handling

The gateway implements robust error handling:

1. **Connection Errors**: Automatically retries with exponential backoff
2. **Timeouts**: Retries up to MAX_RETRIES times
3. **Service Unavailable**: Returns 503 with error details
4. **All errors are logged** with structured logging for debugging

## Development

### Project Structure

```
api-gateway/
├── app/
│   ├── __init__.py       # Package initialization
│   ├── main.py           # FastAPI application and lifespan
│   ├── config.py         # Configuration management
│   └── routes.py         # Request routing and proxying
├── tests/                # Test directory
├── Dockerfile            # Docker build configuration
├── requirements.txt      # Python dependencies
├── .dockerignore         # Docker ignore rules
├── .env.example          # Example environment variables
└── README.md             # This file
```

## License

MIT
