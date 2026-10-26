// Front-end JavaScript logic for SECURE.IoT IDS Dashboard
let socket = null;
let reconnectTimer = null;
let charts = {};
let localDevices = [];
let localFlowHistory = [];
let localSummary = {};
let simulatorEnabled = true;
let soundEnabled = true;
let lastThreatNodeId = null;

// Web Audio API Synthesizer for alarm sounds
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playAlarmSound() {
    if (!soundEnabled) return;
    try {
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        
        // Synthesize a dual-tone alarm siren
        const osc1 = audioCtx.createOscillator();
        const osc2 = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        
        osc1.type = 'sawtooth';
        osc2.type = 'sine';
        
        osc1.frequency.setValueAtTime(520, audioCtx.currentTime); // C5
        osc2.frequency.setValueAtTime(660, audioCtx.currentTime); // E5
        
        // Frequency sweep (siren effect)
        osc1.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.15);
        osc1.frequency.exponentialRampToValueAtTime(520, audioCtx.currentTime + 0.3);
        
        gainNode.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);
        
        osc1.connect(gainNode);
        osc2.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        
        osc1.start();
        osc2.start();
        osc1.stop(audioCtx.currentTime + 0.35);
        osc2.stop(audioCtx.currentTime + 0.35);
    } catch (e) {
        console.warn("Failed to play synthesized alarm sound: ", e);
    }
}

// ----------------- Page Tab Switching -----------------

const tabButtons = document.querySelectorAll('.nav-btn');
const tabContents = document.querySelectorAll('.tab-content');
const pageTitle = document.getElementById('page-title');
const pageSubtitle = document.getElementById('page-subtitle');

const pageDetails = {
    analytics: {
        title: "Analytics Hub",
        subtitle: "Real-time deep learning cyber security threat detection for IoT devices"
    },
    monitor: {
        title: "IDS Live Monitor",
        subtitle: "Real-time packet logs console streams with PyTorch classification overlays"
    },
    topology: {
        title: "Network Topology Map",
        subtitle: "Live security threat visualization of all connected workstation and IoT nodes"
    },
    devices: {
        title: "Device Registry",
        subtitle: "Multi-user network device manager and telemetry streaming guides"
    }
};

tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');
        
        // Toggle Active button
        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Toggle Active content
        tabContents.forEach(content => {
            if (content.id === `${targetTab}-page`) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
        
        // Update headers
        pageTitle.innerText = pageDetails[targetTab].title;
        pageSubtitle.innerText = pageDetails[targetTab].subtitle;
        
        // Redraw charts if switching back to analytics to prevent rendering dimensions issues
        if (targetTab === 'analytics') {
            updateCharts();
        } else if (targetTab === 'topology') {
            drawNetworkTopology();
        }
    });
});

// Update UTC clock
function updateClock() {
    const timeDisplay = document.getElementById('current-time');
    const now = new Date();
    const timeStr = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
    timeDisplay.innerText = timeStr;
}
setInterval(updateClock, 1000);
updateClock();

// Sound toggle button
const soundBtn = document.getElementById('sound-toggle');
soundBtn.addEventListener('click', () => {
    soundEnabled = !soundEnabled;
    if (soundEnabled) {
        soundBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
        soundBtn.classList.remove('muted');
        soundBtn.style.color = 'var(--clr-cyan)';
    } else {
        soundBtn.innerHTML = '<i class="fa-solid fa-volume-xmark"></i>';
        soundBtn.classList.add('muted');
        soundBtn.style.color = 'var(--text-dark)';
    }
});

// ----------------- WebSocket Connection Management -----------------

