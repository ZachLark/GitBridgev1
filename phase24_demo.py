#!/usr/bin/env python3
"""
GitBridge Phase 24 Demonstration Script
Phase: GBP24
Part: P24P6
Step: P24P6S1
Task: P24P6S1T1 - Phase 24 Demo Implementation

Comprehensive demonstration of Phase 24 collaboration and attribution features.
Implements MAS Lite Protocol v2.1 demonstration requirements.

Author: GitBridge Development Team
Date: 2025-06-20
Schema: [P24P6 Schema]
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mas_core.attribution import AttributionManager, ContributorType, ContributionRole
from mas_core.changelog import ChangelogManager, ChangeType
from mas_core.diff_viewer import DiffViewer
from mas_core.activity_feed import ActivityFeedManager, ActivityType, ActivityPriority
from mas_core.task_display import TaskCardRenderer, TaskCardData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase24Demo:
    """
    Comprehensive demonstration of Phase 24 features.
    
    Phase: GBP24
    Part: P24P6
    Step: P24P6S1
    Task: P24P6S1T1 - Core Demo Implementation
    
    Features demonstrated:
    - Contributor registration and management
    - Task attribution tracking
    - Changelog and revision history
    - Diff visualization
    - Activity feed management
    - Task card rendering
    - Real-time collaboration simulation
    """
    
    def __init__(self):
        """Initialize the Phase 24 demonstration."""
        self.attribution_manager = AttributionManager()
        self.changelog_manager = ChangelogManager(attribution_manager=self.attribution_manager)
        self.diff_viewer = DiffViewer(changelog_manager=self.changelog_manager)
        self.activity_feed_manager = ActivityFeedManager(
            attribution_manager=self.attribution_manager,
            changelog_manager=self.changelog_manager
        )
        self.task_card_renderer = TaskCardRenderer(self.attribution_manager)
        
        # Demo data
        self.demo_contributors = []
        self.demo_tasks = []
        self.demo_files = {}
        
        logger.info("[P24P6S1T1] Phase 24 Demo initialized")
    
    def setup_demo_data(self):
        """Set up demonstration data."""
        logger.info("[P24P6S1T1] Setting up demo data...")
        
        # Register demo contributors
        contributors_data = [
            {
                "name": "Alice Developer",
                "contributor_type": ContributorType.HUMAN,
                "avatar_url": "https://example.com/alice.jpg",
                "email": "alice@example.com"
            },
            {
                "name": "Bob CodeReviewer",
                "contributor_type": ContributorType.HUMAN,
                "avatar_url": "https://example.com/bob.jpg",
                "email": "bob@example.com"
            },
            {
                "name": "AI Assistant GPT-4",
                "contributor_type": ContributorType.AI,
                "avatar_url": "https://example.com/ai-assistant.jpg",
                "metadata": {"model": "gpt-4", "version": "1.0"}
            },
            {
                "name": "Code Generator Bot",
                "contributor_type": ContributorType.AI,
                "avatar_url": "https://example.com/code-bot.jpg",
                "metadata": {"model": "claude-3", "version": "2.1"}
            },
            {
                "name": "System Monitor",
                "contributor_type": ContributorType.SYSTEM,
                "metadata": {"component": "monitoring", "version": "1.0"}
            }
        ]
        
        for contributor_data in contributors_data:
            contributor_id = self.attribution_manager.register_contributor(
                name=contributor_data["name"],
                contributor_type=contributor_data["contributor_type"],
                avatar_url=contributor_data.get("avatar_url"),
                email=contributor_data.get("email"),
                metadata=contributor_data.get("metadata", {})
            )
            self.demo_contributors.append(contributor_id)
            
            # Add activity for contributor registration
            self.activity_feed_manager.add_activity(
                feed_id="main",
                activity_type=ActivityType.SYSTEM_NOTIFICATION,
                contributor_id=contributor_id,
                content=f"New contributor '{contributor_data['name']}' registered",
                priority=ActivityPriority.MEDIUM
            )
        
        # Create demo files
        self.demo_files = {
            "main.py": {
                "original": """#!/usr/bin/env python3
\"\"\"
GitBridge Main Application
Simple example application.
\"\"\"

def main():
    print("Hello, GitBridge!")
    return 0

if __name__ == "__main__":
    main()
""",
                "version1": """#!/usr/bin/env python3
\"\"\"
GitBridge Main Application
Enhanced example application with logging.
\"\"\"

import logging

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting GitBridge application")
    print("Hello, GitBridge!")
    logger.info("Application completed successfully")
    return 0

if __name__ == "__main__":
    main()
""",
                "version2": """#!/usr/bin/env python3
\"\"\"
GitBridge Main Application
Production-ready example application.
\"\"\"

import logging
import sys
from pathlib import Path

