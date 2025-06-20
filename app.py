#!/usr/bin/env python3
"""
GitBridgev1 - Main Application Entry Point.

This module serves as the main entry point for the GitBridge application,
implementing the MAS Lite Protocol v2.1 for agent collaboration and task management.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gitbridge.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
    template_folder='webui/templates',
    static_folder='webui/static'
)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev_key_replace_in_prod')
socketio = SocketIO(app, cors_allowed_origins="*")

# Create required directories
Path('logs').mkdir(exist_ok=True)
Path('messages').mkdir(exist_ok=True)
Path('attribution_data').mkdir(exist_ok=True)
Path('changelog_data').mkdir(exist_ok=True)
Path('activity_data').mkdir(exist_ok=True)

# Import routes after app initialization
from webui.routes import webui_bp, register_socketio_events
from agent.routes import agent_bp
from mas_core.routes import mas_core_bp

# Register blueprints
app.register_blueprint(webui_bp)
app.register_blueprint(agent_bp)
app.register_blueprint(mas_core_bp)

# Register WebSocket events
register_socketio_events(socketio)

@app.route('/')
def index():
    """Render main dashboard."""
    return render_template('dashboard.html')

@app.route('/startup')
def startup():
    """User-friendly startup page."""
    return render_template('startup.html')

@app.route('/api/start-demo', methods=['POST'])
def start_demo():
    """API endpoint to start the demo."""
    try:
        # Import demo functionality
        from phase24_demo import Phase24Demo
        
        # Start demo in background
        demo = Phase24Demo()
        demo.setup_demo_data()
        
        return jsonify({
            "success": True,
            "message": "Demo started successfully!",
            "redirect": url_for('index')
        })
    except Exception as e:
        logger.error(f"Demo start error: {e}")
        return jsonify({
            "success": False,
            "message": f"Error starting demo: {str(e)}"
        }), 500

@app.route('/api/check-status')
def check_status():
    """Check if the system is ready."""
    try:
        # Check if core components are available
        from mas_core.attribution import AttributionManager
        from mas_core.activity_feed import ActivityFeedManager
        
        attribution_manager = AttributionManager()
        activity_feed_manager = ActivityFeedManager()
        
        return jsonify({
            "status": "ready",
            "contributors": len(attribution_manager.contributors),
            "activities": len(activity_feed_manager.feeds.get("main", {}).activities if activity_feed_manager.feeds.get("main") else []),
            "message": "System is ready for demo"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"System check failed: {str(e)}"
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "phase": "GBP24", "version": "1.0.0"}

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port."""
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GitBridge Phase 24 Demo Server')
    parser.add_argument('--port', type=int, default=None, help='Port to run the server on')
    parser.add_argument('--auto-port', action='store_true', help='Automatically find an available port')
    args = parser.parse_args()
    
    # Determine port
    if args.port:
        port = args.port
    elif args.auto_port:
        port = find_available_port()
        if port is None:
            logger.error("No available ports found")
            sys.exit(1)
    else:
        # Try default port, fallback to auto-find
        port = find_available_port(5000, 1) or find_available_port(5001, 10)
        if port is None:
            logger.error("No available ports found")
            sys.exit(1)
    
    logger.info(f"Starting GitBridge Phase 24 server on port {port}")
    print(f"\n🚀 GitBridge Phase 24 Demo Server")
    print(f"📍 URL: http://localhost:{port}")
    print(f"🎯 Demo: http://localhost:{port}/startup")
    print(f"📊 Dashboard: http://localhost:{port}/")
    print(f"💚 Health: http://localhost:{port}/health")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False) 