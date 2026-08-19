"""
test_control.py

Tests the Control class through the Drone interface by performing
basic flight operations in ArduPilot SITL.
"""

import time
import logging

from drone.drone import Drone

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    drone = Drone()
    try:
        if not drone.Start():
            logger.error("Startup failed")
            return

        logger.info("Current Flight Mode:")
        logger.info(drone.control.get_mode())

        logger.info("Battery:")
        logger.info(f"{drone.telemetry.get_battery()}%")

        logger.info("Altitude:")
        logger.info(f"{drone.telemetry.get_altitude()} m")

        logger.info("---------------------------------")
        logger.info("Starting flight test")
        logger.info("---------------------------------")

        drone.control.takeoff(5)
        drone.telemetry.wait_until_altitude(5)
        time.sleep(3)

        drone.control.move_body_velocity(
            vf=1,
            vr=0,
            vd=0,
            duration=3
        )
        time.sleep(2)
        drone.control.set_yaw(90)

        time.sleep(4)
        drone.control.land()
        drone.telemetry.get_altitude()
        time.sleep(15)

        logger.info("Flight test completed successfully.")
    except Exception as error:
        logger.error(error)
    finally:
        drone.shutdown()

if __name__ == "__main__":
    main()