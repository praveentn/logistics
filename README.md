# Logistics Microservices Demo - Kubernetes Exploration Platform

A comprehensive demo logistics application built with microservices architecture to explore and demonstrate Kubernetes capabilities. This platform simulates a realistic logistics workflow while showcasing K8s features like service discovery, horizontal scaling, health checks, persistent storage, and monitoring.

## 🎯 Project Overview

This project demonstrates:
- **Microservices Architecture**: Multiple services communicating via REST and messaging
- **Kubernetes Orchestration**: Deployments, Services, StatefulSets, ConfigMaps, Secrets, HPA
- **Event-Driven Communication**: RabbitMQ for async messaging between services
- **Monitoring & Observability**: Prometheus metrics and Grafana dashboards
- **Production Patterns**: Health checks, resource limits, rolling updates, auto-scaling

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway (8000)                      │
│                    (Request Routing)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Order Service │  │Tracking Svc  │  │Inventory Svc │
│   (8001)     │  │   (8002)     │  │   (8003)     │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └────────┬────────┴────────┬────────┘
                │                 │
                ▼                 ▼
         ┌─────────────┐   ┌─────────────┐
         │  RabbitMQ   │   │ PostgreSQL  │
         │  (Events)   │   │ (Data)      │
         └─────────────┘   └─────────────┘
                │
                ▼
       ┌─────────────────┐
       │Notification Svc  │
       │    (8004)        │
       └──────────────────┘
                │
                ▼
       ┌──────────────────────┐
       │  Dashboard (8080)    │
       │  Prometheus (9090)   │
       │  Grafana (3000)      │
       └──────────────────────┘
```

## 🏗️ Current Implementation Status

### ✅ Completed Components

#### Infrastructure
- ✅ **PostgreSQL StatefulSet**: Multi-database setup with persistent storage
- ✅ **RabbitMQ Deployment**: Message broker with management UI
- ✅ **Kubernetes Namespace**: Isolated logistics-demo environment
- ✅ **Prometheus Configuration**: Metrics collection setup
- ✅ **Docker Compose**: Local development environment

#### Shared Libraries
- ✅ **Metrics Module** ([shared/metrics.py](shared/metrics.py)): Prometheus instrumentation
- ✅ **Messaging Module** ([shared/messaging.py](shared/messaging.py)): RabbitMQ publisher/consumer
- ✅ **Database Module** ([shared/database.py](shared/database.py)): SQLAlchemy session management
- ✅ **Logging Module** ([shared/logging_config.py](shared/logging_config.py)): Structured JSON logging

#### Microservices
- ✅ **Order Service** (Complete):
  - Full CRUD API for orders
  - Database models and schemas
  - Event publishing (order.created, order.status_changed)
  - Prometheus metrics
  - Health checks
  - Kubernetes manifests (Deployment, Service, ConfigMap, HPA)
  - Docker image configuration

### 🚧 Pending Components

The following services follow the same pattern as Order Service and need to be implemented:

- ⏳ **Inventory Service**: Warehouse and inventory management with reservation logic
- ⏳ **Tracking Service**: Shipment tracking with location updates
- ⏳ **Notification Service**: Event-driven notification system
- ⏳ **API Gateway**: Request routing and service discovery
- ⏳ **Dashboard**: Real-time monitoring and statistics UI
- ⏳ **Grafana Dashboards**: Pre-configured visualization dashboards
- ⏳ **Kustomize Overlays**: Dev/prod environment configurations

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Kubernetes cluster (minikube, kind, or cloud) - for K8s deployment
- kubectl
- make (optional, for convenience commands)

### Option 1: Local Development with Docker Compose

1. **Start all services**:
   ```bash
   make up
   # or
   docker-compose up -d
   ```

2. **Access the services**:
   - Order Service API: http://localhost:8001/docs
   - RabbitMQ Management: http://localhost:15672 (admin/admin_password_123)
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)
   - PostgreSQL: localhost:5432

3. **Test the Order Service**:
   ```bash
   make test-workflow
   # or
   bash scripts/test-workflow.sh
   ```

4. **View logs**:
   ```bash
   make logs-order
   # or
   docker-compose logs -f order-service
   ```

5. **Stop services**:
   ```bash
   make down
   # or
   docker-compose down
   ```

### Option 2: Kubernetes Deployment

1. **Build Docker images** (if using local registry):
   ```bash
   cd services/order-service
   docker build -t order-service:latest .
   ```

2. **Deploy to Kubernetes**:
   ```bash
   make k8s-deploy
   # or manually:
   kubectl apply -f k8s/base/namespace/
   kubectl apply -f k8s/base/postgresql/
   kubectl apply -f k8s/base/rabbitmq/
   kubectl apply -f k8s/base/order-service/
   ```

3. **Check deployment status**:
   ```bash
   make k8s-status
   # or
   kubectl get pods -n logistics-demo
   kubectl get svc -n logistics-demo
   ```

4. **Port forward for local access**:
   ```bash
   kubectl port-forward svc/order-service 8001:8001 -n logistics-demo
   ```

5. **View logs**:
   ```bash
   make k8s-logs-order
   # or
   kubectl logs -f deployment/order-service -n logistics-demo
   ```

## 📖 API Documentation

### Order Service Endpoints

**Base URL**: `http://localhost:8001`

