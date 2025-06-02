#!/usr/bin/env python3
"""Performance and load testing suite for GitBridge task chain processing."""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any
import json

from generate_task_chain import (
    TaskParams,
    generate_single_task,
    write_to_log,
    summarize_task_chain
)

def generate_test_tasks(count: int) -> List[Dict[str, Any]]:
    """Generate a specified number of test tasks."""
    tasks = []
    for i in range(count):
        params = TaskParams(
            phase_id="P8PERF",
            task_counter=i,
            description=f"Performance test task {i}",
            priority_level="high" if i % 3 == 0 else "medium"
        )
        tasks.append(generate_single_task(params))
    return tasks

@pytest.mark.performance
def test_bulk_task_generation():
    """Test generation of 1000 tasks under 5 seconds."""
    start_time = time.time()
    tasks = generate_test_tasks(1000)
    generation_time = time.time() - start_time
    
    assert len(tasks) == 1000
    assert generation_time < 5.0, f"Task generation took {generation_time:.2f} seconds"
    
    # Verify task integrity
    for task in tasks:
        assert "task_id" in task
        assert task["phase_id"] == "P8PERF"
        assert "timestamp" in task

@pytest.mark.performance
def test_concurrent_task_processing():
    """Test concurrent processing of tasks with thread pool."""
    test_log = Path("test_concurrent.json")
    
    def process_batch(batch: List[Dict[str, Any]]):
        write_to_log(test_log, batch)
    
    # Generate 1000 tasks in batches of 100
    all_tasks = generate_test_tasks(1000)
    batches = [all_tasks[i:i+100] for i in range(0, len(all_tasks), 100)]
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_batch, batches)
    processing_time = time.time() - start_time
    
    assert processing_time < 5.0, f"Concurrent processing took {processing_time:.2f} seconds"
    
    # Cleanup
    if test_log.exists():
        test_log.unlink()

@pytest.mark.performance
def test_chain_summarization_performance():
    """Test summarization performance for large task chains."""
    tasks = generate_test_tasks(1000)
    
    start_time = time.time()
    summary = summarize_task_chain(tasks)
    summary_time = time.time() - start_time
    
    assert summary_time < 1.0, f"Chain summarization took {summary_time:.2f} seconds"
    assert summary.total_tasks == 1000
    assert len(summary.priority_distribution) > 0

@pytest.mark.performance
def test_concurrent_chain_updates():
    """Test concurrent updates to task chain."""
    test_log = Path("test_updates.json")
    
    def update_task(task_id: str):
        with test_log.open('r+') as f:
            data = json.load(f)
            for task in data:
                if task["task_id"] == task_id:
                    task["consensus"] = "approved"
                    break
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    
    # Initialize with test tasks
    initial_tasks = generate_test_tasks(100)
    write_to_log(test_log, initial_tasks)
    
    # Perform concurrent updates
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        task_ids = [task["task_id"] for task in initial_tasks[:20]]
        executor.map(update_task, task_ids)
    update_time = time.time() - start_time
    
    assert update_time < 2.0, f"Concurrent updates took {update_time:.2f} seconds"
    
    # Cleanup
    if test_log.exists():
        test_log.unlink()

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 