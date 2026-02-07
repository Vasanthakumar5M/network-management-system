#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Network Monitor Installation Script

.DESCRIPTION
    Installs all dependencies and configures the Network Monitor application.
    Must be run as Administrator.

.NOTES
    Author: Network Monitor
    Version: 1.0.0
#>

param(
    [switch]$SkipNpcap,
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$SkipRust,
    [switch]$Silent
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Colors
function Write-Step { param($msg) Write-Host "`n[*] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[-] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "    $msg" -ForegroundColor Gray }

# Banner
Write-Host @"

    _   _      _                      _      __  __             _ _             
   | \ | | ___| |___      _____  _ __| | __ |  \/  | ___  _ __ (_) |_ ___  _ __ 
   |  \| |/ _ \ __\ \ /\ / / _ \| '__| |/ / | |\/| |/ _ \| '_ \| | __/ _ \| '__|
   | |\  |  __/ |_ \ V  V / (_) | |  |   <  | |  | | (_) | | | | | || (_) | |   
   |_| \_|\___|\__| \_/\_/ \___/|_|  |_|\_\ |_|  |_|\___/|_| |_|_|\__\___/|_|   
                                                                                
                        Installation Script v1.0.0
"@ -ForegroundColor Magenta

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "This script must be run as Administrator!"
    Write-Info "Right-click PowerShell and select 'Run as Administrator'"
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Step "Project directory: $ProjectRoot"

# ============================================
# Check Windows Version
# ============================================
Write-Step "Checking Windows version..."
$osVersion = [System.Environment]::OSVersion.Version
if ($osVersion.Major -lt 10) {
    Write-Error "Windows 10 or later is required"
    exit 1
}
Write-Success "Windows $($osVersion.Major).$($osVersion.Minor) detected"

# ============================================
# Install Chocolatey (if not installed)
# ============================================
Write-Step "Checking for Chocolatey..."
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Info "Installing Chocolatey..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    Write-Success "Chocolatey installed"
} else {
    Write-Success "Chocolatey already installed"
}

# ============================================
# Install Npcap
# ============================================
if (-not $SkipNpcap) {
    Write-Step "Checking for Npcap..."
    
    $npcapInstalled = Test-Path "C:\Program Files\Npcap\NPFInstall.exe"
    if (-not $npcapInstalled) {
        Write-Info "Downloading Npcap..."
        
        $npcapUrl = "https://npcap.com/dist/npcap-1.79.exe"
        $npcapInstaller = "$env:TEMP\npcap-installer.exe"
        
        try {
            Invoke-WebRequest -Uri $npcapUrl -OutFile $npcapInstaller -UseBasicParsing
            
            Write-Info "Installing Npcap (this requires user interaction)..."
            Write-Warning "IMPORTANT: During installation, check these options:"
            Write-Warning "  - Install Npcap in WinPcap API-compatible Mode"
            Write-Warning "  - Support raw 802.11 traffic (optional)"
            
            Start-Process -FilePath $npcapInstaller -Wait
            
            if (Test-Path "C:\Program Files\Npcap\NPFInstall.exe") {
                Write-Success "Npcap installed successfully"
            } else {
                Write-Warning "Npcap installation may have been cancelled"
            }
        } catch {
            Write-Error "Failed to download Npcap: $_"
            Write-Info "Please download manually from https://npcap.com/#download"
        } finally {
            Remove-Item $npcapInstaller -ErrorAction SilentlyContinue
        }
    } else {
        Write-Success "Npcap already installed"
    }
}

# ============================================
# Install Python
# ============================================
if (-not $SkipPython) {
    Write-Step "Checking for Python..."
    
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python -or $python.Version.Major -lt 3 -or ($python.Version.Major -eq 3 -and $python.Version.Minor -lt 10)) {
        Write-Info "Installing Python 3.11..."
        choco install python311 -y
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        Write-Success "Python installed"
    } else {
        Write-Success "Python $($python.Version) already installed"
    }
}

# ============================================
# Install Node.js
# ============================================
if (-not $SkipNode) {
    Write-Step "Checking for Node.js..."
    
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) {
        Write-Info "Installing Node.js LTS..."
        choco install nodejs-lts -y
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        Write-Success "Node.js installed"
    } else {
        $nodeVersion = & node --version
        Write-Success "Node.js $nodeVersion already installed"
    }
    
    # Install pnpm
    Write-Step "Checking for pnpm..."
    if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
        Write-Info "Installing pnpm..."
        npm install -g pnpm
        Write-Success "pnpm installed"
    } else {
        Write-Success "pnpm already installed"
    }
}

