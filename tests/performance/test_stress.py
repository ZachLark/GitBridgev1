#!/usr/bin/env python3
"""Stress testing suite for GitBridge task chain processing."""

import pytest
import time
import resource
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any
import psutil
import json

from generate_task_chain import (
    TaskParams,
    generate_single_task,
    write_to_log,
    summarize_task_chain,
    ResourceExceededError
)

def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)

@pytest.mark.performance
def test_memory_usage_under_load():
    """Test memory usage stays within bounds under heavy load."""
    initial_memory = get_memory_usage()
    large_tasks = []
    
    # Generate tasks with increasingly large descriptions
    try:
        for i in range(500):
            params = TaskParams(
                phase_id="P8STRESS",
                task_counter=i,
                description="X" * (i * 100),  # Increasing description size
                priority_level="high"
            )
            large_tasks.append(generate_single_task(params))
    except ResourceExceededError:
        # Expected to fail at some point
        pass
    
    final_memory = get_memory_usage()
    memory_increase = final_memory - initial_memory
    
    # Should not increase by more than 100MB
    assert memory_increase < 100, f"Memory usage increased by {memory_increase:.2f}MB"

@pytest.mark.performance
def test_cpu_bound_operations():
    """Test CPU-intensive operations with resource limits."""
    test_log = Path("stress_test.json")
    
    def cpu_intensive_task():
        # Generate and process large number of tasks
        tasks = []
        for i in range(1000):
            params = TaskParams(
                phase_id="P8STRESS",
                task_counter=i,
                description=f"CPU stress test task {i}",
                priority_level="high"
            )
            tasks.append(generate_single_task(params))
        
        # Perform CPU-intensive summarization
        summary = summarize_task_chain(tasks)
        write_to_log(test_log, tasks)
        return summary
    
    start_time = time.time()
    summary = cpu_intensive_task()
    execution_time = time.time() - start_time
    
    assert execution_time < 10.0, f"CPU-intensive task took {execution_time:.2f} seconds"
    assert summary.total_tasks == 1000
    
    # Cleanup
    if test_log.exists():
        test_log.unlink()

@pytest.mark.performance
def test_concurrent_resource_limits():
    """Test behavior under concurrent resource-intensive operations."""
    def resource_intensive_operation():
        tasks = []
        try:
            for i in range(200):
                params = TaskParams(
                    phase_id="P8STRESS",
                    task_counter=i,
                    description="X" * 1000,
                    priority_level="high"
                )
                tasks.append(generate_single_task(params))
            return len(tasks)
        except ResourceExceededError:
            return len(tasks)
    
    # Run multiple resource-intensive operations concurrently
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: resource_intensive_operation(), range(4)))
    
    # At least some operations should complete
    assert any(r > 0 for r in results), "All operations failed"
    
    # Memory usage should still be reasonable
    current_memory = get_memory_usage()
    assert current_memory < 500, f"Memory usage too high: {current_memory:.2f}MB"

@pytest.mark.performance
def test_io_stress():
    """Test I/O operations under stress."""
    test_log = Path("io_stress_test.json")
    
    def io_intensive_operation(batch_num: int):
        tasks = []
        for i in range(100):
            params = TaskParams(
                phase_id="P8STRESS",
                task_counter=i + (batch_num * 100),
                description=f"I/O stress test task {i}",
                priority_level="high"
            )
            tasks.append(generate_single_task(params))
        write_to_log(test_log, tasks)
    
    start_time = time.time()
    
    # Perform multiple I/O operations concurrently
    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(io_intensive_operation, range(10))
    
    io_time = time.time() - start_time
    
    assert io_time < 15.0, f"I/O stress test took {io_time:.2f} seconds"
    
    # Verify file integrity
    with test_log.open('r') as f:
        data = json.load(f)
        assert len(data) == 1000, f"Expected 1000 tasks, got {len(data)}"
    
    # Cleanup
    test_log.unlink()

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 