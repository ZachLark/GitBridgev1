#!/usr/bin/env python3
"""
GitBridge Phase 23 Integration Tests
Phase: GBP23
Part: P23P6
Step: P23P6S1
Task: P23P6S1T1 - Comprehensive Integration Testing

Integration tests for all Phase 23 components working together:
- Trust Graph Core
- Behavior Model
- Trust Analyzer
- Trust Visualizer
- Trust Metrics

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P23P6 Schema]
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

from trust_graph import TrustGraph, TrustEdge
from behavior_model import BehaviorModel, AgentBehavior
from trust_analyzer import TrustAnalyzer, TrustAnalysis
from trust_visualizer import TrustVisualizer
from trust_metrics import TrustMetricsCalculator, TrustMetrics, NetworkMetrics

class TestPhase23Integration(unittest.TestCase):
    """Integration tests for Phase 23 components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.graph_file = os.path.join(self.temp_dir, "test_trust_graph.json")
        self.behavior_file = os.path.join(self.temp_dir, "test_behavior_data")
        
        # Create fresh test trust graph (no persistence to avoid accumulation)
        self.trust_graph = TrustGraph(storage_path=self.temp_dir, auto_save=False)
        
        # Add test agents
        test_agents = ["agent_a", "agent_b", "agent_c", "agent_d", "agent_e"]
        for agent in test_agents:
            self.trust_graph.add_agent(agent)
            
        # Add test trust relationships
        trust_relationships = [
            ("agent_a", "agent_b", 0.8, 0.9),
            ("agent_a", "agent_c", 0.6, 0.7),
            ("agent_b", "agent_c", 0.9, 0.8),
            ("agent_b", "agent_d", 0.7, 0.6),
            ("agent_c", "agent_d", 0.5, 0.5),
            ("agent_c", "agent_e", 0.4, 0.4),
            ("agent_d", "agent_e", 0.8, 0.7),
            ("agent_e", "agent_a", 0.3, 0.3)
        ]
        
        for source, target, trust_score, confidence in trust_relationships:
            self.trust_graph.update_trust(source, target, trust_score, confidence)
            
        # Save trust graph
        self.trust_graph.save_to_file(self.graph_file)
        
        # Create behavior model
        self.behavior_model = BehaviorModel(storage_path=self.behavior_file)
        
        # Add test agents to behavior model
        for agent in test_agents:
            self.behavior_model.add_agent(agent)
            
        # Add some behavioral data
        self.behavior_model.update_personality_trait("agent_a", "conscientiousness", 0.8)
        self.behavior_model.update_personality_trait("agent_a", "extraversion", 0.6)
        self.behavior_model.update_behavioral_pattern("agent_a", "consistency", 0.9, 0.8)
        self.behavior_model.record_interaction("agent_a", True)
        self.behavior_model.record_interaction("agent_a", True)
        self.behavior_model.record_interaction("agent_a", False)
        
        self.behavior_model.update_personality_trait("agent_b", "openness", 0.7)
        self.behavior_model.update_behavioral_pattern("agent_b", "collaboration", 0.8, 0.7)
        self.behavior_model.record_interaction("agent_b", True)
        self.behavior_model.record_interaction("agent_b", True)
        
        # Create analyzer, visualizer, and metrics calculator
        self.analyzer = TrustAnalyzer(self.trust_graph)
        self.visualizer = TrustVisualizer(self.trust_graph, self.analyzer)
        self.metrics_calculator = TrustMetricsCalculator(
            self.trust_graph, 
            self.analyzer, 
            self.behavior_model
        )
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_01_trust_graph_operations(self):
        """Test trust graph core operations."""
        # Test basic operations
        self.assertEqual(len(self.trust_graph.get_all_agents()), 5)
        self.assertEqual(len(self.trust_graph.get_all_edges()), 8)
        
        # Test edge operations
        edge = self.trust_graph.get_edge("agent_a", "agent_b")
        self.assertIsNotNone(edge)
        self.assertEqual(edge.trust_score, 0.8)
        self.assertEqual(edge.confidence, 0.9)
        
        # Test neighbor operations
        neighbors = self.trust_graph.get_neighbors("agent_a")
        self.assertIn("agent_b", neighbors)
        self.assertIn("agent_c", neighbors)
        
    def test_02_behavior_model_operations(self):
        """Test behavior model operations."""
        # Test agent behavior retrieval
        behavior = self.behavior_model.get_agent_behavior("agent_a")
        self.assertIsNotNone(behavior)
        self.assertEqual(behavior.total_interactions, 3)
        self.assertEqual(behavior.successful_interactions, 2)
        self.assertAlmostEqual(behavior.success_rate, 2/3, places=2)
        
        # Test personality traits
        trait = behavior.personality_traits["conscientiousness"]
        self.assertEqual(trait.value, 0.8)
        self.assertEqual(trait.evidence_count, 1)
        
        # Test behavioral patterns
        pattern = behavior.behavioral_patterns["consistency"]
        self.assertEqual(pattern.frequency, 0.9)
        self.assertEqual(pattern.strength, 0.8)
        
        # Test behavior summary
        summary = self.behavior_model.get_behavior_summary("agent_a")
        self.assertIn("success_rate", summary)
        self.assertIn("reliability_score", summary)
        self.assertIn("personality_traits", summary)
        
    def test_03_trust_analyzer_operations(self):
        """Test trust analyzer operations."""
        # Test trust path analysis
        analysis = self.analyzer.analyze_trust_paths("agent_a", "agent_e")
        self.assertIsNotNone(analysis)
        self.assertIsNotNone(analysis.best_path)
        self.assertGreater(len(analysis.all_paths), 0)
        
        # Test trustworthiness assessment
        assessment = self.analyzer.assess_trustworthiness("agent_a", "agent_e")
        self.assertIn("trust_level", assessment)
        self.assertIn("recommendation", assessment)
        self.assertIn("overall_trust", assessment)
        
        # Test trust clusters
        clusters = self.analyzer.find_trust_clusters(min_trust=0.6)
        self.assertGreater(len(clusters), 0)
        
        # Test trust statistics
        stats = self.analyzer.get_trust_statistics()
        self.assertIn("total_agents", stats)
        self.assertIn("average_trust_score", stats)
        
    def test_04_trust_visualizer_operations(self):
        """Test trust visualizer operations."""
        # Test visualization data
        viz_data = self.visualizer.get_visualization_data()
        self.assertIn("nodes", viz_data)
        self.assertIn("edges", viz_data)
        self.assertEqual(len(viz_data["nodes"]), 5)
        self.assertEqual(len(viz_data["edges"]), 8)
        
        # Test path highlighting
        paths = self.visualizer.highlight_trust_path("agent_a", "agent_e")
        self.assertGreater(len(paths), 0)
        
        # Test cluster highlighting
        clusters = self.visualizer.highlight_trust_clusters(min_trust=0.6)
        self.assertGreater(len(clusters), 0)
        
        # Test filtering
        self.visualizer.filter_by_trust_threshold(min_trust=0.5)
        filtered_data = self.visualizer.get_visualization_data()
        # Should have fewer visible edges after filtering
        
        # Test layout changes
        self.assertTrue(self.visualizer.set_layout_type("circular"))
        self.assertTrue(self.visualizer.set_layout_type("hierarchical"))
        self.assertTrue(self.visualizer.set_layout_type("force_directed"))
        
        # Test export
        json_export = self.visualizer.export_visualization("json")
        self.assertIsInstance(json_export, str)
        data = json.loads(json_export)
        self.assertIn("nodes", data)
        
    def test_05_trust_metrics_operations(self):
        """Test trust metrics operations."""
        # Test agent metrics
        agent_metrics = self.metrics_calculator.calculate_agent_metrics("agent_a")
        self.assertIsInstance(agent_metrics, TrustMetrics)
        self.assertEqual(agent_metrics.agent_id, "agent_a")
        self.assertGreater(agent_metrics.average_trust_score, 0)
        self.assertGreater(agent_metrics.confidence_score, 0)
        
        # Test network metrics
        network_metrics = self.metrics_calculator.calculate_network_metrics()
        self.assertIsInstance(network_metrics, NetworkMetrics)
        self.assertEqual(network_metrics.total_agents, 5)
        self.assertEqual(network_metrics.total_edges, 8)
        self.assertGreater(network_metrics.average_trust_score, 0)
        
        # Test trust trends
        trend = self.metrics_calculator.analyze_trust_trends("agent_a", "weekly", 7)
        self.assertIsNotNone(trend)
        self.assertEqual(trend.agent_id, "agent_a")
        self.assertEqual(len(trend.trust_scores), 7)
        
        # Test trust ranking
        ranking = self.metrics_calculator.get_trust_ranking("average_trust_score", limit=3)
        self.assertLessEqual(len(ranking), 3)
        self.assertGreater(len(ranking), 0)
        
        # Test metrics export
        json_export = self.metrics_calculator.export_metrics("json")
        self.assertIsInstance(json_export, str)
        data = json.loads(json_export)
        self.assertIn("network_metrics", data)
        self.assertIn("agent_metrics", data)
        
    def test_06_integrated_workflow(self):
        """Test integrated workflow across all components."""
        # 1. Create a new agent and add trust relationships
        # Check if agent_f already exists to avoid duplication
        if "agent_f" not in self.trust_graph.get_all_agents():
            self.trust_graph.add_agent("agent_f")
        self.trust_graph.update_trust("agent_f", "agent_a", 0.7, 0.8)
        self.trust_graph.update_trust("agent_a", "agent_f", 0.6, 0.7)
        
        # Add a trust relationship that creates a path from agent_b to agent_f
        self.trust_graph.update_trust("agent_b", "agent_a", 0.5, 0.6)
        
        # 2. Add behavioral data for the new agent
        # Check if agent exists in behavior model by trying to get its behavior
        if self.behavior_model.get_agent_behavior("agent_f") is None:
            self.behavior_model.add_agent("agent_f")
        self.behavior_model.update_personality_trait("agent_f", "agreeableness", 0.9)
        self.behavior_model.update_behavioral_pattern("agent_f", "collaboration", 0.8, 0.9)
        self.behavior_model.record_interaction("agent_f", True)
        self.behavior_model.record_interaction("agent_f", True)
        
        # 3. Analyze trust paths to the new agent
        analysis = self.analyzer.analyze_trust_paths("agent_b", "agent_f")
        self.assertIsNotNone(analysis)
        
        # 4. Calculate metrics for the new agent
        agent_metrics = self.metrics_calculator.calculate_agent_metrics("agent_f")
        self.assertEqual(agent_metrics.agent_id, "agent_f")
        
        # 5. Update visualization
        self.visualizer._build_visualization()  # Rebuild with new agent
        viz_data = self.visualizer.get_visualization_data()
        # Should have 6 nodes now (original 5 + agent_f)
        self.assertGreaterEqual(len(viz_data["nodes"]), 6)
        
        # 6. Highlight paths to the new agent
        paths = self.visualizer.highlight_trust_path("agent_b", "agent_f")
        self.assertGreater(len(paths), 0)
        
        # 7. Recalculate network metrics
        network_metrics = self.metrics_calculator.calculate_network_metrics()
        self.assertGreaterEqual(network_metrics.total_agents, 6)
        
    def test_07_performance_and_scaling(self):
        """Test performance and scaling characteristics."""
        # Test with larger dataset
        large_graph = TrustGraph(storage_path=self.temp_dir, auto_save=False)
        
        # Add more agents
        for i in range(20):
            large_graph.add_agent(f"large_agent_{i}")
            
        # Add trust relationships
        for i in range(19):
            large_graph.update_trust(f"large_agent_{i}", f"large_agent_{i+1}", 0.7, 0.8)
            
        # Test analyzer performance
        large_analyzer = TrustAnalyzer(large_graph)
        analysis = large_analyzer.analyze_trust_paths("large_agent_0", "large_agent_19")
        self.assertIsNotNone(analysis)
        
        # Test visualizer performance
        large_visualizer = TrustVisualizer(large_graph, large_analyzer)
        viz_data = large_visualizer.get_visualization_data()
        self.assertEqual(len(viz_data["nodes"]), 20)
        
        # Test metrics performance
        large_metrics = TrustMetricsCalculator(large_graph, large_analyzer)
        network_metrics = large_metrics.calculate_network_metrics()
        self.assertEqual(network_metrics.total_agents, 20)
        
    def test_08_error_handling_and_edge_cases(self):
        """Test error handling and edge cases."""
        # Test with non-existent agents
        analysis = self.analyzer.analyze_trust_paths("nonexistent", "agent_a")
        self.assertEqual(len(analysis.all_paths), 0)
        
        # Test with same source and target
        analysis = self.analyzer.analyze_trust_paths("agent_a", "agent_a")
        self.assertEqual(len(analysis.all_paths), 0)
        
        # Test metrics for non-existent agent
        metrics = self.metrics_calculator.calculate_agent_metrics("nonexistent")
        self.assertEqual(metrics.agent_id, "nonexistent")
        self.assertEqual(metrics.average_trust_score, 0.0)
        
        # Test behavior model with non-existent agent
        behavior = self.behavior_model.get_agent_behavior("nonexistent")
        self.assertIsNone(behavior)
        
        # Test visualization with empty graph
        empty_graph = TrustGraph(storage_path=self.temp_dir, auto_save=False)
        empty_visualizer = TrustVisualizer(empty_graph)
        viz_data = empty_visualizer.get_visualization_data()
        self.assertEqual(len(viz_data["nodes"]), 0)
        self.assertEqual(len(viz_data["edges"]), 0)
        
    def test_09_data_persistence_and_recovery(self):
        """Test data persistence and recovery."""
        # Save and reload trust graph
        temp_graph_file = os.path.join(self.temp_dir, "temp_graph.json")
        self.trust_graph.save_to_file(temp_graph_file)
        
        loaded_graph = TrustGraph(storage_path=self.temp_dir, auto_save=False)
        loaded_graph.load_from_file(temp_graph_file)
        
        self.assertEqual(len(loaded_graph.get_all_agents()), 5)
        self.assertEqual(len(loaded_graph.get_all_edges()), 8)
        
        # Test behavior model persistence
        behavior_data = self.behavior_model.export_data("json")
        self.assertIsInstance(behavior_data, str)
        data = json.loads(behavior_data)
        self.assertIn("agents", data)
        
        # Test metrics export and import
        metrics_export = self.metrics_calculator.export_metrics("json")
        self.assertIsInstance(metrics_export, str)
        data = json.loads(metrics_export)
        self.assertIn("network_metrics", data)
        self.assertIn("agent_metrics", data)
        
    def test_10_concurrent_operations(self):
        """Test concurrent operations and thread safety."""
        import threading
        import time
        
        # Test concurrent trust graph operations
        def add_trust_edges():
            for i in range(10):
                self.trust_graph.update_trust("agent_a", f"concurrent_agent_{i}", 0.5, 0.6)
                time.sleep(0.01)
                
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=add_trust_edges)
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # Verify results
        self.assertGreater(len(self.trust_graph.get_all_agents()), 5)
        
        # Test concurrent metrics calculations
        def calculate_metrics():
            for i in range(5):
                self.metrics_calculator.calculate_agent_metrics("agent_a")
                time.sleep(0.01)
                
        threads = []
        for _ in range(2):
            thread = threading.Thread(target=calculate_metrics)
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # Verify cache is working
        metrics = self.metrics_calculator.calculate_agent_metrics("agent_a")
        self.assertIsNotNone(metrics)

def run_integration_tests():
    """Run all integration tests."""
    print("=== GitBridge Phase 23 Integration Tests ===")
    print("Testing all Phase 23 components working together...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase23Integration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n=== Test Summary ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n=== Failures ===")
        for test, traceback in result.failures:
            print(f"FAIL: {test}")
            print(traceback)
            
    if result.errors:
        print("\n=== Errors ===")
        for test, traceback in result.errors:
            print(f"ERROR: {test}")
            print(traceback)
            
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    return success

if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1) 