#### Create Order
```bash
POST /api/v1/orders
Content-Type: application/json

{
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "origin_address": "123 Main St, New York, NY",
  "destination_address": "456 Oak Ave, Los Angeles, CA",
  "package_weight": 5.5,
  "package_dimensions": "30x20x15",
  "items": [
    {
      "item_name": "Laptop",
      "quantity": 1,
      "sku": "LAPTOP-001"
    }
  ]
}
```

#### List Orders
```bash
GET /api/v1/orders?page=1&page_size=10&status=pending
```

#### Get Order Details
```bash
GET /api/v1/orders/{order_id}
```

#### Update Order Status
```bash
PUT /api/v1/orders/{order_id}/status
Content-Type: application/json

{
  "status": "processing"
}
```

Valid statuses: `pending`, `processing`, `shipped`, `delivered`, `cancelled`

#### Cancel Order
```bash
DELETE /api/v1/orders/{order_id}
```

#### Health Check
```bash
GET /health
```

#### Prometheus Metrics
```bash
GET /metrics
```

### Interactive API Documentation
Open http://localhost:8001/docs for Swagger UI documentation.

## 🧪 Testing

### Basic Health Check
```bash
curl http://localhost:8001/health | jq .
```

### Complete Workflow Test
```bash
bash scripts/test-workflow.sh
```

This script:
1. Checks service health
2. Creates a test order
3. Retrieves order details
4. Lists all orders
5. Updates order status
6. Retrieves order items

### Manual Testing
```bash
# Create an order
curl -X POST http://localhost:8001/api/v1/orders \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "customer_name": "Jane Smith",
  "customer_email": "jane@example.com",
  "origin_address": "789 Pine Rd, Seattle, WA",
  "destination_address": "321 Elm St, Austin, TX",
  "package_weight": 3.2,
  "items": [
    {"item_name": "Book", "quantity": 3, "sku": "BOOK-001"}
  ]
}
EOF

# List orders
curl http://localhost:8001/api/v1/orders | jq .

# Check Prometheus metrics
curl http://localhost:8001/metrics
```

## 📊 Monitoring

### Prometheus
Access at http://localhost:9090

Example queries:
```promql
# HTTP request rate
rate(http_requests_total[5m])

# HTTP request duration (p95)
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Total orders created
orders_created_total

# Orders by status
orders_by_status
```

### Grafana
Access at http://localhost:3000 (admin/admin)

Pre-configured dashboards (to be added):
- Logistics Overview
- Service Health
- Business Metrics

### RabbitMQ Management
Access at http://localhost:15672 (admin/admin_password_123)

Monitor:
- Queue depths
- Message rates
- Consumer activity
- Exchange bindings

## 🔧 Development

### Project Structure
```
logistics/
├── services/                    # Microservices
│   ├── order-service/          # ✅ Order management (COMPLETE)
│   ├── tracking-service/       # ⏳ Shipment tracking (TODO)
│   ├── inventory-service/      # ⏳ Inventory management (TODO)
│   ├── notification-service/   # ⏳ Notifications (TODO)
│   ├── api-gateway/            # ⏳ API routing (TODO)
│   └── dashboard/              # ⏳ Monitoring dashboard (TODO)
├── shared/                      # ✅ Shared utilities (COMPLETE)
│   ├── metrics.py              # Prometheus metrics
│   ├── messaging.py            # RabbitMQ helpers
│   ├── database.py             # Database utilities
│   └── logging_config.py       # Structured logging
├── k8s/                         # Kubernetes manifests
│   ├── base/                   # Base configurations
│   │   ├── namespace/          # ✅ Namespace
│   │   ├── postgresql/         # ✅ Database StatefulSet
│   │   ├── rabbitmq/           # ✅ Message broker
│   │   └── order-service/      # ✅ Order service K8s config
│   └── overlays/               # ⏳ Kustomize overlays (TODO)
├── monitoring/                  # Monitoring configs
│   ├── prometheus/             # ✅ Prometheus configuration
│   └── grafana/                # ⏳ Dashboards (TODO)
├── scripts/                     # Helper scripts
│   ├── init-db.sql             # Database initialization
│   └── test-workflow.sh        # E2E testing
├── docker-compose.yml          # ✅ Local development setup
└── Makefile                    # ✅ Convenience commands
```

### Adding a New Service

Use Order Service as a template:

1. **Copy the structure**:
   ```bash
   cp -r services/order-service services/your-service
   ```

2. **Update the code**:
   - Modify `app/models.py` for your database schema
   - Update `app/schemas.py` with your Pydantic models
   - Implement business logic in `app/services/`
   - Create API endpoints in `app/api/`
   - Update `app/main.py` service name

3. **Update configurations**:
   - Modify `requirements.txt` if needed
   - Update `Dockerfile`
   - Create K8s manifests in `k8s/base/your-service/`

