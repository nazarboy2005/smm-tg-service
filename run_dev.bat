@echo off
echo Starting SMM Bot in Development Mode (Polling)...
echo.
echo This will run the bot in polling mode for development.
echo Press Ctrl+C to stop the bot.
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Warning: Virtual environment not found at .venv
    echo Make sure you have the required packages installed.
)

REM Set environment to development
set ENVIRONMENT=development
set USE_WEBHOOK=false

REM Run the development main file
python dev_main.py

pause
