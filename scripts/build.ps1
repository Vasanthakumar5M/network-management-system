# Network Monitor - Build Script
# Builds the application for production

param(
    [switch]$Debug,
    [switch]$SkipFrontend,
    [switch]$SkipPython
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Network Monitor Build Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[WARNING] Not running as Administrator. Some features may not work." -ForegroundColor Yellow
}

# Set working directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Yellow

# Check Node.js
try {
    $nodeVersion = node --version
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check pnpm
try {
    $pnpmVersion = pnpm --version
    Write-Host "  pnpm: $pnpmVersion" -ForegroundColor Green
} catch {
    Write-Host "  Installing pnpm..." -ForegroundColor Yellow
    npm install -g pnpm
}

# Check Rust
try {
    $rustVersion = rustc --version
    Write-Host "  Rust: $rustVersion" -ForegroundColor Green
} catch {
    Write-Host "  Rust not found. Please install Rust from https://rustup.rs" -ForegroundColor Red
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version
    Write-Host "  Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/5] Installing frontend dependencies..." -ForegroundColor Yellow

if (-not $SkipFrontend) {
    pnpm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install frontend dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  Skipped" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[3/5] Installing Python dependencies..." -ForegroundColor Yellow

if (-not $SkipPython) {
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path "network_monitor_env")) {
        Write-Host "  Creating virtual environment..." -ForegroundColor Gray
        python -m venv network_monitor_env
    }

    # Activate and install
    & ".\network_monitor_env\Scripts\Activate.ps1"
    pip install -r python/requirements.txt -q
    Write-Host "  Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  Skipped" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[4/5] Type checking and linting..." -ForegroundColor Yellow

# TypeScript check
Write-Host "  Running TypeScript check..." -ForegroundColor Gray
pnpm tsc --noEmit
if ($LASTEXITCODE -ne 0) {
    Write-Host "  TypeScript errors found" -ForegroundColor Yellow
} else {
    Write-Host "  TypeScript: OK" -ForegroundColor Green
}

# Rust check
Write-Host "  Running Rust check..." -ForegroundColor Gray
Set-Location src-tauri
cargo check 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Rust errors found" -ForegroundColor Yellow
} else {
    Write-Host "  Rust: OK" -ForegroundColor Green
}
Set-Location ..

Write-Host ""
Write-Host "[5/5] Building application..." -ForegroundColor Yellow

if ($Debug) {
    Write-Host "  Building in debug mode..." -ForegroundColor Gray
    pnpm tauri build --debug
} else {
    Write-Host "  Building in release mode..." -ForegroundColor Gray
    pnpm tauri build
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output location:" -ForegroundColor Cyan
Write-Host "  Executable: src-tauri/target/release/network-monitor.exe"
Write-Host "  Installer:  src-tauri/target/release/bundle/"
Write-Host ""
