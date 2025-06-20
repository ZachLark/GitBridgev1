#!/usr/bin/env python3
"""
GitBridge Web UI Routes
Phase: GBP24
Part: P24P4
Step: P24P4S1
Task: P24P4S1T1 - Web UI Routes Implementation

Web interface routes for collaboration and attribution features.
Implements MAS Lite Protocol v2.1 web interface requirements.

Author: GitBridge Development Team
Date: 2025-06-20
Schema: [P24P4 Schema]
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import emit, join_room, leave_room
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mas_core.attribution import AttributionManager, ContributorType, ContributionRole
from mas_core.changelog import ChangelogManager, ChangeType
from mas_core.diff_viewer import DiffViewer
from mas_core.activity_feed import ActivityFeedManager, ActivityType, ActivityPriority
from mas_core.task_display import TaskCardRenderer, TaskCardData

logger = logging.getLogger(__name__)

# Create blueprints
webui_bp = Blueprint('webui', __name__)

# Initialize managers
attribution_manager = AttributionManager()
changelog_manager = ChangelogManager(attribution_manager=attribution_manager)
diff_viewer = DiffViewer(changelog_manager=changelog_manager)
activity_feed_manager = ActivityFeedManager(
    attribution_manager=attribution_manager,
    changelog_manager=changelog_manager
)
task_card_renderer = TaskCardRenderer(attribution_manager)

@webui_bp.route('/')
def dashboard():
    """Main dashboard with collaboration overview."""
    try:
        # Get recent activities
        recent_activities = activity_feed_manager.get_feed_activities(
            "main", limit=20, offset=0
        )
        
        # Get collaboration statistics
        collaboration_stats = {
            "total_contributors": len(attribution_manager.contributors),
            "total_tasks": len(attribution_manager.task_attributions),
            "recent_activities": len(recent_activities),
            "active_collaborations": len([a for a in recent_activities if "collaboration" in a.activity_type.value])
        }
        
        return render_template('dashboard.html', 
                             collaboration_stats=collaboration_stats,
                             recent_activities=recent_activities)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('error.html', error=str(e))

@webui_bp.route('/attribution')
def attribution_overview():
    """Attribution overview page."""
    try:
        task_id = request.args.get('task_id')
        
        if task_id:
            # Single task attribution
            attribution_data = attribution_manager.get_attribution_display_data(task_id)
            return render_template('attribution_detail.html', 
                                 attribution_data=attribution_data,
                                 task_id=task_id)
        else:
            # All attributions
            all_attributions = []
            for task_id in attribution_manager.task_attributions:
                attribution_data = attribution_manager.get_attribution_display_data(task_id)
                all_attributions.append(attribution_data)
            
            return render_template('attribution_overview.html', 
                                 attributions=all_attributions)
    except Exception as e:
        logger.error(f"Attribution overview error: {e}")
        return render_template('error.html', error=str(e))

@webui_bp.route('/changelog')
def changelog_overview():
    """Changelog overview page."""
    try:
        task_id = request.args.get('task_id')
        
        if task_id:
            # Single task changelog
            changelog = changelog_manager.get_task_changelog(task_id)
            if changelog:
                return render_template('changelog_detail.html', 
                                     changelog=changelog,
                                     task_id=task_id)
            else:
                return render_template('error.html', error="Changelog not found")
        else:
            # All changelogs
            all_changelogs = []
            for task_id in changelog_manager.task_changelogs:
                changelog = changelog_manager.get_task_changelog(task_id)
                if changelog:
                    all_changelogs.append(changelog)
            
            return render_template('changelog_overview.html', 
                                 changelogs=all_changelogs)
    except Exception as e:
        logger.error(f"Changelog overview error: {e}")
        return render_template('error.html', error=str(e))

@webui_bp.route('/diff/<task_id>/<int:revision1>/<int:revision2>')
def diff_view(task_id, revision1, revision2):
    """Diff view between two revisions."""
    try:
        comparison = changelog_manager.compare_revisions(task_id, revision1, revision2)
        
        # Generate diff for each file
        diffs = {}
        for file_change in comparison.get('file_changes', []):
            diff_result = diff_viewer.generate_diff(
                file_change.get('old_content'),
                file_change.get('new_content'),
                file_change['file_path']
            )
            diffs[file_change['file_path']] = diff_result
        
        return render_template('diff_view.html',
                             task_id=task_id,
                             revision1=revision1,
                             revision2=revision2,
                             comparison=comparison,
                             diffs=diffs)
    except Exception as e:
        logger.error(f"Diff view error: {e}")
        return render_template('error.html', error=str(e))

@webui_bp.route('/activity-feed')
def activity_feed():
    """Activity feed page."""
    try:
        feed_id = request.args.get('feed_id', 'main')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        activities = activity_feed_manager.get_feed_activities(
            feed_id, limit=limit, offset=offset
        )
        
        return render_template('activity_feed.html',
                             activities=activities,
                             feed_id=feed_id)
    except Exception as e:
        logger.error(f"Activity feed error: {e}")
        return render_template('error.html', error=str(e))

@webui_bp.route('/task/<task_id>')
def task_detail(task_id):
    """Task detail page with attribution and changelog."""
    try:
        # Get task attribution
        attribution_data = attribution_manager.get_attribution_display_data(task_id)
        
        # Get task changelog
        changelog = changelog_manager.get_task_changelog(task_id)
        
        # Create task card data
        task_data = TaskCardData(
            task_id=task_id,
            title=attribution_data.get('task_title', 'Unknown Task'),
            description=attribution_data.get('task_description', ''),
            status=attribution_data.get('task_status', 'unknown'),
            priority=attribution_data.get('task_priority', 'medium'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            attribution_data=attribution_data
        )
        
        # Render task card
        task_card_html = task_card_renderer.render_task_card(task_data, "html")
        
        return render_template('task_detail.html',
                             task_data=task_data,
                             task_card_html=task_card_html,
                             attribution_data=attribution_data,
                             changelog=changelog)
    except Exception as e:
        logger.error(f"Task detail error: {e}")
        return render_template('error.html', error=str(e))

# API Routes
@webui_bp.route('/api/attribution/<task_id>')
def api_attribution(task_id):
    """API endpoint for task attribution data."""
    try:
        attribution_data = attribution_manager.get_attribution_display_data(task_id)
        return jsonify(attribution_data)
    except Exception as e:
        logger.error(f"API attribution error: {e}")
        return jsonify({"error": str(e)}), 500

@webui_bp.route('/api/changelog/<task_id>')
def api_changelog(task_id):
    """API endpoint for task changelog data."""
    try:
        changelog = changelog_manager.get_task_changelog(task_id)
        if changelog:
            return jsonify(changelog.__dict__)
        else:
            return jsonify({"error": "Changelog not found"}), 404
    except Exception as e:
        logger.error(f"API changelog error: {e}")
        return jsonify({"error": str(e)}), 500

@webui_bp.route('/api/activity-feed/<feed_id>')
def api_activity_feed(feed_id):
    """API endpoint for activity feed data."""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        activities = activity_feed_manager.get_feed_activities(
            feed_id, limit=limit, offset=offset
        )
        
        # Convert to serializable format
        activities_data = []
        for activity in activities:
            activity_dict = activity.__dict__.copy()
            activity_dict['timestamp'] = activity.timestamp.isoformat()
            activities_data.append(activity_dict)
        
        return jsonify(activities_data)
    except Exception as e:
        logger.error(f"API activity feed error: {e}")
        return jsonify({"error": str(e)}), 500

@webui_bp.route('/api/diff/<task_id>/<int:revision1>/<int:revision2>')
def api_diff(task_id, revision1, revision2):
    """API endpoint for diff data."""
    try:
        comparison = changelog_manager.compare_revisions(task_id, revision1, revision2)
        
        # Generate diffs
        diffs = {}
        for file_change in comparison.get('file_changes', []):
            diff_result = diff_viewer.generate_diff(
                file_change.get('old_content'),
                file_change.get('new_content'),
                file_change['file_path']
            )
            diffs[file_change['file_path']] = {
                'summary': diff_result.summary,
                'blocks': [block.__dict__ for block in diff_result.blocks]
            }
        
        return jsonify({
            'comparison': comparison,
            'diffs': diffs
        })
    except Exception as e:
        logger.error(f"API diff error: {e}")
        return jsonify({"error": str(e)}), 500

# WebSocket events for real-time updates
def register_socketio_events(socketio):
    """Register WebSocket events for real-time collaboration."""
    
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {'status': 'connected'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('join_task')
    def handle_join_task(data):
        task_id = data.get('task_id')
        if task_id:
            join_room(f"task_{task_id}")
            emit('joined_task', {'task_id': task_id})
    
    @socketio.on('leave_task')
    def handle_leave_task(data):
        task_id = data.get('task_id')
        if task_id:
            leave_room(f"task_{task_id}")
            emit('left_task', {'task_id': task_id})
    
    @socketio.on('subscribe_feed')
    def handle_subscribe_feed(data):
        feed_id = data.get('feed_id', 'main')
        user_id = data.get('user_id', 'anonymous')
        
        success = activity_feed_manager.subscribe_to_feed(feed_id, user_id)
        if success:
            join_room(f"feed_{feed_id}")
            emit('subscribed_feed', {'feed_id': feed_id, 'success': True})
        else:
            emit('subscribed_feed', {'feed_id': feed_id, 'success': False})
    
    @socketio.on('unsubscribe_feed')
    def handle_unsubscribe_feed(data):
        feed_id = data.get('feed_id', 'main')
        user_id = data.get('user_id', 'anonymous')
        
        success = activity_feed_manager.unsubscribe_from_feed(feed_id, user_id)
        if success:
            leave_room(f"feed_{feed_id}")
            emit('unsubscribed_feed', {'feed_id': feed_id, 'success': True})
        else:
            emit('unsubscribed_feed', {'feed_id': feed_id, 'success': False}) 