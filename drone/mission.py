"""
Mission Planner Module

This module provides functionality for planning, loading, saving, and validating
drone missions. It integrates with the Navigation system to manage waypoint-based
flight operations.
"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from drone.navigations import Waypoint, Navigation
from drone.config import config

# Configure module-specific logger
logger = logging.getLogger(__name__)

class MissionPlanner:
    """
    Mission Planner for managing drone flight missions.    
    Handles loading, saving, validating, and managing waypoint missions.
    """
    def __init__(self, navigation: Navigation):
        """
        Initialize the Mission Planner.
        Parameters: navigation: Navigation - Navigation system instance
        """
        self.navigation = navigation
        self.mission_dir = config.logging.MISSION_DIR
        self.mission_dir.mkdir(exist_ok=True)
        self.current_mission_file: Optional[Path] = None
    
    def create_mission_from_dict(self, mission_data: Dict[str, Any]) -> bool:
        """
        Create a mission from a dictionary.
        Parameters:
            mission_data: Dict - Mission data containing waypoints and metadata
        Returns:
            bool - True if mission created successfully, False otherwise
        """
        try:
            # Clear existing waypoints
            self.navigation.clear_waypoints()
            # Validate mission data structure
            if 'waypoints' not in mission_data:
                logger.error("Mission data missing 'waypoints' key")
                return False

            # Add waypoints from mission data
            for wp_data in mission_data["waypoints"]:
                wp = Waypoint.from_dict(wp_data)
                self.navigation.waypoints.append(wp)
    
            
            logger.info(f"Mission created with {len(mission_data['waypoints'])} waypoints")
            return True
            
        except (KeyError, TypeError) as e:
            logger.error(f"Invalid mission data format: {e}")
            return False
    
    def load_mission(self, filename: str) -> bool:
        """
        Load a mission from a JSON file.
        Parameters: filename: str - Name of the mission file (without extension)
        Returns: bool - True if mission loaded successfully, False otherwise
        """
        mission_file = self.mission_dir / f"{filename}.json"
        
        if not mission_file.exists():
            logger.error(f"Mission file not found: {mission_file}")
            return False
        
        try:
            with open(mission_file, 'r') as f:
                mission_data = json.load(f)
            
            success = self.create_mission_from_dict(mission_data)
            if success:
                self.current_mission_file = mission_file
                logger.info(f"Mission loaded from: {mission_file}") 
            return success
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in mission file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading mission: {e}")
            return False
    
    def save_mission(self, filename: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save the current mission to a JSON file.
        Parameters:
            filename: str - Name for the mission file (without extension)
            metadata: Optional[Dict] - Additional mission metadata
        Returns:
            bool - True if mission saved successfully, False otherwise
        """
        if not self.navigation.waypoints:
            logger.warning("No waypoints to save")
            return False
        
        mission_file = self.mission_dir / f"{filename}.json"
        
        try:
            # Convert waypoints to dictionary format
            waypoints_data = []
            for waypoint in self.navigation.waypoints:
                waypoints_data.append(waypoint.to_dict())
            
            # Create mission data structure
            mission_data = {
                'name': filename,
                'created': datetime.now().isoformat(),
                'waypoints': waypoints_data,
                'total_waypoints': len(waypoints_data)
            }
            
            # Add metadata if provided
            if metadata:
                mission_data['metadata'] = metadata
            
            # Save to file
            with open(mission_file, 'w') as f:
                json.dump(mission_data, f, indent=2)
            
            self.current_mission_file = mission_file
            logger.info(f"Mission saved to: {mission_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving mission: {e}")
            return False
    
    def list_missions(self) -> List[str]:
        """
        List all available mission files.
        Returns: List[str] - List of mission filenames (without extension)
        """
        missions = []
        for file in self.mission_dir.glob("*.json"):
            missions.append(file.stem)
        return sorted(missions)
    
    def delete_mission(self, filename: str) -> bool:
        """
        Delete a mission file.
        Parameters:
            filename: str - Name of the mission file (without extension)
        Returns:
            bool - True if mission deleted successfully, False otherwise
        """
        mission_file = self.mission_dir / f"{filename}.json"
        
        if not mission_file.exists():
            logger.error(f"Mission file not found: {mission_file}")
            return False
        
        try:
            mission_file.unlink()
            logger.info(f"Mission deleted: {mission_file}")
            
            # Clear current mission file reference if it was the deleted one
            if self.current_mission_file == mission_file:
                self.current_mission_file = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting mission: {e}")
            return False
    
    def validate_mission(self) -> Dict[str, Any]:
        """
        Validate the current mission configuration.
        
        Returns:
            Dict - Validation results containing 'valid' (bool) and 'errors' (List[str])
        """
        errors = []
        warning = []

        # Check if waypoints exist
        if not self.navigation.waypoints:
            errors.append("No waypoints in mission")
        
        # Validate each waypoint
        for i, waypoint in enumerate(self.navigation.waypoints):
            # Check latitude range
            if not -90 <= waypoint.latitude <= 90:
                errors.append(f"Waypoint {i+1}: Invalid latitude {waypoint.latitude}")
            
            # Check longitude range
            if not -180 <= waypoint.longitude <= 180:
                errors.append(f"Waypoint {i+1}: Invalid longitude {waypoint.longitude}")
            
            # Check altitude range (assuming reasonable limits)
            if waypoint.altitude < 0 or waypoint.altitude > 500:
                warning.append(f"Waypoint {i+1}: Invalid altitude {waypoint.altitude}")
            
            # Check hold time
            if waypoint.hold_time < 0:
                errors.append(f"Waypoint {i+1}: Negative hold time")
            
            # Check acceptance radius
            if waypoint.acceptance_radius <= 0:
                errors.append(f"Waypoint {i+1}: Invalid acceptance radius")
            
            # Check camera action
            valid_camera_actions = ["none", "photo", "video_start", "video_stop"]
            if waypoint.camera_action not in valid_camera_actions:
                errors.append(f"Waypoint {i+1}: Invalid camera action '{waypoint.camera_action}'")
            
            # Check camera delay
            if waypoint.camera_delay < 0:
                errors.append(f"Waypoint {i+1}: Negative camera delay")
        
        # Check for consecutive waypoints that are too close
        for i in range(len(self.navigation.waypoints) - 1):
            wp1 = self.navigation.waypoints[i]
            wp2 = self.navigation.waypoints[i + 1]
            distance = self.navigation.calculate_distance(wp1,wp2)
            
            if distance < 2:  # Less than 2 meters between waypoints
                errors.append(f"Waypoints {i+1} and {i+2} are too close ({distance:.1f}m)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warning': warning,
            'waypoint_count': len(self.navigation.waypoints)
        }
    
    def get_mission_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current mission.
        Returns:
            Dict - Mission summary information
        """
        if not self.navigation.waypoints:
            return {
                'waypoint_count': 0,
                'total_distance': 0,
                'min_altitude': 0,
                'max_altitude': 0,
                'estimated_time': 0
            }
        
        # Calculate mission statistics
        total_distance = 0
        min_altitude = float('inf')
        max_altitude = float('-inf')
        
        for i, waypoint in enumerate(self.navigation.waypoints):
            # Track altitude range
            min_altitude = min(min_altitude, waypoint.altitude)
            max_altitude = max(max_altitude, waypoint.altitude)
            
            # Calculate distance between consecutive waypoints
            if i > 0:
                previous = self.navigation.waypoints[i-1]
                total_distance += self.navigation.calculate_distance(previous, waypoint)
        
        # Estimate flight time (assuming 5 m/s average speed)
        estimated_time = total_distance / 5  # seconds
        
        return {
            'waypoint_count': len(self.navigation.waypoints),
            'total_distance': round(total_distance, 1),
            'min_altitude': round(min_altitude, 1) if min_altitude != float('inf') else 0,
            'max_altitude': round(max_altitude, 1) if max_altitude != float('-inf') else 0,
            'estimated_time': round(estimated_time, 1),
            'current_file': self.current_mission_file.name if self.current_mission_file else None
        }
    
    def export_mission_to_csv(self, filename: str) -> bool:
        """
        Export the current mission to a CSV file.
        Parameters:
            filename: str - Name for the CSV file (without extension)
        Returns:
            bool - True if export successful, False otherwise
        """
        
        csv_file = self.mission_dir / f"{filename}.csv"
        
        if not self.navigation.waypoints:
            logger.warning("No waypoints to export")
            return False
        try:
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Waypoint', 'Latitude', 'Longitude', 'Altitude', 'Hold Time', 'Acceptance Radius'])
                
                for i, waypoint in enumerate(self.navigation.waypoints):
                    writer.writerow([
                        i + 1,
                        waypoint.latitude,
                        waypoint.longitude,
                        waypoint.altitude,
                        waypoint.hold_time,
                        waypoint.acceptance_radius
                    ])
            
            logger.info(f"Mission exported to CSV: {csv_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting mission to CSV: {e}")
            return False

# Standalone test
if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    
    from drone.connection import Connection
    from drone.control import Control
    from drone.telemetry import Telemetry
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s, %(levelname)s: %(message)s'
    )
    
    # Create mock navigation for testing
    class MockNavigation:
        def __init__(self):
            self.waypoints = []
        
        def clear_waypoints(self):
            self.waypoints.clear()
        
        def add_waypoint(self, waypoint):
            self.waypoints.append(waypoint)
        
        def calculate_distance(self,wp1, wp2):
            return 10.0  # Mock distance
    
    # Test mission planner
    mock_nav = MockNavigation()
    planner = MissionPlanner(mock_nav)
    
    # Create a test mission
    from drone.navigations import Waypoint
    mock_nav.add_waypoint(Waypoint(-35.3632620, 149.1652370, 10.0, hold_time=2))
    mock_nav.add_waypoint(Waypoint(-35.3632700, 149.1652450, 15.0))
    mock_nav.add_waypoint(Waypoint(-35.3632800, 149.1652550, 20.0, hold_time=5))
    
    # Test save
    print("Testing save mission...")
    planner.save_mission("second_mission")
    
    # Test list
    print(f"Available missions: {planner.list_missions()}")
    
    # Test validation
    print("Testing validation...")
    validation = planner.validate_mission()
    print(f"Valid: {validation['valid']}")
    if validation['errors']:
        print(f"Errors: {validation['errors']}")
    
    # Test summary
    print("Testing mission summary...")
    summary = planner.get_mission_summary()
    print(f"Summary: {summary}")
    
    # Test export
    print("Testing CSV export...")
    planner.export_mission_to_csv("test_mission")
    
    # Test load
    print("Testing load mission...")
    mock_nav.clear_waypoints()
    planner.load_mission("test_mission")
    print(f"Loaded {len(mock_nav.waypoints)} waypoints")
    
    print("Mission planner tests completed!")
