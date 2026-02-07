# Building a Production-Grade Microservices Platform with Claude Code

## The Challenge

Build a complete logistics platform from scratch — 6 microservices, event-driven architecture, container orchestration, monitoring, and deployment automation — using Claude Code as the AI-powered development partner.

## What We Built

### Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              API Gateway (8000)              │
                    └──────┬──────┬──────┬──────┬────────────────┘
                           │      │      │      │
              ┌────────────┘      │      │      └────────────┐
              ▼                   ▼      ▼                   ▼
     ┌──────────────┐  ┌──────────────┐ ┌──────────────┐  ┌──────────────┐
     │ Order Service│  │   Tracking   │ │  Inventory   │  │ Notification │
     │    (8001)    │  │   Service    │ │   Service    │  │   Service    │
     │              │  │    (8002)    │ │    (8003)    │  │    (8004)    │
     └──────┬───────┘  └──────┬──────┘ └──────┬───────┘  └──────┬──────┘
            │                 │               │                 │
            └─────────┬───────┴───────┬───────┘                 │
                      ▼               ▼                         │
              ┌──────────────┐ ┌──────────────┐                 │
              │  PostgreSQL  │ │   RabbitMQ   │◄────────────────┘
              │  (4 DBs)     │ │ (Event Bus)  │
              └──────────────┘ └──────────────┘
                      │
              ┌───────┴────────┐
              │   Prometheus   │──▶ Grafana Dashboard
              └────────────────┘
```

### Technology Stack

- **Backend**: Python FastAPI with async/await
- **Database**: PostgreSQL 15 with 4 isolated databases
- **Messaging**: RabbitMQ 3.12 with topic exchange pattern
- **Monitoring**: Prometheus + Grafana with pre-configured dashboards
- **Containers**: Docker with multi-stage builds
- **Orchestration**: Docker Compose (local dev) + Kubernetes (production)
- **Infrastructure as Code**: Kustomize for K8s manifest management

## How Claude Code Helped

### 1. Architecture & Planning

Started with a high-level requirement: *"Set up a demo logistics app to explore Kubernetes capabilities."*

Claude Code entered **plan mode** — asked targeted questions about technology preferences (framework, database, monitoring stack, complexity level), then produced a phased implementation plan covering directory structure, shared utilities, service-by-service implementation, and deployment strategy.

### 2. Parallel Development

Claude Code used **parallel task agents** to implement multiple services simultaneously:

- Inventory Service (warehouse management, stock reservations)
- Tracking Service (shipment tracking, auto-creation from orders)
- Notification Service (templated notifications, multi-event handling)
- API Gateway (request proxying with circuit breaker pattern)
- Dashboard (real-time stats UI with auto-refresh)

All 5 services were scaffolded concurrently, each with models, schemas, API endpoints, messaging consumers, Dockerfiles, and Kubernetes manifests.

### 3. Iterative Debugging

Real-world development isn't error-free. Claude Code diagnosed and fixed issues as they surfaced:

**Error 1**: `ImportError: email-validator is not installed`
- **Root cause**: Pydantic's `EmailStr` field requires a separate package
- **Fix**: Added `pydantic[email]` and `email-validator` to requirements.txt

**Error 2**: `SAWarning: Textual SQL expression 'SELECT 1'`
- **Root cause**: SQLAlchemy 2.0 requires explicit `text()` wrapper for raw SQL
- **Fix**: `db.execute(text("SELECT 1"))` instead of `db.execute("SELECT 1")`

**Error 3**: `ModuleNotFoundError: No module named 'messaging'`
- **Root cause**: Docker build context didn't include the `shared/` directory
- **Fix**: Changed Docker Compose build contexts to repository root, updated all 6 Dockerfiles to copy `shared/` into the image, fixed import paths

**Error 4**: Grafana dashboard not loading
- **Root cause**: Empty JSON file in provisioning directory blocking dashboard load; found by grepping container logs for `"error"` — discovered `"Dashboard title cannot be empty"`
- **Fix**: Imported dashboard via Grafana API instead

**Error 5**: `kustomization.yaml` missing from K8s directories
- **Root cause**: Original infrastructure manifests were created without Kustomize wrappers
- **Fix**: Created kustomization.yaml for all 8 K8s modules, removed `commonLabels` (causes selector conflicts), fixed image names and pull policies

### 4. Infrastructure as Code

Claude Code generated production-grade Kubernetes manifests for every component:

| Resource Type | What It Demonstrates |
|---------------|---------------------|
| **Deployments** | Rolling updates, replica management |
| **StatefulSets** | PostgreSQL with persistent storage |
| **Services** | ClusterIP for internal service discovery |
| **ConfigMaps** | Environment-specific configuration |
| **Secrets** | Credential management |
| **HPA** | Auto-scaling based on CPU/memory (2-5 replicas) |
| **Health Probes** | Liveness & readiness checks on every service |
| **Resource Limits** | CPU/memory requests and limits |
| **PVCs** | Persistent volume claims for database storage |

### 5. Automation Scripts

Generated PowerShell scripts for Windows:
- **deploy-kubernetes.ps1** — One-command deployment: prerequisite checks, minikube startup, image builds, image loading, namespace creation, infrastructure deployment, service deployment
- **test-kubernetes.ps1** — Automated testing with port-forwarding, health checks, order creation
- **setup-grafana.ps1** — Grafana datasource and dashboard provisioning via API

## Event-Driven Workflow

The crown jewel — a fully automated event pipeline:

```
User creates order via API Gateway
  → Order Service saves to DB, publishes "order.created" to RabbitMQ
    → Inventory Service consumes event, reserves stock
    → Tracking Service consumes event, creates shipment with tracking number
    → Notification Service consumes event, sends order confirmation
      → Tracking publishes "shipment.created"
        → Notification Service sends shipment notification
```

All of this happens automatically through RabbitMQ's topic exchange with routing keys like `order.created`, `shipment.updated`, `inventory.low_stock`.

## By the Numbers

| Metric | Count |
|--------|-------|
| **Services created** | 6 microservices + 4 infrastructure |
| **Files generated** | ~80+ files |
| **K8s manifests** | 30+ YAML files across 9 modules |
| **Databases** | 4 isolated PostgreSQL databases |
| **Event types** | 5 (order.created, order.status_changed, shipment.created, shipment.updated, inventory.low_stock) |
| **Deployment targets** | 2 (Docker Compose + Kubernetes) |
| **Bugs diagnosed & fixed** | 5 runtime errors across the session |
| **Automation scripts** | 4 PowerShell scripts |
| **Documentation** | 3 comprehensive guides (700+ lines) |

## Key Takeaways

1. **Claude Code handles complexity iteratively** — It doesn't just generate code; it plans, implements, tests, debugs, and adapts. Each error was diagnosed from actual container logs and fixed in context.

2. **Parallelization matters** — Using task agents to build 5 services concurrently compressed what would be hours of scaffolding into minutes.

3. **Full-stack, end-to-end** — From Python business logic to Dockerfiles to Kubernetes StatefulSets to Grafana dashboards to PowerShell deployment scripts — all in one conversation.

4. **Production patterns, not toy code** — Health probes, resource limits, rolling update strategies, circuit breakers, structured logging, Prometheus metrics, HPA with scale-up/down policies, non-root containers, multi-stage Docker builds.

5. **Real debugging, not just generation** — The most valuable moments weren't the initial code generation — they were when things broke. Claude Code read logs, traced import chains, understood Docker build contexts, and fixed root causes rather than applying band-aids.

---

*The entire platform — from empty directory to running microservices with monitoring and Kubernetes deployment — was built in a single Claude Code session.*
