@echo off
title Secure.IoT Telemetry Client Agent
cls
echo ======================================================================
echo          SECURE.IoT Client Agent - Telemetry Streamer
setlocal enabledelayedexpansion
echo ======================================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.8+ and try again.
    pause
    exit /b
)

:: Configuration
set DEFAULT_SERVER=http://127.0.0.1:8000/api/report-flow
set /p SERVER_IP="Enter IDS Server Address [default: 127.0.0.1:8000]: "
rem Strip leading and trailing spaces from SERVER_IP
for /f "tokens=* delims= " %%A in ("!SERVER_IP!") do set "SERVER_IP=%%A"
if "%SERVER_IP%"=="" (
    set SERVER_URL=!DEFAULT_SERVER!
) else (
    set SERVER_URL=http://!SERVER_IP!/api/report-flow
)

set COMPUTER_NAME=%COMPUTERNAME%
set /p DEVICE_ID="Enter a unique Device ID [default: laptop-%COMPUTER_NAME%]: "
rem Strip leading and trailing spaces from DEVICE_ID
for /f "tokens=* delims= " %%A in ("!DEVICE_ID!") do set "DEVICE_ID=%%A"
if "%DEVICE_ID%"=="" (
    set DEVICE_ID=laptop-!COMPUTER_NAME!
)
rem Strip leading and trailing spaces
for /f "tokens=* delims= " %%A in ("!SERVER_IP!") do set "SERVER_IP=%%A"
for /f "tokens=* delims= " %%A in ("!DEVICE_ID!") do set "DEVICE_ID=%%A"

if "%SERVER_IP%"=="" (
    set DOWNLOAD_IP=127.0.0.1:8000
) else (
    set DOWNLOAD_IP=!SERVER_IP!
)

if not exist client_agent.py (
    echo [*] client_agent.py not found in this folder.
    echo [*] Unpacking core client script...
    powershell -Command "[IO.File]::WriteAllBytes('client_agent.py', [Convert]::FromBase64String( ([regex]::Match([IO.File]::ReadAllText('%~f0'), ('(?ms)---BEGIN_' + 'CLIENT_AGENT_B64---(.*)---END_' + 'CLIENT_AGENT_B64---')).Groups[1].Value -replace '[^A-Za-z0-9+/=]', '') ))" >nul 2>&1
    
    if not exist client_agent.py (
        echo [*] Unpacking failed. Attempting to download from http://!DOWNLOAD_IP!...
        curl -s -f -o client_agent.py http://!DOWNLOAD_IP!/api/download/client/client_agent.py
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to download client_agent.py from the server.
            echo Please ensure the server is running or download it manually from the dashboard.
            pause
            exit /b
        )
        echo [+] Successfully downloaded client_agent.py!
    ) else (
        echo [+] Successfully unpacked client_agent.py!
    )
)


echo.
echo Select Telemetry Mode:
echo [1] Active Connection Sniffer (Inspects real network packets. Requires Admin/scapy)
echo [2] Zero-Privilege Traffic Monitor (Tracks system throughput rates. Safe/psutil)
echo [3] Threat Ingestion Simulator (Generates mock attacks to test IDS)
echo.
set /p MODE_CHOICE="Select option [1-3]: "

if "%MODE_CHOICE%"=="1" (
    set MODE_NAME=sniffer
    echo [*] Checking scapy package...
    python -c "import scapy" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [*] Installing scapy...
        pip install scapy
    )
    echo [!] NOTE: Sniffer mode requires Administrator privileges to access network cards.
    echo [*] Launching sniffer...
) else if "%MODE_CHOICE%"=="3" (
    set MODE_NAME=mock
    echo [*] Launching simulation injector...
) else (
    set MODE_NAME=system
    python -c "import psutil" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [*] Installing psutil for system throughput metrics...
        pip install psutil
    )
    echo [*] Launching system monitor...
)

echo.
echo ======================================================================
echo  Streaming active metrics to: %SERVER_URL%
echo  Device Registered as       : %DEVICE_ID%
echo  Press Ctrl+C to stop the stream
echo ======================================================================
echo.

python client_agent.py --server "%SERVER_URL%" --device "%DEVICE_ID%" --name "%COMPUTER_NAME% Laptop" --mode %MODE_NAME%

pause
goto :eof

:: ---BEGIN_CLIENT_AGENT_B64---
:: @CLIENT_AGENT_BASE64@
:: ---END_CLIENT_AGENT_B64---