function connectWebSocket() {
    const wsStatusDot = document.getElementById('ws-status-dot');
    const wsStatusText = document.getElementById('ws-status-text');
    
    // Dynamically resolve websocket url matching server address
    const host = window.location.host || 'localhost:8000';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${host}/ws`;
    
    console.log(`[WebSocket] Connecting to: ${wsUrl}`);
    
    if (socket) {
        socket.close();
    }
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
        console.log('[WebSocket] Connection established.');
        wsStatusDot.className = "status-dot online";
        wsStatusText.innerText = "System Online";
        if (reconnectTimer) {
            clearInterval(reconnectTimer);
            reconnectTimer = null;
        }
        
        // Fetch server IP information
        fetchServerInfo();
    };
    
    socket.onclose = () => {
        console.warn('[WebSocket] Disconnected from server.');
        wsStatusDot.className = "status-dot offline";
        wsStatusText.innerText = "Reconnecting...";
        
        // Auto-reconnect loop
        if (!reconnectTimer) {
            reconnectTimer = setInterval(connectWebSocket, 4000);
        }
    };
    
    socket.onerror = (err) => {
        console.error('[WebSocket] Error occurred: ', err);
    };
    
    socket.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            handleWebSocketMessage(payload);
        } catch (e) {
            console.error('Error parsing WS message: ', e);
        }
    };
}

// ----------------- WebSocket Message Handler -----------------

function handleWebSocketMessage(payload) {
    const type = payload.type;
    
    if (type === 'init_data') {
        localDevices = payload.devices || [];
        localFlowHistory = payload.recent_flows || [];
        localSummary = payload.summary || {};
        simulatorEnabled = payload.simulator_enabled;
        
        // Sync simulator checkbox state
        const checkbox = document.getElementById('simulator-toggle-checkbox');
        if (checkbox) checkbox.checked = simulatorEnabled;
        updateSimulatorBadge(simulatorEnabled);
        
        // Update views
        updateStatsCounters();
        renderDeviceCards();
        renderMonitorLogs();
        initCharts();
        updateIntegrationGuide();
        drawNetworkTopology();
    }
    else if (type === 'flow_event') {
        const flow = payload.flow;
        localDevices = payload.devices || [];
        localSummary = payload.summary || {};
        
        // Add flow to starting index of array
        localFlowHistory.unshift(flow);
        if (localFlowHistory.length > 200) {
            localFlowHistory.pop();
        }
        
        // Update views
        updateStatsCounters();
        renderDeviceCards();
        appendLogToConsole(flow);
        updateCharts();
        
        // Dynamic Network Map pulse animation
        const isAnomaly = flow.class_name !== 'Normal';
        animateFlowPulse(flow.device_id, isAnomaly);
        
        // Alert trigger
        if (isAnomaly) {
            enqueueThreatToast(flow);
            playAlarmSound();
        }
    }
    else if (type === 'devices_update') {
        localDevices = payload.devices || [];
        localSummary = payload.summary || {};
        renderDeviceCards();
        updateStatsCounters();
        updateCharts();
        updateIntegrationGuide();
        drawNetworkTopology();
    }
    else if (type === 'simulator_update') {
        simulatorEnabled = payload.enabled;
        const checkbox = document.getElementById('simulator-toggle-checkbox');
        if (checkbox) checkbox.checked = simulatorEnabled;
        updateSimulatorBadge(simulatorEnabled);
    }
}

// ----------------- Stats Counters Updates -----------------

function updateStatsCounters() {
    const flowsVal = document.getElementById('stat-total-flows');
    const anomaliesVal = document.getElementById('stat-anomalies');
    const activeVal = document.getElementById('stat-active-devices');
    const indexVal = document.getElementById('stat-threat-index');
    const indexStatus = document.getElementById('stat-threat-status');
    const indexCard = document.getElementById('threat-index-card');
    const flowTrend = document.getElementById('stat-flow-trend');
    const anomaliesPct = document.getElementById('stat-anomalies-pct');

    if (!localSummary) return;

    flowsVal.innerText = localSummary.total_flows || 0;
    anomaliesVal.innerText = localSummary.anomalies || 0;
    activeVal.innerText = localSummary.online_devices || 0;
    
    const threatIdx = localSummary.threat_index || 0;
    indexVal.innerText = `${threatIdx}%`;

    // Dynamic warning glows
    indexCard.className = "stat-card";
    if (threatIdx > 40) {
        indexStatus.innerText = "CRITICAL BREACH";
        indexStatus.style.color = "var(--clr-danger)";
        indexCard.classList.add("danger-glow");
    } else if (threatIdx > 10) {
        indexStatus.innerText = "THREAT DETECTED";
        indexStatus.style.color = "var(--clr-warning)";
        indexCard.classList.add("warning-glow");
    } else {
        indexStatus.innerText = "SECURE";
        indexStatus.style.color = "var(--clr-green)";
    }

    if (localSummary.total_flows > 0) {
        flowTrend.innerText = "Active network packet streams";
        const pct = ((localSummary.anomalies / localSummary.total_flows) * 100).toFixed(1);
        anomaliesPct.innerText = `${pct}% threat ratio`;
    }
}

// ----------------- Chart.js Operations -----------------

function initCharts() {
    // 1. Flow Timeline Chart (Line)
    const ctxTimeline = document.getElementById('flowTimelineChart').getContext('2d');
    if (charts.timeline) charts.timeline.destroy();
    
    // Extract timeseries data
    const timelineData = getTimelineDataPoints();

    charts.timeline = new Chart(ctxTimeline, {
        type: 'line',
        data: {
            labels: timelineData.labels,
            datasets: [
                {
                    label: 'Benign Flows',
                    data: timelineData.benign,
                    borderColor: '#00f0ff',
                    backgroundColor: 'rgba(0, 240, 255, 0.05)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2
                },
                {
                    label: 'Intrusion Flows',
                    data: timelineData.attacks,
                    borderColor: '#ff0055',
                    backgroundColor: 'rgba(255, 0, 85, 0.05)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#8fa0c4', font: { family: 'Outfit' } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.03)' },
                    ticks: { color: '#8fa0c4', font: { family: 'Outfit', size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.03)' },
                    ticks: { color: '#8fa0c4', font: { family: 'Outfit' } },
                    suggestedMax: 10
                }
            }
        }
    });

    // 2. Threat Classification Distribution (Doughnut)
    const ctxPie = document.getElementById('threatPieChart').getContext('2d');
    if (charts.pie) charts.pie.destroy();
    
    const classCounts = localSummary.class_counts || { Normal: 0, DDoS: 0, PortScan: 0, BruteForce: 0 };

    charts.pie = new Chart(ctxPie, {
        type: 'doughnut',
        data: {
            labels: ['Normal', 'DDoS', 'PortScan', 'BruteForce'],
            datasets: [{
                data: [classCounts.Normal, classCounts.DDoS, classCounts.PortScan, classCounts.BruteForce],
                backgroundColor: ['#39d353', '#ff0055', '#ffb700', '#7a22ff'],
                borderColor: 'var(--bg-secondary)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#8fa0c4', font: { family: 'Outfit' } }
                }
            },
            cutout: '65%'
        }
    });

    // 3. Traffic volume by Device (Horizontal Bar)
    const ctxBar = document.getElementById('deviceBarChart').getContext('2d');
    if (charts.bar) charts.bar.destroy();

    const deviceLabels = localDevices.map(d => d.name);
    const deviceData = localDevices.map(d => d.total_flows);
    const deviceAnomalies = localDevices.map(d => d.anomalies_detected);

    charts.bar = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: deviceLabels,
            datasets: [
                {
                    label: 'Total Traffic',
                    data: deviceData,
                    backgroundColor: 'rgba(0, 240, 255, 0.35)',
                    borderColor: 'var(--clr-cyan)',
                    borderWidth: 1
                },
                {
                    label: 'Anomalies',
                    data: deviceAnomalies,
                    backgroundColor: 'rgba(255, 0, 85, 0.65)',
                    borderColor: 'var(--clr-danger)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#8fa0c4', font: { family: 'Outfit' } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.03)' },
                    ticks: { color: '#8fa0c4', font: { family: 'Outfit' } }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#8fa0c4', font: { family: 'Outfit' } }
                }
            }
        }
    });
}

function updateCharts() {
    if (!charts.timeline || !charts.pie || !charts.bar) return;
    
    // 1. Update Timeline
    const timelineData = getTimelineDataPoints();
    charts.timeline.data.labels = timelineData.labels;
    charts.timeline.data.datasets[0].data = timelineData.benign;
    charts.timeline.data.datasets[1].data = timelineData.attacks;
    charts.timeline.update('none'); // silent update

    // 2. Update Pie
    const classCounts = localSummary.class_counts || { Normal: 0, DDoS: 0, PortScan: 0, BruteForce: 0 };
    charts.pie.data.datasets[0].data = [
        classCounts.Normal, 
        classCounts.DDoS, 
        classCounts.PortScan, 
        classCounts.BruteForce
    ];
    charts.pie.update('none');

    // 3. Update Bar
    charts.bar.data.labels = localDevices.map(d => d.name);
    charts.bar.data.datasets[0].data = localDevices.map(d => d.total_flows);
    charts.bar.data.datasets[1].data = localDevices.map(d => d.anomalies_detected);
    charts.bar.update('none');
}

function getTimelineDataPoints() {
    // Bucket history into 10 intervals of time
    const bucketsCount = 10;
    const now = Date.now() / 1000;
    const range = 600; // Lookback range of last 10 minutes
    const step = range / bucketsCount;
    
    const labels = [];
    const benign = Array(bucketsCount).fill(0);
    const attacks = Array(bucketsCount).fill(0);
    
    for (let i = 0; i < bucketsCount; i++) {
        const bucketTime = now - (bucketsCount - 1 - i) * step;
        const dateObj = new Date(bucketTime * 1000);
        labels.push(`${String(dateObj.getMinutes()).padStart(2, '0')}:${String(dateObj.getSeconds()).padStart(2, '0')}`);
    }
    
    // Distribute flows into buckets
    localFlowHistory.forEach(f => {
        const flowTime = f.timestamp;
        const diff = now - flowTime;
        if (diff >= 0 && diff < range) {
            const bucketIndex = Math.floor((range - diff) / step);
            if (bucketIndex >= 0 && bucketIndex < bucketsCount) {
                if (f.class_name === 'Normal') {
                    benign[bucketIndex]++;
                } else {
                    attacks[bucketIndex]++;
                }
            }
        }
    });

    return { labels, benign, attacks };
}

// ----------------- Console Log Screen UI -----------------

function renderMonitorLogs() {
    const logsList = document.getElementById('console-logs-list');
    logsList.innerHTML = '';
    
    if (localFlowHistory.length === 0) {
        logsList.innerHTML = `
            <div class="logger-placeholder">
                <i class="fa-solid fa-spinner fa-spin"></i>
                <p>Awaiting live traffic telemetry...</p>
            </div>`;
        return;
    }
    
    const activeFilter = document.querySelector('.filter-btn.active').getAttribute('data-filter');
    
    localFlowHistory.forEach(flow => {
        if (activeFilter === 'normal' && flow.class_name !== 'Normal') return;
        if (activeFilter === 'threat' && flow.class_name === 'Normal') return;
        
        const row = createLogRowElement(flow);
        logsList.appendChild(row);
    });
}

function appendLogToConsole(flow) {
    const logsList = document.getElementById('console-logs-list');
    
    // Check if active filter matches the incoming flow
    const activeFilter = document.querySelector('.filter-btn.active').getAttribute('data-filter');
    if (activeFilter === 'normal' && flow.class_name !== 'Normal') return;
    if (activeFilter === 'threat' && flow.class_name === 'Normal') return;
    
    // Remove placeholder if present
    const placeholder = logsList.querySelector('.logger-placeholder');
    if (placeholder) {
        logsList.innerHTML = '';
    }
    
    const row = createLogRowElement(flow);
    logsList.insertBefore(row, logsList.firstChild);
    
    // Cap screen display rows
    if (logsList.children.length > 150) {
        logsList.removeChild(logsList.lastChild);
    }
}

function createLogRowElement(flow) {
    const row = document.createElement('div');
    row.className = 'log-row';
    
    const timeStr = new Date(flow.timestamp * 1000).toLocaleTimeString();
    const protoStr = flow.protocol === 6 ? 'TCP' : flow.protocol === 17 ? 'UDP' : `Proto ${flow.protocol}`;
    
    // Style badges
    let badgeClass = 'normal';
    let iconClass = 'fa-solid fa-circle-check';
    if (flow.class_name === 'DDoS') {
        badgeClass = 'ddos';
        iconClass = 'fa-solid fa-radiation';
    } else if (flow.class_name === 'PortScan') {
        badgeClass = 'portscan';
        iconClass = 'fa-solid fa-magnifying-glass-chart';
    } else if (flow.class_name === 'BruteForce') {
        badgeClass = 'bruteforce';
        iconClass = 'fa-solid fa-unlock-keyhole';
    }

    row.innerHTML = `
        <div class="col-time">${timeStr}</div>
        <div class="col-device">${flow.device_name}</div>
        <div class="col-flow">
            <span class="proto-tag">${protoStr}</span>
            ${flow.src_ip}:${flow.src_port} <i class="fa-solid fa-arrow-right-long" style="font-size:0.7rem; color:var(--text-dark);"></i> ${flow.dst_ip}:${flow.dst_port}
        </div>
        <div class="col-packets">${flow.packet_count}</div>
        <div class="col-bytes">${formatBytes(flow.byte_count)}</div>
        <div class="col-rate">${Math.round(flow.packet_rate)}/s</div>
        <div class="col-classification">
            <span class="badge ${badgeClass}"><i class="${iconClass}"></i> ${flow.class_name}</span>
        </div>
        <div class="col-action"><i class="fa-solid fa-chevron-right"></i></div>
    `;
    
    // Add click detail action
    row.addEventListener('click', () => {
        openFlowModal(flow);
    });
    
    return row;
}

function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
}

// Log Filters
const filterBtns = document.querySelectorAll('.filter-btn');
filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderMonitorLogs();
    });
});

// Clear screen
document.getElementById('clear-logs-btn').addEventListener('click', () => {
    localFlowHistory = [];
    renderMonitorLogs();
});

// ----------------- Device Management Grid -----------------

const deviceIcons = {
    "Server": "fa-solid fa-server",
    "IoT Board": "fa-solid fa-microchip",
    "Sensor": "fa-solid fa-temperature-half",
    "Mobile Phone": "fa-solid fa-mobile-screen-button",
    "Router": "fa-solid fa-route",
    "Laptop": "fa-solid fa-laptop"
};

function renderDeviceCards() {
    const grid = document.getElementById('device-cards-list');
    grid.innerHTML = '';
    
    if (localDevices.length === 0) {
        grid.innerHTML = '<p class="text-muted">No registered devices. Add a device to begin tracking.</p>';
        return;
    }
    
    localDevices.forEach(dev => {
        const card = document.createElement('div');
        card.className = 'device-card';
        
        // Check online state (active if seen in past 5 minutes)
        const isOnline = (Date.now() / 1000 - dev.last_seen) < 30;
        const statusClass = isOnline ? 'online' : 'offline';
        const icon = deviceIcons[dev.device_type] || 'fa-solid fa-laptop';
        
        card.innerHTML = `
            <div class="device-card-header">
                <div class="device-info-left">
                    <div class="device-type-icon"><i class="${icon}"></i></div>
                    <div class="device-meta-title">
                        <h4>${dev.name}</h4>
                        <span>${dev.device_id}</span>
                    </div>
                </div>
                <div class="device-header-actions" style="display: flex; align-items: center; gap: 8px;">
                    <span class="device-status-tag ${statusClass}">${isOnline ? 'Online' : 'Offline'}</span>
                    ${dev.device_id !== 'ids-server' ? `
                    <button class="btn-delete-device" data-id="${dev.device_id}" title="Remove Device" style="background: none; border: none; color: var(--clr-danger); cursor: pointer; padding: 2px 6px; font-size: 0.95rem; border-radius: 4px; transition: background 0.2s;">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                    ` : ''}
                </div>
            </div>
            
            <div class="device-card-stats">
                <div class="card-substat">
                    <span>Total Ingestion</span>
                    <p>${dev.total_flows} flows</p>
                </div>
                <div class="card-substat">
                    <span>Intrusions</span>
                    <p class="threat-count-text">${dev.anomalies_detected}</p>
                </div>
            </div>
            
            <div class="device-card-footer">
                <span class="ip">${dev.ip_address}</span>
                <span>Seen: ${new Date(dev.last_seen * 1000).toLocaleTimeString()}</span>
            </div>
        `;
        grid.appendChild(card);
    });
    
    // Add event listeners to delete buttons
    document.querySelectorAll('.btn-delete-device').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const devId = btn.getAttribute('data-id');
            const devName = localDevices.find(d => d.device_id === devId)?.name || devId;
            if (confirm(`Are you sure you want to remove device "${devName}"?`)) {
                try {
                    const response = await fetch(`/api/devices/${devId}`, {
                        method: 'DELETE'
                    });
                    if (response.ok) {
                        localDevices = localDevices.filter(d => d.device_id !== devId);
                        renderDevicesGrid();
                        // If topology page is currently active, redraw it to remove node
                        if (document.getElementById('topology-page').classList.contains('active')) {
                            drawNetworkTopology();
                        }
                    } else {
                        alert('Failed to remove device.');
                    }
                } catch (err) {
                    console.error('Error deleting device:', err);
                }
            }
        });
    });
}

// ----------------- Form Submission -----------------

const addDeviceForm = document.getElementById('add-device-form');
addDeviceForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('dev-name').value.trim();
    const deviceId = document.getElementById('dev-id').value.trim();
    const ipAddress = document.getElementById('dev-ip').value.trim();
    const deviceType = document.getElementById('dev-type').value;
    
    try {
        const response = await fetch('/api/devices', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, name, ip_address: ipAddress, device_type: deviceType })
        });
        
        if (response.ok) {
            addDeviceForm.reset();
            // Show short Success UI overlay
            const successToast = document.createElement('div');
            successToast.className = 'toast';
            successToast.style.borderColor = 'var(--clr-green)';
            successToast.innerHTML = `
                <i class="fa-solid fa-circle-check" style="color:var(--clr-green); font-size:1.75rem;"></i>
                <div class="toast-content">
                    <h4 style="color:var(--clr-green); font-size:0.95rem; font-weight:700; text-transform:uppercase;">Registration Successful</h4>
                    <p class="toast-desc">Device "${name}" added to surveillance matrix.</p>
                </div>
            `;
            
            const container = document.getElementById('toast-container');
            if (container) {
                container.appendChild(successToast);
            } else {
                document.body.appendChild(successToast);
                successToast.style.position = 'fixed';
                successToast.style.bottom = '30px';
                successToast.style.right = '40px';
                successToast.style.zIndex = '99999';
            }
            
            setTimeout(() => {
                successToast.remove();
            }, 3000);
        } else {
            const err = await response.json();
            alert(`Failed to add device: ${err.detail}`);
        }
    } catch (err) {
        console.error('Error submitting form: ', err);
    }
});

// ----------------- Simulator Ingestion Toggle -----------------

const simulatorCheckbox = document.getElementById('simulator-toggle-checkbox');
simulatorCheckbox.addEventListener('change', async () => {
    try {
        const response = await fetch('/api/simulator/toggle', { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            simulatorEnabled = data.simulator_enabled;
            updateSimulatorBadge(simulatorEnabled);
        }
    } catch (e) {
        console.error('Failed to toggle simulator: ', e);
    }
});

function updateSimulatorBadge(enabled) {
    const statusBadge = document.getElementById('simulator-status-badge');
    if (enabled) {
        statusBadge.innerText = 'Enabled';
        statusBadge.className = 'simulator-status-label';
    } else {
        statusBadge.innerText = 'Suspended (External Ingestion)';
        statusBadge.className = 'simulator-status-label disabled';
    }
}

// ----------------- Ingress Code Integrator Guides -----------------

const devSelector = document.getElementById('guide-device-selector');
devSelector.addEventListener('change', () => {
    generateSnippets();
});

function updateIntegrationGuide() {
    const currentVal = devSelector.value;
    devSelector.innerHTML = '';
    
    localDevices.forEach(dev => {
        const opt = document.createElement('option');
        opt.value = dev.device_id;
        opt.innerText = `${dev.name} (${dev.ip_address})`;
        devSelector.appendChild(opt);
    });
    
    // Maintain selection if possible
    if (currentVal && Array.from(devSelector.options).some(o => o.value === currentVal)) {
        devSelector.value = currentVal;
    }
    
    generateSnippets();
}

function generateSnippets() {
    const devId = devSelector.value || 'raspberry-pi-gateway';
    const activeDevice = localDevices.find(d => d.device_id === devId) || { ip_address: '192.168.1.10' };
    const devIp = activeDevice.ip_address;
    
    const host = window.location.hostname || '127.0.0.1';
    const serverUrl = `http://${host}:8000/api/report-flow`;

    // 1. Curl Mock Attack
    const curlCode = `curl -X POST "${serverUrl}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "device_id": "${devId}",
    "src_ip": "${devIp}",
    "dst_ip": "192.168.1.1",
    "src_port": 50130,
    "dst_port": 80,
    "protocol": 6,
    "flow_duration": 0.05,
    "packet_count": 850,
    "byte_count": 54400,
    "tcp_flags_syn": 1,
    "tcp_flags_ack": 0,
    "tcp_flags_rst": 0,
    "tcp_flags_fin": 0
  }'`;

    // 2. Sniffer run snippet
    const runCode = `python client_example.py --server "${serverUrl}" --device "${devId}" --mode sniffer`;

    document.getElementById('curl-code-snippet').innerText = curlCode;
    document.getElementById('client-run-snippet').innerText = runCode;
}

