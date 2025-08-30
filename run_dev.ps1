# PowerShell script to run SMM Bot in Development Mode (Polling)
Write-Host "Starting SMM Bot in Development Mode (Polling)..." -ForegroundColor Green
Write-Host ""
Write-Host "This will run the bot in polling mode for development." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the bot." -ForegroundColor Yellow
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "Warning: Virtual environment not found at .venv" -ForegroundColor Yellow
    Write-Host "Make sure you have the required packages installed." -ForegroundColor Yellow
}

# Set environment variables for development
$env:ENVIRONMENT = "development"
$env:USE_WEBHOOK = "false"

Write-Host "Environment set to development mode" -ForegroundColor Cyan
Write-Host "Webhook disabled - using polling mode" -ForegroundColor Cyan
Write-Host ""

# Run the development main file
try {
    python dev_main.py
} catch {
    Write-Host "Error running the bot: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Bot stopped. Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
