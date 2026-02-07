<#
.SYNOPSIS
    Generate CA Certificate for HTTPS Interception

.DESCRIPTION
    Generates a CA certificate with a disguised identity for HTTPS interception.
    The certificate can be installed on target devices to enable traffic decryption.

.PARAMETER Profile
    Certificate profile to use (google_trust, microsoft, cloudflare, etc.)

.PARAMETER OutputDir
    Directory to save the certificate files

.NOTES
    Author: Network Monitor
    Version: 1.0.0
#>

param(
    [ValidateSet("google_trust", "microsoft", "cloudflare", "amazon", "digicert", "letsencrypt", "comodo", "verisign")]
    [string]$Profile = "google_trust",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

if ($OutputDir -eq "") {
    $OutputDir = Join-Path $ProjectRoot "certs"
}

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host @"

    Certificate Generator
    =====================
    
    Profile: $Profile
    Output:  $OutputDir

"@ -ForegroundColor Cyan

# Activate virtual environment
$venvPath = Join-Path $ProjectRoot "network_monitor_env"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Host "Virtual environment not found. Using system Python." -ForegroundColor Yellow
}

# Run the Python certificate generator
$certGenerator = Join-Path $ProjectRoot "python\https\cert_generator.py"

if (Test-Path $certGenerator) {
    Write-Host "Generating certificate..." -ForegroundColor Cyan
    
    python $certGenerator --profile $Profile --output $OutputDir
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nCertificate generated successfully!" -ForegroundColor Green
        
        $certFile = Join-Path $OutputDir "ca-cert.pem"
        $keyFile = Join-Path $OutputDir "ca-key.pem"
        
        if (Test-Path $certFile) {
            Write-Host "`nFiles created:" -ForegroundColor Yellow
            Write-Host "  - $certFile" -ForegroundColor Gray
            Write-Host "  - $keyFile" -ForegroundColor Gray
            
            # Show certificate info
            Write-Host "`nCertificate info:" -ForegroundColor Yellow
            $certInfo = & openssl x509 -in $certFile -noout -subject -issuer -dates 2>$null
            if ($LASTEXITCODE -eq 0) {
                $certInfo | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            }
        }
    } else {
        Write-Host "Certificate generation failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Certificate generator script not found at: $certGenerator" -ForegroundColor Red
    exit 1
}

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Start the certificate installer server:" -ForegroundColor White
Write-Host "     .\scripts\run.ps1 -Mode cert-server" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Have target devices visit the installer page" -ForegroundColor White
Write-Host ""