// Setup Copy Buttons
setupCopyAction('copy-curl-btn', 'curl-code-snippet');
setupCopyAction('copy-run-btn', 'client-run-snippet');

function setupCopyAction(btnId, targetCodeId) {
    const btn = document.getElementById(btnId);
    const target = document.getElementById(targetCodeId);
    
    btn.addEventListener('click', () => {
        navigator.clipboard.writeText(target.innerText).then(() => {
            // Temporarily change icon to check
            btn.innerHTML = '<i class="fa-solid fa-check" style="color:var(--clr-green)"></i>';
            setTimeout(() => {
                btn.innerHTML = '<i class="fa-regular fa-copy"></i>';
            }, 1500);
        });
    });
}

// ----------------- Interactive Log Modal -----------------

const modal = document.getElementById('flow-modal');
const closeModalBtn = document.getElementById('close-modal-btn');

closeModalBtn.addEventListener('click', () => {
    modal.classList.remove('active');
});

// Close when clicking outside card
modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.classList.remove('active');
    }
});

function openFlowModal(flow) {
    const isAnomaly = flow.class_name !== 'Normal';
    const panel = document.getElementById('modal-threat-panel');
    const panelTitle = document.getElementById('modal-classification-title');
    const panelIcon = document.getElementById('modal-threat-icon');
    const panelSeverity = document.getElementById('modal-severity-badge');
    const panelDesc = document.getElementById('modal-threat-desc');

    // Setup Threat alert overlay banner
    if (isAnomaly) {
        panel.className = 'modal-alert-panel threat';
        panelTitle.innerText = `${flow.class_name} INTRUSION ALERT`;
        panelIcon.className = 'fa-solid fa-triangle-exclamation status-icon';
        panelSeverity.innerText = `${flow.severity} severity`;
        panelDesc.innerText = flow.description;
    } else {
        panel.className = 'modal-alert-panel normal';
        panelTitle.innerText = `Benign baseline flow (Normal)`;
        panelIcon.className = 'fa-solid fa-shield-halved status-icon';
        panelSeverity.innerText = 'low severity';
        panelDesc.innerText = flow.description;
    }

    // Load simple fields
    document.getElementById('modal-src-host').innerText = flow.src_ip;
    document.getElementById('modal-dst-host').innerText = flow.dst_ip;
    document.getElementById('modal-src-port').innerText = flow.src_port;
    document.getElementById('modal-dst-port').innerText = flow.dst_port;
    document.getElementById('modal-protocol').innerText = `${flow.protocol} (${flow.protocol === 6 ? 'TCP' : flow.protocol === 17 ? 'UDP' : 'Other'})`;
    document.getElementById('modal-duration').innerText = `${flow.flow_duration.toFixed(4)}s`;
    document.getElementById('modal-packets').innerText = flow.packet_count;
    document.getElementById('modal-bytes').innerText = formatBytes(flow.byte_count);

    // Derived values
    document.getElementById('modal-packet-rate').innerText = `${Math.round(flow.packet_rate)} pkts/s`;
    document.getElementById('modal-byte-rate').innerText = `${formatBytes(Math.round(flow.byte_rate))}/s`;
    document.getElementById('modal-mean-size').innerText = `${Math.round(flow.mean_packet_size)} B`;
    document.getElementById('modal-syn').innerText = flow.tcp_flags_syn;
    document.getElementById('modal-ack').innerText = flow.tcp_flags_ack;
    document.getElementById('modal-rst').innerText = flow.tcp_flags_rst;
    document.getElementById('modal-fin').innerText = flow.tcp_flags_fin;

    // Build neural probability bars
    const probContainer = document.getElementById('modal-probability-bars');
    probContainer.innerHTML = '';
    
    // Synthesize outputs array matching classifications
    // Normal (0), DDoS (1), PortScan (2), BruteForce (3)
    const probs = { Normal: 0.05, DDoS: 0.05, PortScan: 0.05, BruteForce: 0.05 };
    probs[flow.class_name] = flow.confidence;
    
    // Sum normalization
    const total = Object.values(probs).reduce((a, b) => a + b, 0);
    const classesList = ['Normal', 'DDoS', 'PortScan', 'BruteForce'];
    const colorClasses = { Normal: 'normal', DDoS: 'ddos', PortScan: 'portscan', BruteForce: 'bruteforce' };

    classesList.forEach(cls => {
        const val = probs[cls] / total;
        const row = document.createElement('div');
        row.className = 'prob-row';
        
        row.innerHTML = `
            <div class="prob-labels">
                <span class="prob-name">${cls}</span>
                <span class="prob-val">${(val * 100).toFixed(1)}%</span>
            </div>
            <div class="prob-bar-track">
                <div class="prob-bar-fill ${colorClasses[cls]}" id="bar-fill-${cls}"></div>
            </div>
        `;
        probContainer.appendChild(row);
        
        // Trigger animation delay
        setTimeout(() => {
            const fill = document.getElementById(`bar-fill-${cls}`);
            if (fill) fill.style.width = `${val * 100}%`;
        }, 80);
    });

    modal.classList.add('active');
}

