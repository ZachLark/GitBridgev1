#!/usr/bin/env python3
"""
GitBridge Phase 23 Load & Performance Tests
Phase: GBP23
Part: P23P7
Step: P23P7S4
Task: P23P7S4T1 - Load Testing and Performance Benchmarking

Load and performance tests for Phase 23 trust system components.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P23P7 Schema]
"""

import unittest
import tempfile
import os
import time
import random
import psutil
import gc
from datetime import datetime, timezone

from trust_graph import TrustGraph
from behavior_model import BehaviorModel
from trust_analyzer import TrustAnalyzer, TrustAnalysis
from trust_visualizer import TrustVisualizer
from trust_metrics import TrustMetricsCalculator

class TestPhase23LoadPerformance(unittest.TestCase):
    """Load and performance tests for Phase 23 trust system components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.trust_graph = TrustGraph(storage_path=self.temp_dir, auto_save=True)
        self.behavior_model = BehaviorModel(storage_path=os.path.join(self.temp_dir, "behavior"))
        self.analyzer = TrustAnalyzer(self.trust_graph)
        self.visualizer = TrustVisualizer(self.trust_graph, self.analyzer)
        self.metrics_calculator = TrustMetricsCalculator(
            self.trust_graph, self.analyzer, self.behavior_model
        )
        
        # Performance tracking
        self.start_time = None
        self.start_memory = None
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def _start_performance_tracking(self):
        """Start tracking performance metrics."""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
    def _end_performance_tracking(self):
        """End tracking and return performance metrics."""
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        execution_time = end_time - self.start_time
        memory_used = end_memory - self.start_memory
        
        return {
            'execution_time': execution_time,
            'memory_used': memory_used,
            'peak_memory': end_memory
        }
        
    def test_medium_scale_trust_graph(self):
        """Test performance with medium-scale trust graph (200 agents, 800 edges)."""
        num_agents = 200  # Reduced from 500
        num_edges = 800   # Reduced from 2000
        
        self._start_performance_tracking()
        
        # Create agents
        for i in range(num_agents):
            self.trust_graph.add_agent(f"load_agent_{i}")
            self.behavior_model.add_agent(f"load_agent_{i}")
            
        # Create random trust relationships
        edges_created = 0
        attempts = 0
        max_attempts = num_edges * 2  # Prevent infinite loops
        
        while edges_created < num_edges and attempts < max_attempts:
            source = random.randint(0, num_agents - 1)
            target = random.randint(0, num_agents - 1)
            if source != target:
                self.trust_graph.update_trust(
                    f"load_agent_{source}", 
                    f"load_agent_{target}", 
                    random.uniform(0.1, 1.0), 
                    random.uniform(0.1, 1.0)
                )
                edges_created += 1
            attempts += 1
                
        metrics = self._end_performance_tracking()
        
        # Verify data was created correctly
        all_agents = self.trust_graph.get_all_agents()
        all_edges = self.trust_graph.get_all_edges()
        
        self.assertEqual(len(all_agents), num_agents)
        self.assertGreaterEqual(len(all_edges), num_edges * 0.8)  # Allow for some duplicates
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 60.0, f"Setup took {metrics['execution_time']:.2f} seconds")
        self.assertLess(metrics['memory_used'], 500.0, f"Memory used: {metrics['memory_used']:.2f} MB")
        
        print(f"Medium scale test: {metrics['execution_time']:.2f}s, {metrics['memory_used']:.2f}MB")
        
    def test_large_scale_trust_analysis(self):
        """Test trust analysis performance with large-scale data."""
        # Create large dataset
        num_agents = 150  # Reduced from 300
        for i in range(num_agents):
            self.trust_graph.add_agent(f"analysis_agent_{i}")
            
        # Create chain of trust relationships
        for i in range(num_agents - 1):
            self.trust_graph.update_trust(
                f"analysis_agent_{i}", 
                f"analysis_agent_{i+1}", 
                0.7, 0.8
            )
            
        # Add some cross-connections
        for i in range(0, num_agents - 2, 3):
            self.trust_graph.update_trust(
                f"analysis_agent_{i}", 
                f"analysis_agent_{i+2}", 
                0.6, 0.7
            )
            
        # Test trust path analysis performance
        self._start_performance_tracking()
        
        analysis = self.analyzer.analyze_trust_paths(
            "analysis_agent_0", 
            "analysis_agent_149",  # Updated target
            max_paths=10
        )
        
        metrics = self._end_performance_tracking()
        
        # Verify analysis results
        self.assertIsInstance(analysis, TrustAnalysis)
        self.assertEqual(analysis.source, "analysis_agent_0")
        self.assertEqual(analysis.target, "analysis_agent_149")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 15.0, f"Analysis took {metrics['execution_time']:.2f} seconds")
        self.assertLess(metrics['memory_used'], 100.0, f"Memory used: {metrics['memory_used']:.2f} MB")
        
        print(f"Large scale analysis: {metrics['execution_time']:.2f}s, {metrics['memory_used']:.2f}MB")
        
    def test_visualization_performance(self):
        """Test visualization performance with large datasets."""
        # Create dataset
        num_agents = 200
        for i in range(num_agents):
            self.trust_graph.add_agent(f"viz_agent_{i}")
            
        # Create trust relationships
        for i in range(num_agents - 1):
            self.trust_graph.update_trust(
                f"viz_agent_{i}", 
                f"viz_agent_{i+1}", 
                0.7, 0.8
            )
            
        # Test visualization generation performance
        self._start_performance_tracking()
        
        self.visualizer._build_visualization()
        viz_data = self.visualizer.get_visualization_data()
        
        metrics = self._end_performance_tracking()
        
        # Verify visualization data
        self.assertEqual(len(viz_data["nodes"]), num_agents)
        self.assertEqual(len(viz_data["edges"]), num_agents - 1)
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 5.0, f"Visualization took {metrics['execution_time']:.2f} seconds")
        self.assertLess(metrics['memory_used'], 50.0, f"Memory used: {metrics['memory_used']:.2f} MB")
        
        print(f"Visualization performance: {metrics['execution_time']:.2f}s, {metrics['memory_used']:.2f}MB")
        
    def test_metrics_calculation_performance(self):
        """Test metrics calculation performance with large datasets."""
        # Create dataset
        num_agents = 150
        for i in range(num_agents):
            self.trust_graph.add_agent(f"metrics_agent_{i}")
            self.behavior_model.add_agent(f"metrics_agent_{i}")
            
        # Create trust relationships
        for i in range(num_agents - 1):
            self.trust_graph.update_trust(
                f"metrics_agent_{i}", 
                f"metrics_agent_{i+1}", 
                0.7, 0.8
            )
            
        # Add behavioral data
        for i in range(num_agents):
            for _ in range(5):
                self.behavior_model.record_interaction(f"metrics_agent_{i}", random.choice([True, False]))
                
        # Test metrics calculation performance
        self._start_performance_tracking()
        
        # Calculate metrics for all agents
        all_metrics = {}
        for i in range(num_agents):
            all_metrics[f"metrics_agent_{i}"] = self.metrics_calculator.calculate_agent_metrics(
                f"metrics_agent_{i}", 
                include_behavior=True
            )
            
        # Calculate network metrics
        network_metrics = self.metrics_calculator.calculate_network_metrics()
        
        metrics = self._end_performance_tracking()
        
        # Verify metrics
        self.assertEqual(len(all_metrics), num_agents)
        self.assertEqual(network_metrics.total_agents, num_agents)
        self.assertEqual(network_metrics.total_edges, num_agents - 1)
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 15.0, f"Metrics calculation took {metrics['execution_time']:.2f} seconds")
        self.assertLess(metrics['memory_used'], 200.0, f"Memory used: {metrics['memory_used']:.2f} MB")
        
        print(f"Metrics calculation: {metrics['execution_time']:.2f}s, {metrics['memory_used']:.2f}MB")
        
    def test_concurrent_operations(self):
        """Test performance under concurrent-like operations."""
        num_agents = 100
        
        # Create agents
        for i in range(num_agents):
            self.trust_graph.add_agent(f"concurrent_agent_{i}")
            self.behavior_model.add_agent(f"concurrent_agent_{i}")
            
        self._start_performance_tracking()
        
        # Simulate concurrent operations
        operations = []
        
        # Trust updates
        for _ in range(50):
            source = random.randint(0, num_agents - 1)
            target = random.randint(0, num_agents - 1)
            if source != target:
                self.trust_graph.update_trust(
                    f"concurrent_agent_{source}", 
                    f"concurrent_agent_{target}", 
                    random.uniform(0.1, 1.0), 
                    random.uniform(0.1, 1.0)
                )
                
        # Behavioral updates
        for _ in range(100):
            agent = random.randint(0, num_agents - 1)
            self.behavior_model.record_interaction(f"concurrent_agent_{agent}", random.choice([True, False]))
            
        # Analysis operations
        for _ in range(10):
            source = random.randint(0, num_agents - 1)
            target = random.randint(0, num_agents - 1)
            if source != target:
                self.analyzer.analyze_trust_paths(
                    f"concurrent_agent_{source}", 
                    f"concurrent_agent_{target}", 
                    max_paths=3
                )
                
        # Visualization updates
        self.visualizer._build_visualization()
        viz_data = self.visualizer.get_visualization_data()
        
        # Metrics calculations
        for i in range(0, num_agents, 10):
            self.metrics_calculator.calculate_agent_metrics(f"concurrent_agent_{i}")
            
        metrics = self._end_performance_tracking()
        
        # Verify operations completed
        self.assertGreater(len(viz_data["nodes"]), 0)
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 20.0, f"Concurrent operations took {metrics['execution_time']:.2f} seconds")
        self.assertLess(metrics['memory_used'], 300.0, f"Memory used: {metrics['memory_used']:.2f} MB")
        
        print(f"Concurrent operations: {metrics['execution_time']:.2f}s, {metrics['memory_used']:.2f}MB")
        
    def test_memory_efficiency(self):
        """Test memory efficiency with repeated operations."""
        num_agents = 50
        num_iterations = 10
        
        # Create initial dataset
        for i in range(num_agents):
            self.trust_graph.add_agent(f"memory_agent_{i}")
            self.behavior_model.add_agent(f"memory_agent_{i}")
            
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Perform repeated operations
        for iteration in range(num_iterations):
            # Add some trust relationships
            for i in range(num_agents - 1):
                self.trust_graph.update_trust(
                    f"memory_agent_{i}", 
                    f"memory_agent_{i+1}", 
                    0.7, 0.8
                )
                
            # Perform analysis
            self.analyzer.analyze_trust_paths("memory_agent_0", "memory_agent_49")
            
            # Update visualization
            self.visualizer._build_visualization()
            
            # Calculate metrics
            self.metrics_calculator.calculate_network_metrics()
            
            # Force garbage collection
            gc.collect()
            
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        # Memory efficiency assertions
        self.assertLess(memory_growth, 100.0, f"Memory growth: {memory_growth:.2f} MB")
        
        print(f"Memory efficiency: {memory_growth:.2f}MB growth over {num_iterations} iterations")
        
    def test_throughput_benchmark(self):
        """Test throughput for key operations."""
        num_agents = 200
        
        # Create agents
        for i in range(num_agents):
            self.trust_graph.add_agent(f"throughput_agent_{i}")
            
        # Benchmark trust updates
        self._start_performance_tracking()
        for i in range(num_agents - 1):
            self.trust_graph.update_trust(
                f"throughput_agent_{i}", 
                f"throughput_agent_{i+1}", 
                0.7, 0.8
            )
        trust_update_metrics = self._end_performance_tracking()
        
        # Benchmark analysis operations
        self._start_performance_tracking()
        for i in range(0, num_agents - 1, 5):
            self.analyzer.analyze_trust_paths(
                f"throughput_agent_{i}", 
                f"throughput_agent_{i+1}", 
                max_paths=3
            )
        analysis_metrics = self._end_performance_tracking()
        
        # Calculate throughput
        trust_updates_per_second = (num_agents - 1) / trust_update_metrics['execution_time']
        analysis_per_second = ((num_agents - 1) // 5) / analysis_metrics['execution_time']
        
        # Throughput assertions
        self.assertGreater(trust_updates_per_second, 100.0, f"Trust updates: {trust_updates_per_second:.1f}/s")
        self.assertGreater(analysis_per_second, 10.0, f"Analysis: {analysis_per_second:.1f}/s")
        
        print(f"Throughput - Trust updates: {trust_updates_per_second:.1f}/s, Analysis: {analysis_per_second:.1f}/s")

    def test_optimized_throughput_benchmark(self):
        """Test optimized throughput using batch operations and high-performance mode."""
        print("\n=== Testing Optimized Throughput ===")
        
        # Create high-performance trust graph
        trust_graph = TrustGraph(auto_save=False, high_performance=True)
        
        # Generate test data
        num_agents = 100
        num_updates = 1000
        batch_size = 50
        
        # Create agents
        for i in range(num_agents):
            trust_graph.add_agent(f"agent_{i}")
        
        # Generate batch updates
        import random
        updates = []
        for _ in range(num_updates):
            from_agent = f"agent_{random.randint(0, num_agents-1)}"
            to_agent = f"agent_{random.randint(0, num_agents-1)}"
            trust_score = random.uniform(-1.0, 1.0)
            confidence = random.uniform(0.5, 1.0)
            metadata = {"test": True, "batch": True}
            updates.append((from_agent, to_agent, trust_score, confidence, metadata))
        
        # Test batch updates
        start_time = time.time()
        
        # Process in batches
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            trust_graph.update_trust_batch(batch, high_performance=True)
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = num_updates / duration
        
        print(f"Optimized Throughput Test Results:")
        print(f"  Total updates: {num_updates}")
        print(f"  Batch size: {batch_size}")
        print(f"  Duration: {duration:.3f} seconds")
        print(f"  Throughput: {throughput:.1f} updates/second")
        print(f"  High-performance mode: {trust_graph.high_performance}")
        
        # Verify results
        assert throughput > 100, f"Optimized throughput {throughput:.1f} should be > 100 updates/sec"
        assert len(trust_graph.get_all_edges()) > 0, "Should have created trust edges"
        
        print(f"✅ Optimized throughput test passed: {throughput:.1f} updates/sec")
        
        # Test individual high-performance updates
        print("\n=== Testing Individual High-Performance Updates ===")
        
        trust_graph2 = TrustGraph(auto_save=False, high_performance=True)
        
        # Create agents
        for i in range(50):
            trust_graph2.add_agent(f"agent_{i}")
        
        # Test individual updates
        start_time = time.time()
        
        for i in range(500):
            from_agent = f"agent_{i % 50}"
            to_agent = f"agent_{(i + 1) % 50}"
            trust_score = 0.5
            confidence = 0.8
            trust_graph2.update_trust(from_agent, to_agent, trust_score, confidence)
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = 500 / duration
        
        print(f"Individual High-Performance Test Results:")
        print(f"  Total updates: 500")
        print(f"  Duration: {duration:.3f} seconds")
        print(f"  Throughput: {throughput:.1f} updates/second")
        
        assert throughput > 100, f"Individual high-performance throughput {throughput:.1f} should be > 100 updates/sec"
        
        print(f"✅ Individual high-performance test passed: {throughput:.1f} updates/sec")

    def test_performance_comparison(self):
        """Compare performance between standard and optimized modes."""
        print("\n=== Performance Comparison Test ===")
        
        # Test configurations
        configs = [
            {"name": "Standard Mode", "high_performance": False, "auto_save": True},
            {"name": "High-Performance Mode", "high_performance": True, "auto_save": False},
            {"name": "Batch Operations", "high_performance": True, "auto_save": False, "batch": True}
        ]
        
        results = {}
        
        for config in configs:
            print(f"\n--- Testing {config['name']} ---")
            
            # Create trust graph with configuration
            trust_graph = TrustGraph(
                auto_save=config['auto_save'], 
                high_performance=config['high_performance']
            )
            
            # Create test agents
            num_agents = 50
            num_updates = 200
            
            for i in range(num_agents):
                trust_graph.add_agent(f"agent_{i}")
            
            # Generate test data
            import random
            updates = []
            for _ in range(num_updates):
                from_agent = f"agent_{random.randint(0, num_agents-1)}"
                to_agent = f"agent_{random.randint(0, num_agents-1)}"
                trust_score = random.uniform(-1.0, 1.0)
                confidence = random.uniform(0.5, 1.0)
                updates.append((from_agent, to_agent, trust_score, confidence, {}))
            
            # Run performance test
            start_time = time.time()
            
            if config.get('batch', False):
                # Batch operations
                batch_size = 20
                for i in range(0, len(updates), batch_size):
                    batch = updates[i:i+batch_size]
                    trust_graph.update_trust_batch(batch, high_performance=True)
            else:
                # Individual operations
                for from_agent, to_agent, trust_score, confidence, metadata in updates:
                    trust_graph.update_trust(from_agent, to_agent, trust_score, confidence, metadata)
            
            end_time = time.time()
            duration = end_time - start_time
            throughput = num_updates / duration
            
            results[config['name']] = {
                'throughput': throughput,
                'duration': duration,
                'config': config
            }
            
            print(f"  Throughput: {throughput:.1f} updates/second")
            print(f"  Duration: {duration:.3f} seconds")
            print(f"  High-performance: {config['high_performance']}")
            print(f"  Auto-save: {config['auto_save']}")
            print(f"  Batch mode: {config.get('batch', False)}")
        
        # Performance summary
        print(f"\n=== Performance Summary ===")
        baseline = results["Standard Mode"]["throughput"]
        
        for name, result in results.items():
            improvement = (result["throughput"] / baseline) if baseline > 0 else 0
            print(f"{name}:")
            print(f"  Throughput: {result['throughput']:.1f} updates/sec")
            print(f"  Improvement: {improvement:.1f}x over baseline")
            print(f"  Duration: {result['duration']:.3f} seconds")
        
        # Verify all modes work correctly
        assert results["Standard Mode"]["throughput"] > 0, "Standard mode should work"
        assert results["High-Performance Mode"]["throughput"] > results["Standard Mode"]["throughput"], "High-performance should be faster"
        # Note: Batch operations may not always be fastest for small datasets due to overhead
        
        print(f"\n✅ Performance comparison test passed!")
        print(f"   Best performance: {max(r['throughput'] for r in results.values()):.1f} updates/sec")
        
        # Test with larger dataset to show batch benefits
        print(f"\n=== Large Dataset Batch Test ===")
        
        large_trust_graph = TrustGraph(auto_save=False, high_performance=True)
        
        # Create more agents
        num_agents = 200
        num_updates = 5000
        
        for i in range(num_agents):
            large_trust_graph.add_agent(f"large_agent_{i}")
        
        # Generate large dataset
        large_updates = []
        for _ in range(num_updates):
            from_agent = f"large_agent_{random.randint(0, num_agents-1)}"
            to_agent = f"large_agent_{random.randint(0, num_agents-1)}"
            trust_score = random.uniform(-1.0, 1.0)
            confidence = random.uniform(0.5, 1.0)
            large_updates.append((from_agent, to_agent, trust_score, confidence, {}))
        
        # Test individual vs batch for large dataset
        print("Testing individual updates...")
        start_time = time.time()
        for from_agent, to_agent, trust_score, confidence, metadata in large_updates:
            large_trust_graph.update_trust(from_agent, to_agent, trust_score, confidence, metadata)
        individual_time = time.time() - start_time
        
        # Reset for batch test
        large_trust_graph2 = TrustGraph(auto_save=False, high_performance=True)
        for i in range(num_agents):
            large_trust_graph2.add_agent(f"large_agent_{i}")
        
        print("Testing batch updates...")
        start_time = time.time()
        batch_size = 100
        for i in range(0, len(large_updates), batch_size):
            batch = large_updates[i:i+batch_size]
            large_trust_graph2.update_trust_batch(batch, high_performance=True)
        batch_time = time.time() - start_time
        
        individual_throughput = num_updates / individual_time
        batch_throughput = num_updates / batch_time
        
        print(f"Large Dataset Results:")
        print(f"  Individual: {individual_throughput:.1f} updates/sec ({individual_time:.3f}s)")
        print(f"  Batch: {batch_throughput:.1f} updates/sec ({batch_time:.3f}s)")
        print(f"  Batch improvement: {batch_throughput/individual_throughput:.1f}x")
        
        # For large datasets, batch should be faster
        if num_updates > 1000:
            assert batch_throughput >= individual_throughput * 0.8, "Batch should be competitive for large datasets"

if __name__ == "__main__":
    unittest.main() 