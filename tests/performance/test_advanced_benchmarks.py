#!/usr/bin/env python3
"""Advanced performance benchmarking suite for GitBridge."""

import pytest
import time
import psutil
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np

from generate_task_chain import TaskParams, generate_single_task
from mas_delegate import load_and_validate_task

@pytest.mark.benchmark(
    group="memory",
    min_rounds=100,
    warmup=False
)
def test_memory_usage_under_load(benchmark):
    """Test memory usage under heavy load conditions."""
    def measure_memory():
        tasks = []
        for i in range(1000):
            params = TaskParams(
                phase_id="P8PERF",
                task_counter=i,
                description=f"Memory test task {i}"
            )
            tasks.append(generate_single_task(params))
        
        # Write tasks to file
        test_log = Path("test_memory.json")
        with test_log.open('w') as f:
            json.dump(tasks, f)
        
        # Process tasks and measure memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        load_and_validate_task(test_log)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        test_log.unlink()
        return memory_increase
    
    result = benchmark(measure_memory)
    assert result < 100 * 1024 * 1024  # Memory increase should be less than 100MB

@pytest.mark.benchmark(
    group="cpu",
    min_rounds=50
)
def test_cpu_utilization(benchmark):
    """Test CPU utilization under parallel processing."""
    def parallel_processing():
        tasks = []
        for i in range(100):
            params = TaskParams(
                phase_id="P8PERF",
                task_counter=i,
                description=f"CPU test task {i}"
            )
            tasks.append(generate_single_task(params))
        
        # Process tasks in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            test_log = Path("test_cpu.json")
            with test_log.open('w') as f:
                json.dump(tasks, f)
            
            futures = []
            for _ in range(4):
                futures.append(
                    executor.submit(load_and_validate_task, test_log)
                )
            
            # Wait for all tasks to complete
            for future in futures:
                future.result()
            
            test_log.unlink()
    
    result = benchmark(parallel_processing)
    assert result.stats.mean < 2.0  # Average processing time should be under 2 seconds

@pytest.mark.benchmark(
    group="io",
    min_rounds=50
)
def test_io_performance(benchmark):
    """Test I/O performance with large datasets."""
    def io_operations():
        # Generate large dataset
        large_tasks = []
        for i in range(5000):
            params = TaskParams(
                phase_id="P8PERF",
                task_counter=i,
                description="A" * 1000  # 1KB description
            )
            large_tasks.append(generate_single_task(params))
        
        # Measure I/O operations
        test_log = Path("test_io.json")
        
        # Write operation
        start_time = time.time()
        with test_log.open('w') as f:
            json.dump(large_tasks, f)
        write_time = time.time() - start_time
        
        # Read operation
        start_time = time.time()
        with test_log.open('r') as f:
            data = json.load(f)
        read_time = time.time() - start_time
        
        test_log.unlink()
        return max(write_time, read_time)
    
    result = benchmark(io_operations)
    assert result.stats.mean < 1.0  # I/O operations should complete within 1 second

@pytest.mark.benchmark(
    group="network",
    min_rounds=20
)
def test_network_throughput(benchmark):
    """Test network throughput with concurrent connections."""
    async def simulate_network_load():
        # Simulate network operations
        tasks = []
        for i in range(100):
            params = TaskParams(
                phase_id="P8PERF",
                task_counter=i,
                description=f"Network test task {i}"
            )
            tasks.append(generate_single_task(params))
        
        # Simulate concurrent network operations
        async def process_batch(batch):
            test_log = Path(f"test_network_{batch[0]['task_counter']}.json")
            with test_log.open('w') as f:
                json.dump(batch, f)
            await asyncio.sleep(0.01)  # Simulate network delay
            load_and_validate_task(test_log)
            test_log.unlink()
        
        # Process in batches
        batch_size = 10
        batches = [tasks[i:i+batch_size] for i in range(0, len(tasks), batch_size)]
        await asyncio.gather(*[process_batch(batch) for batch in batches])
    
    def run_network_test():
        asyncio.run(simulate_network_load())
    
    result = benchmark(run_network_test)
    assert result.stats.mean < 5.0  # Network operations should complete within 5 seconds

@pytest.mark.benchmark(
    group="latency",
    min_rounds=100
)
def test_response_latency(benchmark):
    """Test response latency under various conditions."""
    def measure_latency():
        latencies = []
        
        # Generate test cases with varying complexity
        test_cases = []
        for i in range(100):
            params = TaskParams(
                phase_id="P8PERF",
                task_counter=i,
                description="X" * (i * 100)  # Increasing complexity
            )
            test_cases.append(generate_single_task(params))
        
        test_log = Path("test_latency.json")
        
        # Measure latency for each test case
        for task in test_cases:
            with test_log.open('w') as f:
                json.dump([task], f)
            
            start_time = time.time()
            load_and_validate_task(test_log)
            latency = time.time() - start_time
            latencies.append(latency)
        
        test_log.unlink()
        return np.percentile(latencies, 95)  # Return 95th percentile latency
    
    result = benchmark(measure_latency)
    assert result < 0.1  # 95th percentile latency should be under 100ms

@pytest.mark.benchmark(
    group="scalability",
    min_rounds=10
)
def test_scalability(benchmark):
    """Test system scalability with increasing load."""
    def measure_scalability():
        # Test with exponentially increasing load
        load_levels = [10, 100, 1000, 10000]
        processing_times = []
        
        for load in load_levels:
            tasks = []
            for i in range(load):
                params = TaskParams(
                    phase_id="P8PERF",
                    task_counter=i,
                    description=f"Scalability test task {i}"
                )
                tasks.append(generate_single_task(params))
            
            test_log = Path("test_scalability.json")
            with test_log.open('w') as f:
                json.dump(tasks, f)
            
            start_time = time.time()
            load_and_validate_task(test_log)
            processing_time = time.time() - start_time
            processing_times.append(processing_time / load)  # Time per task
            
            test_log.unlink()
        
        # Calculate scalability factor (should be close to 1 for linear scaling)
        scalability = np.mean([processing_times[i] / processing_times[i+1]
                             for i in range(len(processing_times)-1)])
        return scalability
    
    result = benchmark(measure_scalability)
    assert 0.7 <= result <= 1.3  # Scalability factor should be close to 1

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 