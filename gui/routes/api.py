"""
API routes for drone control operations.
Provides REST endpoints for drone control, telemetry, and mission management.
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from drone.config import config
from drone.exceptions import DroneNEAError
from pathlib import Path
import time
from functools import wraps
from collections import defaultdict
import threading
import logging
import hmac

logger = logging.getLogger(__name__)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

api_bp = Blueprint('api', __name__)

# Simple in-memory rate limiter
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, key, limit_per_minute):
        current_time = time.time()
        with self.lock:
            # Remove requests older than 1 minute
            self.requests[key] = [t for t in self.requests[key] if current_time - t < 60]
            if len(self.requests[key]) >= limit_per_minute:
                return False
            self.requests[key].append(current_time)
            return True

rate_limiter = RateLimiter()

def require_auth(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip auth in development mode
        if current_app.config.get('DEBUG', False):
            return f(*args, **kwargs)
        
        expected_key = current_app.config.get('API_KEY')
        if not expected_key:
            logger.error("API_KEY is not set in application configuration.")
            return jsonify({'success': False, 'message': 'Authentication configuration error'}), 500

        # Retrieve API key from X-API-Key header or Bearer token
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                api_key = auth_header.split(' ', 1)[1]

        if not api_key:
            return jsonify({'success': False, 'message': 'API key required'}), 401
        
        # Use constant time comparison to prevent timing attacks
        if not hmac.compare_digest(api_key, expected_key):
            return jsonify({'success': False, 'message': 'Invalid API key'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(f):
    """Decorator to apply rate limiting."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip rate limiting if disabled
        if not current_app.config.get('RATE_LIMIT_ENABLED', True):
            return f(*args, **kwargs)
        
        # Use IP address as rate limit key
        key = request.remote_addr
        limit = current_app.config.get('RATE_LIMIT_PER_MINUTE', 60)
        
        if not rate_limiter.is_allowed(key, limit):
            return jsonify({'success': False, 'message': 'Rate limit exceeded'}), 429
        
        return f(*args, **kwargs)
    return decorated_function


def handle_error(error: Exception) -> tuple:
    """
    Convert exceptions to consistent API error responses.
    Args:
        error: Exception to handle
    Returns:
        tuple: (json_response, status_code)
    """
    if isinstance(error, DroneNEAError):
        logger.warning(f"DroneNEA error: {error}")
        return jsonify({
            'success': False,
            'error': error.to_dict()
        }), 400
    else:
        logger.error(f"Unexpected error: {error}", exc_info=True)
        return jsonify({
            'success': False,
            'error': {
                'error_type': 'InternalServerError',
                'message': 'An unexpected error occurred'
            }
        }), 500


@api_bp.route('/api/connect', methods=['POST'])
@require_auth
@rate_limit
def connect():
    """Connect to the drone."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    telemetry_manager = current_app.telemetry_manager
    
    data = request.get_json(silent=True) or {}
    connection_string = data.get('connection_string')
    baud = data.get('baud')
    timeout = data.get('timeout')
    # Input validation
    if connection_string is not None and not isinstance(connection_string, str):
        return jsonify({'success': False, 'message': 'Connection string must be a string'}), 400
    if baud is not None:
        try:
            baud = int(baud)
            if baud <= 0 or baud > 10000000:
                return jsonify({'success': False, 'message': 'Invalid baud rate'}), 400
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Invalid baud rate'}), 400
    if timeout is not None:
        try:
            timeout = int(timeout)
            if timeout <= 0 or timeout > 300:
                return jsonify({'success': False, 'message': 'Timeout must be between 1 and 300 seconds'}), 400
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Invalid timeout value'}), 400
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
@require_auth
@rate_limit
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


@api_bp.route('/api/status')
@require_auth
def status():
    """Get current drone status."""
    drone_controller = current_app.drone_controller
    return jsonify(drone_controller.get_status())


@api_bp.route('/api/arm', methods=['POST'])
@require_auth
@rate_limit
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
@require_auth
@rate_limit
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
@require_auth
@rate_limit
def takeoff():
    """Initiate takeoff."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    data = request.get_json(silent=True) or {}
    altitude = data.get('altitude', config.flight.DEFAULT_TAKEOFF_ALTITUDE)
    # Input validation
    try:
        altitude = float(altitude)
        if altitude <= 0:
            return jsonify({'success': False, 'message': 'Altitude must be greater than 0'}), 400
        if altitude > config.flight.MAX_ALTITUDE:
            return jsonify({'success': False, 'message': f'Altitude exceeds maximum of {config.flight.MAX_ALTITUDE}m'}), 400
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid altitude value'}), 400
    
    try:
        success = drone_controller.takeoff(altitude)
        return jsonify({'success': success, 'message': f'Takeoff to {altitude}m' if success else 'Takeoff failed'})
    except Exception as e:
        return handle_error(e)

