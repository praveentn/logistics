# Quick Start Guide for Windows

## 🚀 Getting Started

### Step 1: Rebuild Order Service

The order service needs to be rebuilt with the fixed dependencies:

```powershell
# Stop all services
docker-compose down

# Rebuild order service
docker-compose build order-service

# Start all services
docker-compose up -d
```

### Step 2: Verify Services Are Running

```powershell
docker-compose ps
```

You should see all 5 services running:
- ✅ logistics-postgres (healthy)
- ✅ logistics-rabbitmq (healthy)
- ✅ logistics-order-service (healthy)
- ✅ logistics-prometheus
- ✅ logistics-grafana

### Step 3: Test the Order Service

**Option A: Using PowerShell Script**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-workflow.ps1
```

**Option B: Using curl (if installed)**
```bash
# Test health
curl http://localhost:8001/health

# Create an order
curl -X POST http://localhost:8001/api/v1/orders ^
  -H "Content-Type: application/json" ^
  -d "{\"customer_name\":\"John Doe\",\"customer_email\":\"john@example.com\",\"origin_address\":\"123 Main St\",\"destination_address\":\"456 Oak Ave\",\"package_weight\":5.5,\"items\":[{\"item_name\":\"Laptop\",\"quantity\":1,\"sku\":\"LAPTOP-001\"}]}"
```

**Option C: Using Web Browser**
Open http://localhost:8001/docs for interactive API documentation (Swagger UI)

## 📊 Accessing Services

### Order Service API
- **URL**: http://localhost:8001/docs
- **Description**: Interactive API documentation (Swagger UI)
- **Try it**: Create, list, and manage orders

### RabbitMQ Management
- **URL**: http://localhost:15672
- **Credentials**:
  - Username: `admin`
  - Password: `admin_password_123`
- **What to check**:
  - Queues → Should see event queues
  - Exchanges → Look for `logistics.events`
  - Overview → Message rates

### Prometheus
- **URL**: http://localhost:9090
- **Description**: Metrics database
- **Try these queries**:
  ```promql
  # Total HTTP requests
  http_requests_total

  # Request rate over 5 minutes
  rate(http_requests_total[5m])

  # Orders created
  orders_created_total

  # Service status
  service_up
  ```

### Grafana
- **URL**: http://localhost:3000
- **Credentials**:
  - Username: `admin`
  - Password: `admin`
- **Dashboard**:
  - After login, go to **Dashboards** → **Browse**
  - You should see "Logistics Overview" dashboard
  - If not, wait 10 seconds and refresh (auto-provisioning takes a moment)

### PostgreSQL
- **Host**: localhost
- **Port**: 5432
- **Username**: postgres
- **Password**: demo_password_123
- **Databases**: orders_db, tracking_db, inventory_db, notifications_db

**Connect using psql** (if installed):
```bash
psql -h localhost -p 5432 -U postgres -d orders_db
```

**Connect using DBeaver/pgAdmin**:
- Host: localhost
- Port: 5432
- Database: orders_db
- Username: postgres
- Password: demo_password_123

## 🎯 What About the Dashboard?

The **Dashboard service** (monitoring UI on port 8080) is **not implemented yet** - it's on the TODO list.

Currently available:
- ✅ **Grafana** (http://localhost:3000) - Pre-configured metrics dashboard
- ✅ **Prometheus** (http://localhost:9090) - Raw metrics
- ✅ **RabbitMQ UI** (http://localhost:15672) - Message broker stats
- ✅ **Swagger UI** (http://localhost:8001/docs) - API testing

The Grafana dashboard shows:
- HTTP request rates
- Request latency (p50, p95)
- Total orders created
- Service health status
- Orders by status
- HTTP request summary table

## 🧪 Testing Workflow

### 1. Create an Order

Open http://localhost:8001/docs and:
1. Expand `POST /api/v1/orders`
2. Click "Try it out"
3. Use this JSON:

```json
{
  "customer_name": "Jane Smith",
  "customer_email": "jane@example.com",
  "origin_address": "789 Pine Rd, Seattle, WA",
  "destination_address": "321 Elm St, Austin, TX",
  "package_weight": 3.2,
  "package_dimensions": "25x15x10",
  "items": [
    {
      "item_name": "Book",
      "quantity": 3,
      "sku": "BOOK-001"
    },
    {
      "item_name": "Pen",
      "quantity": 5,
      "sku": "PEN-001"
    }
  ]
}
```

4. Click "Execute"
5. Copy the `order_number` from the response

### 2. Check RabbitMQ

1. Go to http://localhost:15672
2. Login with admin/admin_password_123
3. Click **Exchanges** tab
4. Find `logistics.events`
5. You should see it published messages

### 3. View Metrics in Prometheus

1. Go to http://localhost:9090
2. In the query box, type: `orders_created_total`
3. Click "Execute"
4. You should see the counter increase

### 4. View Dashboard in Grafana

1. Go to http://localhost:3000
2. Login with admin/admin
3. Click "Dashboards" → "Browse"
4. Open "Logistics Overview"
5. You should see:
   - Request rate graph
   - Request duration graph
   - Total orders stat
   - Service status
   - Orders by status

### 5. Query PostgreSQL

Using any PostgreSQL client:

```sql
-- Connect to orders_db
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;

