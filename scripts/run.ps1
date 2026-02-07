#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Network Monitor Run Script

.DESCRIPTION
    Starts the Network Monitor application and all required services.
    Must be run as Administrator for packet capture.

.PARAMETER Mode
    Run mode: "full" (default), "proxy-only", "capture-only", "cert-server"

.PARAMETER Debug
    Enable debug logging

.NOTES
    Author: Network Monitor
    Version: 1.0.0
#>

param(
    [ValidateSet("full", "proxy-only", "capture-only", "cert-server")]
    [string]$Mode = "full",
    [switch]$Debug,
    [switch]$NoUI
)

$ErrorActionPreference = "Stop"

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

Write-Step "Mode: $Mode"
Write-Info "Project: $ProjectRoot"

# ============================================
# Activate Virtual Environment
# ============================================
$venvPath = Join-Path $ProjectRoot "network_monitor_env"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    & $activateScript
    Write-Success "Virtual environment activated"
} else {
    Write-Warning "Virtual environment not found. Run install.ps1 first."
}

# ============================================
# Check Npcap
# ============================================
if ($Mode -in @("full", "capture-only")) {
    if (-not (Test-Path "C:\Program Files\Npcap\NPFInstall.exe")) {
        Write-Error "Npcap is not installed! Packet capture will not work."
        Write-Info "Download from: https://npcap.com/#download"
        if ($Mode -eq "capture-only") {
            exit 1
        }
    }
}

# ============================================
# Check Certificate
# ============================================
$certPath = Join-Path $ProjectRoot "certs\ca-cert.pem"
if (-not (Test-Path $certPath)) {
    Write-Warning "CA certificate not found. Generating..."
    
    $certScript = Join-Path $ProjectRoot "python\https\cert_generator.py"
    if (Test-Path $certScript) {
        python $certScript --output (Join-Path $ProjectRoot "certs")
        Write-Success "Certificate generated"
    } else {
        Write-Error "Certificate generator not found!"
    }
}

# ============================================
# Get Network Interface
# ============================================
Write-Step "Detecting network interface..."

$networkAdapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" -and $_.InterfaceDescription -notmatch "Loopback|Virtual|Hyper-V" }
if ($networkAdapters.Count -eq 0) {
    Write-Error "No active network adapters found!"
    exit 1
}

$primaryAdapter = $networkAdapters | Sort-Object -Property { $_.InterfaceMetric } | Select-Object -First 1
$interfaceName = $primaryAdapter.Name
$interfaceIndex = $primaryAdapter.InterfaceIndex

# Get IP configuration
$ipConfig = Get-NetIPConfiguration -InterfaceIndex $interfaceIndex
$localIP = ($ipConfig.IPv4Address | Select-Object -First 1).IPAddress
$gateway = ($ipConfig.IPv4DefaultGateway | Select-Object -First 1).NextHop

Write-Success "Interface: $interfaceName"
Write-Info "Local IP: $localIP"
Write-Info "Gateway: $gateway"

# ============================================
# Process Management
# ============================================
$global:processes = @()

function Start-BackgroundProcess {
    param(
        [string]$Name,
        [string]$Command,
        [string]$Arguments,
        [string]$WorkingDirectory = $ProjectRoot
    )
    
    Write-Info "Starting $Name..."
    
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Command
    $psi.Arguments = $Arguments
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    
    $process = [System.Diagnostics.Process]::Start($psi)
    $global:processes += @{Name=$Name; Process=$process}
    
    Write-Success "$Name started (PID: $($process.Id))"
    return $process
}

function Stop-AllProcesses {
    Write-Step "Stopping all processes..."
    foreach ($p in $global:processes) {
        if (-not $p.Process.HasExited) {
            Write-Info "Stopping $($p.Name) (PID: $($p.Process.Id))..."
            $p.Process.Kill()
        }
    }
    Write-Success "All processes stopped"
}

# Register cleanup on exit
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Stop-AllProcesses }

# Ctrl+C handler
[Console]::TreatControlCAsInput = $false
$null = [Console]::CancelKeyPress.Add({
    param($sender, $e)
    $e.Cancel = $true
    Write-Host "`nShutting down..." -ForegroundColor Yellow
    Stop-AllProcesses
    exit 0
})

# ============================================
# Start Services Based on Mode
# ============================================

