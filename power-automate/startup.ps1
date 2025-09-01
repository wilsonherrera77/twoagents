# AI-Bridge Dual Claude Startup Script
Write-Host "=== Starting AI-Bridge Dual Claude System ===" -ForegroundColor Cyan

# Start Claude-A (port 8080)
Write-Host "Starting Claude-A server..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "advanced_server.py" -WorkingDirectory "C:\ai-bridge"

# Wait a bit
Start-Sleep -Seconds 3

# Start Claude-B (port 8081)  
Write-Host "Starting Claude-B server..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "claude-b-server.py" -WorkingDirectory "C:\ai-bridge"

# Wait a bit
Start-Sleep -Seconds 3

# Start file system watcher
Write-Host "Starting Power Automate file watcher..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-File C:\ai-bridge\power-automate\file-watcher.ps1"

Write-Host "=== All systems started ===" -ForegroundColor Green
Write-Host "Claude-A: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Claude-B: http://localhost:8081" -ForegroundColor Cyan
Write-Host "File Watcher: Active" -ForegroundColor Cyan