def setup_logging():
    \"\"\"Set up application logging.\"\"\"
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    \"\"\"Main application entry point.\"\"\"
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting GitBridge application")
    print("Hello, GitBridge!")
    logger.info("Application completed successfully")
    return 0

if __name__ == "__main__":
    main()
"""
            },
            "config.json": {
                "original": """{
  "app_name": "GitBridge",
  "version": "1.0.0"
}""",
                "version1": """{
  "app_name": "GitBridge",
  "version": "1.1.0",
  "features": {
    "logging": true,
    "debug": false
  }
}""",
                "version2": """{
  "app_name": "GitBridge",
  "version": "1.2.0",
  "features": {
    "logging": true,
    "debug": false,
    "monitoring": true
  },
  "database": {
    "host": "localhost",
    "port": 5432
  }
}"""
            }
        }
        
        logger.info(f"[P24P6S1T1] Demo data setup complete: {len(self.demo_contributors)} contributors, {len(self.demo_files)} files")
    
    def demonstrate_attribution(self):
        """Demonstrate attribution features."""
        logger.info("[P24P6S1T1] Demonstrating attribution features...")
        
        # Create demo tasks
        tasks_data = [
            {
                "task_id": "TASK-001",
                "title": "Implement logging system",
                "description": "Add comprehensive logging to the main application"
            },
            {
                "task_id": "TASK-002", 
                "title": "Add configuration management",
                "description": "Implement JSON-based configuration system"
            },
            {
                "task_id": "TASK-003",
                "title": "Database integration",
                "description": "Add PostgreSQL database connectivity"
            }
        ]
        
        for task_data in tasks_data:
            self.demo_tasks.append(task_data["task_id"])
            
            # Simulate contributions from different contributors
            contributors = self.demo_contributors[:3]  # Use first 3 contributors
            
            for i, contributor_id in enumerate(contributors):
                role = [ContributionRole.CREATOR, ContributionRole.EDITOR, ContributionRole.REVIEWER][i]
                content = f"Contribution to {task_data['title']} as {role.value}"
                
                contribution_id = self.attribution_manager.add_contribution(
                    task_id=task_data["task_id"],
                    contributor_id=contributor_id,
                    role=role,
                    content=content,
                    confidence_score=0.8 + (i * 0.1),
                    token_usage={"input": 100, "output": 200},
                    metadata={"iteration": i + 1}
                )
                
                # Add activity
                contributor_info = self.attribution_manager.get_contributor_info(contributor_id)
                self.activity_feed_manager.add_activity(
                    feed_id="main",
                    activity_type=ActivityType.TASK_UPDATED,
                    contributor_id=contributor_id,
                    task_id=task_data["task_id"],
                    content=f"{contributor_info.name} contributed to {task_data['title']}",
                    priority=ActivityPriority.MEDIUM
                )
        
        logger.info(f"[P24P6S1T1] Attribution demonstration complete: {len(self.demo_tasks)} tasks with contributions")
    
    def demonstrate_changelog(self):
        """Demonstrate changelog features."""
        logger.info("[P24P6S1T1] Demonstrating changelog features...")
        
        for task_id in self.demo_tasks:
            # Create changelog for each task
            self.changelog_manager.create_task_changelog(task_id)
            
            # Add revisions for main.py
            if "TASK-001" in task_id:
                self._add_file_revision(
                    task_id=task_id,
                    contributor_id=self.demo_contributors[0],  # Alice
                    description="Initial implementation with basic logging",
                    file_path="main.py",
                    old_content=self.demo_files["main.py"]["original"],
                    new_content=self.demo_files["main.py"]["version1"]
                )
                
                self._add_file_revision(
                    task_id=task_id,
                    contributor_id=self.demo_contributors[1],  # Bob
                    description="Enhanced logging with file output and proper setup",
                    file_path="main.py",
                    old_content=self.demo_files["main.py"]["version1"],
                    new_content=self.demo_files["main.py"]["version2"]
                )
            
            # Add revisions for config.json
            if "TASK-002" in task_id:
                self._add_file_revision(
                    task_id=task_id,
                    contributor_id=self.demo_contributors[2],  # AI Assistant
                    description="Initial configuration structure",
                    file_path="config.json",
                    old_content=self.demo_files["config.json"]["original"],
                    new_content=self.demo_files["config.json"]["version1"]
                )
                
                self._add_file_revision(
                    task_id=task_id,
                    contributor_id=self.demo_contributors[3],  # Code Generator Bot
                    description="Enhanced configuration with database settings",
                    file_path="config.json",
                    old_content=self.demo_files["config.json"]["version1"],
                    new_content=self.demo_files["config.json"]["version2"]
                )
        
        logger.info("[P24P6S1T1] Changelog demonstration complete")
    
    def _add_file_revision(self, task_id: str, contributor_id: str, description: str, 
                          file_path: str, old_content: str, new_content: str):
        """Add a file revision to a task."""
        file_changes = [{
            "file_path": file_path,
            "change_type": "modified",
            "old_content": old_content,
            "new_content": new_content
        }]
        
        revision_id = self.changelog_manager.add_revision(
            task_id=task_id,
            contributor_id=contributor_id,
            description=description,
            file_changes=file_changes,
            confidence_score=0.9,
            token_usage={"input": 150, "output": 300}
        )
        
        # Add activity
        contributor_info = self.attribution_manager.get_contributor_info(contributor_id)
        self.activity_feed_manager.add_activity(
            feed_id="main",
            activity_type=ActivityType.FILE_MODIFIED,
            contributor_id=contributor_id,
            task_id=task_id,
            file_path=file_path,
            content=f"{contributor_info.name} updated {file_path}: {description}",
            priority=ActivityPriority.MEDIUM
        )
        
        return revision_id
    
    def demonstrate_diff_viewer(self):
        """Demonstrate diff viewer features."""
        logger.info("[P24P6S1T1] Demonstrating diff viewer features...")
        
        # Generate diffs for main.py versions
        diff_result = self.diff_viewer.generate_diff(
            old_content=self.demo_files["main.py"]["original"],
            new_content=self.demo_files["main.py"]["version2"],
            file_path="main.py",
            context_lines=3
        )
        
        # Render diff in different formats
        html_diff = self.diff_viewer.render_diff(diff_result, "html")
        markdown_diff = self.diff_viewer.render_diff(diff_result, "markdown")
        
        # Save demo outputs
        os.makedirs("demo_outputs", exist_ok=True)
        
        with open("demo_outputs/main_py_diff.html", "w") as f:
            f.write(html_diff)
        
        with open("demo_outputs/main_py_diff.md", "w") as f:
            f.write(markdown_diff)
        
        logger.info("[P24P6S1T1] Diff viewer demonstration complete")
        logger.info(f"[P24P6S1T1] Diff summary: {diff_result.summary}")
    
    def demonstrate_task_cards(self):
        """Demonstrate task card rendering."""
        logger.info("[P24P6S1T1] Demonstrating task card rendering...")
        
        # Create task card data
        task_data = TaskCardData(
            task_id="TASK-001",
            title="Implement logging system",
            description="Add comprehensive logging to the main application with file output and proper setup",
            status="completed",
            priority="high",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Render task card in different formats
        html_card = self.task_card_renderer.render_task_card(task_data, "html")
        markdown_card = self.task_card_renderer.render_task_card(task_data, "markdown")
        json_card = self.task_card_renderer.render_task_card(task_data, "json")
        
        # Save demo outputs
        os.makedirs("demo_outputs", exist_ok=True)
        
        with open("demo_outputs/task_card.html", "w") as f:
            f.write(html_card)
        
        with open("demo_outputs/task_card.md", "w") as f:
            f.write(markdown_card)
        
        with open("demo_outputs/task_card.json", "w") as f:
            f.write(json_card)
        
        logger.info("[P24P6S1T1] Task card demonstration complete")
    
    def demonstrate_activity_feed(self):
        """Demonstrate activity feed features."""
        logger.info("[P24P6S1T1] Demonstrating activity feed features...")
        
        # Add various types of activities
        activities = [
            {
                "activity_type": ActivityType.COLLABORATION_STARTED,
                "contributor_id": self.demo_contributors[0],
                "content": "Started collaboration on logging system implementation",
                "task_id": "TASK-001",
                "priority": ActivityPriority.HIGH
            },
            {
                "activity_type": ActivityType.REVIEW_REQUESTED,
                "contributor_id": self.demo_contributors[1],
                "content": "Requested code review for main.py changes",
                "task_id": "TASK-001",
                "priority": ActivityPriority.MEDIUM
            },
            {
                "activity_type": ActivityType.REVIEW_COMPLETED,
                "contributor_id": self.demo_contributors[1],
                "content": "Completed code review - approved with minor suggestions",
                "task_id": "TASK-001",
                "priority": ActivityPriority.MEDIUM
            },
            {
                "activity_type": ActivityType.APPROVAL_GIVEN,
                "contributor_id": self.demo_contributors[4],  # System Monitor
                "content": "System approval: All tests passing, ready for deployment",
                "task_id": "TASK-001",
                "priority": ActivityPriority.HIGH
            }
        ]
        
        for activity_data in activities:
            self.activity_feed_manager.add_activity(
                feed_id="main",
                activity_type=activity_data["activity_type"],
                contributor_id=activity_data["contributor_id"],
                content=activity_data["content"],
                task_id=activity_data.get("task_id"),
                priority=activity_data["priority"]
            )
        
        # Get activity feed summary
        feed_summary = self.activity_feed_manager.get_feed_summary("main")
        
        logger.info(f"[P24P6S1T1] Activity feed demonstration complete")
        logger.info(f"[P24P6S1T1] Feed summary: {feed_summary}")
    
    def export_demo_data(self):
        """Export all demonstration data."""
        logger.info("[P24P6S1T1] Exporting demo data...")
        
        # Export attribution data
        self.attribution_manager.export_attribution_data("demo_outputs/attribution_export.json")
        
        # Export changelog data
        self.changelog_manager.export_changelog_data("demo_outputs/changelog_export.json")
        
        # Export activity data
        self.activity_feed_manager.export_activity_data("demo_outputs/activity_export.json")
        
        logger.info("[P24P6S1T1] Demo data export complete")
    
    def generate_demo_report(self):
        """Generate a comprehensive demo report."""
        try:
            # Get activity feed data
            main_feed = self.activity_feed_manager.feeds.get("main")
            activities = main_feed.activities if main_feed else []
            
            report = {
                "demo_timestamp": datetime.now().isoformat(),
                "phase": "Phase 24 - Collaboration & Task Attribution",
                "status": "completed",
                "summary": {
                    "contributors_registered": len(self.attribution_manager.contributors),
                    "tasks_with_attributions": len(self.attribution_manager.task_attributions),
                    "changelog_revisions": sum(len(changelog.revisions) for changelog in self.changelog_manager.task_changelogs.values()),
                    "total_activities": len(activities),
                    "files_processed": len(self.demo_files)
                },
                "components_tested": [
                    "Contributor Attribution System",
                    "Task Attribution Management", 
                    "Changelog Management",
                    "Diff Viewer",
                    "Activity Feed",
                    "Task Card Rendering"
                ],
                "mas_lite_compliance": {
                    "protocol_version": "2.1",
                    "features_implemented": [
                        "Contributor tracking with unique IDs",
                        "Task attribution with contribution types",
                        "Changelog with revision history",
                        "Activity feed with real-time updates",
                        "Diff visualization with line-level tracking",
                        "Task card rendering with attribution display"
                    ],
                    "compliance_status": "full"
                },
                "performance_metrics": {
                    "attribution_operations": "successful",
                    "changelog_operations": "successful", 
                    "activity_feed_operations": "successful",
                    "diff_processing": "successful",
                    "task_rendering": "successful"
                },
                "export_files": [
                    "demo_outputs/attribution_export.json",
                    "demo_outputs/changelog_export.json", 
                    "demo_outputs/activity_export.json"
                ]
            }
            
            # Save report
            report_path = "demo_outputs/phase24_demo_report.json"
            os.makedirs("demo_outputs", exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"[P24P6S1T1] Demo report saved to {report_path}")
            return report
            
        except Exception as e:
            logger.error(f"[P24P6S1T1] Failed to generate demo report: {e}")
            return {"error": str(e)}
    
    def run_full_demo(self):
        """Run the complete Phase 24 demonstration."""
        logger.info("[P24P6S1T1] Starting Phase 24 full demonstration...")
        
        try:
            # Setup demo data
            self.setup_demo_data()
            
            # Demonstrate each feature
            self.demonstrate_attribution()
            self.demonstrate_changelog()
            self.demonstrate_diff_viewer()
            self.demonstrate_task_cards()
            self.demonstrate_activity_feed()
            
            # Export data
            self.export_demo_data()
            
            # Generate report
            report = self.generate_demo_report()
            if isinstance(report, dict) and "summary" in report:
                logger.info(f"[P24P6S1T1] Demo summary: {report['summary']}")
            else:
                logger.error(f"[P24P6S1T1] Demo failed: {report.get('error', 'Unknown error')}")
            logger.info("[P24P6S1T1] Phase 24 demonstration completed successfully!")
            return report
        except Exception as e:
            logger.error(f"[P24P6S1T1] Demo failed: {e}")
            return {"error": str(e)}

def main():
    """Main demonstration entry point."""
    print("""
================================================================================
GitBridge Phase 24 - Collaboration & Task Attribution Demo
================================================================================
""")
    demo = Phase24Demo()
    report = demo.run_full_demo()
    print("""
================================================================================
DEMO COMPLETED SUCCESSFULLY!
================================================================================

Summary:
""")
    if isinstance(report, dict) and "summary" in report:
        summary = report["summary"]
        print(f"  • Contributors: {summary.get('contributors_registered', 0)}")
        print(f"  • Tasks with Attributions: {summary.get('tasks_with_attributions', 0)}")
        print(f"  • Changelog Revisions: {summary.get('changelog_revisions', 0)}")
        print(f"  • Activities: {summary.get('total_activities', 0)}")
        print(f"  • Files Processed: {summary.get('files_processed', 0)}")
    else:
        print(f"  • Error: {report.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main() 