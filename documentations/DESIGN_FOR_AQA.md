# DroneNEA - Design Section

## 1. System Architecture

### 1.1 Overall System Design
The DroneNEA system follows a **three-tier architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                         │
│                  (Web Interface - GUI)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  HTML/CSS/JavaScript Frontend                          │ │
│  │  - User interface                                      │ │
│  │  - Real-time telemetry display                         │ │
│  │  - Control buttons and forms                           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTP/WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│                   (Flask Server + API)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Flask + Flask-SocketIO Backend                         │ │
│  │  - REST API endpoints                                  │ │
│  │  - WebSocket communication                             │ │
│  │  - Business logic coordination                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ MAVLink Protocol
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                               │
│              (Drone Control Modules)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Python Modules                                         │ │
│  │  - Connection, Control, Telemetry                       │ │
│  │  - Navigation, Mission, Camera                          │ │
│  │  - Failsafe, Configuration                              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Module Structure
The system is divided into **modular components** for maintainability:

**Core Modules:**
- `connection.py` - MAVLink connection management
- `control.py` - Flight control operations
- `telemetry.py` - Data reading and interpretation
- `navigations.py` - Waypoint management
- `mission.py` - Mission file handling
- `camera.py` - Camera control
- `failsafe.py` - Safety monitoring
- `config.py` - Configuration management

**GUI Modules:**
- `api.py` - REST API endpoints
- `drone_controller.py` - Business logic coordination
- `telemetry_manager.py` - Real-time data streaming

### 1.3 Data Flow Architecture
```
User Input → Web Interface → REST API → Drone Controller → MAVLink → Drone
                                                                  ↓
Telemetry ← WebSocket ← Telemetry Manager ← Drone Modules ← MAVLink
```

## 2. Data Structures

### 2.1 Configuration Data Structures
**Configuration Classes** - Type-safe configuration management:

```python
class ConnectionConfig:
    DEFAULT_TCP: str = "tcp:127.0.0.1:5760"
    DEFAULT_UDP: str = "udpin:0.0.0.0:14551"
    DEFAULT_BAUD: int = 115200
    DEFAULT_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

class FlightConfig:
    MIN_ALTITUDE: float = 2.0
    MAX_ALTITUDE: float = 120.0
    DEFAULT_TAKEOFF_ALTITUDE: float = 10.0
    MIN_BATTERY_WARNING: int = 25
    MIN_BATTERY_CRITICAL: int = 15
    MIN_BATTERY_EMERGENCY: int = 10
```

### 2.2 Waypoint Data Structure
**Waypoint Class** - Represents navigation points:

```python
class Waypoint:
    latitude: float      # GPS latitude in decimal degrees
    longitude: float     # GPS longitude in decimal degrees
    altitude: float      # Altitude in meters
    hold_time: int = 0   # Time to hold at waypoint (seconds)
    acceptance_radius: float = 5.0  # Distance to consider arrived (meters)
    camera_action: str = "none"     # Camera action: "none", "photo", "video_start", "video_stop"
    camera_delay: int = 0            # Delay after camera action (seconds)
```

**Data Dictionary Example:**
```json
{
  "latitude": -35.363262,
  "longitude": 149.165237,
  "altitude": 10.0,
  "hold_time": 2,
  "acceptance_radius": 5.0,
  "camera_action": "photo",
  "camera_delay": 1
}
```

### 2.3 Telemetry Data Structure
**Real-time Telemetry Object:**
```python
{
    "position": {
        "latitude": float,
        "longitude": float,
        "altitude": float
    },
    "attitude": {
        "roll": float,
        "pitch": float,
        "yaw": float
    },
    "battery": int,           # Percentage 0-100
    "speed": float,           # m/s
    "gps": {
        "satellites": int,
        "fix_type": int
    },
    "connected": bool,
    "armed": bool,
    "mode": str
}
```

### 2.4 Mission Data Structure
**Mission File Format (JSON):**
```json
{
  "metadata": {
    "name": "Survey Mission",
    "author": "Student Name",
    "created": "2026-09-12",
    "description": "Area survey mission"
  },
  "waypoints": [
    {
      "latitude": -35.363262,
      "longitude": 149.165237,
      "altitude": 10.0,
      "hold_time": 2,
      "camera_action": "photo"
    }
  ]
}
```

### 2.5 Failsafe Data Structure
**Failsafe Level Enumeration:**
```python
class FailsafeLevel(Enum):
    WARNING = "warning"      # Log only, continue mission
    CAUTION = "caution"      # Pause mission, alert user
    CRITICAL = "critical"    # Abort mission, land
    EMERGENCY = "emergency"  # Immediate RTL or emergency land
```

