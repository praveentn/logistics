# Kubernetes Deployment Guide

## 🎯 Overview

This guide walks you through deploying the Logistics Platform to **Kubernetes** while keeping your **Docker Compose** deployment running separately.

**What you'll deploy:**
- 6 Microservices (Order, Tracking, Inventory, Notification, API Gateway, Dashboard)
- PostgreSQL StatefulSet (4 databases)
- RabbitMQ Deployment
- Prometheus & Grafana (monitoring)
- Horizontal Pod Autoscalers (HPA)
- Complete service mesh with health probes

---

## 📋 Prerequisites

### 1. Install Required Tools

```powershell
# Install Chocolatey (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install kubectl
choco install kubernetes-cli -y

# Install minikube
choco install minikube -y

# Verify installations
kubectl version --client
minikube version
docker --version
```

### 2. Start Minikube

```powershell
# Start minikube with sufficient resources
minikube start --cpus=4 --memory=8192 --driver=docker

# Verify it's running
minikube status

# Enable metrics server (optional, for HPA and resource monitoring)
minikube addons enable metrics-server
```

---

## 🚀 Quick Start - Automated Deployment

### One-Command Deployment

```powershell
# Deploy everything to Kubernetes
.\scripts\deploy-kubernetes.ps1
```

This script will:
1. ✅ Check prerequisites (kubectl, minikube, docker)
2. ✅ Start minikube (if not running)
3. ✅ Build Docker images
4. ✅ Load images into minikube
5. ✅ Create namespace
6. ✅ Deploy PostgreSQL & RabbitMQ
7. ✅ Wait for infrastructure to be ready
8. ✅ Deploy all 6 microservices
9. ✅ Show deployment status

**Time**: ~10-15 minutes (first time)

### Script Options

```powershell
# Skip Docker build (if images already exist)
.\scripts\deploy-kubernetes.ps1 -SkipBuild

# Skip image loading (if already loaded)
.\scripts\deploy-kubernetes.ps1 -SkipLoad

# Clean up existing deployment first
.\scripts\deploy-kubernetes.ps1 -Clean

# Combine flags
.\scripts\deploy-kubernetes.ps1 -Clean -SkipBuild
```

---

## 📦 Manual Step-by-Step Deployment

If you prefer to understand each step:

### Step 1: Build Docker Images

```powershell
docker-compose build
```

### Step 2: Load Images into Minikube

```powershell
minikube image load logistics-order-service:latest
minikube image load logistics-tracking-service:latest
minikube image load logistics-inventory-service:latest
minikube image load logistics-notification-service:latest
minikube image load logistics-api-gateway:latest
minikube image load logistics-dashboard:latest
```

### Step 3: Create Namespace

```powershell
kubectl apply -f k8s/base/namespace/namespace.yaml
```

### Step 4: Deploy Infrastructure

```powershell
# Deploy PostgreSQL
kubectl apply -k k8s/base/postgresql/

# Deploy RabbitMQ
kubectl apply -k k8s/base/rabbitmq/

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod -l app=postgresql -n logistics-demo --timeout=300s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n logistics-demo --timeout=300s
```

### Step 5: Deploy Microservices

```powershell
# Deploy each service
kubectl apply -k k8s/base/order-service/
kubectl apply -k k8s/base/tracking-service/
kubectl apply -k k8s/base/inventory-service/
kubectl apply -k k8s/base/notification-service/
kubectl apply -k k8s/base/api-gateway/
kubectl apply -k k8s/base/dashboard/
```

### Step 6: Verify Deployment

```powershell
# Check all pods
kubectl get pods -n logistics-demo

# Check services
kubectl get services -n logistics-demo

# Check HPA status
kubectl get hpa -n logistics-demo
```

---

## 🔍 Accessing Services

### Option A: Port Forwarding (Recommended)

```powershell
# API Gateway
kubectl port-forward -n logistics-demo svc/api-gateway 8000:8000

# Dashboard
kubectl port-forward -n logistics-demo svc/dashboard 8080:8080

# Individual services
kubectl port-forward -n logistics-demo svc/order-service 8001:8001
kubectl port-forward -n logistics-demo svc/tracking-service 8002:8002
kubectl port-forward -n logistics-demo svc/inventory-service 8003:8003

# RabbitMQ Management
kubectl port-forward -n logistics-demo svc/rabbitmq 15672:15672
```

Then access in browser:
- API Gateway: http://localhost:8000
- Dashboard: http://localhost:8080
- RabbitMQ: http://localhost:15672

### Option B: Minikube Service

```powershell
# Open dashboard in browser
minikube service dashboard -n logistics-demo

# Get service URL
minikube service api-gateway -n logistics-demo --url
```

### Option C: Ingress (Advanced)

