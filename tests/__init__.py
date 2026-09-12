"""
DroneNEA Test Suite

This package contains all tests for the DroneNEA project.

Test Structure:
- unit/: Unit tests for individual components (no hardware required)
- integration/: Integration tests requiring drone hardware or SITL
- utils.py: Shared test utilities and helpers
- conftest.py: Shared pytest fixtures and configuration

Running Tests:
- Run all tests: pytest
- Run unit tests only: pytest tests/unit/
- Run integration tests only: pytest tests/integration/
- Run specific test: pytest tests/unit/test_camera.py
"""
