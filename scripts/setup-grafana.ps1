# Setup Grafana Dashboard and Datasource
Write-Host "Setting up Grafana..." -ForegroundColor Cyan

$grafanaUrl = "http://localhost:3000"
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:admin"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Wait for Grafana to be ready
Write-Host "Waiting for Grafana to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if datasource exists
Write-Host "Checking Prometheus datasource..." -ForegroundColor Yellow
try {
    $datasources = Invoke-RestMethod -Uri "$grafanaUrl/api/datasources" -Headers $headers -Method Get
    $prometheusDS = $datasources | Where-Object { $_.name -eq "Prometheus" }

    if ($prometheusDS) {
        Write-Host "Prometheus datasource already exists" -ForegroundColor Green
    } else {
        Write-Host "Creating Prometheus datasource..." -ForegroundColor Yellow
        $dsBody = @{
            name = "Prometheus"
            type = "prometheus"
            url = "http://prometheus:9090"
            access = "proxy"
            isDefault = $true
            jsonData = @{
                timeInterval = "5s"
            }
        } | ConvertTo-Json

        Invoke-RestMethod -Uri "$grafanaUrl/api/datasources" -Headers $headers -Method Post -Body $dsBody
        Write-Host "Prometheus datasource created" -ForegroundColor Green
    }
}
catch {
    Write-Host "Could not configure datasource: $_" -ForegroundColor Yellow
}

# Import dashboard
Write-Host "`nImporting dashboard..." -ForegroundColor Yellow
try {
    $dashboardJson = Get-Content "monitoring/grafana/dashboards/logistics-overview.json" -Raw | ConvertFrom-Json

    $importBody = @{
        dashboard = $dashboardJson.dashboard
        overwrite = $true
        inputs = @()
        folderId = 0
    } | ConvertTo-Json -Depth 100

    $result = Invoke-RestMethod -Uri "$grafanaUrl/api/dashboards/db" -Headers $headers -Method Post -Body $importBody
    Write-Host "Dashboard imported successfully!" -ForegroundColor Green
    Write-Host "URL: $grafanaUrl$($result.url)" -ForegroundColor Cyan
}
catch {
    Write-Host "Could not import dashboard: $_" -ForegroundColor Yellow
    Write-Host "You can manually import the dashboard from: monitoring/grafana/dashboards/logistics-overview.json" -ForegroundColor Yellow
}

Write-Host "`nGrafana setup complete!" -ForegroundColor Green
Write-Host "Access Grafana at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Username: admin" -ForegroundColor Cyan
Write-Host "Password: admin" -ForegroundColor Cyan
