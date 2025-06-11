# P18P8S4 – Stress Test Engine Module

"""
GitBridge Phase 18P8 - Stress Test Engine

This module implements comprehensive parallel stress testing for SmartRepo
fallback scenarios with performance monitoring and Redis write rate tracking.

Author: GitBridge MAS Integration Team
Phase: 18P8 - CLI Test Harness
MAS Lite Protocol: v2.1 Compliance
"""

import json
import time
import threading
import asyncio
import concurrent.futures
import resource
import psutil
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from queue import Queue
import hashlib
import random

# Import fallback simulator for stress testing
from fallback_simulator import FallbackSimulator, FallbackType, FallbackScenario


@dataclass
class StressTestMetrics:
    """Performance metrics for stress test execution"""
    test_session_id: str
    start_time: str
    end_time: str
    total_duration_ms: int
    thread_count: int
    target_duration_seconds: int
    total_operations: int
    successful_operations: int
    failed_operations: int
    operations_per_second: float
    
    # Memory metrics
    peak_memory_mb: float
    memory_usage_samples: List[float] = field(default_factory=list)
    
    # Redis simulation metrics
    redis_writes: int = 0
    redis_write_rate: float = 0.0
    redis_errors: int = 0
    redis_write_samples: List[int] = field(default_factory=list)
    
    # Threading metrics
    max_concurrent_threads: int = 0
    thread_overhead_ms: int = 0
    lock_contention_count: int = 0
    
    # Error distribution
    error_distribution: Dict[str, int] = field(default_factory=dict)
    timeout_count: int = 0
    model_failure_count: int = 0
    escalation_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "test_session_id": self.test_session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_ms": self.total_duration_ms,
            "thread_count": self.thread_count,
            "target_duration_seconds": self.target_duration_seconds,
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "operations_per_second": self.operations_per_second,
            "success_rate": (self.successful_operations / self.total_operations * 100) if self.total_operations > 0 else 0,
            "peak_memory_mb": self.peak_memory_mb,
            "memory_usage_samples": self.memory_usage_samples,
            "redis_writes": self.redis_writes,
            "redis_write_rate": self.redis_write_rate,
            "redis_errors": self.redis_errors,
            "redis_write_samples": self.redis_write_samples,
            "max_concurrent_threads": self.max_concurrent_threads,
            "thread_overhead_ms": self.thread_overhead_ms,
            "lock_contention_count": self.lock_contention_count,
            "error_distribution": self.error_distribution,
            "timeout_count": self.timeout_count,
            "model_failure_count": self.model_failure_count,
            "escalation_count": self.escalation_count,
            "mas_lite_protocol": "v2.1"
        }


@dataclass
class ThreadWorkerResult:
    """Result from individual thread worker"""
    worker_id: str
    start_time: str
    end_time: str
    operations_completed: int
    operations_failed: int
    scenarios: List[FallbackScenario] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    redis_writes: int = 0


