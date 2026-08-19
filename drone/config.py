"""
config.py
Centralized configuration management for DroneNEA framework.
This module provides all configurable parameters for drone operations,
connection settings, safety limits, and mission defaults.
"""

from pathlib import Path
from typing import Dict, Any
import os
import logging

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
MISSION_DIR = BASE_DIR / "missions"
RESEARCH_DIR = BASE_DIR / "research"
CAMERA_DIR = LOG_DIR / "camera"

# Ensure directories exist
LOG_DIR.mkdir(exist_ok=True)
MISSION_DIR.mkdir(exist_ok=True)
RESEARCH_DIR.mkdir(exist_ok=True)
CAMERA_DIR.mkdir(exist_ok=True)


def setup_logging():
    """
    Configure centralized logging for the DroneNEA framework.
    
    This function sets up the root logger with file and console handlers.
    All modules can then simply use:
        logger = logging.getLogger(__name__)
    
    The configuration uses settings from LoggingConfig class.
    Call this function once at application startup.
    """
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Set the log level
    log_level = getattr(logging, LoggingConfig.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        LoggingConfig.LOG_FORMAT,
        datefmt=LoggingConfig.DATE_FORMAT
    )
    
    # Add file handler if enabled
    if LoggingConfig.LOG_TO_FILE:
        file_handler = logging.FileHandler(
            LOG_DIR / "drone.log",
            mode='a'
        )
        file_level = getattr(logging, LoggingConfig.FILE_LOG_LEVEL.upper(), logging.INFO)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Add console handler if enabled
    if LoggingConfig.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_level = getattr(logging, LoggingConfig.CONSOLE_LOG_LEVEL.upper(), logging.INFO)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate logs
    root_logger.propagate = False


class ConnectionConfig:
    """Connection-related configuration parameters."""
    
    # Default connection strings
    DEFAULT_TCP = "tcp:127.0.0.1:5760"
    DEFAULT_UDP = "udpin:0.0.0.0:14551"
    
    # Serial connection settings
    DEFAULT_BAUD = 115200
    
    # Timeouts
    DEFAULT_TIMEOUT = 30  # seconds for connection
    HEARTBEAT_TIMEOUT = 30  # seconds for heartbeat
    MESSAGE_TIMEOUT = 2  # seconds for MAVLink messages
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds


class FlightConfig:
    """Flight safety and operational limits."""
    
    # Altitude limits
    MIN_ALTITUDE = 0.5  # meters
    MAX_ALTITUDE = 120  # meters (default ArduPilot limit)
    DEFAULT_TAKEOFF_ALTITUDE = 10  # meters
    
    # Speed limits
    MAX_HORIZONTAL_SPEED = 30  # m/s
    MAX_VERTICAL_SPEED = 10  # m/s
    DEFAULT_CRUISE_SPEED = 5  # m/s for mission planning
    
    # Battery safety
    MIN_BATTERY_WARNING = 25  # percentage
    MIN_BATTERY_CRITICAL = 15  # percentage
    MIN_BATTERY_EMERGENCY = 10  # percentage
    
    # Time limits
    MAX_FLIGHT_TIME = 1800  # seconds (30 minutes)
    DEFAULT_LOITER_TIME = 30  # seconds
    
    # Mode change timeout
    MODE_CHANGE_TIMEOUT = 20  # seconds


class NavigationConfig:
    """Navigation and waypoint configuration."""
    
    # Waypoint tolerances
    DEFAULT_ACCEPTANCE_RADIUS = 5  # meters
    MIN_ACCEPTANCE_RADIUS = 1  # meters
    MAX_ACCEPTANCE_RADIUS = 50  # meters
    
    # Waypoint validation
    MIN_WAYPOINT_DISTANCE = 2  # meters (minimum distance between waypoints)
    MAX_WAYPOINTS_PER_MISSION = 99  # ArduPilot limit
    EARTH_RADIUS = 6371000

    # Pattern flight settings
    DEFAULT_PATTERN_ALTITUDE = 20  # meters
    DEFAULT_PATTERN_SPEED = 5  # m/s
    
    # Conversion factors
    METERS_PER_DEGREE = 111319.9
    
    # Hold times
    DEFAULT_HOLD_TIME = 0  # seconds
    MAX_HOLD_TIME = 60  # seconds
    
    # Return to launch
    RTL_ALTITUDE = 15  # meters
    RTL_LOITER_TIME = 0  # seconds


class TelemetryConfig:
    """Telemetry and monitoring configuration."""
    
    # Update rates
    TELEMETRY_UPDATE_INTERVAL = 0.1  # seconds
    POSITION_UPDATE_INTERVAL = 0.5  # seconds
    
    # Thresholds
    LANDING_THRESHOLD = 0.5  # meters (altitude below which is considered landed)
    ALTITUDE_TOLERANCE = 0.5  # meters
    
    # GPS requirements
    MIN_GPS_SATELLITES = 6
    MIN_GPS_FIX_TYPE = 3  # 3D fix
    
    # Logging
    LOG_ALL_MESSAGES = False
    LOG_MESSAGE_TYPES = ["HEARTBEAT", "GLOBAL_POSITION_INT", "SYS_STATUS", "ATTITUDE"]


