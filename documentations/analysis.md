# DroneNEA - Analysis Section

## 1. Problem Definition

### 1.1 Problem Statement
Drone technology has become increasingly accessible, but controlling drones programmatically remains complex and requires deep technical knowledge of MAVLink protocols and flight controller systems. There is a need for an educational platform that:

- Provides a user-friendly interface for drone control
- Allows students and researchers to understand drone programming concepts
- Enables safe simulation-based testing without hardware requirements
- Demonstrates real-world applications of computer science in robotics

### 1.2 Project Aim
To develop a comprehensive drone control system called "DroneNEA" that provides:
- A web-based graphical user interface for drone control
- Programmatic API for autonomous flight operations
- Integration with ArduPilot SITL (Software In The Loop) simulation
- Educational documentation and testing framework
- Real-world applicable skills in embedded systems and robotics

### 1.3 Target Users
- **Primary**: A-level Computer Science students learning about embedded systems
- **Secondary**: Researchers requiring drone simulation capabilities
- **Tertiary**: Educational institutions teaching robotics and programming

## 2. User Requirements

### 2.1 Functional Requirements
The system must provide:

1. **Connection Management**
   - Connect to ArduPilot drones via MAVLink protocol
   - Support multiple connection types (TCP, UDP, Serial)
   - Handle connection failures and retry logic
   - Display connection status to user

2. **Flight Control**
   - Arm and disarm drone motors safely
   - Control takeoff and landing operations
   - Implement return-to-launch (RTL) functionality
   - Support multiple flight modes (GUIDED, LOITER, LAND, etc.)
   - Emergency stop capabilities

3. **Navigation and Mission Planning**
   - Create and manage waypoint missions
   - Execute autonomous flight patterns
   - Calculate distances between waypoints
   - Support camera actions at waypoints
   - Save and load mission configurations

4. **Telemetry Monitoring**
   - Real-time display of drone position (GPS coordinates)
   - Battery level monitoring
   - Altitude and speed information
   - Flight mode and armed status
   - GPS quality indicators

5. **Camera Control**
   - Trigger photo capture
   - Start/stop video recording
   - Camera mode switching
   - Camera status monitoring

6. **Safety Systems**
   - Battery level monitoring with warnings
   - Connection loss detection
   - GPS quality checking
   - Altitude limit enforcement
   - Emergency response procedures

### 2.2 Non-Functional Requirements
- **Reliability**: System must maintain stable connection during flight operations
- **Usability**: Web interface must be intuitive for students with basic programming knowledge
- **Performance**: Real-time telemetry updates with minimal latency (<500ms)
- **Security**: Basic authentication for control operations
- **Compatibility**: Work with ArduPilot SITL simulation for testing without hardware

## 3. Research into Existing Solutions

### 3.1 Current Drone Control Solutions
Research identified several existing drone control platforms:

**QGroundControl**
- Pros: Professional-grade, comprehensive features
- Cons: Complex interface, steep learning curve, not education-focused

**Mission Planner**
- Pros: Powerful mission planning, ArduPilot integration
- Cons: Desktop application only, complex for beginners

**DroneKit Python**
- Pros: Programmatic control, Python-based
- Cons: Requires programming knowledge, limited GUI

### 3.2 Gaps Identified
- Lack of educational-focused drone control platforms
- No web-based interfaces combining GUI and API access
- Limited documentation for learning purposes
- No integrated testing frameworks for students

### 3.3 Proposed Solution
DroneNEA addresses these gaps by:
- Providing both web GUI and programmatic API
- Including comprehensive documentation and examples
- Integrating testing framework for validation
- Supporting simulation-based learning without hardware costs

## 4. Hardware and Software Requirements

### 4.1 Hardware Requirements
**Minimum Requirements:**
- Computer with internet connection
- 4GB RAM minimum
- Modern web browser (Chrome, Firefox, Edge)

**Optional Hardware:**
- ArduPilot-compatible flight controller
- MAVLink-compatible drone
- Camera module (for camera features)

### 4.2 Software Requirements
**Development Environment:**
- Python 3.8+
- Flask web framework
- ArduPilot SITL (for simulation)
- MAVLink library

**Runtime Environment:**
- Web browser with JavaScript support
- Network connection (for local development)

### 4.3 Dependencies
Key Python libraries:
- `flask` - Web framework
- `flask-socketio` - WebSocket support
- `pymavlink` - MAVLink protocol implementation
- `pytest` - Testing framework

## 5. Data Requirements

### 5.1 Input Data
- **Connection Parameters**: IP addresses, ports, baud rates
- **Mission Data**: Waypoint coordinates, altitudes, hold times
- **Control Commands**: Flight modes, altitudes, camera actions
- **Configuration Settings**: Safety limits, timeouts, thresholds

### 5.2 Output Data
- **Telemetry Data**: Position, attitude, battery, GPS information
- **Status Information**: Connection state, armed status, flight mode
- **Mission Status**: Current waypoint, mission progress
- **System Logs**: Error messages, warning notifications

### 5.3 Data Storage
- **Mission Files**: JSON format in `missions/` directory
- **Log Files**: Text format in `logs/` directory
- **Configuration**: Python configuration classes
- **Camera Data**: Timestamped photo/video metadata

## 6. Success Criteria

The project will be considered successful if:

1. ✅ System can connect to ArduPilot SITL simulation
2. ✅ Web interface displays real-time telemetry data
3. ✅ User can control basic flight operations (arm, takeoff, land)
4. ✅ Mission planning and execution works correctly
5. ✅ Safety systems prevent unsafe operations
6. ✅ API provides programmatic access to all features
7. ✅ Comprehensive testing validates system reliability
8. ✅ Documentation enables educational use

## 7. Technical Constraints and Limitations

### 7.1 Technical Constraints
- Dependency on ArduPilot ecosystem
- Requires MAVLink protocol knowledge for advanced features
- Web-based limitations (browser security restrictions)
- Network latency in real-time communication

### 7.2 Safety Constraints
- Cannot be used with real aircraft without proper certification
- Requires adult supervision for hardware testing
- Simulation recommended for educational use
- Emergency procedures must be understood

### 7.3 Time Constraints
- Development timeline aligned with academic year
- Balance between feature completeness and deadline
- Prioritization of core functionality over advanced features

---

## Appendix: Technical Setup Commands

### Command for running the SITL drone
```bash
cd ~/ardupilot
source ~/ardupilot-venv/bin/activate
python3 Tools/autotest/sim_vehicle.py \
-v ArduCopter \
--console \
--out=172.24.192.1:14550 \
--out=172.24.192.1:14551
```

This is the command for running the drone simulation and should be run on Ubuntu with virtual environment activated in the ArduPilot folder.
                                                                             