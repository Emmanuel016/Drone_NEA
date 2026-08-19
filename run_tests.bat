@echo off
REM DroneNEA Test Runner Script
echo ====================================
echo DroneNEA Test Runner
echo ====================================
echo.

if "%1"=="unit" (
    echo Running Unit Tests ^(No SITL required^)...
    echo.
    python -m unittest tests.test_failsafe tests.test_api_routes tests.test_drone_controller tests.test_camera -v
    goto end
)

if "%1"=="integration" (
    echo Running Integration Tests ^(SITL required^)...
    echo.
    echo Make sure SITL is running with:
    echo python3 Tools/autotest/sim_vehicle.py -v ArduCopter --out=127.0.0.1:14550
    echo.
    python -m unittest tests.test_connections tests.test_controls tests.test_telemetry tests.test_navigations -v
    goto end
)

if "%1"=="failsafe" (
    echo Running Failsafe Tests...
    python -m unittest tests.test_failsafe -v
    goto end
)

if "%1"=="api" (
    echo Running API Tests...
    python -m unittest tests.test_api_routes -v
    goto end
)

if "%1"=="controller" (
    echo Running Drone Controller Tests...
    python -m unittest tests.test_drone_controller -v
    goto end
)

if "%1"=="all" (
    echo Running All Tests ^(requires SITL for integration tests^)...
    python -m unittest discover tests -v
    goto end
)

echo Usage:
echo   run_tests.bat unit          - Run unit tests only ^(no SITL^)
echo   run_tests.bat integration   - Run integration tests ^(SITL required^)
echo   run_tests.bat failsafe      - Run failsafe tests
echo   run_tests.bat api           - Run API tests
echo   run_tests.bat controller   - Run controller tests
echo   run_tests.bat all           - Run all tests
echo.
echo Quick start: run_tests.bat unit

:end
echo.
pause