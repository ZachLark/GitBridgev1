#!/usr/bin/env python3
"""
GitBridge Activity Feed Framework
Phase: GBP24
Part: P24P3
Step: P24P3S1
Task: P24P3S1T1 - Activity Feed Framework Implementation

Live display of all edit actions and comments with real-time updates.
Implements MAS Lite Protocol v2.1 activity tracking requirements.

Author: GitBridge Development Team
Date: 2025-06-20
Schema: [P24P3 Schema]
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import os
import sys
import asyncio
from collections import deque

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .attribution import AttributionManager, ContributorType, ContributionRole
from .changelog import ChangelogManager, ChangeType
from .utils.logging import MASLogger

logger = MASLogger(__name__)

class ActivityType(str, Enum):
    """Types of activities."""
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    FILE_MODIFIED = "file_modified"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    COMMENT_ADDED = "comment_added"
    COMMENT_EDITED = "comment_edited"
    MENTION_ADDED = "mention_added"
    COLLABORATION_STARTED = "collaboration_started"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_COMPLETED = "review_completed"
    APPROVAL_GIVEN = "approval_given"
    SYSTEM_NOTIFICATION = "system_notification"

class ActivityPriority(str, Enum):
    """Priority levels for activities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class ActivityItem:
    """Represents an activity item in the feed."""
    activity_id: str
    activity_type: ActivityType
    contributor_id: str
    task_id: Optional[str] = None
    file_path: Optional[str] = None
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: ActivityPriority = ActivityPriority.MEDIUM
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read_by: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)