class MissionConfig:
    """Mission planning and execution configuration."""
    
    # File settings
    MISSION_FILE_FORMAT = "json"
    CSV_EXPORT_ENABLED = True
    
    # Default mission metadata
    DEFAULT_MISSION_NAME = "custom_mission"
    DEFAULT_MISSION_AUTHOR = "DroneNEA"
    
    # Validation
    VALIDATE_ON_LOAD = True
    VALIDATE_ON_SAVE = True
    
    # Execution
    MISSION_RETRY_ATTEMPTS = 2
    WAYPOINT_TIMEOUT = 60  # seconds per waypoint


class CameraConfig:
    """Camera control configuration."""
    
    # MAVLink camera settings
    CAMERA_SYSTEM_ID = 1  # MAVLink camera system ID
    CAMERA_COMPONENT_ID = 100  # MAVLink camera component ID
    
    # Camera operation timeouts
    CAMERA_COMMAND_TIMEOUT = 5  # seconds
    CAMERA_STATUS_TIMEOUT = 3  # seconds
    
    # Camera storage
    CAMERA_STORAGE_PATH = CAMERA_DIR
    PHOTO_PREFIX = "photo_"
    VIDEO_PREFIX = "video_"
    
    # Camera operation delays
    PHOTO_CAPTURE_DELAY = 1.0  # seconds to wait after photo command
    VIDEO_START_DELAY = 2.0  # seconds to wait after video start
    VIDEO_STOP_DELAY = 1.0  # seconds to wait after video stop
    
    # Default camera settings
    DEFAULT_CAMERA_MODE = "PHOTO"  # PHOTO or VIDEO
    DEFAULT_PHOTO_INTERVAL = 2.0  # seconds for time-lapse


class FailsafeConfig:
    """Failsafe monitoring and response configuration."""
    
    # Monitoring intervals
    BATTERY_CHECK_INTERVAL = 5.0  # seconds (background monitoring)
    LINK_CHECK_INTERVAL = 2.0  # seconds (background monitoring)
    HEARTBEAT_TIMEOUT = 30.0  # seconds before link considered lost
    
    # Battery thresholds (from FlightConfig)
    BATTERY_WARNING = 25  # percentage
    BATTERY_CRITICAL = 15  # percentage
    BATTERY_EMERGENCY = 10  # percentage
    
    # GPS thresholds
    MIN_GPS_SATELLITES = 6
    MIN_GPS_FIX_TYPE = 3  # 3D fix
    
    # Altitude thresholds
    MAX_ALTITUDE_WARNING = 100  # meters
    MAX_ALTITUDE_CRITICAL = 120  # meters
    MIN_ALTITUDE_WARNING = 1.0  # meters
    
    # Failsafe response levels
    FAILSAFE_LEVELS = {
        "WARNING": "log_only",      # Log only, continue mission
        "CAUTION": "pause_mission", # Pause mission, alert user
        "CRITICAL": "abort_land",   # Abort mission, land
        "EMERGENCY": "rtl_emergency" # Immediate RTL or emergency land
    }
    
    # Response actions
    AUTO_RESPONSE_ENABLED = True
    PAUSE_ON_CAUTION = True
    RTL_ON_CRITICAL = True
    EMERGENCY_LAND_ON_EMERGENCY = True
    
    # Geofence settings (for future implementation)
    GEOFENCE_ENABLED = False
    GEOFENCE_RADIUS = 500  # meters from home
    GEOFENCE_MAX_ALTITUDE = 120  # meters


class LoggingConfig:
    """Logging configuration."""
    
    # Directory paths
    LOG_DIR = LOG_DIR
    MISSION_DIR = MISSION_DIR
    RESEARCH_DIR = RESEARCH_DIR
    
    # Log levels
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    CONSOLE_LOG_LEVEL = "INFO"
    FILE_LOG_LEVEL = "INFO"
    
    # Log format
    LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
    DATE_FORMAT = "%Y-%m-%d"
    
    # Log files
    LOG_TO_FILE = True
    LOG_TO_CONSOLE = True
    LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    LOG_FILE_BACKUP_COUNT = 5
    
    # Module-specific log files
    CONNECTION_LOG = "connection.log"
    CONTROL_LOG = "control.log"
    TELEMETRY_LOG = "telemetry.log"
    NAVIGATION_LOG = "navigation.log"
    MISSION_LOG = "mission.log"
    DRONE_LOG = "drone.log"
    CAMERA_LOG = "camera.log"
    FAILSAFE_LOG = "failsafe.log"


class EnvironmentConfig:
    """Environment-specific configuration."""
    
    # Current environment (can be set via environment variable)
    ENVIRONMENT = os.getenv("DRONE_ENV", "development")
    
    # Environment profiles
    PROFILES = {
        "development": {
            "connection": ConnectionConfig.DEFAULT_UDP,
            "timeout": 30,
            "log_level": "DEBUG",
        },
        "production": {
            "connection": ConnectionConfig.DEFAULT_TCP,
            "timeout": 15,
            "log_level": "INFO",
        },
        "testing": {
            "connection": "udpin:0.0.0.0:14551",
            "timeout": 10,
            "log_level": "WARNING",
        },
        "sitl": {
            "connection": "udpin:0.0.0.0:14551",
            "timeout": 30,
            "log_level": "INFO",
        },
    }
    
    @classmethod
    def get_profile(cls, environment: str = None) -> Dict[str, Any]:
        """Get configuration profile for specified environment."""
        env = environment or cls.ENVIRONMENT
        return cls.PROFILES.get(env, cls.PROFILES["development"])


