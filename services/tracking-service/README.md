# Tracking Service

The Tracking Service handles shipment tracking for the logistics platform. It manages shipment records, tracking events, and automatically creates shipments when new orders are placed.

## Features

- **Shipment Management**: Create and track shipments with unique tracking numbers
- **Real-time Event Tracking**: Record location updates and status changes
- **Order Integration**: Automatically creates shipments when orders are created
- **Event Publishing**: Publishes tracking events to the messaging system
- **RESTful API**: Complete API for managing shipments and tracking events
- **Prometheus Metrics**: Built-in metrics for monitoring
- **Health Checks**: Kubernetes-ready health and readiness endpoints

## Database Models

### Shipment
- `tracking_number` (unique): Unique identifier for the shipment
- `order_number`: Associated order number
- `carrier`: Shipping carrier name
- `current_location`: Current location of the shipment
- `status`: Current status (in_transit, out_for_delivery, delivered)
- `created_at`: Timestamp when shipment was created
- `updated_at`: Timestamp of last update

### TrackingEvent
- `shipment_id` (FK): Foreign key to shipment
- `location`: Location where event occurred
- `event_type`: Type of tracking event
- `description`: Event description
- `timestamp`: When the event occurred

## API Endpoints

### POST /api/v1/shipments
Create a new shipment.

**Request Body:**
```json
{
  "order_number": "ORD-20260207123456",
  "carrier": "FedEx",
  "current_location": "Warehouse A"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "tracking_number": "TRK-20260207123456",
  "order_number": "ORD-20260207123456",
  "carrier": "FedEx",
  "current_location": "Warehouse A",
  "status": "in_transit",
  "created_at": "2026-02-07T12:34:56Z",
  "updated_at": "2026-02-07T12:34:56Z",
  "events": []
}
```

### GET /api/v1/shipments
List all shipments with pagination.

**Query Parameters:**
- `page` (default: 1): Page number
- `page_size` (default: 10, max: 100): Items per page
- `status` (optional): Filter by status

**Response:** `200 OK`
```json
{
  "shipments": [...],
  "total": 100,
  "page": 1,
  "page_size": 10
}
```

### GET /api/v1/shipments/{tracking_number}
Get shipment details by tracking number.

**Response:** `200 OK`
```json
{
  "id": 1,
  "tracking_number": "TRK-20260207123456",
  "order_number": "ORD-20260207123456",
  "carrier": "FedEx",
  "current_location": "Distribution Center",
  "status": "in_transit",
  "created_at": "2026-02-07T12:34:56Z",
  "updated_at": "2026-02-07T13:00:00Z",
  "events": [
    {
      "id": 1,
      "shipment_id": 1,
      "location": "Distribution Center",
      "event_type": "arrived",
      "description": "Package arrived at distribution center",
      "timestamp": "2026-02-07T13:00:00Z"
    }
  ]
}
```

### POST /api/v1/shipments/{tracking_number}/events
Add a tracking event to a shipment.

**Request Body:**
```json
{
  "location": "Distribution Center",
  "event_type": "arrived",
  "description": "Package arrived at distribution center"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "shipment_id": 1,
  "location": "Distribution Center",
  "event_type": "arrived",
  "description": "Package arrived at distribution center",
  "timestamp": "2026-02-07T13:00:00Z"
}
```

### GET /api/v1/shipments/order/{order_number}
Get shipment by order number.

**Response:** `200 OK` (same as GET by tracking number)

## Message Consumer

The service consumes the following events:

### order.created
Automatically creates a shipment when a new order is created.

**Event Payload:**
```json
{
  "order_number": "ORD-20260207123456",
  "origin_address": "Warehouse A",
  "destination_address": "123 Main St",
  "_timestamp": "2026-02-07T12:34:56Z",
  "_routing_key": "order.created"
}
```

**Action:** Creates a new shipment with default carrier "Standard Carrier"

## Message Publisher

The service publishes the following events:

### shipment.created
Published when a new shipment is created.

**Event Payload:**
```json
{
  "tracking_number": "TRK-20260207123456",
  "order_number": "ORD-20260207123456",
  "carrier": "FedEx",
  "status": "in_transit",
  "current_location": "Warehouse A",
  "_timestamp": "2026-02-07T12:34:56Z",
  "_routing_key": "shipment.created"
}
```

### tracking.event_added
Published when a tracking event is added.

**Event Payload:**
```json
{
  "tracking_number": "TRK-20260207123456",
  "order_number": "ORD-20260207123456",
  "event_type": "arrived",
  "location": "Distribution Center",
  "description": "Package arrived at distribution center",
  "timestamp": "2026-02-07T13:00:00Z",
  "_timestamp": "2026-02-07T13:00:00Z",
  "_routing_key": "tracking.event_added"
}
```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:demo_password_123@postgresql:5432/tracking_db`)
- `RABBITMQ_URL`: RabbitMQ connection string (default: `amqp://admin:admin_password_123@rabbitmq:5672/`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### Port

The service runs on port **8002**.

## Health Endpoints

### GET /health
Health check endpoint that verifies database and messaging connectivity.

**Response:** `200 OK` or `503 Service Unavailable`
```json
{
  "status": "healthy",
  "service": "tracking-service",
  "timestamp": "2026-02-07T12:34:56Z",
  "database": "healthy",
  "messaging": "healthy"
}
```

### GET /ready
Readiness check endpoint.

**Response:** `200 OK`
```json
{
  "status": "ready",
  "service": "tracking-service"
}
```

### GET /metrics
Prometheus metrics endpoint.

## Running the Service

### Using Docker

```bash
docker build -t tracking-service .
docker run -p 8002:8002 \
  -e DATABASE_URL=postgresql://postgres:demo_password_123@postgresql:5432/tracking_db \
  -e RABBITMQ_URL=amqp://admin:admin_password_123@rabbitmq:5672/ \
  tracking-service
```

### Using Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## Project Structure

```
tracking-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Database models
│   ├── schemas.py              # Pydantic schemas
│   ├── database.py             # Database configuration
│   ├── api/
│   │   ├── __init__.py
│   │   └── tracking.py         # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── tracking_service.py # Business logic
│   └── messaging/
│       ├── __init__.py
│       ├── consumer.py         # RabbitMQ consumer
│       └── publisher.py        # RabbitMQ publisher
├── Dockerfile
├── requirements.txt
└── README.md
```

## Dependencies

- FastAPI 0.104.1
- Uvicorn 0.24.0
- SQLAlchemy 2.0.23
- PostgreSQL (psycopg2-binary 2.9.9)
- Pydantic 2.5.0
- Prometheus Client 0.19.0
- Structlog 23.2.0
- aio-pika 9.3.1 (RabbitMQ client)
- httpx 0.25.2

## Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `http_requests_total`: Total number of HTTP requests
- `http_request_duration_seconds`: HTTP request duration histogram
- `service_up`: Service health status gauge

## Logging

The service uses structured logging (JSON format) with the following key events:

- `tracking_service_starting`: Service startup
- `database_initialized`: Database tables created
- `messaging_publisher_initialized`: RabbitMQ publisher connected
- `messaging_consumer_started`: RabbitMQ consumer started
- `shipment_created`: New shipment created
- `tracking_event_created`: New tracking event added
- `shipment_auto_created`: Shipment auto-created from order event
- `event_published`: Event published to RabbitMQ
- `message_received`: Message received from RabbitMQ

## Error Handling

The service includes comprehensive error handling:

- Invalid tracking numbers return `404 Not Found`
- Database errors return `500 Internal Server Error`
- Message processing errors are logged but don't crash the consumer
- Health checks report degraded status when dependencies are unavailable
