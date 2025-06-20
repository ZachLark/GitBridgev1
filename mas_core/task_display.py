#!/usr/bin/env python3
"""
GitBridge Task Display Component
Phase: GBP24
Part: P24P1
Step: P24P1S2
Task: P24P1S2T1 - Task Card Attribution Display

Display attribution information on task cards with avatars, icons, and tooltips.
Implements MAS Lite Protocol v2.1 display requirements.

Author: GitBridge Development Team
Date: 2025-06-20
Schema: [P24P1 Schema]
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .attribution import AttributionManager, ContributorType, ContributionRole
from .utils.logging import MASLogger

logger = MASLogger(__name__)

@dataclass
class TaskCardData:
    """Data structure for task card display."""
    task_id: str
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    attribution_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TaskCardRenderer:
    """
    Renders task cards with attribution information.
    
    Phase: GBP24
    Part: P24P1
    Step: P24P1S2
    Task: P24P1S2T1 - Core Implementation
    
    Features:
    - Display attribution on task cards
    - Show contributor avatars and icons
    - Provide detailed tooltips
    - Support multiple display formats
    """
    
    def __init__(self, attribution_manager: AttributionManager):
        """
        Initialize the task card renderer.
        
        Args:
            attribution_manager: Attribution manager instance
        """
        self.attribution_manager = attribution_manager
        self.contributor_icons = {
            ContributorType.HUMAN: "👤",
            ContributorType.AI: "🤖",
            ContributorType.SYSTEM: "⚙️"
        }
        self.role_icons = {
            ContributionRole.CREATOR: "✨",
            ContributionRole.EDITOR: "✏️",
            ContributionRole.REVIEWER: "🔍",
            ContributionRole.APPROVER: "✅",
            ContributionRole.COORDINATOR: "🎯"
        }
        
        logger.info("[P24P1S2T1] TaskCardRenderer initialized")
    
    def render_task_card(self, task_data: TaskCardData, format_type: str = "html") -> str:
        """
        Render a task card with attribution information.
        
        Args:
            task_data: Task data to render
            format_type: Output format ("html", "markdown", "json")
            
        Returns:
            str: Rendered task card
        """
        # Get attribution data if not provided
        if not task_data.attribution_data:
            task_data.attribution_data = self.attribution_manager.get_attribution_display_data(task_data.task_id)
        
        if format_type == "html":
            return self._render_html_card(task_data)
        elif format_type == "markdown":
            return self._render_markdown_card(task_data)
        elif format_type == "json":
            return self._render_json_card(task_data)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def _render_html_card(self, task_data: TaskCardData) -> str:
        """Render task card in HTML format."""
        attribution = task_data.attribution_data
        
        # Status color mapping
        status_colors = {
            "created": "#6B7280",
            "in_progress": "#3B82F6",
            "review": "#F59E0B",
            "completed": "#10B981",
            "failed": "#EF4444"
        }
        
        status_color = status_colors.get(task_data.status.lower(), "#6B7280")
        
        # Priority color mapping
        priority_colors = {
            "low": "#10B981",
            "medium": "#F59E0B",
            "high": "#EF4444",
            "urgent": "#DC2626"
        }
        
        priority_color = priority_colors.get(task_data.priority.lower(), "#6B7280")
        
        html = f"""
        <div class="task-card" data-task-id="{task_data.task_id}">
            <div class="task-header">
                <div class="task-title">
                    <h3>{task_data.title}</h3>
                    <div class="task-meta">
                        <span class="task-id">#{task_data.task_id}</span>
                        <span class="task-status" style="color: {status_color};">{task_data.status}</span>
                        <span class="task-priority" style="color: {priority_color};">{task_data.priority}</span>
                    </div>
                </div>
                <div class="task-attribution">
                    {self._render_attribution_badge(attribution)}
                </div>
            </div>
            
            <div class="task-description">
                <p>{task_data.description}</p>
            </div>
            
            <div class="task-footer">
                <div class="task-timestamps">
                    <span class="created-at">Created: {task_data.created_at.strftime('%Y-%m-%d %H:%M')}</span>
                    <span class="updated-at">Updated: {task_data.updated_at.strftime('%Y-%m-%d %H:%M')}</span>
                </div>
                <div class="task-actions">
                    <button class="btn btn-primary" onclick="viewTaskDetails('{task_data.task_id}')">View Details</button>
                    <button class="btn btn-secondary" onclick="viewAttribution('{task_data.task_id}')">Attribution</button>
                </div>
            </div>
            
            {self._render_attribution_tooltip(attribution)}
        </div>
        """
        
        return html
    
    def _render_attribution_badge(self, attribution: Dict[str, Any]) -> str:
        """Render attribution badge for task card."""
        if not attribution or "error" in attribution:
            return '<span class="attribution-badge no-attribution">No Attribution</span>'
        
        contributors = attribution.get("contributors", [])
        if not contributors:
            return '<span class="attribution-badge no-attribution">No Contributors</span>'
        
        # Show primary contributor or first contributor
        primary_contributor = attribution.get("primary_contributor")
        if primary_contributor:
            contributor = primary_contributor
        else:
            contributor = contributors[0]
        
        contributor_type = contributor.get("type", "unknown")
        icon = self.contributor_icons.get(ContributorType(contributor_type), "❓")
        
        collaboration_score = attribution.get("collaboration_score", 0.0)
        score_color = self._get_score_color(collaboration_score)
        
        html = f"""
        <div class="attribution-badge" data-task-id="{attribution.get('task_id', '')}">
            <div class="contributor-avatar">
                <img src="{contributor.get('avatar_url', '')}" alt="{contributor.get('name', '')}" 
                     onerror="this.src='{self._get_default_avatar_url(contributor_type)}'">
            </div>
            <div class="contributor-info">
                <span class="contributor-name">{contributor.get('name', 'Unknown')}</span>
                <span class="contributor-type">{icon} {contributor_type.title()}</span>
            </div>
            <div class="collaboration-score" style="color: {score_color};">
                {collaboration_score:.1f}
            </div>
        </div>
        """
        
        return html
    
    def _render_attribution_tooltip(self, attribution: Dict[str, Any]) -> str:
        """Render detailed attribution tooltip."""
        if not attribution or "error" in attribution:
            return ""
        
        contributors = attribution.get("contributors", [])
        timeline = attribution.get("timeline", [])
        
        if not contributors:
            return ""
        
        # Build contributor list
        contributor_html = ""
        for contributor in contributors:
            contributor_type = contributor.get("type", "unknown")
            icon = self.contributor_icons.get(ContributorType(contributor_type), "❓")
            
            contributor_html += f"""
            <div class="tooltip-contributor">
                <div class="contributor-header">
                    <img src="{contributor.get('avatar_url', '')}" alt="{contributor.get('name', '')}"
                         onerror="this.src='{self._get_default_avatar_url(contributor_type)}'">
                    <span class="contributor-name">{contributor.get('name', 'Unknown')}</span>
                    <span class="contributor-type">{icon}</span>
                </div>
                <div class="contributor-stats">
                    <span>Contributions: {contributor.get('contributions', 0)}</span>
                    <span>Avg Confidence: {contributor.get('avg_confidence', 0.0):.2f}</span>
                </div>
            </div>
            """
        
        # Build timeline
        timeline_html = ""
        for entry in timeline[-5:]:  # Show last 5 entries
            contributor = entry.get("contributor", {})
            contributor_type = contributor.get("type", "unknown")
            icon = self.contributor_icons.get(ContributorType(contributor_type), "❓")
            role_icon = self.role_icons.get(ContributionRole(entry.get("role", "")), "📝")
            
            timestamp = datetime.fromisoformat(entry.get("timestamp", "")).strftime('%H:%M')
            
            timeline_html += f"""
            <div class="timeline-entry">
                <span class="timeline-time">{timestamp}</span>
                <span class="timeline-icon">{icon}</span>
                <span class="timeline-contributor">{contributor.get('name', 'Unknown')}</span>
                <span class="timeline-role">{role_icon} {entry.get('role', '').title()}</span>
            </div>
            """
        
        html = f"""
        <div class="attribution-tooltip" id="tooltip-{attribution.get('task_id', '')}">
            <div class="tooltip-header">
                <h4>Task Attribution</h4>
                <span class="collaboration-score">Collaboration: {attribution.get('collaboration_score', 0.0):.2f}</span>
            </div>
            
            <div class="tooltip-section">
                <h5>Contributors ({len(contributors)})</h5>
                <div class="contributors-list">
                    {contributor_html}
                </div>
            </div>
            
            <div class="tooltip-section">
                <h5>Recent Activity</h5>
                <div class="timeline-list">
                    {timeline_html}
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _render_markdown_card(self, task_data: TaskCardData) -> str:
        """Render task card in Markdown format."""
        attribution = task_data.attribution_data
        
        # Status and priority badges
        status_badge = f"![{task_data.status}](https://img.shields.io/badge/Status-{task_data.status}-blue)"
        priority_badge = f"![{task_data.priority}](https://img.shields.io/badge/Priority-{task_data.priority}-orange)"
        
        # Attribution info
        if attribution and "error" not in attribution:
            contributors = attribution.get("contributors", [])
            if contributors:
                primary_contributor = attribution.get("primary_contributor") or contributors[0]
                contributor_type = primary_contributor.get("type", "unknown")
                icon = self.contributor_icons.get(ContributorType(contributor_type), "❓")
                attribution_badge = f"![{primary_contributor.get('name', 'Unknown')}](https://img.shields.io/badge/Author-{primary_contributor.get('name', 'Unknown')}-green)"
            else:
                attribution_badge = "![No Attribution](https://img.shields.io/badge/Author-Unknown-gray)"
        else:
            attribution_badge = "![No Attribution](https://img.shields.io/badge/Author-Unknown-gray)"
        
        markdown = f"""
# {task_data.title}

{status_badge} {priority_badge} {attribution_badge}

**Task ID:** `{task_data.task_id}`  
**Created:** {task_data.created_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Updated:** {task_data.updated_at.strftime('%Y-%m-%d %H:%M:%S')}

## Description

{task_data.description}

## Attribution

{self._render_markdown_attribution(attribution)}

---
*Generated by GitBridge Task Display Component*
        """
        
        return markdown.strip()
    
    def _render_markdown_attribution(self, attribution: Dict[str, Any]) -> str:
        """Render attribution information in Markdown format."""
        if not attribution or "error" in attribution:
            return "No attribution data available."
        
        contributors = attribution.get("contributors", [])
        if not contributors:
            return "No contributors found."
        
        markdown = f"**Collaboration Score:** {attribution.get('collaboration_score', 0.0):.2f}\n\n"
        markdown += "### Contributors\n\n"
        
        for contributor in contributors:
            contributor_type = contributor.get("type", "unknown")
            icon = self.contributor_icons.get(ContributorType(contributor_type), "❓")
            
            markdown += f"- **{contributor.get('name', 'Unknown')}** {icon} ({contributor_type.title()})\n"
            markdown += f"  - Contributions: {contributor.get('contributions', 0)}\n"
            markdown += f"  - Avg Confidence: {contributor.get('avg_confidence', 0.0):.2f}\n\n"
        
        # Add timeline
        timeline = attribution.get("timeline", [])
        if timeline:
            markdown += "### Recent Activity\n\n"
            for entry in timeline[-5:]:  # Show last 5 entries
                contributor = entry.get("contributor", {})
                contributor_type = contributor.get("type", "unknown")
                icon = self.contributor_icons.get(ContributorType(contributor_type), "❓")
                role_icon = self.role_icons.get(ContributionRole(entry.get("role", "")), "📝")
                
                timestamp = datetime.fromisoformat(entry.get("timestamp", "")).strftime('%H:%M')
                
                markdown += f"- **{timestamp}** {icon} {contributor.get('name', 'Unknown')} {role_icon} {entry.get('role', '').title()}\n"
        
        return markdown
    
    def _render_json_card(self, task_data: TaskCardData) -> str:
        """Render task card in JSON format."""
        card_data = {
            "task_id": task_data.task_id,
            "title": task_data.title,
            "description": task_data.description,
            "status": task_data.status,
            "priority": task_data.priority,
            "created_at": task_data.created_at.isoformat(),
            "updated_at": task_data.updated_at.isoformat(),
            "attribution": task_data.attribution_data,
            "metadata": task_data.metadata
        }
        
        return json.dumps(card_data, indent=2, default=str)
    
    def _get_score_color(self, score: float) -> str:
        """Get color for collaboration score."""
        if score >= 0.8:
            return "#10B981"  # Green
        elif score >= 0.6:
            return "#F59E0B"  # Yellow
        elif score >= 0.4:
            return "#EF4444"  # Red
        else:
            return "#6B7280"  # Gray
    
    def _get_default_avatar_url(self, contributor_type: str) -> str:
        """Get default avatar URL for contributor type."""
        if contributor_type == "human":
            return "https://via.placeholder.com/40x40/4F46E5/FFFFFF?text=👤"
        elif contributor_type == "ai":
            return "https://via.placeholder.com/40x40/059669/FFFFFF?text=🤖"
        else:
            return "https://via.placeholder.com/40x40/6B7280/FFFFFF?text=⚙️"
    
    def generate_css_styles(self) -> str:
        """Generate CSS styles for task cards."""
        css = """
        .task-card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            background: white;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            transition: box-shadow 0.2s ease;
        }
        
        .task-card:hover {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }
        
        .task-title h3 {
            margin: 0 0 4px 0;
            font-size: 18px;
            font-weight: 600;
            color: #111827;
        }
        
        .task-meta {
            display: flex;
            gap: 8px;
            font-size: 12px;
            color: #6B7280;
        }
        
        .task-id {
            font-family: monospace;
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
        }
        
        .attribution-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px;
            background: #f9fafb;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }
        
        .attribution-badge:hover {
            background: #f3f4f6;
        }
        
        .contributor-avatar img {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            object-fit: cover;
        }
        
        .contributor-info {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        
        .contributor-name {
            font-size: 14px;
            font-weight: 500;
            color: #111827;
        }
        
        .contributor-type {
            font-size: 12px;
            color: #6B7280;
        }
        
        .collaboration-score {
            font-size: 12px;
            font-weight: 600;
            padding: 2px 6px;
            background: #f3f4f6;
            border-radius: 4px;
        }
        
        .task-description {
            margin-bottom: 12px;
        }
        
        .task-description p {
            margin: 0;
            color: #374151;
            line-height: 1.5;
        }
        
        .task-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: #6B7280;
        }
        
        .task-timestamps {
            display: flex;
            gap: 12px;
        }
        
        .task-actions {
            display: flex;
            gap: 8px;
        }
        
        .btn {
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }
        
        .btn-primary {
            background: #3B82F6;
            color: white;
        }
        
        .btn-primary:hover {
            background: #2563EB;
        }
        
        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
        }
        
        .btn-secondary:hover {
            background: #e5e7eb;
        }
        
        .attribution-tooltip {
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            width: 300px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            padding: 16px;
        }
        
        .attribution-badge:hover + .attribution-tooltip,
        .attribution-tooltip:hover {
            display: block;
        }
        
        .tooltip-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .tooltip-header h4 {
            margin: 0;
            font-size: 14px;
            font-weight: 600;
        }
        
        .tooltip-section {
            margin-bottom: 12px;
        }
        
        .tooltip-section h5 {
            margin: 0 0 8px 0;
            font-size: 12px;
            font-weight: 600;
            color: #374151;
        }
        
        .contributors-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .tooltip-contributor {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px;
            background: #f9fafb;
            border-radius: 4px;
        }
        
        .contributor-header {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .contributor-header img {
            width: 24px;
            height: 24px;
            border-radius: 50%;
        }
        
        .contributor-stats {
            display: flex;
            flex-direction: column;
            gap: 2px;
            font-size: 11px;
            color: #6B7280;
        }
        
        .timeline-list {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .timeline-entry {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            color: #6B7280;
        }
        
        .timeline-time {
            font-family: monospace;
            color: #9CA3AF;
        }
        
        .no-attribution {
            color: #9CA3AF;
            font-style: italic;
        }
        """
        
        return css


def main():
    """Main function for testing task card rendering."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitBridge Task Card Renderer')
    parser.add_argument('--task-id', required=True, help='Task ID to render')
    parser.add_argument('--format', choices=['html', 'markdown', 'json'], default='html',
                       help='Output format')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Initialize attribution manager
    attribution_manager = AttributionManager()
    
    # Create sample task data
    task_data = TaskCardData(
        task_id=args.task_id,
        title="Sample Task",
        description="This is a sample task for testing the task card renderer.",
        status="in_progress",
        priority="medium",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Create renderer
    renderer = TaskCardRenderer(attribution_manager)
    
    # Render task card
    result = renderer.render_task_card(task_data, args.format)
    
    # Output result
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
        print(f"Task card rendered to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main() 