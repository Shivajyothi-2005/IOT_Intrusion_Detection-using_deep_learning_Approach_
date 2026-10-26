# SECURE.IoT — Intrusion Detection System (IDS) for IoT Networks

This project implements a real-time Intrusion Detection System (IDS) to monitor network telemetry from Internet of Things (IoT) nodes (such as Raspberry Pis, ESP32 microcontrollers, workstations, smartphones, and routers) and detect malicious cyber security threats (DDoS, PortScan, and BruteForce) using a deep learning (PyTorch 1D-CNN) approach.

The application contains a **FastAPI** web server backend, a **PyTorch** 1D convolutional neural network (1D-CNN) classifier, a premium **Vanilla CSS/JS Glassmorphism** single-page frontend dashboard, and a **standalone sniffing client**.

---

## Folder & Directory Map

Here is the exact structure of the code directory and what each file does:

```
iot_intrusion_detection/
├── backend/
│   ├── app.py                # Core web server, REST API routing, WS, simulation thread
│   ├── model.py              # PyTorch 1D-CNN class definition & classification logic
│   ├── devices.json          # Persistent registry database for connected devices (Auto-generated)
│   ├── flow_history.json     # Persistent logger database of historical traffic flows (Auto-generated)
│   └── ids_model.pt          # Serialized neural network model weight state file (Auto-generated)
├── frontend/
│   ├── index.html            # SPA layout, sidebar navigation, modal drawers, alerts HUD
│   ├── style.css             # Glassmorphism dark-theme stylesheets, visual indicators, animation keyframes
│   └── app.js                # WebSockets broker connection, Chart.js updates, UI rendering
├── client_example.py         # Standalone ingestion agent script (Interface Scapy sniffer & Mock telemetry modes)
├── requirements.txt          # Python virtual environment module dependency requirements
└── README.md                 # Project user guide and technical blueprint (This file)
```

---

## File-by-File Technical Blueprint

### 1. `backend/model.py`
This module handles all operations related to threat classification:
* **`class IDS1DCNN(nn.Module)`**: Implements the PyTorch 1D Convolutional Neural Network. It features two `Conv1d` layers (with ReLU activation and MaxPool subsampling) followed by linear fully-connected dense layers (`Linear`). Input shapes are `(batch_size, 1, 14)` mapping to 4 classifications: *Normal*, *DDoS*, *PortScan*, and *BruteForce*.
* **`class PyTorchInferenceEngine`**: Manages PyTorch execution. Checks if the `ids_model.pt` weights exist. If not, initializes a randomized state, saves it, and loads it to process live tensors.
* **`class NumPyFallbackEngine`**: If the system running this code does not have PyTorch or numpy installed, or fails loading C-extension libraries, this engine provides a threshold-based decision-matrix overlay mimicking the output of a fully trained IDS model. It ensures the server starts successfully without crashing under any environment.
* **`normalize_features()`**: Standardizes incoming values using a pre-calculated MinMax matrix. Raw ports, lengths, duration, rates, and flags are mapped to the `[0, 1]` float range.

### 2. `backend/app.py`
This is the master server controller hosting our API service:
* **`class ConnectionManager`**: Handles active WebSockets (`/ws`) so multiple users can open the dashboard simultaneously and receive incoming metrics instantly.
* **`POST /api/report-flow`**: Accepts network stats conforming to the Pydantic schema `IoTFlowTelemetry`. It automatically derives missing features:
  * `packet_rate` = `packet_count / flow_duration`
  * `byte_rate` = `byte_count / flow_duration`
  * `mean_packet_size` = `byte_count / packet_count`
  * `is_tcp` = `1` (if protocol == 6) else `0`
  It feeds the resulting 14-dimensional array into the PyTorch engine, logs the flow, updates the source device record, and broadcasts the event.
* **`POST /api/devices` & `GET /api/devices`**: Registers new hardware nodes manually and gets lists of registered nodes. Persists data to `devices.json` so registered devices are saved even when restarting the server.
* **`POST /api/simulator/toggle`**: Toggles the simulated packet generator thread.
* **`traffic_simulator_loop()`**: Runs in a background daemon thread. When active, it simulates random devices transmitting normal MQTT/HTTPS packets or generating mock attacks (PortScan or DDoS) to populate the frontend and demonstrate visual reactivity.
* **Network Binding**: Binds to `0.0.0.0` on port `8000` to allow other physical devices on the local area network to connect.

### 3. `frontend/index.html`
Provides the layout structures and styles links. It imports:
* **Outfit & JetBrains Mono Fonts**: Modern premium typography.
* **FontAwesome (v6)**: Cyber security and network device icons.
* **Chart.js (v3)**: Graph visualization canvases.
* **SPA Nav Buttons**: Swapping views between Analytics, Live Monitor, and Device Registry.
* **Modals & HUDs**: Sliding toaster container for threat warnings and a pop-up dialog window displaying detailed 1D-CNN output probabilities.