class MockRedisLogger:
    """Mock Redis logger for stress testing"""
    
    def __init__(self):
        self.write_count = 0
        self.error_count = 0
        self.write_times = []
        self.lock = threading.Lock()
    
    def write_fallback_error(self, error_data: Dict[str, Any]) -> bool:
        """Simulate Redis write operation"""
        start_time = time.time()
        
        try:
            with self.lock:
                # Simulate network latency and Redis processing
                time.sleep(random.uniform(0.001, 0.005))  # 1-5ms
                
                # Randomly simulate errors (5% failure rate)
                if random.random() < 0.05:
                    self.error_count += 1
                    return False
                
                self.write_count += 1
                write_time = (time.time() - start_time) * 1000  # Convert to ms
                self.write_times.append(write_time)
                return True
                
        except Exception:
            with self.lock:
                self.error_count += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis operation statistics"""
        with self.lock:
            return {
                "total_writes": self.write_count,
                "total_errors": self.error_count,
                "avg_write_time_ms": sum(self.write_times) / len(self.write_times) if self.write_times else 0,
                "max_write_time_ms": max(self.write_times) if self.write_times else 0,
                "min_write_time_ms": min(self.write_times) if self.write_times else 0
            }


class PerformanceMonitor:
    """Real-time performance monitoring during stress test"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.samples = []
        self.redis_samples = []
        self.lock = threading.Lock()
    
    def start_monitoring(self, redis_logger: MockRedisLogger):
        """Start performance monitoring in background thread"""
        self.monitoring = True
        self.redis_logger = redis_logger
        
        def monitor_loop():
            while self.monitoring:
                try:
                    # Memory usage
                    memory_info = self.process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    
                    # Redis write rate
                    redis_stats = redis_logger.get_stats()
                    
                    with self.lock:
                        self.samples.append({
                            "timestamp": time.time(),
                            "memory_mb": memory_mb,
                            "cpu_percent": self.process.cpu_percent(),
                            "thread_count": self.process.num_threads()
                        })
                        
                        self.redis_samples.append({
                            "timestamp": time.time(),
                            "redis_writes": redis_stats["total_writes"],
                            "redis_errors": redis_stats["total_errors"]
                        })
                    
                    time.sleep(0.1)  # Sample every 100ms
                    
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    break
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return collected metrics"""
        self.monitoring = False
        time.sleep(0.2)  # Allow final sample
        
        with self.lock:
            if not self.samples:
                return {}
            
            memory_values = [s["memory_mb"] for s in self.samples]
            cpu_values = [s["cpu_percent"] for s in self.samples if s["cpu_percent"] > 0]
            thread_counts = [s["thread_count"] for s in self.samples]
            
            # Calculate Redis write rate
            redis_write_rate = 0.0
            if len(self.redis_samples) > 1:
                first_sample = self.redis_samples[0]
                last_sample = self.redis_samples[-1]
                time_diff = last_sample["timestamp"] - first_sample["timestamp"]
                write_diff = last_sample["redis_writes"] - first_sample["redis_writes"]
                redis_write_rate = write_diff / time_diff if time_diff > 0 else 0
            
            return {
                "peak_memory_mb": max(memory_values),
                "avg_memory_mb": sum(memory_values) / len(memory_values),
                "peak_cpu_percent": max(cpu_values) if cpu_values else 0,
                "avg_cpu_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max_threads": max(thread_counts),
                "redis_write_rate": redis_write_rate,
                "total_samples": len(self.samples)
            }


class StressTestEngine:
    """Advanced parallel stress testing engine"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.metrics = None
        self.redis_logger = MockRedisLogger()
        self.performance_monitor = PerformanceMonitor()
        self.operation_queue = Queue()
        self.results_queue = Queue()
        self.active_threads = 0
        self.thread_lock = threading.Lock()
        
        print(f"⚡ StressTestEngine initialized for session: {session_id}")
    
    def create_worker_thread(self, worker_id: str, duration_seconds: int, 
                           logger: Any) -> ThreadWorkerResult:
        """Create and execute individual worker thread"""
        start_time = datetime.now(timezone.utc)
        worker_simulator = FallbackSimulator(f"{self.session_id}_worker_{worker_id}")
        
        operations_completed = 0
        operations_failed = 0
        scenarios = []
        errors = []
        redis_writes = 0
        
        # Track active thread count
        with self.thread_lock:
            self.active_threads += 1
        
        try:
            end_time = start_time.timestamp() + duration_seconds
            
            while time.time() < end_time:
                try:
                    # Randomly select fallback type to simulate
                    fallback_type = random.choice([FallbackType.TIMEOUT, FallbackType.MODEL_FAILURE, FallbackType.ESCALATION])
                    
                    # Create scenario
                    if fallback_type == FallbackType.TIMEOUT:
                        scenario = worker_simulator.simulate_timeout_scenario()
                    elif fallback_type == FallbackType.MODEL_FAILURE:
                        scenario = worker_simulator.simulate_model_failure_scenario()
                    else:  # ESCALATION
                        scenario = worker_simulator.simulate_escalation_scenario()
                    
                    scenarios.append(scenario)
                    operations_completed += 1
                    
                    # Simulate Redis logging
                    redis_data = {
                        "scenario_id": scenario.scenario_id,
                        "fallback_type": scenario.fallback_type.value,
                        "uid": scenario.uid,
                        "thread_id": scenario.thread_id,
                        "timestamp": scenario.timestamp,
                        "worker_id": worker_id
                    }
                    
                    if self.redis_logger.write_fallback_error(redis_data):
                        redis_writes += 1
                    
                    # Brief pause to prevent overwhelming the system
                    time.sleep(random.uniform(0.01, 0.05))
                    
                except Exception as e:
                    operations_failed += 1
                    errors.append(f"Worker {worker_id} operation failed: {e}")
        
        except Exception as e:
            errors.append(f"Worker {worker_id} thread failed: {e}")
        
        finally:
            with self.thread_lock:
                self.active_threads -= 1
        
        return ThreadWorkerResult(
            worker_id=worker_id,
            start_time=start_time.isoformat(),
            end_time=datetime.now(timezone.utc).isoformat(),
            operations_completed=operations_completed,
            operations_failed=operations_failed,
            scenarios=scenarios,
            errors=errors,
            redis_writes=redis_writes
        )
    
    def run_stress_test(self, thread_count: int, duration_seconds: int, 
                       logger: Any) -> StressTestMetrics:
        """Run comprehensive parallel stress test"""
        logger.info(f"Starting stress test: {thread_count} threads for {duration_seconds}s")
        
        start_time = datetime.now(timezone.utc)
        
        # Start performance monitoring
        self.performance_monitor.start_monitoring(self.redis_logger)
        
        # Create and start worker threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
            # Submit all worker tasks
            future_to_worker = {}
            for i in range(thread_count):
                worker_id = f"worker_{i+1:03d}"
                future = executor.submit(self.create_worker_thread, worker_id, duration_seconds, logger)
                future_to_worker[future] = worker_id
            
            # Track progress
            completed_workers = 0
            all_results = []
            
            # Process completed workers
            for future in concurrent.futures.as_completed(future_to_worker):
                worker_id = future_to_worker[future]
                try:
                    result = future.result()
                    all_results.append(result)
                    completed_workers += 1
                    
                    if completed_workers % max(1, thread_count // 10) == 0:
                        progress = (completed_workers / thread_count) * 100
                        logger.info(f"Progress: {completed_workers}/{thread_count} workers completed ({progress:.1f}%)")
                        
                except Exception as e:
                    logger.error(f"Worker {worker_id} failed: {e}")
        
        # Stop performance monitoring
        perf_metrics = self.performance_monitor.stop_monitoring()
        
        # Calculate final metrics
        end_time = datetime.now(timezone.utc)
        total_duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Aggregate results
        total_operations = sum(r.operations_completed for r in all_results)
        total_failed = sum(r.operations_failed for r in all_results)
        total_redis_writes = sum(r.redis_writes for r in all_results)
        
        operations_per_second = total_operations / (total_duration_ms / 1000) if total_duration_ms > 0 else 0
        
        # Calculate error distribution
        error_distribution = {"timeout": 0, "model_failure": 0, "escalation": 0}
        timeout_count = 0
        model_failure_count = 0
        escalation_count = 0
        
        for result in all_results:
            for scenario in result.scenarios:
                error_type = scenario.fallback_type.value
                error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
                
                if scenario.fallback_type == FallbackType.TIMEOUT:
                    timeout_count += 1
                elif scenario.fallback_type == FallbackType.MODEL_FAILURE:
                    model_failure_count += 1
                elif scenario.fallback_type == FallbackType.ESCALATION:
                    escalation_count += 1
        
        # Get Redis statistics
        redis_stats = self.redis_logger.get_stats()
        redis_write_rate = redis_stats["total_writes"] / (total_duration_ms / 1000) if total_duration_ms > 0 else 0
        
        # Create metrics object
        metrics = StressTestMetrics(
            test_session_id=self.session_id,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_duration_ms=total_duration_ms,
            thread_count=thread_count,
            target_duration_seconds=duration_seconds,
            total_operations=total_operations,
            successful_operations=total_operations,
            failed_operations=total_failed,
            operations_per_second=operations_per_second,
            peak_memory_mb=perf_metrics.get("peak_memory_mb", 0),
            memory_usage_samples=[s["memory_mb"] for s in self.performance_monitor.samples],
            redis_writes=redis_stats["total_writes"],
            redis_write_rate=redis_write_rate,
            redis_errors=redis_stats["total_errors"],
            max_concurrent_threads=perf_metrics.get("max_threads", thread_count),
            error_distribution=error_distribution,
            timeout_count=timeout_count,
            model_failure_count=model_failure_count,
            escalation_count=escalation_count
        )
        
        self.metrics = metrics
        
        # Log final statistics
        logger.success(f"Stress test completed in {total_duration_ms}ms")
        logger.info(f"Total operations: {total_operations}")
        logger.info(f"Operations/second: {operations_per_second:.2f}")
        logger.info(f"Redis writes: {redis_stats['total_writes']}")
        logger.info(f"Redis write rate: {redis_write_rate:.2f} writes/sec")
        logger.info(f"Peak memory: {perf_metrics.get('peak_memory_mb', 0):.1f} MB")
        logger.info(f"Success rate: {(total_operations/(total_operations+total_failed)*100):.1f}%")
        
        return metrics
    
    def save_stress_test_results(self, output_file: str, logger: Any) -> bool:
        """Save stress test results to JSON file"""
        if not self.metrics:
            logger.error("No stress test results to save")
            return False
        
        try:
            stress_results = {
                "stress_test_metadata": {
                    "report_type": "stress_test_results",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "session_id": self.session_id,
                    "mas_lite_protocol": "v2.1"
                },
                "test_summary": {
                    "thread_count": self.metrics.thread_count,
                    "target_duration_seconds": self.metrics.target_duration_seconds,
                    "actual_duration_ms": self.metrics.total_duration_ms,
                    "total_operations": self.metrics.total_operations,
                    "operations_per_second": self.metrics.operations_per_second,
                    "success_rate": (self.metrics.successful_operations / self.metrics.total_operations * 100) if self.metrics.total_operations > 0 else 0
                },
                "performance_metrics": {
                    "peak_memory_mb": self.metrics.peak_memory_mb,
                    "max_concurrent_threads": self.metrics.max_concurrent_threads,
                    "thread_overhead_ms": self.metrics.thread_overhead_ms
                },
                "redis_metrics": {
                    "total_writes": self.metrics.redis_writes,
                    "write_rate_per_second": self.metrics.redis_write_rate,
                    "total_errors": self.metrics.redis_errors,
                    "error_rate": (self.metrics.redis_errors / self.metrics.redis_writes * 100) if self.metrics.redis_writes > 0 else 0
                },
                "error_distribution": self.metrics.error_distribution,
                "detailed_metrics": self.metrics.to_dict()
            }
            
            with open(output_file, 'w') as f:
                json.dump(stress_results, f, indent=2, default=str)
            
            logger.success(f"Stress test results saved to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save stress test results: {e}")
            return False


if __name__ == "__main__":
    """Test the stress test engine"""
    print("🧪 Testing Stress Test Engine")
    
    # Create a simple logger for testing
    class SimpleLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def success(self, msg): print(f"SUCCESS: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    logger = SimpleLogger()
    
    # Run a small stress test
    engine = StressTestEngine("test_session")
    metrics = engine.run_stress_test(thread_count=5, duration_seconds=3, logger=logger)
    
    print(f"✅ Test completed:")
    print(f"   Total operations: {metrics.total_operations}")
    print(f"   Operations/second: {metrics.operations_per_second:.2f}")
    print(f"   Redis writes: {metrics.redis_writes}")
    print(f"   Peak memory: {metrics.peak_memory_mb:.1f} MB")
    
    # Save results
    engine.save_stress_test_results("test_stress_results.json", logger) 