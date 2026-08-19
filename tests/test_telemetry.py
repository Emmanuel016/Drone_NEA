"""
Tests telemetry.py through the Drone interface.
"""

import logging
from drone.drone import Drone

logger = logging.getLogger(__name__)

def main():
    drone = Drone()
    try:
        logger.info("=" * 40)
        logger.info("Starting telemetry test")
        logger.info("=" * 40)

        if not drone.Start():
            logger.error("Startup failed")
            return

        logger.info("Flight Mode:")
        drone.telemetry.get_flight_mode()

        logger.info("System Status:")
        drone.telemetry.get_system_status()

        logger.info("Altitude:")
        drone.telemetry.get_altitude()

        logger.info("Position:")
        drone.telemetry.get_position()

        logger.info("Velocity:")
        drone.telemetry.get_velocity()

        logger.info("Heading:")
        drone.telemetry.get_heading()

        logger.info("Attitude:")
        drone.telemetry.get_attitude()

        logger.info("Battery:")
        drone.telemetry.get_battery()

        logger.info("GPS:")
        drone.telemetry.get_gps()

        logger.info("Heartbeat:")
        drone.telemetry.wait_for_heartbeat()

        logger.info("=" * 40)
        logger.info("Telemetry test completed.")
        logger.info("=" * 40)

    except Exception as error:
        logger.error(error)
    finally:
        drone.shutdown()

if __name__ == "__main__":
    main()