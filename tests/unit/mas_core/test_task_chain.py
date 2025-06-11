#!/usr/bin/env python3
"""
Test task chain functionality.

This module tests the task chain functionality for GitBridge's event processing
system, following MAS Lite Protocol v2.1 task chain requirements.
"""

import pytest
import uuid
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from mas_core.task_chain import (
    TaskChainManager,
    TaskState,
    TaskMetadata,
    Task,
    TaskSource,
    TaskError,
    TaskNotFoundError,
    InvalidStateTransitionError,
    ConcurrentTaskLimitError
)
from mas_core.consensus import ConsensusManager, ConsensusTimeoutError, ConsensusState

@pytest.fixture
def task_chain_config():
    """Test task chain configuration."""
    return {
        "task_chain": {
            "states": [state.value for state in TaskState],
            "max_concurrent": 3,
            "consensus_required": True
        },
        "consensus": {
            "timeout": 1,
            "required_nodes": 3
        }
    }

@pytest.fixture
def task_chain(task_chain_config):
    """Test task chain instance."""
    return TaskChainManager(task_chain_config)

@pytest.fixture
def test_task_data():
    """Test task data."""
    return {
        "type": "test_task",
        "description": "Test task description",
        "parameters": {
            "key": "value"
        }
    }

@pytest.fixture
def test_metadata():
    """Test task metadata."""
    return TaskMetadata(
        created_by="test_user",
        assigned_to="test_agent",
        priority="high",
        tags=["test", "unit"],
        source=TaskSource.Manual
    )

@pytest.mark.asyncio
async def test_create_task(task_chain, test_task_data, test_metadata):
    """Test task creation."""
    task_id = "test_001"
    success = await task_chain.create_task(task_id, test_task_data, test_metadata)
    assert success is True
    
    task = await task_chain.get_task(task_id)
    assert task is not None
    assert task.task_id == task_id
    assert task.state == TaskState.Created
    assert task.data == test_task_data
    assert task.metadata == test_metadata

@pytest.mark.asyncio
async def test_create_task_invalid_data(task_chain):
    """Test task creation with invalid data."""
    with pytest.raises(ValueError):
        await task_chain.create_task("", {})
        
    with pytest.raises(ValueError):
        await task_chain.create_task("test_001", None)

@pytest.mark.asyncio
async def test_create_task_concurrent_limit(task_chain, test_task_data):
    """Test concurrent task limit."""
    # Create max_concurrent tasks
    for i in range(3):
        task_id = f"test_{i}"
        success = await task_chain.create_task(task_id, test_task_data)
        assert success is True
        
    # Try to create one more task
    with pytest.raises(ConcurrentTaskLimitError):
        await task_chain.create_task("test_4", test_task_data)

@pytest.mark.asyncio
async def test_create_task_exception_handling(task_chain, test_task_data):
    """Test exception handling in create_task method."""
    # Mock Task creation to raise an unexpected exception
    with patch('mas_core.task_chain.Task', side_effect=RuntimeError("Unexpected error")):
        result = await task_chain.create_task("test_001", test_task_data)
        assert result is False

@pytest.mark.asyncio
async def test_create_task_default_metadata(task_chain, test_task_data):
    """Test task creation with default metadata."""
    task_id = "test_001"
    success = await task_chain.create_task(task_id, test_task_data)  # No metadata provided
    assert success is True
    
    task = await task_chain.get_task(task_id)
    assert task.metadata.created_by == "system"
    assert task.metadata.source == TaskSource.System

@pytest.mark.asyncio
async def test_update_task_state_valid(task_chain, test_task_data):
    """Test valid task state update."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data)
    
    # Valid transition: Created -> InProgress
    success = await task_chain.update_task_state(task_id, TaskState.InProgress)
    assert success is True
    
    task = await task_chain.get_task(task_id)
    assert task.state == TaskState.InProgress

@pytest.mark.asyncio
async def test_update_task_state_invalid(task_chain, test_task_data):
    """Test invalid task state update."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data)
    
    # Invalid transition: Created -> Resolved
    with pytest.raises(InvalidStateTransitionError):
        await task_chain.update_task_state(task_id, TaskState.Resolved)

@pytest.mark.asyncio
async def test_update_task_state_not_found(task_chain):
    """Test updating non-existent task state."""
    with pytest.raises(TaskNotFoundError):
        await task_chain.update_task_state("nonexistent", TaskState.InProgress)

@pytest.mark.asyncio
async def test_update_task_state_consensus_required(task_chain, test_task_data):
    """Test state update with consensus requirement."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data)
    await task_chain.update_task_state(task_id, TaskState.InProgress)
    
    # Mock consensus manager to return approved consensus
    mock_consensus = MagicMock()
    mock_consensus.state = ConsensusState.Approved
    task_chain.consensus_manager.get_consensus = AsyncMock(return_value=mock_consensus)
    
    # Should succeed with approved consensus
    success = await task_chain.update_task_state(task_id, TaskState.Resolved)
    assert success is True

@pytest.mark.asyncio
async def test_update_task_state_consensus_not_approved(task_chain, test_task_data):
    """Test state update with consensus not approved."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data)
    await task_chain.update_task_state(task_id, TaskState.InProgress)
    
    # Mock consensus manager to return pending consensus
    mock_consensus = MagicMock()
    mock_consensus.state = ConsensusState.Pending
    task_chain.consensus_manager.get_consensus = AsyncMock(return_value=mock_consensus)
    
    # Should fail without approved consensus
    success = await task_chain.update_task_state(task_id, TaskState.Resolved)
    assert success is False

