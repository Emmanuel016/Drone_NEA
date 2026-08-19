"""
drone.py
High-level interface to the DroneNEA framework.
This module provides the main Drone class that acts as the central interface
to all subsystems. It manages initialization, startup, shutdown, and provides
system status information.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from drone.connection import Connection
from drone.control import Control
from drone.telemetry import Telemetry
from drone.navigations import Navigation
from drone.mission import MissionPlanner
from drone.camera import Camera
from drone.failsafe import Failsafe
from drone.config import config

# Configure module-specific logger
logger = logging.getLogger(__name__)

class Drone:
    """
    High-level interface to the entire DroneNEA framework.
    The Drone class creates and manages all subsystems, provides system status,
    and handles startup/shutdown procedures. It does not contain MAVLink code,
    GPS calculations, mission execution logic, or telemetry parsing - those
    responsibilities belong to their respective modules.

    Responsibilities:
        - Create every subsystem
        - Expose subsystems to the user
        - Manage startup
        - Manage shutdown
        - Provide system status
    """
    
    def __init__(self):
        """Initialize the Drone interface without connecting."""
        logger.info("Initializing Drone interface...")
        
        # Create subsystems
        self.connection = Connection()
        self.control: Optional[Control] = None
        self.telemetry: Optional[Telemetry] = None
        self.navigation: Optional[Navigation] = None
        self.mission_planner: Optional[MissionPlanner] = None
        self.camera: Optional[Camera] = None
        self.failsafe: Optional[Failsafe] = None
        self._initialized = False
        logger.info("Drone interface initialized (not connected)")
    
    def is_connected(self) -> bool:
        return self.connection.is_connected()
 
    def _on_failsafe_caution(self, reason: str):
        """Handle CAUTION level failsafe - pause mission."""

        logger.warning(f"Failsafe CAUTION: {reason}")
        if self.navigation and self.navigation.mission_running:
            if self.control:
                self.control.rtl()
            self.navigation.abort_mission()
            logger.info("Mission paused due to failsafe")
 
    def _on_failsafe_critical(self, reason: str):
        """Handle CRITICAL level failsafe - abort mission."""

        logger.critical(f"Failsafe CRITICAL: {reason}")
        if self.navigation and self.navigation.mission_running:
            self.control.brake()
            self.navigation.abort_mission()
            logger.info("Mission aborted due to failsafe")
   
    def emergency_stop(self):
      if self.control:
        self.control.brake()

      if self.navigation:
        self.navigation.abort_mission()

    def _on_failsafe_emergency(self, reason: str):
        """Handle EMERGENCY level failsafe - immediate response."""

        logger.critical(f"Failsafe EMERGENCY: {reason}")
        if self.navigation and self.navigation.mission_running:
            self.navigation.abort_mission()
            logger.info("Mission aborted due to emergency failsafe")

    def Start(self, connection_string: str = None, 
                baud: int = None, timeout: int = None) -> bool:
        """
        Startup the drone system by connecting and initializing all subsystems.
        Parameters:
            connection_string: str - MAVLink connection string (uses config default if None)
            baud: int - Serial baud rate (uses config default if None)
            timeout: int - Connection timeout in seconds (uses config default if None)
        Returns:
            bool - True if startup successful, False otherwise
        """
        # Use config defaults if not provided
        if connection_string is None:
            connection_string = config.connection.DEFAULT_UDP
        if baud is None:
            baud = config.connection.DEFAULT_BAUD
        if timeout is None:
            timeout = config.connection.DEFAULT_TIMEOUT
        if self._initialized:
            logger.warning("Drone already initialized")
            return True
        
        try:
            logger.info("Starting drone system...")
            
            # Establish connection
            self.connection.connect(connection_string, baud, timeout)
            
            # Create subsystems with dependencies
            self.control = Control(self.connection)
            self.telemetry = Telemetry(self.connection)
            self.camera = Camera(self.connection, self.telemetry)
            self.failsafe = Failsafe(self.connection, self.control, self.telemetry)
            self.navigation = Navigation(self.connection, self.control, self.telemetry, self.camera)
            self.mission_planner = MissionPlanner(self.navigation)
            
            # Set up failsafe callbacks
            self.failsafe.set_callbacks(
                on_caution=self._on_failsafe_caution,
                on_critical=self._on_failsafe_critical,
                on_emergency=self._on_failsafe_emergency
            )
            
            # Start background failsafe monitoring
            self.failsafe.start_monitoring()
            
            self._initialized = True
            logger.info("Drone system startup complete")
            return True
            
        except Exception as e:
            logger.error(f"Startup failed: {e}")
            self.shutdown()
            return False
    
    def shutdown(self) -> None:
        """Shutdown the drone system and disconnect safely."""
        logger.info("Shutting down drone system...")
        
        try:
            # Stop failsafe monitoring
            if self.failsafe:
                self.failsafe.stop_monitoring()
            
            # Disconnect from vehicle
            if self.connection.is_connected():
                if self.navigation:
                    self.navigation.mission_running = False
                self.connection.disconnect()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            # Reset subsystems
            self.control = None
            self.telemetry = None
            self.navigation = None
            self.mission_planner = None
            self.camera = None
            self.failsafe = None
            self._initialized = False
            
            logger.info("Drone system shutdown complete")
    
    def status(self) -> Dict[str, Any]:
        """
        Get the current system status.
        Returns:
            Dict - System status information including connection state,
                   subsystem status, and basic telemetry if available.
        """
        status = {
            "initialized": self._initialized,
            "connected": self.connection.is_connected(),
            "connection_string": self.connection.connection_string,
        }
        
        if self._initialized and self.connection.is_connected():
            # Add subsystem status
            status["subsystems"] = {
                "control": self.control is not None,
                "telemetry": self.telemetry is not None,
                "navigation": self.navigation is not None,
                "mission_planner": self.mission_planner is not None,
                "camera": self.camera is not None,
                "failsafe": self.failsafe is not None
            }
            
            # Add basic telemetry if available
            if self.telemetry:
                try:
                    status["telemetry"] = {
                        "flight_mode": self.telemetry.get_flight_mode(),
                        "armed": self.telemetry.is_armed(),
                        "gps": self.telemetry.get_gps(),
                        "position": self.telemetry.get_position(),
                        "system_status": self.telemetry.get_system_status(),
                        "altitude": self.telemetry.get_altitude(),
                        "battery": self.telemetry.get_battery(),
                    }
                except Exception as e:
                    status["telemetry"] = f"Error: {e}"
            
            # Add navigation status if available
            if self.navigation:
                status["navigation"] = {
                    "waypoint_count": self.navigation.number_of_waypoints(),
                    "current_waypoint": self.navigation.current_waypoint_index,
                    "mission_running": self.navigation.mission_running
                }
            
            # Add camera status if available
            if self.camera:
                try:
                    status["camera"] = self.camera.get_camera_status()
                except Exception as e:
                    status["camera"] = f"Error: {e}"
            
            # Add failsafe status if available
            if self.failsafe:
                try:
                    status["failsafe"] = self.failsafe.get_status()
                except Exception as e:
                    status["failsafe"] = f"Error: {e}"
        
        return status
    
    def __repr__(self) -> str:
        lines = [
            "Drone(",
            f"  initialized={self._initialized},",
            f"  connection={self.connection},",
        ]
        
        if self._initialized:
            lines.append(f"  control={self.control},")
            lines.append(f"  telemetry={self.telemetry},")
            lines.append(f"  navigation={self.navigation},")
            lines.append(f"  mission_planner={self.mission_planner.__class__.__name__}()")
            if self.camera:
                lines.append(f"  camera={self.camera},")
            if self.failsafe:
                lines.append(f"  failsafe={self.failsafe},")
        
        lines.append(")")
        return "\n".join(lines)


# Standalone test
if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    
    # Test Drone interface
    drone = Drone()
    
    print("=== Drone Status (before startup) ===")
    print(drone.status())
    print()
    print(drone)
    print()
    
    # Note: Actual connection test would require running SITL
    print("To test with actual connection, call drone.Start()")