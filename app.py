#!/usr/bin/env python3
"""GitBridgev1 - Main Application Entry Point."""

import os
import logging
from pathlib import Path
from flask import Flask, render_template
from flask_socketio import SocketIO

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
socketio = SocketIO(app)

# Create required directories
Path('logs').mkdir(exist_ok=True)
Path('messages').mkdir(exist_ok=True)

# Import routes after app initialization
from webui.routes import *
from agent.routes import *
from mas_core.routes import *

@app.route('/')
def index():
    """Render main dashboard."""
    return render_template('dashboard.html')

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    logger.info('Starting GitBridgev1...')
    socketio.run(app, 
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10002)),
        debug=True
    ) 