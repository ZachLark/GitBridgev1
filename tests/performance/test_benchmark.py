#!/usr/bin/env python3
"""Benchmark testing suite for GitBridge task chain processing."""

import pytest
import time
import statistics
from typing import List, Dict, Any, Tuple
from pathlib import Path
import json

from generate_task_chain import (
    TaskParams,
    generate_single_task,
    write_to_log,
    summarize_task_chain
)

def measure_operation_time(func, *args, **kwargs) -> Tuple[float, Any]:
    """Measure operation time and return result."""
    start_time = time.time()
    result = func(*args, **kwargs)
    return time.time() - start_time, result

@pytest.mark.performance
def test_task_generation_benchmarks():
    """Benchmark task generation performance."""
    generation_times = []
    
    # Measure multiple iterations
    for _ in range(10):
        elapsed, task = measure_operation_time(
            generate_single_task,
            TaskParams(
                phase_id="P8BENCH",
                task_counter=0,
                description="Benchmark test task",
                priority_level="high"
            )
        )
        generation_times.append(elapsed * 1000)  # Convert to milliseconds
    
    avg_time = statistics.mean(generation_times)
    max_time = max(generation_times)
    
    # Single task generation should be fast
    assert avg_time < 10.0, f"Average task generation time: {avg_time:.2f}ms"
    assert max_time < 20.0, f"Maximum task generation time: {max_time:.2f}ms"

@pytest.mark.performance
def test_chain_processing_benchmarks():
    """Benchmark task chain processing performance."""
    # Generate test data
    tasks = []
    for i in range(1000):
        params = TaskParams(
            phase_id="P8BENCH",
            task_counter=i,
            description=f"Benchmark chain task {i}",
            priority_level="high" if i % 3 == 0 else "medium"
        )
        tasks.append(generate_single_task(params))
    
    # Measure chain processing time
    elapsed, summary = measure_operation_time(summarize_task_chain, tasks)
    processing_time = elapsed * 1000  # Convert to milliseconds
    
    # Should process 1000 tasks in under 5 seconds (5000ms)
    assert processing_time < 5000.0, f"Chain processing time: {processing_time:.2f}ms"
    assert summary.total_tasks == 1000

@pytest.mark.performance
def test_io_operation_benchmarks():
    """Benchmark I/O operations performance."""
    test_log = Path("benchmark_test.json")
    write_times = []
    read_times = []
    
    # Generate test data
    tasks = []
    for i in range(100):
        params = TaskParams(
            phase_id="P8BENCH",
            task_counter=i,
            description=f"Benchmark I/O task {i}",
            priority_level="high"
        )
        tasks.append(generate_single_task(params))
    
    # Measure write performance
    for i in range(5):
        elapsed, _ = measure_operation_time(write_to_log, test_log, tasks)
        write_times.append(elapsed * 1000)  # Convert to milliseconds
    
    # Measure read performance
    def read_log():
        with test_log.open('r') as f:
            return json.load(f)
    
    for _ in range(5):
        elapsed, data = measure_operation_time(read_log)
        read_times.append(elapsed * 1000)
    
    avg_write = statistics.mean(write_times)
    avg_read = statistics.mean(read_times)
    
    # Performance assertions
    assert avg_write < 500.0, f"Average write time: {avg_write:.2f}ms"
    assert avg_read < 100.0, f"Average read time: {avg_read:.2f}ms"
    
    # Cleanup
    if test_log.exists():
        test_log.unlink()

@pytest.mark.performance
def test_task_delegation_benchmarks():
    """Benchmark task delegation performance."""
    from mas_delegate import load_and_validate_task, delegate_task
    
    # Create a test task file
    test_task = {
        "task_id": "a" * 64,  # 64-char hex string
        "description": "Benchmark delegation task",
        "assignee": "test_agent",
        "max_cycles": 10,
        "token_budget": 1000
    }
    
    task_file = Path("benchmark_task.json")
    with task_file.open('w') as f:
        json.dump(test_task, f)
    
    # Measure validation performance
    validation_times = []
    for _ in range(10):
        elapsed, _ = measure_operation_time(load_and_validate_task, task_file)
        validation_times.append(elapsed * 1000)
    
    avg_validation = statistics.mean(validation_times)
    assert avg_validation < 10.0, f"Average validation time: {avg_validation:.2f}ms"
    
    # Cleanup
    task_file.unlink()

@pytest.mark.performance
def test_end_to_end_benchmarks():
    """Benchmark end-to-end task chain operations."""
    test_log = Path("benchmark_e2e.json")
    
    def end_to_end_operation():
        # Generate tasks
        tasks = []
        for i in range(100):
            params = TaskParams(
                phase_id="P8BENCH",
                task_counter=i,
                description=f"E2E benchmark task {i}",
                priority_level="high"
            )
            tasks.append(generate_single_task(params))
        
        # Write to log
        write_to_log(test_log, tasks)
        
        # Read and summarize
        with test_log.open('r') as f:
            loaded_tasks = json.load(f)
        return summarize_task_chain(loaded_tasks)
    
    elapsed, summary = measure_operation_time(end_to_end_operation)
    total_time = elapsed * 1000  # Convert to milliseconds
    
    # End-to-end operation should complete in under 1 second
    assert total_time < 1000.0, f"End-to-end operation time: {total_time:.2f}ms"
    assert summary.total_tasks == 100
    
    # Cleanup
    if test_log.exists():
        test_log.unlink()

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 