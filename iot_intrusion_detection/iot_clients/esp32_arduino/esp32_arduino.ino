/*
  SECURE.IoT IDS ESP32 Client Node
  
  This sketch runs on an ESP32 board, connects to local Wi-Fi, 
  and reports mock sensor state or connection volume telemetry 
  to the central FastAPI IDS server.
*/

#include <WiFi.h>
#include <HTTPClient.h>

// WiFi Settings - Replace with your network details
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// FastAPI IDS Server Ingestion Endpoint
// Replace with your server's local IP address
const char* serverUrl = "http://192.168.1.100:8000/api/report-flow";

// Node details
const char* deviceId = "esp32-thermostat-01";
const char* deviceName = "ESP32 Thermostat Node";

// Setup GPIO pins
const int alarmTogglePin = 12; // Pull HIGH to trigger a simulated DDoS attack signature
const int statusLedPin = 2;    // Built-in LED on most ESP32 boards

void setup() {
  Serial.begin(115200);
  pinMode(alarmTogglePin, INPUT_PULLDOWN);
  pinMode(statusLedPin, OUTPUT);

  // Connect to WiFi
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(statusLedPin, !digitalRead(statusLedPin)); // Flash LED during connect
  }

  digitalWrite(statusLedPin, HIGH); // LED solid on connection
  Serial.println("");
  Serial.println("Wi-Fi connected.");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    // Read toggle status to determine flow profile
    bool attackTriggered = (digitalRead(alarmTogglePin) == HIGH);
    
    String jsonPayload;
    
    if (attackTriggered) {
      // Send simulated high volume SYN flood (DDoS anomaly)
      Serial.println("[!] GPIO Trigger: Sending simulated DDoS telemetry signature...");
      jsonPayload = "{"
        "\"device_id\":\"" + String(deviceId) + "\","
        "\"src_ip\":\"" + WiFi.localIP().toString() + "\","
        "\"dst_ip\":\"192.168.1.1\","
        "\"src_port\":" + String(random(1024, 65535)) + ","
        "\"dst_port\":80,"
        "\"protocol\":6,"
        "\"flow_duration\":0.02,"
        "\"packet_count\":" + String(random(300, 500)) + ","
        "\"byte_count\":" + String(random(20000, 35000)) + ","
        "\"tcp_flags_syn\":1,"
        "\"tcp_flags_ack\":0,"
        "\"tcp_flags_rst\":0,"
        "\"tcp_flags_fin\":0"
      "}";
    } else {
      // Send normal benign MQTT connection flow statistics
      Serial.println("[*] Streaming normal telemetry status...");
      jsonPayload = "{"
        "\"device_id\":\"" + String(deviceId) + "\","
        "\"src_ip\":\"" + WiFi.localIP().toString() + "\","
        "\"dst_ip\":\"192.168.1.10\","
        "\"src_port\":" + String(random(1024, 65535)) + ","
        "\"dst_port\":1883,"
        "\"protocol\":6," // TCP
        "\"flow_duration\":1.5,"
        "\"packet_count\":" + String(random(5, 12)) + ","
        "\"byte_count\":" + String(random(300, 800)) + ","
        "\"tcp_flags_syn\":1,"
        "\"tcp_flags_ack\":1,"
        "\"tcp_flags_rst\":0,"
        "\"tcp_flags_fin\":0"
      "}";
    }

    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.print("Response Code: ");
      Serial.print(httpResponseCode);
      Serial.print(" | ");
      Serial.println(response);
    } else {
      Serial.print("Error sending POST request: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("Wi-Fi Disconnected. Reconnecting...");
    WiFi.begin(ssid, password);
  }

  // Send updates every 5 seconds
  delay(5000);
}
