#!/usr/bin/env python3
"""Test suite for task chain generation."""

import pytest
import json
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

from generate_task_chain import (
    TaskParams,
    generate_single_task,
    generate_task_id,
    write_to_log,
    TaskGenerationError,
    LogFileError,
    PRIORITY_LEVELS
)

@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        yield Path(f.name)
        Path(f.name).unlink()

@pytest.fixture
def valid_task_params():
    """Create valid task parameters for testing."""
    return TaskParams(phase_id="P7TEST", task_counter=0)

def test_task_params_validation():
    """Test TaskParams validation."""
    # Test empty phase_id
    with pytest.raises(ValueError, match="phase_id cannot be empty"):
        TaskParams(phase_id="", task_counter=0)
    
    # Test negative task counter
    with pytest.raises(ValueError, match="task_counter must be a non-negative integer"):
        TaskParams(phase_id="P7TEST", task_counter=-1)
    
    # Test invalid priority level
    with pytest.raises(ValueError, match="priority_level must be one of"):
        TaskParams(phase_id="P7TEST", task_counter=0, priority_level="invalid")

def test_generate_task_id():
    """Test task ID generation."""
    task_id = generate_task_id("P7TEST", 42)
    assert task_id == "task_P7TEST_042"
    assert len(task_id) > 0

def test_generate_single_task():
    """Test single task generation."""
    params = TaskParams(
        phase_id="P7TEST",
        task_counter=1,
        description="Test task",
        priority_level="high"
    )
    task = generate_single_task(params)
    
    assert task["task_id"] == "task_P7TEST_001"
    assert task["phase_id"] == "P7TEST"
    assert task["description"] == "Test task"
    assert task["priority_level"] == "high"
    assert isinstance(task["timestamp"], str)
    assert task["consensus"] == "pending"
    assert len(task["status_history"]) == 1
    assert task["status_history"][0]["status"] == "pending"

def test_write_to_log(test_workspace):
    """Test writing tasks to log file."""
    log_path = test_workspace / "test_log.json"
    
    # Generate a test task
    params = TaskParams(
        phase_id="TEST",
        task_counter=0,
        description="Test task"
    )
    task = generate_single_task(params)
    
    # Write task
    write_to_log(log_path, [task])
    
    # Verify written content
    with log_path.open('r') as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["task_id"] == task["task_id"]

def test_concurrent_write(test_workspace):
    """Test concurrent write operations."""
    temp_log_file = test_workspace / "concurrent_test.json"
    
    # Create initial empty file
    temp_log_file.write_text("[]")
    
    # Create tasks for concurrent writing
    tasks = []
    for i in range(5):
        params = TaskParams(
            phase_id="TEST",
            task_counter=i,
            description=f"Concurrent task {i}"
        )
        tasks.append(generate_single_task(params))
    
    # Write tasks concurrently
    threads = []
    for task in tasks:
        thread = threading.Thread(target=write_to_log, args=(temp_log_file, [task]))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify results
    with temp_log_file.open('r') as f:
        data = json.load(f)
        
    # Check that all tasks were written exactly once
    assert len(data) == 5
    task_ids = {task["task_id"] for task in data}
    assert len(task_ids) == 5  # No duplicates
    
    # Verify task integrity
    for task in data:
        assert task["phase_id"] == "TEST"
        assert "description" in task
        assert task["task_id"].startswith("task_TEST_")

def test_large_dataset(test_workspace):
    """Test handling of large datasets."""
    log_path = test_workspace / "large_test.json"
    
    # Generate 50 tasks
    tasks = []
    for i in range(50):
        params = TaskParams(
            phase_id="TEST",
            task_counter=i,
            description=f"Large dataset task {i}",
            priority_level=PRIORITY_LEVELS[i % len(PRIORITY_LEVELS)]
        )
        tasks.append(generate_single_task(params))
    
    # Write tasks
    write_to_log(log_path, tasks)
    
    # Verify written content
    with log_path.open('r') as f:
        data = json.load(f)
        assert len(data) == 50
        assert all(isinstance(task["task_id"], str) for task in data)
        assert all(task["phase_id"] == "TEST" for task in data)

def test_error_handling(test_workspace):
    """Test error handling in task chain operations."""
    # Test case 1: Invalid file path
    with pytest.raises(LogFileError, match="Failed to write to log file"):
        write_to_log(Path("/nonexistent/path/file.json"), [{}])
    
    # Test case 2: Invalid task data
    with pytest.raises(ValueError, match="phase_id cannot be empty"):
        generate_single_task(TaskParams(
            phase_id="",  # Invalid empty phase
            task_counter=0
        ))
    
    # Test case 3: Malformed JSON
    malformed_path = test_workspace / "malformed.json"
    malformed_path.write_text("invalid json content")
    
    # Should handle malformed JSON gracefully
    task = generate_single_task(TaskParams(
        phase_id="TEST",
        task_counter=0
    ))
    write_to_log(malformed_path, [task])
    
    # Verify recovery
    with malformed_path.open('r') as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["task_id"] == "task_TEST_000"

if __name__ == "__main__":
    pytest.main([__file__]) 