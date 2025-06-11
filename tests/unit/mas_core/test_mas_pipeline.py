"""
Test MAS pipeline functionality.

This module tests the MAS pipeline functionality for GitBridge's event processing
system, following MAS Lite Protocol v2.1 pipeline requirements.
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timezone
from mas_core.pipeline import MASPipeline
from mas_core.task_chain import TaskChainManager, TaskState

@pytest.fixture
def config():
    """Test configuration."""
    return {
        "pipeline": {
            "max_retries": 3,
            "retry_delay": 0.1,
            "cleanup_interval": 60
        },
        "task_chain": {
            "states": ["Created", "InProgress", "Blocked", "Resolved", "Failed"],
            "max_concurrent": 5,
            "consensus_required": True
        },
        "consensus": {
            "timeout": 5,
            "required_nodes": 3
        },
        "queue": {
            "redis_url": "redis://localhost:6379/0",
            "max_size": 1000,
            "timeout": 5
        }
    }

@pytest.fixture
def pipeline(config):
    """Test pipeline instance."""
    return MASPipeline(config)

@pytest.fixture
def event_data():
    """Test event data."""
    return {
        "type": "test_event",
        "description": "Test event description",
        "required_capabilities": ["test"]
    }

@pytest.mark.asyncio
async def test_start_stop(pipeline):
    """Test pipeline start and stop."""
    # Start pipeline
    await pipeline.start()
    assert pipeline._running is True
    
    # Stop pipeline
    await pipeline.stop()
    assert pipeline._running is False

@pytest.mark.asyncio
async def test_process_event(pipeline, event_data):
    """Test event processing."""
    # Start pipeline
    await pipeline.start()
    
    # Enqueue event
    success = await pipeline.event_queue.enqueue(event_data)
    assert success is True
    
    # Wait for event to be processed
    await asyncio.sleep(0.1)
    
    # Stop pipeline
    await pipeline.stop()
    
    # Verify task was created
    tasks = await pipeline.task_chain.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].data == event_data
    assert tasks[0].state == TaskState.InProgress

@pytest.mark.asyncio
async def test_invalid_event(pipeline):
    """Test invalid event handling."""
    # Start pipeline
    await pipeline.start()
    
    # Enqueue invalid event
    success = await pipeline.event_queue.enqueue(None)
    assert success is False
    
    # Stop pipeline
    await pipeline.stop()
    
    # Verify no tasks were created
    tasks = await pipeline.task_chain.list_tasks()
    assert len(tasks) == 0

@pytest.mark.asyncio
async def test_cleanup(pipeline, event_data):
    """Test cleanup."""
    # Start pipeline
    await pipeline.start()
    
    # Enqueue event
    success = await pipeline.event_queue.enqueue(event_data)
    assert success is True
    
    # Wait for event to be processed
    await asyncio.sleep(0.1)
    
    # Clean up
    await pipeline.cleanup()
    
    # Verify tasks and events are cleared
    tasks = await pipeline.task_chain.list_tasks()
    assert len(tasks) == 0
    
    # Stop pipeline
    await pipeline.stop()

@pytest.mark.asyncio
async def test_error_handling(pipeline):
    """Test error handling."""
    # Start pipeline
    await pipeline.start()
    
    # Enqueue invalid event
    success = await pipeline.event_queue.enqueue({"type": "invalid"})
    assert success is True
    
    # Wait for event to be processed
    await asyncio.sleep(0.1)
    
    # Stop pipeline
    await pipeline.stop()
    
    # Verify task was not created
    tasks = await pipeline.task_chain.list_tasks()
    assert len(tasks) == 0

@pytest.mark.asyncio
async def test_concurrent_events(pipeline, event_data):
    """Test concurrent event processing."""
    # Start pipeline
    await pipeline.start()
    
    # Enqueue multiple events
    events = []
    for _ in range(3):
        event = event_data.copy()
        event["id"] = str(uuid.uuid4())
        events.append(event)
        success = await pipeline.event_queue.enqueue(event)
        assert success is True
        
    # Wait for events to be processed
    await asyncio.sleep(0.3)
    
    # Stop pipeline
    await pipeline.stop()
    
    # Verify tasks were created
    tasks = await pipeline.task_chain.list_tasks()
    assert len(tasks) == 3
    assert all(task.state == TaskState.InProgress for task in tasks)

@pytest.mark.asyncio
async def test_pipeline_recovery(pipeline, event_data):
    """Test pipeline recovery after error."""
    # Start pipeline
    await pipeline.start()
    
    # Enqueue event that will cause error
    event = event_data.copy()
    event["type"] = "error"
    success = await pipeline.event_queue.enqueue(event)
    assert success is True
    
    # Wait for error to be processed
    await asyncio.sleep(0.1)
    
    # Enqueue valid event
    success = await pipeline.event_queue.enqueue(event_data)
    assert success is True
    
    # Wait for event to be processed
    await asyncio.sleep(0.1)
    
    # Stop pipeline
    await pipeline.stop()
    
    # Verify valid task was created
    tasks = await pipeline.task_chain.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].data == event_data 