# DroneNEA Test Runner Script (PowerShell)
# Helps separate unit tests from integration tests

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "DroneNEA Test Runner" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

if ($args[0] -eq "unit") {
    Write-Host "Running Unit Tests (No SITL required)..." -ForegroundColor Green
    Write-Host ""
    python -m unittest tests.test_failsafe tests.test_api_routes tests.test_drone_controller tests.test_camera -v
    exit
}

if ($args[0] -eq "integration") {
    Write-Host "Running Integration Tests (SITL required)..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Make sure SITL is running with:" -ForegroundColor Yellow
    Write-Host "python3 Tools/autotest/sim_vehicle.py -v ArduCopter --out=127.0.0.1:14550" -ForegroundColor Gray
    Write-Host ""
    python -m unittest tests.test_connections tests.test_controls tests.test_telemetry tests.test_navigations -v
    exit
}

if ($args[0] -eq "failsafe") {
    Write-Host "Running Failsafe Tests..." -ForegroundColor Green
    python -m unittest tests.test_failsafe -v
    exit
}

if ($args[0] -eq "api") {
    Write-Host "Running API Tests..." -ForegroundColor Green
    python -m unittest tests.test_api_routes -v
    exit
}

if ($args[0] -eq "controller") {
    Write-Host "Running Drone Controller Tests..." -ForegroundColor Green
    python -m unittest tests.test_drone_controller -v
    exit
}

if ($args[0] -eq "all") {
    Write-Host "Running All Tests (requires SITL for integration tests)..." -ForegroundColor Yellow
    python -m unittest discover tests -v
    exit
}

Write-Host "Usage:" -ForegroundColor White
Write-Host "  .\run_tests.ps1 unit          - Run unit tests only (no SITL)" -ForegroundColor Gray
Write-Host "  .\run_tests.ps1 integration   - Run integration tests (SITL required)" -ForegroundColor Gray
Write-Host "  .\run_tests.ps1 failsafe      - Run failsafe tests" -ForegroundColor Gray
Write-Host "  .\run_tests.ps1 api           - Run API tests" -ForegroundColor Gray
Write-Host "  .\run_tests.ps1 controller   - Run controller tests" -ForegroundColor Gray
Write-Host "  .\run_tests.ps1 all           - Run all tests" -ForegroundColor Gray
Write-Host ""
Write-Host "Quick start: .\run_tests.ps1 unit" -ForegroundColor Green