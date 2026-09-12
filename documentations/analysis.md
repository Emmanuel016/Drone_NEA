## Table of contents
1. [Control Command](control-command)

2. [Testing Guide](testing-guide)

### Command for running the SITL drone
cd ~/ardupilot
source ~/ardupilot-venv/bin/activate
python3 Tools/autotest/sim_vehicle.py \
-v ArduCopter \
--console \
--out=172.24.192.1:14550 \
--out=172.24.192.1:14551

This is the command for running my drone and it should be ran on ubuntu venv and ardupilot folder
## Commands for testing the SITL and related scripts.
These are recommended commands for testing the script.

MyPy - Best for catching contract violations between modules through type checking
Pyright - Alternative static type checker (faster, more thorough)
```json
pip install mypy
mypy drone/ gui/ --strict --ignore-missing-imports 
or
pip install pyright
pyright drone/ gui/
```

Interface Consistency Checking
Pylint - Checks for interface consistency and API contract violations:

```json
pip install pylint
pylint drone/ gui/ --disable=C0114,C0115,C0116
```
Dependency Analysis
Pydeps - Visualizes module dependencies to identify contract relationships
```json
pip install pydeps
pydeps drone gui --max-bacon=3 -o dependencies.png
```
Advanced Contract Checking
Hypothesis - Property-based testing to verify module contracts

```json
pip install hypothesis pytest-hypothesis
# Add property tests in tests/ directory
pytest tests/ -v
```
Quick Start Command
For immediate results, run this comprehensive audit
```json
pip install mypy pylint pyright
mypy drone/ gui/ --ignore-missing-imports && pyright drone/ gui/
```
Test scripts independently for logics
```json
python -m compileall .
pytest -q
python -m tests.test_telemetry
For running inside a folder like /tests
python -m py_compile drone/file.py
tree /F
```
To see the tree of your folder and compiling python files

## Control Command

(-35.3632622, 149.1652375),
     ^             ^
     |             |
   longitude    latitude
 My current waypoint location which is in austrialia

navigation.add_waypoint(-35.363262, 149.165237, 10, hold_time=2)
                                                 ^        ^
                                                 |        |
                                            altitude     hold time

## Testing Guide

### Unit Testing (No Simulation Required)
Run these tests anytime without starting SITL:

```bash
# Run unit tests with mocks
python -m unittest tests.test_failsafe -v
python -m unittest tests.test_api_routes -v
python -m unittest tests.test_drone_controller -v
python -m unittest tests.test_camera.py -v
```

### Integration Testing (Requires SITL Simulation)

1. Start SITL simulation in Ubuntu terminal:
```bash
cd ~/ardupilot
source ~/ardupilot-venv/bin/activate
python3 Tools/autotest/sim_vehicle.py -v ArduCopter --console --out=127.0.0.1:14550 --out=127.0.0.1:14551
```

2. Run integration tests in Windows terminal:
```bash
python -m unittest tests.test_connections -v
python -m unittest tests.test_controls -v
python -m unittest tests.test_telemetry -v
python -m unittest tests.test_navigations -v
```

For detailed testing guide, see: [TESTING_GUIDE.md](../documentations/TESTING_GUIDE.md)
                                                                             