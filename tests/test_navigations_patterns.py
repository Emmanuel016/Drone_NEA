"""
test_navigations_patterns.py

Tests navigation patterns: rectangle, circle, and return to waypoint
through the Drone interface.
"""

import time
import logging

from drone.drone import Drone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "navigation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    drone = Drone()
    try:
        if not drone.Start():
            logger.error("Startup failed")
            return

        # Current location (Australia)
        center_lat = -35.363262
        center_lon = 149.165237

        logger.info("=================================")
        logger.info("Navigation Pattern Tests")
        logger.info("=================================")

        # Test 1: Rectangular Pattern
        logger.info("---------------------------------")
        logger.info("Test 1: Rectangular Pattern")
        logger.info("---------------------------------")
        
        drone.control.takeoff(20)
        drone.telemetry.wait_until_altitude(20)
        time.sleep(2)
        
        success = drone.navigation.fly_rectangle_pattern(
            center_lat=center_lat,
            center_lon=center_lon,
            altitude=20,
            width=30,
            length=30,
            heading=0
        )
        
        if success:
            logger.info("✓ Rectangular pattern completed")
        else:
            logger.error("✗ Rectangular pattern failed")

        time.sleep(3)

        # Test 2: Circular Pattern
        logger.info("---------------------------------")
        logger.info("Test 2: Circular Pattern")
        logger.info("---------------------------------")
        
        success = drone.navigation.fly_circular_pattern(
            center_lat=center_lat,
            center_lon=center_lon,
            altitude=25,
            radius=20,
            num_points=8
        )
        
        if success:
            logger.info("✓ Circular pattern completed")
        else:
            logger.error("✗ Circular pattern failed")

        time.sleep(3)

        # Test 3: Custom Waypoint Mission with Return
        logger.info("---------------------------------")
        logger.info("Test 3: Custom Waypoint Mission")
        logger.info("---------------------------------")
        
        # Add waypoints for a triangle pattern
        drone.navigation.add_waypoint(center_lat + 0.0001, center_lon + 0.0001, 20, hold_time=2)
        drone.navigation.add_waypoint(center_lat - 0.0001, center_lon + 0.0001, 25, hold_time=2)
        drone.navigation.add_waypoint(center_lat, center_lon - 0.0001, 20, hold_time=2)
        
        success = drone.navigation.execute_mission()
        
        if success:
            logger.info("✓ Custom waypoint mission completed")
        else:
            logger.error("✗ Custom waypoint mission failed")

        # Test 4: Return to Home
        logger.info("---------------------------------")
        logger.info("Test 4: Return to Home")
        logger.info("---------------------------------")
        
        success = drone.navigation.return_to_home()
        
        if success:
            logger.info("✓ Return to home initiated")
        else:
            logger.error("✗ Return to home failed")

        logger.info("=================================")
        logger.info("All navigation tests completed")
        logger.info("=================================")

    except Exception as error:
        logger.error(error)

    finally:
        drone.shutdown()

if __name__ == "__main__":
    main()
