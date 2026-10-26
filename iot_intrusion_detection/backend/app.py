import os
import json
import time
import random
import socket
import threading
import sys
import webbrowser
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ----------------- Dynamic Port Allocation -----------------
def find_available_port(start_port=8000, max_attempts=50):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('0.0.0.0', port))
                return port
            except Exception:
                continue
    return start_port

PORT = find_available_port(8000)

# Ensure project root is on sys.path so imports work when running as a script
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the model module
from backend.model import get_inference_engine

main_event_loop = None

async def periodic_save_loop():
    """Periodically writes devices and flow history to disk to prevent blocking the event loop"""
    try:
        while True:
            await asyncio.sleep(5.0)
            with db_lock:
                save_devices()
                save_history()
    except asyncio.CancelledError:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_event_loop
    main_event_loop = asyncio.get_running_loop()

    def open_browser():
        time.sleep(1.5)
        try:
            webbrowser.open(f"http://localhost:{PORT}")
            print(f"[IDS Server] Browser opened automatically to: http://localhost:{PORT}")
        except Exception as e:
            print(f"Error opening browser: {e}")

    threading.Thread(target=open_browser, daemon=True).start()
    start_simulator_thread()
    
    save_task = asyncio.create_task(periodic_save_loop())
    
    yield
    
    save_task.cancel()
    global simulator_enabled
    simulator_enabled = False
    
    # Final flush to disk
    with db_lock:
        save_devices()
        save_history()

app = FastAPI(title="IoT IDS Threat Detection Dashboard", lifespan=lifespan)

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent storage paths
DEVICES_FILE = "backend/devices.json"
HISTORY_FILE = "backend/flow_history.json"

# In-memory database
devices_db: Dict[str, Dict[str, Any]] = {}
flow_history: List[Dict[str, Any]] = []

# Instantiate our machine learning inference engine
inference_engine = get_inference_engine()

# Lock for database operations
db_lock = threading.RLock()

# ----------------- Database Setup & Mock Data -----------------

