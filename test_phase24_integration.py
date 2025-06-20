#!/usr/bin/env python3
"""
GitBridge Phase 24 Integration Test Suite
Phase: GBP24
Part: P24P6
Step: P24P6S2
Task: P24P6S2T1 - Phase 24 Integration Testing

Comprehensive integration testing for Phase 24 collaboration and attribution features.
Implements MAS Lite Protocol v2.1 testing requirements.

Author: GitBridge Development Team
Date: 2025-06-20
Schema: [P24P6 Schema]
"""

import json
import logging
import unittest
import tempfile
import shutil
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mas_core.attribution import AttributionManager, ContributorType, ContributionRole
from mas_core.changelog import ChangelogManager, ChangeType
from mas_core.diff_viewer import DiffViewer
from mas_core.activity_feed import ActivityFeedManager, ActivityType, ActivityPriority
from mas_core.task_display import TaskCardRenderer, TaskCardData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase24IntegrationTest(unittest.TestCase):
    """
    Integration tests for Phase 24 collaboration and attribution features.
    
    Phase: GBP24
    Part: P24P6
    Step: P24P6S2
    Task: P24P6S2T1 - Core Integration Testing
    """
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp(prefix="phase24_test_")
        self.attribution_dir = os.path.join(self.test_dir, "attribution_data")
        self.changelog_dir = os.path.join(self.test_dir, "changelog_data")
        self.activity_dir = os.path.join(self.test_dir, "activity_data")
        
        # Initialize managers with test directories
        self.attribution_manager = AttributionManager(self.attribution_dir)
        self.changelog_manager = ChangelogManager(
            storage_path=self.changelog_dir,
            attribution_manager=self.attribution_manager
        )
        self.diff_viewer = DiffViewer(changelog_manager=self.changelog_manager)
        self.activity_feed_manager = ActivityFeedManager(
            storage_path=self.activity_dir,
            attribution_manager=self.attribution_manager,
            changelog_manager=self.changelog_manager
        )
        self.task_card_renderer = TaskCardRenderer(self.attribution_manager)
        
        # Test data
        self.test_contributors = []
        self.test_tasks = []
        
        logger.info(f"[P24P6S2T1] Test environment set up in {self.test_dir}")
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directories
        shutil.rmtree(self.test_dir, ignore_errors=True)
        logger.info(f"[P24P6S2T1] Test environment cleaned up")
    
    def test_01_contributor_registration(self):
        """Test contributor registration and management."""
        logger.info("[P24P6S2T1] Testing contributor registration...")
        
        # Test human contributor registration
        human_id = self.attribution_manager.register_contributor(
            name="Test Human",
            contributor_type=ContributorType.HUMAN,
            email="test@example.com"
        )
        self.assertIsNotNone(human_id)
        self.test_contributors.append(human_id)
        
        # Test AI contributor registration
        ai_id = self.attribution_manager.register_contributor(
            name="Test AI",
            contributor_type=ContributorType.AI,
            metadata={"model": "test-model"}
        )
        self.assertIsNotNone(ai_id)
        self.test_contributors.append(ai_id)
        
        # Test system contributor registration
        system_id = self.attribution_manager.register_contributor(
            name="Test System",
            contributor_type=ContributorType.SYSTEM
        )
        self.assertIsNotNone(system_id)
        self.test_contributors.append(system_id)
        
        # Verify contributors were registered
        self.assertEqual(len(self.attribution_manager.contributors), 3)
        
        # Test contributor info retrieval
        human_info = self.attribution_manager.get_contributor_info(human_id)
        self.assertIsNotNone(human_info)
        self.assertEqual(human_info.name, "Test Human")
        self.assertEqual(human_info.contributor_type, ContributorType.HUMAN)
        
        logger.info("[P24P6S2T1] Contributor registration test passed")
    
    def test_02_task_attribution(self):
        """Test task attribution tracking."""
        logger.info("[P24P6S2T1] Testing task attribution...")
        
        # Create test task
        task_id = "TEST-TASK-001"
        self.test_tasks.append(task_id)
        
        # Add contributions from different contributors
        for i, contributor_id in enumerate(self.test_contributors):
            role = [ContributionRole.CREATOR, ContributionRole.EDITOR, ContributionRole.REVIEWER][i]
            
            contribution_id = self.attribution_manager.add_contribution(
                task_id=task_id,
                contributor_id=contributor_id,
                role=role,
                content=f"Test contribution as {role.value}",
                confidence_score=0.8 + (i * 0.1),
                token_usage={"input": 100, "output": 200}
            )
            self.assertIsNotNone(contribution_id)
        
        # Verify task attribution
        attribution = self.attribution_manager.get_task_attribution(task_id)
        self.assertIsNotNone(attribution)
        self.assertEqual(len(attribution.contributions), 3)
        
        # Test attribution display data
        display_data = self.attribution_manager.get_attribution_display_data(task_id)
        self.assertIsNotNone(display_data)
        self.assertIn("contributors", display_data)
        self.assertIn("collaboration_score", display_data)
        
        logger.info("[P24P6S2T1] Task attribution test passed")
    
    def test_03_changelog_management(self):
        """Test changelog and revision management."""
        logger.info("[P24P6S2T1] Testing changelog management...")
        
        task_id = "TEST-TASK-002"
        self.test_tasks.append(task_id)
        
        # Create changelog
        changelog_id = self.changelog_manager.create_task_changelog(task_id)
        self.assertEqual(changelog_id, task_id)
        
        # Add revision with file changes
        file_changes = [{
            "file_path": "test.py",
            "change_type": "modified",
            "old_content": "print('old')",
            "new_content": "print('new')"
        }]
        
        revision_id = self.changelog_manager.add_revision(
            task_id=task_id,
            contributor_id=self.test_contributors[0],
            description="Test revision",
            file_changes=file_changes
        )
        self.assertIsNotNone(revision_id)
        
        # Verify changelog
        changelog = self.changelog_manager.get_task_changelog(task_id)
        self.assertIsNotNone(changelog)
        self.assertEqual(len(changelog.revisions), 1)
        
        # Test revision retrieval
        revision = self.changelog_manager.get_revision(task_id, 1)
        self.assertIsNotNone(revision)
        self.assertEqual(revision.description, "Test revision")
        
        logger.info("[P24P6S2T1] Changelog management test passed")
    
    def test_04_diff_viewer(self):
        """Test diff viewer functionality."""
        logger.info("[P24P6S2T1] Testing diff viewer...")
        
        old_content = """def hello():
    print("Hello, World!")
    return True"""
        
        new_content = """def hello():
    print("Hello, GitBridge!")
    logger.info("Function called")
    return True"""
        
        # Generate diff
        diff_result = self.diff_viewer.generate_diff(
            old_content=old_content,
            new_content=new_content,
            file_path="test.py"
        )
        
        self.assertIsNotNone(diff_result)
        self.assertEqual(diff_result.file_path, "test.py")
        self.assertIn("summary", diff_result.__dict__)
        
        # Test diff rendering
        html_diff = self.diff_viewer.render_diff(diff_result, "html")
        self.assertIsInstance(html_diff, str)
        self.assertIn("diff", html_diff.lower())
        
        markdown_diff = self.diff_viewer.render_diff(diff_result, "markdown")
        self.assertIsInstance(markdown_diff, str)
        
        json_diff = self.diff_viewer.render_diff(diff_result, "json")
        self.assertIsInstance(json_diff, str)
        
        logger.info("[P24P6S2T1] Diff viewer test passed")
    
    def test_05_activity_feed(self):
        """Test activity feed management."""
        logger.info("[P24P6S2T1] Testing activity feed...")
        
        # Create activity feed
        feed_id = "test_feed"
        self.activity_feed_manager.create_feed(feed_id)
        
        # Add activities
        activities = [
            {
                "activity_type": ActivityType.TASK_CREATED,
                "content": "Test task created",
                "priority": ActivityPriority.MEDIUM
            },
            {
                "activity_type": ActivityType.FILE_MODIFIED,
                "content": "Test file modified",
                "priority": ActivityPriority.HIGH
            },
            {
                "activity_type": ActivityType.COMMENT_ADDED,
                "content": "Test comment added",
                "priority": ActivityPriority.LOW
            }
        ]
        
        for activity_data in activities:
            activity_id = self.activity_feed_manager.add_activity(
                feed_id=feed_id,
                activity_type=activity_data["activity_type"],
                contributor_id=self.test_contributors[0],
                content=activity_data["content"],
                priority=activity_data["priority"]
            )
            self.assertIsNotNone(activity_id)
        
        # Get activities
        activities_list = self.activity_feed_manager.get_feed_activities(feed_id)
        self.assertEqual(len(activities_list), 3)
        
        # Test activity filtering
        high_priority_activities = self.activity_feed_manager.get_feed_activities(
            feed_id, priority=ActivityPriority.HIGH
        )
        self.assertEqual(len(high_priority_activities), 1)
        
        # Test feed summary
        summary = self.activity_feed_manager.get_feed_summary(feed_id)
        self.assertIsNotNone(summary)
        self.assertIn("total_activities", summary)
        
        logger.info("[P24P6S2T1] Activity feed test passed")
    
    def test_06_task_card_rendering(self):
        """Test task card rendering."""
        logger.info("[P24P6S2T1] Testing task card rendering...")
        
        # Create task card data
        task_data = TaskCardData(
            task_id="TEST-TASK-003",
            title="Test Task",
            description="This is a test task for rendering",
            status="in_progress",
            priority="medium",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Test HTML rendering
        html_card = self.task_card_renderer.render_task_card(task_data, "html")
        self.assertIsInstance(html_card, str)
        self.assertIn("task-card", html_card)
        self.assertIn("Test Task", html_card)
        
        # Test Markdown rendering
        markdown_card = self.task_card_renderer.render_task_card(task_data, "markdown")
        self.assertIsInstance(markdown_card, str)
        self.assertIn("Test Task", markdown_card)
        
        # Test JSON rendering
        json_card = self.task_card_renderer.render_task_card(task_data, "json")
        self.assertIsInstance(json_card, str)
        json_data = json.loads(json_card)
        self.assertEqual(json_data["task_id"], "TEST-TASK-003")
        
        logger.info("[P24P6S2T1] Task card rendering test passed")
    
    def test_07_data_export(self):
        """Test data export functionality."""
        logger.info("[P24P6S2T1] Testing data export...")
        
        export_dir = os.path.join(self.test_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        # Export attribution data
        attribution_export = os.path.join(export_dir, "attribution.json")
        self.attribution_manager.export_attribution_data(attribution_export)
        self.assertTrue(os.path.exists(attribution_export))
        
        # Verify exported data
        with open(attribution_export, 'r') as f:
            attribution_data = json.load(f)
        self.assertIsInstance(attribution_data, list)
        
        # Export changelog data
        changelog_export = os.path.join(export_dir, "changelog.json")
        self.changelog_manager.export_changelog_data(changelog_export)
        self.assertTrue(os.path.exists(changelog_export))
        
        # Export activity data
        activity_export = os.path.join(export_dir, "activity.json")
        self.activity_feed_manager.export_activity_data(activity_export)
        self.assertTrue(os.path.exists(activity_export))
        
        logger.info("[P24P6S2T1] Data export test passed")
    
    def test_08_integration_workflow(self):
        """Test complete integration workflow."""
        logger.info("[P24P6S2T1] Testing complete integration workflow...")
        
        # 1. Register contributors
        human_id = self.attribution_manager.register_contributor(
            name="Integration Test Human",
            contributor_type=ContributorType.HUMAN
        )
        ai_id = self.attribution_manager.register_contributor(
            name="Integration Test AI",
            contributor_type=ContributorType.AI
        )
        
        # 2. Create task and add contributions
        task_id = "INTEGRATION-TASK"
        self.attribution_manager.add_contribution(
            task_id=task_id,
            contributor_id=human_id,
            role=ContributionRole.CREATOR,
            content="Initial task creation"
        )
        
        self.attribution_manager.add_contribution(
            task_id=task_id,
            contributor_id=ai_id,
            role=ContributionRole.EDITOR,
            content="AI enhancement"
        )
        
        # 3. Create changelog and add revision
        self.changelog_manager.create_task_changelog(task_id)
        self.changelog_manager.add_revision(
            task_id=task_id,
            contributor_id=human_id,
            description="Initial implementation",
            file_changes=[{
                "file_path": "integration_test.py",
                "change_type": "created",
                "new_content": "print('Integration test')"
            }]
        )
        
        # 4. Add activities
        self.activity_feed_manager.add_activity(
            feed_id="main",
            activity_type=ActivityType.TASK_CREATED,
            contributor_id=human_id,
            task_id=task_id,
            content="Integration task created"
        )
        
        # 5. Verify integration
        attribution = self.attribution_manager.get_task_attribution(task_id)
        self.assertIsNotNone(attribution)
        self.assertEqual(len(attribution.contributions), 2)
        
        changelog = self.changelog_manager.get_task_changelog(task_id)
        self.assertIsNotNone(changelog)
        self.assertEqual(len(changelog.revisions), 1)
        
        activities = self.activity_feed_manager.get_feed_activities("main")
        self.assertGreater(len(activities), 0)
        
        # 6. Test task card rendering with real data
        task_data = TaskCardData(
            task_id=task_id,
            title="Integration Test Task",
            description="Complete workflow test",
            status="completed",
            priority="high",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        html_card = self.task_card_renderer.render_task_card(task_data, "html")
        self.assertIn("Integration Test Task", html_card)
        
        logger.info("[P24P6S2T1] Integration workflow test passed")
    
    def test_09_error_handling(self):
        """Test error handling and edge cases."""
        logger.info("[P24P6S2T1] Testing error handling...")
        
        # Test invalid contributor type
        with self.assertRaises(ValueError):
            self.attribution_manager.register_contributor(
                name="Test",
                contributor_type="invalid_type"
            )
        
        # Test invalid contribution role
        with self.assertRaises(ValueError):
            self.attribution_manager.add_contribution(
                task_id="test",
                contributor_id="invalid_id",
                role="invalid_role",
                content="test"
            )
        
        # Test invalid activity type
        with self.assertRaises(ValueError):
            self.activity_feed_manager.add_activity(
                feed_id="test",
                activity_type="invalid_activity",
                contributor_id="invalid_id",
                content="test"
            )
        
        # Test non-existent task attribution
        attribution = self.attribution_manager.get_task_attribution("non_existent")
        self.assertIsNone(attribution)
        
        # Test non-existent changelog
        changelog = self.changelog_manager.get_task_changelog("non_existent")
        self.assertIsNone(changelog)
        
        logger.info("[P24P6S2T1] Error handling test passed")
    
    def test_10_performance_benchmarks(self):
        """Test performance with larger datasets."""
        logger.info("[P24P6S2T1] Testing performance benchmarks...")
        
        import time
        
        # Test contributor registration performance
        start_time = time.time()
        for i in range(100):
            self.attribution_manager.register_contributor(
                name=f"PerfTest{i}",
                contributor_type=ContributorType.HUMAN
            )
        registration_time = time.time() - start_time
        
        # Test contribution addition performance
        start_time = time.time()
        for i in range(100):
            self.attribution_manager.add_contribution(
                task_id=f"PERF-TASK-{i}",
                contributor_id=self.test_contributors[0],
                role=ContributionRole.EDITOR,
                content=f"Performance test contribution {i}"
            )
        contribution_time = time.time() - start_time
        
        # Test activity addition performance
        start_time = time.time()
        for i in range(100):
            self.activity_feed_manager.add_activity(
                feed_id="main",
                activity_type=ActivityType.TASK_UPDATED,
                contributor_id=self.test_contributors[0],
                content=f"Performance test activity {i}"
            )
        activity_time = time.time() - start_time
        
        # Performance assertions (adjust thresholds as needed)
        self.assertLess(registration_time, 5.0, "Contributor registration too slow")
        self.assertLess(contribution_time, 5.0, "Contribution addition too slow")
        self.assertLess(activity_time, 5.0, "Activity addition too slow")
        
        logger.info(f"[P24P6S2T1] Performance benchmarks: "
                   f"Registration: {registration_time:.3f}s, "
                   f"Contributions: {contribution_time:.3f}s, "
                   f"Activities: {activity_time:.3f}s")

def run_integration_tests():
    """Run all Phase 24 integration tests."""
    logger.info("[P24P6S2T1] Starting Phase 24 integration tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test methods
    test_methods = [
        'test_01_contributor_registration',
        'test_02_task_attribution',
        'test_03_changelog_management',
        'test_04_diff_viewer',
        'test_05_activity_feed',
        'test_06_task_card_rendering',
        'test_07_data_export',
        'test_08_integration_workflow',
        'test_09_error_handling',
        'test_10_performance_benchmarks'
    ]
    
    for method_name in test_methods:
        test_suite.addTest(Phase24IntegrationTest(method_name))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Generate test report
    test_report = {
        "phase": "GBP24",
        "test_suite": "Phase 24 Integration Tests",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped) if hasattr(result, 'skipped') else 0,
            "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
        },
        "failures": [str(failure) for failure in result.failures],
        "errors": [str(error) for error in result.errors]
    }
    
    # Save test report
    os.makedirs("test_reports", exist_ok=True)
    with open("test_reports/phase24_integration_test_report.json", "w") as f:
        json.dump(test_report, f, indent=2, default=str)
    
    logger.info(f"[P24P6S2T1] Integration tests completed: {test_report['summary']}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1) 