#!/usr/bin/env python3
"""
GitBridge Phase 24 - Performance Benchmarks
Comprehensive performance testing and optimization for collaboration features.

MAS Lite Protocol v2.1 Compliance
"""

import time
import json
import statistics
import psutil
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
import logging
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mas_core.attribution import AttributionManager, ContributorType, ContributionRole
from mas_core.changelog import ChangelogManager
from mas_core.activity_feed import ActivityFeedManager, ActivityType
from mas_core.task_display import TaskCardRenderer
from mas_core.diff_viewer import DiffViewer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_benchmarks.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PerformanceBenchmark:
    """Comprehensive performance benchmarking for Phase 24 components."""
    
    def __init__(self):
        """Initialize benchmark components."""
        self.attribution_manager = AttributionManager()
        self.changelog_manager = ChangelogManager()
        self.activity_feed_manager = ActivityFeedManager()
        self.task_card_renderer = TaskCardRenderer(self.attribution_manager)
        self.diff_viewer = DiffViewer()
        
        self.benchmark_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": "GBP24",
            "benchmark_suite": "Phase 24 Performance Benchmarks",
            "system_info": self._get_system_info(),
            "tests": {},
            "summary": {},
            "recommendations": []
        }
        
        # Test data
        self.test_contributors = []
        self.test_tasks = []
        self.test_activities = []
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmarking context."""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "python_version": sys.version,
                "platform": sys.platform
            }
        except Exception as e:
            logger.warning(f"Could not get system info: {e}")
            return {"error": str(e)}
    
    def _measure_execution_time(self, func, *args, **kwargs) -> Tuple[float, Any]:
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory
        
        return execution_time, memory_delta, result
    
    def _run_concurrent_test(self, func, num_threads: int, *args, **kwargs) -> List[float]:
        """Run a function concurrently and measure performance."""
        results = []
        threads = []
        
        def worker():
            execution_time, _, _ = self._measure_execution_time(func, *args, **kwargs)
            results.append(execution_time)
        
        # Start threads
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return results
    
    def benchmark_01_contributor_registration(self) -> Dict[str, Any]:
        """Benchmark contributor registration performance."""
        logger.info("[P24P7S1T1] Benchmarking contributor registration...")
        
        results = {
            "test_name": "Contributor Registration",
            "description": "Test performance of contributor registration with various loads",
            "metrics": {}
        }
        
        # Single registration
        execution_time, memory_delta, _ = self._measure_execution_time(
            self.attribution_manager.register_contributor,
            name="BenchmarkUser",
            contributor_type=ContributorType.HUMAN
        )
        
        results["metrics"]["single_registration"] = {
            "execution_time_ms": round(execution_time * 1000, 3),
            "memory_delta_kb": round(memory_delta / 1024, 2)
        }
        
        # Batch registration (100 contributors)
        batch_times = []
        batch_memory = []
        
        for i in range(100):
            execution_time, memory_delta, _ = self._measure_execution_time(
                self.attribution_manager.register_contributor,
                name=f"BatchUser{i}",
                contributor_type=ContributorType.HUMAN
            )
            batch_times.append(execution_time)
            batch_memory.append(memory_delta)
        
        results["metrics"]["batch_registration"] = {
            "count": 100,
            "total_time_ms": round(sum(batch_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(batch_times) * 1000, 3),
            "median_time_ms": round(statistics.median(batch_times) * 1000, 3),
            "min_time_ms": round(min(batch_times) * 1000, 3),
            "max_time_ms": round(max(batch_times) * 1000, 3),
            "total_memory_kb": round(sum(batch_memory) / 1024, 2),
            "average_memory_kb": round(statistics.mean(batch_memory) / 1024, 2)
        }
        
        # Concurrent registration (10 threads)
        concurrent_times = self._run_concurrent_test(
            self.attribution_manager.register_contributor,
            10,
            name="ConcurrentUser",
            contributor_type=ContributorType.HUMAN
        )
        
        results["metrics"]["concurrent_registration"] = {
            "threads": 10,
            "total_time_ms": round(sum(concurrent_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(concurrent_times) * 1000, 3),
            "median_time_ms": round(statistics.median(concurrent_times) * 1000, 3),
            "min_time_ms": round(min(concurrent_times) * 1000, 3),
            "max_time_ms": round(max(concurrent_times) * 1000, 3)
        }
        
        logger.info(f"[P24P7S1T1] Contributor registration benchmark completed")
        return results
    
    def benchmark_02_task_attribution(self) -> Dict[str, Any]:
        """Benchmark task attribution performance."""
        logger.info("[P24P7S1T2] Benchmarking task attribution...")
        
        results = {
            "test_name": "Task Attribution",
            "description": "Test performance of task attribution operations",
            "metrics": {}
        }
        
        # Create test contributors
        contributor_ids = []
        for i in range(50):
            contributor_id = self.attribution_manager.register_contributor(
                name=f"AttributionUser{i}",
                contributor_type=ContributorType.HUMAN
            )
            contributor_ids.append(contributor_id)
        
        # Single attribution
        execution_time, memory_delta, _ = self._measure_execution_time(
            self.attribution_manager.add_contribution,
            task_id="BENCH-TASK-001",
            contributor_id=contributor_ids[0],
            role=ContributionRole.EDITOR,
            content="Benchmark contribution"
        )
        
        results["metrics"]["single_attribution"] = {
            "execution_time_ms": round(execution_time * 1000, 3),
            "memory_delta_kb": round(memory_delta / 1024, 2)
        }
        
        # Multiple attributions per task
        multi_times = []
        for i in range(20):
            execution_time, _, _ = self._measure_execution_time(
                self.attribution_manager.add_contribution,
                task_id="BENCH-TASK-002",
                contributor_id=contributor_ids[i % len(contributor_ids)],
                role=ContributionRole.EDITOR,
                content=f"Multi-attribution contribution {i}"
            )
            multi_times.append(execution_time)
        
        results["metrics"]["multi_attribution"] = {
            "count": 20,
            "total_time_ms": round(sum(multi_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(multi_times) * 1000, 3),
            "median_time_ms": round(statistics.median(multi_times) * 1000, 3)
        }
        
        # Attribution retrieval
        retrieval_times = []
        for i in range(100):
            execution_time, _, _ = self._measure_execution_time(
                self.attribution_manager.get_task_attribution,
                "BENCH-TASK-001"
            )
            retrieval_times.append(execution_time)
        
        results["metrics"]["attribution_retrieval"] = {
            "count": 100,
            "total_time_ms": round(sum(retrieval_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(retrieval_times) * 1000, 3),
            "median_time_ms": round(statistics.median(retrieval_times) * 1000, 3),
            "min_time_ms": round(min(retrieval_times) * 1000, 3),
            "max_time_ms": round(max(retrieval_times) * 1000, 3)
        }
        
        logger.info(f"[P24P7S1T2] Task attribution benchmark completed")
        return results
    
    def benchmark_03_changelog_management(self) -> Dict[str, Any]:
        """Benchmark changelog management performance."""
        logger.info("[P24P7S1T3] Benchmarking changelog management...")
        
        results = {
            "test_name": "Changelog Management",
            "description": "Test performance of changelog creation and revision management",
            "metrics": {}
        }
        
        # Create test contributors
        contributor_ids = []
        for i in range(20):
            contributor_id = self.attribution_manager.register_contributor(
                name=f"ChangelogUser{i}",
                contributor_type=ContributorType.HUMAN
            )
            contributor_ids.append(contributor_id)
        
        # Changelog creation
        creation_times = []
        for i in range(50):
            execution_time, _, _ = self._measure_execution_time(
                self.changelog_manager.create_task_changelog,
                f"CHANGELOG-TASK-{i:03d}"
            )
            creation_times.append(execution_time)
        
        results["metrics"]["changelog_creation"] = {
            "count": 50,
            "total_time_ms": round(sum(creation_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(creation_times) * 1000, 3),
            "median_time_ms": round(statistics.median(creation_times) * 1000, 3)
        }
        
        # Revision addition
        revision_times = []
        for i in range(100):
            execution_time, _, _ = self._measure_execution_time(
                self.changelog_manager.add_revision,
                task_id=f"CHANGELOG-TASK-{i % 50:03d}",
                contributor_id=contributor_ids[i % len(contributor_ids)],
                description=f"Revision {i}",
                file_changes=[{
                    "file_path": f"file_{i}.py",
                    "change_type": "modified",
                    "new_content": f"# Revision {i}\nprint('Hello World')"
                }]
            )
            revision_times.append(execution_time)
        
        results["metrics"]["revision_addition"] = {
            "count": 100,
            "total_time_ms": round(sum(revision_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(revision_times) * 1000, 3),
            "median_time_ms": round(statistics.median(revision_times) * 1000, 3)
        }
        
        # Changelog retrieval
        retrieval_times = []
        for i in range(100):
            execution_time, _, _ = self._measure_execution_time(
                self.changelog_manager.get_task_changelog,
                f"CHANGELOG-TASK-{i % 50:03d}"
            )
            retrieval_times.append(execution_time)
        
        results["metrics"]["changelog_retrieval"] = {
            "count": 100,
            "total_time_ms": round(sum(retrieval_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(retrieval_times) * 1000, 3),
            "median_time_ms": round(statistics.median(retrieval_times) * 1000, 3)
        }
        
        logger.info(f"[P24P7S1T3] Changelog management benchmark completed")
        return results
    
    def benchmark_04_activity_feed(self) -> Dict[str, Any]:
        """Benchmark activity feed performance."""
        logger.info("[P24P7S1T4] Benchmarking activity feed...")
        
        results = {
            "test_name": "Activity Feed",
            "description": "Test performance of activity feed operations",
            "metrics": {}
        }
        
        # Create test contributors
        contributor_ids = []
        for i in range(30):
            contributor_id = self.attribution_manager.register_contributor(
                name=f"ActivityUser{i}",
                contributor_type=ContributorType.HUMAN
            )
            contributor_ids.append(contributor_id)
        
        # Activity addition
        activity_times = []
        for i in range(200):
            execution_time, _, _ = self._measure_execution_time(
                self.activity_feed_manager.add_activity,
                feed_id="main",
                activity_type=ActivityType.TASK_UPDATED,
                contributor_id=contributor_ids[i % len(contributor_ids)],
                content=f"Activity {i}"
            )
            activity_times.append(execution_time)
        
        results["metrics"]["activity_addition"] = {
            "count": 200,
            "total_time_ms": round(sum(activity_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(activity_times) * 1000, 3),
            "median_time_ms": round(statistics.median(activity_times) * 1000, 3)
        }
        
        # Feed retrieval
        retrieval_times = []
        for i in range(50):
            execution_time, _, _ = self._measure_execution_time(
                self.activity_feed_manager.get_feed_activities,
                "main"
            )
            retrieval_times.append(execution_time)
        
        results["metrics"]["feed_retrieval"] = {
            "count": 50,
            "total_time_ms": round(sum(retrieval_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(retrieval_times) * 1000, 3),
            "median_time_ms": round(statistics.median(retrieval_times) * 1000, 3)
        }
        
        # Concurrent activity addition
        concurrent_times = self._run_concurrent_test(
            self.activity_feed_manager.add_activity,
            20,
            feed_id="main",
            activity_type=ActivityType.TASK_CREATED,
            contributor_id=contributor_ids[0],
            content="Concurrent activity"
        )
        
        results["metrics"]["concurrent_activity"] = {
            "threads": 20,
            "total_time_ms": round(sum(concurrent_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(concurrent_times) * 1000, 3),
            "median_time_ms": round(statistics.median(concurrent_times) * 1000, 3)
        }
        
        logger.info(f"[P24P7S1T4] Activity feed benchmark completed")
        return results
    
    def benchmark_05_task_card_rendering(self) -> Dict[str, Any]:
        """Benchmark task card rendering performance."""
        logger.info("[P24P7S1T5] Benchmarking task card rendering...")
        
        results = {
            "test_name": "Task Card Rendering",
            "description": "Test performance of task card rendering in different formats",
            "metrics": {}
        }
        
        from mas_core.task_display import TaskCardData
        
        # Create test task data
        task_data = TaskCardData(
            task_id="RENDER-TASK-001",
            title="Performance Test Task",
            description="This is a comprehensive test task for benchmarking rendering performance",
            status="in_progress",
            priority="high",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # HTML rendering
        html_times = []
        for i in range(100):
            execution_time, _, _ = self._measure_execution_time(
                self.task_card_renderer.render_task_card,
                task_data,
                "html"
            )
            html_times.append(execution_time)
        
        results["metrics"]["html_rendering"] = {
            "count": 100,
            "total_time_ms": round(sum(html_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(html_times) * 1000, 3),
            "median_time_ms": round(statistics.median(html_times) * 1000, 3)
        }
        
        # JSON rendering
        json_times = []
        for i in range(100):
            execution_time, _, _ = self._measure_execution_time(
                self.task_card_renderer.render_task_card,
                task_data,
                "json"
            )
            json_times.append(execution_time)
        
        results["metrics"]["json_rendering"] = {
            "count": 100,
            "total_time_ms": round(sum(json_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(json_times) * 1000, 3),
            "median_time_ms": round(statistics.median(json_times) * 1000, 3)
        }
        
        # Markdown rendering
        md_times = []
        for i in range(100):
            execution_time, _, _ = self._measure_execution_time(
                self.task_card_renderer.render_task_card,
                task_data,
                "markdown"
            )
            md_times.append(execution_time)
        
        results["metrics"]["markdown_rendering"] = {
            "count": 100,
            "total_time_ms": round(sum(md_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(md_times) * 1000, 3),
            "median_time_ms": round(statistics.median(md_times) * 1000, 3)
        }
        
        logger.info(f"[P24P7S1T5] Task card rendering benchmark completed")
        return results
    
    def benchmark_06_diff_viewer(self) -> Dict[str, Any]:
        """Benchmark diff viewer performance."""
        logger.info("[P24P7S1T6] Benchmarking diff viewer...")
        
        results = {
            "test_name": "Diff Viewer",
            "description": "Test performance of diff generation and rendering",
            "metrics": {}
        }
        
        # Create test diff data
        old_content = """# Original file
