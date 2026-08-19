cd ~/ardupilot
source ~/ardupilot-venv/bin/activate
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


python -m tests.test_telemetry
For running inside a folder like /tests

python -m py_compile drone/file.py
for compiling python files

tree /F
To see the tree of your folder

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
                                                                             