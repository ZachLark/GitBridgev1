#!/usr/bin/env python3
"""
GitBridge Arbitration Engine Tests
Phase: GBP22
Part: P22P5
Step: P22P5S1
Task: P22P5S1T1 - Arbitration Engine Test Implementation

Unit tests for arbitration engine and strategies.
End-to-end arbitration tests simulating conflicting agent responses.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P22P5 Schema]
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from arbitration_engine import (
    ArbitrationEngine, 
    AgentOutput, 
    ArbitrationConflict, 
    ArbitrationResult,
    ArbitrationPluginBase
)

class TestArbitrationEngine(unittest.TestCase):
    """Test cases for ArbitrationEngine."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugins_dir = Path(self.temp_dir) / "plugins" / "arbitration"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy strategy plugins to test directory
        source_plugins = Path(__file__).parent.parent / "plugins" / "arbitration"
        if source_plugins.exists():
            for plugin_file in source_plugins.glob("*.py"):
                shutil.copy2(plugin_file, self.plugins_dir)
        
        # Create test config
        self.config_path = Path(self.temp_dir) / "arbitration_config.json"
        
        # Initialize engine
        self.engine = ArbitrationEngine(
            plugins_dir=str(self.plugins_dir),
            config_path=str(self.config_path)
        )
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
        
    def test_engine_initialization(self):
        """Test arbitration engine initialization."""
        self.assertIsNotNone(self.engine)
        # Should have loaded the strategy plugins
        self.assertGreater(len(self.engine.strategies), 0)
        self.assertIsInstance(self.engine.config, dict)
        
    def test_config_loading(self):
        """Test configuration loading."""
        config = self.engine.config
        self.assertIn("default_strategy", config)
        self.assertIn("fallback_strategy", config)
        self.assertIn("timeout_ms", config)
        
    def test_conflict_type_detection(self):
        """Test conflict type detection."""
        # Test contradiction
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8),
            AgentOutput("agent2", "task1", "subtask1", "answer2", 0.9)
        ]
        conflict_type = self.engine._determine_conflict_type(outputs)
        self.assertEqual(conflict_type, "contradiction")
        
        # Test quality dispute
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.9),
            AgentOutput("agent2", "task1", "subtask1", "answer1", 0.5)
        ]
        conflict_type = self.engine._determine_conflict_type(outputs)
        self.assertEqual(conflict_type, "quality_dispute")
        
        # Test error
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8, error_count=1),
            AgentOutput("agent2", "task1", "subtask1", "answer1", 0.9)
        ]
        conflict_type = self.engine._determine_conflict_type(outputs)
        self.assertEqual(conflict_type, "error")
        
    def test_fallback_arbitration(self):
        """Test fallback arbitration when strategy fails."""
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8),
            AgentOutput("agent2", "task1", "subtask1", "answer2", 0.9)
        ]
        
        conflict = ArbitrationConflict(
            conflict_id="test_conflict",
            task_id="task1",
            subtask_id="subtask1",
            agent_outputs=outputs,
            conflict_type="contradiction"
        )
        
        result = self.engine._fallback_arbitration(conflict, Exception("Test error"))
        
        self.assertIsInstance(result, ArbitrationResult)
        self.assertEqual(result.winner_agent_id, "agent2")  # Higher confidence
        self.assertEqual(result.strategy_used, "fallback_confidence")
        self.assertTrue(result.fallback_triggered)
        
    def test_arbitration_history(self):
        """Test arbitration history retrieval."""
        # Add some test results
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8),
            AgentOutput("agent2", "task1", "subtask1", "answer2", 0.9)
        ]
        
        result = self.engine.arbitrate_conflict(outputs, "task1", "subtask1")
        
        # Test filtering
        history = self.engine.get_arbitration_history(task_id="task1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].winner_agent_id, result.winner_agent_id)
        
        history = self.engine.get_arbitration_history(agent_id="agent2")
        self.assertEqual(len(history), 1)
        
    def test_export_logs(self):
        """Test log export functionality."""
        # Add some test data
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8),
            AgentOutput("agent2", "task1", "subtask1", "answer2", 0.9)
        ]
        
        self.engine.arbitrate_conflict(outputs, "task1", "subtask1")
        
        # Test export
        export_path = Path(self.temp_dir) / "export.json"
        success = self.engine.export_arbitration_logs(str(export_path))
        
        self.assertTrue(success)
        self.assertTrue(export_path.exists())
        
        # Verify export content
        with open(export_path, 'r') as f:
            export_data = json.load(f)
            
        self.assertIn("total_conflicts", export_data)
        self.assertIn("total_results", export_data)
        self.assertEqual(export_data["total_conflicts"], 1)
        self.assertEqual(export_data["total_results"], 1)
        
    def test_statistics(self):
        """Test statistics generation."""
        # Add some test data
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8),
            AgentOutput("agent2", "task1", "subtask1", "answer2", 0.9)
        ]
        
        self.engine.arbitrate_conflict(outputs, "task1", "subtask1")
        
        stats = self.engine.get_statistics()
        
        self.assertIn("total_arbitrations", stats)
        self.assertIn("strategy_usage", stats)
        self.assertIn("agent_wins", stats)
        self.assertEqual(stats["total_arbitrations"], 1)