@dataclass
class ActivityFeed:
    """Complete activity feed for a project or workspace."""
    feed_id: str
    activities: List[ActivityItem]
    subscribers: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class ActivityFeedManager:
    """
    Manages real-time activity feeds and notifications.
    
    Phase: GBP24
    Part: P24P3
    Step: P24P3S1
    Task: P24P3S1T1 - Core Implementation
    
    Features:
    - Live activity tracking
    - Real-time feed updates
    - Activity filtering and search
    - Mention notifications
    - Feed subscriptions
    """
    
    def __init__(
        self,
        storage_path: str = "activity_data",
        attribution_manager: Optional[AttributionManager] = None,
        changelog_manager: Optional[ChangelogManager] = None
    ):
        """
        Initialize the activity feed manager.
        
        Args:
            storage_path: Path to store activity data
            attribution_manager: Optional attribution manager for contributor info
            changelog_manager: Optional changelog manager for file changes
        """
        self.storage_path = storage_path
        self.attribution_manager = attribution_manager or AttributionManager()
        self.changelog_manager = changelog_manager or ChangelogManager()
        self.feeds: Dict[str, ActivityFeed] = {}
        self.subscribers: Dict[str, List[str]] = {}  # feed_id -> [subscriber_ids]
        self.mention_notifications: Dict[str, List[str]] = {}  # user_id -> [activity_ids]
        
        # Real-time update callbacks
        self.update_callbacks: List[callable] = []
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing data
        self._load_data()
        
        logger.info("[P24P3S1T1] ActivityFeedManager initialized")
    
    def _load_data(self):
        """Load existing activity data from storage."""
        try:
            feeds_file = os.path.join(self.storage_path, "activity_feeds.json")
            if os.path.exists(feeds_file):
                with open(feeds_file, 'r') as f:
                    feeds_data = json.load(f)
                    for feed_data in feeds_data:
                        activities = []
                        for activity_data in feed_data['activities']:
                            activity = ActivityItem(
                                activity_id=activity_data['activity_id'],
                                activity_type=ActivityType(activity_data['activity_type']),
                                contributor_id=activity_data['contributor_id'],
                                task_id=activity_data.get('task_id'),
                                file_path=activity_data.get('file_path'),
                                content=activity_data.get('content', ''),
                                metadata=activity_data.get('metadata', {}),
                                priority=ActivityPriority(activity_data.get('priority', 'medium')),
                                timestamp=datetime.fromisoformat(activity_data['timestamp']),
                                read_by=activity_data.get('read_by', []),
                                mentions=activity_data.get('mentions', [])
                            )
                            activities.append(activity)
                        
                        feed = ActivityFeed(
                            feed_id=feed_data['feed_id'],
                            activities=activities,
                            subscribers=feed_data.get('subscribers', []),
                            filters=feed_data.get('filters', {}),
                            created_at=datetime.fromisoformat(feed_data['created_at']),
                            updated_at=datetime.fromisoformat(feed_data['updated_at'])
                        )
                        self.feeds[feed.feed_id] = feed
                        
            logger.info(f"[P24P3S1T1] Loaded {len(self.feeds)} activity feeds")
            
        except Exception as e:
            logger.error(f"[P24P3S1T1] Failed to load activity data: {e}")
    
    def _save_data(self):
        """Save activity data to storage."""
        try:
            feeds_file = os.path.join(self.storage_path, "activity_feeds.json")
            feeds_data = [asdict(feed) for feed in self.feeds.values()]
            with open(feeds_file, 'w') as f:
                json.dump(feeds_data, f, indent=2, default=str)
                
            logger.info(f"[P24P3S1T1] Saved {len(self.feeds)} activity feeds")
            
        except Exception as e:
            logger.error(f"[P24P3S1T1] Failed to save activity data: {e}")
    
    def create_feed(self, feed_id: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new activity feed.
        
        Args:
            feed_id: Feed identifier
            filters: Optional filters for the feed
            
        Returns:
            str: Feed ID
        """
        if feed_id not in self.feeds:
            self.feeds[feed_id] = ActivityFeed(
                feed_id=feed_id,
                activities=[],
                filters=filters or {}
            )
            self.subscribers[feed_id] = []
            self._save_data()
            logger.info(f"[P24P3S1T1] Created activity feed: {feed_id}")
        
        return feed_id
    
    def add_activity(
        self,
        feed_id: str,
        activity_type: ActivityType,
        contributor_id: str,
        content: str,
        task_id: Optional[str] = None,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: ActivityPriority = ActivityPriority.MEDIUM
    ) -> str:
        """
        Add a new activity to a feed.
        
        Args:
            feed_id: Feed identifier
            activity_type: Type of activity
            contributor_id: Contributor ID
            content: Activity content/description
            task_id: Optional task ID
            file_path: Optional file path
            metadata: Optional metadata
            priority: Activity priority
            
        Returns:
            str: Activity ID
        """
        # Ensure feed exists
        self.create_feed(feed_id)
        
        # Generate activity ID
        activity_id = str(uuid.uuid4())
        
        # Extract mentions from content
        mentions = self._extract_mentions(content)
        
        # Create activity item
        activity = ActivityItem(
            activity_id=activity_id,
            activity_type=activity_type,
            contributor_id=contributor_id,
            task_id=task_id,
            file_path=file_path,
            content=content,
            metadata=metadata or {},
            priority=priority,
            mentions=mentions
        )
        
        # Add to feed
        feed = self.feeds[feed_id]
        feed.activities.append(activity)
        feed.updated_at = datetime.now(timezone.utc)
        
        # Process mentions
        for mention in mentions:
            self._add_mention_notification(mention, activity_id)
        
        # Trigger real-time updates
        self._notify_subscribers(feed_id, activity)
        
        self._save_data()
        
        contributor_name = self._get_contributor_name(contributor_id)
        logger.info(f"[P24P3S1T1] Added activity from {contributor_name} to feed {feed_id}")
        return activity_id
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content."""
        mentions = []
        # Simple regex to find @username patterns
        import re
        mention_pattern = r'@(\w+)'
        matches = re.findall(mention_pattern, content)
        
        for match in matches:
            # Try to find contributor by name
            contributor_id = self._find_contributor_by_name(match)
            if contributor_id:
                mentions.append(contributor_id)
        
        return mentions
    
    def _find_contributor_by_name(self, name: str) -> Optional[str]:
        """Find contributor ID by name."""
        if self.attribution_manager:
            for contributor in self.attribution_manager.contributors.values():
                if contributor.name.lower() == name.lower():
                    return contributor.contributor_id
        return None
    
    def _add_mention_notification(self, contributor_id: str, activity_id: str):
        """Add mention notification for a contributor."""
        if contributor_id not in self.mention_notifications:
            self.mention_notifications[contributor_id] = []
        
        if activity_id not in self.mention_notifications[contributor_id]:
            self.mention_notifications[contributor_id].append(activity_id)
    
    def _notify_subscribers(self, feed_id: str, activity: ActivityItem):
        """Notify subscribers of new activity."""
        for callback in self.update_callbacks:
            try:
                callback(feed_id, activity)
            except Exception as e:
                logger.error(f"[P24P3S1T1] Error in update callback: {e}")
    
    def subscribe_to_feed(self, feed_id: str, subscriber_id: str) -> bool:
        """
        Subscribe a user to a feed.
        
        Args:
            feed_id: Feed identifier
            subscriber_id: Subscriber ID
            
        Returns:
            bool: True if subscription successful
        """
        if feed_id not in self.feeds:
            return False
        
        if feed_id not in self.subscribers:
            self.subscribers[feed_id] = []
        
        if subscriber_id not in self.subscribers[feed_id]:
            self.subscribers[feed_id].append(subscriber_id)
            self._save_data()
            logger.info(f"[P24P3S1T1] {subscriber_id} subscribed to feed {feed_id}")
        
        return True
    
    def unsubscribe_from_feed(self, feed_id: str, subscriber_id: str) -> bool:
        """
        Unsubscribe a user from a feed.
        
        Args:
            feed_id: Feed identifier
            subscriber_id: Subscriber ID
            
        Returns:
            bool: True if unsubscription successful
        """
        if feed_id in self.subscribers and subscriber_id in self.subscribers[feed_id]:
            self.subscribers[feed_id].remove(subscriber_id)
            self._save_data()
            logger.info(f"[P24P3S1T1] {subscriber_id} unsubscribed from feed {feed_id}")
            return True
        
        return False
    
    def get_feed_activities(
        self,
        feed_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        activity_types: Optional[List[ActivityType]] = None,
        contributor_id: Optional[str] = None,
        priority: Optional[ActivityPriority] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[ActivityItem]:
        """
        Get activities from a feed with filtering.
        
        Args:
            feed_id: Feed identifier
            limit: Maximum number of activities to return
            offset: Number of activities to skip
            activity_types: Filter by activity types
            contributor_id: Filter by contributor
            priority: Filter by priority
            date_from: Filter by start date
            date_to: Filter by end date
            
        Returns:
            List[ActivityItem]: Filtered activities
        """
        if feed_id not in self.feeds:
            return []
        
        feed = self.feeds[feed_id]
        activities = feed.activities.copy()
        
        # Apply filters
        if activity_types:
            activities = [a for a in activities if a.activity_type in activity_types]
        
        if contributor_id:
            activities = [a for a in activities if a.contributor_id == contributor_id]
        
        if priority:
            activities = [a for a in activities if a.priority == priority]
        
        if date_from:
            activities = [a for a in activities if a.timestamp >= date_from]
        
        if date_to:
            activities = [a for a in activities if a.timestamp <= date_to]
        
        # Sort by timestamp (newest first)
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        if offset:
            activities = activities[offset:]
        
        if limit:
            activities = activities[:limit]
        
        return activities
    
    def get_mentions_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all mentions for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[Dict[str, Any]]: Mention notifications with activity details
        """
        mentions = []
        
        if user_id in self.mention_notifications:
            for activity_id in self.mention_notifications[user_id]:
                activity = self._find_activity_by_id(activity_id)
                if activity:
                    mentions.append({
                        'activity_id': activity_id,
                        'activity': asdict(activity),
                        'contributor_name': self._get_contributor_name(activity.contributor_id),
                        'timestamp': activity.timestamp.isoformat()
                    })
        
        # Sort by timestamp (newest first)
        mentions.sort(key=lambda x: x['timestamp'], reverse=True)
        return mentions
    
    def _find_activity_by_id(self, activity_id: str) -> Optional[ActivityItem]:
        """Find activity by ID across all feeds."""
        for feed in self.feeds.values():
            for activity in feed.activities:
                if activity.activity_id == activity_id:
                    return activity
        return None
    
    def mark_activity_read(self, activity_id: str, user_id: str) -> bool:
        """
        Mark an activity as read by a user.
        
        Args:
            activity_id: Activity ID
            user_id: User ID
            
        Returns:
            bool: True if marked successfully
        """
        activity = self._find_activity_by_id(activity_id)
        if activity and user_id not in activity.read_by:
            activity.read_by.append(user_id)
            self._save_data()
            return True
        
        return False
    
    def get_feed_summary(self, feed_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a feed.
        
        Args:
            feed_id: Feed identifier
            
        Returns:
            Dict[str, Any]: Feed summary
        """
        if feed_id not in self.feeds:
            return {"error": "Feed not found"}
        
        feed = self.feeds[feed_id]
        activities = feed.activities
        
        summary = {
            "feed_id": feed_id,
            "total_activities": len(activities),
            "subscribers": len(self.subscribers.get(feed_id, [])),
            "activity_types": {},
            "contributors": {},
            "priorities": {},
            "recent_activity": [],
            "unread_count": 0
        }
        
        # Count activity types
        for activity in activities:
            activity_type = activity.activity_type.value
            summary["activity_types"][activity_type] = summary["activity_types"].get(activity_type, 0) + 1
        
        # Count contributors
        for activity in activities:
            contributor_id = activity.contributor_id
            contributor_name = self._get_contributor_name(contributor_id)
            
            if contributor_id not in summary["contributors"]:
                summary["contributors"][contributor_id] = {
                    "id": contributor_id,
                    "name": contributor_name,
                    "activities": 0
                }
            
            summary["contributors"][contributor_id]["activities"] += 1
        
        # Count priorities
        for activity in activities:
            priority = activity.priority.value
            summary["priorities"][priority] = summary["priorities"].get(priority, 0) + 1
        
        # Recent activity (last 10)
        recent_activities = sorted(activities, key=lambda x: x.timestamp, reverse=True)[:10]
        for activity in recent_activities:
            summary["recent_activity"].append({
                "activity_id": activity.activity_id,
                "type": activity.activity_type.value,
                "contributor": self._get_contributor_name(activity.contributor_id),
                "content": activity.content[:100] + "..." if len(activity.content) > 100 else activity.content,
                "timestamp": activity.timestamp.isoformat(),
                "priority": activity.priority.value
            })
        
        return summary
    
    def _get_contributor_name(self, contributor_id: str) -> str:
        """Get contributor name from attribution manager."""
        if self.attribution_manager:
            contributor = self.attribution_manager.get_contributor_info(contributor_id)
            if contributor:
                return contributor.name
        return "Unknown"
    
    def add_update_callback(self, callback: callable):
        """Add a callback for real-time updates."""
        self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: callable):
        """Remove a callback for real-time updates."""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def export_activity_data(self, output_path: str = "activity_export.json") -> None:
        """Export all activity data to JSON file."""
        export_data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "feeds": [asdict(feed) for feed in self.feeds.values()],
            "subscribers": self.subscribers,
            "mention_notifications": self.mention_notifications,
            "summary": {
                "total_feeds": len(self.feeds),
                "total_activities": sum(len(f.activities) for f in self.feeds.values()),
                "total_subscribers": sum(len(s) for s in self.subscribers.values()),
                "total_mentions": sum(len(m) for m in self.mention_notifications.values())
            }
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            logger.info(f"[P24P3S1T1] Activity data exported to {output_path}")
        except Exception as e:
            logger.error(f"[P24P3S1T1] Failed to export activity data: {e}")


def main():
    """Main function for testing activity feed."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitBridge Activity Feed')
    parser.add_argument('--create-feed', metavar='FEED_ID', help='Create activity feed')
    parser.add_argument('--add-activity', nargs=4, metavar=('FEED_ID', 'TYPE', 'CONTRIBUTOR_ID', 'CONTENT'),
                       help='Add activity to feed')
    parser.add_argument('--get-feed', metavar='FEED_ID', help='Get feed activities')
    parser.add_argument('--get-mentions', metavar='USER_ID', help='Get mentions for user')
    parser.add_argument('--export', metavar='OUTPUT_PATH', help='Export activity data')
    
    args = parser.parse_args()
    
    activity_manager = ActivityFeedManager()
    
    if args.create_feed:
        feed_id = activity_manager.create_feed(args.create_feed)
        print(f"Created feed: {feed_id}")
    
    elif args.add_activity:
        feed_id, activity_type_str, contributor_id, content = args.add_activity
        try:
            activity_type = ActivityType(activity_type_str)
            activity_id = activity_manager.add_activity(
                feed_id, activity_type, contributor_id, content
            )
            print(f"Added activity: {activity_id}")
        except ValueError as e:
            print(f"Error: {e}")
    
    elif args.get_feed:
        activities = activity_manager.get_feed_activities(args.get_feed, limit=10)
        summary = activity_manager.get_feed_summary(args.get_feed)
        print(json.dumps(summary, indent=2, default=str))
    
    elif args.get_mentions:
        mentions = activity_manager.get_mentions_for_user(args.get_mentions)
        print(json.dumps(mentions, indent=2, default=str))
    
    elif args.export:
        activity_manager.export_activity_data(args.export)
        print(f"Activity data exported to {args.export}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 