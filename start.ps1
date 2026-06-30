# Kill port 8000 correctly
Write-Host "Clearing port 8000..." -ForegroundColor Yellow
$netstatOutput = netstat -ano | findstr "0.0.0.0:8000"
if ($netstatOutput) {
  $pid8000 = ($netstatOutput -split '\s+') | Select-Object -Last 1
  if ($pid8000 -match '^\d+$') {
    Write-Host "Killing PID $pid8000 on port 8000..." -ForegroundColor Yellow
    taskkill /PID $pid8000 /F 2>$null
    Start-Sleep -Seconds 2
  }
}
Write-Host "Port 8000 cleared" -ForegroundColor Green

# Start Qdrant
Write-Host "Starting Qdrant..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker run -p 6333:6333 qdrant/qdrant"

# Wait for Qdrant to be ready
Write-Host "Waiting for Qdrant..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start Ollama
Write-Host "Starting Ollama..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ollama serve"

# Wait for Ollama
Start-Sleep -Seconds 3

# Start Electron app (launches backend + dashboard automatically)
Write-Host "Starting Context Engine..." -ForegroundColor Green
Set-Location "C:\Users\dnyanesh\OneDrive\Desktop\context-engine"
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
npm start