# Dashboard Service

The Dashboard Service provides a web-based UI and API endpoints for aggregating statistics from all backend services in the logistics platform.

## Features

- **Real-time Dashboard UI**: Simple, responsive HTML/CSS/JavaScript dashboard
- **Auto-refresh**: Dashboard auto-refreshes every 10 seconds
- **Service Aggregation**: Aggregates data from Order, Tracking, Inventory, and Notification services
- **Service Health Monitoring**: Displays health status of all backend services
- **Statistics API**: RESTful API endpoints for retrieving aggregated statistics

## Architecture

### Technology Stack
- **Framework**: FastAPI (Python)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **HTTP Client**: httpx (for async service calls)
- **Monitoring**: Prometheus metrics
- **Logging**: structlog

### Port
- **8080**: HTTP API and web UI

## API Endpoints

### Statistics Endpoints

#### GET /api/stats/overview
Aggregates statistics from all services.

**Response:**
```json
{
  "orders": {
    "total_orders": 150,
    "pending_orders": 25,
    "delivered_orders": 100,
    "status": "success"
  },
  "shipments": {
    "total_shipments": 140,
    "active_shipments": 30,
    "delivered_shipments": 95,
    "status": "success"
  },
  "inventory": {
    "total_items": 500,
    "low_stock_items": 12,
    "status": "success"
  },
  "notifications": {
    "notifications_sent_today": 45,
    "status": "success"
  },
  "service_health": {
    "services": [...],
    "all_healthy": true
  }
}
```

#### GET /api/stats/orders
Get order statistics from the Order Service.

**Response:**
```json
{
  "total_orders": 150,
  "pending_orders": 25,
  "delivered_orders": 100,
  "status": "success"
}
```

#### GET /api/stats/shipments
Get shipment statistics from the Tracking Service.

**Response:**
```json
{
  "total_shipments": 140,
  "active_shipments": 30,
  "delivered_shipments": 95,
  "status": "success"
}
```

#### GET /api/stats/inventory
Get inventory statistics from the Inventory Service.

**Response:**
```json
{
  "total_items": 500,
  "low_stock_items": 12,
  "status": "success"
}
```

#### GET /api/stats/notifications
Get notification statistics from the Notification Service.

**Response:**
```json
{
  "notifications_sent_today": 45,
  "status": "success"
}
```

#### GET /api/stats/health
Get health status of all backend services.

**Response:**
```json
{
  "services": [
    {
      "service": "order-service",
      "status": "healthy",
      "data": {...}
    },
    {
      "service": "tracking-service",
      "status": "healthy",
      "data": {...}
    }
  ],
  "all_healthy": true
}
```

### System Endpoints

#### GET /
Serves the dashboard HTML page.

#### GET /health
Health check endpoint for Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "service": "dashboard-service",
  "timestamp": "2024-02-07T10:30:00.000000"
}
```

#### GET /ready
Readiness check endpoint.

**Response:**
```json
{
  "status": "ready",
  "service": "dashboard-service"
}
```

#### GET /metrics
Prometheus metrics endpoint.

## Dashboard UI

The dashboard displays:

1. **Orders Card**
   - Total orders
   - Pending orders
   - Delivered orders
   - Service status

2. **Shipments Card**
   - Total shipments
   - Active (in transit) shipments
   - Delivered shipments
   - Service status

3. **Inventory Card**
   - Total inventory items
   - Low stock alerts
   - Service status

4. **Notifications Card**
   - Notifications sent today
   - Service status

5. **Service Health Section**
   - Health status of each backend service
   - Overall system status

## Configuration

### Environment Variables

- `ORDER_SERVICE_URL`: Order Service URL (default: `http://localhost:8001`)
- `TRACKING_SERVICE_URL`: Tracking Service URL (default: `http://localhost:8002`)
- `INVENTORY_SERVICE_URL`: Inventory Service URL (default: `http://localhost:8003`)
- `NOTIFICATION_SERVICE_URL`: Notification Service URL (default: `http://localhost:8004`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Running the Service

### Using Python directly

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Using Docker

```bash
# Build the image
docker build -t dashboard-service .

# Run the container
docker run -p 8080:8080 \
  -e ORDER_SERVICE_URL=http://order-service:8001 \
  -e TRACKING_SERVICE_URL=http://tracking-service:8002 \
  -e INVENTORY_SERVICE_URL=http://inventory-service:8003 \
  -e NOTIFICATION_SERVICE_URL=http://notification-service:8004 \
  dashboard-service
```

### Using Docker Compose

See the main `docker-compose.yml` in the project root.

## Development

### Project Structure

```
dashboard/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── stats.py            # Statistics API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── service_client.py   # Backend service client
│   └── static/
│       ├── index.html          # Dashboard UI
│       ├── style.css           # Dashboard styles
│       └── dashboard.js        # Dashboard JavaScript
├── Dockerfile
├── requirements.txt
└── README.md
```

### Service Client

The `service_client.py` module provides functions to:
- Call backend service APIs
- Aggregate data from multiple services
- Handle service failures gracefully
- Return consistent error responses

### Error Handling

- All service calls have a 5-second timeout
- Failed service calls return error status with zero values
- Dashboard displays error states for unreachable services
- Graceful degradation when services are unavailable

## Monitoring

### Prometheus Metrics

The service exposes standard Prometheus metrics at `/metrics`:
- `http_requests_total`: Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds`: HTTP request duration histogram
- `service_up`: Service health status gauge

## Testing

Access the dashboard at: `http://localhost:8080`

The dashboard will automatically refresh every 10 seconds to display the latest statistics.

## Notes

- No database required - this is a stateless aggregation service
- All data is fetched in real-time from backend services
- Dashboard uses vanilla JavaScript (no frameworks) for simplicity
- Responsive design works on desktop and mobile devices
