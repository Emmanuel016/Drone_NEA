"""
test_mission.py

Tests the MissionPlanner class functionality including loading, saving,
validating, and managing drone missions.
"""

import logging
from pathlib import Path

from drone.drone import Drone
from drone.navigations import Waypoint

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "mission.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_save_and_load_mission():
    """Test saving and loading mission files."""
    logger.info("=================================")
    logger.info("Test: Save and Load Mission")
    logger.info("=================================")
    
    drone = Drone()
    try:
        if not drone.Start():
            logger.error("Startup failed")
            return False
        
        # Create test waypoints
        center_lat = -35.363262
        center_lon = 149.165237
        
        drone.navigation.add_waypoint(center_lat, center_lon, 20, hold_time=2)
        drone.navigation.add_waypoint(center_lat + 0.0001, center_lon + 0.0001, 25)
        drone.navigation.add_waypoint(center_lat - 0.0001, center_lon - 0.0001, 20, hold_time=3)
        
        # Save mission
        success = drone.mission_planner.save_mission("test_mission", metadata={"test": True})
        if success:
            logger.info("✓ Mission saved successfully")
        else:
            logger.error("✗ Mission save failed")
            return False
        
        # Clear waypoints
        drone.navigation.clear_waypoints()
        logger.info(f"Waypoints cleared: {drone.navigation.number_of_waypoints()}")
        
        # Load mission
        success = drone.mission_planner.load_mission("test_mission")
        if success:
            logger.info("✓ Mission loaded successfully")
            logger.info(f"Loaded {drone.navigation.number_of_waypoints()} waypoints")
        else:
            logger.error("✗ Mission load failed")
            return False
        
        return True
        
    except Exception as error:
        logger.error(f"Test failed: {error}")
        return False
    finally:
        drone.shutdown()

def test_validate_mission():
    """Test mission validation."""
    logger.info("=================================")
    logger.info("Test: Validate Mission")
    logger.info("=================================")
    
    drone = Drone()
    try:
        if not drone.Start():
            logger.error("Startup failed")
            return False
        
        # Create valid waypoints
        center_lat = -35.363262
        center_lon = 149.165237
        
        drone.navigation.add_waypoint(center_lat, center_lon, 20)
        drone.navigation.add_waypoint(center_lat + 0.001, center_lon + 0.001, 25)
        
        # Validate valid mission
        validation = drone.mission_planner.validate_mission()
        if validation['valid']:
            logger.info("✓ Valid mission passed validation")
        else:
            logger.error("✗ Valid mission failed validation")
            logger.error(f"Errors: {validation['errors']}")
            return False
        
        # Test invalid waypoint (invalid latitude)
        drone.navigation.add_waypoint(95.0, center_lon, 20)  # Invalid latitude
        validation = drone.mission_planner.validate_mission()
        if not validation['valid']:
            logger.info("✓ Invalid latitude detected correctly")
            logger.info(f"Error: {validation['errors']}")
        else:
            logger.error("✗ Invalid latitude not detected")
            return False
        
        return True
        
    except Exception as error:
        logger.error(f"Test failed: {error}")
        return False
    finally:
        drone.shutdown()

def test_mission_summary():
    """Test mission summary generation."""
    logger.info("=================================")
    logger.info("Test: Mission Summary")
    logger.info("=================================")
    
    drone = Drone()
    try:
        if not drone.Start():
            logger.error("Startup failed")
            return False
        
        # Create waypoints
        center_lat = -35.363262
        center_lon = 149.165237
        
        drone.navigation.add_waypoint(center_lat, center_lon, 20)
        drone.navigation.add_waypoint(center_lat + 0.001, center_lon + 0.001, 30)
        drone.navigation.add_waypoint(center_lat + 0.002, center_lon + 0.002, 25)
        
        # Get summary
        summary = drone.mission_planner.get_mission_summary()
        
        logger.info(f"Waypoint count: {summary['waypoint_count']}")
        logger.info(f"Total distance: {summary['total_distance']} m")
        logger.info(f"Min altitude: {summary['min_altitude']} m")
        logger.info(f"Max altitude: {summary['max_altitude']} m")
        logger.info(f"Estimated time: {summary['estimated_time']} s")
        
        if summary['waypoint_count'] == 3:
            logger.info("✓ Mission summary generated correctly")
        else:
            logger.error("✗ Incorrect waypoint count in summary")
            return False
        
        return True
        
    except Exception as error:
        logger.error(f"Test failed: {error}")
        return False
    finally:
        drone.shutdown()

