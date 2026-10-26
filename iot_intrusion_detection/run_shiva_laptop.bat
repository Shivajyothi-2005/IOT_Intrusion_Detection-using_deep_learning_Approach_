@echo off
title Shiva Jyothi HP Laptop Client Agent
echo ======================================================================
echo  Starting Telemetry Client for: Shiva Jyothi HP Laptop
echo ======================================================================
echo.

:: Move into the clients folder and run the python agent directly
cd iot_clients
python client_agent.py --server "http://127.0.0.1:8000/api/report-flow" --device "hp-laptop-15" --name "Shiva Jyothi HP Laptop" --mode "system"

pause
