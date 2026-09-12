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
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from pymavlink import mavutil
from drone.connection import Connection
from drone.telemetry import Telemetry
from drone.message_receiver import MessageReceiver
from drone.config import config
from drone.exceptions import ConnectionError as DroneConnectionError

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
    
    def __init__(self, connection: Connection, telemetry: Telemetry, socketio=None, message_receiver: MessageReceiver = None):
        """
        Initialize camera controller.
        Parameters:
            connection: Active MAVLink connection
            telemetry: Telemetry instance for system information
            socketio: Optional Socket.IO instance for real-time events
            message_receiver: Optional central message receiver for camera messages
        """
        self.connection = connection
        self.telemetry = telemetry
        self.master = connection.get_master()
        self.socketio = socketio
        self.message_receiver = message_receiver
        
        # Camera state
        self._is_recording = False
        self._camera_mode = config.camera.DEFAULT_CAMERA_MODE
        self._last_photo_time = None
        self._last_video_start_time = None
        
        # Photo tracking with thread safety
        self._captured_photos: List[Dict[str, Any]] = []
        self._photos_lock = threading.Lock()
        self._photo_storage_path = Path(config.camera.CAMERA_STORAGE_PATH)
        self._photo_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Subscribe to camera messages if receiver is provided
        if self.message_receiver and config.camera.ENABLE_PHOTO_DOWNLOAD:
            self._setup_message_subscriptions()
        
        logger.info("Camera controller initialized")
    
    def _check_connection(self):
        """Ensure the vehicle is connected."""
        if not self.connection.is_connected():
            raise DroneConnectionError("Drone is not connected.")
    
    def _setup_message_subscriptions(self):
        """
        Subscribe to camera-related MAVLink messages through the central receiver.
        """
        self.message_receiver.subscribe('CAMERA_IMAGE_CAPTURED', self._handle_camera_message)
        self.message_receiver.subscribe('CAMERA_TRIGGER', self._handle_camera_message)
        logger.debug("Camera message subscriptions set up")
    
    def _cleanup_message_subscriptions(self):
        """
        Unsubscribe from camera-related MAVLink messages.
        """
        if self.message_receiver:
            self.message_receiver.unsubscribe('CAMERA_IMAGE_CAPTURED', self._handle_camera_message)
            self.message_receiver.unsubscribe('CAMERA_TRIGGER', self._handle_camera_message)
            logger.debug("Camera message subscriptions cleaned up")
    
    def _handle_camera_message(self, msg):
        """Handle incoming camera messages."""
        try:
            if msg.get_type() == 'CAMERA_IMAGE_CAPTURED':
                self._handle_image_captured(msg)
            elif msg.get_type() == 'CAMERA_TRIGGER':
                self._handle_camera_trigger(msg)
                
        except Exception as e:
            logger.error(f"Error handling camera message: {e}")
    
    def _handle_image_captured(self, msg):
        """Handle CAMERA_IMAGE_CAPTURED message."""
        photo_info = {
            'time_utc': msg.time_utc,
            'time_boot_ms': msg.time_boot_ms,
            'camera_id': msg.camera_id,
            'image_index': msg.image_index,
            'file_url': msg.file_url if hasattr(msg, 'file_url') else None,
            'latitude': msg.latitude if hasattr(msg, 'latitude') else None,
            'longitude': msg.longitude if hasattr(msg, 'longitude') else None,
            'altitude': msg.altitude if hasattr(msg, 'altitude') else None,
            'relative_alt': msg.relative_alt if hasattr(msg, 'relative_alt') else None,
            'captured_at': datetime.now().isoformat()
        }
        
        with self._photos_lock:
            self._captured_photos.append(photo_info)
        logger.info(f"Photo captured: {photo_info['image_index']} at {photo_info['captured_at']}")
        
        # Emit WebSocket event if socketio is available
        if self.socketio:
            self.socketio.emit('photo_captured', photo_info)
        
        # Attempt to download photo if URL is available
        if config.camera.ENABLE_PHOTO_DOWNLOAD and photo_info['file_url']:
            downloaded_path = self._download_photo(photo_info)
            if not downloaded_path:
                # Fallback: create a placeholder file if download fails
                self._create_placeholder_photo(photo_info)
        elif config.camera.ENABLE_PHOTO_DOWNLOAD:
            # Fallback: create a placeholder file if no URL provided
            self._create_placeholder_photo(photo_info)
    
    def _handle_camera_trigger(self, msg):
        """Handle CAMERA_TRIGGER message."""
        logger.debug(f"Camera triggered: seq={msg.seq}")
    
    def _download_photo(self, photo_info: Dict[str, Any]) -> Optional[Path]:
        """
        Download photo from camera via MAVLink FTP or HTTP.
        Parameters:
            photo_info: Photo information from CAMERA_IMAGE_CAPTURED message
        Returns:
            Path to downloaded file or None if download failed
        """
        if not photo_info.get('file_url'):
            logger.warning("No file URL available for photo download")
            return None
        
        try:
            # Generate local filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{config.camera.PHOTO_PREFIX}{timestamp}.{config.camera.PHOTO_FORMAT}"
            local_path = self._photo_storage_path / filename
            
            # Try MAVLink FTP download (if supported)
            if photo_info['file_url'].startswith('ftp://'):
                return self._download_via_ftp(photo_info['file_url'], local_path)
            
            # Try HTTP download (if supported)
            elif photo_info['file_url'].startswith('http://') or photo_info['file_url'].startswith('https://'):
                return self._download_via_http(photo_info['file_url'], local_path)
            
            else:
                logger.warning(f"Unsupported file URL scheme: {photo_info['file_url']}")
                return None
                
        except Exception as e:
            logger.error(f"Photo download failed: {e}")
            return None
    
    def _download_via_ftp(self, ftp_url: str, local_path: Path) -> Optional[Path]:
        """
        Download photo via MAVLink FTP.
        
        Parameters:
            ftp_url: FTP URL of the photo
            local_path: Local path to save the photo
            
        Returns:
            Path to downloaded file or None if download failed
        """
        try:
            # Parse FTP URL
            # Format: ftp://<component_id>/<path>
            url_parts = ftp_url.replace('ftp://', '').split('/', 1)
            if len(url_parts) < 2:
                logger.error(f"Invalid FTP URL: {ftp_url}")
                return None
            
            component_id = int(url_parts[0])
            remote_path = url_parts[1]
            
            # Use pymavlink's FTP functionality
            # Note: This requires the camera to support MAVLink FTP
            logger.info(f"Downloading via FTP: {remote_path}")
            
            # For now, return placeholder - full FTP implementation requires
            # additional pymavlink FTP client setup
            logger.warning("MAVLink FTP download not fully implemented yet")
            return None
            
        except Exception as e:
            logger.error(f"FTP download error: {e}")
            return None
    
    def _download_via_http(self, http_url: str, local_path: Path) -> Optional[Path]:
        """
        Download photo via HTTP.
        
        Parameters:
            http_url: HTTP URL of the photo
            local_path: Local path to save the photo
            
        Returns:
            Path to downloaded file or None if download failed
        """
        try:
            import requests
            
            logger.info(f"Downloading via HTTP: {http_url}")
            response = requests.get(http_url, timeout=config.camera.PHOTO_DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            
            # Save the photo
            local_path.write_bytes(response.content)
            logger.info(f"Photo saved to: {local_path}")
            
            return local_path
            
        except ImportError:
            logger.warning("requests library not available for HTTP download")
            return None
        except Exception as e:
            logger.error(f"HTTP download error: {e}")
            return None
    
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
            
            # In simulation mode, create a placeholder file
            if config.camera.SIMULATION_MODE:
                self._create_placeholder_photo()
            
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
    
    def get_captured_photos(self) -> List[Dict[str, Any]]:
        """
        Get list of all captured photos.
        Returns:
            List of photo information dictionaries
        """
        with self._photos_lock:
            return self._captured_photos.copy()
    
    def get_latest_photo(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recently captured photo.
        Returns:
            Latest photo information or None if no photos captured
        """
        with self._photos_lock:
            if self._captured_photos:
                return self._captured_photos[-1]
            return None
    
    def get_photo_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get photo information by image index.
        Parameters:
            index: Image index from camera
        Returns:
            Photo information dictionary or None if not found
        """
        with self._photos_lock:
            for photo in self._captured_photos:
                if photo['image_index'] == index:
                    return photo
            return None
    
    def clear_captured_photos(self):
        """Clear the list of captured photos."""
        with self._photos_lock:
            self._captured_photos.clear()
        logger.info("Captured photos list cleared")
    
    def get_photo_storage_path(self) -> Path:
        """
        Get the photo storage directory path.
        Returns:
            Path to photo storage directory
        """
        return self._photo_storage_path
    
    def _create_simple_jpeg(self, width: int, height: int, color: tuple) -> bytes:
        """
        Create a simple solid color JPEG without PIL.
        Parameters:
            width: Image width
            height: Image height  
            color: RGB color tuple
            
        Returns:
            JPEG bytes
        """
        # This is a minimal valid JPEG header with a solid color
        # For simplicity, we'll create a very basic JPEG structure
        r, g, b = color
        
        # Create a simple pattern - this is still minimal but better than 1x1
        # Using a basic uncompressed JPEG-like structure
        import struct
        
        # JPEG SOI marker
        jpeg_data = bytearray(b'\xff\xd8')
        
        # JFIF marker
        jpeg_data.extend(b'\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
        
        # Quantization table (simplified)
        jpeg_data.extend(b'\xff\xdb\x00\x43\x00')
        for i in range(64):
            jpeg_data.append(16)  # Simple quantization values
        
        # Huffman table (simplified)
        jpeg_data.extend(b'\xff\xc4\x00\x1f\x00')
        for i in range(16):
            jpeg_data.append(1)
        for i in range(12):
            jpeg_data.append(i)
            
        # Start of frame
        jpeg_data.extend(b'\xff\xc0\x00\x11\x08')
        jpeg_data.extend(struct.pack('>H', height))
        jpeg_data.extend(struct.pack('>H', width))
        jpeg_data.extend(b'\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01')
        
        # Start of scan
        jpeg_data.extend(b'\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00')
        
        # Simple image data (repeated pattern)
        # This creates a visible pattern instead of single pixel
        for y in range(height):
            for x in range(width):
                # Create a simple gradient pattern
                pixel_r = int(r * (x / width))
                pixel_g = int(g * (y / height))
                pixel_b = b
                jpeg_data.extend([pixel_r, pixel_g, pixel_b])
        
        # End of image
        jpeg_data.extend(b'\xff\xd9')
        
        return bytes(jpeg_data)
    
    def _create_placeholder_photo(self) -> Optional[Path]:
        """
        Create a placeholder photo file for simulation mode.
        Returns:
            Path to created placeholder file or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{config.camera.PHOTO_PREFIX}{timestamp}.{config.camera.PHOTO_FORMAT}"
            local_path = self._photo_storage_path / filename
            
            # Create a better placeholder image (100x100 pixel JPEG with visible pattern)
            # This creates a simple gradient pattern that's clearly visible
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                # Create a 100x100 image with a gradient
                img = Image.new('RGB', (100, 100), color='lightblue')
                pixels = img.load()
                
                # Create a simple gradient pattern
                for x in range(100):
                    for y in range(100):
                        r = int(255 * (x / 100))
                        g = int(255 * (y / 100))
                        b = 128
                        pixels[x, y] = (r, g, b)
                
                # Add text overlay
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("arial.ttf", 12)
                except:
                    font = ImageFont.load_default()
                draw.text((10, 40), "SIMULATION", fill='white', font=font)
                draw.text((25, 55), "PHOTO", fill='white', font=font)
                
                img.save(local_path, 'JPEG', quality=95)
                
            except ImportError:
                # Fallback to simple colored JPEG if PIL not available
                # Create a 100x100 solid color JPEG
                placeholder_data = self._create_simple_jpeg(100, 100, (100, 150, 200))
                local_path.write_bytes(placeholder_data)
            
            logger.info(f"Placeholder photo created: {local_path}")
            
            # Add to captured photos list with thread safety
            with self._photos_lock:
                photo_info = {
                    'time_utc': int(datetime.now().timestamp()),
                    'time_boot_ms': 0,
                    'camera_id': config.camera.CAMERA_SYSTEM_ID,
                    'image_index': len(self._captured_photos) + 1,
                    'file_url': None,
                    'latitude': None,
                    'longitude': None,
                    'altitude': None,
                    'relative_alt': None,
                    'captured_at': datetime.now().isoformat()
                }
                self._captured_photos.append(photo_info)
            
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to create placeholder photo: {e}")
            return None

    def shutdown(self):
        """ Shutting down camera """
        self._cleanup_message_subscriptions()

    def get_local_photos(self) -> List[Path]:
        """
        Get list of locally saved photo files.
        Returns:
            List of Path objects for saved photos
        """
        if not self._photo_storage_path.exists():
            return []
        
        photo_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        photos = []
        
        for file_path in self._photo_storage_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in photo_extensions:
                photos.append(file_path)
        
        return sorted(photos, key=lambda p: p.stat().st_mtime, reverse=True)
    
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
                f"recording={self._is_recording}, "
                f"photos_captured={len(self._captured_photos)})")
    
    def __del__(self):
        """Cleanup when camera instance is destroyed."""
        self._cleanup_message_subscriptions()


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
