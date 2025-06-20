#!/usr/bin/env python3
"""
GitBridgev1 - Main Application Entry Point.

This module serves as the main entry point for the GitBridge application,
implementing the MAS Lite Protocol v2.1 for agent collaboration and task management.
"""

import os
import logging
from pathlib import Path
from flask import Flask, render_template
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

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "phase": "GBP24", "version": "1.0.0"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting GitBridge Phase 24 server on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False) 