# Dashboard Service - Quick Start Guide

## File Structure
```
dashboard/
├── app/
│   ├── __init__.py                 # Package init
│   ├── main.py                     # FastAPI application (209 lines)
│   ├── api/
│   │   ├── __init__.py            # API package init
│   │   └── stats.py               # Statistics endpoints (150 lines)
│   ├── services/
│   │   ├── __init__.py            # Services package init
│   │   └── service_client.py      # Backend service client (309 lines)
│   └── static/
│       ├── index.html             # Dashboard UI (141 lines)
│       ├── style.css              # Dashboard styles (308 lines)
│       └── dashboard.js           # Dashboard logic (236 lines)
├── Dockerfile                      # Docker configuration
├── requirements.txt                # Python dependencies
├── README.md                       # Full documentation
├── IMPLEMENTATION_SUMMARY.md       # Implementation details
└── QUICK_START.md                 # This file
```

## Quick Test (Local Development)

### 1. Install Dependencies
```bash
cd c:\Users\praveen\expts\logistics\services\dashboard
pip install -r requirements.txt
```

### 2. Run the Service
```bash
# Using Python directly
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Or using the main module
python app/main.py
```

### 3. Access Dashboard
- Open browser: http://localhost:8080
- API docs: http://localhost:8080/docs
- Health check: http://localhost:8080/health

## Quick Test (Docker)

### Build and Run
```bash
cd c:\Users\praveen\expts\logistics\services\dashboard

# Build image
docker build -t dashboard-service .

# Run container
docker run -p 8080:8080 \
  -e ORDER_SERVICE_URL=http://host.docker.internal:8001 \
  -e TRACKING_SERVICE_URL=http://host.docker.internal:8002 \
  -e INVENTORY_SERVICE_URL=http://host.docker.internal:8003 \
  -e NOTIFICATION_SERVICE_URL=http://host.docker.internal:8004 \
  dashboard-service
```

## API Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI (HTML page) |
| `/api/stats/overview` | GET | All statistics aggregated |
| `/api/stats/orders` | GET | Order statistics |
| `/api/stats/shipments` | GET | Shipment statistics |
| `/api/stats/inventory` | GET | Inventory statistics |
| `/api/stats/notifications` | GET | Notification statistics |
| `/api/stats/health` | GET | Service health status |
| `/health` | GET | Service health check |
| `/ready` | GET | Readiness probe |
| `/metrics` | GET | Prometheus metrics |
| `/docs` | GET | API documentation (Swagger) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ORDER_SERVICE_URL` | `http://localhost:8001` | Order Service URL |
| `TRACKING_SERVICE_URL` | `http://localhost:8002` | Tracking Service URL |
| `INVENTORY_SERVICE_URL` | `http://localhost:8003` | Inventory Service URL |
| `NOTIFICATION_SERVICE_URL` | `http://localhost:8004` | Notification Service URL |
| `LOG_LEVEL` | `INFO` | Logging level |

## Service Dependencies

The dashboard aggregates data from:
1. **Order Service** (port 8001) - Order statistics
2. **Tracking Service** (port 8002) - Shipment statistics
3. **Inventory Service** (port 8003) - Inventory statistics
4. **Notification Service** (port 8004) - Notification statistics

## Dashboard Features

### Overview Cards
- **Orders**: Total, Pending, Delivered
- **Shipments**: Total, Active (In Transit), Delivered
- **Inventory**: Total Items, Low Stock Alerts
- **Notifications**: Sent Today

### Service Health
- Real-time health status of all backend services
- Visual indicators (green/red/yellow)
- Overall system health status

### Auto-Refresh
- Dashboard refreshes automatically every 10 seconds
- Shows last update timestamp
- Graceful error handling

## Testing the Dashboard

### 1. Test Health Endpoint
```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "dashboard-service",
  "timestamp": "2024-02-07T10:30:00.000000"
}
```

### 2. Test Overview API
```bash
curl http://localhost:8080/api/stats/overview
```

### 3. Test Order Stats
```bash
curl http://localhost:8080/api/stats/orders
```

### 4. Access Dashboard UI
```bash
# Open in browser
start http://localhost:8080
```

## Common Issues

### Issue: Module not found errors
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Service unreachable errors
**Solution**: Ensure backend services are running
- Order Service on port 8001
- Tracking Service on port 8002
- Inventory Service on port 8003
- Notification Service on port 8004

### Issue: CORS errors
**Solution**: CORS is already enabled in main.py - check browser console

## Development

### Enable Hot Reload
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Check Logs
Logs are output in JSON format to stdout using structlog.

### View Metrics
```bash
curl http://localhost:8080/metrics
```

## Production Deployment

See `docker-compose.yml` in the project root for production deployment configuration.

## Support

For detailed documentation, see:
- `README.md` - Full service documentation
- `IMPLEMENTATION_SUMMARY.md` - Implementation details
- FastAPI docs at http://localhost:8080/docs
