# DroneNEA - AQA A-level Computer Science NEA Project

**Candidate Name:** [Your Name]
**Centre Number:** [Your Centre Number]
**Candidate Number:** [Your Candidate Number]
**Project Title:** DroneNEA - Educational Drone Control System
**Date:** September 2026

---

## Table of Contents

1. [Analysis](#analysis)
2. [Design](#design)
3. [Implementation](#implementation)
4. [Testing](#testing)
5. [Evaluation](#evaluation)
6. [Appendices](#appendices)

---

## Analysis

*The full Analysis section is available in [documentations/analysis.md](documentations/analysis.md)*

### 1.1 Problem Definition
Drone technology has become increasingly accessible, but controlling drones programmatically remains complex and requires deep technical knowledge of MAVLink protocols and flight controller systems. There is a need for an educational platform that provides a user-friendly interface for drone control, allows students to understand drone programming concepts, enables safe simulation-based testing without hardware requirements, and demonstrates real-world applications of computer science in robotics.

### 1.2 Project Aim
To develop a comprehensive drone control system called "DroneNEA" that provides a web-based graphical user interface for drone control, programmatic API for autonomous flight operations, integration with ArduPilot SITL simulation, educational documentation and testing framework, and real-world applicable skills in embedded systems and robotics.

### 1.3 User Requirements
**Functional Requirements:**
- Connection Management (TCP, UDP, Serial protocols)
- Flight Control (arm, takeoff, land, RTL, flight modes)
- Navigation and Mission Planning (waypoints, autonomous execution)
- Telemetry Monitoring (real-time position, battery, GPS data)
- Camera Control (photo capture, video recording)
- Safety Systems (battery monitoring, connection detection, emergency response)

**Non-Functional Requirements:**
- Reliability: Stable connection during flight operations
- Usability: Intuitive for students with basic programming knowledge
- Performance: Real-time telemetry updates with minimal latency (<500ms)
- Security: Basic authentication for control operations
- Compatibility: Work with ArduPilot SITL simulation

### 1.4 Success Criteria
1. System can connect to ArduPilot SITL simulation ✅
2. Web interface displays real-time telemetry data ✅
3. User can control basic flight operations ✅
4. Mission planning and execution works correctly ✅
5. Safety systems prevent unsafe operations ✅
6. API provides programmatic access to all features ✅
7. Comprehensive testing validates system reliability ✅
8. Documentation enables educational use ✅

*Continue reading the full Analysis section: [documentations/analysis.md](documentations/analysis.md)*

---

## Design

*The full Design section is available in [documentations/DESIGN_FOR_AQA.md](documentations/DESIGN_FOR_AQA.md)*

### 2.1 System Architecture
The DroneNEA system follows a three-tier architecture:
- **Presentation Layer:** Web Interface (HTML/CSS/JavaScript)
- **Application Layer:** Flask Server + API (Python)
- **Data Layer:** Drone Control Modules (Python)

### 2.2 Data Structures
**Configuration Classes:** Type-safe configuration management for connection, flight, navigation, and failsafe parameters.

**Waypoint Class:** Represents navigation points with GPS coordinates, altitude, hold times, and camera actions.

**Telemetry Data Structure:** Real-time object containing position, attitude, battery, speed, GPS, and status information.

**Mission Data Structure:** JSON format with metadata and waypoint arrays for mission planning.

### 2.3 Algorithms
**Haversine Formula:** Calculate distance between GPS coordinates (O(1) complexity).

**Failsafe Monitoring:** Background monitoring of critical safety parameters with configurable response levels.

**Mission Execution:** Sequential waypoint navigation with safety checks and camera integration (O(n) complexity).

**Emergency Landing:** Context-aware landing strategy based on battery and altitude conditions.

### 2.4 User Interface Design
The web interface is divided into four main sections:
- Connection Status Panel
- Telemetry Display
- Flight Controls
- Mission Planning Interface

Colour scheme uses green (normal), amber (warning), and red (error) for clear status indication.

### 2.5 Input/Output Design
**Input:** Connection parameters, flight commands, mission data, camera controls
**Output:** Real-time telemetry, status messages, API responses, log files

*Continue reading the full Design section: [documentations/DESIGN_FOR_AQA.md](documentations/DESIGN_FOR_AQA.md)*

---

## Implementation

*The full Implementation section is available in [documentations/IMPLEMENTATION_FOR_AQA.md](documentations/IMPLEMENTATION_FOR_AQA.md)*

### 3.1 Development Environment
- **Languages:** Python 3.8+, JavaScript ES6+, HTML5/CSS3
- **Frameworks:** Flask, Flask-SocketIO, Pymavlink
- **Tools:** VS Code, Git, ArduPilot SITL

### 3.2 Key Implementation Features
**Modular Architecture:** Independent modules for connection, control, telemetry, navigation, mission, camera, and failsafe systems.

**MAVLink Integration:** Pymavlink library with custom wrapper for error handling and timeout management.

**Real-Time Telemetry:** WebSocket-based streaming with 500ms update intervals and background thread management.

**Safety Systems:** Multi-level failsafe system with background monitoring, configurable thresholds, and automatic response triggering.

**Mission Planning:** JSON-based mission files with comprehensive validation and save/load functionality.

### 3.3 Code Structure
**Package Organisation:**
- `drone/` - Core drone control modules (12 modules)
- `gui/` - Web interface and API layer
- `tests/` - Comprehensive test suite (unit and integration)

**Class Hierarchy:** Main Drone interface with dependency injection pattern for modular design.

**Error Handling:** Custom exception hierarchy with centralised error handler for consistent API responses.

### 3.4 Technical Challenges and Solutions
- **MAVLink Complexity:** Used Pymavlink library with custom wrappers
- **Real-Time Communication:** WebSocket implementation with fallback mechanisms
- **Thread Safety:** Daemon threads with proper cleanup procedures
- **Cross-Platform Compatibility:** Flexible configuration handling
- **Testing Without Hardware:** Comprehensive mocking framework with SITL integration

### 3.5 Implementation Statistics
- **Total Lines of Code:** ~3,500 lines
- **Python Modules:** 12 core modules
- **Test Cases:** 30+ unit tests, 15+ integration tests
- **API Endpoints:** 20+ REST endpoints
- **Documentation:** 5+ comprehensive documents

*Continue reading the full Implementation section: [documentations/IMPLEMENTATION_FOR_AQA.md](documentations/IMPLEMENTATION_FOR_AQA.md)*

---

## Testing

*The full Testing section is available in [documentations/TESTING_FOR_AQA.md](documentations/TESTING_FOR_AQA.md)*

### 4.1 Testing Strategy
Comprehensive testing approach combining:
- **Unit Testing:** Individual component testing with mocks (59 tests)
- **Integration Testing:** Module interaction with SITL simulation (26 tests)
- **User Acceptance Testing:** Real user scenarios (8 tests)
- **Regression Testing:** Regular test execution throughout development

### 4.2 Unit Testing Results
**Framework:** Python unittest with unittest.mock

| Module | Test Cases | Passed | Coverage |
|--------|------------|--------|----------|
| Failsafe | 24 | 24 | 95% |
| Camera | 8 | 8 | 90% |
| API Routes | 12 | 12 | 85% |
| Drone Controller | 15 | 15 | 88% |
| **Total** | **59** | **59** | **89%** |

### 4.3 Integration Testing Results
**Environment:** ArduPilot SITL simulation

| Module | Test Cases | Passed | Notes |
|--------|------------|--------|-------|
| Connections | 6 | 6 | Requires SITL running |
| Controls | 8 | 8 | Requires armed drone |
| Telemetry | 5 | 5 | Real-time data validation |
| Navigation | 7 | 7 | Waypoint execution tests |
| **Total** | **26** | **26** | **All SITL-dependent** |

### 4.4 Performance Test Results
- **Telemetry Latency:** Average 120ms (target: <500ms) ✅
- **Connection Time:** Average 2.3s (target: <30s) ✅
- **Navigation Accuracy:** Average error 1.2m (target: <5m) ✅

### 4.5 User Acceptance Testing
**Participants:** 3 A-level Computer Science students
- **Scenario 1 (Connection):** 3/3 success, average 45 seconds
- **Scenario 2 (Mission Planning):** 3/3 success, average 3 minutes
- **Scenario 3 (Emergency Response):** 3/3 success, average 5 seconds

### 4.6 Test Evidence
All test executions logged with 100% pass rate. Comprehensive coverage analysis demonstrates thorough testing of all critical functionality.

*Continue reading the full Testing section: [documentations/TESTING_FOR_AQA.md](documentations/TESTING_FOR_AQA.md)*

---

## Evaluation

*The full Evaluation section is available in [documentations/evaluation.md](documentations/evaluation.md)*

### 5.1 Success Criteria Evaluation
**Overall Success Rate:** 8/8 criteria (100%)

| Success Criterion | Status | Achievement |
|-------------------|--------|-------------|
| ArduPilot SITL Connection | ✅ Achieved | 100% |
| Real-Time Telemetry Display | ✅ Achieved | 100% |
| Basic Flight Control | ✅ Achieved | 100% |
| Mission Planning & Execution | ✅ Achieved | 100% |
| Safety Systems | ✅ Achieved | 100% |
| Programmatic API Access | ✅ Achieved | 100% |
| Comprehensive Testing | ✅ Achieved | 100% |
| Educational Documentation | ✅ Achieved | 100% |

### 5.2 User Feedback
**Positive Feedback:**
- Intuitive interface with clear status indicators
- Real-time telemetry display is very responsive
- Comprehensive documentation and examples
- Safety systems provide confidence in use

**Areas for Improvement:**
- More tutorial content for beginners
- Camera controls could be more prominent
- Mobile optimisation would be helpful

### 5.3 Limitations
**Technical Limitations:**
- Network dependency for web interface
- Browser compatibility requirements
- Simulation dependency for testing
- Real-time latency constraints

**Functional Limitations:**
- Camera hardware compatibility
- Basic navigation without obstacle avoidance
- Linear mission execution
- Single drone control only

**Security Limitations:**
- No authentication implemented
- No HTTPS encryption
- No rate limiting on API endpoints

### 5.4 Potential Improvements
**Short-Term:** Enhanced tutorials, UI improvements, performance optimisations
**Medium-Term:** Advanced navigation, enhanced safety, multi-vehicle support
**Long-Term:** AI/ML integration, cloud services, advanced camera features

### 5.5 Personal Learning Outcomes
**Technical Skills:** Python programming, web development, embedded systems, testing frameworks
**Software Engineering:** Modular design, version control, code quality, error handling
**Problem-Solving:** Debugging techniques, performance optimisation, cross-platform development

### 5.6 Conclusion
The DroneNEA project has been highly successful in meeting its objectives with 100% of success criteria achieved. The system is well-suited for its intended educational purpose, demonstrating the application of A-level Computer Science concepts to a real-world problem.

*Continue reading the full Evaluation section: [documentations/evaluation.md](documentations/evaluation.md)*

---

## Appendices

### Appendix A: Technical Documentation
Additional technical documentation is available in the `documentations/` folder:

- **[design.md](documentations/design.md)** - Detailed system architecture and module documentation
- **[API_DOCUMENTATION.md](documentations/API_DOCUMENTATION.md)** - Complete API reference with examples
- **[TESTING_GUIDE.md](documentations/TESTING_GUIDE.md)** - Comprehensive testing guide for developers
- **[FRONTEND_BACKEND_COMMUNICATION.md](documentations/FRONTEND_BACKEND_COMMUNICATION.md)** - Communication architecture guide

### Appendix B: Code Structure
```
DroneNEA/
├── drone/                      # Core drone control modules
│   ├── drone.py               # Main interface
│   ├── connection.py          # MAVLink connection
│   ├── control.py            # Flight control
│   ├── telemetry.py          # Data reading
│   ├── navigations.py        # Waypoint management
│   ├── mission.py            # Mission files
│   ├── camera.py             # Camera control
│   ├── failsafe.py           # Safety monitoring
│   ├── config.py             # Configuration
│   └── exceptions.py         # Custom exceptions
├── gui/                       # Web interface
│   ├── routes/               # URL routing
│   ├── models/               # Business logic
│   ├── templates/            # HTML templates
│   └── config.py             # GUI configuration
├── tests/                     # Test suite
│   ├── unit/                 # Unit tests (mocked)
│   ├── integration/          # Integration tests (SITL)
│   └── manual/               # Manual test scripts
├── logs/                      # Log files
├── missions/                  # Mission files
├── documentations/           # Documentation
├── requirements.txt           # Python dependencies
└── run.py                    # Application entry point
```

### Appendix C: Running the System
**Prerequisites:**
- Python 3.8+
- ArduPilot SITL (for simulation)

**Installation:**
```bash
pip install -r requirements.txt
```

**Running the Application:**
```bash
python run.py
```

**Starting SITL Simulation (Ubuntu):**
```bash
cd ~/ardupilot
source ~/ardupilot-venv/bin/activate
python3 Tools/autotest/sim_vehicle.py -v ArduCopter --console --out=127.0.0.1:14550 --out=127.0.0.1:14551
```

**Accessing the Interface:**
Open web browser to: `http://localhost:5000`

### Appendix D: Testing Commands
**Unit Tests (No SITL required):**
```bash
python -m unittest tests.unit.test_failsafe -v
python -m unittest tests.unit.test_api_routes -v
python -m unittest tests.unit.test_drone_controller -v
python -m unittest tests.unit.test_camera -v
```

**Integration Tests (SITL required):**
```bash
python -m unittest tests.integration.test_connections -v
python -m unittest tests.integration.test_controls -v
python -m unittest tests.integration.test_telemetry -v
python -m unittest tests.integration.test_navigations -v
```

### Appendix E: Key Code Examples
**Connection Example:**
```python
from drone.connection import Connection
from drone.config import ConnectionConfig

config = ConnectionConfig()
connection = Connection(config)
success = connection.connect("udpin:127.0.0.1:14551")
```

**Mission Planning Example:**
```python
from drone.navigations import Waypoint

waypoint = Waypoint(
    latitude=-35.363262,
    longitude=149.165237,
    altitude=10.0,
    hold_time=2,
    camera_action="photo"
)
```

**API Usage Example:**
```bash
curl -X POST http://localhost:5000/api/connect \
  -H "Content-Type: application/json" \
  -d '{"connection_string": "udpin:0.0.0.0:14551"}'
```

---

## Bibliography

### Technical Resources
- ArduPilot. (2026). *ArduPilot SITL Simulation Guide*. Retrieved from http://ardupilot.org
- MAVLink. (2026). *MAVLink Protocol Documentation*. Retrieved from https://mavlink.io
- Python Software Foundation. (2026). *Python 3.8 Documentation*. Retrieved from https://docs.python.org

### Development Tools
- Flask Project. (2026). *Flask Web Framework*. Retrieved from https://flask.palletsprojects.com
- Pallets Projects. (2026). *Flask-SocketIO Documentation*. Retrieved from https://flask-socketio.readthedocs.io
- Python Testing. (2026). *unittest Documentation*. Retrieved from https://docs.python.org/3/library/unittest.html

### Academic Sources
- AQA. (2026). *A-level Computer Science NEA Guidance*. Assessment and Qualifications Alliance.
- Downing, D. (2025). *Python Programming for Beginners*. Academic Press.
- Simmons, C. (2024). *Web Development with Flask*. Technical Publications.

---

**End of Report**

*This document serves as the main submission for the AQA A-level Computer Science NEA project. All detailed sections are referenced and available in the accompanying documentation files.*