// ----------------- Threat Toast Popups -----------------

const toastQueue = [];
let activeToastsCount = 0;
const MAX_ACTIVE_TOASTS = 1; // Strictly show one threat toast at a time

function enqueueThreatToast(flow) {
    toastQueue.push(flow);
    processToastQueue();
}

function processToastQueue() {
    if (activeToastsCount >= MAX_ACTIVE_TOASTS || toastQueue.length === 0) {
        return;
    }
    
    const flow = toastQueue.shift();
    activeToastsCount++;
    displayThreatToast(flow);
}

function displayThreatToast(flow) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    
    const timeStr = new Date(flow.timestamp * 1000).toLocaleTimeString();
    
    toast.innerHTML = `
        <i class="fa-solid fa-triangle-exclamation toast-icon"></i>
        <div class="toast-content">
            <div class="toast-header">
                <h4>${flow.class_name} Attack Ingress</h4>
                <span>${timeStr}</span>
            </div>
            <p class="toast-desc">${flow.description}</p>
            <p class="toast-meta">
                Source: <b>${flow.device_name}</b> (${flow.src_ip}) <br>
                Target: ${flow.dst_ip}:${flow.dst_port}
            </p>
        </div>
        <button class="toast-close">&times;</button>
    `;
    
    const closeBtn = toast.querySelector('.toast-close');
    
    const handleClose = () => {
        if (toast.classList.contains('removing')) return;
        removeToast(toast);
        
        // Decrease count and process next in queue after fade-out transition completes (350ms)
        setTimeout(() => {
            activeToastsCount = Math.max(0, activeToastsCount - 1);
            processToastQueue();
        }, 350);
    };
    
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        handleClose();
    });
    
    toast.addEventListener('click', (e) => {
        if (e.target !== closeBtn) {
            openFlowModal(flow);
        }
    });

    container.appendChild(toast);
    
    // Auto-remove toast after 4.5 seconds to keep the queue moving smoothly
    const autoCloseTimer = setTimeout(() => {
        handleClose();
    }, 4500);
}

