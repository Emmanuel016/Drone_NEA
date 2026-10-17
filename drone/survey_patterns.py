"""
survey_patterns.py
Provides advanced survey and mapping flight patterns for ArduPilot vehicles.
Includes lawnmower/grid survey, spiral search, and mapping flight patterns with automatic photo triggering.
Author: Emmanuel Ugwu
Project: DroneNEA
"""

import logging
import math
from typing import List, Tuple, Optional, Dict, Any
from drone.navigations import Waypoint, Navigation
from drone.config import config

logger = logging.getLogger(__name__)


class SurveyPattern:
    """Base class for survey patterns."""
    
    def __init__(self, navigation: Navigation):
        """
        Initialize survey pattern controller.
        
        Parameters:
            navigation: Navigation - Navigation system instance
        """
        self.navigation = navigation
        self.pattern_type = "base"
    
    def _offset_point(self, lat: float, lon: float, dx: float, dy: float) -> Tuple[float, float]:
        """
        Convert meter offsets to latitude/longitude.
        
        Parameters:
            lat: float - Starting latitude
            lon: float - Starting longitude
            dx: float - East offset in meters
            dy: float - North offset in meters
            
        Returns:
            Tuple[float, float] - New (latitude, longitude)
        """
        lat_offset = dy / config.navigation.METERS_PER_DEGREE
        lon_offset = dx / (config.navigation.METERS_PER_DEGREE * math.cos(math.radians(lat)))
        return lat + lat_offset, lon + lon_offset
    
    def generate_waypoints(self) -> List[Waypoint]:
        """Generate waypoints for the pattern. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement generate_waypoints()")
    
    def execute_pattern(self, timeout_per_waypoint: int = 120) -> bool:
        """
        Execute the survey pattern.
        
        Parameters:
            timeout_per_waypoint: int - Maximum time per waypoint in seconds
            
        Returns:
            bool - True if pattern completed successfully
        """
        waypoints = self.generate_waypoints()
        
        if not waypoints:
            logger.warning(f"No waypoints generated for {self.pattern_type} pattern")
            return False
        
        logger.info(f"Executing {self.pattern_type} pattern with {len(waypoints)} waypoints")
        
        # Clear existing waypoints and add new ones
        self.navigation.clear_waypoints()
        for wp in waypoints:
            self.navigation.waypoints.append(wp)
        
        # Execute the mission
        return self.navigation.execute_mission(timeout_per_waypoint)


class LawnmowerPattern(SurveyPattern):
    """
    Lawnmower (grid) survey pattern for area coverage.
    Ideal for mapping, inspection, and search operations.
    """
    
    def __init__(self, navigation: Navigation):
        super().__init__(navigation)
        self.pattern_type = "lawnmower"
    
    def generate_waypoints(
        self,
        center_lat: float,
        center_lon: float,
        altitude: float,
        area_width: float,
        area_length: float,
        spacing: float = 20,
        heading: float = 0,
        photo_interval: float = 0,
        hold_time: float = 0
    ) -> List[Waypoint]:
        """
        Generate waypoints for lawnmower pattern.
        
        Parameters:
            center_lat: float - Center latitude of survey area
            center_lon: float - Center longitude of survey area
            altitude: float - Flight altitude in meters
            area_width: float - Width of survey area in meters (perpendicular to flight direction)
            area_length: float - Length of survey area in meters (flight direction)
            spacing: float - Distance between parallel lines in meters
            heading: float - Heading of survey area in degrees (0 = North)
            photo_interval: float - Take photo every X meters (0 = no photos)
            hold_time: float - Hold time at each waypoint in seconds
            
        Returns:
            List[Waypoint] - List of waypoints for the pattern
        """
        logger.info(f"Generating lawnmower pattern: {area_width}x{area_length}m, spacing {spacing}m")
        
        waypoints = []
        heading_rad = math.radians(heading)
        
        # Calculate number of lines needed
        num_lines = int(math.ceil(area_width / spacing)) + 1
        
        # Calculate start position (bottom-left of area)
        start_lat, start_lon = self._offset_point(
            center_lat, center_lon,
            -area_length / 2,
            -area_width / 2
        )
        
        # Generate waypoints for each line
        for i in range(num_lines):
            # Calculate offset for this line
            line_offset = i * spacing
            if line_offset > area_width:
                line_offset = area_width
            
            # Rotate offset by heading
            rotated_dx = 0
            rotated_dy = line_offset
            
            if heading != 0:
                rotated_dx = line_offset * math.sin(heading_rad)
                rotated_dy = line_offset * math.cos(heading_rad)
            
            # Calculate line start and end points
            line_start_lat, line_start_lon = self._offset_point(
                start_lat, start_lon,
                rotated_dx,
                rotated_dy
            )
            
            line_end_lat, line_end_lon = self._offset_point(
                line_start_lat, line_start_lon,
                area_length * math.cos(heading_rad),
                area_length * math.sin(heading_rad)
            )
            
            # Add waypoints for this line (alternating direction)
            if i % 2 == 0:
                # Even lines: left to right
                line_waypoints = self._generate_line_waypoints(
                    line_start_lat, line_start_lon,
                    line_end_lat, line_end_lon,
                    altitude, photo_interval, hold_time
                )
            else:
                # Odd lines: right to left
                line_waypoints = self._generate_line_waypoints(
                    line_end_lat, line_end_lon,
                    line_start_lat, line_start_lon,
                    altitude, photo_interval, hold_time
                )
            
            waypoints.extend(line_waypoints)
        
        logger.info(f"Generated {len(waypoints)} waypoints for lawnmower pattern")
        return waypoints
    
    def _generate_line_waypoints(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        altitude: float,
        photo_interval: float,
        hold_time: float
    ) -> List[Waypoint]:
        """Generate waypoints along a single line."""
        waypoints = []
        
        # Calculate line length
        distance = self.navigation.calculate_distance(
            Waypoint(start_lat, start_lon, altitude),
            Waypoint(end_lat, end_lon, altitude)
        )
        
        if photo_interval > 0:
            # Generate waypoints at photo intervals
            num_points = int(math.ceil(distance / photo_interval)) + 1
            for i in range(num_points):
                fraction = i / (num_points - 1) if num_points > 1 else 0
                lat = start_lat + (end_lat - start_lat) * fraction
                lon = start_lon + (end_lon - start_lon) * fraction
                
                camera_action = "photo" if i > 0 and i < num_points - 1 else "none"
                waypoints.append(Waypoint(
                    lat, lon, altitude,
                    hold_time=hold_time,
                    camera_action=camera_action,
                    camera_delay=1.0 if camera_action == "photo" else 0
                ))
        else:
            # Just start and end points
            waypoints.append(Waypoint(start_lat, start_lon, altitude, hold_time=hold_time))
            waypoints.append(Waypoint(end_lat, end_lon, altitude, hold_time=hold_time))
        
        return waypoints


class SpiralPattern(SurveyPattern):
    """
    Spiral search pattern for target location.
    Expands outward from center point in spiral pattern.
    """
    
    def __init__(self, navigation: Navigation):
        super().__init__(navigation)
        self.pattern_type = "spiral"
    
    def generate_waypoints(
        self,
        center_lat: float,
        center_lon: float,
        altitude: float,
        max_radius: float,
        spacing: float = 15,
        revolutions: int = 3,
        photo_interval: float = 0,
        hold_time: float = 0
    ) -> List[Waypoint]:
        """
        Generate waypoints for spiral search pattern.
        
        Parameters:
            center_lat: float - Center latitude
            center_lon: float - Center longitude
            altitude: float - Flight altitude in meters
            max_radius: float - Maximum radius of spiral in meters
            spacing: float - Distance between spiral arms in meters
            revolutions: int - Number of complete revolutions
            photo_interval: float - Take photo every X degrees (0 = no photos)
            hold_time: float - Hold time at each waypoint in seconds
            
        Returns:
            List[Waypoint] - List of waypoints for the pattern
        """
        logger.info(f"Generating spiral pattern: max radius {max_radius}m, {revolutions} revolutions")
        
        waypoints = []
        
        # Calculate total angle and step size
        total_angle = 2 * math.pi * revolutions
        num_points = int(math.ceil(max_radius / spacing * 2 * math.pi * revolutions))
        angle_step = total_angle / num_points if num_points > 0 else 0.1
        
        # Start at center
        waypoints.append(Waypoint(center_lat, center_lon, altitude, hold_time=hold_time))
        
        # Generate spiral points
        for i in range(num_points):
            angle = i * angle_step
            radius = (i / num_points) * max_radius
            
            # Calculate position
            dx = radius * math.cos(angle)
            dy = radius * math.sin(angle)
            
            lat, lon = self._offset_point(center_lat, center_lon, dx, dy)
            
            # Determine camera action
            camera_action = "none"
            if photo_interval > 0 and i % int(photo_interval) == 0:
                camera_action = "photo"
            
            waypoints.append(Waypoint(
                lat, lon, altitude,
                hold_time=hold_time,
                camera_action=camera_action,
                camera_delay=1.0 if camera_action == "photo" else 0
            ))
        
        logger.info(f"Generated {len(waypoints)} waypoints for spiral pattern")
        return waypoints


class MappingPattern(SurveyPattern):
    """
    Mapping flight pattern with automatic photo triggering.
    Optimized for aerial photography and photogrammetry.
    """
    
    def __init__(self, navigation: Navigation):
        super().__init__(navigation)
        self.pattern_type = "mapping"
    
    def generate_waypoints(
        self,
        center_lat: float,
        center_lon: float,
        altitude: float,
        area_width: float,
        area_length: float,
        overlap_x: float = 70,
        overlap_y: float = 70,
        camera_fov: float = 90,
        heading: float = 0
    ) -> List[Waypoint]:
        """
        Generate waypoints for mapping pattern with calculated photo intervals.
        
        Parameters:
            center_lat: float - Center latitude of mapping area
            center_lon: float - Center longitude of mapping area
            altitude: float - Flight altitude in meters
            area_width: float - Width of mapping area in meters
            area_length: float - Length of mapping area in meters
            overlap_x: float - Forward overlap percentage (recommended 60-80%)
            overlap_y: float - Side overlap percentage (recommended 60-80%)
            camera_fov: float - Camera field of view in degrees
            heading: float - Heading of mapping area in degrees (0 = North)
            
        Returns:
            List[Waypoint] - List of waypoints with automatic photo actions
        """
        logger.info(f"Generating mapping pattern: {area_width}x{area_length}m at {altitude}m altitude")
        
        # Calculate ground sample distance and spacing
        # Ground coverage at altitude = 2 * altitude * tan(FOV/2)
        ground_coverage = 2 * altitude * math.tan(math.radians(camera_fov / 2))
        
        # Calculate spacing based on overlap requirements
        spacing_x = ground_coverage * (1 - overlap_x / 100)
        spacing_y = ground_coverage * (1 - overlap_y / 100)
        
        logger.info(f"Ground coverage: {ground_coverage:.1f}m, Spacing X: {spacing_x:.1f}m, Spacing Y: {spacing_y:.1f}m")
        
        # Use lawnmower pattern with calculated spacing
        lawnmower = LawnmowerPattern(self.navigation)
        waypoints = lawnmower.generate_waypoints(
            center_lat=center_lat,
            center_lon=center_lon,
            altitude=altitude,
            area_width=area_width,
            area_length=area_length,
            spacing=spacing_y,
            heading=heading,
            photo_interval=spacing_x,
            hold_time=0.5  # Short hold for photo capture
        )
        
        # Update camera actions for mapping (photos at all waypoints except turns)
        for i, wp in enumerate(waypoints):
            if i % 2 == 0 or i == len(waypoints) - 1:
                # These are turn points or final point - no photo
                wp.camera_action = "none"
                wp.camera_delay = 0
            else:
                # Regular waypoints - take photo
                wp.camera_action = "photo"
                wp.camera_delay = 1.0
        
        logger.info(f"Generated {len(waypoints)} waypoints for mapping pattern")
        return waypoints


class SurveyPatterns:
    """
    Main controller for all survey patterns.
    Provides unified interface for different survey types.
    """
    
    def __init__(self, navigation: Navigation):
        """
        Initialize survey patterns controller.
        
        Parameters:
            navigation: Navigation - Navigation system instance
        """
        self.navigation = navigation
        self.current_pattern = None
    
    def fly_lawnmower(
        self,
        center_lat: float,
        center_lon: float,
        altitude: float,
        area_width: float,
        area_length: float,
        spacing: float = 20,
        heading: float = 0,
        photo_interval: float = 0,
        hold_time: float = 0,
        timeout_per_waypoint: int = 120
    ) -> bool:
        """
        Execute lawnmower survey pattern.
        
        Parameters:
            center_lat: float - Center latitude
            center_lon: float - Center longitude
            altitude: float - Flight altitude in meters
            area_width: float - Width of survey area in meters
            area_length: float - Length of survey area in meters
            spacing: float - Distance between parallel lines in meters
            heading: float - Heading in degrees
            photo_interval: float - Take photo every X meters
            hold_time: float - Hold time at waypoints in seconds
            timeout_per_waypoint: int - Timeout per waypoint in seconds
            
        Returns:
            bool - True if pattern completed successfully
        """
        pattern = LawnmowerPattern(self.navigation)
        self.current_pattern = pattern
        
        waypoints = pattern.generate_waypoints(
            center_lat, center_lon, altitude,
            area_width, area_length, spacing, heading,
            photo_interval, hold_time
        )
        
        if not waypoints:
            return False
        
        self.navigation.clear_waypoints()
        for wp in waypoints:
            self.navigation.waypoints.append(wp)
        
        return self.navigation.execute_mission(timeout_per_waypoint)
    
    def fly_spiral(
        self,
        center_lat: float,
        center_lon: float,
        altitude: float,
        max_radius: float,
        spacing: float = 15,
        revolutions: int = 3,
        photo_interval: float = 0,
        hold_time: float = 0,
        timeout_per_waypoint: int = 120
    ) -> bool:
        """
        Execute spiral search pattern.
        
        Parameters:
            center_lat: float - Center latitude
            center_lon: float - Center longitude
            altitude: float - Flight altitude in meters
            max_radius: float - Maximum radius in meters
            spacing: float - Distance between spiral arms in meters
            revolutions: int - Number of revolutions
            photo_interval: float - Take photo every X degrees
            hold_time: float - Hold time at waypoints in seconds
            timeout_per_waypoint: int - Timeout per waypoint in seconds
            
        Returns:
            bool - True if pattern completed successfully
        """
        pattern = SpiralPattern(self.navigation)
        self.current_pattern = pattern
        
        waypoints = pattern.generate_waypoints(
            center_lat, center_lon, altitude,
            max_radius, spacing, revolutions,
            photo_interval, hold_time
        )
        
        if not waypoints:
            return False
        
        self.navigation.clear_waypoints()
        for wp in waypoints:
            self.navigation.waypoints.append(wp)
        
        return self.navigation.execute_mission(timeout_per_waypoint)
    
    def fly_mapping(
        self,
        center_lat: float,
        center_lon: float,
        altitude: float,
        area_width: float,
        area_length: float,
        overlap_x: float = 70,
        overlap_y: float = 70,
        camera_fov: float = 90,
        heading: float = 0,
        timeout_per_waypoint: int = 120
    ) -> bool:
        """
        Execute mapping flight pattern with automatic photo triggering.
        
        Parameters:
            center_lat: float - Center latitude
            center_lon: float - Center longitude
            altitude: float - Flight altitude in meters
            area_width: float - Width of mapping area in meters
            area_length: float - Length of mapping area in meters
            overlap_x: float - Forward overlap percentage
            overlap_y: float - Side overlap percentage
            camera_fov: float - Camera field of view in degrees
            heading: float - Heading in degrees
            timeout_per_waypoint: int - Timeout per waypoint in seconds
            
        Returns:
            bool - True if pattern completed successfully
        """
        pattern = MappingPattern(self.navigation)
        self.current_pattern = pattern
        
        waypoints = pattern.generate_waypoints(
            center_lat, center_lon, altitude,
            area_width, area_length,
            overlap_x, overlap_y, camera_fov, heading
        )
        
        if not waypoints:
            return False
        
        self.navigation.clear_waypoints()
        for wp in waypoints:
            self.navigation.waypoints.append(wp)
        
        return self.navigation.execute_mission(timeout_per_waypoint)
    
    def abort_pattern(self):
        """Abort the current survey pattern."""
        if self.navigation.mission_running:
            self.navigation.abort_mission()
            logger.info("Survey pattern aborted")


# Standalone test
if __name__ == "__main__":
    from drone.connection import Connection
    from drone.control import Control
    from drone.telemetry import Telemetry
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    # Test with mock navigation
    class MockNavigation:
        def __init__(self):
            self.waypoints = []
            self.mission_running = False
        
        def clear_waypoints(self):
            self.waypoints.clear()
        
        def calculate_distance(self, wp1, wp2):
            return math.sqrt(
                (wp1.latitude - wp2.latitude)**2 +
                (wp1.longitude - wp2.longitude)**2
            ) * 111319.9  # Approximate
    
    mock_nav = MockNavigation()
    survey = SurveyPatterns(mock_nav)
    
    # Test lawnmower pattern generation
    print("Testing lawnmower pattern generation...")
    pattern = LawnmowerPattern(mock_nav)
    waypoints = pattern.generate_waypoints(
        center_lat=-35.363262,
        center_lon=149.165237,
        altitude=30,
        area_width=100,
        area_length=150,
        spacing=20,
        heading=0,
        photo_interval=30
    )
    print(f"Generated {len(waypoints)} waypoints for lawnmower pattern")
    
    # Test spiral pattern generation
    print("\nTesting spiral pattern generation...")
    pattern = SpiralPattern(mock_nav)
    waypoints = pattern.generate_waypoints(
        center_lat=-35.363262,
        center_lon=149.165237,
        altitude=30,
        max_radius=100,
        spacing=15,
        revolutions=3,
        photo_interval=5
    )
    print(f"Generated {len(waypoints)} waypoints for spiral pattern")
    
    # Test mapping pattern generation
    print("\nTesting mapping pattern generation...")
    pattern = MappingPattern(mock_nav)
    waypoints = pattern.generate_waypoints(
        center_lat=-35.363262,
        center_lon=149.165237,
        altitude=50,
        area_width=100,
        area_length=150,
        overlap_x=70,
        overlap_y=70,
        camera_fov=90,
        heading=0
    )
    print(f"Generated {len(waypoints)} waypoints for mapping pattern")
    
    print("\nSurvey patterns module tests completed!")
