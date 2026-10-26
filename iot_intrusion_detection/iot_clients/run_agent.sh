#!/usr/bin/env bash
# Secure.IoT Telemetry Client Agent Launcher for Linux/macOS

clear
echo "======================================================================"
echo "         SECURE.IoT Client Agent - Telemetry Streamer"
echo "======================================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    exit 1
fi

# Configuration
DEFAULT_SERVER="http://127.0.0.1:8000/api/report-flow"
read -p "Enter IDS Server Address [default: 127.0.0.1:8000]: " SERVER_IP
if [ -z "$SERVER_IP" ]; then
    SERVER_URL=$DEFAULT_SERVER
else
    SERVER_URL="http://${SERVER_IP}/api/report-flow"
fi

COMPUTER_NAME=$(hostname)
read -p "Enter a unique Device ID [default: laptop-${COMPUTER_NAME}]: " DEVICE_ID
if [ -z "$DEVICE_ID" ]; then
    DEVICE_ID="laptop-${COMPUTER_NAME}"
fi
if [ -z "$SERVER_IP" ]; then
    DOWNLOAD_IP="127.0.0.1:8000"
else
    DOWNLOAD_IP=$SERVER_IP
fi

if [ ! -f "client_agent.py" ]; then
    echo "[*] client_agent.py not found in this folder."
    echo "[*] Unpacking core client script..."
    
    # Extract base64 block and decode it (split token to avoid self-match)
    sed -n '/---BEGIN_CLIENT_'\''AGENT_B64---/,/---END_CLIENT_'\''AGENT_B64---/p' "$0" | grep -v '---' | sed 's/^#\s*//' | base64 -d > client_agent.py 2>/dev/null
    if [ $? -ne 0 ]; then
        # Try macOS base64
        sed -n '/---BEGIN_CLIENT_'\''AGENT_B64---/,/---END_CLIENT_'\''AGENT_B64---/p' "$0" | grep -v '---' | sed 's/^#\s*//' | base64 -D > client_agent.py 2>/dev/null
    fi
    
    if [ ! -f "client_agent.py" ]; then
        echo "[*] Unpacking failed. Downloading core script from http://${DOWNLOAD_IP}..."
        if command -v curl &> /dev/null; then
            curl -s -f -o client_agent.py "http://${DOWNLOAD_IP}/api/download/client/client_agent.py"
        elif command -v wget &> /dev/null; then
            wget -q -O client_agent.py "http://${DOWNLOAD_IP}/api/download/client/client_agent.py"
        else
            echo "[ERROR] Neither curl nor wget found. Please download client_agent.py manually."
            exit 1
        fi
        if [ $? -ne 0 ]; then
            echo "[ERROR] Failed to download client_agent.py from the server."
            exit 1
        fi
        echo "[+] Successfully downloaded client_agent.py!"
    else
        echo "[+] Successfully unpacked client_agent.py!"
    fi
fi

echo ""
echo "Select Telemetry Mode:"
echo "[1] Active Connection Sniffer (Inspects real network packets. Requires sudo/scapy)"
echo "[2] Zero-Privilege Traffic Monitor (Tracks system throughput rates. Safe/psutil)"
echo "[3] Threat Ingestion Simulator (Generates mock attacks to test IDS)"
echo ""
read -p "Select option [1-3]: " MODE_CHOICE

if [ "$MODE_CHOICE" = "1" ]; then
    MODE_NAME="sniffer"
    # Check scapy
    python3 -c "import scapy" &> /dev/null
    if [ $? -ne 0 ]; then
        echo "[*] Installing scapy..."
        pip3 install scapy
    fi
    echo "[!] NOTE: Sniffer mode requires sudo privileges to access raw sockets."
    echo "[*] Launching sniffer..."
    sudo python3 client_agent.py --server "$SERVER_URL" --device "$DEVICE_ID" --name "${COMPUTER_NAME} Laptop" --mode $MODE_NAME
elif [ "$MODE_CHOICE" = "3" ]; then
    MODE_NAME="mock"
    echo "[*] Launching simulation injector..."
    python3 client_agent.py --server "$SERVER_URL" --device "$DEVICE_ID" --name "${COMPUTER_NAME} Laptop" --mode $MODE_NAME
else
    MODE_NAME="system"
    # Check psutil
    python3 -c "import psutil" &> /dev/null
    if [ $? -ne 0 ]; then
        echo "[*] Installing psutil..."
        pip3 install psutil
    fi
    echo "[*] Launching system monitor..."
    python3 client_agent.py --server "$SERVER_URL" --device "$DEVICE_ID" --name "${COMPUTER_NAME} Laptop" --mode $MODE_NAME
fi

exit 0

# ---BEGIN_CLIENT_AGENT_B64---
# @CLIENT_AGENT_BASE64@
# ---END_CLIENT_AGENT_B64---
