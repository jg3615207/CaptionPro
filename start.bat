@echo off
echo ==============================================
echo   Starting Standalone Whisper Web UI
echo ==============================================
echo.

if not exist venv (
    echo [ERROR] Virtual environment not found. Please run install.bat first.
    pause
    exit /b
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting server...
python -m uvicorn server:app --host 0.0.0.0 --port 8000

pause