function removeToast(toast) {
    if (toast.parentNode) {
        toast.classList.add('removing');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }
}

// ----------------- Browser Client Streamer -----------------
let browserStreamInterval = null;
let isBrowserStreaming = false;
let browserScanPort = 20;

// Initialize dynamic device identifier
const randomBrowserId = 'browser-' + Math.floor(1000 + Math.random() * 9000);
document.getElementById('browser-dev-id').value = randomBrowserId;

// Autofill name based on device type
const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
document.getElementById('browser-dev-name').value = isMobileDevice ? "My Mobile Phone" : "My Workstation Web";

const streamBtn = document.getElementById('browser-stream-btn');
streamBtn.addEventListener('click', () => {
    isBrowserStreaming = !isBrowserStreaming;
    
    if (isBrowserStreaming) {
        // Start streaming
        streamBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop Stream';
        streamBtn.style.background = 'var(--clr-danger)';
        streamBtn.style.color = '#fff';
        
        // Disable text inputs to prevent mid-stream alterations
        document.getElementById('browser-dev-name').disabled = true;
        
        // Trigger first payload immediately and schedule loop
        sendBrowserTelemetry();
        browserStreamInterval = setInterval(sendBrowserTelemetry, 3000);
    } else {
        // Stop streaming
        streamBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Stream';
        streamBtn.style.background = 'var(--clr-green)';
        streamBtn.style.color = '#000';
        
        document.getElementById('browser-dev-name').disabled = false;
        
        clearInterval(browserStreamInterval);
    }
});

