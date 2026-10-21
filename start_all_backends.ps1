<#
.SYNOPSIS
    Starts all 4 OutfitIQ backend services for a live demo, each in its
    own visible window, bound to 0.0.0.0.

.NOTES
    Safe to re-run: clears any stale process already holding one of the
    4 target ports before starting fresh ones. Run stop_all_backends.ps1
    to shut everything down afterward.

    For a demo on a real Android phone, run connect_phone.ps1 next
    (after plugging the phone in via USB) — it sets up `adb reverse` so
    the phone reaches these backends via 127.0.0.1, with no IP address
    or WiFi network to worry about at all.

    Only if USB isn't available: set the laptop's LAN IP from
    Profile > Server Connection inside the app itself (no rebuild
    needed), and make sure Windows Firewall allows inbound TCP
    8001-8004 and the phone is on the same WiFi network.
#>

$ErrorActionPreference = "Stop"
$repoRoot = $PSScriptRoot

$services = @(
    @{
        Name   = "Chala (auth / preferences / learning)"
        Dir    = Join-Path $repoRoot "auth-backend"
        Port   = 8001
    },
    @{
        Name   = "Koji (data collection / recommendations)"
        Dir    = Join-Path $repoRoot "recommendation-backend"
        Port   = 8002
    },
    @{
        Name   = "Givi (trend analysis)"
        # Runs from the in-repo trend-engine/ folder like the other services.
        # It needs its own venv and .env (copy .env.example and fill in
        # DATABASE_URL); the script skips it with a message if the venv is missing.
        Dir    = Join-Path $repoRoot "trend-engine"
        Port   = 8003
    },
    @{
        Name   = "Senu (outfit compatibility)"
        Dir    = Join-Path $repoRoot "outfitcompatibility-engine"
        Port   = 8004
    }
)

Write-Host "== Clearing any stale process on target ports ==" -ForegroundColor Cyan
foreach ($service in $services) {
    $existing = Get-NetTCPConnection -LocalPort $service.Port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $existing) {
        Write-Host "  Port $($service.Port): stopping stale process $($conn.OwningProcess)" -ForegroundColor Yellow
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "== Starting all 4 backends ==" -ForegroundColor Cyan
foreach ($service in $services) {
    $venvPython = Join-Path $service.Dir "venv\Scripts\python.exe"

    if (-not (Test-Path $venvPython)) {
        Write-Host "  SKIPPED $($service.Name): no venv found at $venvPython" -ForegroundColor Red
        continue
    }

    Write-Host "  Starting $($service.Name) on port $($service.Port)..." -ForegroundColor Green

    $argList = @(
        "-NoExit",
        "-Command",
        "cd '$($service.Dir)'; & '$venvPython' -m uvicorn app.main:app --host 0.0.0.0 --port $($service.Port)"
    )
    Start-Process powershell -ArgumentList $argList -WindowStyle Normal
}

Write-Host ""
Write-Host "== Waiting for services to come up ==" -ForegroundColor Cyan
Write-Host "  (Senu loads a PyTorch model on startup - this takes longer than the others)" -ForegroundColor DarkGray
Start-Sleep -Seconds 18

Write-Host ""
Write-Host "== Health check ==" -ForegroundColor Cyan
$anyFailed = $false
foreach ($service in $services) {
    $url = "http://127.0.0.1:$($service.Port)/docs"
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "  OK   $($service.Name) - port $($service.Port)" -ForegroundColor Green
        } else {
            Write-Host "  FAIL $($service.Name) - port $($service.Port) - status $($response.StatusCode)" -ForegroundColor Red
            $anyFailed = $true
        }
    } catch {
        Write-Host "  FAIL $($service.Name) - port $($service.Port) - not responding" -ForegroundColor Red
        $anyFailed = $true
    }
}

Write-Host ""
if ($anyFailed) {
    Write-Host "One or more services failed to start - check their PowerShell windows for the error." -ForegroundColor Red
} else {
    Write-Host "All 4 backends are up." -ForegroundColor Green
}
