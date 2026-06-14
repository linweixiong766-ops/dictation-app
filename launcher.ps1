# Dictation App Launcher
$host.UI.RawUI.WindowTitle = "Dictation App"
Set-Location "D:\First-cc\first_cc\dictation-app"

Write-Host "==============================" -ForegroundColor Green
Write-Host "   Dictation App Launcher" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green
Write-Host ""

# Check if node_modules exists
if (!(Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host "Starting server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Open browser: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Start browser after delay
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:5173"
}

# Start dev server
npm run dev
