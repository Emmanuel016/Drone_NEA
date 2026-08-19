"""
navigations.py
Provides navigation and waypoint mission capabilities for ArduPilot vehicles.
Author: Emmanuel Ugwu
Project: DroneNEA
"""

import logging
import time
from typing import List, Tuple, Optional
from pymavlink import mavutil
from drone.connection import Connection
from drone.control import Control
from drone.telemetry import Telemetry
from drone.config import config
import math
from math import radians, sin, cos, sqrt, asin

# Configure module-specific logger
logger = logging.getLogger(__name__)

class Waypoint:
    """Represents a single waypoint in a mission."""
    def __init__(self, latitude: float, longitude: float, altitude: float, 
                 hold_time: float = 0, acceptance_radius: float = 5,
                 camera_action: str = "none", camera_delay: float = 0):
        """
        Initialize a waypoint.        
        Parameters:
            latitude: float - Latitude in decimal degrees
            longitude: float - Longitude in decimal degrees  
            altitude: float - Altitude in meters
            hold_time: float - Time to hold at waypoint in seconds
            acceptance_radius: float - Radius in meters to consider waypoint reached
            camera_action: str - Camera action ("none", "photo", "video_start", "video_stop")
            camera_delay: float - Additional delay after camera action in seconds
        """
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.hold_time = hold_time
        self.acceptance_radius = acceptance_radius
        self.camera_action = camera_action
        self.camera_delay = camera_delay
        
    @classmethod
    def from_dict(cls, data):
        return cls(
                latitude=data["latitude"],
                longitude=data['longitude'],
            altitude=data['altitude'],
            hold_time=data.get('hold_time', 0),
            acceptance_radius=data.get('acceptance_radius', 5),
            camera_action=data.get('camera_action', 'none'),
            camera_delay=data.get('camera_delay', 0),
        )

    def to_dict(self) -> dict:
        """Convert waypoint to dictionary representation."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "hold_time": self.hold_time,
            "acceptance_radius": self.acceptance_radius,
            "camera_action": self.camera_action,
            "camera_delay": self.camera_delay
        }
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert waypoint to tuple representation (lat, lon, alt)."""
        return (self.latitude, self.longitude, self.altitude)
    
    def __repr__(self):
        return (f"Waypoint(lat={self.latitude:.7f}, lon={self.longitude:.7f}, "
                f"alt={self.altitude:.1f}m, hold={self.hold_time}s)")