def test_export_to_csv():
    """Test CSV export functionality."""
    logger.info("=================================")
    logger.info("Test: Export to CSV")
    logger.info("=================================")
    
    drone = Drone()
    try:
        if not drone.Start():
            logger.error("Startup failed")
            return False
        
        # Create waypoints
        center_lat = -35.363262
        center_lon = 149.165237
        
        drone.navigation.add_waypoint(center_lat, center_lon, 20)
        drone.navigation.add_waypoint(center_lat + 0.0001, center_lon + 0.0001, 25)
        
        # Export to CSV
        success = drone.mission_planner.export_mission_to_csv("test_export")
        if success:
            logger.info("✓ Mission exported to CSV successfully")
        else:
            logger.error("✗ CSV export failed")
            return False
        
        # Check if file exists
        csv_file = Path(__file__).resolve().parent.parent / "missions" / "test_export.csv"
        if csv_file.exists():
            logger.info(f"✓ CSV file created: {csv_file}")
        else:
            logger.error("✗ CSV file not found")
            return False
        
        return True
        
    except Exception as error:
        logger.error(f"Test failed: {error}")
        return False
    finally:
        drone.shutdown()

def test_list_and_delete_missions():
    """Test listing and deleting missions."""
    logger.info("=================================")
    logger.info("Test: List and Delete Missions")
    logger.info("=================================")
    
    drone = Drone()
    try:
        if not drone.Start():
            logger.error("Startup failed")
            return False
        
        # Create a test mission
        drone.navigation.add_waypoint(-35.363262, 149.165237, 20)
        drone.mission_planner.save_mission("temp_test_mission")
        
        # List missions
        missions = drone.mission_planner.list_missions()
        logger.info(f"Available missions: {missions}")
        
        if "temp_test_mission" in missions:
            logger.info("✓ Mission listed correctly")
        else:
            logger.error("✗ Mission not found in list")
            return False
        
        # Delete mission
        success = drone.mission_planner.delete_mission("temp_test_mission")
        if success:
            logger.info("✓ Mission deleted successfully")
        else:
            logger.error("✗ Mission deletion failed")
            return False
        
        # Verify deletion
        missions = drone.mission_planner.list_missions()
        if "temp_test_mission" not in missions:
            logger.info("✓ Mission removed from list")
        else:
            logger.error("✗ Mission still in list after deletion")
            return False
        
        return True
        
    except Exception as error:
        logger.error(f"Test failed: {error}")
        return False
    finally:
        drone.shutdown()

def test_create_mission_from_dict():
    """Test creating mission from dictionary."""
    logger.info("=================================")
    logger.info("Test: Create Mission from Dict")
    logger.info("=================================")
    
    drone = Drone()
    try:
        if not drone.Start():
            logger.error("Startup failed")
            return False
        
        # Create mission data
        mission_data = {
            "waypoints": [
                {
                    "latitude": -35.363262,
                    "longitude": 149.165237,
                    "altitude": 20.0,
                    "hold_time": 2,
                    "acceptance_radius": 5.0
                },
                {
                    "latitude": -35.363262 + 0.0001,
                    "longitude": 149.165237 + 0.0001,
                    "altitude": 25.0,
                    "hold_time": 0,
                    "acceptance_radius": 5.0
                }
            ]
        }
        
        # Create mission from dict
        success = drone.mission_planner.create_mission_from_dict(mission_data)
        if success:
            logger.info("✓ Mission created from dictionary")
            logger.info(f"Waypoints: {drone.navigation.number_of_waypoints()}")
        else:
            logger.error("✗ Failed to create mission from dictionary")
            return False
        
        # Test invalid data (missing waypoints key)
        invalid_data = {"name": "test"}
        success = drone.mission_planner.create_mission_from_dict(invalid_data)
        if not success:
            logger.info("✓ Invalid data rejected correctly")
        else:
            logger.error("✗ Invalid data should have been rejected")
            return False
        
        return True
        
    except Exception as error:
        logger.error(f"Test failed: {error}")
        return False
    finally:
        drone.shutdown()

def main():
    """Run all mission planner tests."""
    logger.info("=================================")
    logger.info("Mission Planner Test Suite")
    logger.info("=================================")
    
    tests = [
        ("Save and Load Mission", test_save_and_load_mission),
        ("Validate Mission", test_validate_mission),
        ("Mission Summary", test_mission_summary),
        ("Export to CSV", test_export_to_csv),
        ("List and Delete Missions", test_list_and_delete_missions),
        ("Create Mission from Dict", test_create_mission_from_dict),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test crashed: {e}")
            results[test_name] = False
    
    # Print summary
    logger.info("\n=================================")
    logger.info("Test Summary")
    logger.info("=================================")
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    logger.info(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