-- View order items
SELECT o.order_number, o.customer_name, oi.item_name, oi.quantity
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
ORDER BY o.created_at DESC;

-- Count orders by status
SELECT status, COUNT(*) as count
FROM orders
GROUP BY status;
```

## 🐛 Troubleshooting

### Order Service Not Running

```powershell
# Check logs
docker-compose logs order-service

# Rebuild and restart
docker-compose down
docker-compose build order-service
docker-compose up -d order-service
```

### Can't Connect to PostgreSQL

PostgreSQL **IS** running on localhost:5432. You need a PostgreSQL client:
- **psql** (command line)
- **DBeaver** (GUI - free)
- **pgAdmin** (GUI - free)
- **Azure Data Studio** with PostgreSQL extension

```powershell
# Test with Docker
docker-compose exec postgres psql -U postgres -c "SELECT version();"
```

### Grafana Dashboard Not Showing

1. Wait 10-20 seconds after startup (provisioning takes time)
2. Refresh the page
3. Check if datasource is configured:
   - Go to **Configuration** → **Data Sources**
   - Should see "Prometheus" configured
4. Manually import dashboard:
   - Click **+** → **Import**
   - Upload: `monitoring/grafana/dashboards/logistics-overview.json`

### No Data in Grafana

Create some orders first! The metrics only appear after you use the API:

```powershell
# Run the test script to generate data
powershell -ExecutionPolicy Bypass -File .\scripts\test-workflow.ps1
```

## 📝 Quick Commands

```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f order-service
docker-compose logs -f postgres
docker-compose logs -f rabbitmq

# Rebuild after code changes
docker-compose build order-service
docker-compose up -d order-service

# Check service status
docker-compose ps

# Execute commands in containers
docker-compose exec postgres psql -U postgres -d orders_db
docker-compose exec order-service /bin/sh

# Clean everything (remove volumes)
docker-compose down -v
```

## 🎓 What's Implemented vs TODO

### ✅ Working Now
- Order Service (full CRUD API)
- PostgreSQL (4 databases)
- RabbitMQ (message broker)
- Prometheus (metrics collection)
- Grafana (dashboards)
- Event publishing (order.created, order.status_changed)

### ⏳ TODO (Not Implemented Yet)
- Inventory Service
- Tracking Service
- Notification Service
- API Gateway (centralized routing)
- Dashboard Service (custom monitoring UI)
- Kubernetes deployment scripts
- More Grafana dashboards

## 🔗 Useful Links

- **Order API Docs**: http://localhost:8001/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **RabbitMQ**: http://localhost:15672 (admin/admin_password_123)

## 💡 Tips

1. **First time?** Run the PowerShell test script to create sample data
2. **Testing APIs?** Use the Swagger UI at http://localhost:8001/docs
3. **Checking metrics?** Grafana is easier to read than Prometheus
4. **Debugging?** Check `docker-compose logs -f <service-name>`
5. **Fresh start?** Run `docker-compose down -v` to delete all data

---

**Need help?** Check the main [README.md](README.md) for detailed documentation.
