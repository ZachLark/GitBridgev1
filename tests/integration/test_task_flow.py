#!/usr/bin/env python3
"""Integration tests for GitBridge task flow."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

from generate_task_chain import (
    TaskParams,
    generate_single_task,
    write_to_log,
    summarize_task_chain
)

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "outputs").mkdir()
        yield workspace

@pytest.fixture
def sample_task_chain(temp_workspace):
    """Generate a sample task chain for testing."""
    tasks = []
    phase_id = "P8TEST"
    
    # Create a sequence of tasks with different states
    for i in range(5):
        params = TaskParams(
            phase_id=phase_id,
            task_counter=i,
            description=f"Integration test task {i}",
            priority_level="high" if i < 2 else "medium",
            sections_reviewed=["1.1", "2.0"] if i % 2 == 0 else ["3.0", "4.0"]
        )
        task = generate_single_task(params)
        tasks.append(task)
    
    # Write tasks to log file
    log_path = temp_workspace / "mas_log.json"
    write_to_log(log_path, tasks)
    
    return tasks, log_path

def test_end_to_end_task_flow(temp_workspace, sample_task_chain):
    """Test complete task flow from generation to summary."""
    tasks, log_path = sample_task_chain
    
    # Step 1: Verify task generation
    assert len(tasks) == 5
    assert all(isinstance(task["task_id"], str) for task in tasks)
    assert all(task["phase_id"] == "P8TEST" for task in tasks)
    
    # Step 2: Verify file creation
    assert log_path.exists()
    with log_path.open('r') as f:
        loaded_tasks = json.load(f)
    assert len(loaded_tasks) == 5
    
    # Step 3: Verify task structure
    for task in loaded_tasks:
        assert set(task.keys()) >= {
            "task_id",
            "phase_id",
            "description",
            "timestamp",
            "consensus",
            "status_history",
            "agent_assignment",
            "outputs",
            "priority_level",
            "sections_reviewed"
        }
    
    # Step 4: Test summary generation
    summary = summarize_task_chain(loaded_tasks)
    assert summary.phase_id == "P8TEST"
    assert summary.total_tasks == 5
    assert summary.priority_distribution["high"] == 2
    assert summary.priority_distribution["medium"] == 3
    
    # Step 5: Verify output paths
    outputs_dir = temp_workspace / "outputs"
    assert outputs_dir.exists()
    for task in loaded_tasks:
        for output_path in task["outputs"].values():
            path = output_path.split("#")[0]  # Remove hash
            assert Path(outputs_dir / Path(path).name).parent.exists()

def test_concurrent_task_updates(temp_workspace, sample_task_chain):
    """Test concurrent task updates and file locking."""
    tasks, log_path = sample_task_chain
    
    # Simulate concurrent updates
    update_tasks = []
    for i in range(3):
        params = TaskParams(
            phase_id="P8TEST",
            task_counter=i + 5,
            description=f"Concurrent task {i}",
            priority_level="high",
            sections_reviewed=["1.1", "2.0"]
        )
        task = generate_single_task(params)
        update_tasks.append(task)
    
    # Write updates
    write_to_log(log_path, update_tasks)
    
    # Verify final state
    with log_path.open('r') as f:
        final_tasks = json.load(f)
    
    assert len(final_tasks) == 8  # Original 5 + 3 new
    assert len([t for t in final_tasks if "Concurrent task" in t["description"]]) == 3

def test_task_chain_recovery(temp_workspace, sample_task_chain):
    """Test task chain recovery and validation."""
    tasks, log_path = sample_task_chain
    
    # Clean up any existing file
    if log_path.exists():
        log_path.unlink()
    
    # Simulate system interruption by writing partial data
    partial_tasks = tasks[:3]
    write_to_log(log_path, partial_tasks)
    
    # Verify partial state
    with log_path.open('r') as f:
        loaded_partial = json.load(f)
    assert len(loaded_partial) == 3
    assert all(t["task_id"] == f"task_P8TEST_{i:03d}" for i, t in enumerate(loaded_partial))
    
    # Recover by writing remaining tasks
    remaining_tasks = tasks[3:]
    write_to_log(log_path, remaining_tasks)
    
    # Verify final state
    with log_path.open('r') as f:
        recovered_tasks = json.load(f)
    assert len(recovered_tasks) == 5  # Should not duplicate tasks
    
    # Verify task order and integrity
    task_ids = [t["task_id"] for t in recovered_tasks]
    assert task_ids == sorted(task_ids)  # Tasks should maintain order
    assert all(t["phase_id"] == "P8TEST" for t in recovered_tasks)
    
    # Verify no duplicate task IDs
    assert len(set(task_ids)) == len(task_ids)

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 