## 3. Algorithms

### 3.1 Distance Calculation Algorithm (Haversine Formula)
**Purpose:** Calculate distance between two GPS coordinates

**Algorithm:**
```python
import math

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula.
    Returns distance in meters.
    """
    # Earth radius in meters
    R = 6371000
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c
```

**Complexity:** O(1) - Constant time calculation

### 3.2 Failsafe Monitoring Algorithm
**Purpose:** Background monitoring of critical safety parameters

**Algorithm:**
```python
def failsafe_monitoring_loop():
    while monitoring_active:
        # Critical checks (every 2-5 seconds)
        current_time = time.time()
        
        # Battery check (every 5 seconds)
        if current_time - last_battery_check > 5:
            battery_level = telemetry.get_battery()
            if battery_level <= BATTERY_EMERGENCY:
                trigger_failsafe(EMERGENCY, "Critical battery level")
            elif battery_level <= BATTERY_CRITICAL:
                trigger_failsafe(CRITICAL, "Low battery level")
            last_battery_check = current_time
        
        # Connection check (every 2 seconds)
        if current_time - last_heartbeat_check > 2:
            heartbeat_age = current_time - last_heartbeat_time
            if heartbeat_age > HEARTBEAT_TIMEOUT:
                trigger_failsafe(EMERGENCY, "Connection lost")
            last_heartbeat_check = current_time
        
        time.sleep(1)
```

**Complexity:** O(1) per iteration, runs in background thread

### 3.3 Mission Execution Algorithm
**Purpose:** Execute waypoint mission with safety checks

**Algorithm:**
```python
def execute_mission(waypoints: List[Waypoint]):
    # Pre-flight checks
    if not connection.is_connected():
        raise ConnectionError("Drone not connected")
    
    if not validate_waypoints(waypoints):
        raise ValidationError("Invalid waypoints")
    
    # Arm and takeoff
    control.set_mode("GUIDED")
    control.arm()
    control.takeoff(DEFAULT_ALTITUDE)
    telemetry.wait_until_altitude(DEFAULT_ALTITUDE)
    
    # Execute waypoints
    for waypoint in waypoints:
        # Navigate to waypoint
        navigation.goto_waypoint(waypoint)
        
        # Wait for arrival
        while navigation.get_distance_to_waypoint(waypoint) > waypoint.acceptance_radius:
            if failsafe.check_all():
                handle_failsafe()
            time.sleep(0.5)
        
        # Execute camera action
        if waypoint.camera_action == "photo":
            camera.take_photo()
        elif waypoint.camera_action == "video_start":
            camera.start_video()
        
        # Hold if required
        if waypoint.hold_time > 0:
            time.sleep(waypoint.hold_time)
    
    # Return to launch
    control.rtl()
    telemetry.wait_until_landed()
```

**Complexity:** O(n) where n = number of waypoints

### 3.4 Emergency Landing Algorithm
**Purpose:** Safe emergency landing based on current conditions

**Algorithm:**
```python
def emergency_land(reason: str):
    # Get current telemetry
    altitude = telemetry.get_altitude()
    battery = telemetry.get_battery()
    current_mode = telemetry.get_flight_mode()
    
    # Determine landing strategy
    if battery < 15 and altitude > 20:
        # Use RTL to preserve battery
        control.rtl()
    elif altitude > 50:
        # Descend to safe altitude first
        control.set_mode("GUIDED")
        navigation.goto_position(current_lat, current_lon, 50)
        telemetry.wait_until_altitude(50)
    
    # Execute landing
    control.set_mode("LAND")
    
    # Wait for landing with timeout
    start_time = time.time()
    while not telemetry.is_landed():
        if time.time() - start_time > LANDING_TIMEOUT:
            logger.warning("Landing timeout, forcing shutdown")
            break
        time.sleep(1)
    
    # Log emergency context
    logger.error(f"Emergency landing: {reason}, Alt: {altitude}, Batt: {battery}")
```

**Complexity:** O(1) - Decision tree with constant time operations

## 4. User Interface Design

### 4.1 Interface Layout
The web interface is divided into **four main sections**:

