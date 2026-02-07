# Kubernetes Deployment Script for Logistics Platform
# This script automates the complete deployment to minikube

param(
    [switch]$SkipBuild,
    [switch]$SkipLoad,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Logistics Platform - Kubernetes Deployment  " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Check prerequisites
Write-Host "[1/9] Checking prerequisites..." -ForegroundColor Yellow
$missingTools = @()

if (-not (Test-Command "kubectl")) { $missingTools += "kubectl" }
if (-not (Test-Command "minikube")) { $missingTools += "minikube" }
if (-not (Test-Command "docker")) { $missingTools += "docker" }

if ($missingTools.Count -gt 0) {
    Write-Host "ERROR: Missing required tools: $($missingTools -join ', ')" -ForegroundColor Red
    Write-Host "Please install them first:" -ForegroundColor Red
    Write-Host "  - kubectl: https://kubernetes.io/docs/tasks/tools/" -ForegroundColor Red
    Write-Host "  - minikube: https://minikube.sigs.k8s.io/docs/start/" -ForegroundColor Red
    Write-Host "  - docker: https://docs.docker.com/get-docker/" -ForegroundColor Red
    exit 1
}
Write-Host "All prerequisites found!" -ForegroundColor Green
Write-Host ""

# Clean up if requested
if ($Clean) {
    Write-Host "[CLEAN] Cleaning up existing deployment..." -ForegroundColor Yellow
    kubectl delete namespace logistics-demo --ignore-not-found=true
    Write-Host "Waiting for namespace to be deleted..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    Write-Host "Cleanup complete!" -ForegroundColor Green
    Write-Host ""
}

# Check if minikube is running
Write-Host "[2/9] Checking minikube status..." -ForegroundColor Yellow
$minikubeStatus = minikube status --format='{{.Host}}' 2>$null

if ($minikubeStatus -ne "Running") {
    Write-Host "Minikube is not running. Starting minikube..." -ForegroundColor Yellow
    Write-Host "This may take 2-3 minutes..." -ForegroundColor Yellow
    minikube start --cpus=4 --memory=8192 --driver=docker
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to start minikube" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Minikube is already running!" -ForegroundColor Green
}
Write-Host ""

# Build Docker images
if (-not $SkipBuild) {
    Write-Host "[3/9] Building Docker images..." -ForegroundColor Yellow
    Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow

    docker-compose build

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "Docker images built successfully!" -ForegroundColor Green
} else {
    Write-Host "[3/9] Skipping Docker build (--SkipBuild flag)" -ForegroundColor Yellow
}
Write-Host ""

# Load images into minikube
if (-not $SkipLoad) {
    Write-Host "[4/9] Loading Docker images into minikube..." -ForegroundColor Yellow
    Write-Host "This may take 3-5 minutes..." -ForegroundColor Yellow

    $images = @(
        "logistics-order-service:latest",
        "logistics-tracking-service:latest",
        "logistics-inventory-service:latest",
        "logistics-notification-service:latest",
        "logistics-api-gateway:latest",
        "logistics-dashboard:latest"
    )

    foreach ($image in $images) {
        Write-Host "  Loading $image..." -ForegroundColor Gray
        minikube image load $image
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to load image $image" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "All images loaded into minikube!" -ForegroundColor Green
} else {
    Write-Host "[4/9] Skipping image loading (--SkipLoad flag)" -ForegroundColor Yellow
}
Write-Host ""

# Create namespace
Write-Host "[5/9] Creating Kubernetes namespace..." -ForegroundColor Yellow
kubectl apply -f k8s/base/namespace/namespace.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create namespace" -ForegroundColor Red
    exit 1
}
Write-Host "Namespace created!" -ForegroundColor Green
Write-Host ""

# Deploy PostgreSQL
Write-Host "[6/9] Deploying PostgreSQL..." -ForegroundColor Yellow
kubectl apply -k k8s/base/postgresql/
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to deploy PostgreSQL" -ForegroundColor Red
    exit 1
}
Write-Host "PostgreSQL deployed!" -ForegroundColor Green
Write-Host ""

# Deploy RabbitMQ
Write-Host "[7/9] Deploying RabbitMQ..." -ForegroundColor Yellow
kubectl apply -k k8s/base/rabbitmq/
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to deploy RabbitMQ" -ForegroundColor Red
    exit 1
}
Write-Host "RabbitMQ deployed!" -ForegroundColor Green
Write-Host ""

# Wait for infrastructure to be ready
Write-Host "[8/9] Waiting for infrastructure to be ready..." -ForegroundColor Yellow
Write-Host "Waiting for PostgreSQL..." -ForegroundColor Gray
kubectl wait --for=condition=ready pod -l app=postgresql -n logistics-demo --timeout=300s
Write-Host "Waiting for RabbitMQ..." -ForegroundColor Gray
kubectl wait --for=condition=ready pod -l app=rabbitmq -n logistics-demo --timeout=300s
Write-Host "Infrastructure is ready!" -ForegroundColor Green
Write-Host ""

# Deploy microservices
Write-Host "[9/9] Deploying microservices..." -ForegroundColor Yellow

$services = @("order-service", "tracking-service", "inventory-service", "notification-service", "api-gateway", "dashboard")

foreach ($service in $services) {
    Write-Host "  Deploying $service..." -ForegroundColor Gray
    kubectl apply -k k8s/base/$service/
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to deploy $service" -ForegroundColor Red
        exit 1
    }
}
Write-Host "All microservices deployed!" -ForegroundColor Green
Write-Host ""

# Wait for services to be ready
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Write-Host "(This may take 2-3 minutes)" -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check deployment status
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Deployment Status                            " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
kubectl get pods -n logistics-demo

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Services                                      " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
kubectl get services -n logistics-demo

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Deployment Complete!                          " -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Check pod status: kubectl get pods -n logistics-demo" -ForegroundColor White
Write-Host "2. Access services via port-forward:" -ForegroundColor White
Write-Host "   kubectl port-forward -n logistics-demo svc/api-gateway 8000:8000" -ForegroundColor Gray
Write-Host "   kubectl port-forward -n logistics-demo svc/dashboard 8080:8080" -ForegroundColor Gray
Write-Host "3. View logs: kubectl logs -n logistics-demo <pod-name>" -ForegroundColor White
Write-Host "4. Run test workflow: .\scripts\test-kubernetes.ps1" -ForegroundColor White
Write-Host ""
Write-Host "For detailed instructions, see: KUBERNETES-GUIDE.md" -ForegroundColor Cyan
Write-Host ""
