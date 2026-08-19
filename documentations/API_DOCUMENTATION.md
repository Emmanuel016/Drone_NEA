# DroneNEA API Documentation

## Overview

The DroneNEA API provides REST endpoints for controlling ArduPilot drones via a web interface. All endpoints return JSON responses and follow a consistent error handling pattern.

**Base URL:** `http://localhost:5000/api`

**Authentication:** Currently not implemented (see security recommendations)

**Content-Type:** `application/json`

---

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

### Error Response
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

---

## Connection Endpoints

### Connect to Drone
**POST** `/api/connect`

Establishes connection to the drone MAVLink interface.

**Request Body:**
```json
{
  "connection_string": "udpin:0.0.0.0:14551",
  "baud": 115200,
  "timeout": 30
}
```

**Parameters:**
- `connection_string` (string, optional): MAVLink connection string. Defaults to config value.
- `baud` (integer, optional): Serial baud rate. Defaults to 115200.
- `timeout` (integer, optional): Connection timeout in seconds. Defaults to 30.

**Response:**
```json
{
  "success": true,
  "message": "Connected successfully"
}
```

**Error Responses:**
- `ConnectionError`: Connection failed or timeout
- `ConfigurationError`: Invalid connection parameters

---

### Disconnect from Drone
**POST** `/api/disconnect`

