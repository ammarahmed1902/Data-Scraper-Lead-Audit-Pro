# Start Lead Audit Pro locally (Windows, no Docker)
# Prerequisites: PostgreSQL + Redis running on localhost

Write-Host "Starting Lead Audit Pro..." -ForegroundColor Cyan

# Backend
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$PSScriptRoot\backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# Frontend
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$PSScriptRoot\frontend'; npm run dev"
) -WindowStyle Normal

Write-Host ""
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor Green
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Green
Write-Host "  API Docs:  http://localhost:8000/api/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Login requires PostgreSQL and Redis. See README for setup." -ForegroundColor Yellow
