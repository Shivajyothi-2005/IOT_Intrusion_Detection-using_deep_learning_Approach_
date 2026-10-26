@echo off
title Shiva Jyothi HP Laptop Client Agent
echo ======================================================================
echo  Starting Telemetry Client for: Shiva Jyothi HP Laptop
echo ======================================================================
echo.

:: Run the python agent directly since we are already inside the folder
python client_agent.py --server "http://127.0.0.1:8000/api/report-flow" --device "hp-laptop-15" --name "Shiva Jyothi HP Laptop" --mode "system"

pause
