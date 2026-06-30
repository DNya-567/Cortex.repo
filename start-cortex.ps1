# start-cortex.ps1
# Starts Qdrant (Docker), Ollama, and the Cortex Electron app in the right order.
# Usage: right-click > Run with PowerShell, or run: .\start-cortex.ps1

$ErrorActionPreference = "Continue"
$ProjectRoot = "C:\Users\dnyanesh\OneDrive\Desktop\context-engine"

function Test-Url($url) {
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

Write-Host "=== Starting Cortex services ===" -ForegroundColor Cyan

# --- 1. Start Qdrant (Docker) if not already running ---
Write-Host "`n[1/3] Checking Qdrant..." -ForegroundColor Yellow
if (Test-Url "http://localhost:6333/dashboard") {
    Write-Host "Qdrant already running." -ForegroundColor Green
} else {
    Write-Host "Starting Qdrant via Docker..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker run -p 6333:6333 qdrant/qdrant"

    $maxWait = 30
    $waited = 0
    while (-not (Test-Url "http://localhost:6333/dashboard") -and $waited -lt $maxWait) {
        Start-Sleep -Seconds 2
        $waited += 2
        Write-Host "  waiting for Qdrant... ($waited s)" -ForegroundColor DarkGray
    }
    if (Test-Url "http://localhost:6333/dashboard") {
        Write-Host "Qdrant is up." -ForegroundColor Green
    } else {
        Write-Host "WARNING: Qdrant did not respond after $maxWait s. Check Docker Desktop is running." -ForegroundColor Red
    }
}

# --- 2. Start Ollama if not already running ---
Write-Host "`n[2/3] Checking Ollama..." -ForegroundColor Yellow
if (Test-Url "http://localhost:11434") {
    Write-Host "Ollama already running." -ForegroundColor Green
} else {
    Write-Host "Starting Ollama..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "ollama serve"

    $maxWait = 20
    $waited = 0
    while (-not (Test-Url "http://localhost:11434") -and $waited -lt $maxWait) {
        Start-Sleep -Seconds 2
        $waited += 2
        Write-Host "  waiting for Ollama... ($waited s)" -ForegroundColor DarkGray
    }
    if (Test-Url "http://localhost:11434") {
        Write-Host "Ollama is up." -ForegroundColor Green
    } else {
        Write-Host "WARNING: Ollama did not respond after $maxWait s." -ForegroundColor Red
    }
}

# --- 3. Start Cortex (npm start) ---
Write-Host "`n[3/3] Starting Cortex app..." -ForegroundColor Yellow
Set-Location $ProjectRoot
npm start
