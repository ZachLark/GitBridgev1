#!/usr/bin/env python3
"""
GitBridge Attribution System
Phase: GBP24
Part: P24P1
Step: P24P1S1
Task: P24P1S1T1 - Contributor Attribution Implementation

Track human and AI authors per task with unique IDs and display attribution.
Implements MAS Lite Protocol v2.1 attribution requirements.

Author: GitBridge Development Team
Date: 2025-06-20
Schema: [P24P1 Schema]
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

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .utils.logging import MASLogger

logger = MASLogger(__name__)

class ContributorType(str, Enum):
    """Types of contributors."""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"

class ContributionRole(str, Enum):
    """Roles in task contribution."""
    CREATOR = "creator"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    COORDINATOR = "coordinator"

@dataclass
class Contributor:
    """Represents a contributor (human or AI)."""
    contributor_id: str
    name: str
    contributor_type: ContributorType
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class TaskContribution:
    """Represents a contribution to a task."""
    contribution_id: str
    task_id: str
    contributor_id: str
    role: ContributionRole
    content: str
    confidence_score: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskAttribution:
    """Complete attribution for a task."""
    task_id: str
    contributions: List[TaskContribution]
    primary_contributor_id: Optional[str] = None
    collaboration_score: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class AttributionManager:
    """
    Manages task attribution and contributor tracking.
    
    Phase: GBP24
    Part: P24P1
    Step: P24P1S1
    Task: P24P1S1T1 - Core Implementation
    
    Features:
    - Track human and AI contributors per task
    - Generate unique contributor IDs
    - Calculate collaboration scores
    - Export attribution data
    - Display attribution information
    """
    
    def __init__(self, storage_path: str = "attribution_data"):
        """
        Initialize the attribution manager.
        
        Args:
            storage_path: Path to store attribution data
        """
        self.storage_path = storage_path
        self.contributors: Dict[str, Contributor] = {}
        self.task_attributions: Dict[str, TaskAttribution] = {}
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing data
        self._load_data()
        
        logger.info("[P24P1S1T1] AttributionManager initialized")
        
    def _load_data(self):
        """Load existing attribution data from storage."""
        try:
            # Load contributors
            contributors_file = os.path.join(self.storage_path, "contributors.json")
            if os.path.exists(contributors_file):
                with open(contributors_file, 'r') as f:
                    contributors_data = json.load(f)
                    for contributor_data in contributors_data:
                        contributor = Contributor(
                            contributor_id=contributor_data['contributor_id'],
                            name=contributor_data['name'],
                            contributor_type=ContributorType(contributor_data['contributor_type']),
                            avatar_url=contributor_data.get('avatar_url'),
                            email=contributor_data.get('email'),
                            metadata=contributor_data.get('metadata', {}),
                            created_at=datetime.fromisoformat(contributor_data['created_at'])
                        )
                        self.contributors[contributor.contributor_id] = contributor
            
            # Load task attributions
            attributions_file = os.path.join(self.storage_path, "task_attributions.json")
            if os.path.exists(attributions_file):
                with open(attributions_file, 'r') as f:
                    attributions_data = json.load(f)
                    for attribution_data in attributions_data:
                        contributions = []
                        for contrib_data in attribution_data['contributions']:
                            contribution = TaskContribution(
                                contribution_id=contrib_data['contribution_id'],
                                task_id=contrib_data['task_id'],
                                contributor_id=contrib_data['contributor_id'],
                                role=ContributionRole(contrib_data['role']),
                                content=contrib_data['content'],
                                confidence_score=contrib_data.get('confidence_score', 0.0),
                                token_usage=contrib_data.get('token_usage', {}),
                                timestamp=datetime.fromisoformat(contrib_data['timestamp']),
                                metadata=contrib_data.get('metadata', {})
                            )
                            contributions.append(contribution)
                        
                        attribution = TaskAttribution(
                            task_id=attribution_data['task_id'],
                            contributions=contributions,
                            primary_contributor_id=attribution_data.get('primary_contributor_id'),
                            collaboration_score=attribution_data.get('collaboration_score', 0.0),
                            created_at=datetime.fromisoformat(attribution_data['created_at']),
                            updated_at=datetime.fromisoformat(attribution_data['updated_at'])
                        )
                        self.task_attributions[attribution.task_id] = attribution
                        
            logger.info(f"[P24P1S1T1] Loaded {len(self.contributors)} contributors and {len(self.task_attributions)} task attributions")
            
        except Exception as e:
            logger.error(f"[P24P1S1T1] Failed to load attribution data: {e}")
    
    def _save_data(self):
        """Save attribution data to storage."""
        try:
            # Save contributors
            contributors_file = os.path.join(self.storage_path, "contributors.json")
            contributors_data = [asdict(contributor) for contributor in self.contributors.values()]
            with open(contributors_file, 'w') as f:
                json.dump(contributors_data, f, indent=2, default=str)
            
            # Save task attributions
            attributions_file = os.path.join(self.storage_path, "task_attributions.json")
            attributions_data = [asdict(attribution) for attribution in self.task_attributions.values()]
            with open(attributions_file, 'w') as f:
                json.dump(attributions_data, f, indent=2, default=str)
                
            logger.info(f"[P24P1S1T1] Saved {len(self.contributors)} contributors and {len(self.task_attributions)} task attributions")
            
        except Exception as e:
            logger.error(f"[P24P1S1T1] Failed to save attribution data: {e}")
    
    def register_contributor(
        self,
        name: str,
        contributor_type: ContributorType,
        avatar_url: Optional[str] = None,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new contributor.
        
        Args:
            name: Contributor name
            contributor_type: Type of contributor (human/ai/system)
            avatar_url: Optional avatar URL
            email: Optional email address
            metadata: Optional metadata
            
        Returns:
            str: Contributor ID
        """
        # Generate unique contributor ID
        contributor_id = self._generate_contributor_id(name, contributor_type)
        
        # Create contributor
        contributor = Contributor(
            contributor_id=contributor_id,
            name=name,
            contributor_type=contributor_type,
            avatar_url=avatar_url,
            email=email,
            metadata=metadata or {}
        )
        
        self.contributors[contributor_id] = contributor
        self._save_data()
        
        logger.info(f"[P24P1S1T1] Registered contributor: {name} ({contributor_type.value})")
        return contributor_id
    
    def _generate_contributor_id(self, name: str, contributor_type: ContributorType) -> str:
        """Generate unique contributor ID."""
        # Create a hash based on name, type, and timestamp
        unique_string = f"{name}_{contributor_type.value}_{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    def add_contribution(
        self,
        task_id: str,
        contributor_id: str,
        role: ContributionRole,
        content: str,
        confidence_score: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a contribution to a task.
        
        Args:
            task_id: Task identifier
            contributor_id: Contributor ID
            role: Role in the contribution
            content: Contribution content
            confidence_score: Confidence score (0.0-1.0)
            token_usage: Token usage statistics
            metadata: Optional metadata
            
        Returns:
            str: Contribution ID
        """
        # Validate contributor exists
        if contributor_id not in self.contributors:
            raise ValueError(f"Contributor {contributor_id} not found")
        
        # Generate contribution ID
        contribution_id = str(uuid.uuid4())
        
        # Create contribution
        contribution = TaskContribution(
            contribution_id=contribution_id,
            task_id=task_id,
            contributor_id=contributor_id,
            role=role,
            content=content,
            confidence_score=confidence_score,
            token_usage=token_usage or {},
            metadata=metadata or {}
        )
        
        # Add to task attribution
        if task_id not in self.task_attributions:
            self.task_attributions[task_id] = TaskAttribution(task_id=task_id, contributions=[])
        
        self.task_attributions[task_id].contributions.append(contribution)
        self.task_attributions[task_id].updated_at = datetime.now(timezone.utc)
        
        # Update collaboration score
        self._update_collaboration_score(task_id)
        
        self._save_data()
        
        contributor_name = self.contributors[contributor_id].name
        logger.info(f"[P24P1S1T1] Added contribution from {contributor_name} to task {task_id}")
        return contribution_id
    
    def _update_collaboration_score(self, task_id: str):
        """Update collaboration score for a task."""
        attribution = self.task_attributions[task_id]
        
        if not attribution.contributions:
            attribution.collaboration_score = 0.0
            return
        
        # Calculate collaboration score based on:
        # 1. Number of contributors
        # 2. Diversity of roles
        # 3. Average confidence scores
        # 4. Token usage distribution
        
        unique_contributors = len(set(c.contributor_id for c in attribution.contributions))
        unique_roles = len(set(c.role for c in attribution.contributions))
        avg_confidence = sum(c.confidence_score for c in attribution.contributions) / len(attribution.contributions)
        
        # Normalize factors
        contributor_factor = min(unique_contributors / 5.0, 1.0)  # Cap at 5 contributors
        role_factor = min(unique_roles / 4.0, 1.0)  # Cap at 4 roles
        confidence_factor = avg_confidence
        
        # Weighted collaboration score
        attribution.collaboration_score = (
            contributor_factor * 0.4 +
            role_factor * 0.3 +
            confidence_factor * 0.3
        )
        
        # Set primary contributor (highest confidence or most recent)
        if attribution.contributions:
            primary_contribution = max(attribution.contributions, key=lambda c: c.confidence_score)
            attribution.primary_contributor_id = primary_contribution.contributor_id
    
    def get_task_attribution(self, task_id: str) -> Optional[TaskAttribution]:
        """Get attribution for a specific task."""
        return self.task_attributions.get(task_id)
    
    def get_contributor_info(self, contributor_id: str) -> Optional[Contributor]:
        """Get contributor information."""
        return self.contributors.get(contributor_id)
    
    def get_contributor_contributions(self, contributor_id: str) -> List[TaskContribution]:
        """Get all contributions by a specific contributor."""
        contributions = []
        for attribution in self.task_attributions.values():
            for contribution in attribution.contributions:
                if contribution.contributor_id == contributor_id:
                    contributions.append(contribution)
        return contributions
    
    def generate_attribution_summary(self, task_id: str) -> Dict[str, Any]:
        """Generate a summary of task attribution."""
        attribution = self.get_task_attribution(task_id)
        if not attribution:
            return {"error": "Task attribution not found"}
        
        summary = {
            "task_id": task_id,
            "total_contributions": len(attribution.contributions),
            "collaboration_score": attribution.collaboration_score,
            "primary_contributor": None,
            "contributors": [],
            "roles_used": [],
            "total_tokens": 0,
            "created_at": attribution.created_at.isoformat(),
            "updated_at": attribution.updated_at.isoformat()
        }
        
        # Get primary contributor info
        if attribution.primary_contributor_id:
            primary_contributor = self.get_contributor_info(attribution.primary_contributor_id)
            if primary_contributor:
                summary["primary_contributor"] = {
                    "id": primary_contributor.contributor_id,
                    "name": primary_contributor.name,
                    "type": primary_contributor.contributor_type.value,
                    "avatar_url": primary_contributor.avatar_url
                }
        
        # Collect contributor info
        contributor_stats = {}
        for contribution in attribution.contributions:
            contributor = self.get_contributor_info(contribution.contributor_id)
            if contributor:
                if contributor.contributor_id not in contributor_stats:
                    contributor_stats[contributor.contributor_id] = {
                        "id": contributor.contributor_id,
                        "name": contributor.name,
                        "type": contributor.contributor_type.value,
                        "avatar_url": contributor.avatar_url,
                        "contributions": 0,
                        "total_confidence": 0.0,
                        "total_tokens": 0,
                        "roles": set()
                    }
                
                stats = contributor_stats[contributor.contributor_id]
                stats["contributions"] += 1
                stats["total_confidence"] += contribution.confidence_score
                stats["total_tokens"] += sum(contribution.token_usage.values())
                stats["roles"].add(contribution.role.value)
        
        # Convert sets to lists for JSON serialization
        for stats in contributor_stats.values():
            stats["roles"] = list(stats["roles"])
            stats["avg_confidence"] = stats["total_confidence"] / stats["contributions"]
            summary["total_tokens"] += stats["total_tokens"]
        
        summary["contributors"] = list(contributor_stats.values())
        summary["roles_used"] = list(set(c.role.value for c in attribution.contributions))
        
        return summary
    
    def export_attribution_data(self, output_path: str = "attribution_export.json") -> None:
        """Export all attribution data to JSON file."""
        export_data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "contributors": [asdict(contributor) for contributor in self.contributors.values()],
            "task_attributions": [asdict(attribution) for attribution in self.task_attributions.values()],
            "summary": {
                "total_contributors": len(self.contributors),
                "total_tasks": len(self.task_attributions),
                "total_contributions": sum(len(a.contributions) for a in self.task_attributions.values()),
                "avg_collaboration_score": sum(a.collaboration_score for a in self.task_attributions.values()) / max(1, len(self.task_attributions))
            }
        }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            logger.info(f"[P24P1S1T1] Attribution data exported to {output_path}")
        except Exception as e:
            logger.error(f"[P24P1S1T1] Failed to export attribution data: {e}")
    
    def get_attribution_display_data(self, task_id: str) -> Dict[str, Any]:
        """Get formatted data for displaying attribution in UI."""
        attribution = self.get_task_attribution(task_id)
        if not attribution:
            return {"error": "Task attribution not found"}
        
        display_data = {
            "task_id": task_id,
            "collaboration_score": attribution.collaboration_score,
            "contributors": [],
            "timeline": [],
            "primary_contributor": None
        }
        
        # Get primary contributor
        if attribution.primary_contributor_id:
            primary_contributor = self.get_contributor_info(attribution.primary_contributor_id)
            if primary_contributor:
                display_data["primary_contributor"] = {
                    "id": primary_contributor.contributor_id,
                    "name": primary_contributor.name,
                    "type": primary_contributor.contributor_type.value,
                    "avatar_url": primary_contributor.avatar_url or self._get_default_avatar(primary_contributor.contributor_type)
                }
        
        # Build contributor list and timeline
        for contribution in sorted(attribution.contributions, key=lambda c: c.timestamp):
            contributor = self.get_contributor_info(contribution.contributor_id)
            if contributor:
                # Add to contributors list (if not already present)
                contributor_display = {
                    "id": contributor.contributor_id,
                    "name": contributor.name,
                    "type": contributor.contributor_type.value,
                    "avatar_url": contributor.avatar_url or self._get_default_avatar(contributor.contributor_type),
                    "contributions": 0,
                    "total_confidence": 0.0
                }
                
                # Check if contributor already in list
                existing_contributor = next((c for c in display_data["contributors"] if c["id"] == contributor.contributor_id), None)
                if not existing_contributor:
                    display_data["contributors"].append(contributor_display)
                    existing_contributor = contributor_display
                
                # Update contributor stats
                existing_contributor["contributions"] += 1
                existing_contributor["total_confidence"] += contribution.confidence_score
                
                # Add to timeline
                timeline_entry = {
                    "timestamp": contribution.timestamp.isoformat(),
                    "contributor": {
                        "id": contributor.contributor_id,
                        "name": contributor.name,
                        "type": contributor.contributor_type.value,
                        "avatar_url": contributor.avatar_url or self._get_default_avatar(contributor.contributor_type)
                    },
                    "role": contribution.role.value,
                    "confidence_score": contribution.confidence_score,
                    "content_preview": contribution.content[:100] + "..." if len(contribution.content) > 100 else contribution.content
                }
                display_data["timeline"].append(timeline_entry)
        
        # Calculate average confidence for each contributor
        for contributor in display_data["contributors"]:
            contributor["avg_confidence"] = contributor["total_confidence"] / contributor["contributions"]
        
        return display_data
    
    def _get_default_avatar(self, contributor_type: ContributorType) -> str:
        """Get default avatar URL based on contributor type."""
        if contributor_type == ContributorType.HUMAN:
            return "https://via.placeholder.com/40x40/4F46E5/FFFFFF?text=👤"
        elif contributor_type == ContributorType.AI:
            return "https://via.placeholder.com/40x40/059669/FFFFFF?text=🤖"
        else:
            return "https://via.placeholder.com/40x40/6B7280/FFFFFF?text=⚙️"


def main():
    """Main function for testing attribution system."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitBridge Attribution System')
    parser.add_argument('--register-contributor', nargs=3, metavar=('NAME', 'TYPE', 'EMAIL'),
                       help='Register a new contributor')
    parser.add_argument('--add-contribution', nargs=4, metavar=('TASK_ID', 'CONTRIBUTOR_ID', 'ROLE', 'CONTENT'),
                       help='Add a contribution to a task')
    parser.add_argument('--get-attribution', metavar='TASK_ID', help='Get task attribution')
    parser.add_argument('--export', metavar='OUTPUT_PATH', help='Export attribution data')
    
    args = parser.parse_args()
    
    attribution_manager = AttributionManager()
    
    if args.register_contributor:
        name, contributor_type_str, email = args.register_contributor
        try:
            contributor_type = ContributorType(contributor_type_str)
            contributor_id = attribution_manager.register_contributor(name, contributor_type, email=email)
            print(f"Registered contributor: {contributor_id}")
        except ValueError as e:
            print(f"Error: {e}")
    
    elif args.add_contribution:
        task_id, contributor_id, role_str, content = args.add_contribution
        try:
            role = ContributionRole(role_str)
            contribution_id = attribution_manager.add_contribution(task_id, contributor_id, role, content)
            print(f"Added contribution: {contribution_id}")
        except ValueError as e:
            print(f"Error: {e}")
    
    elif args.get_attribution:
        attribution = attribution_manager.get_task_attribution(args.get_attribution)
        if attribution:
            summary = attribution_manager.generate_attribution_summary(args.get_attribution)
            print(json.dumps(summary, indent=2, default=str))
        else:
            print("Task attribution not found")
    
    elif args.export:
        attribution_manager.export_attribution_data(args.export)
        print(f"Attribution data exported to {args.export}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 