### 4. `frontend/style.css`
Declares the visual theme of the dashboard:
* **Glassmorphism Theme**: Uses semi-transparent glass backdrops (`backdrop-filter: blur(20px)`), dark gradients, and custom scrollbars.
* **Neon Alert Statuses**: Outlines active threats in bright cyan (benign), warning yellow (PortScan), or critical red (DDoS/BruteForce).
* **Animations**: Responsive transitions, siren flash loops (`@keyframes alert-flash`), and floating slide-ins.

### 5. `frontend/app.js`
Runs client-side browser logic:
* **Dynamic WebSocket Connection**: Automatically detects the host domain (e.g. `192.168.1.150:8000` or `localhost:8000`) and connects. Automatically reconnects on network dropped state.
* **Real-time Charting**: Integrates three instances of Chart.js:
  1. Timeline line chart (benign vs attack counts).
  2. Doughnut chart (CNN classification splits).
  3. Horizontal bar chart (traffic volume per device).
* **Siren Synthesizer**: Uses the browser's native **Web Audio API** to generate a warning siren when an intrusion is detected, avoiding heavy static audio files.
* **Code Generator**: Tailors copy-paste `curl` mock payloads and Python commands for whichever device the user selects in the dropdown.

### 6. `client_example.py`
A standalone sniffing tool to stream traffic statistics:
* **Interface Sniffing Mode**: Uses the Python `scapy` library to hook into network cards (e.g. Wi-Fi or Ethernet interfaces). Packets are grouped by connection tuples over a sliding 2.0-second time window. The aggregates are sent to the FastAPI server.
* **Mock Telemetry Mode**: Runs a dependency-free daemon using Python's standard `urllib` module. It generates realistic home automation/MQTT flow stats periodically and occasionally injects mock anomalies (SYN flood, SSH brute force) for test evaluation.

---

## Detailed Step-by-Step Execution Guide

This project is designed to be extremely simple to run and connect devices without requiring advanced technical knowledge or terminal command scripting.

### Step 1: Start the Dashboard (One-Click Launch)
If you are on Windows, simply **double-click the `run_dashboard.bat` file** in the project folder. This script will automatically:
1. Detect your Python installation.
2. Install all required dependencies (`pip install -r requirements.txt`).
3. Detect your computer's local IP address.
4. Start the FastAPI backend server.
5. Open your default web browser automatically to the dashboard (`http://localhost:8000`).

*(On macOS/Linux, run `pip install -r requirements.txt` followed by `python backend/app.py` in your terminal).*

### Step 2: Open the Dashboard on Other Devices
To connect other devices (like your smartphone, tablet, or another laptop) to the IDS network surveillance:
1. Make sure the device is connected to the same Wi-Fi/local network as your server computer.
2. Look at the **IDS SERVER IP** badge in the bottom-left sidebar of the dashboard on your main computer. It will show a network address (e.g. `192.168.1.150:8000`).
3. Open the web browser on your phone/other device and type that address in: `http://192.168.1.150:8000`.

### Step 3: Stream Live Telemetry (Zero-Configuration Browser Method)
You can stream simulated benign or attack traffic from any connected phone or secondary device directly from its browser session:
1. Open the dashboard on your phone or secondary device (`http://<server-ip>:8000`).
2. Go to the **Device Registry** tab.
3. Locate the **Browser Client Streamer** panel at the top-right:
   * **Device Name**: Change this to something friendly (e.g. `Dad's iPhone` or `Kitchen iPad`).
   * **Simulated Traffic Profile**: Select the type of traffic you want this device to report (e.g., *Benign Baseline (Normal)*, *DDoS Simulation*, *Port Scan*, or *Brute Force*).
4. Click **Start Stream**.
5. **Watch the live monitor console!** The device will instantly register in the registry cards grid, its status will show as "Online", and its traffic flows will stream directly onto the live console log. If you selected an attack profile, you will immediately see warning popups and hear alarm chimes playing across all active screens!

### Step 4: Stream Real Network Card Traffic (Advanced Sniffer Client)
If you want to sniff actual network interface traffic from a device, you can use the command-line script:
1. Copy the `client_example.py` script to your target device.
2. Run the client script in simulated mock mode (no dependencies or root access required):
   ```bash
   python client_example.py --server http://<your-server-ip>:8000/api/report-flow --device my-workstation --mode mock
   ```
3. To capture and report actual packets passing through your network card, install Scapy (`pip install scapy`) and run the client as Administrator/sudo:
   ```bash
   # Linux/macOS
   sudo python client_example.py --server http://<your-server-ip>:8000/api/report-flow --device pi-node --mode sniffer --interface wlan0
   
   # Windows (Run Command Prompt as Administrator)
   python client_example.py --server http://<your-server-ip>:8000/api/report-flow --device office-laptop --mode sniffer
   ```
