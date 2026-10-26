#!/usr/bin/env python3
"""
Secure.IoT IDS Client Agent
Allows any laptop, PC, or IoT gateway to stream network traffic analytics
to the Central Deep Learning Intrusion Detection System.

Features:
1. Sniffer Mode: Uses Scapy to trace actual network packets on Wi-Fi/Ethernet.
2. System Throughput Mode: Zero-dependency system-level traffic tracking.
3. Mock mode: Simulation for testing intrusion detections.
"""

import sys
import time
import argparse
import random
import json
import urllib.request
import urllib.error
import socket
import os
import subprocess

# Check dependencies
try:
    from scapy.all import sniff, IP, TCP, UDP
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Global connection tracker for Sniffer mode
flow_table = {}
flow_lock = False

def get_local_ip():
    """Detects this device's active local network IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def send_payload(server_url, payload):
    """Sends the flow telemetry payload using standard urllib (no third-party requests module needed)"""
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        server_url, 
        data=data, 
        headers={'Content-Type': 'application/json', 'User-Agent': 'IDS-Client/1.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=2.5) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"[-] Connection Error to {server_url}: {e.reason}")
    except socket.timeout:
        print("[-] Server timeout: Connection slow or offline.")
    except Exception as e:
        print(f"[-] Ingestion Error: {e}")
    return None

def register_device(server_url, device_id, name, device_type):
    """Register the device explicitly to the dashboard database"""
    reg_url = server_url.replace("/report-flow", "/devices")
    payload = {
        "device_id": device_id,
        "name": name,
        "ip_address": get_local_ip(),
        "device_type": device_type
    }
    print(f"[*] Registering node '{name}' as a '{device_type}'...")
    response = send_payload(reg_url, payload)
    if response:
        print(f"[+] Registration successful.")
        return True
    return False

# ----------------- Interface Sniffer Mode (Scapy) -----------------

def packet_callback(pkt):
    global flow_table, flow_lock
    if flow_lock:
        return
        
    if not pkt.haslayer(IP):
        return
        
    ip_layer = pkt[IP]
    proto = ip_layer.proto
    
    # Analyze TCP (6) or UDP (17)
    if proto not in [6, 17]:
        return
        
    src_ip = ip_layer.src
    dst_ip = ip_layer.dst
    
    if proto == 6 and pkt.haslayer(TCP):
        tcp_layer = pkt[TCP]
        src_port = tcp_layer.sport
        dst_port = tcp_layer.dport
        syn = 1 if 'S' in tcp_layer.flags else 0
        ack = 1 if 'A' in tcp_layer.flags else 0
        rst = 1 if 'R' in tcp_layer.flags else 0
        fin = 1 if 'F' in tcp_layer.flags else 0
    elif proto == 17 and pkt.haslayer(UDP):
        udp_layer = pkt[UDP]
        src_port = udp_layer.sport
        dst_port = udp_layer.dport
        syn, ack, rst, fin = 0, 0, 0, 0
    else:
        return

    flow_key = (src_ip, dst_ip, src_port, dst_port, proto)
    pkt_len = len(pkt)
    now = time.time()
    
    if flow_key not in flow_table:
        flow_table[flow_key] = {
            "start_time": now,
            "last_time": now,
            "packet_count": 1,
            "byte_count": pkt_len,
            "syn": syn,
            "ack": ack,
            "rst": rst,
            "fin": fin
        }
    else:
        flow = flow_table[flow_key]
        flow["last_time"] = now
        flow["packet_count"] += 1
        flow["byte_count"] += pkt_len
        flow["syn"] = max(flow["syn"], syn)
        flow["ack"] = max(flow["ack"], ack)
        flow["rst"] = max(flow["rst"], rst)
        flow["fin"] = max(flow["fin"], fin)

def flush_flows_loop(server_url, device_id):
    global flow_table, flow_lock
    print(f"[+] Started sniffer pipeline aggregation. Sampling window: 2.0s")
    while True:
        time.sleep(2.0)
        
        # Lock and swap buffers
        flow_lock = True
        current_flows = flow_table
        flow_table = {}
        flow_lock = False
        
        if not current_flows:
            continue
            
        print(f"[*] Aggregated {len(current_flows)} connections. Ingesting to dashboard...")
        
        for key, stats in current_flows.items():
            src_ip, dst_ip, src_port, dst_port, protocol = key
            duration = max(0.0001, stats["last_time"] - stats["start_time"])
            
            payload = {
                "device_id": device_id,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": int(src_port),
                "dst_port": int(dst_port),
                "protocol": int(protocol),
                "flow_duration": float(duration),
                "packet_count": int(stats["packet_count"]),
                "byte_count": int(stats["byte_count"]),
                "tcp_flags_syn": int(stats["syn"]),
                "tcp_flags_ack": int(stats["ack"]),
                "tcp_flags_rst": int(stats["rst"]),
                "tcp_flags_fin": int(stats["fin"])
            }
            send_payload(server_url, payload)

def run_sniffer_mode(server_url, device_id, name, interface):
    if not HAS_SCAPY:
        print("[-] Error: Scapy package is required for sniffer mode. Install via: pip install scapy")
        sys.exit(1)
        
    print(f"\n[+] Starting Interface Sniffing Client...")
    print(f"    Target Server API : {server_url}")
    print(f"    Device Node ID    : {device_id}")
    print(f"    Sniffing Interface: {interface if interface else 'Default Interface'}")
    print("="*60 + "\n")
    
    register_device(server_url, device_id, name, "Laptop")
    
    import threading
    flush_thread = threading.Thread(target=flush_flows_loop, args=(server_url, device_id), daemon=True)
    flush_thread.start()
    
    try:
        if interface:
            sniff(iface=interface, prn=packet_callback, store=0)
        else:
            sniff(prn=packet_callback, store=0)
    except KeyboardInterrupt:
        print("\n[-] Sniffing paused. Exiting.")
    except Exception as e:
        print(f"\n[-] Sniffing crashed: {e}")
        print("    Ensure you are running as Administrator/sudo or have network permissions.")
        print("    Alternatively, run in system mode: python client_agent.py --mode system")

# ----------------- System Traffic Throughput Mode -----------------

def get_system_traffic_counters():
    """Gets total transmitted and received bytes/packets at the OS level"""
    if HAS_PSUTIL:
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "pkts_sent": net_io.packets_sent,
            "pkts_recv": net_io.packets_recv
        }
    
    # Fallback to parsing CLI stats
    if sys.platform == "win32":
        try:
            out = subprocess.check_output("netstat -e", shell=True).decode('utf-8', errors='ignore')
            lines = [line.strip().split() for line in out.splitlines() if line.strip()]
            for line in lines:
                if line[0].lower().startswith("bytes"):
                    return {
                        "bytes_recv": int(line[1]),
                        "bytes_sent": int(line[2]),
                        "pkts_recv": 1000, # Mock packet ratios if not parseable
                        "pkts_sent": 1000
                    }
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        try:
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()
            tot_bytes_recv = 0
            tot_bytes_sent = 0
            tot_pkts_recv = 0
            tot_pkts_sent = 0
            for line in lines[2:]:
                parts = line.strip().split()
                if len(parts) >= 9:
                    tot_bytes_recv += int(parts[1])
                    tot_pkts_recv += int(parts[2])
                    tot_bytes_sent += int(parts[9])
                    tot_pkts_sent += int(parts[10])
            return {
                "bytes_recv": tot_bytes_recv,
                "bytes_sent": tot_bytes_sent,
                "pkts_recv": tot_pkts_recv,
                "pkts_sent": tot_pkts_sent
            }
        except Exception:
            pass

    # Generic simulation if OS parsing fails
    return {
        "bytes_sent": random.randint(1000, 5000),
        "bytes_recv": random.randint(1000, 5000),
        "pkts_sent": random.randint(10, 50),
        "pkts_recv": random.randint(10, 50)
    }

def run_system_mode(server_url, device_id, name):
    print(f"\n[+] Starting System Traffic Monitor (No dependencies/root required)...")
    print(f"    Target Server API : {server_url}")
    print(f"    Device Node ID    : {device_id}")
    print("="*60 + "\n")
    
    register_device(server_url, device_id, name, "Laptop")
    
    local_ip = get_local_ip()
    last_stats = get_system_traffic_counters()
    last_time = time.time()
    
    try:
        while True:
            time.sleep(2.0)
            now = time.time()
            current_stats = get_system_traffic_counters()
            dt = now - last_time
            
            # Calculate rates
            bytes_diff = (current_stats["bytes_sent"] - last_stats["bytes_sent"]) + (current_stats["bytes_recv"] - last_stats["bytes_recv"])
            pkts_diff = (current_stats["pkts_sent"] - last_stats["pkts_sent"]) + (current_stats["pkts_recv"] - last_stats["pkts_recv"])
            
            # Reset checks (in case counter rolls over or resets)
            if bytes_diff < 0 or pkts_diff < 0:
                bytes_diff = random.randint(100, 500)
                pkts_diff = random.randint(1, 5)
                
            # Create a mock flow representing this system's active connection rate
            payload = {
                "device_id": device_id,
                "src_ip": local_ip,
                "dst_ip": "192.168.1.1", # Gateway
                "src_port": random.randint(49152, 65535),
                "dst_port": 443, # Represents secure web traffic
                "protocol": 6, # TCP
                "flow_duration": float(dt),
                "packet_count": int(max(1, pkts_diff)),
                "byte_count": int(max(64, bytes_diff)),
                "tcp_flags_syn": 1,
                "tcp_flags_ack": 1,
                "tcp_flags_rst": 0,
                "tcp_flags_fin": 0
            }
            
            print(f"[*] System throughput: {bytes_diff} Bytes across {pkts_diff} packets over {dt:.2f}s. Streaming telemetry...")
            send_payload(server_url, payload)
            
            last_stats = current_stats
            last_time = now
            
    except KeyboardInterrupt:
        print("\n[-] Monitoring stopped.")

# ----------------- Mock Simulation Mode -----------------

def run_mock_mode(server_url, device_id, name):
    local_ip = get_local_ip()
    print(f"\n[+] Starting Mock Traffic Injector...")
    print(f"    Target Server API : {server_url}")
    print(f"    Device Node ID    : {device_id}")
    print("="*60 + "\n")
    
    register_device(server_url, device_id, name, "IoT Board")
    
    try:
        while True:
            roll = random.random()
            
            if roll > 0.85:
                # Attack injection (15% chance)
                attack = random.choice(["DDoS", "PortScan", "BruteForce"])
                print(f"[!] INJECTING simulated {attack} attack pattern...")
                
                if attack == "DDoS":
                    for _ in range(5):
                        payload = {
                            "device_id": device_id,
                            "src_ip": local_ip,
                            "dst_ip": "192.168.1.1",
                            "src_port": random.randint(1024, 65535),
                            "dst_port": 80,
                            "protocol": 6,
                            "flow_duration": random.uniform(0.001, 0.01),
                            "packet_count": random.randint(400, 800),
                            "byte_count": random.randint(25000, 50000),
                            "tcp_flags_syn": 1,
                            "tcp_flags_ack": 0,
                            "tcp_flags_rst": 0,
                            "tcp_flags_fin": 0
                        }
                        send_payload(server_url, payload)
                        time.sleep(0.1)
                elif attack == "PortScan":
                    base_port = random.randint(20, 100)
                    for offset in range(8):
                        payload = {
                            "device_id": device_id,
                            "src_ip": local_ip,
                            "dst_ip": "192.168.1.1",
                            "src_port": random.randint(5000, 6000),
                            "dst_port": base_port + offset,
                            "protocol": 6,
                            "flow_duration": 0.05,
                            "packet_count": 2,
                            "byte_count": 80,
                            "tcp_flags_syn": 1,
                            "tcp_flags_ack": 0,
                            "tcp_flags_rst": 0,
                            "tcp_flags_fin": 0
                        }
                        send_payload(server_url, payload)
                        time.sleep(0.1)
                else: # BruteForce
                    for _ in range(6):
                        payload = {
                            "device_id": device_id,
                            "src_ip": local_ip,
                            "dst_ip": "192.168.1.1",
                            "src_port": random.randint(1024, 65535),
                            "dst_port": 22,
                            "protocol": 6,
                            "flow_duration": random.uniform(1.0, 3.0),
                            "packet_count": random.randint(20, 35),
                            "byte_count": random.randint(2000, 3800),
                            "tcp_flags_syn": 1,
                            "tcp_flags_ack": 1,
                            "tcp_flags_rst": 0,
                            "tcp_flags_fin": 0
                        }
                        send_payload(server_url, payload)
                        time.sleep(0.3)
            else:
                # Normal flows (85% chance)
                service = random.choice(["MQTT", "HTTPS", "DNS"])
                if service == "MQTT":
                    payload = {
                        "device_id": device_id,
                        "src_ip": local_ip,
                        "dst_ip": "192.168.1.10",
                        "src_port": random.randint(1024, 65535),
                        "dst_port": 1883,
                        "protocol": 6,
                        "flow_duration": random.uniform(0.1, 4.0),
                        "packet_count": random.randint(3, 10),
                        "byte_count": random.randint(128, 800),
                        "tcp_flags_syn": 1,
                        "tcp_flags_ack": 1
                    }
                elif service == "HTTPS":
                    payload = {
                        "device_id": device_id,
                        "src_ip": local_ip,
                        "dst_ip": "172.217.16.142",
                        "src_port": random.randint(1024, 65535),
                        "dst_port": 443,
                        "protocol": 6,
                        "flow_duration": random.uniform(0.5, 3.0),
                        "packet_count": random.randint(15, 50),
                        "byte_count": random.randint(1024, 35000),
                        "tcp_flags_syn": 1,
                        "tcp_flags_ack": 1
                    }
                else: # DNS
                    payload = {
                        "device_id": device_id,
                        "src_ip": local_ip,
                        "dst_ip": "8.8.8.8",
                        "src_port": random.randint(1024, 65535),
                        "dst_port": 53,
                        "protocol": 17,
                        "flow_duration": random.uniform(0.01, 0.1),
                        "packet_count": 2,
                        "byte_count": random.randint(120, 250)
                    }
                print(f"[+] Reporting benign {service} traffic flow statistics...")
                send_payload(server_url, payload)
                
            time.sleep(random.uniform(3.0, 7.0))
            
    except KeyboardInterrupt:
        print("\n[-] Injector stopped.")

# ----------------- CLI Entry Point -----------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Secure.IoT IDS Client Sniffing Agent")
    parser.add_argument("--server", type=str, default="http://127.0.0.1:8000/api/report-flow",
                        help="FastAPI ingestion endpoint URL")
    parser.add_argument("--device", type=str, default="laptop-agent",
                        help="Unique alphanumeric device identifier")
    parser.add_argument("--name", type=str, default="My Laptop Card",
                        help="Human-friendly node name")
    parser.add_argument("--mode", type=str, choices=["sniffer", "system", "mock"], default="system",
                        help="Mode: 'sniffer' (captures active network packets), 'system' (polls system throughput), 'mock' (simulated telemetry)")
    parser.add_argument("--interface", type=str, default=None,
                        help="Network card interface to sniff (sniffer mode only)")
                        
    args = parser.parse_args()
    
    # Autocorrect mode if Scapy is missing but sniffer requested
    if args.mode == "sniffer" and not HAS_SCAPY:
        print("[!] Warning: Scapy module not found. Sniffing packets is unavailable.")
        print("    Automatically falling back to 'system' throughput mode.")
        args.mode = "system"
        
    # Execute chosen mode
    if args.mode == "sniffer":
        run_sniffer_mode(args.server, args.device, args.name, args.interface)
    elif args.mode == "system":
        run_system_mode(args.server, args.device, args.name)
    else:
        run_mock_mode(args.server, args.device, args.name)
