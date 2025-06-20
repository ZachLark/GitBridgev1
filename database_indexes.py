#!/usr/bin/env python3
"""
GitBridge Database Index Enhancement
Phase: GBP24 Hotfix
Part: P24P2
Step: P24P2S3
Task: P24P2S3T1 - Database Index Implementation

Implements database indexing for task_id, contributor_id, and attribution_id fields
to improve query performance as recommended in the completion memo.

Author: GitBridge Development Team
Date: 2025-06-20
Schema: [P24P2 Schema]
"""

import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import pickle
import hashlib

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mas_core.utils.logging import MASLogger

logger = MASLogger(__name__)

class DatabaseIndexManager:
    """
    Manages database indexes for improved query performance.
    
    Phase: GBP24 Hotfix
    Part: P24P2
    Step: P24P2S3
    Task: P24P2S3T1 - Core Implementation
    
    Features:
    - Create indexes for task_id, contributor_id, attribution_id
    - Maintain index consistency
    - Provide fast lookups
    - Support index rebuilding
    """
    
    def __init__(self, data_path: str = "attribution_data"):
        """
        Initialize the index manager.
        
        Args:
            data_path: Path to data files
        """
        self.data_path = data_path
        self.index_path = os.path.join(data_path, "indexes")
        self.indexes = {}
        
        # Create index directory
        os.makedirs(self.index_path, exist_ok=True)
        
        # Initialize indexes
        self._initialize_indexes()
        
        logger.info("[P24P2S3T1] DatabaseIndexManager initialized")
    
    def _initialize_indexes(self):
        """Initialize all indexes."""
        self.indexes = {
            'task_id': self._load_index('task_id'),
            'contributor_id': self._load_index('contributor_id'),
            'attribution_id': self._load_index('attribution_id'),
            'activity_id': self._load_index('activity_id'),
            'revision_id': self._load_index('revision_id')
        }
    
    def _load_index(self, index_name: str) -> Dict[str, Set[str]]:
        """Load an index from disk."""
        index_file = os.path.join(self.index_path, f"{index_name}_index.pkl")
        if os.path.exists(index_file):
            try:
                with open(index_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load {index_name} index: {e}")
        
        return defaultdict(set)
    
    def _save_index(self, index_name: str, index_data: Dict[str, Set[str]]):
        """Save an index to disk."""
        index_file = os.path.join(self.index_path, f"{index_name}_index.pkl")
        try:
            with open(index_file, 'wb') as f:
                pickle.dump(dict(index_data), f)
        except Exception as e:
            logger.error(f"Failed to save {index_name} index: {e}")
    
    def build_all_indexes(self):
        """Build all indexes from current data."""
        logger.info("[P24P2S3T1] Building all indexes...")
        
        # Build task attribution indexes
        self._build_task_attribution_indexes()
        
        # Build activity feed indexes
        self._build_activity_feed_indexes()
        
        # Build changelog indexes
        self._build_changelog_indexes()
        
        # Save all indexes
        for index_name, index_data in self.indexes.items():
            self._save_index(index_name, index_data)
        
        logger.info("[P24P2S3T1] All indexes built successfully")
    
    def _build_task_attribution_indexes(self):
        """Build indexes for task attribution data."""
        attributions_file = os.path.join(self.data_path, "task_attributions.json")
        if not os.path.exists(attributions_file):
            return
        
        with open(attributions_file, 'r') as f:
            attributions = json.load(f)
        
        # Clear existing indexes
        self.indexes['task_id'].clear()
        self.indexes['contributor_id'].clear()
        self.indexes['attribution_id'].clear()
        
        for attribution in attributions:
            task_id = attribution['task_id']
            
            # Index by task_id
            self.indexes['task_id'][task_id].add(task_id)
            
            # Index by contributor_id
            for contribution in attribution.get('contributions', []):
                contributor_id = contribution['contributor_id']
                contribution_id = contribution['contribution_id']
                
                self.indexes['contributor_id'][contributor_id].add(task_id)
                self.indexes['attribution_id'][contribution_id].add(task_id)
    
    def _build_activity_feed_indexes(self):
        """Build indexes for activity feed data."""
        activity_file = os.path.join(self.data_path, "activity_feeds.json")
        if not os.path.exists(activity_file):
            return
        
        with open(activity_file, 'r') as f:
            feeds = json.load(f)
        
        # Clear existing activity indexes
        self.indexes['activity_id'].clear()
        
        for feed in feeds:
            feed_id = feed['feed_id']
            
            for activity in feed.get('activities', []):
                activity_id = activity['activity_id']
                contributor_id = activity['contributor_id']
                task_id = activity.get('task_id')
                
                # Index by activity_id
                self.indexes['activity_id'][activity_id].add(feed_id)
                
                # Index by contributor_id (for activities)
                if contributor_id:
                    self.indexes['contributor_id'][contributor_id].add(f"activity_{feed_id}")
                
                # Index by task_id (for activities)
                if task_id:
                    self.indexes['task_id'][task_id].add(f"activity_{feed_id}")
    
    def _build_changelog_indexes(self):
        """Build indexes for changelog data."""
        changelog_file = os.path.join(self.data_path, "changelogs.json")
        if not os.path.exists(changelog_file):
            return
        
        with open(changelog_file, 'r') as f:
            changelogs = json.load(f)
        
        # Clear existing revision indexes
        self.indexes['revision_id'].clear()
        
        for changelog in changelogs:
            task_id = changelog['task_id']
            
            for revision in changelog.get('revisions', []):
                revision_id = revision['revision_id']
                contributor_id = revision['contributor_id']
                
                # Index by revision_id
                self.indexes['revision_id'][revision_id].add(task_id)
                
                # Index by contributor_id (for revisions)
                if contributor_id:
                    self.indexes['contributor_id'][contributor_id].add(f"revision_{task_id}")
                
                # Index by task_id (for revisions)
                self.indexes['task_id'][task_id].add(f"revision_{task_id}")
    
    def get_tasks_by_contributor(self, contributor_id: str) -> List[str]:
        """Get all tasks associated with a contributor."""
        return list(self.indexes['contributor_id'].get(contributor_id, set()))
    
    def get_contributors_by_task(self, task_id: str) -> List[str]:
        """Get all contributors associated with a task."""
        contributors = set()
        for contrib_id, tasks in self.indexes['contributor_id'].items():
            if task_id in tasks:
                contributors.add(contrib_id)
        return list(contributors)
    
    def get_attribution_by_id(self, attribution_id: str) -> List[str]:
        """Get tasks associated with an attribution ID."""
        return list(self.indexes['attribution_id'].get(attribution_id, set()))
    
    def get_activity_by_id(self, activity_id: str) -> List[str]:
        """Get feeds associated with an activity ID."""
        return list(self.indexes['activity_id'].get(activity_id, set()))
    
    def get_revision_by_id(self, revision_id: str) -> List[str]:
        """Get tasks associated with a revision ID."""
        return list(self.indexes['revision_id'].get(revision_id, set()))
    
    def add_task_attribution(self, task_id: str, contributor_id: str, contribution_id: str):
        """Add a new task attribution to indexes."""
        self.indexes['task_id'][task_id].add(task_id)
        self.indexes['contributor_id'][contributor_id].add(task_id)
        self.indexes['attribution_id'][contribution_id].add(task_id)
        
        # Save updated indexes
        self._save_index('task_id', self.indexes['task_id'])
        self._save_index('contributor_id', self.indexes['contributor_id'])
        self._save_index('attribution_id', self.indexes['attribution_id'])
    
    def add_activity(self, activity_id: str, feed_id: str, contributor_id: str, task_id: Optional[str] = None):
        """Add a new activity to indexes."""
        self.indexes['activity_id'][activity_id].add(feed_id)
        self.indexes['contributor_id'][contributor_id].add(f"activity_{feed_id}")
        
        if task_id:
            self.indexes['task_id'][task_id].add(f"activity_{feed_id}")
        
        # Save updated indexes
        self._save_index('activity_id', self.indexes['activity_id'])
        self._save_index('contributor_id', self.indexes['contributor_id'])
        if task_id:
            self._save_index('task_id', self.indexes['task_id'])
    
    def add_revision(self, revision_id: str, task_id: str, contributor_id: str):
        """Add a new revision to indexes."""
        self.indexes['revision_id'][revision_id].add(task_id)
        self.indexes['contributor_id'][contributor_id].add(f"revision_{task_id}")
        self.indexes['task_id'][task_id].add(f"revision_{task_id}")
        
        # Save updated indexes
        self._save_index('revision_id', self.indexes['revision_id'])
        self._save_index('contributor_id', self.indexes['contributor_id'])
        self._save_index('task_id', self.indexes['task_id'])
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about all indexes."""
        stats = {}
        
        for index_name, index_data in self.indexes.items():
            total_entries = sum(len(entries) for entries in index_data.values())
            unique_keys = len(index_data)
            
            stats[index_name] = {
                "total_entries": total_entries,
                "unique_keys": unique_keys,
                "average_entries_per_key": round(total_entries / unique_keys, 2) if unique_keys > 0 else 0
            }
        
        return stats
    
    def validate_indexes(self) -> Dict[str, bool]:
        """Validate index consistency."""
        validation_results = {}
        
        # Check if all index files exist
        for index_name in self.indexes.keys():
            index_file = os.path.join(self.index_path, f"{index_name}_index.pkl")
            validation_results[f"{index_name}_file_exists"] = os.path.exists(index_file)
        
        # Check index data integrity
        for index_name, index_data in self.indexes.items():
            validation_results[f"{index_name}_data_valid"] = isinstance(index_data, dict)
        
        return validation_results

def main():
    """Main function for testing index manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitBridge Database Index Manager')
    parser.add_argument('--build', action='store_true', help='Build all indexes')
    parser.add_argument('--stats', action='store_true', help='Show index statistics')
    parser.add_argument('--validate', action='store_true', help='Validate indexes')
    parser.add_argument('--data-path', default='attribution_data', help='Path to data files')
    
    args = parser.parse_args()
    
    # Create index manager
    index_manager = DatabaseIndexManager(args.data_path)
    
    if args.build:
        print("Building all indexes...")
        index_manager.build_all_indexes()
        print("Index building complete!")
    
    if args.stats:
        print("\nIndex Statistics:")
        stats = index_manager.get_index_stats()
        for index_name, stat_data in stats.items():
            print(f"  {index_name}:")
            print(f"    Total entries: {stat_data['total_entries']}")
            print(f"    Unique keys: {stat_data['unique_keys']}")
            print(f"    Avg entries per key: {stat_data['average_entries_per_key']}")
    
    if args.validate:
        print("\nIndex Validation:")
        validation = index_manager.validate_indexes()
        for check, result in validation.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {check}: {status}")
    
    if not any([args.build, args.stats, args.validate]):
        print("Use --help to see available options")

if __name__ == "__main__":
    main() 