@pytest.mark.asyncio
async def test_update_task_state_consensus_timeout(task_chain, test_task_data):
    """Test state update with consensus timeout."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data)
    await task_chain.update_task_state(task_id, TaskState.InProgress)
    
    # Mock consensus manager to raise timeout
    task_chain.consensus_manager.get_consensus = AsyncMock(side_effect=asyncio.TimeoutError())
    
    # Should fail due to timeout
    success = await task_chain.update_task_state(task_id, TaskState.Resolved)
    assert success is False

@pytest.mark.asyncio
async def test_update_task_state_consensus_timeout_error(task_chain, test_task_data):
    """Test state update with ConsensusTimeoutError."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data)
    await task_chain.update_task_state(task_id, TaskState.InProgress)
    
    # Mock consensus manager to raise ConsensusTimeoutError
    task_chain.consensus_manager.get_consensus = AsyncMock(side_effect=ConsensusTimeoutError("Consensus timeout"))
    
    # Should fail due to consensus timeout
    success = await task_chain.update_task_state(task_id, TaskState.Resolved)
    assert success is False

@pytest.mark.asyncio
async def test_update_task_state_general_exception(task_chain, test_task_data):
    """Test exception handling in update_task_state method."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data)
    
    # Mock _get_current_time to raise an unexpected exception
    with patch.object(task_chain, '_get_current_time', side_effect=RuntimeError("Time error")):
        result = await task_chain.update_task_state(task_id, TaskState.InProgress)
        assert result is False

@pytest.mark.asyncio
async def test_get_task(task_chain, test_task_data):
    """Test getting task."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data)
    
    task = await task_chain.get_task(task_id)
    assert task is not None
    assert task.task_id == task_id
    assert task.state == TaskState.Created
    assert task.data == test_task_data

@pytest.mark.asyncio
async def test_get_task_not_found(task_chain):
    """Test getting non-existent task."""
    task = await task_chain.get_task("nonexistent")
    assert task is None

@pytest.mark.asyncio
async def test_list_tasks(task_chain, test_task_data):
    """Test listing tasks."""
    # Create multiple tasks
    task_ids = ["test_001", "test_002", "test_003"]
    for task_id in task_ids:
        await task_chain.create_task(task_id, test_task_data)
        
    # List all tasks
    tasks = await task_chain.list_tasks()
    assert len(tasks) == 3
    assert all(task.state == TaskState.Created for task in tasks)
    
    # Update one task state
    await task_chain.update_task_state(task_ids[0], TaskState.InProgress)
    
    # List tasks by state
    created_tasks = await task_chain.list_tasks(TaskState.Created)
    assert len(created_tasks) == 2
    
    in_progress_tasks = await task_chain.list_tasks(TaskState.InProgress)
    assert len(in_progress_tasks) == 1

@pytest.mark.asyncio
async def test_task_state_transitions(task_chain, test_task_data):
    """Test task state transitions."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data)
    
    # Created -> InProgress
    await task_chain.update_task_state(task_id, TaskState.InProgress)
    task = await task_chain.get_task(task_id)
    assert task.state == TaskState.InProgress
    
    # InProgress -> Blocked
    await task_chain.update_task_state(task_id, TaskState.Blocked)
    task = await task_chain.get_task(task_id)
    assert task.state == TaskState.Blocked
    
    # Blocked -> InProgress
    await task_chain.update_task_state(task_id, TaskState.InProgress)
    task = await task_chain.get_task(task_id)
    assert task.state == TaskState.InProgress
    
    # InProgress -> Failed
    await task_chain.update_task_state(task_id, TaskState.Failed)
    task = await task_chain.get_task(task_id)
    assert task.state == TaskState.Failed
    
    # Cannot transition from Failed (terminal state)
    with pytest.raises(InvalidStateTransitionError):
        await task_chain.update_task_state(task_id, TaskState.InProgress)

@pytest.mark.asyncio
async def test_task_metadata(task_chain, test_task_data, test_metadata):
    """Test task metadata handling."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data, test_metadata)
    
    task = await task_chain.get_task(task_id)
    assert task.metadata.created_by == "test_user"
    assert task.metadata.assigned_to == "test_agent"
    assert task.metadata.priority == "high"
    assert task.metadata.tags == ["test", "unit"]
    assert task.metadata.source == TaskSource.Manual

@pytest.mark.asyncio
async def test_task_cleanup(task_chain, test_task_data):
    """Test task cleanup."""
    # Create multiple tasks
    task_ids = ["test_001", "test_002", "test_003"]
    for task_id in task_ids:
        await task_chain.create_task(task_id, test_task_data)
        
    # Update some task states
    await task_chain.update_task_state(task_ids[0], TaskState.InProgress)
    await task_chain.update_task_state(task_ids[1], TaskState.InProgress)
    await task_chain.update_task_state(task_ids[1], TaskState.Failed)
    await task_chain.update_task_state(task_ids[2], TaskState.InProgress)
    await task_chain.update_task_state(task_ids[2], TaskState.Failed)
    
    # Run cleanup
    await task_chain.cleanup()
    
    # Verify only non-terminal tasks remain
    tasks = await task_chain.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].state == TaskState.InProgress

@pytest.mark.asyncio
async def test_cleanup_exception_handling(task_chain, test_task_data):
    """Test exception handling in cleanup method."""
    task_id = "test_001"
    await task_chain.create_task(task_id, test_task_data)
    
    # Mock consensus manager cleanup to raise an exception
    task_chain.consensus_manager.cleanup = AsyncMock(side_effect=RuntimeError("Cleanup error"))
    
    # Should handle exception gracefully
    await task_chain.cleanup()
    
    # Task should still be there since cleanup failed
    task = await task_chain.get_task(task_id)
    assert task is not None 