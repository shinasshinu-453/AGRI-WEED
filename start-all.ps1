# start-all.ps1
# AgriVision + ETL Pipeline Startup Script

Write-Host "🚀 Starting AgriVision + ETL Pipeline..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Gray

# Start ETL Pipeline
Write-Host "`n📊 Starting ETL Pipeline (Airflow + PostgreSQL + Redis)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\shina\ETL PIPELINE'; Write-Host '📊 ETL Pipeline Terminal' -ForegroundColor Cyan; docker-compose up"

# Wait for Airflow to initialize
Write-Host "`n⏳ Waiting for Airflow to start (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Start Flask Backend
Write-Host "`n🐍 Starting Flask Backend (YOLO + API)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\main project\Main-project-Wheat'; Write-Host '🐍 Flask Backend Terminal' -ForegroundColor Cyan; python server.py --ngrok"

# Wait for Flask to start
Write-Host "`n⏳ Waiting for Flask to start (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start Vite Frontend
Write-Host "`n⚛️  Starting Vite Frontend (React)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\main project\Main-project-Wheat'; Write-Host '⚛️ Vite Frontend Terminal' -ForegroundColor Cyan; npm run dev"

Write-Host "`n✅ All services are starting!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Gray
Write-Host "`nAccess Points:" -ForegroundColor White
Write-Host "  • AgriVision UI:  http://localhost:5173" -ForegroundColor Magenta
Write-Host "  • Airflow UI:     http://localhost:8080 (admin/admin)" -ForegroundColor Cyan
Write-Host "  • Flask API:      http://localhost:5000" -ForegroundColor Yellow
Write-Host "  • PostgreSQL:     localhost:5432 (postgres/postgres)" -ForegroundColor Gray
Write-Host "`nPress Ctrl+C in each terminal to stop services" -ForegroundColor DarkGray
Write-Host "Or run .\stop-all.ps1 to stop everything" -ForegroundColor DarkGray
