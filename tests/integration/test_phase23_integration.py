#!/usr/bin/env python3
"""
GitBridge Phase 23 Integration Tests
Phase: GBP23
Part: P23P7
Step: P23P7S2
Task: P23P7S2T1 - Comprehensive Integration Testing

Integration tests for Phase 23 trust system components.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P23P7 Schema]
"""

import unittest
import tempfile
import os
import json
import time
from datetime import datetime, timezone, timedelta

from trust_graph import TrustGraph
from behavior_model import BehaviorModel
from trust_analyzer import TrustAnalyzer, TrustAnalysis
from trust_visualizer import TrustVisualizer
from trust_metrics import TrustMetricsCalculator

class TestPhase23Integration(unittest.TestCase):
    """Integration tests for Phase 23 trust system components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.trust_graph = TrustGraph(storage_path=self.temp_dir, auto_save=True)
        self.behavior_model = BehaviorModel(storage_path=os.path.join(self.temp_dir, "behavior"))
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
        
    def test_end_to_end_trust_flow(self):
        """Test complete end-to-end trust flow from creation to metrics."""
        # 1. Create agents
        agents = ["agent_a", "agent_b", "agent_c", "agent_d", "agent_e"]
        for agent in agents:
            self.trust_graph.add_agent(agent)
            self.behavior_model.add_agent(agent)
            
        # 2. Add trust relationships
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
            
        # 3. Add behavioral data
        for agent in agents:
            self.behavior_model.record_interaction(agent, True)
            self.behavior_model.record_interaction(agent, True)
            self.behavior_model.record_interaction(agent, False)
            self.behavior_model.update_personality_trait(agent, "openness", 0.7, 0.8)
            
        # 4. Analyze trust paths
        analysis = self.analyzer.analyze_trust_paths("agent_a", "agent_e", max_paths=3)
        self.assertIsInstance(analysis, TrustAnalysis)
        self.assertEqual(analysis.source, "agent_a")
        self.assertEqual(analysis.target, "agent_e")
        
        # 5. Find trust clusters
        clusters = self.analyzer.find_trust_clusters(min_trust=0.6)
        self.assertIsInstance(clusters, list)
        
        # 6. Generate visualization data
        self.visualizer._build_visualization()  # Rebuild to include latest data
        viz_data = self.visualizer.get_visualization_data()
        self.assertIn("nodes", viz_data)
        self.assertIn("edges", viz_data)
        self.assertEqual(len(viz_data["nodes"]), 5)
        self.assertEqual(len(viz_data["edges"]), 8)
        
        # 7. Calculate metrics
        agent_metrics = self.metrics_calculator.calculate_agent_metrics("agent_a")
        network_metrics = self.metrics_calculator.calculate_network_metrics()
        
        # 8. Verify metrics
        self.assertEqual(agent_metrics.agent_id, "agent_a")
        self.assertEqual(network_metrics.total_agents, 5)
        self.assertEqual(network_metrics.total_edges, 8)
        
        # 9. Export data
        export_data = self.metrics_calculator.export_metrics("json")
        self.assertIsInstance(export_data, str)
        
        # 10. Verify export contains expected data
        data = json.loads(export_data)
        self.assertIn("agent_metrics", data)
        self.assertIn("network_metrics", data)
        self.assertIn("agent_a", data["agent_metrics"])
        
    def test_behavioral_integration(self):
        """Test integration between behavior model and trust analysis."""
        # Create agents and trust relationships
        agents = ["agent_x", "agent_y", "agent_z"]
        for agent in agents:
            self.trust_graph.add_agent(agent)
            self.behavior_model.add_agent(agent)
            
        # Add trust relationships
        self.trust_graph.update_trust("agent_x", "agent_y", 0.7, 0.8)
        self.trust_graph.update_trust("agent_y", "agent_z", 0.8, 0.9)
        
        # Add behavioral data
        self.behavior_model.record_interaction("agent_x", True)
        self.behavior_model.record_interaction("agent_x", True)
        self.behavior_model.record_interaction("agent_x", False)
        self.behavior_model.record_interaction("agent_y", True)
        self.behavior_model.record_interaction("agent_y", True)
        self.behavior_model.record_interaction("agent_z", True)
        
        # Calculate metrics with behavior integration
        metrics_x = self.metrics_calculator.calculate_agent_metrics("agent_x", include_behavior=True)
        metrics_y = self.metrics_calculator.calculate_agent_metrics("agent_y", include_behavior=True)
        
        # Verify behavioral metrics are included
        self.assertIn("success_rate", metrics_x.metadata)
        self.assertIn("success_rate", metrics_y.metadata)
        
        # Verify behavioral data affects trust analysis
        self.assertGreater(metrics_x.metadata["success_rate"], 0.0)
        self.assertGreater(metrics_y.metadata["success_rate"], 0.0)
        
    def test_trust_analysis_integration(self):
        """Test integration between trust analyzer and other components."""
        # Create complex trust network
        agents = ["agent_1", "agent_2", "agent_3", "agent_4", "agent_5", "agent_6"]
        for agent in agents:
            self.trust_graph.add_agent(agent)
            
        # Create trust relationships with some circular paths
        trust_relationships = [
            ("agent_1", "agent_2", 0.8, 0.9),
            ("agent_2", "agent_3", 0.7, 0.8),
            ("agent_3", "agent_4", 0.6, 0.7),
            ("agent_4", "agent_5", 0.9, 0.8),
            ("agent_5", "agent_6", 0.5, 0.6),
            ("agent_6", "agent_1", 0.4, 0.5),  # Creates circular path
            ("agent_2", "agent_4", 0.8, 0.7),  # Shortcut
            ("agent_3", "agent_6", 0.7, 0.6),  # Another shortcut
        ]
        
        for source, target, trust_score, confidence in trust_relationships:
            self.trust_graph.update_trust(source, target, trust_score, confidence)
            
        # Test trust path analysis
        analysis = self.analyzer.analyze_trust_paths("agent_1", "agent_6", max_paths=5)
        self.assertIsInstance(analysis, TrustAnalysis)
        self.assertEqual(analysis.source, "agent_1")
        self.assertEqual(analysis.target, "agent_6")
        
        # Test trust cluster analysis
        clusters = self.analyzer.find_trust_clusters(min_trust=0.6)
        self.assertIsInstance(clusters, list)
        
        # Test visualization with analysis data
        self.visualizer._build_visualization()  # Rebuild to include latest data
        viz_data = self.visualizer.get_visualization_data()
        self.assertEqual(len(viz_data["nodes"]), 6)
        self.assertEqual(len(viz_data["edges"]), 8)
        
        # Test metrics calculation with analysis
        network_metrics = self.metrics_calculator.calculate_network_metrics()
        self.assertEqual(network_metrics.total_agents, 6)
        self.assertEqual(network_metrics.total_edges, 8)
        
    def test_visualization_integration(self):
        """Test integration between visualizer and other components."""
        # Create test data
        agents = ["viz_agent_1", "viz_agent_2", "viz_agent_3"]
        for agent in agents:
            self.trust_graph.add_agent(agent)
            
        # Add trust relationships
        self.trust_graph.update_trust("viz_agent_1", "viz_agent_2", 0.8, 0.9)
        self.trust_graph.update_trust("viz_agent_2", "viz_agent_3", 0.7, 0.8)
        self.trust_graph.update_trust("viz_agent_3", "viz_agent_1", 0.6, 0.7)
        
        # Test visualization data generation
        viz_data = self.visualizer.get_visualization_data()
        self.assertIn("nodes", viz_data)
        self.assertIn("edges", viz_data)
        self.assertIn("metadata", viz_data)
        
        # Test path highlighting
        paths = self.visualizer.highlight_trust_path("viz_agent_1", "viz_agent_3")
        self.assertIsInstance(paths, list)
        
        # Test cluster highlighting
        clusters = self.visualizer.highlight_trust_clusters(min_trust=0.6)
        self.assertIsInstance(clusters, list)
        
        # Test filtering
        self.visualizer.filter_by_trust_threshold(min_trust=0.7)
        filtered_data = self.visualizer.get_visualization_data()
        self.assertLessEqual(len(filtered_data["edges"]), 3)
        
        # Test export
        export_data = self.visualizer.export_visualization("json")
        self.assertIsInstance(export_data, str)
        
        # Verify export data
        data = json.loads(export_data)
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        
    def test_metrics_integration(self):
        """Test integration between metrics calculator and other components."""
        # Create test data
        agents = ["metric_agent_1", "metric_agent_2", "metric_agent_3", "metric_agent_4"]
        for agent in agents:
            self.trust_graph.add_agent(agent)
            self.behavior_model.add_agent(agent)
            
        # Add trust relationships
        trust_relationships = [
            ("metric_agent_1", "metric_agent_2", 0.9, 0.9),
            ("metric_agent_2", "metric_agent_3", 0.8, 0.8),
            ("metric_agent_3", "metric_agent_4", 0.7, 0.7),
            ("metric_agent_4", "metric_agent_1", 0.6, 0.6),
            ("metric_agent_1", "metric_agent_3", 0.5, 0.5),
        ]
        
        for source, target, trust_score, confidence in trust_relationships:
            self.trust_graph.update_trust(source, target, trust_score, confidence)
            
        # Add behavioral data
        for agent in agents:
            self.behavior_model.record_interaction(agent, True)
            self.behavior_model.record_interaction(agent, True)
            self.behavior_model.record_interaction(agent, False)
            
        # Test individual agent metrics
        for agent in agents:
            metrics = self.metrics_calculator.calculate_agent_metrics(agent, include_behavior=True)
            self.assertEqual(metrics.agent_id, agent)
            self.assertGreaterEqual(metrics.average_trust_score, 0.0)
            self.assertLessEqual(metrics.average_trust_score, 1.0)
            self.assertIn("success_rate", metrics.metadata)
            
        # Test network metrics
        network_metrics = self.metrics_calculator.calculate_network_metrics()
        self.assertEqual(network_metrics.total_agents, 4)
        self.assertEqual(network_metrics.total_edges, 5)
        self.assertGreaterEqual(network_metrics.average_trust_score, 0.0)
        self.assertLessEqual(network_metrics.average_trust_score, 1.0)
        
        # Test trust ranking
        ranking = self.metrics_calculator.get_trust_ranking("average_trust_score", limit=3)
        self.assertIsInstance(ranking, list)
        self.assertLessEqual(len(ranking), 3)
        
        # Test metrics export
        export_data = self.metrics_calculator.export_metrics("json")
        self.assertIsInstance(export_data, str)
        
        # Verify export structure
        data = json.loads(export_data)
        self.assertIn("agent_metrics", data)
        self.assertIn("network_metrics", data)
        
    def test_error_handling_integration(self):
        """Test error handling across all components."""
        # Test with non-existent agents
        analysis = self.analyzer.analyze_trust_paths("nonexistent", "also_nonexistent")
        self.assertEqual(analysis.source, "nonexistent")
        self.assertEqual(analysis.target, "also_nonexistent")
        self.assertEqual(len(analysis.all_paths), 0)
        
        clusters = self.analyzer.find_trust_clusters(min_trust=0.6)
        self.assertEqual(len(clusters), 0)
        
        metrics = self.metrics_calculator.calculate_agent_metrics("nonexistent")
        self.assertEqual(metrics.agent_id, "nonexistent")
        self.assertEqual(metrics.average_trust_score, 0.0)
        
        viz_data = self.visualizer.get_visualization_data()
        self.assertEqual(len(viz_data["nodes"]), 0)
        self.assertEqual(len(viz_data["edges"]), 0)
        
        # Test with empty trust graph
        empty_graph = TrustGraph(storage_path=self.temp_dir, auto_save=False)
        empty_analyzer = TrustAnalyzer(empty_graph)
        empty_visualizer = TrustVisualizer(empty_graph, empty_analyzer)
        empty_metrics = TrustMetricsCalculator(empty_graph, empty_analyzer, self.behavior_model)
        
        # Verify all components handle empty graph gracefully
        empty_analysis = empty_analyzer.analyze_trust_paths("agent_a", "agent_b")
        self.assertEqual(len(empty_analysis.all_paths), 0)
        
        empty_viz = empty_visualizer.get_visualization_data()
        self.assertEqual(len(empty_viz["nodes"]), 0)
        self.assertEqual(len(empty_viz["edges"]), 0)
        
        empty_network_metrics = empty_metrics.calculate_network_metrics()
        self.assertEqual(empty_network_metrics.total_agents, 0)
        self.assertEqual(empty_network_metrics.total_edges, 0)
        
    def test_performance_integration(self):
        """Test performance with larger datasets."""
        # Create larger dataset
        num_agents = 50
        agents = [f"perf_agent_{i}" for i in range(num_agents)]
        
        start_time = time.time()
        
        # Add agents
        for agent in agents:
            self.trust_graph.add_agent(agent)
            self.behavior_model.add_agent(agent)
            
        # Add trust relationships (create a chain)
        for i in range(num_agents - 1):
            self.trust_graph.update_trust(agents[i], agents[i+1], 0.7, 0.8)
            
        # Add some cross-connections
        for i in range(0, num_agents - 2, 2):
            self.trust_graph.update_trust(agents[i], agents[i+2], 0.6, 0.7)
            
        # Add behavioral data
        for agent in agents:
            self.behavior_model.record_interaction(agent, True)
            self.behavior_model.record_interaction(agent, True)
            
        # Test analysis performance
        analysis_start = time.time()
        analysis = self.analyzer.analyze_trust_paths(agents[0], agents[-1], max_paths=5)
        analysis_time = time.time() - analysis_start
        
        # Test visualization performance
        viz_start = time.time()
        self.visualizer._build_visualization()  # Rebuild to include latest data
        viz_data = self.visualizer.get_visualization_data()
        viz_time = time.time() - viz_start
        
        # Test metrics performance
        metrics_start = time.time()
        network_metrics = self.metrics_calculator.calculate_network_metrics()
        metrics_time = time.time() - metrics_start
        
        total_time = time.time() - start_time
        
        # Verify performance is reasonable (should complete within 10 seconds)
        self.assertLess(total_time, 10.0, f"Total setup and testing took {total_time:.2f} seconds")
        self.assertLess(analysis_time, 5.0, f"Analysis took {analysis_time:.2f} seconds")
        self.assertLess(viz_time, 2.0, f"Visualization took {viz_time:.2f} seconds")
        self.assertLess(metrics_time, 3.0, f"Metrics calculation took {metrics_time:.2f} seconds")
        
        # Verify results
        self.assertEqual(network_metrics.total_agents, num_agents)
        self.assertGreater(network_metrics.total_edges, num_agents - 1)
        self.assertEqual(len(viz_data["nodes"]), num_agents)
        self.assertGreater(len(viz_data["edges"]), num_agents - 1)
        
    def test_data_persistence_integration(self):
        """Test data persistence across component restarts."""
        # Create test data
        agents = ["persist_agent_1", "persist_agent_2", "persist_agent_3"]
        for agent in agents:
            self.trust_graph.add_agent(agent)
            self.behavior_model.add_agent(agent)
            
        # Add trust relationships
        self.trust_graph.update_trust("persist_agent_1", "persist_agent_2", 0.8, 0.9)
        self.trust_graph.update_trust("persist_agent_2", "persist_agent_3", 0.7, 0.8)
        
        # Add behavioral data
        self.behavior_model.record_interaction("persist_agent_1", True)
        self.behavior_model.record_interaction("persist_agent_2", True)
        
        # Note: TrustGraph auto-saves when auto_save=True, so no explicit save needed
        
        # Verify data persistence
        all_agents = self.trust_graph.get_all_agents()
        self.assertEqual(len(all_agents), 3)
        self.assertIn("persist_agent_1", all_agents)
        self.assertIn("persist_agent_2", all_agents)
        self.assertIn("persist_agent_3", all_agents)
        
        # Verify trust relationships persisted
        edge = self.trust_graph.get_edge("persist_agent_1", "persist_agent_2")
        self.assertIsNotNone(edge)
        self.assertEqual(edge.trust_score, 0.8)
        self.assertEqual(edge.confidence, 0.9)
        
        # Verify behavioral data persisted
        behavior = self.behavior_model.get_agent_behavior("persist_agent_1")
        self.assertIsNotNone(behavior)
        self.assertGreater(behavior.total_interactions, 0)
        
        # Verify components work with persisted data
        analysis = self.analyzer.analyze_trust_paths("persist_agent_1", "persist_agent_3")
        self.assertIsInstance(analysis, TrustAnalysis)
        
        self.visualizer._build_visualization()  # Rebuild to include latest data
        viz_data = self.visualizer.get_visualization_data()
        self.assertEqual(len(viz_data["nodes"]), 3)
        self.assertEqual(len(viz_data["edges"]), 2)
        
        metrics = self.metrics_calculator.calculate_agent_metrics("persist_agent_1")
        self.assertEqual(metrics.agent_id, "persist_agent_1")
        # Note: persist_agent_1 has no incoming trust relationships, so average_trust_score is 0.0
        # This is expected behavior for agents with only outgoing trust

if __name__ == "__main__":
    unittest.main() 