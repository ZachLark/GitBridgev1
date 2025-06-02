#!/usr/bin/env python3
"""Route handlers for GitBridge WebUI."""

from flask import Blueprint, render_template, jsonify
from flask_socketio import SocketIO, emit
from pathlib import Path
import json
import time
from typing import Dict, List, Any
from collections import deque
from datetime import datetime, timedelta

# Create blueprint
webui = Blueprint('webui', __name__)
socketio = SocketIO()

# Store recent tasks and metrics
recent_tasks: deque = deque(maxlen=100)
processing_rates: deque = deque(maxlen=60)  # 1 minute of rate data
last_update = datetime.now()

@webui.route('/')
def dashboard():
    """Render the main dashboard."""
    return render_template('dashboard.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('connected', {'status': 'success'})

@socketio.on('request_initial_data')
def handle_initial_data():
    """Send initial data to client."""
    tasks = list(recent_tasks)
    metrics = calculate_metrics()
    emit('task_update', {
        'tasks': tasks,
        'metrics': metrics
    })

def calculate_metrics() -> Dict[str, Any]:
    """Calculate current metrics."""
    total = len(recent_tasks)
    pending = sum(1 for task in recent_tasks if task['status'] == 'pending')
    processing = sum(1 for task in recent_tasks if task['status'] == 'processing')
    completed = sum(1 for task in recent_tasks if task['status'] == 'completed')
    failed = sum(1 for task in recent_tasks if task['status'] == 'failed')
    
    # Calculate processing rate (tasks/second)
    rate = 0
    if processing_rates:
        rate = sum(processing_rates) / len(processing_rates)
    
    return {
        'total': total,
        'pending': pending,
        'processing': processing,
        'completed': completed,
        'failed': failed,
        'rate': round(rate, 2)
    }

def update_task_status(task_id: str, status: str):
    """Update task status and notify clients."""
    global last_update
    
    # Update task status
    for task in recent_tasks:
        if task['task_id'] == task_id:
            task['status'] = status
            break
    
    # Calculate processing rate
    now = datetime.now()
    time_diff = (now - last_update).total_seconds()
    if time_diff >= 1.0:  # Update rate every second
        completed_in_window = sum(
            1 for task in recent_tasks
            if task['status'] == 'completed'
            and (now - datetime.fromisoformat(task['completed_at'])) <= timedelta(seconds=1)
        )
        processing_rates.append(completed_in_window)
        last_update = now
    
    # Notify clients
    socketio.emit('task_update', {
        'tasks': list(recent_tasks),
        'metrics': calculate_metrics()
    })

def add_task(task: Dict[str, Any]):
    """Add new task and notify clients."""
    task['created_at'] = datetime.now().isoformat()
    task['status'] = 'pending'
    recent_tasks.append(task)
    
    # Notify clients
    socketio.emit('task_update', {
        'tasks': list(recent_tasks),
        'metrics': calculate_metrics()
    })

# Register error handlers
@webui.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('errors/404.html'), 404

@webui.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template('errors/500.html'), 500 