# DroneNEA Testing Guide

## Overview

DroneNEA has two types of tests:
1. **Unit Tests** - Use mocks, no hardware/SITL required
2. **Integration Tests** - Require real drone or SITL simulation

---

## Unit Testing (With Mocks - No Simulation Required)

### Run Specific Unit Test Files

```bash
# Run specific unit test file
python -m unittest tests.test_failsafe -v

# Run new API and controller tests
python -m unittest tests.test_api_routes -v
python -m unittest tests.test_drone_controller -v

# Run all unit tests that use mocks
python -m unittest tests.test_failsafe tests.test_api_routes tests.test_drone_controller -v
```

### Unit Test Files (No Simulation Required)

- ✅ `tests/test_failsafe.py` - Uses mocks for all drone components
- ✅ `tests/test_api_routes.py` - Tests API with mocked Flask context
- ✅ `tests/test_drone_controller.py` - Tests controller with mocked drone
- ✅ `tests/test_camera.py` - Uses mocks for camera operations

### Example Unit Test Run

```bash
# From project root
cd C:\Users\user\Documents\DroneNEA

# Run failsafe tests (completely mocked)
python -m unittest tests.test_failsafe -v

# Output:
# test_check_all ... ok
# test_check_battery_critical ... ok
# ... (24 tests total)
# Ran 24 tests in 0.225s
# OK
```

---

## Integration Testing (With SITL Simulation Required)

### Step 1: Start SITL Simulation

**On Ubuntu/Linux (in your ArduPilot environment):**

```bash
cd ~/ardupilot
source ~/ardupilot-venv/bin/activate

# Start SITL simulation
python3 Tools/autotest/sim_vehicle.py \
  -v ArduCopter \
  --console \
  --out=127.0.0.1:14550 \
  --out=127.0.0.1:14551
```

**What this does:**
- Starts ArduCopter SITL (software in the loop simulation)
- Exposes MAVLink on UDP ports 14550 and 14551
- Simulates a real drone without hardware

### Step 2: Run Integration Tests

**In a separate terminal (Windows):**

```bash
cd C:\Users\user\Documents\DroneNEA

# Run connection test (requires SITL)
python -m unittest tests.test_connections -v

# Run control test (requires SITL and armed drone)
python -m unittest tests.test_controls -v

# Run telemetry test (requires SITL)
python -m unittest tests.test_telemetry -v

# Run navigation tests (requires SITL)
python -m unittest tests.test_navigations -v
```

### Integration Test Files (Simulation Required)

- ⚠️ `tests/test_connections.py` - Requires SITL connection
- ⚠️ `tests/test_controls.py` - Requires SITL + armed drone
- ⚠️ `tests/test_telemetry.py` - Requires SITL connection
- ⚠️ `tests/test_navigations.py` - Requires SITL + armed drone
- ⚠️ `tests/test_navigations_patterns.py` - Requires SITL + armed drone
- ⚠️ `tests/test_mission.py` - Requires SITL + armed drone

---

## Organizing Tests by Type

### Recommended Directory Structure

```
tests/
├── unit/                    # Unit tests (mocked)
│   ├── test_failsafe.py
│   ├── test_camera.py
│   ├── test_api_routes.py
│   └── test_drone_controller.py
├── integration/             # Integration tests (SITL required)
│   ├── test_connections.py
│   ├── test_controls.py
│   ├── test_telemetry.py
│   ├── test_navigations.py
│   ├── test_navigations_patterns.py
│   └── test_mission.py
└── __init__.py
```

### Running by Category

```bash
# Run only unit tests
python -m unittest discover tests/unit -v

# Run only integration tests (after starting SITL)
python -m unittest discover tests/integration -v

# Run all tests (will fail on integration tests without SITL)
python -m unittest discover tests -v
```

---

## Using Environment Variables to Skip Tests

### Add Skip Decorators to Integration Tests

```python
import os
import unittest

# Skip integration tests if SITL not available
SKIP_INTEGRATION = not os.environ.get('DRONE_SITL_AVAILABLE', '').lower() == 'true'

@unittest.skipIf(SKIP_INTEGRATION, "SITL simulation not available")
class TestConnections(unittest.TestCase):
    def test_connection(self):
        # Test code here
        pass
```

### Run Tests with Environment Variable

```bash
# Skip integration tests (default)
python -m unittest discover tests -v

# Include integration tests
set DRONE_SITL_AVAILABLE=true
python -m unittest discover tests -v
```

---

## Creating Mock-Based Unit Tests

### Example: Testing Without Real Drone

```python
import unittest
from unittest.mock import Mock, patch
from drone.failsafe import Failsafe
from drone.connection import Connection
from drone.control import Control
from drone.telemetry import Telemetry

class TestFailsafeUnit(unittest.TestCase):
    def setUp(self):
        # Create mock objects instead of real drone
        self.mock_connection = Mock(spec=Connection)
        self.mock_connection.is_connected.return_value = True
        self.mock_connection.get_master.return_value = Mock()
        
        self.mock_control = Mock(spec=Control)
        self.mock_telemetry = Mock(spec=Telemetry)
        
        # Create failsafe with mocks
        self.failsafe = Failsafe(
            self.mock_connection, 
            self.mock_control, 
            self.mock_telemetry
        )
    
    def test_battery_warning(self):
        # Mock battery reading
        self.mock_telemetry.get_battery.return_value = 20
        
        # Test failsafe logic without real drone
        result = self.failsafe._check_battery()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], FailsafeLevel.WARNING)
```