@api_bp.route('/api/guided', methods=['POST'])
@require_auth
@rate_limit
def guided():
    """Initiate guided mode."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    try:
        success = drone_controller.set_mode('GUIDED')
        return jsonify({'success': success, 'message': 'Guided mode initiated.' if success else 'Failed to enter guided mode.'})
    except Exception as e:
        return handle_error(e)

@api_bp.route('/api/land', methods=['POST'])
@require_auth
@rate_limit
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
@require_auth
@rate_limit
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
@require_auth
@rate_limit
def set_mode():
    """Set flight mode."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    data = request.get_json(silent=True) or {}
    mode = data.get('mode')
    
    if not mode:
        return jsonify({'success': False, 'message': 'Mode not specified'}), 400
    
    # Input validation - sanitize mode string
    if not isinstance(mode, str):
        return jsonify({'success': False, 'message': 'Mode must be a string'}), 400
    
    mode = mode.strip().upper()
    # Basic whitelist of common flight modes
    valid_modes = {'STABILIZE', 'ACRO', 'ALT_HOLD', 'AUTO', 'GUIDED', 'LOITER', 'RTL', 'LAND', 'BRAKE', 'POSITION', 'OFFBOARD'}
    if mode not in valid_modes:
        return jsonify({'success': False, 'message': f'Invalid flight mode: {mode}'}), 400
    
    try:
        success = drone_controller.set_mode(mode)
        return jsonify({'success': success, 'message': f'Mode set to {mode}' if success else 'Mode change failed'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/mission/list')
@require_auth
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
@require_auth
@rate_limit
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
@require_auth
@rate_limit
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
@require_auth
@rate_limit
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
@require_auth
@rate_limit
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
@require_auth
@rate_limit
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
@require_auth
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
@require_auth
@rate_limit
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
@require_auth
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
@require_auth
@rate_limit
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
@require_auth
@rate_limit
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
@require_auth
@rate_limit
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


# Camera photo endpoints
@api_bp.route('/api/camera/photos')
@require_auth
@rate_limit
def get_captured_photos():
    """Get list of all captured photos."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        photos = drone_controller.get_captured_photos()
        return jsonify({'success': True, 'photos': photos})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/camera/photos/latest')
@require_auth
@rate_limit
def get_latest_photo():
    """Get the most recently captured photo."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        photo = drone_controller.get_latest_photo()
        if photo:
            return jsonify({'success': True, 'photo': photo})
        else:
            return jsonify({'success': True, 'photo': None, 'message': 'No photos captured'})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/camera/photos/local')
@require_auth
@rate_limit
def get_local_photos():
    """Get list of locally saved photo files."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        photos = drone_controller.get_local_photos()
        return jsonify({'success': True, 'photos': photos})
    except Exception as e:
        return handle_error(e)


@api_bp.route('/api/camera/photos/download/<filename>')
@require_auth
@rate_limit
def download_photo(filename):
    """Download a specific photo file."""
    from flask import current_app
    drone_controller = current_app.drone_controller
    
    try:
        # Path traversal protection - sanitize filename
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
            return jsonify({'success': False, 'message': 'Invalid filename'}), 400
        
        # Prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'message': 'Invalid filename'}), 400
        
        photo_path = Path(config.camera.CAMERA_STORAGE_PATH) / filename
        
        # Ensure the resolved path is still within the storage directory
        photo_path = photo_path.resolve()
        storage_path = Path(config.camera.CAMERA_STORAGE_PATH).resolve()
        
        if not str(photo_path).startswith(str(storage_path)):
            return jsonify({'success': False, 'message': 'Invalid filename'}), 400
        
        if not photo_path.exists():
            return jsonify({'success': False, 'message': 'Photo not found'}), 404
        
        return send_file(photo_path, as_attachment=True)
    except Exception as e:
        return handle_error(e)


# Health check endpoints
@api_bp.route('/api/health')
def health_check():
    """Basic health check endpoint (Unauthenticated for load balancer probes)."""
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
        drone_connected = drone_controller.connected if hasattr(drone_controller, '_connected') else False
        
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
    """Readiness check (Unauthenticated for container orchestration)."""
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
        drone_connected = drone_controller.connected if hasattr(drone_controller, '_connected') else False
        
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