Safely disconnects from the drone and stops all background processes.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "Disconnected successfully"
}
```

**Error Responses:**
- `ConnectionError`: Disconnection failed

---

## Flight Control Endpoints

### Arm Drone
**POST** `/api/arm`

Arms the drone motors for flight.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "Armed"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `ControlError`: Arming failed (safety interlocks, low battery, etc.)

**Prerequisites:**
- Drone must be connected
- GPS lock required (in most modes)
- Battery level sufficient
- Safety switches enabled

---

### Disarm Drone
**POST** `/api/disarm`

Disarms the drone motors.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "Disarmed"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `ControlError`: Disarming failed

---

### Takeoff
**POST** `/api/takeoff`

Commands the drone to take off to a specified altitude.

**Request Body:**
```json
{
  "altitude": 10.0
}
```

**Parameters:**
- `altitude` (number, optional): Target altitude in meters. Defaults to 10.0.

**Response:**
```json
{
  "success": true,
  "message": "Takeoff to 10.0m"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `ControlError`: Takeoff failed (altitude invalid, safety checks)
- `ValidationError`: Altitude out of range

**Prerequisites:**
- Drone must be armed
- GPS lock required
- Altitude within configured limits

---

### Land
**POST** `/api/land`

Commands the drone to land at its current location.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "Landing initiated"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `ControlError`: Landing failed

---

### Return to Launch (RTL)
**POST** `/api/rtl`

Commands the drone to return to its launch position and land.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "RTL initiated"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `ControlError`: RTL failed

---

### Set Flight Mode
**POST** `/api/mode`

Changes the drone's flight mode.

**Request Body:**
```json
{
  "mode": "GUIDED"
}
```

**Parameters:**
- `mode` (string, required): Flight mode name (e.g., "GUIDED", "LOITER", "LAND", "RTL", "STABILIZE")

**Available Modes:**
- `GUIDED`: Autonomous control
- `LOITER`: Hold position
- `LAND`: Land at current location
- `RTL`: Return to launch
- `STABILIZE`: Manual stabilised flight
- `AUTO`: Autonomous mission execution

**Response:**
```json
{
  "success": true,
  "message": "Mode set to GUIDED"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `ControlError`: Mode change failed
- `ValidationError`: Invalid mode name

---

## Mission Endpoints

### List Missions
**GET** `/api/mission/list`

Lists all available mission files.

**Request Parameters:** None

**Response:**
```json
{
  "success": true,
  "missions": ["test_mission", "second_mission", "survey_mission"]
}
```

**Error Responses:**
- `MissionError`: Failed to read mission directory

---

### Load Mission
**POST** `/api/mission/load`

Loads a mission file for execution.

**Request Body:**
```json
{
  "filename": "test_mission"
}
```

**Parameters:**
- `filename` (string, required): Mission filename without extension

**Response:**
```json
{
  "success": true,
  "message": "Mission test_mission loaded"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `MissionError`: Mission file not found or invalid
- `ValidationError`: Invalid filename

---

### Start Mission
**POST** `/api/mission/start`

Starts execution of the loaded mission.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "Mission started"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `MissionError`: No mission loaded or mission invalid
- `NavigationError`: Mission execution failed

**Prerequisites:**
- Mission must be loaded
- Drone must be armed
- GPS lock required

---

## Camera Endpoints

### Take Photo
**POST** `/api/camera/photo`

Triggers camera to capture a photo.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "Photo captured"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `CameraError`: Photo capture failed

---

### Start Video Recording
**POST** `/api/camera/video/start`

Starts video recording.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "Video recording started"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `CameraError`: Video start failed (already recording, camera error)

---

### Stop Video Recording
**POST** `/api/camera/video/stop`

Stops video recording.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "Video recording stopped"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `CameraError`: Video stop failed (not recording, camera error)

---

### Get Camera Status
**GET** `/api/camera/status`

Gets current camera status and configuration.

**Request Parameters:** None

**Response:**
```json
{
  "success": true,
  "status": {
    "mode": "PHOTO",
    "is_recording": false,
    "last_photo_time": "2026-08-04T10:30:00",
    "last_video_start_time": null
  }
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `CameraError`: Failed to get camera status

---

### Set Camera Mode
**POST** `/api/camera/mode`

Sets camera operation mode.

**Request Body:**
```json
{
  "mode": "PHOTO"
}
```

**Parameters:**
- `mode` (string, required): Camera mode ("PHOTO" or "VIDEO")

**Response:**
```json
{
  "success": true,
  "message": "Camera mode set to PHOTO"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `CameraError`: Mode change failed
- `ValidationError`: Invalid camera mode

---

## Failsafe Endpoints

### Get Failsafe Status
**GET** `/api/failsafe/status`

Gets current failsafe system status.

**Request Parameters:** None

**Response:**
```json
{
  "success": true,
  "status": {
    "monitoring_active": true,
    "current_level": null,
    "current_reason": null,
    "failsafe_count": 0,
    "last_heartbeat": 1696456789.123
  }
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `FailsafeError`: Failed to get failsafe status

---

### Check All Failsafe
**POST** `/api/failsafe/check`

Runs all failsafe checks and returns results.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "results": {
    "battery": {"level": "normal", "value": 85},
    "gps": {"level": "normal", "satellites": 12},
    "altitude": {"level": "normal", "value": 15.5},
    "link": {"level": "normal", "heartbeat_age": 0.5},
    "timestamp": 1696456789.123
  }
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `FailsafeError`: Failsafe check failed

---

### Reset Failsafe
**POST** `/api/failsafe/reset`

Resets failsafe state and counters.

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "Failsafe reset"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `FailsafeError`: Reset failed

---

### Trigger Failsafe
**POST** `/api/failsafe/trigger`

Manually triggers a failsafe at specified level.

**Request Body:**
```json
{
  "level": "WARNING",
  "reason": "Manual test trigger"
}
```

**Parameters:**
- `level` (string, required): Failsafe level ("WARNING", "CAUTION", "CRITICAL", "EMERGENCY")
- `reason` (string, required): Reason for manual trigger

**Response:**
```json
{
  "success": true,
  "message": "Failsafe triggered"
}
```

**Error Responses:**
- `ConnectionError`: Drone not connected
- `FailsafeError`: Trigger failed
- `ValidationError`: Invalid failsafe level

---

## Telemetry Endpoints

### Get Status
**GET** `/api/status`

Gets comprehensive drone status for UI sync.

**Request Parameters:** None

**Response:**
```json
{
  "success": true,
  "status": {
    "connected": true,
    "initialized": true,
    "connection_string": "udpin:0.0.0.0:14551",
    "armed": false,
    "mode": "GUIDED"
  }
}
```

**Error Responses:**
- None (returns default status on error)

---

## Health Check Endpoints

### Basic Health Check
**GET** `/api/health`

Basic health check to verify the API is running.

**Request Parameters:** None

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": 1696456789.123
}
```

**Error Responses:**
- `InternalServerError`: Server error

---

### Detailed Health Check
**GET** `/api/health/detailed`

Comprehensive health check with system metrics and service status.

**Request Parameters:** None

**Response:**
```json
{
  "success": true,
  "timestamp": 1696456789.123,
  "system": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "memory_available": 8589934592,
    "memory_total": 17179869184,
    "disk_percent": 65.3,
    "disk_free": 107374182400,
    "disk_total": 536870912000
  },
  "drone": {
    "connected": true,
    "initialized": true
  },
  "services": {
    "telemetry_manager": {
      "running": true,
      "thread_alive": true
    }
  },
  "overall_status": "healthy"
}
```

**Status Values:**
- `healthy`: All systems operational
- `degraded`: Some systems not fully operational
- `unhealthy`: Critical system failures

**Error Responses:**
- `InternalServerError`: Failed to gather health metrics

---

### Readiness Check
**GET** `/api/health/ready`

Readiness check for load balancers and orchestration systems.

**Request Parameters:** None

**Response:**
```json
{
  "success": true,
  "status": "ready",
  "drone_connected": true,
  "timestamp": 1696456789.123
}
```

**Status Values:**
- `ready`: System ready to accept requests
- `not_ready`: System not ready (returns 503 status)

**Error Responses:**
- HTTP 503 Service Unavailable: System not ready

---

## WebSocket Events

### Telemetry Updates
**Event:** `telemetry_update`

Real-time telemetry data pushed via WebSocket.

**Payload:**
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
    "yaw": 45.2
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

**Update Rate:** 500ms

---

## Error Codes

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| `ConnectionError` | 400 | Connection-related failures |
| `TelemetryError` | 400 | Telemetry data issues |
| `ControlError` | 400 | Flight control failures |
| `NavigationError` | 400 | Navigation/waypoint issues |
| `MissionError` | 400 | Mission planning/execution issues |
| `CameraError` | 400 | Camera operation failures |
| `FailsafeError` | 400 | Failsafe system issues |
| `ConfigurationError` | 400 | Configuration problems |
| `ValidationError` | 400 | Input validation failures |
| `TimeoutError` | 400 | Operation timeouts |
| `EmergencyError` | 400 | Emergency situations |
| `InternalServerError` | 500 | Unexpected server errors |

---

## Rate Limiting

Currently not implemented. Recommended for production:
- 100 requests per minute per IP
- Stricter limits for control endpoints

---

## Security Considerations

### Current State
- No authentication implemented
- CORS allows all origins
- No rate limiting
- No request signing

### Recommended Improvements
1. Implement API key authentication
2. Add JWT token support
3. Restrict CORS to specific domains
4. Add rate limiting
5. Implement request signing
6. Add HTTPS support
7. Add audit logging

---

## Testing

### Example Requests

**Connect to drone:**
```bash
curl -X POST http://localhost:5000/api/connect \
  -H "Content-Type: application/json" \
  -d '{"connection_string": "udpin:0.0.0.0:14551"}'
```

**Arm drone:**
```bash
curl -X POST http://localhost:5000/api/arm \
  -H "Content-Type: application/json"
```

**Takeoff:**
```bash
curl -X POST http://localhost:5000/api/takeoff \
  -H "Content-Type: application/json" \
  -d '{"altitude": 10}'
```

**Get status:**
```bash
curl http://localhost:5000/api/status
```

---

## Versioning

API Version: 1.0.0

Versioning scheme: Semantic Versioning (MAJOR.MINOR.PATCH)

---

## Changelog

### v1.0.0 (2026-08-04)
- Initial API release
- Basic flight control endpoints
- Mission management
- Camera control
- Failsafe monitoring
- Telemetry streaming via WebSocket