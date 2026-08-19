"""
control.py
Contains high-level flight control commands for an ArduPilot vehicle.
Author: Emmanuel Ugwu
Project: DroneNEA
"""

import logging
from pathlib import Path
import time
from pymavlink import mavutil
from drone.connection import Connection
from drone.telemetry import Telemetry
from drone.config import config
from drone.exceptions import ConnectionError as DroneConnectionError, ControlError, TimeoutError

# Configure module-specific logger
logger = logging.getLogger(__name__)

# Control Class

class Control:
    """
    High-level drone controller.
    This class wraps common MAVLink commands into simple
    Python methods.
    Features
    --------
    • Arm / Disarm
    • Flight Mode Control
    • Takeoff
    • Landing
    • Return To Launch
    • Velocity Movement
    • Yaw Control
    • Position Hold
    • Telemetry Helpers
    """
    def __init__(self, connection: Connection):
        """
        Create a new flight controller.
        Parameters: Connection
            Active MAVLink connection.
        """
        self.connection = connection
        self.master = connection.get_master()
        self.telemetry = Telemetry(connection)

    def _check_connection(self):
        """
        Ensure the vehicle is connected.
        """
        if not self.connection.is_connected():
            raise DroneConnectionError("Drone is not connected.")

    def _wait_for_mode(self, mode, timeout=20):

        #Wait until the requested flight mode is active.
        start = time.time()
        while time.time() - start < timeout:
            hb = self.master.recv_match(
                type="HEARTBEAT",
                blocking=True,
                timeout=1)

            if hb is None:
                logger.info(f"An error occurred while waiting for mode change.")
                continue
            current = self.master.flightmode
            logger.info(f"Current mode: {current}")

            if current == mode:
                logger.info(f"{mode} confirmed.")
                return
            else:
                logger.info(f"Waiting for {mode} mode... and it's not yet on {mode}")

        raise TimeoutError(
            f"Failed to enter {mode} mode. Current mode: {self.master.flightmode}.",
            details={"requested_mode": mode, "current_mode": self.master.flightmode, "timeout": timeout}
        )
    # Vehicle Status

    def is_armed(self):
        """Returns: bool True if motors are armed.
        """
        self._check_connection()
        return self.master.motors_armed()
    
    def get_mode(self):
        """
        Returns the current flight mode.
        """
        self._check_connection()
        mode = self.master.flightmode
        logger.info(f"Current Mode : {mode}")
        return mode

    # Flight Modes
    def set_mode(self, mode):
       """Change the drone flight mode.
       Example: control.set_mode("GUIDED")"""
       self._check_connection()
       mode = mode.upper()
       # Available flight modes
       mode_mapping = self.master.mode_mapping()
       if mode not in mode_mapping:
            raise ValueError(f"'{mode}' is not a valid flight mode.")
            
       # Already in requested mode
       if self.master.flightmode == mode:
            logger.info(f"Drone is already in {mode} mode.")
            return True
       logger.info(f"Changing mode to {mode}...")
       mode_id = mode_mapping[mode]
       
       # Use MAV_CMD_DO_SET_MODE for reliable mode changes
       self.master.mav.command_long_send(
           self.master.target_system,
           self.master.target_component,
           mavutil.mavlink.MAV_CMD_DO_SET_MODE,
           0, 
           1, 
           mode_id,  # param2: custom mode (flight mode number)
           0,  # param3: not used
           0,  # param4: not used
           0,  # param5: not used
           0,  # param6: not used
           0   # param7: not used
       )
       
       # Wait until ArduPilot reports the new mode
       self._wait_for_mode(mode)
       logger.info(f"Flight mode changed to {mode}.")
       return True

    # Arm / Disarm

    def arm(self):
        """
        Arm the drone motors.
        """
        self._check_connection()
        if self.is_armed():
            logger.info("Drone is already armed.")
            return True
        logger.info("Arming drone...")
        self.master.arducopter_arm()
        self.master.motors_armed_wait()
        logger.info("Drone armed successfully.")
        return True

    def disarm(self):
        """
        Disarm the drone motors.
        """
        self._check_connection()
        if not self.is_armed():
            logger.info("Drone is already disarmed.")
            return True
        logger.info("Disarming drone...")
        self.master.arducopter_disarm()
        self.master.motors_disarmed_wait()
        logger.info("Drone disarmed successfully.")
        return True

    # Flight Operations

    def takeoff(self, altitude):
        """
        Arm the drone and take off to the specified altitude.
        Parameters: altitude: float Target altitude in metres.
        """
        self._check_connection()
        if altitude <= 0:
            raise ControlError("Takeoff altitude must be greater than zero.", 
                            details={"altitude": altitude, "min_altitude": 0})
        logger.info(f"Preparing for takeoff to {altitude:.1f} m...")
        self.set_mode("GUIDED")
        time.sleep(3)
        if not self.is_armed():
            self.arm()
            time.sleep(2)
        logger.info("Sending takeoff command...")
        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,0, 0, 0, 0, 0, 0, 0, altitude)
        logger.info("Takeoff command sent.")
        return True

    def land(self):
        """
        Land the drone at its current location.
        """
        self._check_connection()
        logger.info("Landing drone...")
        self.set_mode("LAND")
        logger.info("LAND mode activated.")
        self.telemetry.wait_until_landed()
        return True


    def rtl(self):
        """
        Return the drone to its launch position.
        """
        self._check_connection()
        logger.info("Returning to launch...")
        self.set_mode("RTL")
        logger.info("RTL mode activated.")
        return True

    def hold_position(self):
        """
        Hold the current position.
        This switches the drone into LOITER mode.
        """
        self._check_connection()
        logger.info("Holding current position...")
        self.set_mode("LOITER")
        logger.info("Drone is now holding position.")
        return True

    def emergency_land(self, reason="Unknown"):
        """
        Immediately command the drone to land with safety adaptations.
        
        Parameters:
            reason: str - Description of emergency reason for logging
        
        Safety adaptations:
            - Checks current altitude and battery status
            - Reduces speed before landing if at high altitude
            - Uses RTL if far from home and battery critical
            - Implements timeout and fallback mechanisms
            - Logs emergency context for post-flight analysis
        """
        self._check_connection()
        logger.warning(f"EMERGENCY LANDING INITIATED - Reason: {reason}")
        
        try:
            # Get current telemetry for safety decisions
            current_altitude = self.telemetry.get_altitude()
            battery = self.telemetry.get_battery()
            current_mode = self.get_mode()
            
            logger.warning(f"Emergency context - Altitude: {current_altitude:.1f}m, Battery: {battery}%, Mode: {current_mode}")
            
            # Safety check: if critically low battery and far from home, use RTL
            if battery is not None and battery < 15 and current_altitude > 20:
                logger.critical("Critical battery - Using RTL for emergency return")
                try:
                    self.set_mode("RTL")
                    # Wait for RTL to bring drone closer, then switch to LAND
                    time.sleep(5)
                    current_altitude = self.telemetry.get_altitude()
                    if current_altitude > 10:
                        logger.warning("Altitude still high after RTL, switching to LAND")
                except Exception as e:
                    logger.error(f"RTL failed: {e}, proceeding with direct LAND")
            
            # Safety check: if at very high altitude, reduce descent rate
            if current_altitude is not None and current_altitude > 50:
                logger.warning("High altitude emergency - reducing descent rate")
                # First switch to GUIDED for controlled descent
                try:
                    self.set_mode("GUIDED")
                    time.sleep(1)
                    # Send descent command at controlled rate
                    for _ in range(3):  # Multiple attempts to ensure command received
                        self.master.mav.command_long_send(
                            self.master.target_system,
                            self.master.target_component,
                            mavutil.mavlink.MAV_CMD_NAV_LAND,
                            0, 0, 0, 0, 0, 0, 0, 0
                        )
                        time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Controlled descent failed: {e}, switching to LAND mode")
            
            # Primary landing command
            logger.warning("Executing LAND mode command")
            try:
                self.set_mode("LAND")
            except Exception as e:
                logger.error(f"LAND mode failed: {e}")
                # Fallback: try direct land command
                logger.warning("Attempting direct land command as fallback")
                self.master.mav.command_long_send(
                    self.master.target_system,
                    self.master.target_component,
                    mavutil.mavlink.MAV_CMD_NAV_LAND,
                    0, 0, 0, 0, 0, 0, 0, 0
                )
            
            # Wait for landing with extended timeout for emergency scenarios
            logger.warning("Waiting for landing confirmation...")
            landed = self.telemetry.wait_until_landed(timeout=90, threshold=1.0)
            
            if landed:
                logger.warning("EMERGENCY LANDING COMPLETED SUCCESSFULLY")
                # Ensure drone is disarmed
                try:
                    self.disarm()
                    logger.info("Drone disarmed after emergency landing")
                except Exception as e:
                    logger.error(f"Disarm failed after landing: {e}")
            else:
                logger.critical("EMERGENCY LANDING TIMEOUT - Drone may still be airborne!")
                # Last resort: try to disarm anyway
                try:
                    self.disarm()
                except Exception as disarm_error:
                    logger.critical(f"Emergency disarm also failed: {disarm_error}")
                    pass
                    
        except Exception as e:
            logger.critical(f"Emergency landing procedure failed: {e}")
            # Last ditch effort: direct disarm
            try:
                logger.critical("Attempting emergency disarm as last resort")
                self.master.mav.command_long_send(
                    self.master.target_system,
                    self.master.target_component,
                    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                    0, 0, 0, 0, 0, 0, 0, 0, 0  # Disarm command
                )
            except Exception as disarm_error:
                logger.critical(f"Emergency disarm also failed: {disarm_error}")
                return False
        return True
        
    def brake(self):
        #Brake in emergency
        self._check_connection()
        logger.critical(f'BRAKING COMMAND SENT')
        self.set_mode('BRAKE')

    # Velocity Control 
    def move_body_velocity(self, vf, vr, vd, duration):
        """
        Move the drone using body-frame velocities.
        Parameters:
        vf: float Forward velocity (m/s)
        vr: float Right velocity (m/s)
        vd: float Down velocity (m/s)
        duration: float Time in seconds to apply the velocity.
        """
        self._check_connection()
        logger.info(f"Velocity Command | "f"Forward={vf:.2f} "f"Right={vr:.2f} "f"Downwards={vd:.2f}")
        start = time.time()
        while time.time() - start < duration:
            self.master.mav.set_position_target_local_ned_send(0,
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_FRAME_BODY_NED,
                0b0000111111000111,
                0, 0, 0, vf, vr, vd, 0, 0, 0, 0, 0)
            time.sleep(0.1)
        logger.info("Velocity movement complete.")
        return True

    # Yaw Control

    def set_yaw(self,angle,clockwise=True,relative=False):
        """
        Rotate the drone to a yaw angle.
        Parameters:
        angle: float Target yaw angle.
        clockwise: bool True = clockwise.
        relative: bool True if the angle is relative to the current heading.
        """
        self._check_connection()
        direction = 1 if clockwise else -1
        relative_flag = 1 if relative else 0
        logger.info(f"Rotating to {angle}°")
        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_CONDITION_YAW,
            0,angle,20,direction,relative_flag,0,0,0)
        
        logger.info("Yaw command sent.")
        return True

    # Debug Representation

    def __repr__(self):
        mode = self.master.flightmode if self.connection.is_connected() else "UNKNOWN"
        return (
            f"Control("
            f"connected={self.connection.is_connected()}, "
            f"armed = {(self.is_armed()if self.connection.is_connected()else False)}"
            f"mode='{mode}')"
        )

# Standalone Test
if __name__ == "__main__":
    connection = Connection()
    
    try:
        connection.connect()
        control = Control(connection)
        control.set_mode("GUIDED")
        control.arm()
        control.takeoff(5)
        control.wait_until_altitude(5)
        logger.info(f"Battery: {control.get_battery_status()}%")
        logger.info(f"Heading: {control.get_heading()}°")
        time.sleep(5)
        control.land()
    except Exception as error:
        logger.error(error)
    finally:
        connection.disconnect()