# ============================================
# Install Rust
# ============================================
if (-not $SkipRust) {
    Write-Step "Checking for Rust..."
    
    $cargo = Get-Command cargo -ErrorAction SilentlyContinue
    if (-not $cargo) {
        Write-Info "Installing Rust..."
        
        $rustupInit = "$env:TEMP\rustup-init.exe"
        Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile $rustupInit -UseBasicParsing
        
        Start-Process -FilePath $rustupInit -ArgumentList "-y" -Wait
        
        # Add Rust to PATH
        $env:Path += ";$env:USERPROFILE\.cargo\bin"
        [System.Environment]::SetEnvironmentVariable("Path", $env:Path, "User")
        
        Remove-Item $rustupInit -ErrorAction SilentlyContinue
        Write-Success "Rust installed"
    } else {
        $rustVersion = & rustc --version
        Write-Success "Rust already installed: $rustVersion"
    }
}

# ============================================
# Create Python Virtual Environment
# ============================================
Write-Step "Setting up Python virtual environment..."

$venvPath = Join-Path $ProjectRoot "network_monitor_env"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
    Write-Success "Virtual environment created at $venvPath"
} else {
    Write-Success "Virtual environment already exists"
}

# Activate and install dependencies
Write-Step "Installing Python dependencies..."
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
& $activateScript

$pythonReqs = Join-Path $ProjectRoot "python\requirements.txt"
if (Test-Path $pythonReqs) {
    pip install -r $pythonReqs
    Write-Success "Python dependencies installed"
} else {
    Write-Warning "requirements.txt not found at $pythonReqs"
}

$certInstallerReqs = Join-Path $ProjectRoot "cert-installer\requirements.txt"
if (Test-Path $certInstallerReqs) {
    pip install -r $certInstallerReqs
    Write-Success "Certificate installer dependencies installed"
}

# ============================================
# Install Node.js Dependencies
# ============================================
Write-Step "Installing Node.js dependencies..."
Push-Location $ProjectRoot
if (Test-Path "package.json") {
    pnpm install
    Write-Success "Node.js dependencies installed"
} else {
    Write-Warning "package.json not found - skipping Node.js dependencies"
}
Pop-Location

# ============================================
# Create Required Directories
# ============================================
Write-Step "Creating required directories..."

$directories = @(
    "database",
    "logs",
    "certs",
    "backups"
)

foreach ($dir in $directories) {
    $path = Join-Path $ProjectRoot $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Info "Created: $dir/"
    }
}
Write-Success "Directories created"

# ============================================
# Configure Windows Firewall
# ============================================
Write-Step "Configuring Windows Firewall..."

$firewallRules = @(
    @{Name="NetworkMonitor-Proxy"; Port=8080; Description="Network Monitor HTTPS Proxy"},
    @{Name="NetworkMonitor-CertInstaller"; Port=8888; Description="Network Monitor Certificate Installer"}
)

foreach ($rule in $firewallRules) {
    $existingRule = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue
    if (-not $existingRule) {
        New-NetFirewallRule -DisplayName $rule.Name -Direction Inbound -Protocol TCP -LocalPort $rule.Port -Action Allow -Description $rule.Description | Out-Null
        Write-Info "Created firewall rule: $($rule.Name)"
    }
}
Write-Success "Firewall configured"

# ============================================
# Summary
# ============================================
Write-Host "`n" + "="*60 -ForegroundColor Magenta
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Magenta

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Generate SSL certificate:" -ForegroundColor White
Write-Host "     python python/https/cert_generator.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Start the application:" -ForegroundColor White
Write-Host "     .\scripts\run.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Set up certificate on target devices:" -ForegroundColor White
Write-Host "     Navigate to http://<your-ip>:8888" -ForegroundColor Gray
Write-Host ""

if (-not $SkipNpcap -and -not (Test-Path "C:\Program Files\Npcap\NPFInstall.exe")) {
    Write-Warning "Npcap was not detected. Packet capture will not work without it."
    Write-Info "Download from: https://npcap.com/#download"
}

Write-Host "`nProject location: $ProjectRoot" -ForegroundColor Cyan
Write-Host ""
