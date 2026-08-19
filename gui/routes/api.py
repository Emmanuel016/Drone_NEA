"""
API routes for drone control operations.
Provides REST endpoints for drone control, telemetry, and mission management.
"""

from flask import Blueprint, request, jsonify
from drone.config import config
from drone.exceptions import DroneNEAError
import time

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

api_bp = Blueprint('api', __name__)


def handle_error(error: Exception) -> tuple:
    """
    Convert exceptions to consistent API error responses.
    
    Args:
        error: Exception to handle
        
    Returns:
        tuple: (json_response, status_code)
    """
    if isinstance(error, DroneNEAError):
        return jsonify({
            'success': False,
            'error': error.to_dict()
        }), 400
    else:
        return jsonify({
            'success': False,
            'error': {
                'error_type': 'InternalServerError',
                'message': 'An unexpected error occurred',
                'details': str(error)
            }
        }), 500


@api_bp.route('/api/connect', methods=['POST'])
def connect():
    """Connect to the drone."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    telemetry_manager = current_app.telemetry_manager
    
    data = request.get_json(silent=True) or {}
    connection_string = data.get('connection_string')
    baud = data.get('baud')
    timeout = data.get('timeout')
    
    print(f"[API] Connect request: conn={connection_string}, baud={baud}, timeout={timeout}")
    
    try:
        success = drone_controller.connect(connection_string, baud, timeout)
        print(f"[API] Connect result: success={success}")
        if success:
            print(f"[API] Starting telemetry manager")
            telemetry_manager.start()
            return jsonify({'success': True, 'message': 'Connected successfully'})
        return jsonify({'success': False, 'message': 'Connection failed internally'})
    except Exception as e:
        print(f"[API] Connect error: {e}")
        return handle_error(e)


@api_bp.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from the drone."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    telemetry_manager = current_app.telemetry_manager
    
    try:
        telemetry_manager.stop()
        drone_controller.disconnect()
        return jsonify({'success': True, 'message': 'Disconnected successfully'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/arm', methods=['POST'])
def arm():
    """Arm the drone."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        success = drone_controller.arm()
        return jsonify({'success': success, 'message': 'Armed' if success else 'Failed to arm'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/disarm', methods=['POST'])
def disarm():
    """Disarm the drone."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        success = drone_controller.disarm()
        return jsonify({'success': success, 'message': 'Disarmed' if success else 'Failed to disarm'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/takeoff', methods=['POST'])
def takeoff():
    """Initiate takeoff."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    data = request.get_json(silent=True) or {}
    altitude = data.get('altitude', config.flight.DEFAULT_TAKEOFF_ALTITUDE)
    
    try:
        success = drone_controller.takeoff(altitude)
        return jsonify({'success': success, 'message': f'Takeoff to {altitude}m' if success else 'Takeoff failed'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/land', methods=['POST'])
def land():
    """Initiate landing."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        success = drone_controller.land()
        return jsonify({'success': success, 'message': 'Landing initiated' if success else 'Land failed'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/rtl', methods=['POST'])
def rtl():
    """Initiate Return to Launch."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        success = drone_controller.set_mode("RTL")
        return jsonify({'success': success, 'message': 'RTL initiated' if success else 'RTL failed'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/mode', methods=['POST'])
def set_mode():
    """Set flight mode."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    data = request.get_json(silent=True) or {}
    mode = data.get('mode')
    
    if not mode:
        return jsonify({'success': False, 'message': 'Mode not specified'})
    
    try:
        success = drone_controller.set_mode(mode)
        return jsonify({'success': success, 'message': f'Mode set to {mode}' if success else 'Mode change failed'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/mission/list')
def list_missions():
    """List available missions."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        missions = drone_controller.list_missions()
        return jsonify({'success': True, 'missions': missions})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/mission/load', methods=['POST'])
def load_mission():
    """Load a mission file."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    data = request.get_json(silent=True) or {}
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'message': 'Filename not specified'})
    
    try:
        success = drone_controller.load_mission(filename)
        return jsonify({'success': success, 'message': f'Mission {filename} loaded' if success else 'Mission load failed'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/mission/start', methods=['POST'])
def start_mission():
    """Start the loaded mission."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        success = drone_controller.start_mission()
        return jsonify({'success': success, 'message': 'Mission started' if success else 'Mission start failed'})
    except Exception as e:
        return handle_error(e)


# Camera API endpoints
@api_bp.route('/api/camera/photo', methods=['POST'])
def take_photo():
    """Trigger camera photo capture."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        success = drone_controller.take_photo()
        return jsonify({'success': success, 'message': 'Photo captured' if success else 'Photo capture failed'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/camera/video/start', methods=['POST'])
def start_video():
    """Start video recording."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        success = drone_controller.start_video()
        return jsonify({'success': success, 'message': 'Video recording started' if success else 'Video start failed'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/camera/video/stop', methods=['POST'])
def stop_video():
    """Stop video recording."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        success = drone_controller.stop_video()
        return jsonify({'success': success, 'message': 'Video recording stopped' if success else 'Video stop failed'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/camera/status')
def camera_status():
    """Get camera status."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        status = drone_controller.get_camera_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/camera/mode', methods=['POST'])
def set_camera_mode():
    """Set camera mode."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    data = request.get_json(silent=True) or {}
    mode = data.get('mode')
    
    if not mode:
        return jsonify({'success': False, 'message': 'Mode not specified'})
    
    try:
        success = drone_controller.set_camera_mode(mode)
        return jsonify({'success': success, 'message': f'Camera mode set to {mode}' if success else 'Camera mode change failed'})
    except Exception as e:
        return handle_error(e)


# Failsafe API endpoints
@api_bp.route('/api/failsafe/status')
def failsafe_status():
    """Get failsafe system status."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        status = drone_controller.get_failsafe_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/failsafe/check')
def check_failsafe():
    """Run all failsafe checks."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        results = drone_controller.check_all_failsafe()
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/failsafe/reset', methods=['POST'])
def reset_failsafe():
    """Reset failsafe state."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        drone_controller.reset_failsafe()
        return jsonify({'success': True, 'message': 'Failsafe state reset'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/failsafe/trigger', methods=['POST'])
def trigger_failsafe():
    """Manually trigger failsafe."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    data = request.get_json(silent=True) or {}
    level = data.get('level')
    reason = data.get('reason', 'Manual trigger')
    
    if not level:
        return jsonify({'success': False, 'message': 'Failsafe level not specified'})
    
    try:
        drone_controller.trigger_failsafe(level, reason)
        return jsonify({'success': True, 'message': f'Failsafe {level} triggered: {reason}'})
    except Exception as e:
        return handle_error(e)


# Health check endpoints
@api_bp.route('/api/health')
def health_check():
    """Basic health check endpoint."""
    try:
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@api_bp.route('/api/health/detailed')
def detailed_health_check():
    """Detailed health check with system metrics."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    telemetry_manager = current_app.telemetry_manager
    
    try:
        # System metrics
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'memory_total': memory.total,
                'disk_percent': disk.percent,
                'disk_free': disk.free,
                'disk_total': disk.total
            }
        else:
            system_metrics = {
                'cpu_percent': None,
                'memory_percent': None,
                'memory_available': None,
                'memory_total': None,
                'disk_percent': None,
                'disk_free': None,
                'disk_total': None,
                'message': 'psutil not installed - system metrics unavailable'
            }
        
        # Drone connection status
        drone_connected = drone_controller._connected if hasattr(drone_controller, '_connected') else False
        
        # Telemetry manager status
        telemetry_running = telemetry_manager.running if hasattr(telemetry_manager, 'running') else False
        
        health_status = {
            'success': True,
            'timestamp': time.time(),
            'system': system_metrics,
            'drone': {
                'connected': drone_connected,
                'initialized': getattr(drone_controller.drone, '_initialized', False) if hasattr(drone_controller, 'drone') else False
            },
            'services': {
                'telemetry_manager': {
                    'running': telemetry_running,
                    'thread_alive': telemetry_manager.thread.is_alive() if telemetry_manager.thread else False
                }
            },
            'overall_status': 'healthy' if drone_connected and telemetry_running else 'degraded'
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500


@api_bp.route('/api/health/ready')
def readiness_check():
    """Readiness check - is the system ready to accept requests?"""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        # Check if drone controller is ready
        if not hasattr(drone_controller, 'drone'):
            return jsonify({
                'success': False,
                'status': 'not_ready',
                'reason': 'Drone controller not initialized'
            }), 503
        
        # Check if drone is connected
        drone_connected = drone_controller._connected if hasattr(drone_controller, '_connected') else False
        
        return jsonify({
            'success': True,
            'status': 'ready',
            'drone_connected': drone_connected,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'not_ready',
            'error': str(e)
        }), 503