4. **Add to docker-compose.yml**:
   ```yaml
   your-service:
     build: ./services/your-service
     ports:
       - "8XXX:8XXX"
     environment:
       DATABASE_URL: "postgresql://postgres:demo_password_123@postgres:5432/your_db"
     depends_on:
       - postgres
       - rabbitmq
   ```

5. **Update Prometheus config**:
   Add your service to `monitoring/prometheus/prometheus.yml`

### Database Schema Management

Each service manages its own database schema using SQLAlchemy migrations (to be added) or direct model creation.

Current databases:
- `orders_db` - Order Service
- `tracking_db` - Tracking Service (pending)
- `inventory_db` - Inventory Service (pending)
- `notifications_db` - Notification Service (pending)

## 🎯 Kubernetes Capabilities Demonstrated

### Core Concepts
- ✅ **Pods**: Container runtime units
- ✅ **Deployments**: Declarative updates, rolling deployments
- ✅ **StatefulSets**: PostgreSQL with persistent storage
- ✅ **Services**: ClusterIP for service discovery
- ✅ **ConfigMaps**: Environment configuration
- ✅ **Secrets**: Sensitive data storage
- ✅ **Namespaces**: Resource isolation
- ✅ **PersistentVolumes**: Data persistence

### Advanced Features
- ✅ **HorizontalPodAutoscaler**: CPU-based auto-scaling
- ✅ **Liveness/Readiness Probes**: Health monitoring
- ✅ **Resource Requests/Limits**: Resource management
- ✅ **Rolling Updates**: Zero-downtime deployments
- ⏳ **Ingress**: External access routing (TODO)
- ⏳ **Network Policies**: Service-to-service security (TODO)

### Operational Patterns
- ✅ **Service Discovery**: DNS-based (http://order-service:8001)
- ✅ **Load Balancing**: Automatic across replicas
- ✅ **Self-Healing**: Automatic pod restart
- ✅ **Horizontal Scaling**: Manual and automatic (HPA)

## 🔐 Security Notes

**⚠️ This is a DEMO project. Do NOT use in production without hardening!**

Current security limitations:
- Hardcoded credentials in ConfigMaps/Secrets
- No authentication/authorization on APIs
- No TLS/HTTPS
- No network policies
- No RBAC beyond Prometheus
- Default passwords

For production, implement:
- External secret management (Vault, AWS Secrets Manager)
- API authentication (JWT, OAuth2)
- TLS certificates (cert-manager)
- Network policies for pod-to-pod communication
- RBAC for service accounts
- Secure password policies

## 📚 Technology Stack

- **Language**: Python 3.11
- **Web Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0.23
- **Message Broker**: RabbitMQ 3.12
- **Monitoring**: Prometheus + Grafana
- **Container Runtime**: Docker
- **Orchestration**: Kubernetes
- **API Documentation**: OpenAPI/Swagger

## 🛠️ Troubleshooting

### Service won't start
```bash
# Check logs
docker-compose logs order-service

# Check database connectivity
docker-compose exec postgres psql -U postgres -l

# Check RabbitMQ
docker-compose exec rabbitmq rabbitmq-diagnostics ping
```

### Database connection errors
```bash
# Ensure PostgreSQL is healthy
docker-compose ps postgres

# Verify database exists
docker-compose exec postgres psql -U postgres -c "\l"

# Recreate databases
docker-compose down -v
docker-compose up -d
```

### Kubernetes pod crashes
```bash
# Check pod status
kubectl describe pod <pod-name> -n logistics-demo

# View logs
kubectl logs <pod-name> -n logistics-demo

# Check events
kubectl get events -n logistics-demo --sort-by='.lastTimestamp'
```

## 🗺️ Next Steps

To complete the full logistics platform:

1. **Implement remaining services**:
   - [ ] Inventory Service (reservation logic, low-stock alerts)
   - [ ] Tracking Service (shipment creation, location updates)
   - [ ] Notification Service (email/SMS templates, event handlers)
   - [ ] API Gateway (routing, rate limiting, authentication)
   - [ ] Dashboard (real-time stats, service health UI)

2. **Add monitoring dashboards**:
   - [ ] Grafana logistics overview dashboard
   - [ ] Grafana service health dashboard
   - [ ] Alerting rules in Prometheus

3. **Implement Kustomize overlays**:
   - [ ] Dev environment configuration
   - [ ] Prod environment configuration

4. **Add testing**:
   - [ ] Unit tests for each service
   - [ ] Integration tests
   - [ ] Load testing scripts

5. **Documentation**:
   - [ ] Architecture diagrams
   - [ ] Deployment guide
   - [ ] API documentation for all services

6. **Advanced K8s features**:
   - [ ] Ingress controller setup
   - [ ] Network policies
   - [ ] Service mesh (optional)
   - [ ] GitOps with ArgoCD (optional)

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This is a demo project for learning Kubernetes. Feel free to:
- Fork and experiment
- Add new features
- Improve documentation
- Report issues

---

**Built with Claude Code** - Exploring Kubernetes capabilities through practical microservices implementation.
