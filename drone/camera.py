"""
camera.py
MAVLink camera control for ArduPilot vehicles.
Provides camera operations via MAVLink commands including photo capture,
video recording, and camera status monitoring.
Author: Emmanuel Ugwu
Project: DroneNEA
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any
from pymavlink import mavutil
from drone.connection import Connection
from drone.telemetry import Telemetry
from drone.config import config

# Configure module-specific logger
logger = logging.getLogger(__name__)


class Camera:
    """
    MAVLink camera controller for drone-mounted cameras.
    
    This class provides high-level camera control using MAVLink commands.
    It supports digital cameras compatible with MAVLink protocol.
    
    Features:
        - Single photo capture
        - Video recording control
        - Camera mode switching
        - Camera status monitoring
        - Camera information queries
    """
    
    def __init__(self, connection: Connection, telemetry: Telemetry):
        """
        Initialize camera controller.
        
        Parameters:
            connection: Active MAVLink connection
            telemetry: Telemetry instance for system information
        """
        self.connection = connection
        self.telemetry = telemetry
        self.master = connection.get_master()
        
        # Camera state
        self._is_recording = False
        self._camera_mode = config.camera.DEFAULT_CAMERA_MODE
        self._last_photo_time = None
        self._last_video_start_time = None
        
        logger.info("Camera controller initialized")
    
    def _check_connection(self):
        """Ensure the vehicle is connected."""
        if not self.connection.is_connected():
            raise ConnectionError("Drone is not connected.")
    
    def take_photo(self, session: int = 0, save_location: bool = True) -> bool:
        """
        Trigger single photo capture via MAVLink.
        
        Parameters:
            session: int - Camera session ID (0 for default)
            save_location: bool - Whether to save location metadata with photo
            
        Returns:
            bool - True if photo command sent successfully
        """
        self._check_connection()
        logger.info("Triggering photo capture...")
        
        try:
            # Send DIGICAM_CONTROL command for photo
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_DO_DIGICAM_CONTROL,
                0,  # confirmation
                0,  # param1: session (0 for default)
                1,  # param2: zoom position (not used)
                0,  # param3: zoom step (not used)
                0,  # param4: focus lock (0 = unlock)
                1 if save_location else 0,  # param5: shot command (1 = take photo)
                0,  # param6: image quality (not used)
                0   # param7: image resolution (not used)
            )
            
            # Wait for camera to process
            time.sleep(config.camera.PHOTO_CAPTURE_DELAY)
            
            self._last_photo_time = datetime.now()
            logger.info("Photo capture command sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Photo capture failed: {e}")
            return False
    
    def start_video(self, session: int = 0) -> bool:
        """
        Start video recording via MAVLink.
        
        Parameters:
            session: int - Camera session ID (0 for default)
            
        Returns:
            bool - True if video start command sent successfully
        """
        self._check_connection()
        
        if self._is_recording:
            logger.warning("Video recording already in progress")
            return True
        
        logger.info("Starting video recording...")
        
        try:
            # Send VIDEO_START_CAPTURE command
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_VIDEO_START_CAPTURE,
                0,  # confirmation
                session,  # param1: camera session ID
                0,  # param2: frequency (0 = normal)
                0,  # param3: status (not used)
                0,  # param4: not used
                0,  # param5: not used
                0,  # param6: not used
                0   # param7: not used
            )
            
            # Wait for camera to start recording
            time.sleep(config.camera.VIDEO_START_DELAY)
            
            self._is_recording = True
            self._last_video_start_time = datetime.now()
            logger.info("Video recording started")
            return True
            
        except Exception as e:
            logger.error(f"Video start failed: {e}")
            return False
    
    def stop_video(self, session: int = 0) -> bool:
        """
        Stop video recording via MAVLink.
        
        Parameters:
            session: int - Camera session ID (0 for default)
            
        Returns:
            bool - True if video stop command sent successfully
        """
        self._check_connection()
        
        if not self._is_recording:
            logger.warning("No video recording in progress")
            return True
        
        logger.info("Stopping video recording...")
        
        try:
            # Send VIDEO_STOP_CAPTURE command
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_VIDEO_STOP_CAPTURE,
                0,  # confirmation
                session,  # param1: camera session ID
                0,  # param2: not used
                0,  # param3: not used
                0,  # param4: not used
                0,  # param5: not used
                0,  # param6: not used
                0   # param7: not used
            )
            
            # Wait for camera to stop recording
            time.sleep(config.camera.VIDEO_STOP_DELAY)
            
            self._is_recording = False
            logger.info("Video recording stopped")
            return True
            
        except Exception as e:
            logger.error(f"Video stop failed: {e}")
            return False
    
    def set_camera_mode(self, mode: str) -> bool:
        """
        Set camera mode (photo or video).
        
        Parameters:
            mode: str - Camera mode ("PHOTO" or "VIDEO")
            
        Returns:
            bool - True if mode set successfully
        """
        self._check_connection()
        
        mode = mode.upper()
        if mode not in ["PHOTO", "VIDEO"]:
            logger.error(f"Invalid camera mode: {mode}")
            return False
        
        logger.info(f"Setting camera mode to {mode}")
        self._camera_mode = mode
        return True
    
    def get_camera_status(self) -> Dict[str, Any]:
        """
        Get current camera status.
        
        Returns:
            Dict - Camera status information
        """
        self._check_connection()
        
        status = {
            "mode": self._camera_mode,
            "is_recording": self._is_recording,
            "last_photo_time": self._last_photo_time.isoformat() if self._last_photo_time else None,
            "last_video_start_time": self._last_video_start_time.isoformat() if self._last_video_start_time else None,
        }
        
        return status
    
    def get_camera_info(self) -> Optional[Dict[str, Any]]:
        """
        Query camera information and capabilities.
        
        Returns:
            Dict - Camera information or None if unavailable
        """
        self._check_connection()
        logger.info("Querying camera information...")
        
        try:
            # Request camera information via MAVLink
            # This is a simplified implementation - actual implementation
            # would depend on camera's MAVLink capabilities
            
            info = {
                "system_id": config.camera.CAMERA_SYSTEM_ID,
                "component_id": config.camera.CAMERA_COMPONENT_ID,
                "supported_modes": ["PHOTO", "VIDEO"],
                "status": "available"
            }
            
            logger.info(f"Camera info: {info}")
            return info
            
        except Exception as e:
            logger.error(f"Failed to get camera info: {e}")
            return None
    
    def is_recording(self) -> bool:
        """Check if video recording is in progress."""
        return self._is_recording
    
    def get_camera_mode(self) -> str:
        """Get current camera mode."""
        return self._camera_mode
    
    def time_lapse_photo(self, interval: float, count: int) -> bool:
        """
        Capture time-lapse photos.
        
        Parameters:
            interval: float - Time between photos in seconds
            count: int - Number of photos to capture
            
        Returns:
            bool - True if time-lapse completed successfully
        """
        self._check_connection()
        logger.info(f"Starting time-lapse: {count} photos every {interval}s")
        
        # Switch to photo mode
        self.set_camera_mode("PHOTO")
        
        for i in range(count):
            logger.info(f"Time-lapse photo {i+1}/{count}")
            
            if not self.take_photo():
                logger.error(f"Time-lapse failed at photo {i+1}")
                return False
            
            # Wait for interval (except after last photo)
            if i < count - 1:
                time.sleep(interval)
        
        logger.info("Time-lapse completed")
        return True
    
    def __repr__(self) -> str:
        return (f"Camera("
                f"mode={self._camera_mode}, "
                f"recording={self._is_recording})")


# Standalone Test
if __name__ == "__main__":
    from drone.connection import Connection
    from drone.telemetry import Telemetry
    
    connection = Connection()
    
    try:
        connection.connect()
        telemetry = Telemetry(connection)
        camera = Camera(connection, telemetry)
        
        print("=== Camera Status ===")
        print(camera.get_camera_status())
        print()
        print(camera)
        
        # Note: Actual camera commands would require a MAVLink-compatible camera
        print("To test with actual camera, call camera.take_photo()")
        
    except ConnectionError as e:
        logger.error(e)
    finally:
        if connection.is_connected():
            connection.disconnect()
