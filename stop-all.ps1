# stop-all.ps1
# AgriVision + ETL Pipeline Shutdown Script

Write-Host "🛑 Stopping all services..." -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Gray

# Stop Docker containers
Write-Host "`n📊 Stopping ETL Pipeline (Docker)..." -ForegroundColor Yellow
Push-Location "C:\Users\shina\ETL PIPELINE"
docker-compose down
Pop-Location

# Kill Flask processes
Write-Host "`n🐍 Stopping Flask processes..." -ForegroundColor Yellow
$flaskProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*server.py*"}
if ($flaskProcesses) {
    $flaskProcesses | Stop-Process -Force
    Write-Host "   ✓ Flask stopped" -ForegroundColor Green
} else {
    Write-Host "   ℹ No Flask processes found" -ForegroundColor Gray
}

# Kill Node processes (Vite)
Write-Host "`n⚛️  Stopping Vite processes..." -ForegroundColor Yellow
$nodeProcesses = Get-Process -Name node -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    $nodeProcesses | Stop-Process -Force
    Write-Host "   ✓ Vite stopped" -ForegroundColor Green
} else {
    Write-Host "   ℹ No Vite processes found" -ForegroundColor Gray
}

# Kill ngrok processes
Write-Host "`n🌐 Stopping ngrok processes..." -ForegroundColor Yellow
$ngrokProcesses = Get-Process -Name ngrok -ErrorAction SilentlyContinue
if ($ngrokProcesses) {
    $ngrokProcesses | Stop-Process -Force
    Write-Host "   ✓ ngrok stopped" -ForegroundColor Green
} else {
    Write-Host "   ℹ No ngrok processes found" -ForegroundColor Gray
}

Write-Host "`n✅ All services stopped!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Gray