def get_local_ip():
    """Detect the host's actual local IP on the network"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

SERVER_IP = get_local_ip()

def load_data():
    global devices_db, flow_history
    with db_lock:
        # Load devices
        if os.path.exists(DEVICES_FILE):
            try:
                with open(DEVICES_FILE, "r") as f:
                    devices_db = json.load(f)
                # Reset statuses on startup so they start offline and become online only when active
                for dev_id, dev in list(devices_db.items()):
                    if dev_id != "ids-server":
                        dev["status"] = "offline"
                        dev["last_seen"] = time.time() - 600  # 10 minutes ago
                save_devices()
            except Exception as e:
                print(f"Error loading devices: {e}")
                devices_db = {}
        else:
            # Populate default mock devices
            devices_db = {
                "ids-server": {
                    "device_id": "ids-server",
                    "name": "IDS Local Server Node",
                    "ip_address": SERVER_IP,
                    "device_type": "Server",
                    "status": "online",
                    "total_flows": 124,
                    "anomalies_detected": 0,
                    "last_seen": time.time()
                },
                "raspberry-pi-gateway": {
                    "device_id": "raspberry-pi-gateway",
                    "name": "Raspberry Pi Security Gateway",
                    "ip_address": "192.168.1.10",
                    "device_type": "IoT Board",
                    "status": "online",
                    "total_flows": 982,
                    "anomalies_detected": 14,
                    "last_seen": time.time() - 30
                },
                "smart-thermostat": {
                    "device_id": "smart-thermostat",
                    "name": "ESP32 Smart Thermostat",
                    "ip_address": "192.168.1.22",
                    "device_type": "Sensor",
                    "status": "online",
                    "total_flows": 431,
                    "anomalies_detected": 2,
                    "last_seen": time.time() - 100
                },
                "iphone-client": {
                    "device_id": "iphone-client",
                    "name": "Admin Mobile Device",
                    "ip_address": "192.168.1.105",
                    "device_type": "Mobile Phone",
                    "status": "offline",
                    "total_flows": 88,
                    "anomalies_detected": 0,
                    "last_seen": time.time() - 1200
                }
            }
            save_devices()

        # Load flow history
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    flow_history = json.load(f)
            except Exception as e:
                print(f"Error loading flow history: {e}")
                flow_history = []
        else:
            # Generate some realistic seed flow history for charts
            flow_history = []
            now = time.time()
            # Generate 40 mock flows spanning the last 2 hours
            for i in range(40):
                flow_time = now - (40 - i) * 60
                # Pick a random device
                dev_id = random.choice(list(devices_db.keys()))
                dev_ip = devices_db[dev_id]["ip_address"]
                
                # 80% normal, 20% mock attacks
                attack_roll = random.random()
                if attack_roll > 0.8:
                    # Attack
                    attack_type = random.choice(["DDoS", "PortScan", "BruteForce"])
                    if attack_type == "DDoS":
                        src_port = random.randint(49152, 65535)
                        dst_port = 80
                        proto = 6 # TCP
                        duration = random.uniform(0.01, 0.1)
                        pkts = random.randint(100, 500)
                        bytes_cnt = pkts * random.randint(64, 128)
                        syn, ack, rst, fin = 1, 0, 0, 0
                        cls_name, severity = "DDoS", "high"
                    elif attack_type == "PortScan":
                        src_port = random.randint(1024, 5000)
                        dst_port = random.randint(20, 1000)
                        proto = 6
                        duration = random.uniform(0.05, 0.5)
                        pkts = random.randint(2, 5)
                        bytes_cnt = pkts * 40
                        syn, ack, rst, fin = 1, 0, 0, 0
                        cls_name, severity = "PortScan", "medium"
                    else: # BruteForce
                        src_port = random.randint(1024, 65535)
                        dst_port = 22 # SSH
                        proto = 6
                        duration = random.uniform(1.0, 5.0)
                        pkts = random.randint(15, 40)
                        bytes_cnt = pkts * 110
                        syn, ack, rst, fin = 1, 1, 0, 0
                        cls_name, severity = "BruteForce", "high"
                    
                    desc = f"Mock {attack_type} attack seeded."
                else:
                    # Normal
                    src_port = random.randint(1024, 65535)
                    dst_port = random.choice([80, 443, 8080, 1883])
                    proto = random.choice([6, 17]) # TCP or UDP
                    duration = random.uniform(0.1, 10.0)
                    pkts = random.randint(3, 30)
                    bytes_cnt = pkts * random.randint(64, 1500)
                    syn = 1 if proto == 6 else 0
                    ack = 1 if proto == 6 else 0
                    rst, fin = 0, 0
                    cls_name, severity = "Normal", "low"
                    desc = "Normal benign network activity."

                # Calculate derived
                pkt_rate = pkts / duration if duration > 0 else 0
                byte_rate = bytes_cnt / duration if duration > 0 else 0
                mean_sz = bytes_cnt / pkts if pkts > 0 else 0
                
                flow_history.append({
                    "timestamp": flow_time,
                    "device_id": dev_id,
                    "device_name": devices_db[dev_id]["name"],
                    "src_ip": dev_ip if random.choice([True, False]) else "192.168.1.1",
                    "dst_ip": "192.168.1.1" if dev_ip != "192.168.1.1" else "192.168.1.100",
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "protocol": proto,
                    "flow_duration": duration,
                    "packet_count": pkts,
                    "byte_count": bytes_cnt,
                    "packet_rate": pkt_rate,
                    "byte_rate": byte_rate,
                    "mean_packet_size": mean_sz,
                    "tcp_flags_syn": syn,
                    "tcp_flags_ack": ack,
                    "tcp_flags_rst": rst,
                    "tcp_flags_fin": fin,
                    "class_name": cls_name,
                    "severity": severity,
                    "confidence": 0.85 + 0.14 * random.random(),
                    "description": desc
                })
            save_history()

def save_devices():
    try:
        os.makedirs(os.path.dirname(DEVICES_FILE), exist_ok=True)
        with open(DEVICES_FILE, "w") as f:
            json.dump(devices_db, f, indent=2)
    except Exception as e:
        print(f"Error saving devices: {e}")

def save_history():
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w") as f:
            json.dump(flow_history[-500:], f, indent=2) # Caps flow log history at 500 records
    except Exception as e:
        print(f"Error saving history: {e}")

# Load storage files on startup
load_data()

# ----------------- WebSockets Connection Manager -----------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS Manager] Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[WS Manager] Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        disconnected_sockets = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_sockets.append(connection)
        
        for ws in disconnected_sockets:
            self.disconnect(ws)

ws_manager = ConnectionManager()

# ----------------- Pydantic Schemas -----------------

class IoTFlowTelemetry(BaseModel):
    device_id: str = Field(..., description="ID of the reporting device (e.g. laptop-mac, esp32-livingroom)")
    src_ip: str = Field(..., json_schema_extra={"example": "192.168.1.20"})
    dst_ip: str = Field(..., json_schema_extra={"example": "192.168.1.1"})
    src_port: int = Field(..., ge=0, le=65535)
    dst_port: int = Field(..., ge=0, le=65535)
    protocol: int = Field(..., description="IP protocol number (6=TCP, 17=UDP, 1=ICMP)")
    flow_duration: float = Field(..., ge=0.0001, description="Flow duration in seconds")
    packet_count: int = Field(..., ge=1)
    byte_count: int = Field(..., ge=0)
    tcp_flags_syn: int = Field(default=0, ge=0)
    tcp_flags_ack: int = Field(default=0, ge=0)
    tcp_flags_rst: int = Field(default=0, ge=0)
    tcp_flags_fin: int = Field(default=0, ge=0)

class NewDeviceSchema(BaseModel):
    device_id: str
    name: str
    ip_address: str
    device_type: str # Server, IoT Board, Sensor, Mobile Phone, Router, Laptop

# ----------------- Pipeline Execution Helper -----------------

async def process_network_flow(data: Dict[str, Any]):
    """Runs a single flow through feature extraction, inference, statistics updating, and broadcasting"""
    dev_id = data.get("device_id", "unknown-device").strip().replace(" ", "-").lower()
    src_ip = data.get("src_ip", "0.0.0.0")
    
    # 1. Update/Register device implicitly if it doesn't exist
    with db_lock:
        if dev_id not in devices_db:
            devices_db[dev_id] = {
                "device_id": dev_id,
                "name": f"Autodetected Device ({dev_id})",
                "ip_address": src_ip,
                "device_type": (
                    "IoT Board" if "pi" in dev_id.lower() or "esp" in dev_id.lower() 
                    else "Sensor" if "sensor" in dev_id.lower() or "temp" in dev_id.lower() or "thermostat" in dev_id.lower()
                    else "Router" if "router" in dev_id.lower() or "gateway" in dev_id.lower()
                    else "Mobile Phone" if "phone" in dev_id.lower() or "android" in dev_id.lower() or "iphone" in dev_id.lower()
                    else "Laptop"
                ),
                "status": "online",
                "total_flows": 0,
                "anomalies_detected": 0,
                "last_seen": time.time()
            }
        else:
            devices_db[dev_id]["status"] = "online"
            devices_db[dev_id]["last_seen"] = time.time()
            devices_db[dev_id]["ip_address"] = src_ip # update if changed

    # 2. Extract and derive feature metrics
    flow_duration = max(0.0001, float(data["flow_duration"]))
    packet_count = int(data["packet_count"])
    byte_count = int(data["byte_count"])
    protocol = int(data["protocol"])

    packet_rate = float(packet_count) / flow_duration
    byte_rate = float(byte_count) / flow_duration
    mean_packet_size = float(byte_count) / float(packet_count) if packet_count > 0 else 0.0
    is_tcp = 1.0 if protocol == 6 else 0.0

    # Build the 14-dimensional raw feature array
    raw_features = [
        float(data["src_port"]),
        float(data["dst_port"]),
        float(protocol),
        float(flow_duration),
        float(packet_count),
        float(byte_count),
        packet_rate,
        byte_rate,
        mean_packet_size,
        float(data.get("tcp_flags_syn", 0)),
        float(data.get("tcp_flags_ack", 0)),
        float(data.get("tcp_flags_rst", 0)),
        float(data.get("tcp_flags_fin", 0)),
        is_tcp
    ]

    # 3. Model Inference via PyTorch/NumPy
    pred_result = inference_engine.predict(raw_features)
    is_anomaly = pred_result["class_name"] != "Normal"

    # 4. Update device counters
    with db_lock:
        devices_db[dev_id]["total_flows"] += 1
        if is_anomaly:
            devices_db[dev_id]["anomalies_detected"] += 1

    # 5. Save flow history
    flow_record = {
        "timestamp": time.time(),
        "device_id": dev_id,
        "device_name": devices_db[dev_id]["name"],
        "src_ip": src_ip,
        "dst_ip": data.get("dst_ip", "0.0.0.0"),
        "src_port": data["src_port"],
        "dst_port": data["dst_port"],
        "protocol": protocol,
        "flow_duration": flow_duration,
        "packet_count": packet_count,
        "byte_count": byte_count,
        "packet_rate": packet_rate,
        "byte_rate": byte_rate,
        "mean_packet_size": mean_packet_size,
        "tcp_flags_syn": data.get("tcp_flags_syn", 0),
        "tcp_flags_ack": data.get("tcp_flags_ack", 0),
        "tcp_flags_rst": data.get("tcp_flags_rst", 0),
        "tcp_flags_fin": data.get("tcp_flags_fin", 0),
        "class_name": pred_result["class_name"],
        "severity": pred_result["severity"],
        "confidence": pred_result["confidence"],
        "description": pred_result["description"]
    }

    with db_lock:
        flow_history.append(flow_record)
        # limit history cache size
        if len(flow_history) > 500:
            flow_history.pop(0)

    # 6. WebSocket Broadcast
    broadcast_payload = {
        "type": "flow_event",
        "flow": flow_record,
        "devices": list(devices_db.values()),
        "summary": get_summary_stats()
    }
    await ws_manager.broadcast(broadcast_payload)

def get_summary_stats():
    """Calculate aggregated stats across active database"""
    with db_lock:
        total_flows = len(flow_history)
        anomalies = sum(1 for f in flow_history if f["class_name"] != "Normal")
        
        # Threat index calculation based on severity ratio
        threat_index = 0.0
        if total_flows > 0:
            high_threats = sum(1.0 for f in flow_history if f["severity"] == "high")
            med_threats = sum(0.5 for f in flow_history if f["severity"] == "medium")
            threat_index = min(100.0, ((high_threats + med_threats) / total_flows) * 100.0)

        # Device metrics
        online_devices = sum(1 for d in devices_db.values() if d["status"] == "online" and (time.time() - d["last_seen"] < 30))
        
        # Threat classifications counts
        class_counts = {"Normal": 0, "DDoS": 0, "PortScan": 0, "BruteForce": 0}
        for f in flow_history:
            cls = f["class_name"]
            if cls in class_counts:
                class_counts[cls] += 1
                
        return {
            "total_flows": total_flows,
            "anomalies": anomalies,
            "threat_index": round(threat_index, 1),
            "online_devices": online_devices,
            "class_counts": class_counts
        }

# ----------------- Background Traffic Simulator -----------------

simulator_enabled = True
simulator_thread = None

def traffic_simulator_loop():
    """Background thread generating normal and attack flows to feed the dashboard"""
    global simulator_enabled
    print("[Simulator] Background simulation thread started.")
    
    # Run async function in sync loop using a simple utility
    import asyncio
    
    # Attack generator details
    attacks_scenarios = [
        # DDoS
        {"class": "DDoS", "proto": 6, "ports": (80, 80), "pkts": (150, 400), "bytes": (128, 512), "duration": (0.01, 0.05), "syn": 1},
        # PortScan
        {"class": "PortScan", "proto": 6, "ports": (1024, 65535), "pkts": (2, 4), "bytes": (40, 80), "duration": (0.05, 0.2), "syn": 1},
        # BruteForce
        {"class": "BruteForce", "proto": 6, "ports": (22, 22), "pkts": (25, 60), "bytes": (1000, 3000), "duration": (2.0, 8.0), "syn": 1}
    ]

    while True:
        if not simulator_enabled:
            time.sleep(1.0)
            continue
            
        try:
            # 1. Choose device
            with db_lock:
                devs = [d for d in devices_db.values() if d["status"] == "online"]
                if not devs:
                    devs = list(devices_db.values())
            
            target_device = random.choice(devs)
            
            # Roll traffic type: 75% normal, 25% anomaly
            roll = random.random()
            
            if roll > 0.75:
                # Attack
                scenario = random.choice(attacks_scenarios)
                att_class = scenario["class"]
                
                # DDoS has custom port selection
                if att_class == "DDoS":
                    dp = 80
                    sp = random.randint(10000, 65535)
                elif att_class == "BruteForce":
                    dp = random.choice([22, 3389])
                    sp = random.randint(1024, 65535)
                else: # PortScan
                    dp = random.randint(20, 1024)
                    sp = random.randint(1024, 65535)
                    
                proto = scenario["proto"]
                duration = random.uniform(*scenario["duration"])
                pkts = random.randint(*scenario["pkts"])
                bytes_cnt = random.randint(*scenario["bytes"]) * pkts
                syn = scenario.get("syn", 1)
                ack = 1 if att_class == "BruteForce" else 0
                rst, fin = 0, 0
            else:
                # Normal Benign Flow
                sp = random.randint(1024, 65535)
                dp = random.choice([80, 443, 8080, 1883, 53])
                proto = random.choice([6, 17]) # TCP or UDP
                duration = random.uniform(0.5, 12.0)
                pkts = random.randint(3, 45)
                bytes_cnt = pkts * random.randint(64, 1400)
                syn = 1 if proto == 6 else 0
                ack = 1 if proto == 6 else 0
                rst = random.choice([0, 0, 0, 0, 1]) if proto == 6 else 0
                fin = 0

            flow_payload = {
                "device_id": target_device["device_id"],
                "src_ip": target_device["ip_address"],
                "dst_ip": "192.168.1.1" if target_device["ip_address"] != "192.168.1.1" else "192.168.1.100",
                "src_port": sp,
                "dst_port": dp,
                "protocol": proto,
                "flow_duration": duration,
                "packet_count": pkts,
                "byte_count": bytes_cnt,
                "tcp_flags_syn": syn,
                "tcp_flags_ack": ack,
                "tcp_flags_rst": rst,
                "tcp_flags_fin": fin
            }

            # Process flow
            if main_event_loop is not None and main_event_loop.is_running():
                asyncio.run_coroutine_threadsafe(process_network_flow(flow_payload), main_event_loop)
            else:
                asyncio.run(process_network_flow(flow_payload))

        except Exception as e:
            print(f"[Simulator ERROR]: {e}")
            
        # Wait between 1.5 and 3 seconds
        time.sleep(random.uniform(1.5, 3.0))

def start_simulator_thread():
    global simulator_thread
    simulator_thread = threading.Thread(target=traffic_simulator_loop, daemon=True)
    simulator_thread.start()

# ----------------- REST API Endpoints -----------------

@app.get("/api/server-info")
def get_server_info():
    """Returns local server configuration details"""
    return {
        "server_ip": SERVER_IP,
        "port": PORT,
        "protocol": "http",
        "websocket_url": f"ws://{SERVER_IP}:{PORT}/ws"
    }

@app.get("/api/devices")
def get_devices():
    """List all registered IoT/network devices and their alert counts"""
    # Auto mark devices offline if they haven't sent flows in 5 minutes
    with db_lock:
        now = time.time()
        for dev in devices_db.values():
            if now - dev["last_seen"] > 30:
                dev["status"] = "offline"
        save_devices()
        return list(devices_db.values())

@app.post("/api/devices")
async def add_device(dev: NewDeviceSchema):
    """Manually register a device to monitor"""
    dev_id = dev.device_id.strip().replace(" ", "-").lower()
    if not dev_id:
        raise HTTPException(status_code=400, detail="Invalid Device ID")
        
    with db_lock:
        if dev_id in devices_db:
            # Update existing
            devices_db[dev_id]["name"] = dev.name
            devices_db[dev_id]["ip_address"] = dev.ip_address
            devices_db[dev_id]["device_type"] = dev.device_type
        else:
            # Create new
            devices_db[dev_id] = {
                "device_id": dev_id,
                "name": dev.name,
                "ip_address": dev.ip_address,
                "device_type": dev.device_type,
                "status": "online",
                "total_flows": 0,
                "anomalies_detected": 0,
                "last_seen": time.time()
            }
        save_devices()
        
    # Broadcast list update via WS
    await ws_manager.broadcast({
        "type": "devices_update",
        "devices": list(devices_db.values()),
        "summary": get_summary_stats()
    })
        
    return {"status": "success", "device": devices_db[dev_id]}

@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: str):
    """Remove a device from surveillance database"""
    dev_id = device_id.strip().lower()
    if dev_id == "ids-server":
        raise HTTPException(status_code=400, detail="Cannot delete central IDS server node")
        
    with db_lock:
        if dev_id not in devices_db:
            raise HTTPException(status_code=404, detail="Device not found")
        del devices_db[dev_id]
        save_devices()
        
    # Broadcast list update via WS
    await ws_manager.broadcast({
        "type": "devices_update",
        "devices": list(devices_db.values()),
        "summary": get_summary_stats()
    })
    
    return {"status": "success", "deleted": dev_id}

@app.post("/api/report-flow")
async def report_flow(telemetry: IoTFlowTelemetry, request: Request):
    """
    Ingest a flow record from external network agent/IoT device.
    Fibers out derived features, executes 1D-CNN class evaluation, 
    persists history, updates devices db, and broadcasts to dashboard.
    """
    data = telemetry.dict()
    if data["src_ip"] == "detect" or data["src_ip"] == "0.0.0.0" or not data["src_ip"]:
        data["src_ip"] = request.client.host
    await process_network_flow(data)
    return {"status": "processed"}

@app.post("/api/simulator/toggle")
async def toggle_simulator():
    """Toggle the background traffic simulation thread"""
    global simulator_enabled
    simulator_enabled = not simulator_enabled
    
    # Broadcast current status to update client controls
    await ws_manager.broadcast({
        "type": "simulator_update",
        "enabled": simulator_enabled
    })
    
    return {"status": "success", "simulator_enabled": simulator_enabled}

@app.get("/api/simulator/status")
def get_simulator_status():
    return {"simulator_enabled": simulator_enabled}

@app.get("/api/download/client/{filename}")
async def download_client_file(filename: str):
    """Serve integration client agent files directly from the dashboard"""
    allowed_files = {
        "client_agent.py": "iot_clients/client_agent.py",
        "run_agent.bat": "iot_clients/run_agent.bat",
        "run_agent.sh": "iot_clients/run_agent.sh",
        "esp32_arduino.ino": "iot_clients/esp32_arduino/esp32_arduino.ino"
    }
    
    if filename not in allowed_files:
        raise HTTPException(status_code=404, detail="File signature not found in download manifest")
        
    file_path = os.path.join(PROJECT_ROOT, allowed_files[filename])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Target file {filename} not compiled on host server")
        
    # Dynamically inject client_agent.py base64 into run_agent.bat/run_agent.sh
    if filename in ["run_agent.bat", "run_agent.sh"]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            agent_path = os.path.join(PROJECT_ROOT, "iot_clients/client_agent.py")
            if os.path.exists(agent_path):
                with open(agent_path, "rb") as af:
                    import base64
                    b64 = base64.b64encode(af.read()).decode("utf-8")
                
                # Format base64 block based on script type comments
                comment_char = ":: " if filename == "run_agent.bat" else "# "
                b64_lines = [f"{comment_char}{b64[i:i+80]}" for i in range(0, len(b64), 80)]
                b64_block = "\n".join(b64_lines)
                
                content = content.replace("@CLIENT_AGENT_BASE64@", b64_block)
                
            headers = {"Content-Disposition": f"attachment; filename={filename}"}
            from fastapi.responses import Response
            return Response(content=content, media_type="application/octet-stream", headers=headers)
        except Exception as e:
            pass

    # Set headers so the browser triggers a file download dialogue
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

@app.get("/api/stats")
def get_stats():
    """Returns flow logs summary and initial logs list"""
    with db_lock:
        logs = list(flow_history)
    return {
        "summary": get_summary_stats(),
        "recent_flows": list(reversed(logs))[:100] # Return latest 100 logs
    }

# ----------------- WebSocket Server Route -----------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial database payload upon connecting
        with db_lock:
            init_payload = {
                "type": "init_data",
                "devices": list(devices_db.values()),
                "recent_flows": list(reversed(flow_history))[:50],
                "summary": get_summary_stats(),
                "simulator_enabled": simulator_enabled
            }
        await websocket.send_json(init_payload)
        
        while True:
            # Keep socket alive and listen for client actions
            data = await websocket.receive_text()
            # If client sends ping, we reply pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"[WS ERROR]: {e}")
        ws_manager.disconnect(websocket)

# Serve the static files from the frontend folder
# Mount last so API routers match first
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    print(f"Warning: Frontend folder not found at path {frontend_dir}. Static hosting disabled.")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print(f"  IoT Security Intrusion Detection System Dashboard Server")
    print(f"  Access local panel at: http://localhost:{PORT}")
    print(f"  Access network panel at: http://{SERVER_IP}:{PORT}")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