class Navigation:
    """
    High-level navigation controller for waypoint missions and autonomous flight.
    """    
    def __init__(self, connection: Connection, control: Control, telemetry: Telemetry, camera=None):
        """
        Initialize navigation controller.
        
        Parameters:
            connection: Active MAVLink connection
            control: Control instance for flight commands
            telemetry: Telemetry instance for position data
            camera: Optional Camera instance for waypoint camera actions
        """
        self.connection = connection
        self.control = control
        self.telemetry = telemetry
        self.camera = camera
        self.master = connection.get_master()
        self.waypoints: List[Waypoint] = []
        self.current_waypoint_index = 0
        self.current_waypoint = None
        self.mission_running = False

    def _check_connection(self):
        """Ensure the vehicle is connected."""
        if not self.connection.is_connected():
            raise ConnectionError("Drone is not connected.")
    
    def add_waypoint(self, latitude: float, longitude: float, altitude: float,
                     hold_time: float = 0, acceptance_radius: float = 5,
                     camera_action: str = "none", camera_delay: float = 0):
        """
        Add a waypoint to the mission.
        
        Parameters:
            latitude: float - Latitude in decimal degrees
            longitude: float - Longitude in decimal degrees
            altitude: float - Altitude in meters
            hold_time: float - Time to hold at waypoint in seconds
            acceptance_radius: float - Radius in meters to consider waypoint reached
            camera_action: str - Camera action ("none", "photo", "video_start", "video_stop")
            camera_delay: float - Additional delay after camera action in seconds
        """
        waypoint = Waypoint(latitude, longitude, altitude, hold_time, acceptance_radius, 
                           camera_action, camera_delay)
        self.waypoints.append(waypoint)
        logger.info(f"Added waypoint {len(self.waypoints)}: {waypoint}")
        return waypoint
    
    def remove_waypoint(self, index: int):
        if 0 <= index < len(self.waypoints):
            waypoint = self.waypoints.pop(index)
            logger.info(f"Removed waypoint {index}: {waypoint}")
        else:
            raise IndexError("Waypoint out of range")

    def get_waypoint(self, index: int) -> Optional[Waypoint]:
        if 0 <= index < len(self.waypoints):
            return self.waypoints[index]
        return None #Perfectly acceptable
    
    def edit_waypoint(self, index: int, latitude: Optional[float] = None,
                      longitude: Optional[float] = None, altitude: Optional[float] = None,
                      hold_time: Optional[float] = None, acceptance_radius: Optional[float] = None,
                      camera_action: Optional[str] = None, camera_delay: Optional[float] = None):
        if 0 <= index < len(self.waypoints):
            waypoint = self.waypoints[index]
            if latitude is not None:
                waypoint.latitude = latitude
            if longitude is not None:
                waypoint.longitude = longitude
            if altitude is not None:
                waypoint.altitude = altitude
            if hold_time is not None:
                waypoint.hold_time = hold_time
            if acceptance_radius is not None:
                waypoint.acceptance_radius = acceptance_radius
            if camera_action is not None:
                waypoint.camera_action = camera_action
            if camera_delay is not None:
                waypoint.camera_delay = camera_delay
            logger.info(f"Edited waypoint {index}: {waypoint}")
        else:
            raise IndexError("Waypoint out of range")

    def number_of_waypoints(self) -> int:
        return len(self.waypoints)

    def clear_waypoints(self):
        """Clear all waypoints from the mission."""
        self.waypoints.clear()
        self.current_waypoint_index = 0
        self.current_waypoint = None
        logger.info("All waypoints cleared.")
    
    def get_distance_to_waypoint(self, waypoint: Waypoint) -> float:
        """
        Calculate distance from current position to waypoint.
        Parameters:
            waypoint: Waypoint - Target waypoint
        Returns:
            float - Distance in meters
        """
        position = self.telemetry.get_position()
        if position is None:
            return float('inf')
        
        current_lat, current_lon, _ = position
        
        # Haversine formula for distance calculation        
        lat1, lon1 = radians(current_lat), radians(current_lon)
        lat2, lon2 = radians(waypoint.latitude), radians(waypoint.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        earth_radius = config.navigation.EARTH_RADIUS
        return c * earth_radius
    
    def calculate_distance(self, wp1:Waypoint, wp2:Waypoint):
        '''Calculate the distance between two waypoints in meters.
           Args: wp1=First waypoint
                 wp2=Second waypoint
           Returns: float - distance in meters '''
        # Haversine formula for distance calculation
        lat1, lon1 = radians(wp1.latitude), radians(wp1.longitude)
        lat2, lon2 = radians(wp2.latitude), radians(wp2.longitude)

        distancelat = lat2 - lat1
        distancelon = lon2 - lon1
        a = sin(distancelat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(distancelon / 2) ** 2
        c = 2 * asin(sqrt(a))

        earth_radius = config.navigation.EARTH_RADIUS
        return c*earth_radius

    def fly_to_waypoint(self, waypoint: Waypoint, timeout: int = 120) -> bool:
        """
        Fly the drone to a specified waypoint using MAVLink SET_POSITION_TARGET_GLOBAL_INT.

        Parameters:
            waypoint (Waypoint): Target waypoint with latitude, longitude, altitude.
            timeout (int): Time in seconds to wait for arrival confirmation.

        Returns:
            bool: True if waypoint reached within timeout, False otherwise.
        """
        self._check_connection()
        logger.info(f"Flying to waypoint: {waypoint}")
        
        # Set mode to GUIDED for waypoint navigation
        self.control.set_mode("GUIDED")
        
        # Send position target command
        self.master.mav.set_position_target_global_int_send(
            0,  # time_boot_ms
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            0b0000111111111000,  # type_mask (only position enabled)
            int(waypoint.latitude * 1e7),
            int(waypoint.longitude * 1e7),
            waypoint.altitude,
            0, 0, 0,  # velocity x, y, z
            0, 0, 0,  # acceleration x, y, z
            0, 0      # yaw, yaw_rate
        )
        
        # Wait for waypoint to be reached
        start_time = time.time()
        while time.time() - start_time < timeout:
            msg = self.master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=1)
            distance = self.get_distance_to_waypoint(waypoint)
            logger.debug(f"Distance to waypoint: {distance:.1f}m")
            
            if msg:
                # Check if waypoint reached using acceptance radius
                if distance <= waypoint.acceptance_radius:
                    logger.info(f"Waypoint reached: {waypoint}")
                    
                    # Execute camera action if specified
                    if self.camera and waypoint.camera_action != "none":
                        self._execute_camera_action(waypoint.camera_action)
                    
                    # Hold at waypoint if specified
                    if waypoint.hold_time > 0:
                        logger.info(f"Holding for {waypoint.hold_time} seconds...")
                        time.sleep(waypoint.hold_time)
                    
                    # Additional camera delay if specified
                    if waypoint.camera_delay > 0:
                        logger.info(f"Camera delay: {waypoint.camera_delay} seconds...")
                        time.sleep(waypoint.camera_delay)
                    
                    return True
        
        logger.warning(f"Timeout: waypoint {waypoint} not reached within {timeout} seconds")
        return False
    
    def _execute_camera_action(self, action: str):
        """
        Execute camera action at waypoint.
        
        Parameters:
            action: str - Camera action ("photo", "video_start", "video_stop")
        """
        if not self.camera:
            logger.warning("Camera not available for waypoint action")
            return
        
        logger.info(f"Executing camera action: {action}")
        
        try:
            if action == "photo":
                self.camera.take_photo()
            elif action == "video_start":
                self.camera.start_video()
            elif action == "video_stop":
                self.camera.stop_video()
            else:
                logger.warning(f"Unknown camera action: {action}")
        except Exception as e:
            logger.error(f"Camera action failed: {e}")
    
    def abort_mission(self):
        self.mission_running = False

    def execute_mission(self, timeout_per_waypoint: int = 120) -> bool:
        """
        Execute the complete waypoint mission.
        Parameters: timeout_per_waypoint: int - Maximum time per waypoint in seconds
        Returns: bool - True if all waypoints completed, False if any failed
        """
        if not self.waypoints:
            logger.warning("No waypoints in mission.")
            return False
        
        self.mission_running = True
        try:
            self._check_connection()
            logger.info(f"Starting mission with {len(self.waypoints)} waypoints")
        
            self.current_waypoint_index = 0
            for i, waypoint in enumerate(self.waypoints):
                self.current_waypoint_index = i
                self.current_waypoint = waypoint
                logger.info(f"Waypoint {i+1}/{len(self.waypoints)}")
            
                if not self.fly_to_waypoint(waypoint, timeout_per_waypoint):
                    logger.error(f"Mission failed at waypoint {i+1}")
                    self.control.rtl()  # Return to launch on failure
                    self.mission_running = False
                    raise RuntimeError(f"Waypoint {i+1} failed")
        except RuntimeError as e:
            logger.error(e)
            self.control.rtl()
            return False        
        finally:
            self.mission_running = False
        self.current_waypoint = None
        logger.info("Mission completed successfully!")
        return True
    
    def fly_rectangle_pattern(self, center_lat: float, center_lon: float, 
                              altitude: float, width: float, length: float,
                              heading: float = 0) -> bool:
        """
        Fly a rectangular pattern around a center point.
        Parameters:
            center_lat: float - Center latitude
            center_lon: float - Center longitude
            altitude: float - Flight altitude in meters
            width: float - Rectangle width in meters
            length: float - Rectangle length in meters
            heading: float - Heading of rectangle in degrees
        Returns:
            bool - True if pattern completed
        """
        logger.info(f"Starting rectangle pattern at {altitude}m altitude")
        
        # Calculate corner points based on heading
        heading_rad = math.radians(heading)
        
        def offset_point(lat, lon, dx, dy):
            # Convert meters to degrees (approximate)
            lat_offset = dx / config.navigation.METERS_PER_DEGREE  # meters per degree latitude
            lon_offset = dy / (config.navigation.METERS_PER_DEGREE * math.cos(math.radians(lat)))
            return lat + lat_offset, lon + lon_offset
        
        # Calculate corners relative to center (5 points to complete the rectangle)
        corners = [
            (-length/2, -width/2),  # Bottom-left (start)
            (length/2, -width/2),   # Bottom-right
            (length/2, width/2),    # Top-right
            (-length/2, width/2),   # Top-left
            (-length/2, -width/2),  # Bottom-left (return to start)
        ]
        
        # Rotate corners by heading and add to center
        first_point = None
        for i, (dx, dy) in enumerate(corners):
            rotated_dx = dx * math.cos(heading_rad) - dy * math.sin(heading_rad)
            rotated_dy = dx * math.sin(heading_rad) + dy * math.cos(heading_rad)
            lat, lon = offset_point(center_lat, center_lon, rotated_dx, rotated_dy)
            
            # Store first point
            if i == 0:
                first_point = (lat, lon)
            self.add_waypoint(lat, lon, altitude)
        
        logger.info("Added return waypoint to complete full rectangle")
        
        # Execute the pattern
        result = self.execute_mission()
        if result:
            self.clear_waypoints()
        return result
    
    def fly_circular_pattern(self, center_lat: float, center_lon: float,
                             altitude: float, radius: float, 
                             num_points: int = 8) -> bool:
        """
        Fly a circular pattern around a center point.
        Parameters:
            center_lat: float - Center latitude
            center_lon: float - Center longitude
            altitude: float - Flight altitude in meters
            radius: float - Circle radius in meters
            num_points: int - Number of waypoints in circle
            
        Returns:
            bool - True if pattern completed
        """
        logger.info(f"Starting circular pattern at {altitude}m altitude, radius {radius}m")
        
        # Store first point to close the circle
        first_lat, first_lon = None, None
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            
            # Calculate offset in meters
            dx = radius * math.cos(angle)
            dy = radius * math.sin(angle)
            
            # Convert to degrees
            lat_offset = dx / config.navigation.METERS_PER_DEGREE
            lon_offset = dy / (config.navigation.METERS_PER_DEGREE * math.cos(math.radians(center_lat)))
            
            lat = center_lat + lat_offset
            lon = center_lon + lon_offset
            
            # Store first point
            if i == 0:
                first_lat, first_lon = lat, lon
            self.add_waypoint(lat, lon, altitude)
        
        # Add first point again to complete the full circle
        if first_lat is not None and first_lon is not None:
            self.add_waypoint(first_lat, first_lon, altitude)
            logger.info("Added return waypoint to complete full circle")
        
        # Execute the pattern
        result = self.execute_mission()
        if result:
            self.clear_waypoints()
        return result
    
    def return_to_home(self) -> bool:
        """
        Return to the launch point and land.
        Returns:
            bool - True if successful
        """
        logger.info("Returning to home...")
        self.control.rtl()
        return True
    
    def __repr__(self):
      return (
        f"Navigation("
        f"waypoints={len(self.waypoints)}, "
        f"current={self.current_waypoint_index}, "
        f"mission_running={self.mission_running})"
      )

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
        navigation = Navigation(connection, control, telemetry)
        
        # Example: Fly a rectangular pattern
        # navigation.fly_rectangle_pattern(
        #     center_lat=47.397742,
        #     center_lon=8.545594,
        #     altitude=20,
        #     width=50,
        #     length=100,
        #     heading=0
        # )
        
        # Example: Custom waypoint mission
        # navigation.add_waypoint(47.397742, 8.545594, 20, hold_time=5)
        # navigation.add_waypoint(47.398000, 8.545800, 25)
        # navigation.add_waypoint(47.397500, 8.546000, 20)
        # navigation.execute_mission()
        
    except Exception as error:
        logger.error(error)
    finally:
        connection.disconnect()
