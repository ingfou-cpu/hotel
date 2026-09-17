#!/usr/bin/env pwsh
# Start Django + React dev servers in parallel
# Usage: ./start-dev.ps1  (run from repo root)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$djangoDir = Join-Path $repoRoot "backend"
$frontDir  = Join-Path $repoRoot "frontend"
$venvPy    = Join-Path $repoRoot ".venv\Scripts\python.exe"

Write-Host "Starting Django on :8000..." -ForegroundColor Cyan
$djangoJob = Start-Job -WorkingDirectory $djangoDir -ScriptBlock {
    param($py) & $py manage.py runserver --noreload
} -ArgumentList $venvPy

Write-Host "Starting Vite on :5173..." -ForegroundColor Cyan
$viteJob = Start-Job -WorkingDirectory $frontDir -ScriptBlock {
    npm run dev
}

Write-Host "Both servers running. Press Ctrl+C to stop." -ForegroundColor Green
Write-Host "  Django: http://localhost:8000" -ForegroundColor Gray
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Gray

try {
    Wait-Job $djangoJob, $viteJob
}
finally {
    Write-Host "Stopping servers..." -ForegroundColor Yellow
    Stop-Job $djangoJob, $viteJob
    Remove-Job $djangoJob, $viteJob -Force
}