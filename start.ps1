# EcoCampus AI PowerShell Launcher
Write-Host "========================================================" -ForegroundColor Green
Write-Host "             EcoCampus AI Platform" -ForegroundColor Cyan
Write-Host "  AI-Powered Predictive Campus Resource Optimization" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Starting EcoCampus AI server on http://localhost:5000 ..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server anytime." -ForegroundColor DarkGray
Write-Host ""

python -m backend.app
