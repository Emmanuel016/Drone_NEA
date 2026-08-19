"""
telemetry.py
Reads telemetry data from an ArduPilot vehicle.
This module never controls the drone.
It only receives and interprets MAVLink messages.
"""

import logging
import time
from drone.connection import Connection
from drone.config import config

# Configure module-specific logger
logger = logging.getLogger(__name__)

class Telemetry:
    """
    Reads telemetry information from the connected drone.
    Examples include:
    • Flight mode
    • Altitude
    • GPS position
    • Battery
    • Speed
    • Attitude
    • Heartbeat
    """

    def __init__(self, connection: Connection):
        self.connection = connection
        self.master = connection.get_master()

    def _check_connection(self):
        """
        Ensure a MAVLink connection exists.
        """
        if not self.connection.is_connected():
            raise ConnectionError("Drone is not connected.")

    def _receive(self, message_type):
        """
        Receive a MAVLink message.
        Returns the latest message of the requested type.
        """
        self._check_connection()
        return self.master.recv_match(
            type=message_type,
            blocking=True,
            timeout=2
        )

    def get_flight_mode(self):
        """
        Return the current flight mode.
        """
        self._check_connection()
        mode = self.master.flightmode
        logger.info(f"Flight Mode : {mode}")
        return mode
    
    def is_armed(self) -> str:
        self._check_connection()
        return f"Drone is armed" if self.master.motors_armed() else f"Drone is not armed"

    def get_system_status(self):
        """
        Return the autopilot system status.
        """
        heartbeat = self._receive("HEARTBEAT")
        if heartbeat is None:
            logger.warning("No heartbeat received")
            return None
        statuses = {
            0: "UNINIT",
            1: "BOOT",
            2: "CALIBRATING",
            3: "STANDBY",
            4: "ACTIVE",
            5: "CRITICAL",
            6: "EMERGENCY",
            7: "POWEROFF"
        }

        status = statuses.get(
        heartbeat.system_status,
        "UNKNOWN"
       )
        logger.info(f"System Status : {status}")
        return status

    def get_altitude(self):
        """
        Return the current relative altitude.
        """
        msg = self._receive("GLOBAL_POSITION_INT")
        if msg is None:
            logger.warning("Could not receive altitude message.")
            return None
        altitude = msg.relative_alt / 1000
        logger.info(f"Altitude : {altitude:.2f} m")
        return altitude

    def get_position(self):
        """
        Return latitude, longitude and altitude.
        """
        msg = self._receive("GLOBAL_POSITION_INT")
        if msg is None:
            logger.warning("Could not receive position message.")
            return None
        latitude = msg.lat / 1e7
        longitude = msg.lon / 1e7
        altitude = msg.relative_alt / 1000
        logger.info(
            f"Position : "
            f"{latitude:.7f}, "
            f"{longitude:.7f}, "
            f"{altitude:.2f} m"
        )

        return latitude, longitude, altitude

    def get_battery(self):
        """
        Return remaining battery percentage.
        """
        msg = self._receive("SYS_STATUS")
        if msg is None:
            logger.warning('No battery message received')
            return None

        battery = msg.battery_remaining
        if battery < 0:
            logger.info('Battery Information Unavailable')
        else:
            logger.info(f"Battery : {battery}%")
        return battery

    def get_velocity(self):
        """
        Return velocity in m/s.
        """
        msg = self._receive("GLOBAL_POSITION_INT")
        if msg is None:
            logger.warning("No velocity info received")
            return None

        v_forward = msg.vx / 100
        v_right = msg.vy / 100
        v_up = msg.vz / 100

        logger.info(
            f"Velocity : "
            f"Forwards={v_forward:.2f} "
            f"Right={v_right:.2f} "
            f"Up={v_up:.2f}"
        )
        return v_forward, v_right, v_up
    
    def get_attitude(self):
        """
        Return roll, pitch and yaw.
        """
        msg = self._receive("ATTITUDE")
        if msg is None:
            logger.warning("No attitude info received")
            return None
        
        logger.info(
            f"Roll={msg.roll:.2f} "
            f"Pitch={msg.pitch:.2f} "
            f"Yaw={msg.yaw:.2f}"
        )
        return (
            msg.roll,
            msg.pitch,
            msg.yaw
        )

    def get_gps(self):
        """
        Return GPS information.
        """
        msg = self._receive("GPS_RAW_INT")
        if msg is None:
            logger.warning("No GPS data received")
            return None
        logger.info(
            f"Satellites = {msg.satellites_visible}"
        )
        return {
            "fix_type": msg.fix_type,
            "satellites": msg.satellites_visible,
            "latitude": msg.lat / 1e7,
            "longitude": msg.lon / 1e7
        }

    def get_heading(self):
        """
        Return the current heading in degrees.
        """
        msg = self._receive("VFR_HUD")
        if msg is None:
            logger.warning("No heading info received")
            return None
        heading = msg.heading
        logger.info(f"Heading : {heading}°")
        return heading

    def wait_until_altitude(self, target_altitude, timeout=30):
        """
        Wait until the drone reaches the specified altitude.
        """
        self._check_connection()
        logger.info(f"Waiting to reach {target_altitude:.1f} m...")
        start = time.time()
        previous_altitude = None
        while time.time() - start < timeout:
            msg = self._receive("GLOBAL_POSITION_INT")
            if msg is None:
                continue
            altitude = msg.relative_alt / 1000.0
            if previous_altitude is None or abs(altitude - previous_altitude) >= 0.1:
                logger.info(f"Current Altitude : {altitude:.2f} m")
                previous_altitude = altitude
            if altitude >= target_altitude:
                logger.info("Target altitude reached.")
                return True
            time.sleep(0.5)
        logger.warning("Timed out waiting for altitude.")
        return False

    def wait_until_landed(self, timeout=60, threshold=0.5):
        """
        Wait until the drone lands (altitude drops below threshold).
        """
        self._check_connection()
        logger.info(f"Waiting for landing (altitude < {threshold:.1f} m)...")
        start = time.time()
        previous_altitude = None
        while time.time() - start < timeout:
            msg = self._receive("GLOBAL_POSITION_INT")
            if msg is None:
                continue
            altitude = msg.relative_alt / 1000.0
            if previous_altitude is None or abs(altitude - previous_altitude) >= 0.1:
                logger.info(f"Current Altitude : {altitude:.2f} m")
                previous_altitude = altitude
            if altitude <= threshold:
                logger.info("Landing confirmed.")
                return True
            time.sleep(0.5)
        logger.warning("Timed out waiting for landing.")
        return False

    def wait_for_heartbeat(self):
        """
        Wait for a heartbeat.
        Returns True if received.
        """
        self._check_connection()
        self.master.wait_heartbeat(timeout=5)
        logger.info("Heartbeat received.")
        return True
    
    def get_message(self, message_type):
       """Receive any MAVLink message.
       Example:telemetry.get_message("ATTITUDE")
       """
       return self._receive(message_type)

    def get_all(self):
        """Return all important telemetry."""

        return {
        "mode": self.get_flight_mode(),
        "altitude": self.get_altitude(),
        "battery": self.get_battery(),
        "position": self.get_position(),
        "heading": self.get_heading(),
        "velocity": self.get_velocity(),
        }

    def __repr__(self):
        return (
            f"Telemetry("
            f"connected={self.connection.is_connected()}, "
            f"mode='{self.master.flightmode}')"
        )

if __name__ == "__main__":
    connection = Connection()
    try:
        connection.connect()
        telemetry = Telemetry(connection)

        telemetry.get_flight_mode()
        telemetry.get_system_status()
        telemetry.get_altitude()
        telemetry.get_position()
        telemetry.get_velocity()
        telemetry.get_heading()
        telemetry.get_attitude()
        telemetry.get_battery()
        telemetry.get_gps()

    except Exception as error:
        logger.error(error)
    finally:
        connection.disconnect()