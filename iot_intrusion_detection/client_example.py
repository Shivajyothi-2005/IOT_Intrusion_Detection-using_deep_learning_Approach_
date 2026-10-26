#!/usr/bin/env python3
import sys
import time
import argparse
import random
import json
import urllib.request
import urllib.error
import socket

# Try importing scapy for sniffer mode
try:
    from scapy.all import sniff, IP, TCP, UDP
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False

def get_local_ip():
    """Get this device's local network IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Global connection tracker for Sniffer mode
# Key: (src_ip, dst_ip, src_port, dst_port, protocol)
# Value: {start_time, last_time, packet_count, byte_count, syn, ack, rst, fin}
flow_table = {}
flow_lock = False # simple lock

def get_proto_name(proto):
    if proto == 6: return "TCP"
    if proto == 17: return "UDP"
    return str(proto)

def send_payload(server_url, payload):
    """Sends the flow telemetry payload using standard urllib to avoid third-party dependencies"""
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        server_url, 
        data=data, 
        headers={'Content-Type': 'application/json', 'User-Agent': 'IDS-Client/1.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"[-] Network Error reporting to server: {e.reason}")
    except socket.timeout:
        print("[-] Connection Timeout reporting to server.")
    except Exception as e:
        print(f"[-] Error reporting to server: {e}")
    return None

# ----------------- Interface Sniffer Mode (Scapy) -----------------

def packet_callback(pkt):
    global flow_table, flow_lock
    if flow_lock:
        return
        
    # We only analyze IP packets (IPv4/IPv6)
    if not pkt.haslayer(IP):
        return
        
    ip_layer = pkt[IP]
    proto = ip_layer.proto
    
    # Track only TCP or UDP for simplicity
    if proto not in [6, 17]:
        return
        
    src_ip = ip_layer.src
    dst_ip = ip_layer.dst
    
    # Determine ports
    if proto == 6 and pkt.haslayer(TCP):
        tcp_layer = pkt[TCP]
        src_port = tcp_layer.sport
        dst_port = tcp_layer.dport
        # Check TCP flags
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
    print(f"[+] Started packet flow aggregation flush loop. Window: 2.0s")
    while True:
        time.sleep(2.0)
        
        # Lock and swap flow table to process current buffer
        flow_lock = True
        current_flows = flow_table
        flow_table = {}
        flow_lock = False
        
        if not current_flows:
            continue
            
        print(f"[*] Aggregated {len(current_flows)} active connections. Streaming to IDS...")
        
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
            
            # Send payload
            send_payload(server_url, payload)

def run_sniffer_mode(server_url, device_id, interface):
    if not HAS_SCAPY:
        print("[-] ERROR: Scapy module is not installed. Scapy is required for sniffer mode.")
        print("    Please run: pip install scapy")
        print("    Or run this client in Mock mode: --mode mock")
        sys.exit(1)
        
    print(f"\n[+] Starting Local Interface Sniffing Client...")
    print(f"    Target Server API: {server_url}")
    print(f"    Reporting Device : {device_id}")
    print(f"    Interface        : {interface if interface else 'Default Interface'}")
    print(f"    CRITICAL NOTE    : Sniffer mode requires Administrator (root) privileges.")
    print("="*60 + "\n")
    
    # Start the aggregation loop in a background thread
    import threading
    flush_thread = threading.Thread(target=flush_flows_loop, args=(server_url, device_id), daemon=True)
    flush_thread.start()
    
    # Start sniffing (blocks execution)
    try:
        if interface:
            sniff(iface=interface, prn=packet_callback, store=0)
        else:
            sniff(prn=packet_callback, store=0)
    except KeyboardInterrupt:
        print("\n[-] Sniffing stopped by user.")
    except Exception as e:
        print(f"[-] Permission error or sniffing error: {e}")
        print("    Try running the terminal as Administrator/sudo, or run --mode mock")

# ----------------- Socket Telemetry / Mock Mode -----------------

def run_mock_mode(server_url, device_id):
    local_ip = get_local_ip()
    print(f"\n[+] Starting Simulated Telemetry / Mock Client...")
    print(f"    Target Server API: {server_url}")
    print(f"    Reporting Device : {device_id}")
    print(f"    Detected IP      : {local_ip}")
    print("    This mode does not require root permissions or packages.")
    print("="*60 + "\n")
    
    # Categories of mock flows we can generate:
    # 1. Normal (MQTT, HTTPS, DNS, NTP)
    # 2. PortScan (sequential port requests)
    # 3. DDoS (heavy volume SYN packets)
    # 4. BruteForce (repeated login hits to port 22)
    
    try:
        while True:
            # Pick a scenario
            roll = random.random()
            
            if roll > 0.85:
                # 15% chance to simulate an attack traffic flow from this device
                attack_type = random.choice(["DDoS", "PortScan", "BruteForce"])
                print(f"[!] Generating simulated {attack_type} telemetry sequence...")
                
                if attack_type == "DDoS":
                    # Heavy volume, small packets
                    for _ in range(5):
                        payload = {
                            "device_id": device_id,
                            "src_ip": local_ip,
                            "dst_ip": "192.168.1.1",
                            "src_port": random.randint(1024, 65535),
                            "dst_port": 80,
                            "protocol": 6,
                            "flow_duration": random.uniform(0.001, 0.02),
                            "packet_count": random.randint(300, 600),
                            "byte_count": random.randint(19200, 38400),
                            "tcp_flags_syn": 1,
                            "tcp_flags_ack": 0,
                            "tcp_flags_rst": 0,
                            "tcp_flags_fin": 0
                        }
                        send_payload(server_url, payload)
                        time.sleep(0.2)
                
                elif attack_type == "PortScan":
                    # Multiple sequential destination ports
                    base_port = random.randint(20, 80)
                    for offset in range(10):
                        payload = {
                            "device_id": device_id,
                            "src_ip": local_ip,
                            "dst_ip": "192.168.1.1",
                            "src_port": random.randint(3000, 4000),
                            "dst_port": base_port + offset,
                            "protocol": 6,
                            "flow_duration": random.uniform(0.1, 0.3),
                            "packet_count": random.randint(1, 3),
                            "byte_count": random.randint(40, 120),
                            "tcp_flags_syn": 1,
                            "tcp_flags_ack": 0,
                            "tcp_flags_rst": 0,
                            "tcp_flags_fin": 0
                        }
                        send_payload(server_url, payload)
                        time.sleep(0.1)
                
                else: # BruteForce
                    # Repeated connections to SSH
                    for _ in range(8):
                        payload = {
                            "device_id": device_id,
                            "src_ip": local_ip,
                            "dst_ip": "192.168.1.1",
                            "src_port": random.randint(1024, 65535),
                            "dst_port": 22,
                            "protocol": 6,
                            "flow_duration": random.uniform(1.5, 4.0),
                            "packet_count": random.randint(20, 40),
                            "byte_count": random.randint(2200, 4400),
                            "tcp_flags_syn": 1,
                            "tcp_flags_ack": 1,
                            "tcp_flags_rst": 0,
                            "tcp_flags_fin": 0
                        }
                        send_payload(server_url, payload)
                        time.sleep(0.4)
            else:
                # 85% normal traffic flow
                # Choose a benign protocol
                traffic_type = random.choice(["MQTT", "HTTPS", "DNS", "NTP"])
                
                if traffic_type == "MQTT":
                    # TCP port 1883
                    payload = {
                        "device_id": device_id,
                        "src_ip": local_ip,
                        "dst_ip": "192.168.1.10", # local MQTT broker
                        "src_port": random.randint(1024, 65535),
                        "dst_port": 1883,
                        "protocol": 6,
                        "flow_duration": random.uniform(0.2, 5.0),
                        "packet_count": random.randint(4, 15),
                        "byte_count": random.randint(256, 1500),
                        "tcp_flags_syn": 1,
                        "tcp_flags_ack": 1,
                        "tcp_flags_rst": 0,
                        "tcp_flags_fin": 0
                    }
                elif traffic_type == "HTTPS":
                    # TCP port 443
                    payload = {
                        "device_id": device_id,
                        "src_ip": local_ip,
                        "dst_ip": "142.250.190.46", # Google IP
                        "src_port": random.randint(1024, 65535),
                        "dst_port": 443,
                        "protocol": 6,
                        "flow_duration": random.uniform(0.5, 3.5),
                        "packet_count": random.randint(15, 60),
                        "byte_count": random.randint(1024, 50000),
                        "tcp_flags_syn": 1,
                        "tcp_flags_ack": 1,
                        "tcp_flags_rst": 0,
                        "tcp_flags_fin": 0
                    }
                elif traffic_type == "DNS":
                    # UDP port 53
                    payload = {
                        "device_id": device_id,
                        "src_ip": local_ip,
                        "dst_ip": "8.8.8.8", # Google DNS
                        "src_port": random.randint(1024, 65535),
                        "dst_port": 53,
                        "protocol": 17, # UDP
                        "flow_duration": random.uniform(0.01, 0.15),
                        "packet_count": 2,
                        "byte_count": random.randint(120, 240),
                        "tcp_flags_syn": 0,
                        "tcp_flags_ack": 0,
                        "tcp_flags_rst": 0,
                        "tcp_flags_fin": 0
                    }
                else: # NTP
                    # UDP port 123
                    payload = {
                        "device_id": device_id,
                        "src_ip": local_ip,
                        "dst_ip": "129.6.15.28",
                        "src_port": random.randint(1024, 65535),
                        "dst_port": 123,
                        "protocol": 17,
                        "flow_duration": random.uniform(0.02, 0.2),
                        "packet_count": 2,
                        "byte_count": 192,
                        "tcp_flags_syn": 0,
                        "tcp_flags_ack": 0,
                        "tcp_flags_rst": 0,
                        "tcp_flags_fin": 0
                    }
                
                print(f"[+] Reporting normal {traffic_type} flow flow statistics...")
                send_payload(server_url, payload)
                
            # Sleep between flows
            time.sleep(random.uniform(4.0, 9.0))
            
    except KeyboardInterrupt:
        print("\n[-] Client stopped.")

# ----------------- Argument Parser -----------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Secure.IoT IDS Client Sniffing Agent")
    parser.add_argument("--server", type=str, default="http://localhost:8000/api/report-flow",
                        help="FastAPI ingestion endpoint URL (default: http://localhost:8000/api/report-flow)")
    parser.add_argument("--device", type=str, default="external-pi-node",
                        help="Unique device identifier (default: external-pi-node)")
    parser.add_argument("--mode", type=str, choices=["sniffer", "mock"], default="mock",
                        help="Operation mode: 'sniffer' (sniffs real packets, needs root/scapy) or 'mock' (simulates telemetry, default)")
    parser.add_argument("--interface", type=str, default=None,
                        help="Network card interface to sniff (e.g. eth0, wlan0, en0). Defaults to automatic selection.")
                        
    args = parser.parse_args()
    
    # Run loop
    if args.mode == "sniffer":
        run_sniffer_mode(args.server, args.device, args.interface)
    else:
        run_mock_mode(args.server, args.device)
