"""
Custom exception hierarchy for DroneNEA framework.
Provides specific exception types for better error handling and debugging.
"""


class DroneNEAError(Exception):
    """Base exception for all DroneNEA errors."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ConnectionError(DroneNEAError):
    """Raised when connection to drone fails or is lost."""
    pass


class TelemetryError(DroneNEAError):
    """Raised when telemetry data is unavailable or invalid."""
    pass


class ControlError(DroneNEAError):
    """Raised when flight control operation fails."""
    pass


class NavigationError(DroneNEAError):
    """Raised when navigation or waypoint operation fails."""
    pass


class MissionError(DroneNEAError):
    """Raised when mission planning or execution fails."""
    pass


class CameraError(DroneNEAError):
    """Raised when camera operation fails."""
    pass


class FailsafeError(DroneNEAError):
    """Raised when failsafe system encounters critical issues."""
    pass


class ConfigurationError(DroneNEAError):
    """Raised when configuration is invalid or missing."""
    pass


class ValidationError(DroneNEAError):
    """Raised when input validation fails."""
    pass


class TimeoutError(DroneNEAError):
    """Raised when operation times out."""
    pass


class EmergencyError(DroneNEAError):
    """Raised when emergency situation occurs."""
    pass