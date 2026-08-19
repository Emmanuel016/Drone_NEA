# DroneNEA Frontend-Backend Communication Guide

## Overview

The DroneNEA web interface uses a **REST API + WebSocket** architecture to communicate between the frontend (`index.html`) and backend (`api.py`). This guide explains the complete data flow.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser (Frontend)                    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    index.html                             │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  • HTML Structure (UI elements)                  │  │  │
│  │  │  • CSS Styling (Visual appearance)               │  │  │
│  │  │  • JavaScript (Logic & API calls)                │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           │ HTTP Requests (REST API)        │
│                           │ WebSocket (Real-time)        │
│                           ▼                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           │
┌─────────────────────────────────────────────────────────────┐
│                    Flask Server (Backend)                       │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                     api.py                               │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  • REST API Endpoints (/api/*)                  │  │  │
│  │  │  • Request Handling                             │  │  │
│  │  │  • JSON Response Formatting                     │  │  │
│  │  │  • Error Handling                               │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           │ Business Logic                │
│                           ▼                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Drone Controller & Subsystems              │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  • Connection, Control, Telemetry                │  │
│  │  │  • Navigation, Mission, Camera, Failsafe         │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. REST API Communication

### How API Calls Work

#### Frontend (index.html) → Backend (api.py)

**JavaScript Function:**
```javascript
async function apiCall(endpoint, payload = null) {
    try {
        const options = { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }
        };
        if (payload) options.body = JSON.stringify(payload);
        
        const response = await fetch(endpoint, options);
        const data = await response.json();
        showAlert(data.message, data.success ? 'success' : 'error');
        return data.success;
    } catch (error) {
        showAlert(`Request failed: ${error.message}`, 'error');
        return false;
    }
}
```

**How it works:**
1. **Build Request:** Creates HTTP POST request with JSON content type
2. **Add Payload:** Converts JavaScript object to JSON string
3. **Send Request:** Uses `fetch()` to send HTTP request to Flask server
4. **Parse Response:** Converts JSON response to JavaScript object
5. **Handle Result:** Shows success/error message and returns boolean

#### Example: Connect Function

**Frontend:**
```javascript
async function connect() {
    const payload = {
        connection_string: document.getElementById('connectionString').value,
        baud: parseInt(document.getElementById('baudRate').value),
        timeout: parseInt(document.getElementById('timeout').value)
    };
    
    const success = await apiCall('/api/connect', payload);
    if (success) {
        updateConnectionStatus(true);
        listMissions();
    }
}
```

**Backend (api.py):**
```python
@api_bp.route('/api/connect', methods=['POST'])
def connect():
    """Connect to the drone."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    telemetry_manager = current_app.telemetry_manager
    
    data = request.get_json(silent=True) or {}
    connection_string = data.get('connection_string')
    baud = data.get('baud')
    timeout = data.get('timeout')
    
    try:
        success = drone_controller.connect(connection_string, baud, timeout)
        if success:
            telemetry_manager.start()
            return jsonify({'success': True, 'message': 'Connected successfully'})
        return jsonify({'success': False, 'message': 'Connection failed internally'})
    except Exception as e:
        return handle_error(e)
```

**Data Flow:**
```
Frontend JavaScript              Backend Python
┌─────────────────┐             ┌──────────────────┐
│ connectionString│             │ request.get_json()│
│ baud: 115200     │ ────────▶ │ Parses JSON      │
│ timeout: 30       │             │                  │
└─────────────────┘             │                  │
                                  │ Drone Controller  │
                                  │ connect()          │
                                  │     ↓              │
┌─────────────────┐             │                  │
│ success: true    │ ◀───────   │                  │
│ message: "..."   │             │ jsonify()          │
└─────────────────┘             │                  │
                                  └──────────────────┘
```

---

## 2. JSON Data Interpretation & Display

### Response Format

**Backend sends:**
```json
{
  "success": true,
  "message": "Connected successfully"
}
```

**Frontend receives and processes:**
```javascript
const response = await fetch(endpoint, options);
const data = await response.json();  // Parse JSON string to object
showAlert(data.message, data.success ? 'success' : 'error');
return data.success;
```

### Telemetry Data Flow (WebSocket)

**Backend sends real-time data:**
```json
{
  "position": {
    "latitude": -35.363261,
    "longitude": 149.165237,
    "altitude": 15.5
  },
  "speed": 5.2,
  "attitude": {
    "yaw": 0.78,
    "pitch": -0.3,
    "roll": 0.5
  },
  "battery": 85,
  "gps": {
    "satellites": 12,
    "fix_type": 3
  },
  "connected": true,
  "armed": false,
  "mode": "GUIDED"
}
```

**Frontend receives and displays:**
```javascript
socket.on('telemetry_update', function(data) {
    updateTelemetryUI(data);
});

function updateTelemetryUI(data) {
    // Extract and display altitude
    if (data.position) {
        document.getElementById('altitude').textContent = 
            (data.position.altitude || 0).toFixed(1) + ' m';
    }
    
    // Extract and display battery
    if (data.battery !== null && data.battery !== undefined) {
        const bPercent = data.battery;
        document.getElementById('battery').textContent = bPercent.toFixed(0) + '%';
        
        // Update battery bar color based on level
        const bFill = document.getElementById('batteryFill');
        bFill.style.width = bPercent + '%';
        bFill.classList.remove('warning', 'danger');
        if (bPercent < 25) bFill.classList.add('danger');
        else if (bPercent < 50) bFill.classList.add('warning');
    }
    
    // Extract and display flight mode
    if (data.mode) {
        document.getElementById('flightMode').textContent = 'Mode: ' + data.mode;
    }
}
```

**HTML Elements Updated:**
```html
<!-- Before: -->
<div class="telemetry-value" id="altitude">0.0 m</div>
<div class="telemetry-value" id="battery">0%</div>
<div id="flightMode">Mode: --</div>

<!-- After: -->
<div class="telemetry-value" id="altitude">15.5 m</div>
<div class="telemetry-value" id="battery">85%</div>
<div id="flightMode">Mode: GUIDED</div>
```

---

## 3. WebSocket Real-Time Communication

### WebSocket Connection Setup

**Frontend:**
```javascript
const socket = io();  // Connect to Flask-SocketIO server

socket.on('connect', function() {
    // When WebSocket connects
    document.getElementById('serverStatusDot').classList.add('connected');
    document.getElementById('serverStatusText').textContent = 'Server Linked';
    fetchInitialStatus();
});

socket.on('disconnect', function() {
    // When WebSocket disconnects
    document.getElementById('serverStatusDot').classList.remove('connected');
    document.getElementById('serverStatusText').textContent = 'Server Offline';
    showAlert('WebSocket server connection lost!', 'error');
});

socket.on('telemetry_update', function(data) {
    // When real-time telemetry data arrives
    updateTelemetryUI(data);
});
```

**Backend (Telemetry Manager):**
```python
class TelemetryManager:
    def _telemetry_loop(self):
        """Background thread to emit telemetry updates."""
        while self.running:
            try:
                telemetry_data = self._get_telemetry_data()
                self.socketio.emit('telemetry_update', telemetry_data)
            except Exception as e:
                print(f"Telemetry update error: {e}")
            
            time.sleep(0.5)  # Update every 500ms
```

**WebSocket Data Flow:**
```
Telemetry Manager (Backend)              WebSocket Connection          Frontend JavaScript
┌────────────────────────┐              ┌─────────────────┐              ┌──────────────────┐
│ _get_telemetry_data()  │ ─────────────▶ │ Socket.io Server │ ─────────────▶ │ socket.on()       │
│                      │              │ Broadcasts to   │              │ updateTelemetryUI()│
│ {position, battery...}│              │ all clients     │              │ DOM updates      │
└────────────────────────┘              └─────────────────┘              └──────────────────┘
      ↑                                    ↑                                    ↑
      │ Every 500ms                        │                                    │
      └────────────────────────────────┘                                    │
```

---

## 4. API Endpoints Usage

### Connection API

**Frontend Call:**
```javascript
async function connect() {
    const payload = {
        connection_string: document.getElementById('connectionString').value,
        baud: parseInt(document.getElementById('baudRate').value),
        timeout: parseInt(document.getElementById('timeout').value)
    };
    
    const success = await apiCall('/api/connect', payload);
}
```

**Backend Endpoint:**
```python
@api_bp.route('/api/connect', methods=['POST'])
def connect():
    # Extract JSON payload
    data = request.get_json(silent=True) or {}
    connection_string = data.get('connection_string')
    
    # Call drone controller
    success = drone_controller.connect(connection_string, baud, timeout)
    
    # Return JSON response
    return jsonify({'success': True, 'message': 'Connected successfully'})
```

### Flight Control APIs

**Frontend Call:**
```javascript
const arm = () => apiCall('/api/arm');

const disarm = () => apiCall('/api/disarm');

function takeoff() {
    const altitude = parseFloat(document.getElementById('takeoffAltitude').value) || 10;
    apiCall('/api/takeoff', { altitude });
}

function setMode() {
    const mode = document.getElementById('flightModeSelect').value;
    apiCall('/api/mode', { mode });
}
```

**Backend Endpoints:**
```python
@api_bp.route('/api/arm', methods=['POST'])
def arm():
    success = drone_controller.arm()
    return jsonify({'success': success, 'message': 'Armed' if success else 'Failed to arm'})

@api_bp.route('/api/takeoff', methods=['POST'])
def takeoff():
    data = request.get_json(silent=True) or {}
    altitude = data.get('altitude', config.flight.DEFAULT_TAKEOFF_ALTITUDE)
    success = drone_controller.takeoff(altitude)
    return jsonify({'success': success, 'message': f'Takeoff to {altitude}m'})
```

### Mission APIs

**Frontend Call:**
```javascript
async function listMissions() {
    const response = await fetch('/api/mission/list');
    const data = await response.json();
    
    if (data.success) {
        // Update mission list UI
        missionList.innerHTML = data.missions.map(m => 
            `<div class="mission-item" onclick="selectMission('${m}')">📄 ${m}</div>`
        ).join('');
    }
}

function loadMission() {
    const filename = document.getElementById('missionFilename').value;
    apiCall('/api/mission/load', { filename });
}

const startMission = () => apiCall('/api/mission/start');
```

**Backend Endpoints:**
```python
@api_bp.route('/api/mission/list')
def list_missions():
    missions = drone_controller.list_missions()
    return jsonify({'success': True, 'missions': missions})

@api_bp.route('/api/mission/load', methods=['POST'])
def load_mission():
    data = request.get_json(silent=True) or {}
    filename = data.get('filename')
    success = drone_controller.load_mission(filename)
    return jsonify({'success': success, 'message': f'Mission {filename} loaded'})
```

---

## 5. UI State Management

### Connection Status Management

**Frontend Function:**
```javascript
function updateConnectionStatus(isConnected, forceDisableServer = false) {
    connected = isConnected;
    const droneDot = document.getElementById('droneStatusDot');
    const connectionStatus = document.getElementById('connectionStatus');
    
    const interactiveIds = ['armBtn', 'disarmBtn', 'takeoffBtn', 'landBtn', 'rtlBtn', 
                            'setModeBtn', 'loadMissionBtn', 'startMissionBtn'];
    
    if (isConnected && !forceDisableServer) {
        // Enable controls
        droneDot.classList.add('connected');
        connectionStatus.textContent = 'Drone Connected';
        interactiveIds.forEach(id => document.getElementById(id).disabled = false);
    } else {
        // Disable controls
        droneDot.classList.remove('connected');
        connectionStatus.textContent = 'Drone Disconnected';
        interactiveIds.forEach(id => document.getElementById(id).disabled = true);
    }
}
```

**How it works:**
1. Updates visual indicators (green/red dot)
2. Updates text status
3. Enables/disables control buttons based on connection state
4. Prevents user from sending commands when disconnected

---

## 6. Error Handling

### Frontend Error Handling

**API Call Error Handling:**
```javascript
async function apiCall(endpoint, payload = null) {
    try {
        const response = await fetch(endpoint, options);
        const data = await response.json();
        showAlert(data.message, data.success ? 'success' : 'error');
        return data.success;
    } catch (error) {
        showAlert(`Request failed: ${error.message}`, 'error');
        return false;
    }
}
```

**Alert Display:**
```javascript
function showAlert(message, type) {
    const alertId = type === 'success' ? 'successAlert' : 'errorAlert';
    const alert = document.getElementById(alertId);
    alert.textContent = message;
    alert.style.display = 'block';
    setTimeout(() => { alert.style.display = 'none'; }, 4000);
}
```

### Backend Error Handling

**Centralized Error Handler:**
```python
def handle_error(error: Exception) -> tuple:
    """Convert exceptions to consistent API error responses."""
    if isinstance(error, DroneNEAError):
        return jsonify({
            'success': False,
            'error': error.to_dict()
        }), 400
    else:
        return jsonify({
            'success': False,
            'error': {
                'error_type': 'InternalServerError',
                'message': 'An unexpected error occurred',
                'details': str(error)
            }
        }), 500
```

**Usage in Endpoints:**
```python
@api_bp.route('/api/arm', methods=['POST'])
def arm():
    try:
        success = drone_controller.arm()
        return jsonify({'success': success, 'message': 'Armed'})
    except Exception as e:
        return handle_error(e)
```

---

## 7. Complete Data Flow Example

### Takeoff Operation Flow

```
1. User clicks "Takeoff" button
   ↓
2. Frontend: takeoff() function called
   ↓
3. Frontend: Extracts altitude from input field
   ↓
4. Frontend: apiCall('/api/takeoff', { altitude: 10 })
   ↓
5. Frontend: HTTP POST request to Flask server
   {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: '{"altitude": 10}'
   }
   ↓
6. Backend: Flask receives request at /api/takeoff
   ↓
7. Backend: request.get_json() parses JSON payload
   ↓
8. Backend: drone_controller.takeoff(10) called
   ↓
9. Backend: Drone control logic via MAVLink
   ↓
10. Backend: jsonify({success: true, message: 'Takeoff to 10m'})
   ↓
11. Frontend: Receives JSON response
   ↓
12. Frontend: showAlert('Takeoff to 10m', 'success')
   ↓
13. Frontend: Success message displayed for 4 seconds
```

---

## 8. Real-Time Telemetry Flow

### Continuous Telemetry Updates

```
Backend (Every 500ms)                WebSocket                  Frontend
┌────────────────────────┐              ┌──────────┐              ┌──────────────┐
│ TelemetryManager       │              │ Socket.io │              │   Browser    │
│                          │              │          │              │              │
│ _telemetry_loop()       │─────────────▶│ Broadcast │─────────────▶│ socket.on()   │
│                          │              │          │              │              │
│ _get_telemetry_data()   │              │          │              │              │
│ {position, battery...} │              │          │              │              │
└────────────────────────┘              └──────────┘              └──────────────┘
```

**Frontend Updates:**
```javascript
socket.on('telemetry_update', function(data) {
    // Updates UI elements
    document.getElementById('altitude').textContent = data.position.altitude + ' m';
    document.getElementById('battery').textContent = data.battery + '%';
    document.getElementById('flightMode').textContent = 'Mode: ' + data.mode;
});
```

---

## 9. JSON Data Structure Reference

### Standard Success Response
```json
{
  "success": true,
  "message": "Operation successful"
}
```

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "error_type": "ConnectionError",
    "message": "Drone is not connected",
    "details": {}
  }
}
```

### Telemetry Data Structure
```json
{
  "position": {
    "latitude": -35.363261,
    "longitude": 149.165237,
    "altitude": 15.5
  },
  "attitude": {
    "roll": 0.5,
    "pitch": -0.3,
    "yaw": 0.78
  },
  "battery": 85,
  "speed": 5.2,
  "gps": {
    "satellites": 12,
    "fix_type": 3
  },
  "connected": true,
  "armed": false,
  "mode": "GUIDED"
}
```

---

## 10. Key Technologies

### Frontend
- **HTML5** - Structure and layout
- **CSS3** - Styling and visual design
- **JavaScript (ES6+)** - Logic and API calls
- **Socket.io Client** - WebSocket communication
- **Fetch API** - HTTP requests

### Backend
- **Flask** - Web framework
- **Flask-SocketIO** - WebSocket support
- **Python** - Server-side logic
- **MAVLink** - Drone communication protocol

---

## 11. Communication Summary

### Two-Way Communication

**HTTP (REST API):**
- **Direction:** Frontend → Backend
- **Method:** Request-Response
- **Use Case:** Commands (connect, arm, takeoff, missions)
- **Trigger:** User actions (button clicks)

**WebSocket:**
- **Direction:** Backend → Frontend (real-time)
- **Method:** Continuous broadcast
- **Use Case:** Telemetry updates (position, battery, status)
- **Trigger:** Background thread (every 500ms)

### Data Formats

**HTTP Requests:**
- **Content-Type:** `application/json`
- **Method:** Mostly POST
- **Body:** JSON string

**HTTP Responses:**
- **Content-Type:** `application/json`
- **Structure:** `{success: bool, message: str, data?: any}`

**WebSocket Events:**
- **Event Name:** `telemetry_update`
- **Data:** JSON object with telemetry fields

---

This architecture provides a responsive, real-time interface for drone control with clear separation between user commands (HTTP) and automatic status updates (WebSocket).