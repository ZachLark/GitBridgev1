#!/usr/bin/env python3
"""
GitBridge Changelog System
Phase: GBP24
Part: P24P2
Step: P24P2S1
Task: P24P2S1T1 - Changelog Backend Implementation

Create backend task revision history store with file-level changelogs.
Implements MAS Lite Protocol v2.1 changelog requirements.

Author: GitBridge Development Team
Date: 2025-06-20
Schema: [P24P2 Schema]
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import os
import sys
from difflib import unified_diff, SequenceMatcher

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .attribution import AttributionManager, ContributorType, ContributionRole
from .utils.logging import MASLogger

logger = MASLogger(__name__)

class ChangeType(str, Enum):
    """Types of changes."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    MOVED = "moved"

class ChangeScope(str, Enum):
    """Scope of changes."""
    TASK = "task"
    FILE = "file"
    CODE = "code"
    CONFIG = "config"
    DOCUMENTATION = "documentation"
    METADATA = "metadata"

@dataclass
class FileChange:
    """Represents a change to a file."""
    change_id: str
    file_path: str
    change_type: ChangeType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    diff: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class TaskRevision:
    """Represents a revision of a task."""
    revision_id: str
    task_id: str
    contributor_id: str
    revision_number: int
    description: str
    changes: List[FileChange]
    confidence_score: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class TaskChangelog:
    """Complete changelog for a task."""
    task_id: str
    revisions: List[TaskRevision]
    current_revision: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class ChangelogManager:
    """
    Manages task revision history and file-level changelogs.
    
    Phase: GBP24
    Part: P24P2
    Step: P24P2S1
    Task: P24P2S1T1 - Core Implementation
    
    Features:
    - Track task revision history
    - Store file-level changes
    - Generate diffs between versions
    - Export changelog data
    - Search and filter changes
    """
    
    def __init__(self, storage_path: str = "changelog_data", attribution_manager: Optional[AttributionManager] = None):
        """
        Initialize the changelog manager.
        
        Args:
            storage_path: Path to store changelog data
            attribution_manager: Optional attribution manager for contributor info
        """
        self.storage_path = storage_path
        self.attribution_manager = attribution_manager or AttributionManager()
        self.task_changelogs: Dict[str, TaskChangelog] = {}
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing data
        self._load_data()
        
        logger.info("[P24P2S1T1] ChangelogManager initialized")
    
    def _load_data(self):
        """Load existing changelog data from storage."""
        try:
            changelogs_file = os.path.join(self.storage_path, "task_changelogs.json")
            if os.path.exists(changelogs_file):
                with open(changelogs_file, 'r') as f:
                    changelogs_data = json.load(f)
                    for changelog_data in changelogs_data:
                        revisions = []
                        for revision_data in changelog_data['revisions']:
                            changes = []
                            for change_data in revision_data['changes']:
                                change = FileChange(
                                    change_id=change_data['change_id'],
                                    file_path=change_data['file_path'],
                                    change_type=ChangeType(change_data['change_type']),
                                    old_content=change_data.get('old_content'),
                                    new_content=change_data.get('new_content'),
                                    diff=change_data.get('diff'),
                                    metadata=change_data.get('metadata', {}),
                                    timestamp=datetime.fromisoformat(change_data['timestamp'])
                                )
                                changes.append(change)
                            
                            revision = TaskRevision(
                                revision_id=revision_data['revision_id'],
                                task_id=revision_data['task_id'],
                                contributor_id=revision_data['contributor_id'],
                                revision_number=revision_data['revision_number'],
                                description=revision_data['description'],
                                changes=changes,
                                confidence_score=revision_data.get('confidence_score', 0.0),
                                token_usage=revision_data.get('token_usage', {}),
                                metadata=revision_data.get('metadata', {}),
                                timestamp=datetime.fromisoformat(revision_data['timestamp'])
                            )
                            revisions.append(revision)
                        
                        changelog = TaskChangelog(
                            task_id=changelog_data['task_id'],
                            revisions=revisions,
                            current_revision=changelog_data.get('current_revision', 0),
                            created_at=datetime.fromisoformat(changelog_data['created_at']),
                            updated_at=datetime.fromisoformat(changelog_data['updated_at'])
                        )
                        self.task_changelogs[changelog.task_id] = changelog
                        
            logger.info(f"[P24P2S1T1] Loaded {len(self.task_changelogs)} task changelogs")
            
        except Exception as e:
            logger.error(f"[P24P2S1T1] Failed to load changelog data: {e}")
    
    def _save_data(self):
        """Save changelog data to storage."""
        try:
            changelogs_file = os.path.join(self.storage_path, "task_changelogs.json")
            changelogs_data = [asdict(changelog) for changelog in self.task_changelogs.values()]
            with open(changelogs_file, 'w') as f:
                json.dump(changelogs_data, f, indent=2, default=str)
                
            logger.info(f"[P24P2S1T1] Saved {len(self.task_changelogs)} task changelogs")
            
        except Exception as e:
            logger.error(f"[P24P2S1T1] Failed to save changelog data: {e}")
    
    def create_task_changelog(self, task_id: str) -> str:
        """
        Create a new changelog for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            str: Changelog ID (same as task_id)
        """
        if task_id not in self.task_changelogs:
            self.task_changelogs[task_id] = TaskChangelog(task_id=task_id, revisions=[])
            self._save_data()
            logger.info(f"[P24P2S1T1] Created changelog for task {task_id}")
        
        return task_id
    
    def add_revision(
        self,
        task_id: str,
        contributor_id: str,
        description: str,
        file_changes: List[Dict[str, Any]],
        confidence_score: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a new revision to a task changelog.
        
        Args:
            task_id: Task identifier
            contributor_id: Contributor ID
            description: Revision description
            file_changes: List of file changes
            confidence_score: Confidence score (0.0-1.0)
            token_usage: Token usage statistics
            metadata: Optional metadata
            
        Returns:
            str: Revision ID
        """
        # Ensure changelog exists
        self.create_task_changelog(task_id)
        
        changelog = self.task_changelogs[task_id]
        revision_number = len(changelog.revisions) + 1
        revision_id = str(uuid.uuid4())
        
        # Process file changes
        changes = []
        for change_data in file_changes:
            change = self._create_file_change(change_data)
            changes.append(change)
        
        # Create revision
        revision = TaskRevision(
            revision_id=revision_id,
            task_id=task_id,
            contributor_id=contributor_id,
            revision_number=revision_number,
            description=description,
            changes=changes,
            confidence_score=confidence_score,
            token_usage=token_usage or {},
            metadata=metadata or {}
        )
        
        # Add to changelog
        changelog.revisions.append(revision)
        changelog.current_revision = revision_number
        changelog.updated_at = datetime.now(timezone.utc)
        
        self._save_data()
        
        contributor_name = self._get_contributor_name(contributor_id)
        logger.info(f"[P24P2S1T1] Added revision {revision_number} from {contributor_name} to task {task_id}")
        return revision_id
    
    def _create_file_change(self, change_data: Dict[str, Any]) -> FileChange:
        """Create a file change from change data."""
        change_id = str(uuid.uuid4())
        file_path = change_data['file_path']
        change_type = ChangeType(change_data['change_type'])
        old_content = change_data.get('old_content')
        new_content = change_data.get('new_content')
        
        # Generate diff if both old and new content are provided
        diff = None
        if old_content is not None and new_content is not None and change_type == ChangeType.MODIFIED:
            diff = self._generate_diff(old_content, new_content, file_path)
        
        return FileChange(
            change_id=change_id,
            file_path=file_path,
            change_type=change_type,
            old_content=old_content,
            new_content=new_content,
            diff=diff,
            metadata=change_data.get('metadata', {})
        )
    
    def _generate_diff(self, old_content: str, new_content: str, file_path: str) -> str:
        """Generate unified diff between old and new content."""
        try:
            diff_lines = unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm=""
            )
            return "\n".join(diff_lines)
        except Exception as e:
            logger.error(f"[P24P2S1T1] Failed to generate diff: {e}")
            return f"# Diff generation failed: {e}"
    
    def _get_contributor_name(self, contributor_id: str) -> str:
        """Get contributor name from attribution manager."""
        if self.attribution_manager:
            contributor = self.attribution_manager.get_contributor_info(contributor_id)
            if contributor:
                return contributor.name
        return "Unknown"
    
    def get_task_changelog(self, task_id: str) -> Optional[TaskChangelog]:
        """Get changelog for a specific task."""
        return self.task_changelogs.get(task_id)
    
    def get_revision(self, task_id: str, revision_number: int) -> Optional[TaskRevision]:
        """Get a specific revision of a task."""
        changelog = self.get_task_changelog(task_id)
        if changelog and 1 <= revision_number <= len(changelog.revisions):
            return changelog.revisions[revision_number - 1]
        return None
    
    def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """Get history of changes for a specific file."""
        history = []
        
        for changelog in self.task_changelogs.values():
            for revision in changelog.revisions:
                for change in revision.changes:
                    if change.file_path == file_path:
                        history.append({
                            'task_id': changelog.task_id,
                            'revision_number': revision.revision_number,
                            'revision_id': revision.revision_id,
                            'contributor_id': revision.contributor_id,
                            'contributor_name': self._get_contributor_name(revision.contributor_id),
                            'change_type': change.change_type.value,
                            'timestamp': change.timestamp.isoformat(),
                            'description': revision.description,
                            'diff': change.diff
                        })
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        return history
    
    def compare_revisions(self, task_id: str, revision1: int, revision2: int) -> Dict[str, Any]:
        """Compare two revisions of a task."""
        rev1 = self.get_revision(task_id, revision1)
        rev2 = self.get_revision(task_id, revision2)
        
        if not rev1 or not rev2:
            return {"error": "One or both revisions not found"}
        
        comparison = {
            'task_id': task_id,
            'revision1': {
                'number': rev1.revision_number,
                'contributor': self._get_contributor_name(rev1.contributor_id),
                'description': rev1.description,
                'timestamp': rev1.timestamp.isoformat()
            },
            'revision2': {
                'number': rev2.revision_number,
                'contributor': self._get_contributor_name(rev2.contributor_id),
                'description': rev2.description,
                'timestamp': rev2.timestamp.isoformat()
            },
            'changes': []
        }
        
        # Compare file changes
        rev1_files = {change.file_path: change for change in rev1.changes}
        rev2_files = {change.file_path: change for change in rev2.changes}
        
        all_files = set(rev1_files.keys()) | set(rev2_files.keys())
        
        for file_path in all_files:
            change1 = rev1_files.get(file_path)
            change2 = rev2_files.get(file_path)
            
            if change1 and change2:
                # File modified in both revisions
                if change1.new_content != change2.new_content:
                    comparison['changes'].append({
                        'file_path': file_path,
                        'type': 'modified',
                        'diff': self._generate_diff(change1.new_content, change2.new_content, file_path)
                    })
            elif change1 and not change2:
                # File deleted in revision 2
                comparison['changes'].append({
                    'file_path': file_path,
                    'type': 'deleted',
                    'content': change1.new_content
                })
            elif not change1 and change2:
                # File created in revision 2
                comparison['changes'].append({
                    'file_path': file_path,
                    'type': 'created',
                    'content': change2.new_content
                })
        
        return comparison
    
    def search_changes(
        self,
        query: str,
        change_type: Optional[ChangeType] = None,
        contributor_id: Optional[str] = None,
        file_path: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Search for changes based on various criteria."""
        results = []
        
        for changelog in self.task_changelogs.values():
            for revision in changelog.revisions:
                # Apply filters
                if contributor_id and revision.contributor_id != contributor_id:
                    continue
                
                if date_from and revision.timestamp < date_from:
                    continue
                
                if date_to and revision.timestamp > date_to:
                    continue
                
                for change in revision.changes:
                    # Apply file path filter
                    if file_path and change.file_path != file_path:
                        continue
                    
                    # Apply change type filter
                    if change_type and change.change_type != change_type:
                        continue
                    
                    # Apply text search
                    if query:
                        search_text = f"{revision.description} {change.file_path}"
                        if change.new_content:
                            search_text += f" {change.new_content}"
                        if query.lower() not in search_text.lower():
                            continue
                    
                    results.append({
                        'task_id': changelog.task_id,
                        'revision_number': revision.revision_number,
                        'revision_id': revision.revision_id,
                        'contributor_id': revision.contributor_id,
                        'contributor_name': self._get_contributor_name(revision.contributor_id),
                        'file_path': change.file_path,
                        'change_type': change.change_type.value,
                        'description': revision.description,
                        'timestamp': change.timestamp.isoformat(),
                        'diff': change.diff
                    })
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        return results
    
    def export_changelog_data(self, output_path: str = "changelog_export.json") -> None:
        """Export all changelog data to JSON file."""
        export_data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "task_changelogs": [asdict(changelog) for changelog in self.task_changelogs.values()],
            "summary": {
                "total_tasks": len(self.task_changelogs),
                "total_revisions": sum(len(c.revisions) for c in self.task_changelogs.values()),
                "total_changes": sum(len(r.changes) for c in self.task_changelogs.values() for r in c.revisions),
                "avg_revisions_per_task": sum(len(c.revisions) for c in self.task_changelogs.values()) / max(1, len(self.task_changelogs))
            }
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            logger.info(f"[P24P2S1T1] Changelog data exported to {output_path}")
        except Exception as e:
            logger.error(f"[P24P2S1T1] Failed to export changelog data: {e}")
    
    def get_changelog_summary(self, task_id: str) -> Dict[str, Any]:
        """Get a summary of changelog for a task."""
        changelog = self.get_task_changelog(task_id)
        if not changelog:
            return {"error": "Changelog not found"}
        
        summary = {
            "task_id": task_id,
            "total_revisions": len(changelog.revisions),
            "current_revision": changelog.current_revision,
            "created_at": changelog.created_at.isoformat(),
            "updated_at": changelog.updated_at.isoformat(),
            "contributors": [],
            "files_modified": set(),
            "change_types": {},
            "recent_activity": []
        }
        
        # Collect contributor info
        contributor_stats = {}
        for revision in changelog.revisions:
            contributor_id = revision.contributor_id
            contributor_name = self._get_contributor_name(contributor_id)
            
            if contributor_id not in contributor_stats:
                contributor_stats[contributor_id] = {
                    "id": contributor_id,
                    "name": contributor_name,
                    "revisions": 0,
                    "total_confidence": 0.0,
                    "total_tokens": 0
                }
            
            stats = contributor_stats[contributor_id]
            stats["revisions"] += 1
            stats["total_confidence"] += revision.confidence_score
            stats["total_tokens"] += sum(revision.token_usage.values())
            
            # Collect file changes
            for change in revision.changes:
                summary["files_modified"].add(change.file_path)
                
                change_type = change.change_type.value
                summary["change_types"][change_type] = summary["change_types"].get(change_type, 0) + 1
            
            # Add to recent activity
            summary["recent_activity"].append({
                "revision_number": revision.revision_number,
                "contributor": contributor_name,
                "description": revision.description,
                "timestamp": revision.timestamp.isoformat(),
                "files_changed": len(revision.changes)
            })
        
        # Convert sets to lists for JSON serialization
        summary["files_modified"] = list(summary["files_modified"])
        summary["contributors"] = list(contributor_stats.values())
        
        # Calculate averages for contributors
        for contributor in summary["contributors"]:
            contributor["avg_confidence"] = contributor["total_confidence"] / contributor["revisions"]
        
        # Sort recent activity by timestamp (newest first)
        summary["recent_activity"].sort(key=lambda x: x["timestamp"], reverse=True)
        summary["recent_activity"] = summary["recent_activity"][:10]  # Keep last 10
        
        return summary


def main():
    """Main function for testing changelog system."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitBridge Changelog System')
    parser.add_argument('--create-changelog', metavar='TASK_ID', help='Create changelog for task')
    parser.add_argument('--add-revision', nargs=4, metavar=('TASK_ID', 'CONTRIBUTOR_ID', 'DESCRIPTION', 'FILE_PATH'),
                       help='Add revision to task')
    parser.add_argument('--get-changelog', metavar='TASK_ID', help='Get task changelog')
    parser.add_argument('--file-history', metavar='FILE_PATH', help='Get file history')
    parser.add_argument('--export', metavar='OUTPUT_PATH', help='Export changelog data')
    
    args = parser.parse_args()
    
    changelog_manager = ChangelogManager()
    
    if args.create_changelog:
        changelog_id = changelog_manager.create_task_changelog(args.create_changelog)
        print(f"Created changelog: {changelog_id}")
    
    elif args.add_revision:
        task_id, contributor_id, description, file_path = args.add_revision
        
        # Create sample file changes
        file_changes = [{
            'file_path': file_path,
            'change_type': 'modified',
            'old_content': '# Old content\nThis is the old version.',
            'new_content': '# New content\nThis is the updated version.',
            'metadata': {'reason': 'Update for testing'}
        }]
        
        revision_id = changelog_manager.add_revision(
            task_id, contributor_id, description, file_changes
        )
        print(f"Added revision: {revision_id}")
    
    elif args.get_changelog:
        changelog = changelog_manager.get_task_changelog(args.get_changelog)
        if changelog:
            summary = changelog_manager.get_changelog_summary(args.get_changelog)
            print(json.dumps(summary, indent=2, default=str))
        else:
            print("Changelog not found")
    
    elif args.file_history:
        history = changelog_manager.get_file_history(args.file_history)
        print(json.dumps(history, indent=2, default=str))
    
    elif args.export:
        changelog_manager.export_changelog_data(args.export)
        print(f"Changelog data exported to {args.export}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 