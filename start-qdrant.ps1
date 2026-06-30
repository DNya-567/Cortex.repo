# start-qdrant.ps1
# Always starts Qdrant with a persistent volume mount.
# Run this INSTEAD of typing "docker run -p 6333:6333 qdrant/qdrant" manually.
# This guarantees your vector data survives every restart.

$ProjectRoot = "C:\Users\dnyanesh\OneDrive\Desktop\context-engine"
$StoragePath = "$ProjectRoot\qdrant_storage"

# Create the storage folder if it doesn't exist yet
if (-not (Test-Path $StoragePath)) {
    New-Item -ItemType Directory -Path $StoragePath | Out-Null
    Write-Host "Created persistent storage folder: $StoragePath" -ForegroundColor Green
}

Write-Host "Starting Qdrant with persistent storage at: $StoragePath" -ForegroundColor Cyan
docker run -p 6333:6333 -v "${StoragePath}:/qdrant/storage" qdrant/qdrant