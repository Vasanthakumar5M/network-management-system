<#
.SYNOPSIS
    Npcap Installation Helper

.DESCRIPTION
    Downloads and assists with Npcap installation, which is required for packet capture.

.NOTES
    Author: Network Monitor
    Version: 1.0.0
#>

$ErrorActionPreference = "Stop"

Write-Host @"

    Npcap Installation Helper
    =========================
    
    Npcap is required for packet capture on Windows.
    This script will download and run the Npcap installer.

"@ -ForegroundColor Cyan

# Check if already installed
$npcapInstalled = Test-Path "C:\Program Files\Npcap\NPFInstall.exe"
if ($npcapInstalled) {
    Write-Host "Npcap is already installed!" -ForegroundColor Green
    
    $reinstall = Read-Host "Do you want to reinstall/update? (y/N)"
    if ($reinstall -ne 'y' -and $reinstall -ne 'Y') {
        exit 0
    }
}

# Check for admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNING: Running as non-admin. Npcap installer will request elevation." -ForegroundColor Yellow
}

# Download Npcap
Write-Host "`nDownloading Npcap..." -ForegroundColor Cyan

$npcapVersion = "1.79"
$npcapUrl = "https://npcap.com/dist/npcap-$npcapVersion.exe"
$npcapInstaller = "$env:TEMP\npcap-$npcapVersion.exe"

try {
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri $npcapUrl -OutFile $npcapInstaller -UseBasicParsing
    Write-Host "Downloaded to: $npcapInstaller" -ForegroundColor Green
} catch {
    Write-Host "Failed to download Npcap: $_" -ForegroundColor Red
    Write-Host "`nPlease download manually from: https://npcap.com/#download" -ForegroundColor Yellow
    exit 1
}

# Installation instructions
Write-Host @"

    IMPORTANT: Installation Options
    ================================
    
    During the Npcap installation, please select these options:
    
    [REQUIRED] 
      - Install Npcap in WinPcap API-compatible Mode
        (Enables compatibility with Scapy and other tools)
    
    [RECOMMENDED]
      - Support raw 802.11 traffic (and target scanning tools)
        (Enables WiFi packet capture)
    
    [OPTIONAL]
      - Restrict Npcap driver's access to Administrators only
        (More secure, but limits non-admin access)

"@ -ForegroundColor Yellow

$proceed = Read-Host "Press Enter to start installation, or 'q' to quit"
if ($proceed -eq 'q') {
    Remove-Item $npcapInstaller -ErrorAction SilentlyContinue
    exit 0
}

# Run installer
Write-Host "`nStarting Npcap installer..." -ForegroundColor Cyan
Start-Process -FilePath $npcapInstaller -Wait

# Verify installation
$npcapInstalled = Test-Path "C:\Program Files\Npcap\NPFInstall.exe"
if ($npcapInstalled) {
    Write-Host "`nNpcap installed successfully!" -ForegroundColor Green
    
    # Get version
    $npcapDll = "C:\Windows\System32\Npcap\wpcap.dll"
    if (Test-Path $npcapDll) {
        $version = (Get-Item $npcapDll).VersionInfo.ProductVersion
        Write-Host "Version: $version" -ForegroundColor Gray
    }
} else {
    Write-Host "`nNpcap installation may have been cancelled or failed." -ForegroundColor Yellow
    Write-Host "Please try again or download manually from: https://npcap.com/#download" -ForegroundColor Yellow
}

# Cleanup
Remove-Item $npcapInstaller -ErrorAction SilentlyContinue

Write-Host "`nDone!" -ForegroundColor Green
