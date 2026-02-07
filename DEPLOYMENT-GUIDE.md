# Complete Logistics Platform - Deployment Guide

## 🎉 What's Been Implemented

All 6 microservices are now complete and ready to run!

### ✅ Services Implemented

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Order Service** | 8001 | Order management & CRUD operations | ✅ Complete |
| **Tracking Service** | 8002 | Shipment tracking & location updates | ✅ Complete |
| **Inventory Service** | 8003 | Warehouse & inventory management | ✅ Complete |
| **Notification Service** | 8004 | Event-driven notifications | ✅ Complete |
| **API Gateway** | 8000 | Request routing to all services | ✅ Complete |
| **Dashboard** | 8080 | Real-time monitoring UI | ✅ Complete |

### ✅ Infrastructure

| Component | Port | Purpose |
|-----------|------|---------|
| **PostgreSQL** | 5432 | 4 separate databases (orders, tracking, inventory, notifications) |
| **RabbitMQ** | 5672, 15672 | Event bus & management UI |
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3000 | Metrics visualization |

---

## 🚀 Quick Start - Deploy Everything

### Step 1: Stop Existing Services

```powershell
docker-compose down
```

### Step 2: Build All Services

This will take 5-10 minutes the first time:

```powershell
docker-compose build
```

### Step 3: Start All Services

```powershell
docker-compose up -d
```

### Step 4: Wait for Services to Start

```powershell
# Wait 30 seconds for all services to initialize
Start-Sleep -Seconds 30

# Check status
docker-compose ps
```

You should see all 11 containers running:
- ✅ logistics-postgres
- ✅ logistics-rabbitmq
- ✅ logistics-order-service
- ✅ logistics-tracking-service
- ✅ logistics-inventory-service
- ✅ logistics-notification-service
- ✅ logistics-api-gateway
- ✅ logistics-dashboard
- ✅ logistics-prometheus
- ✅ logistics-grafana

---

## 🔗 Access All Services

### Microservices APIs

| Service | URL | Documentation |
|---------|-----|---------------|
| **API Gateway** | http://localhost:8000 | http://localhost:8000/docs |
| Order Service | http://localhost:8001 | http://localhost:8001/docs |
| Tracking Service | http://localhost:8002 | http://localhost:8002/docs |
| Inventory Service | http://localhost:8003 | http://localhost:8003/docs |
| Notification Service | http://localhost:8004 | http://localhost:8004/docs |

### Dashboards & Monitoring

| Dashboard | URL | Credentials |
|-----------|-----|-------------|
| **Logistics Dashboard** | http://localhost:8080 | None required |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | None required |
| **RabbitMQ** | http://localhost:15672 | admin / admin_password_123 |

### Database

- **PostgreSQL**: localhost:5432
- **Username**: postgres
- **Password**: demo_password_123
- **Databases**: orders_db, tracking_db, inventory_db, notifications_db

---

## 🧪 Test the Complete Workflow

### 1. Seed Inventory Data

First, add some inventory items:

```powershell
# Create a warehouse
curl -X POST http://localhost:8000/api/v1/warehouses `
  -H "Content-Type: application/json" `
  -d '{
    "warehouse_code": "WH-001",
    "name": "Main Warehouse",
    "location": "New York, NY",
    "capacity": 10000
  }'

# Add inventory items
curl -X POST http://localhost:8003/api/v1/inventory `
  -H "Content-Type: application/json" `
  -d '{
    "warehouse_id": 1,
    "sku": "LAPTOP-001",
    "item_name": "Dell Laptop",
    "quantity": 100,
    "reorder_level": 10
  }'

curl -X POST http://localhost:8003/api/v1/inventory `
  -H "Content-Type: application/json" `
  -d '{
    "warehouse_id": 1,
    "sku": "MOUSE-001",
    "item_name": "Wireless Mouse",
    "quantity": 200,
    "reorder_level": 20
  }'
```

### 2. Create an Order (via API Gateway)

