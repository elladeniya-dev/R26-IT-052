<#
.SYNOPSIS
    Forwards all 4 backend ports from a USB-connected Android phone to
    this laptop, so the app can use 127.0.0.1 on the phone exactly like
    normal local dev — completely bypassing WiFi and IP addresses.

.NOTES
    Run this AFTER start_all_backends.ps1, with the phone plugged in
    via USB and USB debugging enabled + authorized (accept the "Allow
    USB debugging?" prompt on the phone the first time).

    Re-run this any time the phone gets unplugged and replugged — the
    port forwarding doesn't survive a USB disconnect.

    Requires `adb` on PATH (comes with the Android SDK / Flutter's
    Android toolchain — already installed if you can run Flutter
    Android builds).
#>

$ErrorActionPreference = "Stop"

$adbCheck = Get-Command adb -ErrorAction SilentlyContinue
if ($adbCheck) {
    $adb = "adb"
} else {
    # Not on PATH - fall back to the standard Android SDK install
    # location rather than failing outright.
    $fallback = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"
    if (Test-Path $fallback) {
        $adb = $fallback
    } else {
        Write-Host "adb not found on PATH or at $fallback." -ForegroundColor Red
        exit 1
    }
}

$devices = & $adb devices | Select-String "device$" | Where-Object { $_ -notmatch "List of devices" }

if (-not $devices) {
    Write-Host "No Android device detected." -ForegroundColor Red
    Write-Host "  1. Plug the phone in via USB." -ForegroundColor Yellow
    Write-Host "  2. Enable Developer Options + USB debugging on the phone." -ForegroundColor Yellow
    Write-Host "  3. Accept the 'Allow USB debugging?' prompt on the phone screen." -ForegroundColor Yellow
    exit 1
}

Write-Host "Device connected:" -ForegroundColor Green
$devices | ForEach-Object { Write-Host "  $_" }

Write-Host ""
Write-Host "Forwarding ports..." -ForegroundColor Cyan
$ports = @(8001, 8002, 8003, 8004)
foreach ($port in $ports) {
    & $adb reverse "tcp:$port" "tcp:$port"
    Write-Host "  phone:$port -> laptop:$port" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. The app can now reach all 4 backends via 127.0.0.1 on the phone." -ForegroundColor Green
Write-Host "Make sure Profile > Server Connection is set to default (empty) on the phone, not a LAN IP." -ForegroundColor DarkGray
