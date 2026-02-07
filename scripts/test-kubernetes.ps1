# Test Kubernetes Deployment Script
# This script tests the logistics platform running in Kubernetes

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Kubernetes Deployment Test                   " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if services are running
Write-Host "[1/5] Checking pod status..." -ForegroundColor Yellow
$pods = kubectl get pods -n logistics-demo --no-headers 2>$null

if (-not $pods) {
    Write-Host "ERROR: No pods found in logistics-demo namespace" -ForegroundColor Red
    Write-Host "Please run: .\scripts\deploy-kubernetes.ps1" -ForegroundColor Red
    exit 1
}

$runningPods = ($pods | Select-String "Running" | Measure-Object).Count
$totalPods = ($pods | Measure-Object).Count

Write-Host "Pods running: $runningPods/$totalPods" -ForegroundColor Green
Write-Host ""

# Start port-forward in background
Write-Host "[2/5] Setting up port forwarding..." -ForegroundColor Yellow
Write-Host "Starting port-forward for API Gateway (port 8000)..." -ForegroundColor Gray

$portForwardJob = Start-Job -ScriptBlock {
    kubectl port-forward -n logistics-demo svc/api-gateway 8000:8000
}

Start-Sleep -Seconds 5
Write-Host "Port forwarding established!" -ForegroundColor Green
Write-Host ""

try {
    # Test health endpoints
    Write-Host "[3/5] Testing health endpoints..." -ForegroundColor Yellow

    $services = @(
        @{Name="API Gateway"; Port=8000}
    )

    foreach ($svc in $services) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$($svc.Port)/health" -TimeoutSec 5
            Write-Host "  $($svc.Name): HEALTHY" -ForegroundColor Green
        } catch {
            Write-Host "  $($svc.Name): UNHEALTHY" -ForegroundColor Red
        }
    }
    Write-Host ""

    # Create test order
    Write-Host "[4/5] Creating test order..." -ForegroundColor Yellow

    $orderData = @{
        customer_name = "Test User K8s"
        customer_email = "test@kubernetes.local"
        origin_address = "123 K8s St, Container City"
        destination_address = "456 Pod Ave, Cluster Town"
        package_weight = 10.5
        package_dimensions = "40x30x20"
        items = @(
            @{
                item_name = "Kubernetes Book"
                quantity = 1
                sku = "K8S-BOOK-001"
            }
        )
    } | ConvertTo-Json -Depth 10

    try {
        $order = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/orders" -Method Post -Body $orderData -ContentType "application/json"
        Write-Host "Order created successfully!" -ForegroundColor Green
        Write-Host "Order Number: $($order.order_number)" -ForegroundColor Cyan
        Write-Host "Order ID: $($order.id)" -ForegroundColor Cyan
    } catch {
        Write-Host "Failed to create order: $_" -ForegroundColor Red
    }
    Write-Host ""

    # Check Kubernetes-specific features
    Write-Host "[5/5] Checking Kubernetes features..." -ForegroundColor Yellow

    # Check HPA status
    Write-Host "Horizontal Pod Autoscalers:" -ForegroundColor Gray
    kubectl get hpa -n logistics-demo

    Write-Host ""
    Write-Host "Resource Usage:" -ForegroundColor Gray
    kubectl top pods -n logistics-demo 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  (Metrics server not available - this is normal for new clusters)" -ForegroundColor Yellow
    }

} finally {
    # Clean up port-forward
    Write-Host ""
    Write-Host "Cleaning up port-forward..." -ForegroundColor Yellow
    Stop-Job $portForwardJob -ErrorAction SilentlyContinue
    Remove-Job $portForwardJob -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Test Complete!                                " -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "To access services manually:" -ForegroundColor Cyan
Write-Host "  kubectl port-forward -n logistics-demo svc/api-gateway 8000:8000" -ForegroundColor White
Write-Host "  kubectl port-forward -n logistics-demo svc/dashboard 8080:8080" -ForegroundColor White
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  kubectl logs -n logistics-demo -l app=order-service" -ForegroundColor White
Write-Host ""
Write-Host "To scale services:" -ForegroundColor Cyan
Write-Host "  kubectl scale deployment order-service -n logistics-demo --replicas=3" -ForegroundColor White
Write-Host ""