Create an Ingress resource for external access (see Advanced section below).

---

## 🧪 Testing the Deployment

### Automated Test

```powershell
.\scripts\test-kubernetes.ps1
```

This will:
- Check pod status
- Test health endpoints
- Create a test order
- Show HPA status

### Manual Testing

```powershell
# 1. Port-forward API Gateway
kubectl port-forward -n logistics-demo svc/api-gateway 8000:8000

# 2. In another terminal, create an order
$orderData = @{
    customer_name = "John Doe K8s"
    customer_email = "john@k8s.example.com"
    origin_address = "123 K8s Ave"
    destination_address = "456 Pod St"
    package_weight = 5.0
    package_dimensions = "30x20x15"
    items = @(
        @{
            item_name = "Kubernetes Book"
            quantity = 1
            sku = "K8S-001"
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/orders" -Method Post -Body $orderData -ContentType "application/json"
```

---

## 🎓 Kubernetes Features Demonstrated

### 1. Service Discovery

Services communicate via Kubernetes DNS:

```yaml
# In configmap.yaml
ORDER_SERVICE_URL: "http://order-service:8001"
```

Test it:
```powershell
kubectl exec -n logistics-demo -it deployment/api-gateway -- curl http://order-service:8001/health
```

### 2. Horizontal Pod Autoscaling (HPA)

All services have HPA configured:

```powershell
# Check HPA status
kubectl get hpa -n logistics-demo

# Describe HPA
kubectl describe hpa order-service-hpa -n logistics-demo

# Manual scaling (bypasses HPA)
kubectl scale deployment order-service -n logistics-demo --replicas=5

# Watch pods scale
kubectl get pods -n logistics-demo -w
```

### 3. Health Probes

Liveness and readiness probes ensure healthy traffic routing:

```powershell
# Kill a pod's process to test self-healing
kubectl exec -n logistics-demo deployment/order-service -- pkill -9 uvicorn

# Watch Kubernetes restart it
kubectl get pods -n logistics-demo -w
```

### 4. Rolling Updates

Deploy a new version with zero downtime:

```powershell
# Update image
kubectl set image deployment/order-service order-service=logistics-order-service:v2 -n logistics-demo

# Watch rollout
kubectl rollout status deployment/order-service -n logistics-demo

# Rollback if needed
kubectl rollout undo deployment/order-service -n logistics-demo
```

### 5. Resource Limits & Requests

```powershell
# View resource usage
kubectl top pods -n logistics-demo

# Describe pod resources
kubectl describe pod -n logistics-demo -l app=order-service | findstr -i "requests limits"
```

### 6. StatefulSets

PostgreSQL uses StatefulSet for stable network identity:

```powershell
# Check StatefulSet
kubectl get statefulset -n logistics-demo

# View persistent volumes
kubectl get pv
kubectl get pvc -n logistics-demo
```

---

## 📊 Monitoring in Kubernetes

### View Logs

```powershell
# Stream logs from a service
kubectl logs -f -n logistics-demo -l app=order-service

# View logs from all replicas
kubectl logs -n logistics-demo -l app=order-service --tail=50

# View logs from specific pod
kubectl logs -n logistics-demo <pod-name>

# View previous container logs (if crashed)
kubectl logs -n logistics-demo <pod-name> --previous
```

### Events

```powershell
# View events for namespace
kubectl get events -n logistics-demo --sort-by='.lastTimestamp'

# Watch events
kubectl get events -n logistics-demo -w
```

### Resource Usage

```powershell
# Cluster overview
kubectl top nodes

# Pod resource usage
kubectl top pods -n logistics-demo

# Sort by CPU
kubectl top pods -n logistics-demo --sort-by=cpu

# Sort by memory
kubectl top pods -n logistics-demo --sort-by=memory
```

---

## 🛠️ Common Operations

### Restart a Service

```powershell
# Restart all pods in a deployment
kubectl rollout restart deployment/order-service -n logistics-demo
```

### Update ConfigMap

```powershell
# Edit configmap
kubectl edit configmap order-service-config -n logistics-demo

# Restart pods to pick up new config
kubectl rollout restart deployment/order-service -n logistics-demo
```

### Debug a Pod

```powershell
# Get shell in a pod
kubectl exec -it -n logistics-demo deployment/order-service -- /bin/sh

# Run commands
kubectl exec -n logistics-demo deployment/order-service -- env | findstr DATABASE

# Copy files from pod
kubectl cp logistics-demo/<pod-name>:/app/logs/app.log ./local-app.log
```

### View Descriptions

```powershell
# Describe pod (useful for debugging)
kubectl describe pod -n logistics-demo <pod-name>

# Describe service
kubectl describe service order-service -n logistics-demo

# Describe HPA
kubectl describe hpa order-service-hpa -n logistics-demo
```

