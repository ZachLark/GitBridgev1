#!/usr/bin/env python3
"""
GitBridge MAS Core Routes
Phase: GBP24
Part: P24P4
Step: P24P4S3
Task: P24P4S3T1 - MAS Core Routes Implementation

Core MAS collaboration and attribution API endpoints.
Implements MAS Lite Protocol v2.1 core interface requirements.

Author: GitBridge Development Team
Date: 2025-06-20
Schema: [P24P4 Schema]
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, session
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .attribution import AttributionManager, ContributorType, ContributionRole
from .changelog import ChangelogManager, ChangeType
from .diff_viewer import DiffViewer
from .activity_feed import ActivityFeedManager, ActivityType, ActivityPriority
from .task_display import TaskCardRenderer, TaskCardData

logger = logging.getLogger(__name__)

# Create blueprint
mas_core_bp = Blueprint('mas_core', __name__)

# Initialize managers
attribution_manager = AttributionManager()
changelog_manager = ChangelogManager(attribution_manager=attribution_manager)
diff_viewer = DiffViewer(changelog_manager=changelog_manager)
activity_feed_manager = ActivityFeedManager(
    attribution_manager=attribution_manager,
    changelog_manager=changelog_manager
)
task_card_renderer = TaskCardRenderer(attribution_manager)

# Attribution API endpoints
@mas_core_bp.route('/api/mas/attribution/register', methods=['POST'])
def register_contributor():
    """Register a new contributor (human or AI)."""
    try:
        data = request.get_json()
        
        name = data.get('name')
        contributor_type = data.get('contributor_type', 'human')
        avatar_url = data.get('avatar_url')
        email = data.get('email')
        metadata = data.get('metadata', {})
        
        if not name:
            return jsonify({"error": "Contributor name is required"}), 400
        
        contributor_id = attribution_manager.register_contributor(
            name=name,
            contributor_type=ContributorType(contributor_type),
            avatar_url=avatar_url,
            email=email,
            metadata=metadata
        )
        
        return jsonify({
            "contributor_id": contributor_id,
            "status": "registered",
            "message": f"Contributor '{name}' registered successfully"
        })
        
    except Exception as e:
        logger.error(f"Contributor registration error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/attribution/contribute', methods=['POST'])
def add_contribution():
    """Add a contribution to a task."""
    try:
        data = request.get_json()
        
        task_id = data.get('task_id')
        contributor_id = data.get('contributor_id')
        role = data.get('role', 'editor')
        content = data.get('content', '')
        confidence_score = data.get('confidence_score', 0.0)
        token_usage = data.get('token_usage', {})
        metadata = data.get('metadata', {})
        
        if not all([task_id, contributor_id, content]):
            return jsonify({"error": "task_id, contributor_id, and content are required"}), 400
        
        contribution_id = attribution_manager.add_contribution(
            task_id=task_id,
            contributor_id=contributor_id,
            role=ContributionRole(role),
            content=content,
            confidence_score=confidence_score,
            token_usage=token_usage,
            metadata=metadata
        )
        
        return jsonify({
            "contribution_id": contribution_id,
            "status": "contributed",
            "message": "Contribution added successfully"
        })
        
    except Exception as e:
        logger.error(f"Contribution error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/attribution/task/<task_id>')
def get_task_attribution(task_id):
    """Get attribution data for a specific task."""
    try:
        attribution_data = attribution_manager.get_attribution_display_data(task_id)
        return jsonify(attribution_data)
        
    except Exception as e:
        logger.error(f"Task attribution error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/attribution/contributor/<contributor_id>')
def get_contributor_info(contributor_id):
    """Get information about a specific contributor."""
    try:
        contributor_info = attribution_manager.get_contributor_info(contributor_id)
        if not contributor_info:
            return jsonify({"error": "Contributor not found"}), 404
        
        return jsonify({
            "contributor_id": contributor_info.contributor_id,
            "name": contributor_info.name,
            "contributor_type": contributor_info.contributor_type.value,
            "avatar_url": contributor_info.avatar_url,
            "email": contributor_info.email,
            "metadata": contributor_info.metadata,
            "created_at": contributor_info.created_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Contributor info error: {e}")
        return jsonify({"error": str(e)}), 500

# Changelog API endpoints
@mas_core_bp.route('/api/mas/changelog/create', methods=['POST'])
def create_task_changelog():
    """Create a new changelog for a task."""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({"error": "task_id is required"}), 400
        
        changelog_id = changelog_manager.create_task_changelog(task_id)
        
        return jsonify({
            "changelog_id": changelog_id,
            "status": "created",
            "message": f"Changelog created for task {task_id}"
        })
        
    except Exception as e:
        logger.error(f"Changelog creation error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/changelog/revision', methods=['POST'])
def add_revision():
    """Add a revision to a task changelog."""
    try:
        data = request.get_json()
        
        task_id = data.get('task_id')
        contributor_id = data.get('contributor_id')
        description = data.get('description', '')
        file_changes = data.get('file_changes', [])
        confidence_score = data.get('confidence_score', 0.0)
        token_usage = data.get('token_usage', {})
        metadata = data.get('metadata', {})
        
        if not all([task_id, contributor_id, description]):
            return jsonify({"error": "task_id, contributor_id, and description are required"}), 400
        
        revision_id = changelog_manager.add_revision(
            task_id=task_id,
            contributor_id=contributor_id,
            description=description,
            file_changes=file_changes,
            confidence_score=confidence_score,
            token_usage=token_usage,
            metadata=metadata
        )
        
        return jsonify({
            "revision_id": revision_id,
            "status": "revised",
            "message": "Revision added successfully"
        })
        
    except Exception as e:
        logger.error(f"Revision error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/changelog/task/<task_id>')
def get_task_changelog(task_id):
    """Get changelog for a specific task."""
    try:
        changelog = changelog_manager.get_task_changelog(task_id)
        if not changelog:
            return jsonify({"error": "Changelog not found"}), 404
        
        return jsonify(changelog.__dict__)
        
    except Exception as e:
        logger.error(f"Task changelog error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/changelog/compare/<task_id>/<int:revision1>/<int:revision2>')
def compare_revisions(task_id, revision1, revision2):
    """Compare two revisions of a task."""
    try:
        comparison = changelog_manager.compare_revisions(task_id, revision1, revision2)
        return jsonify(comparison)
        
    except Exception as e:
        logger.error(f"Revision comparison error: {e}")
        return jsonify({"error": str(e)}), 500

# Diff viewer API endpoints
@mas_core_bp.route('/api/mas/diff/generate', methods=['POST'])
def generate_diff():
    """Generate a diff between two content versions."""
    try:
        data = request.get_json()
        
        old_content = data.get('old_content')
        new_content = data.get('new_content')
        file_path = data.get('file_path', 'unknown')
        context_lines = data.get('context_lines', 3)
        
        if old_content is None and new_content is None:
            return jsonify({"error": "At least one content version is required"}), 400
        
        diff_result = diff_viewer.generate_diff(
            old_content=old_content,
            new_content=new_content,
            file_path=file_path,
            context_lines=context_lines
        )
        
        return jsonify({
            "file_path": diff_result.file_path,
            "summary": diff_result.summary,
            "blocks": [block.__dict__ for block in diff_result.blocks]
        })
        
    except Exception as e:
        logger.error(f"Diff generation error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/diff/render', methods=['POST'])
def render_diff():
    """Render a diff in a specific format."""
    try:
        data = request.get_json()
        
        old_content = data.get('old_content')
        new_content = data.get('new_content')
        file_path = data.get('file_path', 'unknown')
        format_type = data.get('format_type', 'html')
        context_lines = data.get('context_lines', 3)
        
        diff_result = diff_viewer.generate_diff(
            old_content=old_content,
            new_content=new_content,
            file_path=file_path,
            context_lines=context_lines
        )
        
        rendered_diff = diff_viewer.render_diff(diff_result, format_type)
        
        return jsonify({
            "rendered_diff": rendered_diff,
            "format_type": format_type,
            "summary": diff_result.summary
        })
        
    except Exception as e:
        logger.error(f"Diff rendering error: {e}")
        return jsonify({"error": str(e)}), 500

# Activity feed API endpoints
@mas_core_bp.route('/api/mas/activity/create', methods=['POST'])
def create_activity_feed():
    """Create a new activity feed."""
    try:
        data = request.get_json()
        feed_id = data.get('feed_id')
        filters = data.get('filters', {})
        
        if not feed_id:
            return jsonify({"error": "feed_id is required"}), 400
        
        feed_id = activity_feed_manager.create_feed(feed_id, filters)
        
        return jsonify({
            "feed_id": feed_id,
            "status": "created",
            "message": f"Activity feed '{feed_id}' created successfully"
        })
        
    except Exception as e:
        logger.error(f"Activity feed creation error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/activity/add', methods=['POST'])
def add_activity():
    """Add an activity to a feed."""
    try:
        data = request.get_json()
        
        feed_id = data.get('feed_id', 'main')
        activity_type = data.get('activity_type')
        contributor_id = data.get('contributor_id')
        content = data.get('content', '')
        task_id = data.get('task_id')
        file_path = data.get('file_path')
        priority = data.get('priority', 'medium')
        metadata = data.get('metadata', {})
        
        if not all([activity_type, contributor_id, content]):
            return jsonify({"error": "activity_type, contributor_id, and content are required"}), 400
        
        activity_id = activity_feed_manager.add_activity(
            feed_id=feed_id,
            activity_type=ActivityType(activity_type),
            contributor_id=contributor_id,
            content=content,
            task_id=task_id,
            file_path=file_path,
            priority=ActivityPriority(priority),
            metadata=metadata
        )
        
        return jsonify({
            "activity_id": activity_id,
            "status": "added",
            "message": "Activity added successfully"
        })
        
    except Exception as e:
        logger.error(f"Activity addition error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/activity/feed/<feed_id>')
def get_activity_feed(feed_id):
    """Get activities from a specific feed."""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        activity_types = request.args.getlist('activity_types')
        contributor_id = request.args.get('contributor_id')
        priority = request.args.get('priority')
        
        # Convert activity types if provided
        activity_type_list = None
        if activity_types:
            activity_type_list = [ActivityType(at) for at in activity_types]
        
        # Convert priority if provided
        priority_enum = None
        if priority:
            priority_enum = ActivityPriority(priority)
        
        activities = activity_feed_manager.get_feed_activities(
            feed_id=feed_id,
            limit=limit,
            offset=offset,
            activity_types=activity_type_list,
            contributor_id=contributor_id,
            priority=priority_enum
        )
        
        # Convert to serializable format
        activities_data = []
        for activity in activities:
            activity_dict = activity.__dict__.copy()
            activity_dict['timestamp'] = activity.timestamp.isoformat()
            activities_data.append(activity_dict)
        
        return jsonify(activities_data)
        
    except Exception as e:
        logger.error(f"Activity feed error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/activity/subscribe', methods=['POST'])
def subscribe_to_feed():
    """Subscribe to an activity feed."""
    try:
        data = request.get_json()
        feed_id = data.get('feed_id', 'main')
        subscriber_id = data.get('subscriber_id')
        
        if not subscriber_id:
            return jsonify({"error": "subscriber_id is required"}), 400
        
        success = activity_feed_manager.subscribe_to_feed(feed_id, subscriber_id)
        
        return jsonify({
            "success": success,
            "message": f"Subscription {'successful' if success else 'failed'}"
        })
        
    except Exception as e:
        logger.error(f"Feed subscription error: {e}")
        return jsonify({"error": str(e)}), 500

# Task display API endpoints
@mas_core_bp.route('/api/mas/task/render', methods=['POST'])
def render_task_card():
    """Render a task card with attribution information."""
    try:
        data = request.get_json()
        
        task_id = data.get('task_id')
        title = data.get('title', 'Unknown Task')
        description = data.get('description', '')
        status = data.get('status', 'unknown')
        priority = data.get('priority', 'medium')
        format_type = data.get('format_type', 'html')
        
        if not task_id:
            return jsonify({"error": "task_id is required"}), 400
        
        # Create task card data
        task_data = TaskCardData(
            task_id=task_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Render task card
        rendered_card = task_card_renderer.render_task_card(task_data, format_type)
        
        return jsonify({
            "rendered_card": rendered_card,
            "format_type": format_type,
            "task_id": task_id
        })
        
    except Exception as e:
        logger.error(f"Task card rendering error: {e}")
        return jsonify({"error": str(e)}), 500

# Export API endpoints
@mas_core_bp.route('/api/mas/export/attribution')
def export_attribution():
    """Export attribution data."""
    try:
        output_path = request.args.get('output_path', 'attribution_export.json')
        attribution_manager.export_attribution_data(output_path)
        
        return jsonify({
            "status": "exported",
            "output_path": output_path,
            "message": "Attribution data exported successfully"
        })
        
    except Exception as e:
        logger.error(f"Attribution export error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/export/changelog')
def export_changelog():
    """Export changelog data."""
    try:
        output_path = request.args.get('output_path', 'changelog_export.json')
        changelog_manager.export_changelog_data(output_path)
        
        return jsonify({
            "status": "exported",
            "output_path": output_path,
            "message": "Changelog data exported successfully"
        })
        
    except Exception as e:
        logger.error(f"Changelog export error: {e}")
        return jsonify({"error": str(e)}), 500

@mas_core_bp.route('/api/mas/export/activity')
def export_activity():
    """Export activity data."""
    try:
        output_path = request.args.get('output_path', 'activity_export.json')
        activity_feed_manager.export_activity_data(output_path)
        
        return jsonify({
            "status": "exported",
            "output_path": output_path,
            "message": "Activity data exported successfully"
        })
        
    except Exception as e:
        logger.error(f"Activity export error: {e}")
        return jsonify({"error": str(e)}), 500 