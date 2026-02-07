# Monitoring Setup & Kubernetes Deployment Guide

## 🎯 Summary of Your Questions

### 1. ✅ **Grafana Dashboards** - FIXED!

**Issue**: No dashboards visible in Grafana
**Root Cause**: Empty logistics-overview.json file in provisioning directory blocked dashboard loading
**Solution**: Removed empty file and imported dashboard via API

**Your Dashboard is now live:**
- URL: http://localhost:3000/d/c9518576-b6a9-40b2-a143-c205375912fe/logistics-overview
- Login: admin / admin

The dashboard shows:
- HTTP Request Rate across all services
- HTTP Request Duration (p50, p95)
- Total Orders Created
- Service Status (UP/DOWN)
- Orders by Status
- HTTP Requests Summary Table

---

### 2. ✅ **Prometheus Metrics** - WORKING!

**Your concern**: "I queried prometheus but no results"
**Status**: Prometheus IS working correctly! ✅

#### Verification:

All services are being scraped successfully:
```bash
# Check targets status
curl http://localhost:9090/targets

# All targets show "health": "up":
- order-service:8001 ✅
- tracking-service:8002 ✅
- inventory-service:8003 ✅
- notification-service:8004 ✅
- api-gateway:8000 ✅
- dashboard:8080 ✅
- rabbitmq:15692 ✅
```

#### Test Queries That Should Work:

1. **HTTP Requests**: `http_requests_total`
2. **Request Rate**: `rate(http_requests_total[5m])`
3. **Service Status**: `service_up`
4. **Request Duration**: `http_request_duration_seconds`

**Why you might see "no results":**
- If you're querying metrics that don't exist yet (e.g., `orders_created_total` requires custom metrics from services)
- Some business metrics are incremented only when specific actions occur (create order, update status, etc.)
- Try querying `http_requests_total` - this should always have data

#### Example Queries in Prometheus:

```promql
# Total HTTP requests across all services
sum(http_requests_total)

# Request rate per service
sum by (service) (rate(http_requests_total[5m]))

# Services that are UP
service_up

# 95th percentile request duration
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Access Prometheus:**
- URL: http://localhost:9090
- Go to Graph tab, enter a query, click "Execute"

---

### 3. ❓ **Kubernetes - Not Deployed Yet**

**Your question**: "where is kubernetes being used?"
**Answer**: Kubernetes manifests exist but are **not currently deployed**. You're running everything with Docker Compose.

#### Current Setup:

```
Docker Compose (✅ Running)
├── 6 Microservices
├── PostgreSQL
├── RabbitMQ
├── Prometheus
└── Grafana
```

#### Kubernetes Deployment Status:

**What exists:**
- ✅ K8s manifests in `k8s/base/`
  - namespace.yaml
  - postgresql/ (StatefulSet, Service, ConfigMap)
  - rabbitmq/ (Deployment, Service, ConfigMap, Secret)
  - order-service/ (Deployment, Service, ConfigMap, HPA)
  - prometheus/ (Deployment, ConfigMap, RBAC)
  - grafana/ (Deployment, ConfigMaps)

**What's missing:**
- ❌ K8s manifests for: tracking-service, inventory-service, notification-service, api-gateway, dashboard
- ❌ Actual deployment to a Kubernetes cluster

#### Why Kubernetes Isn't Running:

The **original goal** was to create a demo app to **explore Kubernetes capabilities**, but:

1. We focused first on getting the microservices working with Docker Compose
2. All your testing has been with Docker Compose (which is working great!)
3. The K8s manifests exist but are incomplete

#### Options Moving Forward:

**Option A: Continue with Docker Compose (Recommended for now)**
- ✅ Already working
- ✅ Easier to develop and test
- ✅ Perfect for local development
- Use case: Learning microservices architecture, event-driven design, monitoring

**Option B: Deploy to Kubernetes**
- Would demonstrate K8s features:
  - Service discovery via DNS
  - Horizontal Pod Autoscaling (HPA)
  - Rolling updates / self-healing
  - Resource limits / health probes
  - Persistent storage (StatefulSets)
- Requires:
  1. Complete K8s manifests for all 6 services
  2. Kubernetes cluster (minikube, kind, or cloud)
  3. Build and push Docker images to registry
  4. Deploy with `kubectl apply -k k8s/base/`

#### To Deploy to Kubernetes (If Desired):

**Prerequisites:**
```powershell
# Install minikube (local Kubernetes)
choco install minikube

