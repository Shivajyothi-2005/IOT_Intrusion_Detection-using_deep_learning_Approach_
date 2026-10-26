# SECURE.IoT Client Integration Suite

This directory contains standalone agents and source code sketches to connect physical workstations (laptops/PCs), routers, and microcontrollers (ESP32) to the Central Intrusion Detection System (IDS) dashboard.

## Folder Contents
1. **`client_agent.py`**: The unified telemetry client script. Supports packet sniffing, zero-root traffic rate monitoring, and simulated ingestion testing.
2. **`run_agent.bat`**: A double-click interactive Windows CLI agent.
3. **`run_agent.sh`**: A bash CLI launcher for macOS and Linux workstations.
4. **`esp32_arduino/`**: Source folder with the `esp32_arduino.ino` sketch.

---

## 1. Monitor Your Laptop or Workstation (One-Click)

### Windows
1. Double-click `run_agent.bat` or run in terminal:
   ```cmd
   run_agent.bat
   ```
2. Enter your IDS server address (e.g. `localhost:8000` or a specific network IP).
3. Select **Mode [2] (Zero-Privilege Traffic Monitor)** for a standard connection or **Mode [1] (Packet Sniffer)** if you want to inspect actual network adapters.

### macOS & Linux
1. Grant execute permissions:
   ```bash
   chmod +x run_agent.sh
   ```
2. Run the launcher:
   ```bash
   ./run_agent.sh
   ```

---

## 2. Monitor Custom IoT Microcontrollers (ESP32)

1. Open the [esp32_arduino.ino](esp32_arduino/esp32_arduino.ino) file inside the Arduino IDE.
2. Configure your Wi-Fi credentials (`ssid` and `password`) and set the `serverUrl` to match your IDS dashboard host network IP.
3. Flash the code to your ESP32.
4. To test attack detection, connect **GPIO Pin 12** to the **3.3V (HIGH)** pin to trigger a simulated intrusion flood payload.
