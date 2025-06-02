#!/usr/bin/env python3
"""Benchmark script for task chain generator."""

import time
import memory_profiler
from pathlib import Path
from generate_task_chain import TaskParams, generate_single_task, write_to_log

def benchmark_task_generation(task_counts=[10, 100, 1000]):
    """Benchmark task generation with different sizes."""
    results = []
    for count in task_counts:
        start_time = time.time()
        peak_memory = memory_profiler.memory_usage((generate_tasks, (count,)))
        end_time = time.time()
        
        results.append({
            'task_count': count,
            'time_taken': end_time - start_time,
            'peak_memory_mb': max(peak_memory)
        })
    return results

def generate_tasks(count):
    """Generate specified number of tasks."""
    tasks = [
        generate_single_task(TaskParams(phase_id="BENCH", task_counter=i))
        for i in range(count)
    ]
    write_to_log(Path("benchmark_log.json"), tasks)

def benchmark_concurrent_writes(thread_counts=[5, 10, 20]):
    """Benchmark concurrent write performance."""
    import threading
    results = []
    for thread_count in thread_counts:
        start_time = time.time()
        threads = [
            threading.Thread(target=lambda: write_to_log(
                Path("benchmark_log.json"),
                [generate_single_task(TaskParams(phase_id="BENCH", task_counter=i))]
            ))
            for i in range(thread_count)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        end_time = time.time()
        results.append({
            'thread_count': thread_count,
            'time_taken': end_time - start_time
        })
    return results

if __name__ == "__main__":
    print("Running task generation benchmarks...")
    gen_results = benchmark_task_generation()
    for result in gen_results:
        print(f"Tasks: {result['task_count']}, "
              f"Time: {result['time_taken']:.2f}s, "
              f"Memory: {result['peak_memory_mb']:.1f}MB")
    
    print("\nRunning concurrent write benchmarks...")
    conc_results = benchmark_concurrent_writes()
    for result in conc_results:
        print(f"Threads: {result['thread_count']}, "
              f"Time: {result['time_taken']:.2f}s") 