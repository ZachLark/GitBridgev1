#!/usr/bin/env python3
"""
GitBridge Agent Routes
Phase: GBP24
Part: P24P4
Step: P24P4S2
Task: P24P4S2T1 - Agent Routes Implementation

Agent-specific routes for collaboration and task management.
Implements MAS Lite Protocol v2.1 agent interface requirements.

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

from mas_core.attribution import AttributionManager, ContributorType, ContributionRole
from mas_core.changelog import ChangelogManager, ChangeType
from mas_core.activity_feed import ActivityFeedManager, ActivityType, ActivityPriority

logger = logging.getLogger(__name__)

# Create blueprint
agent_bp = Blueprint('agent', __name__)

# Initialize managers
attribution_manager = AttributionManager()
changelog_manager = ChangelogManager(attribution_manager=attribution_manager)
activity_feed_manager = ActivityFeedManager(
    attribution_manager=attribution_manager,
    changelog_manager=changelog_manager
)

@agent_bp.route('/api/agent/register', methods=['POST'])
def register_agent():
    """Register a new AI agent contributor."""
    try:
        data = request.get_json()
        
        name = data.get('name')
        agent_type = data.get('agent_type', 'ai')
        avatar_url = data.get('avatar_url')
        metadata = data.get('metadata', {})
        
        if not name:
            return jsonify({"error": "Agent name is required"}), 400
        
        contributor_id = attribution_manager.register_contributor(
            name=name,
            contributor_type=ContributorType(agent_type),
            avatar_url=avatar_url,
            metadata=metadata
        )
        
        # Add activity
        activity_feed_manager.add_activity(
            feed_id="main",
            activity_type=ActivityType.SYSTEM_NOTIFICATION,
            contributor_id=contributor_id,
            content=f"New AI agent '{name}' registered",
            priority=ActivityPriority.MEDIUM
        )
        
        return jsonify({
            "contributor_id": contributor_id,
            "status": "registered",
            "message": f"Agent '{name}' registered successfully"
        })
        
    except Exception as e:
        logger.error(f"Agent registration error: {e}")
        return jsonify({"error": str(e)}), 500

@agent_bp.route('/api/agent/contribute', methods=['POST'])
def agent_contribution():
    """Record an agent contribution to a task."""
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
        
        # Add contribution
        contribution_id = attribution_manager.add_contribution(
            task_id=task_id,
            contributor_id=contributor_id,
            role=ContributionRole(role),
            content=content,
            confidence_score=confidence_score,
            token_usage=token_usage,
            metadata=metadata
        )
        
        # Add activity
        contributor_info = attribution_manager.get_contributor_info(contributor_id)
        contributor_name = contributor_info.name if contributor_info else "Unknown"
        
        activity_feed_manager.add_activity(
            feed_id="main",
            activity_type=ActivityType.TASK_UPDATED,
            contributor_id=contributor_id,
            task_id=task_id,
            content=f"Agent '{contributor_name}' contributed to task {task_id}",
            priority=ActivityPriority.MEDIUM
        )
        
        return jsonify({
            "contribution_id": contribution_id,
            "status": "contributed",
            "message": "Contribution recorded successfully"
        })
        
    except Exception as e:
        logger.error(f"Agent contribution error: {e}")
        return jsonify({"error": str(e)}), 500

@agent_bp.route('/api/agent/revision', methods=['POST'])
def agent_revision():
    """Record an agent revision to a task."""
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
        
        # Add revision
        revision_id = changelog_manager.add_revision(
            task_id=task_id,
            contributor_id=contributor_id,
            description=description,
            file_changes=file_changes,
            confidence_score=confidence_score,
            token_usage=token_usage,
            metadata=metadata
        )
        
        # Add activity
        contributor_info = attribution_manager.get_contributor_info(contributor_id)
        contributor_name = contributor_info.name if contributor_info else "Unknown"
        
        activity_feed_manager.add_activity(
            feed_id="main",
            activity_type=ActivityType.FILE_MODIFIED,
            contributor_id=contributor_id,
            task_id=task_id,
            content=f"Agent '{contributor_name}' made revision to task {task_id}",
            priority=ActivityPriority.MEDIUM
        )
        
        return jsonify({
            "revision_id": revision_id,
            "status": "revised",
            "message": "Revision recorded successfully"
        })
        
    except Exception as e:
        logger.error(f"Agent revision error: {e}")
        return jsonify({"error": str(e)}), 500

@agent_bp.route('/api/agent/activity', methods=['POST'])
def agent_activity():
    """Record an agent activity."""
    try:
        data = request.get_json()
        
        activity_type = data.get('activity_type')
        contributor_id = data.get('contributor_id')
        content = data.get('content', '')
        task_id = data.get('task_id')
        file_path = data.get('file_path')
        priority = data.get('priority', 'medium')
        metadata = data.get('metadata', {})
        
        if not all([activity_type, contributor_id, content]):
            return jsonify({"error": "activity_type, contributor_id, and content are required"}), 400
        
        # Add activity
        activity_id = activity_feed_manager.add_activity(
            feed_id="main",
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
            "status": "recorded",
            "message": "Activity recorded successfully"
        })
        
    except Exception as e:
        logger.error(f"Agent activity error: {e}")
        return jsonify({"error": str(e)}), 500

@agent_bp.route('/api/agent/status/<contributor_id>')
def agent_status(contributor_id):
    """Get agent status and recent activities."""
    try:
        # Get contributor info
        contributor_info = attribution_manager.get_contributor_info(contributor_id)
        if not contributor_info:
            return jsonify({"error": "Contributor not found"}), 404
        
        # Get recent contributions
        recent_contributions = attribution_manager.get_contributor_contributions(contributor_id)
        
        # Get recent activities
        recent_activities = activity_feed_manager.get_feed_activities(
            "main", limit=10, contributor_id=contributor_id
        )
        
        # Calculate statistics
        total_contributions = len(recent_contributions)
        total_tasks = len(set(c.task_id for c in recent_contributions))
        
        return jsonify({
            "contributor": {
                "id": contributor_info.contributor_id,
                "name": contributor_info.name,
                "type": contributor_info.contributor_type.value,
                "avatar_url": contributor_info.avatar_url,
                "created_at": contributor_info.created_at.isoformat()
            },
            "statistics": {
                "total_contributions": total_contributions,
                "total_tasks": total_tasks,
                "recent_activities": len(recent_activities)
            },
            "recent_contributions": [
                {
                    "contribution_id": c.contribution_id,
                    "task_id": c.task_id,
                    "role": c.role.value,
                    "timestamp": c.timestamp.isoformat(),
                    "confidence_score": c.confidence_score
                }
                for c in recent_contributions[:5]
            ],
            "recent_activities": [
                {
                    "activity_id": a.activity_id,
                    "activity_type": a.activity_type.value,
                    "content": a.content,
                    "timestamp": a.timestamp.isoformat(),
                    "priority": a.priority.value
                }
                for a in recent_activities
            ]
        })
        
    except Exception as e:
        logger.error(f"Agent status error: {e}")
        return jsonify({"error": str(e)}), 500

@agent_bp.route('/api/agent/collaboration/<task_id>')
def task_collaboration(task_id):
    """Get collaboration information for a specific task."""
    try:
        # Get task attribution
        attribution_data = attribution_manager.get_attribution_display_data(task_id)
        
        # Get task changelog
        changelog = changelog_manager.get_task_changelog(task_id)
        
        # Get recent activities for this task
        recent_activities = activity_feed_manager.get_feed_activities(
            "main", limit=20, offset=0
        )
        task_activities = [a for a in recent_activities if a.task_id == task_id]
        
        return jsonify({
            "task_id": task_id,
            "attribution": attribution_data,
            "changelog": changelog.__dict__ if changelog else None,
            "recent_activities": [
                {
                    "activity_id": a.activity_id,
                    "activity_type": a.activity_type.value,
                    "contributor_id": a.contributor_id,
                    "content": a.content,
                    "timestamp": a.timestamp.isoformat(),
                    "priority": a.priority.value
                }
                for a in task_activities
            ]
        })
        
    except Exception as e:
        logger.error(f"Task collaboration error: {e}")
        return jsonify({"error": str(e)}), 500 