async function sendBrowserTelemetry() {
    const devId = document.getElementById('browser-dev-id').value;
    const devName = document.getElementById('browser-dev-name').value.trim() || 'Browser Node';
    const profile = document.getElementById('browser-traffic-profile').value;
    
    let payload = {
        "device_id": devId,
        "src_ip": "detect", // The FastAPI backend resolves this to the real HTTP request client host IP!
        "dst_ip": "192.168.1.1",
        "src_port": Math.floor(1024 + Math.random() * 64000),
        "dst_port": 80,
        "protocol": 6,
        "flow_duration": 0.5,
        "packet_count": 10,
        "byte_count": 800,
        "tcp_flags_syn": 0,
        "tcp_flags_ack": 0,
        "tcp_flags_rst": 0,
        "tcp_flags_fin": 0
    };
    
    // Customize payload variables based on profile
    if (profile === 'Normal') {
        payload.dst_port = Math.random() > 0.5 ? 443 : 80;
        payload.protocol = Math.random() > 0.3 ? 6 : 17; // TCP or UDP
        payload.flow_duration = parseFloat((0.2 + Math.random() * 3.5).toFixed(4));
        payload.packet_count = Math.floor(4 + Math.random() * 20);
        payload.byte_count = payload.packet_count * Math.floor(64 + Math.random() * 1000);
        payload.tcp_flags_syn = payload.protocol === 6 ? 1 : 0;
        payload.tcp_flags_ack = payload.protocol === 6 ? 1 : 0;
    } 
    else if (profile === 'DDoS') {
        payload.dst_port = 80;
        payload.protocol = 6;
        payload.flow_duration = parseFloat((0.005 + Math.random() * 0.03).toFixed(4));
        payload.packet_count = Math.floor(250 + Math.random() * 600);
        payload.byte_count = payload.packet_count * Math.floor(54 + Math.random() * 128);
        payload.tcp_flags_syn = 1;
        payload.tcp_flags_ack = 0;
    } 
    else if (profile === 'PortScan') {
        browserScanPort = (browserScanPort + 1) % 1024 + 10;
        payload.dst_port = browserScanPort;
        payload.protocol = 6;
        payload.flow_duration = 0.05;
        payload.packet_count = 2;
        payload.byte_count = 80;
        payload.tcp_flags_syn = 1;
        payload.tcp_flags_ack = 0;
    } 
    else if (profile === 'BruteForce') {
        payload.dst_port = Math.random() > 0.5 ? 22 : 3389; // SSH or RDP
        payload.protocol = 6;
        payload.flow_duration = parseFloat((1.2 + Math.random() * 4.0).toFixed(4));
        payload.packet_count = Math.floor(20 + Math.random() * 45);
        payload.byte_count = payload.packet_count * 115;
        payload.tcp_flags_syn = 1;
        payload.tcp_flags_ack = 1;
    }
    
    // Register device dynamically on backend
    try {
        // Check if device is in device list, if not, register it on FastAPI first
        const devExists = localDevices.some(d => d.device_id === devId);
        if (!devExists) {
            await fetch('/api/devices', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_id: devId,
                    name: devName,
                    ip_address: "detect",
                    device_type: isMobileDevice ? "Mobile Phone" : "Laptop"
                })
            });
        }
        
        // Report flow telemetry
        await fetch('/api/report-flow', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    } catch (e) {
        console.error("Browser client streamer failed to report flow: ", e);
    }
}

