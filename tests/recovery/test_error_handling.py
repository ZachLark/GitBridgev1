#!/usr/bin/env python3
"""Error recovery testing suite for GitBridge."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from generate_task_chain import (
    TaskParams,
    generate_single_task,
    write_to_log,
    summarize_task_chain,
    ResourceExceededError
)

def test_file_corruption_recovery():
    """Test recovery from corrupted log files."""
    test_log = Path("test_recovery.json")
    
    # Create initial valid data
    tasks = []
    for i in range(10):
        params = TaskParams(
            phase_id="P8REC",
            task_counter=i,
            description=f"Recovery test task {i}"
        )
        tasks.append(generate_single_task(params))
    
    write_to_log(test_log, tasks)
    
    # Corrupt the file
    with test_log.open('a') as f:
        f.write("corrupted data")
    
    # Attempt recovery by writing new data
    new_tasks = [
        generate_single_task(
            TaskParams(
                phase_id="P8REC",
                task_counter=20,
                description="Recovery task"
            )
        )
    ]
    
    # Should handle corruption and rewrite file
    write_to_log(test_log, new_tasks)
    
    # Verify recovery
    with test_log.open('r') as f:
        recovered_data = json.load(f)
        assert len(recovered_data) > 0
        assert all(isinstance(task, dict) for task in recovered_data)
    
    # Cleanup
    test_log.unlink()

def test_concurrent_failure_recovery():
    """Test recovery from concurrent operation failures."""
    test_log = Path("test_concurrent_recovery.json")
    
    def simulate_failure(task_id: str):
        """Simulate a failing operation."""
        if task_id.endswith('5'):
            raise RuntimeError("Simulated failure")
        return task_id
    
    # Initialize with test data
    tasks = []
    for i in range(10):
        params = TaskParams(
            phase_id="P8REC",
            task_counter=i,
            description=f"Concurrent recovery test {i}"
        )
        tasks.append(generate_single_task(params))
    
    write_to_log(test_log, tasks)
    
    # Attempt concurrent operations with failures
    with ThreadPoolExecutor(max_workers=4) as executor:
        task_ids = [task["task_id"] for task in tasks]
        results = list(executor.map(simulate_failure, task_ids))
    
    # Verify partial success
    successful = [r for r in results if isinstance(r, str)]
    assert len(successful) >= 8  # At least 8 should succeed
    
    # Cleanup
    test_log.unlink()

def test_resource_exhaustion_recovery():
    """Test recovery from resource exhaustion."""
    test_log = Path("test_resource_recovery.json")
    large_tasks = []
    
    try:
        # Attempt to exhaust resources
        for i in range(1000):
            params = TaskParams(
                phase_id="P8REC",
                task_counter=i,
                description="X" * 1000000  # Very large description
            )
            large_tasks.append(generate_single_task(params))
    except ResourceExceededError:
        # Verify we can still write smaller tasks
        small_tasks = []
        for i in range(5):
            params = TaskParams(
                phase_id="P8REC",
                task_counter=i,
                description=f"Small task {i}"
            )
            small_tasks.append(generate_single_task(params))
        
        write_to_log(test_log, small_tasks)
        
        # Verify recovery
        with test_log.open('r') as f:
            recovered_data = json.load(f)
            assert len(recovered_data) == 5
    
    # Cleanup
    if test_log.exists():
        test_log.unlink()

def test_interrupted_operation_recovery():
    """Test recovery from interrupted operations."""
    test_log = Path("test_interrupt_recovery.json")
    
    def interrupt_handler(signum, frame):
        """Handle interrupt signal."""
        raise KeyboardInterrupt
    
    # Set up interrupt handler
    original_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, interrupt_handler)
    
    try:
        # Start long operation
        tasks = []
        for i in range(100):
            params = TaskParams(
                phase_id="P8REC",
                task_counter=i,
                description=f"Interrupt test task {i}"
            )
            tasks.append(generate_single_task(params))
        
        # Schedule interrupt
        signal.alarm(1)
        
        try:
            write_to_log(test_log, tasks)
        except KeyboardInterrupt:
            # Verify partial write
            assert test_log.exists()
            with test_log.open('r') as f:
                partial_data = json.load(f)
                assert len(partial_data) > 0
        
        # Attempt recovery
        signal.alarm(0)  # Cancel any pending alarm
        write_to_log(test_log, tasks)
        
        # Verify full recovery
        with test_log.open('r') as f:
            recovered_data = json.load(f)
            assert len(recovered_data) == 100
    finally:
        # Restore original handler
        signal.signal(signal.SIGALRM, original_handler)
        if test_log.exists():
            test_log.unlink()

def test_filesystem_error_recovery():
    """Test recovery from filesystem errors."""
    test_dir = Path("test_fs_recovery")
    test_dir.mkdir(exist_ok=True)
    test_log = test_dir / "recovery.json"
    
    try:
        # Create some tasks
        tasks = []
        for i in range(5):
            params = TaskParams(
                phase_id="P8REC",
                task_counter=i,
                description=f"Filesystem test task {i}"
            )
            tasks.append(generate_single_task(params))
        
        # Write initial data
        write_to_log(test_log, tasks)
        
        # Simulate filesystem error by removing permissions
        test_dir.chmod(0o000)
        
        # Attempt write (should fail)
        with pytest.raises(IOError):
            write_to_log(test_log, tasks)
        
        # Restore permissions and retry
        test_dir.chmod(0o755)
        write_to_log(test_log, tasks)
        
        # Verify recovery
        with test_log.open('r') as f:
            recovered_data = json.load(f)
            assert len(recovered_data) == 5
    finally:
        # Cleanup
        test_dir.chmod(0o755)
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 