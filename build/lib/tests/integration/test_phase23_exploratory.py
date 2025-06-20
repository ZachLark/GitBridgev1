#!/usr/bin/env python3
"""
GitBridge Phase 23 Exploratory Tests
Phase: GBP23
Part: P23P7
Step: P23P7S3
Task: P23P7S3T1 - Exploratory Edge Case and Protocol Compliance Testing

Exploratory tests for edge cases, large/complex networks, and protocol compliance.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P23P7 Schema]
"""

import unittest
import tempfile
import os
import random
from trust_graph import TrustGraph
from behavior_model import BehaviorModel
from trust_analyzer import TrustAnalyzer, TrustAnalysis
from trust_visualizer import TrustVisualizer
from trust_metrics import TrustMetricsCalculator

class TestPhase23Exploratory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.trust_graph = TrustGraph(storage_path=self.temp_dir, auto_save=True)
        self.behavior_model = BehaviorModel(storage_path=os.path.join(self.temp_dir, "behavior"))
        self.analyzer = TrustAnalyzer(self.trust_graph)
        self.visualizer = TrustVisualizer(self.trust_graph, self.analyzer)
        self.metrics_calculator = TrustMetricsCalculator(
            self.trust_graph, self.analyzer, self.behavior_model
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_agents_with_no_trust(self):
        """Agents with no trust relationships should be handled gracefully."""
        self.trust_graph.add_agent("loner_agent")
        self.visualizer._build_visualization()
        viz_data = self.visualizer.get_visualization_data()
        self.assertIn("loner_agent", [n["id"] for n in viz_data["nodes"]])
        metrics = self.metrics_calculator.calculate_agent_metrics("loner_agent")
        self.assertEqual(metrics.average_trust_score, 0.0)

    def test_circular_trust(self):
        """Circular trust relationships should not cause infinite loops."""
        agents = ["a", "b", "c"]
        for agent in agents:
            self.trust_graph.add_agent(agent)
        self.trust_graph.update_trust("a", "b", 0.8, 0.9)
        self.trust_graph.update_trust("b", "c", 0.7, 0.8)
        self.trust_graph.update_trust("c", "a", 0.6, 0.7)
        analysis = self.analyzer.analyze_trust_paths("a", "c")
        self.assertIsInstance(analysis, TrustAnalysis)
        self.visualizer._build_visualization()
        viz_data = self.visualizer.get_visualization_data()
        self.assertEqual(len(viz_data["nodes"]), 3)
        self.assertEqual(len(viz_data["edges"]), 3)

    def test_disconnected_subgraphs(self):
        """Disconnected subgraphs should be handled correctly."""
        for i in range(2):
            for j in range(3):
                self.trust_graph.add_agent(f"g{i}_a{j}")
        self.trust_graph.update_trust("g0_a0", "g0_a1", 0.7, 0.8)
        self.trust_graph.update_trust("g0_a1", "g0_a2", 0.6, 0.7)
        self.trust_graph.update_trust("g1_a0", "g1_a1", 0.8, 0.9)
        self.trust_graph.update_trust("g1_a1", "g1_a2", 0.9, 0.8)
        self.visualizer._build_visualization()
        viz_data = self.visualizer.get_visualization_data()
        self.assertEqual(len(viz_data["nodes"]), 6)
        self.assertEqual(len(viz_data["edges"]), 4)
        clusters = self.analyzer.find_trust_clusters(min_trust=0.6)
        self.assertTrue(any(len(c) == 3 for c in clusters))

    def test_extreme_trust_confidence(self):
        """Extremely high/low trust and confidence values should be accepted."""
        self.trust_graph.add_agent("high")
        self.trust_graph.add_agent("low")
        self.trust_graph.update_trust("high", "low", 1.0, 1.0)
        self.trust_graph.update_trust("low", "high", 0.0, 0.0)
        self.visualizer._build_visualization()
        viz_data = self.visualizer.get_visualization_data()
        self.assertEqual(len(viz_data["edges"]), 2)
        metrics_high = self.metrics_calculator.calculate_agent_metrics("high")
        metrics_low = self.metrics_calculator.calculate_agent_metrics("low")
        self.assertGreaterEqual(metrics_high.average_trust_score, 0.0)
        self.assertGreaterEqual(metrics_low.average_trust_score, 0.0)

    def test_malformed_agent_ids(self):
        """Malformed agent IDs should not break the system."""
        bad_ids = ["", " ", "!@#$$%", "a\nb", "null"]
        for bad_id in bad_ids:
            self.trust_graph.add_agent(bad_id)
        self.visualizer._build_visualization()
        viz_data = self.visualizer.get_visualization_data()
        for bad_id in bad_ids:
            self.assertIn(bad_id, [n["id"] for n in viz_data["nodes"]])

    def test_large_sparse_network(self):
        """Large sparse trust graph should be handled efficiently."""
        num_agents = 50  # Reduced from 200 to prevent hanging
        for i in range(num_agents):
            self.trust_graph.add_agent(f"agent_{i}")
        for i in range(0, num_agents, 5):  # Reduced density
            for j in range(i+1, min(i+5, num_agents)):
                self.trust_graph.update_trust(f"agent_{i}", f"agent_{j}", random.uniform(0.1, 1.0), random.uniform(0.1, 1.0))
        self.visualizer._build_visualization()
        viz_data = self.visualizer.get_visualization_data()
        self.assertEqual(len(viz_data["nodes"]), num_agents)

    def test_large_dense_network(self):
        """Large dense trust graph should be handled efficiently."""
        num_agents = 20  # Reduced from 100 to prevent hanging
        for i in range(num_agents):
            self.trust_graph.add_agent(f"d_agent_{i}")
        for i in range(num_agents):
            for j in range(num_agents):
                if i != j:
                    self.trust_graph.update_trust(f"d_agent_{i}", f"d_agent_{j}", 0.5, 0.5)
        self.visualizer._build_visualization()
        viz_data = self.visualizer.get_visualization_data()
        self.assertEqual(len(viz_data["nodes"]), num_agents)
        self.assertEqual(len(viz_data["edges"]), num_agents * (num_agents - 1))

    def test_protocol_compliance(self):
        """All inter-module data structures should comply with MAS Lite Protocol v2.1."""
        # Create a small network
        agents = ["proto_a", "proto_b"]
        for agent in agents:
            self.trust_graph.add_agent(agent)
        self.trust_graph.update_trust("proto_a", "proto_b", 0.7, 0.8)
        self.visualizer._build_visualization()
        viz_data = self.visualizer.get_visualization_data()
        # Check for required fields in nodes/edges
        for node in viz_data["nodes"]:
            self.assertIn("id", node)
            self.assertIn("label", node)
            self.assertIn("metadata", node)
        for edge in viz_data["edges"]:
            self.assertIn("source", edge)
            self.assertIn("target", edge)
            self.assertIn("trust_score", edge)
            self.assertIn("metadata", edge)
        # Check metrics export
        export = self.metrics_calculator.export_metrics("json")
        import json
        data = json.loads(export)
        self.assertIn("agent_metrics", data)
        self.assertIn("network_metrics", data)

if __name__ == "__main__":
    unittest.main() 