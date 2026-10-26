@echo off
title IoT IDS Threat Detection Dashboard Startup
echo ======================================================================
echo          SECURE.IoT Intrusion Detection System Dashboard
echo ======================================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.8+ and try again.
    pause
    exit /b
)

echo [+] Python detected. Installing dependencies from requirements.txt...
echo [*] Running: pip install -r requirements.txt
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Some dependencies failed to install. 
    echo Attempting to start the application anyway...
    echo.
)

echo [+] Starting FastAPI backend server...
echo [+] Access Dashboard locally at the browser window that opens automatically.
echo.

:: Start the Python server from the project root
python backend/app.py

pause
