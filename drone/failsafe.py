"""
failsafe.py
Failsafe monitoring and response system for autonomous drone operations.
Provides hybrid monitoring with background thread for critical issues and
on-demand checks for non-critical safety parameters.
Author: Emmanuel Ugwu
Project: DroneNEA
"""

import logging
import threading
import time
from typing import Optional, Dict, Any, Callable
from enum import Enum
from drone.connection import Connection
from drone.control import Control
from drone.telemetry import Telemetry
from drone.config import config

# Configure module-specific logger
logger = logging.getLogger(__name__)


class FailsafeLevel(Enum):
    """Failsafe severity levels."""
    WARNING = "WARNING"        # Log only, continue mission
    CAUTION = "CAUTION"        # Pause mission, alert user
    CRITICAL = "CRITICAL"      # Abort mission, land
    EMERGENCY = "EMERGENCY"    # Immediate RTL or emergency land


class Failsafe:
    """
    Hybrid failsafe monitoring system for autonomous drone safety.
    
    This class provides both background monitoring (for critical issues)
    and on-demand checks (for non-critical parameters) with configurable
    response actions based on severity levels.
    
    Background Monitoring (Critical):
        - Battery level
        - Connection/heartbeat status
    
    On-Demand Monitoring (Non-critical):
        - GPS quality
        - Altitude limits
        - Manual trigger via check_all()
    
    Response Actions:
        - WARNING: Log only
        - CAUTION: Pause mission, alert user
        - CRITICAL: Abort mission, land
        - EMERGENCY: Immediate RTL or emergency land
    """
    
    def __init__(self, connection: Connection, control: Control, telemetry: Telemetry):
        """
        Initialize failsafe monitoring system.
        
        Parameters:
            connection: Active MAVLink connection
            control: Control instance for safety responses
            telemetry: Telemetry instance for monitoring
        """
        self.connection = connection
        self.control = control
        self.telemetry = telemetry
        self.master = connection.get_master()
        
        # Monitoring state
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Failsafe state
        self._last_heartbeat_time = time.time()
        self._current_failsafe_level: Optional[FailsafeLevel] = None
        self._failsafe_reason = None
        self._failsafe_count = 0
        
        # Callbacks for external systems
        self._on_caution: Optional[Callable] = None
        self._on_critical: Optional[Callable] = None
        self._on_emergency: Optional[Callable] = None
        
        logger.info("Failsafe monitoring system initialized")
    
    def _check_connection(self):
        """Ensure the vehicle is connected."""
        if not self.connection.is_connected():
            raise ConnectionError("Drone is not connected.")
    
    def set_callbacks(self, on_caution: Optional[Callable] = None,
                      on_critical: Optional[Callable] = None,
                      on_emergency: Optional[Callable] = None):
        """
        Set callback functions for failsafe events.
        
        Parameters:
            on_caution: Callable - Function to call on CAUTION level
            on_critical: Callable - Function to call on CRITICAL level
            on_emergency: Callable - Function to call on EMERGENCY level
        """
        self._on_caution = on_caution
        self._on_critical = on_critical
        self._on_emergency = on_emergency
        logger.info("Failsafe callbacks updated")
    
    def start_monitoring(self):
        """Start background monitoring thread for critical parameters."""
        if self._monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self._monitoring_active = True
        self._stop_event.clear()
        
        self._monitor_thread = threading.Thread(
            target=self._background_monitor,
            daemon=True,
            name="FailsafeMonitor"
        )
        self._monitor_thread.start()
        
        logger.info("Background failsafe monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring thread."""
        if not self._monitoring_active:
            logger.warning("Monitoring not active")
            return
        
        self._monitoring_active = False
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        logger.info("Background failsafe monitoring stopped")
    
    def _background_monitor(self):
        """Background thread for monitoring critical parameters."""
        logger.info("Background monitor thread started")
        
        while not self._stop_event.is_set():
            try:
                if not self.connection.is_connected():
                    logger.warning("Connection lost in background monitor")
                    self._handle_failsafe(FailsafeLevel.EMERGENCY, "Connection lost")
                    break
                
                # Monitor battery
                battery_status = self._check_battery()
                if battery_status:
                    self._handle_failsafe(*battery_status)
                
                # Monitor link/heartbeat
                link_status = self._check_link()
                if link_status:
                    self._handle_failsafe(*link_status)
                
                # Update heartbeat time
                self._last_heartbeat_time = time.time()
                
            except Exception as e:
                logger.error(f"Error in background monitor: {e}")
            
            # Sleep for interval
            self._stop_event.wait(config.failsafe.BATTERY_CHECK_INTERVAL)
        
        logger.info("Background monitor thread stopped")
    
    def _check_battery(self) -> Optional[tuple]:
        """
        Check battery level and return failsafe status if needed.
        
        Returns:
            Optional[tuple] - (FailsafeLevel, reason) if threshold exceeded, None otherwise
        """
        try:
            battery = self.telemetry.get_battery()
            
            if battery is None:
                logger.warning("Battery data unavailable")
                return None
            
            if battery <= config.failsafe.BATTERY_EMERGENCY:
                return (FailsafeLevel.EMERGENCY, f"Critical battery: {battery}%")
            elif battery <= config.failsafe.BATTERY_CRITICAL:
                return (FailsafeLevel.CRITICAL, f"Low battery: {battery}%")
            elif battery <= config.failsafe.BATTERY_WARNING:
                return (FailsafeLevel.WARNING, f"Low battery warning: {battery}%")
            
            return None
            
        except Exception as e:
            logger.error(f"Battery check failed: {e}")
            return None
    
    def _check_link(self) -> Optional[tuple]:
        """
        Check connection/heartbeat status.
        
        Returns:
            Optional[tuple] - (FailsafeLevel, reason) if link issue, None otherwise
        """
        try:
            time_since_heartbeat = time.time() - self._last_heartbeat_time
            
            if time_since_heartbeat > config.failsafe.HEARTBEAT_TIMEOUT:
                return (FailsafeLevel.EMERGENCY, 
                       f"Heartbeat timeout: {time_since_heartbeat:.1f}s")
            
            return None
            
        except Exception as e:
            logger.error(f"Link check failed: {e}")
            return None
    
    def check_gps(self) -> Optional[tuple]:
        """
        Check GPS quality (on-demand).
        
        Returns:
            Optional[tuple] - (FailsafeLevel, reason) if GPS issue, None otherwise
        """
        self._check_connection()
        
        try:
            gps = self.telemetry.get_gps()
            
            if gps is None:
                return (FailsafeLevel.CRITICAL, "GPS data unavailable")
            
            satellites = gps.get("satellites", 0)
            fix_type = gps.get("fix_type", 0)
            
            if satellites < config.failsafe.MIN_GPS_SATELLITES:
                return (FailsafeLevel.CRITICAL, 
                       f"Insufficient satellites: {satellites}")
            
            if fix_type < config.failsafe.MIN_GPS_FIX_TYPE:
                return (FailsafeLevel.CRITICAL, 
                       f"Invalid GPS fix type: {fix_type}")
            
            return None
            
        except Exception as e:
            logger.error(f"GPS check failed: {e}")
            return None
    
    def check_altitude(self) -> Optional[tuple]:
        """
        Check altitude limits (on-demand).
        
        Returns:
            Optional[tuple] - (FailsafeLevel, reason) if altitude issue, None otherwise
        """
        self._check_connection()
        
        try:
            altitude = self.telemetry.get_altitude()
            
            if altitude is None:
                return (FailsafeLevel.WARNING, "Altitude data unavailable")
            
            if altitude > config.failsafe.MAX_ALTITUDE_CRITICAL:
                return (FailsafeLevel.CRITICAL, 
                       f"Altitude exceeded critical limit: {altitude:.1f}m")
            elif altitude > config.failsafe.MAX_ALTITUDE_WARNING:
                return (FailsafeLevel.WARNING, 
                       f"Altitude warning: {altitude:.1f}m")
            elif altitude < config.failsafe.MIN_ALTITUDE_WARNING:
                return (FailsafeLevel.WARNING, 
                       f"Low altitude warning: {altitude:.1f}m")
            
            return None
            
        except Exception as e:
            logger.error(f"Altitude check failed: {e}")
            return None
    
    def check_all(self) -> Dict[str, Any]:
        """
        Run all on-demand checks.
        
        Returns:
            Dict - Results of all checks
        """
        self._check_connection()
        
        results = {
            "gps": self.check_gps(),
            "altitude": self.check_altitude(),
            "battery": self._check_battery(),
            "link": self._check_link(),
            "timestamp": time.time()
        }
        
        return results
    
    def _handle_failsafe(self, level: FailsafeLevel, reason: str):
        """
        Handle failsafe event based on severity level.
        
        Parameters:
            level: FailsafeLevel - Severity of failsafe
            reason: str - Description of failsafe reason
        """
        self._current_failsafe_level = level
        self._failsafe_reason = reason
        self._failsafe_count += 1
        
        logger.warning(f"Failsafe triggered: {level.value} - {reason}")
        
        if not config.failsafe.AUTO_RESPONSE_ENABLED:
            logger.info("Auto-response disabled, failsafe logged only")
            return
        
        # Execute response based on level
        if level == FailsafeLevel.WARNING:
            # Log only, continue mission
            pass
            
        elif level == FailsafeLevel.CAUTION:
            # Pause mission, alert user
            logger.critical("CAUTION: Pausing mission")
            if self._on_caution:
                self._on_caution(reason)
            
        elif level == FailsafeLevel.CRITICAL:
            # Abort mission, land
            logger.critical("CRITICAL: Aborting mission and landing")
            if self._on_critical:
                self._on_critical(reason)
            if config.failsafe.RTL_ON_CRITICAL:
                self.control.rtl()
            
        elif level == FailsafeLevel.EMERGENCY:
            # Immediate RTL or emergency land
            logger.critical("EMERGENCY: Immediate response required")
            if self._on_emergency:
                self._on_emergency(reason)
            if config.failsafe.EMERGENCY_LAND_ON_EMERGENCY:
                self.control.emergency_land(reason)
    
    def trigger_failsafe(self, level: FailsafeLevel, reason: str):
        """
        Manually trigger a failsafe event.
        
        Parameters:
            level: FailsafeLevel - Severity of failsafe
            reason: str - Description of failsafe reason
        """
        self._handle_failsafe(level, reason)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current failsafe status.
        
        Returns:
            Dict - Failsafe system status
        """
        return {
            "monitoring_active": self._monitoring_active,
            "current_level": self._current_failsafe_level.value if self._current_failsafe_level else None,
            "current_reason": self._failsafe_reason,
            "failsafe_count": self._failsafe_count,
            "last_heartbeat": self._last_heartbeat_time,
            "auto_response_enabled": config.failsafe.AUTO_RESPONSE_ENABLED
        }
    
    def reset_failsafe(self):
        """Reset failsafe state after recovery."""
        self._current_failsafe_level = None
        self._failsafe_reason = None
        logger.info("Failsafe state reset")
    
    def is_monitoring(self) -> bool:
        """Check if background monitoring is active."""
        return self._monitoring_active
    
    def __repr__(self) -> str:
        return (f"Failsafe("
                f"monitoring={self._monitoring_active}, "
                f"level={self._current_failsafe_level.value if self._current_failsafe_level else 'None'}, "
                f"count={self._failsafe_count})")


# Standalone Test
if __name__ == "__main__":
    from drone.connection import Connection
    from drone.control import Control
    from drone.telemetry import Telemetry
    
    connection = Connection()
    
    try:
        connection.connect()
        control = Control(connection)
        telemetry = Telemetry(connection)
        failsafe = Failsafe(connection, control, telemetry)
        
        print("=== Failsafe Status ===")
        print(failsafe.get_status())
        print()
        print(failsafe)
        
        # Test on-demand checks
        print("\n=== Running On-Demand Checks ===")
        results = failsafe.check_all()
        for check, result in results.items():
            if check != "timestamp":
                print(f"{check}: {result}")
        
        # Note: Background monitoring would require actual connection
        print("\nTo test background monitoring, call failsafe.start_monitoring()")
        
    except ConnectionError as e:
        logger.error(e)
    finally:
        if connection.is_connected():
            connection.disconnect()