def hello_world():
    print("Hello, World!")
    return True

class TestClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value"""
        
        new_content = """# Updated file
def hello_world():
    print("Hello, Updated World!")
    return True

class TestClass:
    def __init__(self):
        self.value = 42
        self.name = "Test"
    
    def get_value(self):
        return self.value
    
    def get_name(self):
        return self.name"""
        
        # Diff generation
        diff_times = []
        for i in range(50):
            execution_time, _, _ = self._measure_execution_time(
                self.diff_viewer.generate_diff,
                old_content,
                new_content,
                "test_file.py"
            )
            diff_times.append(execution_time)
        
        results["metrics"]["diff_generation"] = {
            "count": 50,
            "total_time_ms": round(sum(diff_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(diff_times) * 1000, 3),
            "median_time_ms": round(statistics.median(diff_times) * 1000, 3)
        }
        
        # HTML diff rendering
        diff_data = self.diff_viewer.generate_diff(old_content, new_content, "test_file.py")
        html_times = []
        for i in range(50):
            execution_time, _, _ = self._measure_execution_time(
                self.diff_viewer.render_diff_html,
                diff_data
            )
            html_times.append(execution_time)
        
        results["metrics"]["html_diff_rendering"] = {
            "count": 50,
            "total_time_ms": round(sum(html_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(html_times) * 1000, 3),
            "median_time_ms": round(statistics.median(html_times) * 1000, 3)
        }
        
        logger.info(f"[P24P7S1T6] Diff viewer benchmark completed")
        return results
    
    def benchmark_07_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage patterns."""
        logger.info("[P24P7S1T7] Benchmarking memory usage...")
        
        results = {
            "test_name": "Memory Usage",
            "description": "Test memory usage patterns under various loads",
            "metrics": {}
        }
        
        # Initial memory
        initial_memory = psutil.Process().memory_info().rss
        
        # Memory usage during heavy operations
        heavy_operations = []
        for i in range(1000):
            # Register contributor
            self.attribution_manager.register_contributor(
                name=f"MemoryUser{i}",
                contributor_type=ContributorType.HUMAN
            )
            
            # Add contribution
            self.attribution_manager.add_contribution(
                task_id=f"MEMORY-TASK-{i}",
                contributor_id=f"MemoryUser{i}",
                role=ContributionRole.EDITOR,
                content=f"Memory test contribution {i}"
            )
            
            # Add activity
            self.activity_feed_manager.add_activity(
                feed_id="main",
                activity_type=ActivityType.TASK_CREATED,
                contributor_id=f"MemoryUser{i}",
                content=f"Memory test activity {i}"
            )
            
            if i % 100 == 0:
                current_memory = psutil.Process().memory_info().rss
                heavy_operations.append({
                    "operation_count": i,
                    "memory_mb": round(current_memory / (1024**2), 2)
                })
        
        final_memory = psutil.Process().memory_info().rss
        
        results["metrics"]["memory_usage"] = {
            "initial_memory_mb": round(initial_memory / (1024**2), 2),
            "final_memory_mb": round(final_memory / (1024**2), 2),
            "memory_increase_mb": round((final_memory - initial_memory) / (1024**2), 2),
            "memory_per_operation_kb": round((final_memory - initial_memory) / 1000, 2),
            "progression": heavy_operations
        }
        
        logger.info(f"[P24P7S1T7] Memory usage benchmark completed")
        return results
    
    def benchmark_08_concurrent_load(self) -> Dict[str, Any]:
        """Benchmark concurrent load handling."""
        logger.info("[P24P7S1T8] Benchmarking concurrent load...")
        
        results = {
            "test_name": "Concurrent Load",
            "description": "Test system performance under concurrent load",
            "metrics": {}
        }
        
        # Mixed concurrent operations
        def mixed_operation():
            # Register contributor
            contributor_id = self.attribution_manager.register_contributor(
                name=f"ConcurrentUser{threading.current_thread().ident}",
                contributor_type=ContributorType.HUMAN
            )
            
            # Add contribution
            self.attribution_manager.add_contribution(
                task_id=f"CONCURRENT-TASK-{threading.current_thread().ident}",
                contributor_id=contributor_id,
                role=ContributionRole.EDITOR,
                content="Concurrent test contribution"
            )
            
            # Add activity
            self.activity_feed_manager.add_activity(
                feed_id="main",
                activity_type=ActivityType.TASK_UPDATED,
                contributor_id=contributor_id,
                content="Concurrent test activity"
            )
        
        # Run concurrent mixed operations
        concurrent_times = self._run_concurrent_test(mixed_operation, 50)
        
        results["metrics"]["concurrent_mixed_operations"] = {
            "threads": 50,
            "total_time_ms": round(sum(concurrent_times) * 1000, 3),
            "average_time_ms": round(statistics.mean(concurrent_times) * 1000, 3),
            "median_time_ms": round(statistics.median(concurrent_times) * 1000, 3),
            "min_time_ms": round(min(concurrent_times) * 1000, 3),
            "max_time_ms": round(max(concurrent_times) * 1000, 3)
        }
        
        logger.info(f"[P24P7S1T8] Concurrent load benchmark completed")
        return results
    
    def generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Analyze results and generate recommendations
        for test_name, test_results in self.benchmark_results["tests"].items():
            metrics = test_results.get("metrics", {})
            
            # Contributor registration recommendations
            if "batch_registration" in metrics:
                avg_time = metrics["batch_registration"]["average_time_ms"]
                if avg_time > 10:
                    recommendations.append(
                        f"Consider implementing batch contributor registration API to reduce "
                        f"average registration time (currently {avg_time:.2f}ms)"
                    )
            
            # Attribution recommendations
            if "attribution_retrieval" in metrics:
                avg_time = metrics["attribution_retrieval"]["average_time_ms"]
                if avg_time > 5:
                    recommendations.append(
                        f"Consider implementing caching for task attributions to improve "
                        f"retrieval performance (currently {avg_time:.2f}ms)"
                    )
            
            # Activity feed recommendations
            if "feed_retrieval" in metrics:
                avg_time = metrics["feed_retrieval"]["average_time_ms"]
                if avg_time > 20:
                    recommendations.append(
                        f"Consider implementing pagination and indexing for activity feeds "
                        f"to improve retrieval performance (currently {avg_time:.2f}ms)"
                    )
            
            # Memory recommendations
            if "memory_usage" in metrics:
                memory_per_op = metrics["memory_usage"]["memory_per_operation_kb"]
                if memory_per_op > 1:
                    recommendations.append(
                        f"Consider implementing object pooling or memory cleanup to reduce "
                        f"memory usage per operation (currently {memory_per_op:.2f}KB)"
                    )
        
        # General recommendations
        recommendations.extend([
            "Implement Redis caching for frequently accessed data",
            "Consider database indexing for task_id and contributor_id fields",
            "Implement connection pooling for database operations",
            "Add monitoring and alerting for performance metrics",
            "Consider implementing rate limiting for API endpoints",
            "Optimize JSON serialization for large datasets"
        ])
        
        return recommendations
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all performance benchmarks."""
        logger.info("[P24P7S1] Starting comprehensive performance benchmarks...")
        
        benchmark_methods = [
            self.benchmark_01_contributor_registration,
            self.benchmark_02_task_attribution,
            self.benchmark_03_changelog_management,
            self.benchmark_04_activity_feed,
            self.benchmark_05_task_card_rendering,
            self.benchmark_06_diff_viewer,
            self.benchmark_07_memory_usage,
            self.benchmark_08_concurrent_load
        ]
        
        for i, benchmark_method in enumerate(benchmark_methods, 1):
            try:
                logger.info(f"[P24P7S1] Running benchmark {i}/{len(benchmark_methods)}: {benchmark_method.__name__}")
                results = benchmark_method()
                self.benchmark_results["tests"][f"benchmark_{i:02d}"] = results
            except Exception as e:
                logger.error(f"[P24P7S1] Benchmark {i} failed: {e}")
                self.benchmark_results["tests"][f"benchmark_{i:02d}"] = {
                    "error": str(e),
                    "test_name": benchmark_method.__name__
                }
        
        # Generate recommendations
        self.benchmark_results["recommendations"] = self.generate_recommendations()
        
        # Generate summary
        self.benchmark_results["summary"] = self._generate_summary()
        
        logger.info("[P24P7S1] All performance benchmarks completed")
        return self.benchmark_results
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate benchmark summary."""
        summary = {
            "total_tests": len(self.benchmark_results["tests"]),
            "successful_tests": 0,
            "failed_tests": 0,
            "total_execution_time_ms": 0,
            "average_execution_time_ms": 0,
            "performance_score": 0
        }
        
        execution_times = []
        
        for test_name, test_results in self.benchmark_results["tests"].items():
            if "error" not in test_results:
                summary["successful_tests"] += 1
                
                # Calculate total execution time for this test
                test_total_time = 0
                metrics = test_results.get("metrics", {})
                
                for metric_name, metric_data in metrics.items():
                    if "total_time_ms" in metric_data:
                        test_total_time += metric_data["total_time_ms"]
                    elif "execution_time_ms" in metric_data:
                        test_total_time += metric_data["execution_time_ms"]
                
                execution_times.append(test_total_time)
                summary["total_execution_time_ms"] += test_total_time
            else:
                summary["failed_tests"] += 1
        
        if execution_times:
            summary["average_execution_time_ms"] = round(statistics.mean(execution_times), 3)
            
            # Calculate performance score (lower is better)
            # Base score on average execution time, with bonus for consistency
            avg_time = summary["average_execution_time_ms"]
            if avg_time < 10:
                performance_score = 95
            elif avg_time < 50:
                performance_score = 85
            elif avg_time < 100:
                performance_score = 75
            elif avg_time < 200:
                performance_score = 60
            else:
                performance_score = 40
            
            # Bonus for consistency (low standard deviation)
            if len(execution_times) > 1:
                std_dev = statistics.stdev(execution_times)
                if std_dev < avg_time * 0.1:  # Less than 10% variation
                    performance_score += 10
                elif std_dev < avg_time * 0.2:  # Less than 20% variation
                    performance_score += 5
            
            summary["performance_score"] = min(100, max(0, performance_score))
        
        return summary
    
    def save_results(self, filename: str = None) -> str:
        """Save benchmark results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_benchmarks_{timestamp}.json"
        
        os.makedirs("benchmark_results", exist_ok=True)
        filepath = os.path.join("benchmark_results", filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.benchmark_results, f, indent=2, default=str)
        
        logger.info(f"[P24P7S1] Benchmark results saved to {filepath}")
        return filepath

def main():
    """Run performance benchmarks."""
    print("""
================================================================================
GitBridge Phase 24 - Performance Benchmarks
================================================================================
""")
    
    benchmark = PerformanceBenchmark()
    results = benchmark.run_all_benchmarks()
    
    # Save results
    filepath = benchmark.save_results()
    
    # Print summary
    summary = results["summary"]
    print(f"""
================================================================================
BENCHMARK SUMMARY
================================================================================

Total Tests: {summary['total_tests']}
Successful: {summary['successful_tests']}
Failed: {summary['failed_tests']}
Total Execution Time: {summary['total_execution_time_ms']:.2f}ms
Average Execution Time: {summary['average_execution_time_ms']:.2f}ms
Performance Score: {summary['performance_score']}/100

Results saved to: {filepath}

================================================================================
TOP RECOMMENDATIONS
================================================================================
""")
    
    for i, recommendation in enumerate(results["recommendations"][:5], 1):
        print(f"{i}. {recommendation}")
    
    print(f"""
================================================================================
BENCHMARK COMPLETED
================================================================================
""")

if __name__ == "__main__":
    main() 