```powershell
curl -X POST http://localhost:8000/api/v1/orders `
  -H "Content-Type: application/json" `
  -d '{
    "customer_name": "John Doe",
    "customer_email": "john.doe@example.com",
    "origin_address": "123 Main St, New York, NY 10001",
    "destination_address": "456 Oak Ave, Los Angeles, CA 90001",
    "package_weight": 5.5,
    "package_dimensions": "30x20x15",
    "items": [
      {
        "item_name": "Dell Laptop",
        "quantity": 1,
        "sku": "LAPTOP-001"
      },
      {
        "item_name": "Wireless Mouse",
        "quantity": 2,
        "sku": "MOUSE-001"
      }
    ]
  }'
```

### 3. Verify the Workflow

**What Should Happen Automatically:**

1. ✅ **Order Created** in Order Service
2. ✅ **Inventory Reserved** in Inventory Service (via RabbitMQ event)
3. ✅ **Shipment Created** in Tracking Service (via RabbitMQ event)
4. ✅ **Notifications Sent**:
   - Order confirmation email
   - Shipment created notification

**Check Each Step:**

```powershell
# 1. Check order was created
curl http://localhost:8000/api/v1/orders | ConvertFrom-Json | ConvertTo-Json -Depth 10

# 2. Check inventory was reserved
curl http://localhost:8000/api/v1/inventory/check `
  -X POST `
  -H "Content-Type: application/json" `
  -d '{"items": [{"sku": "LAPTOP-001", "quantity": 1}]}'

# 3. Check shipment was created (replace ORDER_NUMBER)
curl "http://localhost:8000/api/v1/shipments/order/ORD-20260207..." | ConvertFrom-Json

# 4. Check notifications were sent
curl "http://localhost:8000/api/v1/notifications?page=1&page_size=10" | ConvertFrom-Json
```

### 4. Add a Tracking Event

```powershell
# Get the tracking number from the shipment response above, then:
curl -X POST "http://localhost:8000/api/v1/shipments/TRK-20260207.../events" `
  -H "Content-Type: application/json" `
  -d '{
    "location": "Chicago Distribution Center",
    "event_type": "in_transit",
    "description": "Package arrived at distribution center"
  }'
```

This will:
- ✅ Update shipment location
- ✅ Send tracking update notification

### 5. View the Dashboard

Open **http://localhost:8080** in your browser to see:

- 📊 Total orders, shipments, inventory
- 📈 Real-time statistics
- 🚦 Service health status
- 🔔 Notifications sent

---

## 📊 Monitor the System

### RabbitMQ Events

1. Open **http://localhost:15672** (admin/admin_password_123)
2. Go to **Exchanges** tab
3. Click on **logistics.events**
4. You should see:
   - `order.created` events
   - `order.status_changed` events
   - `shipment.created` events
   - `shipment.updated` events

### Prometheus Metrics

1. Open **http://localhost:9090**
2. Try these queries:
   ```promql
   # Total orders created
   orders_created_total

   # Total shipments created
   shipments_created_total

   # Total notifications sent
   notifications_sent_total

   # Service health
   service_up

   # HTTP requests across all services
   sum(http_requests_total) by (service)
   ```

### Grafana Dashboards

1. Open **http://localhost:3000** (admin/admin)
2. Go to **Dashboards** → **Browse**
3. Open **Logistics Overview**
4. You'll see:
   - HTTP request rates
   - Request latencies
   - Business metrics (orders, shipments)
   - Service health

---

## 🔄 Complete End-to-End Workflow

Here's what happens when you create an order:

```
1. User creates order via API Gateway
   ↓
2. API Gateway → Order Service
   ↓
3. Order Service:
   - Saves order to orders_db
   - Checks inventory via REST call
   - Publishes "order.created" event
   ↓
4. Inventory Service (listens to order.created):
   - Reserves inventory
   - Updates inventory_db
   ↓
5. Tracking Service (listens to order.created):
   - Creates shipment
   - Generates tracking number
   - Saves to tracking_db
   - Publishes "shipment.created" event
   ↓
