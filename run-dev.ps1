# run-dev.ps1 — Start CausalMesh Backend and Frontend in Development Mode

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "⚡ Starting CausalMesh Development Environment" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$backendDir = Join-Path $PSScriptRoot "backend"
$frontendDir = Join-Path $PSScriptRoot "frontend"

# Check Python virtual environment
$pythonExe = Join-Path $backendDir "venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "[1/3] Creating Python virtual environment..." -ForegroundColor Yellow
    Set-Location $backendDir
    python -m venv venv
    & (Join-Path $backendDir "venv\Scripts\pip.exe") install -r requirements.txt
}

# Start Backend
Write-Host "[2/3] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
$backendJob = Start-Process -FilePath $pythonExe -ArgumentList "main.py" -WorkingDirectory $backendDir -PassThru

# Start Frontend
Write-Host "[3/3] Starting Next.js Frontend on http://localhost:3001..." -ForegroundColor Green
Set-Location $frontendDir
npm.cmd run dev

# Stop backend process on frontend exit
if ($backendJob -and -not $backendJob.HasExited) {
    Stop-Process -Id $backendJob.Id -Force
}
