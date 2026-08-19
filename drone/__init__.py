"""
DroneNEA - ArduPilot Drone Control Library
A Python library for controlling ArduPilot vehicles via MAVLink.
Provides high-level interfaces for flight control, telemetry, and navigation.
"""

from drone.connection import Connection
from drone.control import Control
from drone.telemetry import Telemetry
from drone.exceptions import (
    DroneNEAError,
    ConnectionError as DroneConnectionError,
    TelemetryError,
    ControlError,
    NavigationError,
    MissionError,
    CameraError,
    FailsafeError,
    ConfigurationError,
    ValidationError,
    TimeoutError,
    EmergencyError
)

__all__ = [
    "Connection",
    "Control", 
    "Telemetry",
    "DroneNEAError",
    "DroneConnectionError",
    "TelemetryError",
    "ControlError",
    "NavigationError",
    "MissionError",
    "CameraError",
    "FailsafeError",
    "ConfigurationError",
    "ValidationError",
    "TimeoutError",
    "EmergencyError"
]

__version__ = "0.1.0"
