"""
TelemetryManager for managing background telemetry updates and WebSocket emissions.
"""

import threading
import time


class TelemetryManager:
    """Manages background telemetry updates and WebSocket emissions."""
    
    def __init__(self, socketio, drone):
        self.socketio = socketio
        self.drone = drone
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the background telemetry thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._telemetry_loop, daemon=True)
            self.thread.start()
            print(f"[TelemetryManager] Thread started, running={self.running}")
        else:
            print(f"[TelemetryManager] Thread already running")
    
    def stop(self):
        """Stop the background telemetry thread."""
        self.running = False
        print(f"[TelemetryManager] Stopping thread, running={self.running}")
        if self.thread:
            self.thread.join(timeout=2)
            print(f"[TelemetryManager] Thread stopped")
    
    def _telemetry_loop(self):
        """Background thread to emit telemetry updates to connected clients."""
        print(f"[TelemetryManager] Loop started")
        while self.running:
            try:
                is_connected = self.drone.is_connected()
                telemetry_data = self._get_telemetry_data()
                print(f"[TelemetryManager] Emitting telemetry: connected={is_connected}, battery={telemetry_data.get('battery')}")
                self.socketio.emit('telemetry_update', telemetry_data)
            except Exception as e:
                print(f"[TelemetryManager] Telemetry update error: {e}")
            
            time.sleep(0.5)  # Update every 500ms
        print(f"[TelemetryManager] Loop ended")
    
    def _get_telemetry_data(self):
        """Collect telemetry data from drone subsystems safely."""
        try:
            position_tuple = self.drone.telemetry.get_position()
            attitude_tuple = self.drone.telemetry.get_attitude()
            battery = self.drone.telemetry.get_battery()
            velocity = self.drone.telemetry.get_velocity()
            gps = self.drone.telemetry.get_gps()
            
            # Convert position tuple to dictionary
            if position_tuple:
                latitude, longitude, altitude = position_tuple
                position = {'latitude': latitude, 'longitude': longitude, 'altitude': altitude}
            else:
                position = {'latitude': 0.0, 'longitude': 0.0, 'altitude': 0.0}
            
            # Convert attitude tuple to dictionary
            if attitude_tuple:
                roll, pitch, yaw = attitude_tuple
                attitude = {'roll': roll, 'pitch': pitch, 'yaw': yaw}
            else:
                attitude = {'yaw': 0.0, 'pitch': 0.0, 'roll': 0.0}
            
            # Convert velocity tuple to ground speed
            if velocity:
                v_forward, v_right, v_up = velocity
                speed = (v_forward**2 + v_right**2 + v_up**2)**0.5  # Calculate magnitude
            else:
                speed = 0.0
                
        except Exception as e:
            # Continue running but return fallback data if telemetry fails on a tick
            position = {'latitude': 0.0, 'longitude': 0.0, 'altitude': 0.0}
            attitude = {'yaw': 0.0, 'pitch': 0.0, 'roll': 0.0}
            battery = 0.0
            speed = 0.0
            gps = {'satellites': 0, 'fix_type': 0}
        
        is_connected = self.drone.is_connected()
        return {
            'position': position,
            'attitude': attitude,
            'battery': battery,
            'speed': speed,
            'gps': gps,
            'connected': is_connected,
            'armed': self.drone.control.is_armed() if is_connected and getattr(self.drone, 'control', None) else False,
            'mode': self.drone.control.get_mode() if is_connected and getattr(self.drone, 'control', None) else 'Unknown'
        }