```
┌─────────────────────────────────────────────────────────────┐
│  Header: DroneNEA Control Panel                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Connection   │  │ Telemetry    │  │ Failsafe     │      │
│  │ Status       │  │ Display      │  │ Status       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Flight Controls                                        │  │
│  │ [Arm] [Disarm] [Takeoff] [Land] [RTL] [Emergency]     │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Mission Planning                                      │  │
│  │ [Load Mission] [Start Mission] [Waypoint Editor]      │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Camera Controls                                        │  │
│  │ [Take Photo] [Start Video] [Stop Video] [Camera Mode]│  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Colour Scheme and Visual Design
- **Status Indicators:** Green (connected/normal), Red (disconnected/error), Amber (warning)
- **Button States:** Enabled (blue), Disabled (grey), Active (green)
- **Telemetry Display:** Large, clear fonts for critical data
- **Responsive Design:** Adapts to different screen sizes

### 4.3 User Interaction Flow
```
1. User opens web interface
2. Connection panel shows status (disconnected)
3. User enters connection parameters
4. User clicks "Connect" button
5. System establishes MAVLink connection
6. Telemetry display starts updating
7. Flight controls become enabled
8. User can execute flight operations
9. Real-time feedback via WebSocket updates
```

### 4.4 Input Validation
- **Connection Parameters:** IP address format validation, port range checking
- **Altitude Input:** Min/max altitude limits enforced
- **Mission Data:** GPS coordinate range validation, waypoint count limits
- **Camera Actions:** Mode validation, state checking

## 5. Input/Output Design

### 5.1 Input Design
**User Inputs:**
- Connection settings (IP, port, baud rate)
- Flight commands (arm, takeoff altitude, flight mode)
- Mission parameters (waypoints, hold times, camera actions)
- Camera controls (photo trigger, video recording)

**System Inputs:**
- MAVLink messages from drone
- Telemetry data streams
- Configuration file parameters
- Mission file data

### 5.2 Output Design
**User Outputs:**
- Real-time telemetry display (position, battery, altitude)
- Status messages (success/error notifications)
- Connection status indicators
- Mission progress updates

**System Outputs:**
- MAVLink commands to drone
- Log files (drone.log, camera logs)
- Mission save files (JSON format)
- API responses (JSON format)

### 5.3 API Response Format
**Success Response:**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "error_type": "ConnectionError",
    "message": "Drone is not connected",
    "details": { ... }
  }
}
```

## 6. File Structure

### 6.1 Project Directory Structure
```
DroneNEA/
├── drone/                      # Core drone control modules
│   ├── __init__.py
│   ├── drone.py               # Main interface
│   ├── connection.py           # MAVLink connection
│   ├── control.py             # Flight control
│   ├── telemetry.py           # Data reading
│   ├── navigations.py         # Waypoint management
│   ├── mission.py             # Mission files
│   ├── camera.py              # Camera control
│   ├── failsafe.py            # Safety systems
│   ├── config.py              # Configuration
│   └── exceptions.py          # Custom exceptions
├── gui/                       # Web interface
│   ├── routes/
│   │   ├── api.py            # REST API endpoints
│   │   └── main.py           # Main routes
│   ├── models/
│   │   ├── drone_controller.py
│   │   └── telemetry_manager.py
│   ├── templates/
│   │   └── index.html        # Main interface
│   └── config.py             # GUI configuration
├── tests/                     # Test suite
│   ├── unit/                 # Unit tests (mocked)
│   ├── integration/          # Integration tests (SITL)
│   └── manual/               # Manual test scripts
├── logs/                      # Log files
│   ├── drone.log
│   └── camera/
├── missions/                  # Mission files
├── documentations/           # Documentation
├── requirements.txt           # Python dependencies
└── run.py                    # Application entry point
```

### 6.2 File Formats
**Mission Files (.json):**
- JSON format for easy parsing and human readability
- Contains metadata and waypoint arrays
- Validated on load and save

**Log Files (.log):**
- Text format with timestamps
- Different log levels (INFO, WARNING, ERROR)
- Rotated by size to prevent disk overflow

**Configuration Files:**
- Python classes for type safety
- Environment variables for deployment flexibility

## 7. Security Considerations

### 7.1 Current Security Measures
- Input validation on all user inputs
- Connection timeout handling
- Safe disconnection procedures
- Emergency stop functionality

### 7.2 Planned Security Improvements
- API authentication (API keys/JWT tokens)
- Rate limiting on control endpoints
- HTTPS support for encrypted communication
- CORS restriction to specific domains
- Audit logging for all control operations

## 8. Error Handling Strategy

### 8.1 Exception Hierarchy
```python
DroneNEAError (base)
├── ConnectionError
├── ControlError
├── TelemetryError
├── NavigationError
├── MissionError
├── CameraError
├── FailsafeError
└── ConfigurationError
```

### 8.2 Error Recovery
- **Connection Errors:** Automatic retry with exponential backoff
- **Control Errors:** Safe mode activation, user notification
- **Telemetry Errors:** Fallback to last known values
- **Navigation Errors:** Mission abort, return to launch
- **Camera Errors:** Log error, continue mission

This design provides a comprehensive foundation for implementing the DroneNEA system while following software engineering best practices and AQA examination requirements.