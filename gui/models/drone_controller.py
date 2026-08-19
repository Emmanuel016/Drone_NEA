"""
DroneController model for managing drone operations and state.
"""

from drone.drone import Drone
from drone.config import config
from drone.failsafe import FailsafeLevel
from typing import Optional, Dict, Any


class DroneController:
    """Manages drone operations and state."""
    def __init__(self):
        self.drone = Drone()
        self._connected = False
    
    def connect(self, connection_string=None, baud=None, timeout=None):
        """Connect to drone."""
        try:
            success = self.drone.Start(connection_string, baud, timeout)
            if success:
                self._connected = True
            return success
        except Exception as e:
            raise Exception(f"Connection failed: {str(e)}")
    
    def disconnect(self):
        """Disconnect from drone."""
        try:
            self.drone.shutdown()
            self._connected = False
            return True
        except Exception as e:
            raise Exception(f"Disconnect failed: {str(e)}")
    
    def arm(self):
        if not self._connected: raise Exception("Drone not connected")
        return self.drone.control.arm()
    
    def disarm(self):
        if not self._connected: raise Exception("Drone not connected")
        return self.drone.control.disarm()
    
    def takeoff(self, altitude):
        if not self._connected: raise Exception("Drone not connected")
        return self.drone.control.takeoff(altitude)
    
    def land(self):
        if not self._connected: raise Exception("Drone not connected")
        return self.drone.control.land()
    
    def set_mode(self, mode):
        if not self._connected: raise Exception("Drone not connected")
        return self.drone.control.set_mode(mode)
    
    def list_missions(self):
        if self.drone.mission_planner:
            return self.drone.mission_planner.list_missions()
        return []
    
    def load_mission(self, filename):
        if not self._connected: raise Exception("Drone not connected")
        return self.drone.mission_planner.load_mission(filename)
    
    def start_mission(self):
        if not self._connected: raise Exception("Drone not connected")
        return self.drone.navigation.start_mission()
    
    def get_status(self):
        """Get current comprehensive drone status for initial UI sync."""
        is_conn = self._connected
        return {
            'connected': is_conn,
            'initialized': getattr(self.drone, '_initialized', False),
            'connection_string': self.drone.connection.connection_string if getattr(self.drone, 'connection', None) else None,
            'armed': self.drone.control.is_armed() if is_conn and getattr(self.drone, 'control', None) else False,
            'mode': self.drone.control.get_mode() if is_conn and getattr(self.drone, 'control', None) else 'Unknown'
        }
    
    # Camera methods
    def take_photo(self):
        """Trigger camera photo capture."""
        if not self._connected:
            raise Exception("Drone not connected")
        return self.drone.camera.take_photo()
    
    def start_video(self):
        """Start video recording."""
        if not self._connected:
            raise Exception("Drone not connected")
        return self.drone.camera.start_video()
    
    def stop_video(self):
        """Stop video recording."""
        if not self._connected:
            raise Exception("Drone not connected")
        return self.drone.camera.stop_video()
    
    def get_camera_status(self):
        """Get camera status."""
        if not self._connected:
            raise Exception("Drone not connected")
        return self.drone.camera.get_camera_status()
    
    def set_camera_mode(self, mode):
        """Set camera mode."""
        if not self._connected:
            raise Exception("Drone not connected")
        return self.drone.camera.set_camera_mode(mode)
    
    # Failsafe methods
    def get_failsafe_status(self):
        """Get failsafe system status."""
        if not self._connected:
            raise Exception("Drone not connected")
        return self.drone.failsafe.get_status()
    
    def check_all_failsafe(self):
        """Run all failsafe checks."""
        if not self._connected:
            raise Exception("Drone not connected")
        return self.drone.failsafe.check_all()
    
    def reset_failsafe(self):
        """Reset failsafe state."""
        if not self._connected:
            raise Exception("Drone not connected")
        return self.drone.failsafe.reset_failsafe()
    
    def trigger_failsafe(self, level, reason):
        """Manually trigger failsafe."""
        if not self._connected:
            raise Exception("Drone not connected")
        level_enum = FailsafeLevel[level.upper()]
        return self.drone.failsafe.trigger_failsafe(level_enum, reason)