// Fetch server config details
async function fetchServerInfo() {
    try {
        const r = await fetch('/api/server-info');
        if (r.ok) {
            const data = await r.json();
            document.getElementById('display-server-ip').innerText = `${data.server_ip}:${data.port}`;
        }
    } catch (e) {
        console.warn("Could not query server info: ", e);
        document.getElementById('display-server-ip').innerText = window.location.host;
    }
}

// Initialize application connect
connectWebSocket();
initGuideTabs();

// ----------------- Guide Tab Switching -----------------
function initGuideTabs() {
    const guideTabBtns = document.querySelectorAll('.guide-tab-btn');
    const guideTabContents = document.querySelectorAll('.guide-tab-content');
    
    guideTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-guide-tab');
            
            // Toggle active tab button
            guideTabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Toggle active tab content
            guideTabContents.forEach(content => {
                if (content.id === `guide-${target}-content`) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
        });
    });
}

// ----------------- Network Topology SVG Renderer -----------------
function drawNetworkTopology() {
    const svg = document.getElementById('network-topology-svg');
    if (!svg) return;
    
    const connGroup = document.getElementById('topology-connections');
    const nodeGroup = document.getElementById('topology-nodes');
    
    if (!connGroup || !nodeGroup) return;
    
    connGroup.innerHTML = '';
    nodeGroup.innerHTML = '';
    
    const centerX = 400;
    const centerY = 260;
    const radius = 170;
    
    // 1. Central Server Node
    const serverG = document.createElementNS("http://www.w3.org/2000/svg", "g");
    serverG.setAttribute("class", "topo-node central");
    serverG.setAttribute("transform", `translate(${centerX}, ${centerY})`);
    
    const serverIp = document.getElementById('display-server-ip').innerText || '127.0.0.1:8000';
    
    serverG.innerHTML = `
        <circle r="30" class="node-circle-glow central" />
        <circle r="16" fill="#00f0ff" />
        <rect x="-6" y="-6" width="12" height="12" rx="2" fill="#080c14" />
        <text y="46" class="node-label central" text-anchor="middle">IDS Central Server</text>
        <text y="58" font-size="9px" fill="var(--text-muted)" font-family="var(--font-mono)" text-anchor="middle">${serverIp}</text>
    `;
    
    serverG.addEventListener('mouseenter', (e) => showNodeTooltip(e, {
        name: "IDS Central Core",
        device_id: "ids-server",
        device_type: "IDS Core Server",
        ip_address: serverIp.split(':')[0],
        status: "online",
        total_flows: localSummary.total_flows || 0,
        anomalies_detected: localSummary.anomalies || 0
    }));
    serverG.addEventListener('mouseleave', hideNodeTooltip);
    nodeGroup.appendChild(serverG);
    
    // 2. Client Devices Nodes (arranged in a circle)
    const activeClients = localDevices.filter(d => d.device_id !== 'ids-server');
    const totalClients = activeClients.length;
    
    activeClients.forEach((dev, idx) => {
        // Compute circular coordinates
        const angle = (idx * 2 * Math.PI) / totalClients - Math.PI / 2;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        
        const isOnline = (Date.now() / 1000 - dev.last_seen) < 30;
        let nodeClass = `topo-node client ${isOnline ? 'online' : 'offline'}`;
        
        // Colors mapping by category
        let strokeColor = "var(--clr-cyan)";
        if (dev.anomalies_detected > 0) {
            strokeColor = "var(--clr-danger)";
            nodeClass += " compromised";
            if (isOnline && dev.device_id === lastThreatNodeId) {
                nodeClass += " threat-alert";
            }
        } else if (dev.device_type === "Sensor") {
            strokeColor = "var(--clr-warning)";
        } else if (dev.device_type === "Laptop") {
            strokeColor = "var(--clr-green)";
        }
        
        // Draw connection line path (from client to server)
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", `M ${x} ${y} L ${centerX} ${centerY}`);
        path.setAttribute("class", `connection-path ${dev.anomalies_detected > 0 ? 'threat-path' : 'benign'}`);
        path.setAttribute("id", `path-${dev.device_id}`);
        connGroup.appendChild(path);
        
        // Draw Device Node
        const clientG = document.createElementNS("http://www.w3.org/2000/svg", "g");
        clientG.setAttribute("class", nodeClass);
        clientG.setAttribute("id", `node-${dev.device_id}`);
        clientG.setAttribute("transform", `translate(${x}, ${y})`);
        
        // Select icon based on device type
        let iconMarkup = `<circle r="5" fill="${strokeColor}" />`;
        if (dev.device_type === "Laptop") {
            iconMarkup = `<rect x="-5" y="-5" width="10" height="8" rx="1" fill="${strokeColor}" /><line x1="-7" y1="5" x2="7" y2="5" stroke="${strokeColor}" stroke-width="1.5" />`;
        } else if (dev.device_type === "Sensor") {
            iconMarkup = `<circle r="4" fill="none" stroke="${strokeColor}" stroke-width="1.5" /><line x1="0" y1="-7" x2="0" y2="7" stroke="${strokeColor}" stroke-width="1" /><line x1="-7" y1="0" x2="7" y2="0" stroke="${strokeColor}" stroke-width="1" />`;
        } else if (dev.device_type === "IoT Board") {
            iconMarkup = `<rect x="-6" y="-6" width="12" height="12" rx="2" fill="none" stroke="${strokeColor}" stroke-width="1.5" /><circle r="3" fill="${strokeColor}" />`;
        }
        
        clientG.innerHTML = `
            <circle r="22" class="node-circle-glow client ${isOnline ? 'online' : 'offline'}" />
            <circle r="13" fill="var(--bg-primary)" stroke="${isOnline ? strokeColor : 'var(--text-dark)'}" stroke-width="1.5" />
            <g transform="translate(0, 0)">${iconMarkup}</g>
            <text y="34" class="node-label" text-anchor="middle">${dev.name}</text>
            <text y="44" font-size="9px" fill="var(--text-dark)" font-family="var(--font-mono)" text-anchor="middle">${dev.ip_address}</text>
        `;
        
        // Add dynamic Tooltip listeners
        clientG.addEventListener('mouseenter', (e) => showNodeTooltip(e, dev));
        clientG.addEventListener('mousemove', (e) => positionTooltip(e));
        clientG.addEventListener('mouseleave', hideNodeTooltip);
        
        nodeGroup.appendChild(clientG);
    });
}