---

## 🔧 Troubleshooting

### Pods Not Starting

```powershell
# Check pod status
kubectl get pods -n logistics-demo

# Describe pod to see events
kubectl describe pod -n logistics-demo <pod-name>

# Check logs
kubectl logs -n logistics-demo <pod-name>

# Check if images are loaded
minikube image ls | findstr logistics
```

### ImagePullBackOff Error

```powershell
# Load image into minikube
minikube image load logistics-order-service:latest

# Or rebuild and reload
docker-compose build order-service
minikube image load logistics-order-service:latest

# Restart deployment
kubectl rollout restart deployment/order-service -n logistics-demo
```

### CrashLoopBackOff

```powershell
# View logs
kubectl logs -n logistics-demo <pod-name>

# View previous logs
kubectl logs -n logistics-demo <pod-name> --previous

# Check if dependencies are ready
kubectl get pods -n logistics-demo | findstr postgres
kubectl get pods -n logistics-demo | findstr rabbitmq
```

### Service Not Accessible

```powershell
# Check service exists
kubectl get service -n logistics-demo

# Check endpoints
kubectl get endpoints order-service -n logistics-demo

# Test from within cluster
kubectl run test-pod --rm -it --image=curlimages/curl -n logistics-demo -- sh
curl http://order-service:8001/health
```

### Database Connection Issues

```powershell
# Check PostgreSQL pod
kubectl logs -n logistics-demo -l app=postgresql

# Exec into pod
kubectl exec -it -n logistics-demo -l app=postgresql -- psql -U postgres -l

# Test connectivity from service
kubectl exec -n logistics-demo deployment/order-service -- env | findstr DATABASE
```

---

## 🧹 Cleanup

### Delete Everything

```powershell
# Delete entire namespace (removes all resources)
kubectl delete namespace logistics-demo

# Or use script with --Clean flag
.\scripts\deploy-kubernetes.ps1 -Clean
```

### Delete Specific Service

```powershell
kubectl delete -k k8s/base/order-service/
```

### Stop Minikube

```powershell
# Stop minikube (keeps state)
minikube stop

# Delete minikube cluster (removes everything)
minikube delete
```

---

## 📚 Advanced Topics

### Ingress Configuration

Create an Ingress for external access:

```yaml
# k8s/base/ingress/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: logistics-ingress
  namespace: logistics-demo
spec:
  rules:
  - host: logistics.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
```

```powershell
# Enable ingress addon
minikube addons enable ingress

# Apply ingress
kubectl apply -f k8s/base/ingress/ingress.yaml

# Get ingress IP
minikube ip

# Add to hosts file: C:\Windows\System32\drivers\etc\hosts
# <minikube-ip> logistics.local
```

### Persistent Storage

For production, use persistent storage:

```yaml
# storageclass.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-storage
provisioner: k8s.io/minikube-hostpath
parameters:
  type: pd-ssd
```

### Secrets Management

Replace ConfigMaps with Secrets for sensitive data:

```powershell
# Create secret
kubectl create secret generic postgres-secret -n logistics-demo `
  --from-literal=password=demo_password_123

# Reference in deployment
envFrom:
- secretRef:
    name: postgres-secret
```

---

## 📊 Comparison: Docker Compose vs Kubernetes

| Feature | Docker Compose | Kubernetes |
|---------|----------------|------------|
| **Ports** | localhost:8000-8080 | Port-forward or Ingress |
| **Scaling** | Manual (`docker-compose up --scale`) | Automatic (HPA) |
| **Health Checks** | Docker healthcheck | Liveness/Readiness probes |
| **Service Discovery** | Container names | Kubernetes DNS |
| **Load Balancing** | None (single container) | Automatic (Service) |
| **Self-Healing** | Restart policy | ReplicaSets |
| **Rolling Updates** | Manual | Built-in |
| **Resource Limits** | Docker limits | Kubernetes requests/limits |
| **Monitoring** | Prometheus/Grafana | Prometheus/Grafana + K8s metrics |

---

## 🎯 Next Steps

1. ✅ Deploy to Kubernetes: `.\scripts\deploy-kubernetes.ps1`
2. ✅ Test deployment: `.\scripts\test-kubernetes.ps1`
3. ✅ Explore HPA: `kubectl get hpa -n logistics-demo -w`
4. ✅ Try rolling update
5. ✅ Test self-healing (kill a pod)
6. ✅ Monitor resource usage
7. ✅ Set up Ingress for external access

---

## 📖 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kustomize Documentation](https://kustomize.io/)

---

**You now have a production-grade Kubernetes deployment! 🎉**

Both Docker Compose and Kubernetes deployments can run simultaneously on different ports/clusters.
