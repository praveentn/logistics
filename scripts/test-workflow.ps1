# PowerShell Test Script for Logistics Order Workflow

Write-Host "=== Logistics Order Workflow Test ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8001"

# Step 1: Check service health
Write-Host "Step 1: Checking service health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    $health | ConvertTo-Json -Depth 10 | Write-Host
    Write-Host ""
}
catch {
    Write-Host "ERROR: Service health check failed. Is the order service running?" -ForegroundColor Red
    Write-Host "Run: docker-compose ps" -ForegroundColor Red
    exit 1
}

# Step 2: Create a test order
Write-Host "Step 2: Creating a test order..." -ForegroundColor Yellow
$orderData = @{
    customer_name = "John Doe"
    customer_email = "john.doe@example.com"
    origin_address = "123 Main St, New York, NY 10001"
    destination_address = "456 Oak Ave, Los Angeles, CA 90001"
    package_weight = 5.5
    package_dimensions = "30x20x15"
    items = @(
        @{
            item_name = "Laptop"
            quantity = 1
            sku = "LAPTOP-001"
        },
        @{
            item_name = "Mouse"
            quantity = 2
            sku = "MOUSE-001"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $orderResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/orders" -Method Post -Body $orderData -ContentType "application/json"
    $orderResponse | ConvertTo-Json -Depth 10 | Write-Host
    $orderId = $orderResponse.id
    $orderNumber = $orderResponse.order_number
    Write-Host ""
    Write-Host "✓ Order created: $orderNumber" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "ERROR: Failed to create order" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Step 3: Retrieve order details
Write-Host "Step 3: Retrieving order details..." -ForegroundColor Yellow
$orderDetails = Invoke-RestMethod -Uri "$baseUrl/api/v1/orders/$orderId" -Method Get
$orderDetails | ConvertTo-Json -Depth 10 | Write-Host
Write-Host ""

# Step 4: List all orders
Write-Host "Step 4: Listing all orders..." -ForegroundColor Yellow
$ordersList = Invoke-RestMethod -Uri "$baseUrl/api/v1/orders?page=1&page_size=10" -Method Get
$ordersList | ConvertTo-Json -Depth 10 | Write-Host
Write-Host ""

# Step 5: Update order status
Write-Host "Step 5: Updating order status..." -ForegroundColor Yellow
$updateData = @{
    status = "processing"
} | ConvertTo-Json

$updateResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/orders/$orderId/status" -Method Put -Body $updateData -ContentType "application/json"
$updateResponse | ConvertTo-Json -Depth 10 | Write-Host
Write-Host ""
Write-Host "✓ Order status updated to 'processing'" -ForegroundColor Green
Write-Host ""

# Step 6: Get order items
Write-Host "Step 6: Getting order items..." -ForegroundColor Yellow
$items = Invoke-RestMethod -Uri "$baseUrl/api/v1/orders/$orderId/items" -Method Get
$items | ConvertTo-Json -Depth 10 | Write-Host
Write-Host ""

# Summary
Write-Host "=== Workflow Test Completed Successfully! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  - Order Number: $orderNumber"
Write-Host "  - Order ID: $orderId"
Write-Host "  - Status: processing"
Write-Host "  - Items: $($items.Count)"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  - Check RabbitMQ management UI: http://localhost:15672 (admin/admin_password_123)"
Write-Host "  - View Prometheus metrics: http://localhost:9090"
Write-Host "  - Check Grafana dashboards: http://localhost:3000 (admin/admin)"
Write-Host "  - Check service logs: docker-compose logs -f order-service"