function showNodeTooltip(e, dev) {
    const tooltip = document.getElementById('topology-node-tooltip');
    if (!tooltip) return;
    
    const isOnline = dev.device_id === 'ids-server' || (Date.now() / 1000 - dev.last_seen) < 30;
    
    tooltip.innerHTML = `
        <h4 style="color:${dev.anomalies_detected > 0 ? 'var(--clr-danger)' : 'var(--clr-cyan)'}">
            <i class="fa-solid fa-microchip"></i> ${dev.name}
        </h4>
        <p><b>ID:</b> ${dev.device_id}</p>
        <p><b>Category:</b> ${dev.device_type}</p>
        <p><b>Address:</b> ${dev.ip_address}</p>
        <p><b>Surveillance:</b> <span class="badge ${isOnline ? 'normal' : 'offline'}" style="padding:1px 5px; font-size:0.65rem;">${isOnline ? 'ONLINE' : 'OFFLINE'}</span></p>
        <p style="margin-top:6px; border-top:1px solid var(--border-color); padding-top:6px;">
            <b>Total Ingestion:</b> ${dev.total_flows} flows
        </p>
        <p style="color:var(--clr-danger)">
            <b>Intrusions Traced:</b> ${dev.anomalies_detected}
        </p>
    `;
    
    positionTooltip(e);
    tooltip.style.display = 'block';
}

function positionTooltip(e) {
    const tooltip = document.getElementById('topology-node-tooltip');
    if (!tooltip) return;
    
    const canvasBox = document.querySelector('.topology-canvas-box');
    const rect = canvasBox.getBoundingClientRect();
    
    // Position tooltip 15px down/right of cursor relative to parent box
    const x = e.clientX - rect.left + 15;
    const y = e.clientY - rect.top + 15;
    
    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
}

function hideNodeTooltip() {
    const tooltip = document.getElementById('topology-node-tooltip');
    if (tooltip) tooltip.style.display = 'none';
}

// ----------------- Packet flow pulse animation along path -----------------
function animateFlowPulse(devId, isAnomaly) {
    const path = document.getElementById(`path-${devId}`);
    if (!path) return;
    
    const pulsesGroup = document.getElementById('topology-pulses');
    if (!pulsesGroup) return;
    
    const pulse = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    pulse.setAttribute("r", isAnomaly ? "6" : "4.5");
    pulse.setAttribute("fill", isAnomaly ? "var(--clr-danger)" : "var(--clr-green)");
    pulse.setAttribute("class", "flow-pulse");
    
    if (isAnomaly) {
        pulse.setAttribute("filter", "url(#glow-red)");
    }
    
    const animate = document.createElementNS("http://www.w3.org/2000/svg", "animateMotion");
    animate.setAttribute("dur", "0.9s");
    animate.setAttribute("repeatCount", "1");
    animate.setAttribute("fill", "freeze");
    
    // Retrieve the exact connection path
    const pathD = path.getAttribute("d");
    animate.setAttribute("path", pathD);
    
    pulse.appendChild(animate);
    pulsesGroup.appendChild(pulse);
    
    // Remove pulse element from DOM after duration completes
    setTimeout(() => {
        pulse.remove();
    }, 950);
    
    // Handle transient threat alert ring flashes on the node
    const nodeG = document.getElementById(`node-${devId}`);
    if (nodeG) {
        const dev = localDevices.find(d => d.device_id === devId);
        const isOnline = dev ? (Date.now() / 1000 - dev.last_seen) < 30 : true;
        const hasAnomalies = dev ? dev.anomalies_detected > 0 : false;
        
        let baseClass = `topo-node client ${isOnline ? 'online' : 'offline'}`;
        if (hasAnomalies) {
            baseClass += " compromised";
        }
        
        if (isAnomaly) {
            lastThreatNodeId = devId;
            nodeG.setAttribute("class", `${baseClass} threat-alert`);
            setTimeout(() => {
                nodeG.setAttribute("class", baseClass);
            }, 3000);
        } else {
            nodeG.setAttribute("class", `${baseClass} normal-pulse`);
            setTimeout(() => {
                nodeG.setAttribute("class", baseClass);
            }, 1000);
        }
    }
}
