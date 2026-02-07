# Network Monitor - Run as Admin Script
# Elevates privileges and runs the application

param(
    [string]$Mode = "normal",
    [switch]$Dev
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath

# Check if already admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    
    # Build arguments
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    if ($Mode) { $arguments += " -Mode $Mode" }
    if ($Dev) { $arguments += " -Dev" }
    
    # Restart as admin
    Start-Process PowerShell -ArgumentList $arguments -Verb RunAs
    exit
}

# We're running as admin now
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Network Monitor (Administrator)" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $projectRoot

# Activate Python environment
if (Test-Path "network_monitor_env\Scripts\Activate.ps1") {
    Write-Host "Activating Python environment..." -ForegroundColor Gray
    & ".\network_monitor_env\Scripts\Activate.ps1"
}

# Run based on mode
switch ($Mode) {
    "dev" {
        Write-Host "Starting development server..." -ForegroundColor Green
        pnpm tauri dev
    }
    "stealth" {
        Write-Host "Starting in stealth mode..." -ForegroundColor Green
        # Apply stealth settings first
        python -c "from python.stealth.mac_changer import MacChanger; MacChanger().apply_profile('hp_printer')"
        pnpm tauri dev
    }
    "capture-only" {
        Write-Host "Starting capture only (no UI)..." -ForegroundColor Green
        python python/main.py --mode capture
    }
    "proxy-only" {
        Write-Host "Starting HTTPS proxy only..." -ForegroundColor Green
        python python/https/transparent_proxy.py
    }
    "cert-server" {
        Write-Host "Starting certificate server..." -ForegroundColor Green
        python cert-installer/server.py
    }
    default {
        if ($Dev) {
            Write-Host "Starting development server..." -ForegroundColor Green
            pnpm tauri dev
        } else {
            # Check if built executable exists
            $exePath = "src-tauri\target\release\network-monitor.exe"
            if (Test-Path $exePath) {
                Write-Host "Starting Network Monitor..." -ForegroundColor Green
                Start-Process $exePath
            } else {
                Write-Host "Built executable not found. Running in dev mode..." -ForegroundColor Yellow
                pnpm tauri dev
            }
        }
    }
}
