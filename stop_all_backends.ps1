<#
.SYNOPSIS
    Stops all 4 OutfitIQ backend services (whatever is listening on
    8001-8004), for a clean shutdown after a demo.
#>

$ports = @(8001, 8002, 8003, 8004)

foreach ($port in $ports) {
    $existing = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $existing) {
        Write-Host "Stopping process on port $port (PID $($conn.OwningProcess))" -ForegroundColor Yellow
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Done." -ForegroundColor Green