class Config:
    """
    Main configuration class that aggregates all configuration sections.
    Provides easy access to all configuration parameters.
    """
    
    connection = ConnectionConfig()
    flight = FlightConfig()
    navigation = NavigationConfig()
    telemetry = TelemetryConfig()
    mission = MissionConfig()
    camera = CameraConfig()
    failsafe = FailsafeConfig()
    logging = LoggingConfig()
    environment = EnvironmentConfig()
    
    @classmethod
    def get_current_profile(cls) -> Dict[str, Any]:
        """Get the current environment profile."""
        return cls.environment.get_profile()
    
    @classmethod
    def set_environment(cls, environment: str):
        """Set the current environment."""
        if environment in cls.environment.PROFILES:
            cls.environment.ENVIRONMENT = environment
        else:
            raise ValueError(f"Unknown environment: {environment}")
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Get all configuration settings as a dictionary."""
        return {
            "connection": {
                "default_tcp": cls.connection.DEFAULT_TCP,
                "default_udp": cls.connection.DEFAULT_UDP,
                "default_baud": cls.connection.DEFAULT_BAUD,
                "default_timeout": cls.connection.DEFAULT_TIMEOUT,
            },
            "flight": {
                "min_altitude": cls.flight.MIN_ALTITUDE,
                "max_altitude": cls.flight.MAX_ALTITUDE,
                "max_horizontal_speed": cls.flight.MAX_HORIZONTAL_SPEED,
                "max_vertical_speed": cls.flight.MAX_VERTICAL_SPEED,
                "min_battery_warning": cls.flight.MIN_BATTERY_WARNING,
                "min_battery_critical": cls.flight.MIN_BATTERY_CRITICAL,
            },
            "navigation": {
                "default_acceptance_radius": cls.navigation.DEFAULT_ACCEPTANCE_RADIUS,
                "min_waypoint_distance": cls.navigation.MIN_WAYPOINT_DISTANCE,
                "max_waypoints": cls.navigation.MAX_WAYPOINTS_PER_MISSION,
            },
            "telemetry": {
                "landing_threshold": cls.telemetry.LANDING_THRESHOLD,
                "min_gps_satellites": cls.telemetry.MIN_GPS_SATELLITES,
            },
            "mission": {
                "mission_file_format": cls.mission.MISSION_FILE_FORMAT,
                "validate_on_load": cls.mission.VALIDATE_ON_LOAD,
            },
            "logging": {
                "log_level": cls.logging.LOG_LEVEL,
                "log_to_file": cls.logging.LOG_TO_FILE,
                "log_to_console": cls.logging.LOG_TO_CONSOLE,
            },
            "environment": {
                "current": cls.environment.ENVIRONMENT,
                "profile": cls.get_current_profile(),
            },
        }


# Convenience access
config = Config()


if __name__ == "__main__":
    # Display current configuration
    print("=" * 60)
    print("DroneNEA Configuration")
    print("=" * 60)
    print(f"Environment: {config.environment.ENVIRONMENT}")
    print(f"Profile: {config.get_current_profile()}")
    print()
    
    print("Connection Settings:")
    print(f"  Default UDP: {config.connection.DEFAULT_UDP}")
    print(f"  Default TCP: {config.connection.DEFAULT_TCP}")
    print(f"  Default Baud: {config.connection.DEFAULT_BAUD}")
    print(f"  Timeout: {config.connection.DEFAULT_TIMEOUT}s")
    print()
    
    print("Flight Safety Limits:")
    print(f"  Max Altitude: {config.flight.MAX_ALTITUDE}m")
    print(f"  Max Horizontal Speed: {config.flight.MAX_HORIZONTAL_SPEED}m/s")
    print(f"  Max Vertical Speed: {config.flight.MAX_VERTICAL_SPEED}m/s")
    print(f"  Min Battery Warning: {config.flight.MIN_BATTERY_WARNING}%")
    print()
    
    print("Navigation Settings:")
    print(f"  Acceptance Radius: {config.navigation.DEFAULT_ACCEPTANCE_RADIUS}m")
    print(f"  Min Waypoint Distance: {config.navigation.MIN_WAYPOINT_DISTANCE}m")
    print(f"  Max Waypoints: {config.navigation.MAX_WAYPOINTS_PER_MISSION}")
    print()
    
    print("Directory Paths:")
    print(f"  Base: {BASE_DIR}")
    print(f"  Logs: {LOG_DIR}")
    print(f"  Missions: {MISSION_DIR}")
    print(f"  Research: {RESEARCH_DIR}")
    print(f"  Camera: {config.camera.CAMERA_STORAGE_PATH}")