6. Notification Service (listens to order.created & shipment.created):
   - Sends order confirmation
   - Sends shipment notification
   - Saves to notifications_db
   ↓
7. Dashboard displays updated statistics
```

---

## 🛠️ Useful Commands

### View Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f order-service
docker-compose logs -f tracking-service
docker-compose logs -f inventory-service
docker-compose logs -f notification-service
docker-compose logs -f api-gateway
docker-compose logs -f dashboard
```

### Restart a Service

```powershell
docker-compose restart order-service
```

### Rebuild and Restart

```powershell
docker-compose build order-service
docker-compose up -d order-service
```

### Check Service Health

```powershell
curl http://localhost:8000/health  # API Gateway (checks all services)
curl http://localhost:8001/health  # Order Service
curl http://localhost:8002/health  # Tracking Service
curl http://localhost:8003/health  # Inventory Service
curl http://localhost:8004/health  # Notification Service
curl http://localhost:8080/health  # Dashboard
```

### Database Access

```powershell
# Access PostgreSQL
docker-compose exec postgres psql -U postgres

# List databases
\l

# Connect to specific database
\c orders_db

# List tables
\dt

# Query orders
SELECT * FROM orders;
```

### Clean Slate

```powershell
# Stop and remove everything (including data)
docker-compose down -v

# Rebuild and start fresh
docker-compose build
docker-compose up -d
```

---

## 📈 Kubernetes Deployment

The Kubernetes manifests are ready in `k8s/base/`. To deploy to Kubernetes:

```bash
# Deploy namespace and infrastructure
kubectl apply -f k8s/base/namespace/
kubectl apply -f k8s/base/postgresql/
kubectl apply -f k8s/base/rabbitmq/

# Wait for infrastructure
kubectl wait --for=condition=ready pod -l app=postgresql -n logistics-demo --timeout=120s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n logistics-demo --timeout=120s

# Deploy services (manifests need to be created)
kubectl apply -f k8s/base/order-service/
# TODO: Create manifests for other services following order-service pattern
```

---

## 🎯 Success Criteria

Your deployment is successful when:

- ✅ All 11 containers are running (`docker-compose ps`)
- ✅ All health checks are passing (green/healthy status)
- ✅ You can create an order via API Gateway
- ✅ Shipment is auto-created for the order
- ✅ Inventory is reserved automatically
- ✅ Notifications are sent automatically
- ✅ Dashboard shows statistics
- ✅ RabbitMQ shows events being published
- ✅ Prometheus shows metrics
- ✅ Grafana displays dashboards

---

## 🐛 Troubleshooting

### Service Won't Start

```powershell
# Check logs
docker-compose logs <service-name>

# Check if port is already in use
netstat -ano | findstr :<port>

# Rebuild the service
docker-compose build <service-name>
docker-compose up -d <service-name>
```

### Database Issues

```powershell
# Recreate databases
docker-compose down postgres
docker-compose up -d postgres

# Wait for it to initialize
Start-Sleep -Seconds 15
```

### RabbitMQ Connection Issues

```powershell
# Restart RabbitMQ
docker-compose restart rabbitmq

# Check it's healthy
docker-compose exec rabbitmq rabbitmq-diagnostics ping
```

### Events Not Being Processed

1. Check RabbitMQ management UI (http://localhost:15672)
2. Look for queues - they should be consuming messages
3. Check service logs for errors
4. Verify services are connected to RabbitMQ

---

## 📚 Next Steps

1. **Explore APIs**: Open http://localhost:8000/docs and test all endpoints
2. **View Dashboard**: Open http://localhost:8080 for real-time monitoring
3. **Monitor Events**: Watch RabbitMQ at http://localhost:15672
4. **Check Metrics**: View Prometheus at http://localhost:9090
5. **Create Grafana Dashboards**: Customize at http://localhost:3000

---

**You now have a fully functional microservices logistics platform! 🎉**

All services are communicating via REST and RabbitMQ, data is being persisted to PostgreSQL, and everything is monitored with Prometheus and Grafana.