# Start minikube
minikube start --cpus 4 --memory 8192

# Verify
kubectl get nodes
```

**Steps:**
1. Create missing K8s manifests (tracking, inventory, notification, api-gateway, dashboard)
2. Build Docker images
3. Load images into minikube: `minikube image load <image-name>`
4. Deploy: `kubectl apply -k k8s/base/`
5. Access services: `kubectl port-forward` or `minikube service`

**Let me know if you want to proceed with Kubernetes deployment, and I can:**
- Create the remaining K8s manifests
- Provide step-by-step deployment instructions
- Set up Kubernetes-specific features (Ingress, HPA, etc.)

---

## 🚀 Quick Testing Commands

### Test Complete Workflow:

```powershell
# 1. Create a warehouse and inventory
Invoke-RestMethod -Uri 'http://localhost:8003/api/v1/warehouses' -Method Post -Body (@{
    warehouse_code = "WH-001"
    name = "Main Warehouse"
    location = "New York, NY"
    capacity = 10000
} | ConvertTo-Json) -ContentType 'application/json'

Invoke-RestMethod -Uri 'http://localhost:8003/api/v1/inventory' -Method Post -Body (@{
    warehouse_id = 1
    sku = "LAPTOP-001"
    item_name = "Dell Laptop"
    quantity = 100
    reorder_level = 10
} | ConvertTo-Json) -ContentType 'application/json'

# 2. Create an order (triggers workflow)
Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/orders' -Method Post -Body (@{
    customer_name = "John Doe"
    customer_email = "john.doe@example.com"
    origin_address = "123 Main St, New York, NY 10001"
    destination_address = "456 Oak Ave, Los Angeles, CA 90001"
    package_weight = 5.5
    package_dimensions = "30x20x15"
    items = @(
        @{
            item_name = "Dell Laptop"
            quantity = 1
            sku = "LAPTOP-001"
        }
    )
} | ConvertTo-Json -Depth 10) -ContentType 'application/json'

# 3. Check RabbitMQ for events
# Open: http://localhost:15672 (admin / admin_password_123)
# Go to: Exchanges → logistics.events → click "Publish message" to see events

# 4. View Prometheus metrics
# Open: http://localhost:9090
# Query: http_requests_total

# 5. View Grafana dashboard
# Open: http://localhost:3000/d/c9518576-b6a9-40b2-a143-c205375912fe/logistics-overview
```

---

## 📊 Monitoring URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana Dashboard** | http://localhost:3000/d/c9518576-b6a9-40b2-a143-c205375912fe/logistics-overview | admin / admin |
| **Grafana Home** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | None |
| **RabbitMQ Management** | http://localhost:15672 | admin / admin_password_123 |
| **Custom Dashboard** | http://localhost:8080 | None |

---

## 🎓 What You've Built

### Current Architecture (Docker Compose):

```
API Gateway (8000) ──┐
                     ├──→ Order Service (8001) ──┐
                     │                            │
                     ├──→ Tracking Service (8002) ├──→ PostgreSQL (4 DBs)
                     │                            │
                     ├──→ Inventory Service (8003)│
                     │                            │
                     └──→ Notification Service────┘
                                   │
                                   ├──→ RabbitMQ (Event Bus)
                                   │
                                   └──→ Prometheus → Grafana
```

### Event-Driven Workflow:

1. User creates order via API Gateway
2. Order Service saves order & publishes `order.created` event
3. Inventory Service consumes event & reserves inventory
4. Tracking Service consumes event & creates shipment
5. Notification Service consumes event & sends notifications
6. All events flow through RabbitMQ
7. All metrics collected by Prometheus
8. Grafana visualizes everything

---

## 📝 Next Steps

1. ✅ **Test the workflow** - Create orders and watch events in RabbitMQ
2. ✅ **Explore Grafana** - View the imported dashboard at http://localhost:3000
3. ✅ **Query Prometheus** - Try the example queries above
4. ❓ **Deploy to Kubernetes?** - Let me know if you want to proceed with K8s deployment

---

**Summary:**
- ✅ Grafana dashboard: Fixed and imported
- ✅ Prometheus: Working correctly (metrics are being collected)
- ✅ Docker Compose: All services running
- ❌ Kubernetes: Not deployed (manifests exist but incomplete)