try {
    switch ($Mode) {
        "full" {
            # Start Certificate Installer Server
            $certInstallerScript = Join-Path $ProjectRoot "cert-installer\server.py"
            if (Test-Path $certInstallerScript) {
                Start-BackgroundProcess -Name "CertInstaller" -Command "python" -Arguments $certInstallerScript
            }
            
            # Start HTTPS Proxy (mitmproxy)
            $proxyScript = Join-Path $ProjectRoot "python\https\transparent_proxy.py"
            if (Test-Path $proxyScript) {
                $proxyArgs = "--interface $interfaceName"
                if ($Debug) { $proxyArgs += " --debug" }
                Start-BackgroundProcess -Name "HTTPSProxy" -Command "python" -Arguments "$proxyScript $proxyArgs"
            }
            
            # Start ARP Gateway
            $arpScript = Join-Path $ProjectRoot "python\arp\arp_gateway.py"
            if (Test-Path $arpScript) {
                Start-BackgroundProcess -Name "ARPGateway" -Command "python" -Arguments "$arpScript --interface $interfaceName --gateway $gateway"
            }
            
            # Start DNS Capture
            $dnsScript = Join-Path $ProjectRoot "python\dns\dns_capture.py"
            if (Test-Path $dnsScript) {
                Start-BackgroundProcess -Name "DNSCapture" -Command "python" -Arguments "$dnsScript --interface $interfaceName"
            }
            
            # Start Tauri App (if not NoUI)
            if (-not $NoUI) {
                $tauriApp = Join-Path $ProjectRoot "src-tauri\target\release\network-monitor.exe"
                if (Test-Path $tauriApp) {
                    Start-BackgroundProcess -Name "TauriApp" -Command $tauriApp -Arguments ""
                } else {
                    Write-Warning "Tauri app not built. Run 'pnpm tauri build' first."
                }
            }
        }
        
        "proxy-only" {
            $proxyScript = Join-Path $ProjectRoot "python\https\transparent_proxy.py"
            if (Test-Path $proxyScript) {
                $proxyArgs = "--interface $interfaceName"
                if ($Debug) { $proxyArgs += " --debug" }
                Start-BackgroundProcess -Name "HTTPSProxy" -Command "python" -Arguments "$proxyScript $proxyArgs"
            }
        }
        
        "capture-only" {
            # Start ARP Gateway
            $arpScript = Join-Path $ProjectRoot "python\arp\arp_gateway.py"
            if (Test-Path $arpScript) {
                Start-BackgroundProcess -Name "ARPGateway" -Command "python" -Arguments "$arpScript --interface $interfaceName --gateway $gateway"
            }
            
            # Start DNS Capture
            $dnsScript = Join-Path $ProjectRoot "python\dns\dns_capture.py"
            if (Test-Path $dnsScript) {
                Start-BackgroundProcess -Name "DNSCapture" -Command "python" -Arguments "$dnsScript --interface $interfaceName"
            }
        }
        
        "cert-server" {
            $certInstallerScript = Join-Path $ProjectRoot "cert-installer\server.py"
            if (Test-Path $certInstallerScript) {
                Start-BackgroundProcess -Name "CertInstaller" -Command "python" -Arguments $certInstallerScript
            }
        }
    }
    
    # ============================================
    # Display Status
    # ============================================
    Write-Host "`n" + "="*60 -ForegroundColor Green
    Write-Host "  Network Monitor Running" -ForegroundColor Green
    Write-Host "="*60 -ForegroundColor Green
    
    Write-Host "`nActive Services:" -ForegroundColor Yellow
    foreach ($p in $global:processes) {
        $status = if ($p.Process.HasExited) { "Stopped" } else { "Running" }
        $color = if ($p.Process.HasExited) { "Red" } else { "Green" }
        Write-Host "  - $($p.Name): " -NoNewline
        Write-Host $status -ForegroundColor $color
    }
    
    Write-Host "`nEndpoints:" -ForegroundColor Yellow
    Write-Host "  Certificate Installer: http://$($localIP):8888" -ForegroundColor Cyan
    Write-Host "  Proxy: http://$($localIP):8080" -ForegroundColor Cyan
    
    Write-Host "`nPress Ctrl+C to stop all services..." -ForegroundColor Gray
    
    # Keep script running
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Check if any process has exited unexpectedly
        foreach ($p in $global:processes) {
            if ($p.Process.HasExited -and $p.Process.ExitCode -ne 0) {
                Write-Warning "$($p.Name) exited with code $($p.Process.ExitCode)"
            }
        }
    }
    
} catch {
    Write-Error "Error: $_"
    Stop-AllProcesses
    exit 1
} finally {
    Stop-AllProcesses
}
