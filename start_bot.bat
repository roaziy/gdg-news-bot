@echo off
echo Starting GDG News Bot...
echo.

REM Check if .env file exists
if not exist .env (
    echo Error: .env file not found!
    echo Please copy .env.example to .env and configure it with your Discord token and channel ID.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment and run the bot
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    python bot.py
) else (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then: .venv\Scripts\activate.bat
    echo Then: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

pause