---

## Testing Workflow

### Development Workflow

```bash
# 1. Write code
# 2. Write unit test with mocks
python -m unittest tests.unit.test_new_feature -v

# 3. Fix issues until unit tests pass

# 4. Start SITL (in Ubuntu terminal)
# 5. Run integration tests
python -m unittest tests.integration.test_new_feature -v

# 6. Fix integration issues

# 7. Run all tests
python -m unittest discover tests -v
```

### CI/CD Workflow

```bash
# In CI/CD pipeline:

# Stage 1: Unit tests (always run)
python -m unittest discover tests/unit -v

# Stage 2: Start SITL container
# Stage 3: Integration tests (if SITL available)
python -m unittest discover tests/integration -v
```

---

## Common Testing Scenarios

### Scenario 1: Quick Development Test

```bash
# Just run unit tests (fast, no setup)
python -m unittest tests.test_failsafe tests.test_api_routes -v
```

### Scenario 2: Full System Test

```bash
# Terminal 1: Start SITL
cd ~/ardupilot && source ~/ardupilot-venv/bin/activate
python3 Tools/autotest/sim_vehicle.py -v ArduCopter --out=127.0.0.1:14550

# Terminal 2: Run all tests
cd C:\Users\user\Documents\DroneNEA
python -m unittest discover tests -v
```

### Scenario 3: Test Specific Functionality

```bash
# Test only failsafe system
python -m unittest tests.test_failsafe -v

# Test only API endpoints
python -m unittest tests.test_api_routes -v

# Test only navigation (requires SITL)
python -m unittest tests.test_navigations -v
```

---

## Debugging Failed Tests

### Verbose Output

```bash
# Get detailed test output
python -m unittest tests.test_failsafe -v

# Get even more detail
python -m unittest tests.test_failsafe -vv
```

### Run Single Test Method

```bash
# Run specific test method
python -m unittest tests.test_failsafe.TestFailsafe.test_check_battery_warning -v
```

### Debug with pdb

```python
import unittest
import pdb

class MyTest(unittest.TestCase):
    def test_something(self):
        pdb.set_trace()  # Add breakpoint
        # Test code here
```

---

## Test Coverage

### Check Coverage (requires coverage.py)

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run -m unittest discover tests/unit

# Generate coverage report
coverage report -m

# Generate HTML report
coverage html
```

---

## Best Practices

### 1. Mock External Dependencies
- Always mock MAVLink connections in unit tests
- Mock hardware-specific operations
- Use `unittest.mock.Mock` and `unittest.mock.patch`

### 2. Keep Tests Independent
- Each test should run independently
- Use `setUp()` and `tearDown()` for test isolation
- Don't rely on test execution order

### 3. Test Edge Cases
- Test error conditions
- Test boundary values
- Test timeout scenarios

### 4. Use Descriptive Test Names
```python
# Good
def test_battery_critical_level_triggers_emergency_failsafe(self):

# Bad
def test_battery(self):
```

### 5. Organize Tests by Feature
- Group related tests together
- Use test classes for related functionality
- Keep test files focused

---

## Troubleshooting

### Issue: Tests Hang Waiting for Connection

**Cause:** Running integration test without SITL running

**Solution:** 
- Start SITL first, or
- Run unit tests only, or
- Add skip decorators to integration tests

### Issue: Import Errors in Tests

**Cause:** Python path issues

**Solution:**
```bash
# Run from project root
cd C:\Users\user\Documents\DroneNEA
python -m unittest tests.test_failsafe -v
```

### Issue: Mock Not Working

**Cause:** Mock object not configured correctly

**Solution:**
```python
# Make sure to configure return values
mock_connection.is_connected.return_value = True
mock_telemetry.get_battery.return_value = 50
```

---

## Quick Reference

### Unit Test Commands (No SITL)
```bash
python -m unittest tests.test_failsafe -v
python -m unittest tests.test_api_routes -v
python -m unittest tests.test_drone_controller -v
python -m unittest tests.test_camera.py -v
```

### Integration Test Commands (Requires SITL)
```bash
python -m unittest tests.test_connections -v
python -m unittest tests.test_controls -v
python -m unittest tests.test_telemetry -v
python -m unittest tests.test_navigations -v
python -m unittest tests.test_mission -v
```

### SITL Startup Command
```bash
cd ~/ardupilot
source ~/ardupilot-venv/bin/activate
python3 Tools/autotest/sim_vehicle.py -v ArduCopter --console --out=127.0.0.1:14550 --out=127.0.0.1:14551
```

---

This guide helps you separate unit testing (fast, mocked) from integration testing (slower, requires SITL) for efficient development workflow.