class TestArbitrationStrategies(unittest.TestCase):
    """Test cases for arbitration strategies."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugins_dir = Path(self.temp_dir) / "plugins" / "arbitration"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy strategy plugins to test directory
        source_plugins = Path(__file__).parent.parent / "plugins" / "arbitration"
        if source_plugins.exists():
            for plugin_file in source_plugins.glob("*.py"):
                shutil.copy2(plugin_file, self.plugins_dir)
                
        # Initialize engine
        self.engine = ArbitrationEngine(plugins_dir=str(self.plugins_dir))
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
        
    def test_majority_vote_strategy(self):
        """Test majority vote strategy."""
        # Create test outputs with majority agreement
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8),
            AgentOutput("agent2", "task1", "subtask1", "answer1", 0.9),
            AgentOutput("agent3", "task1", "subtask1", "answer2", 0.7)
        ]
        
        result = self.engine.arbitrate_conflict(outputs, "task1", "subtask1", "majority_vote")
        
        self.assertIsInstance(result, ArbitrationResult)
        self.assertIn(result.winner_agent_id, ["agent1", "agent2"])  # One of the agents with "answer1"
        self.assertEqual(result.winning_output, "answer1")
        
    def test_confidence_weight_strategy(self):
        """Test confidence weight strategy."""
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8),
            AgentOutput("agent2", "task1", "subtask1", "answer2", 0.9),
            AgentOutput("agent3", "task1", "subtask1", "answer3", 0.7)
        ]
        
        result = self.engine.arbitrate_conflict(outputs, "task1", "subtask1", "confidence_weight")
        
        self.assertIsInstance(result, ArbitrationResult)
        self.assertEqual(result.winner_agent_id, "agent2")  # Highest confidence
        self.assertEqual(result.winning_output, "answer2")
        
    def test_recency_bias_strategy(self):
        """Test recency bias strategy."""
        now = datetime.now(timezone.utc)
        
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8, timestamp=now),
            AgentOutput("agent2", "task1", "subtask1", "answer2", 0.9, timestamp=now),
            AgentOutput("agent3", "task1", "subtask1", "answer3", 0.7, timestamp=now)
        ]
        
        result = self.engine.arbitrate_conflict(outputs, "task1", "subtask1", "recency_bias")
        
        self.assertIsInstance(result, ArbitrationResult)
        # Should select agent2 due to highest confidence (all timestamps are same)
        self.assertEqual(result.winner_agent_id, "agent2")
        
    def test_strategy_fallback(self):
        """Test strategy fallback when primary strategy not found."""
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8),
            AgentOutput("agent2", "task1", "subtask1", "answer2", 0.9)
        ]
        
        # Try to use non-existent strategy
        result = self.engine.arbitrate_conflict(outputs, "task1", "subtask1", "non_existent_strategy")
        
        self.assertIsInstance(result, ArbitrationResult)
        # Should fall back to confidence-based selection
        self.assertEqual(result.winner_agent_id, "agent2")

class TestEndToEndArbitration(unittest.TestCase):
    """End-to-end arbitration tests."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugins_dir = Path(self.temp_dir) / "plugins" / "arbitration"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy strategy plugins
        source_plugins = Path(__file__).parent.parent / "plugins" / "arbitration"
        if source_plugins.exists():
            for plugin_file in source_plugins.glob("*.py"):
                shutil.copy2(plugin_file, self.plugins_dir)
                
        self.engine = ArbitrationEngine(plugins_dir=str(self.plugins_dir))
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
        
    def test_conflicting_agent_responses(self):
        """Test arbitration with conflicting agent responses."""
        # Simulate conflicting responses
        outputs = [
            AgentOutput("openai_gpt4o", "code_review", "security_check", "No vulnerabilities found", 0.85),
            AgentOutput("grok_3", "code_review", "security_check", "SQL injection vulnerability detected", 0.92),
            AgentOutput("cursor_assistant", "code_review", "security_check", "No vulnerabilities found", 0.78)
        ]
        
        # Test different strategies
        strategies = ["majority_vote", "confidence_weight", "recency_bias"]
        
        for strategy in strategies:
            with self.subTest(strategy=strategy):
                result = self.engine.arbitrate_conflict(outputs, "code_review", "security_check", strategy)
                
                self.assertIsInstance(result, ArbitrationResult)
                self.assertIn(result.winner_agent_id, ["openai_gpt4o", "grok_3", "cursor_assistant"])
                self.assertIn(result.winning_output, ["No vulnerabilities found", "SQL injection vulnerability detected"])
                
    def test_agent_failure_fallback(self):
        """Test fallback execution when agent fails."""
        # Simulate agent failure
        outputs = [
            AgentOutput("openai_gpt4o", "analysis", "data_processing", "Analysis complete", 0.9, error_count=0),
            AgentOutput("grok_3", "analysis", "data_processing", "Error occurred", 0.0, error_count=3),
            AgentOutput("cursor_assistant", "analysis", "data_processing", "Analysis complete", 0.8, error_count=0)
        ]
        
        result = self.engine.arbitrate_conflict(outputs, "analysis", "data_processing", "confidence_weight")
        
        self.assertIsInstance(result, ArbitrationResult)
        # Should select openai_gpt4o (highest confidence, no errors)
        self.assertEqual(result.winner_agent_id, "openai_gpt4o")
        
    def test_timeout_handling(self):
        """Test timeout handling in arbitration."""
        # Simulate timeout scenario
        outputs = [
            AgentOutput("openai_gpt4o", "complex_task", "subtask1", "Result", 0.9, execution_time_ms=15000),
            AgentOutput("grok_3", "complex_task", "subtask1", "Result", 0.8, execution_time_ms=35000),  # Timeout
            AgentOutput("cursor_assistant", "complex_task", "subtask1", "Result", 0.85, execution_time_ms=12000)
        ]
        
        result = self.engine.arbitrate_conflict(outputs, "complex_task", "subtask1", "confidence_weight")
        
        self.assertIsInstance(result, ArbitrationResult)
        # Should select openai_gpt4o (highest confidence, no timeout)
        self.assertEqual(result.winner_agent_id, "openai_gpt4o")

if __name__ == "__main__":
    unittest.main() 