"""
connection.py
Handles all communication between the project and an ArduPilot
vehicle through MAVLink.
Author: Emmanuel Ugwu
Project: DroneNEA
"""
import logging
import time
from pymavlink import mavutil
from drone.config import config
from drone.exceptions import ConnectionError as DroneConnectionError

# Configure module-specific logger
logger = logging.getLogger(__name__)

# Connection Class

class Connection:
    """
    Creates and manages a MAVLink connection to an ArduPilot vehicle.
    Responsibilities
    ----------------
    • Connect to the vehicle
    • Wait for a heartbeat
    • Disconnect safely
    • Reconnect if required
    • Provide access to the MAVLink master object
    • Display connection information
    """
    def __init__(self):
        """Initialise a new connection."""
        self.master = None
        self.connection_string = None
        self._connected = False

    def _check_connection(self):
        """
        Raises: DroneConnectionError If no connection exists.
        """
        if not self._connected:
            raise DroneConnectionError("Drone is not connected.")
        
    def connect(self, connection_string=None, baud=None, timeout=None):
        """
        Connect to an ArduPilot vehicle.
        Parameters: connection_string: str MAVLink connection string.
        baud: int Serial baud rate (ignored for UDP/TCP).
        timeout: int Heartbeat timeout in seconds.
        Returns: mavutil.mavfile Active MAVLink connection.
        Raises: DroneConnectionError If the connection cannot be established.
        """
        # Use config defaults if not provided
        if connection_string is None:
            connection_string = config.connection.DEFAULT_UDP
        if baud is None:
            baud = config.connection.DEFAULT_BAUD
        if timeout is None:
            timeout = config.connection.DEFAULT_TIMEOUT
        
        if self._connected:
            logger.warning("Already connected.")
            return self.master
        for attempt in range(config.connection.MAX_RETRIES):
          try:
            logger.info("Connecting to ArduPilot...")
            self.connection_string = connection_string
            self.master = mavutil.mavlink_connection(
                connection_string,
                baud=baud
            )
            self.wait_for_heartbeat(timeout)
            logger.info("Connection established.")
            self.print_connection_info()
            return self.master
          except Exception as error:
            self._connected = False
            self.master = None
            logger.error(f"Connection failed: {type(error).__name__}: {error}")
            if attempt < config.connection.MAX_RETRIES - 1:
                logger.info(f"Retrying in {config.connection.RETRY_DELAY} seconds...")
                time.sleep(config.connection.RETRY_DELAY)
            else:
                raise DroneConnectionError(
                    f"Unable to connect to ArduPilot after {config.connection.MAX_RETRIES} attempts: {error}",
                    details={"attempts": config.connection.MAX_RETRIES, "last_error": str(error)}
                )

    def disconnect(self):
        """
        Close the MAVLink connection safely.
        """
        if self.master:
            self.master.close()
        self.master = None
        self.connection_string = None
        self._connected = False
        logger.info("Disconnected from ArduPilot.")

    def reconnect(self, connection_string=None, baud=None, timeout=None):
        """
        Disconnect then reconnect using the supplied settings.
        """
        # Use config defaults if not provided
        if connection_string is None:
            connection_string = config.connection.DEFAULT_UDP
        if baud is None:
            baud = config.connection.DEFAULT_BAUD
        if timeout is None:
            timeout = config.connection.DEFAULT_TIMEOUT
        
        logger.info("Reconnecting...")
        self.disconnect()
        return self.connect(connection_string, baud, timeout)

    # Heartbeat

    def wait_for_heartbeat(self, timeout=None):
        """
        Wait until ArduPilot sends its first heartbeat.
        A heartbeat confirms that communication has been
        successfully established.
        Raises: DroneConnectionError If no heartbeat is received.
        """
        if timeout is None:
            timeout = config.connection.DEFAULT_TIMEOUT
        if self.master is None:
            raise ConnectionError("No MAVLink connection exists.")
        
        logger.info("Waiting for heartbeat...")
        start = time.time()
        try:
            self.master.wait_heartbeat(timeout=timeout)
            self._connected = True
            elapsed = time.time() - start
            logger.info(
                "Heartbeat received "
                f"(System={self.master.target_system}, "
                f"Component={self.master.target_component})"
            )
            logger.info(f"Heartbeat received after "f"{elapsed:.2f} seconds.")
            msg = self.master.recv_match(
                blocking=True,
                timeout=2
            )
            if msg:
                logger.info(f"First MAVLink message: "f"{msg.get_type()}")
        except Exception as error:
            self._connected = False
            raise DroneConnectionError(f"Failed to receive heartbeat: {error}")

    # Utility Methods

    def get_master(self):
        #Return the active MAVLink connection.
        self._check_connection()
        return self.master
    
    def is_connected(self):
        #Returns bool: True if connected.
        return self._connected
    
    def print_connection_info(self):
        """
        Display information about the current connection.
        """
        self._check_connection()
        logger.info("\n" + "=" * 50)
        logger.info("Connection Information")
        logger.info("=" * 50)
        logger.info(f"Connection : {self.connection_string}")
        logger.info(f"System ID  : {self.master.target_system}")
        logger.info(f"Component  : {self.master.target_component}")
        logger.info(f"Mode       : {self.master.flightmode}")
        logger.info("=" * 50)

    # String Representation

    def __repr__(self):
        return (f"Connection("f"connected={self._connected}, "f"connection='{self.connection_string}')")

# Standalone Test

if __name__ == "__main__":
    connection = Connection()
    try:
        connection.connect()
    except ConnectionError as error:
        logger.error(error)
    finally:
        if connection.is_connected():
            connection.disconnect()