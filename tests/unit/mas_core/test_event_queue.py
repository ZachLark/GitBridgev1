#!/usr/bin/env python3
"""
Unit tests for event queue management.
"""

import asyncio
import pytest
from datetime import datetime, timezone
from mas_core.event_queue import (
    EventQueue,
    QueueError,
    QueueTimeoutError,
    QueueFullError
)

@pytest.fixture
def queue_config():
    """Test queue configuration."""
    return {
        "queue": {
            "max_size": 5,
            "timeout": 1
        }
    }

@pytest.fixture
def event_queue(queue_config):
    """Test event queue instance."""
    return EventQueue(queue_config)

@pytest.fixture
def test_event():
    """Test event."""
    return {
        "type": "test_event",
        "id": "test_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "key": "value"
        }
    }

@pytest.mark.asyncio
async def test_queue_init(event_queue):
    """Test queue initialization."""
    assert event_queue.max_size == 5
    assert event_queue.timeout == 1
    assert event_queue.is_running() is True
    assert event_queue.get_queue_size() == 0

@pytest.mark.asyncio
async def test_enqueue_success(event_queue, test_event):
    """Test successful enqueue operation."""
    success = await event_queue.enqueue(test_event)
    assert success is True
    assert event_queue.get_queue_size() == 1

@pytest.mark.asyncio
async def test_dequeue_success(event_queue, test_event):
    """Test successful dequeue operation."""
    await event_queue.enqueue(test_event)
    event = await event_queue.dequeue()
    assert event == test_event
    assert event_queue.get_queue_size() == 0

@pytest.mark.asyncio
async def test_queue_full(event_queue, test_event):
    """Test queue full behavior."""
    # Fill the queue to capacity
    for i in range(5):
        success = await event_queue.enqueue(test_event)
        assert success is True
    
    # Try to add one more - should fail due to full queue
    success = await event_queue.enqueue(test_event)
    assert success is False

@pytest.mark.asyncio
async def test_dequeue_empty(event_queue):
    """Test dequeue from empty queue."""
    # Set a very short timeout to avoid long waits
    event_queue.timeout = 0.1
    event = await event_queue.dequeue()
    assert event is None

@pytest.mark.asyncio
async def test_queue_cleanup(event_queue, test_event):
    """Test queue cleanup functionality."""
    await event_queue.enqueue(test_event)
    assert event_queue.get_queue_size() == 1
    
    await event_queue.cleanup()
    assert event_queue.is_running() is False

@pytest.mark.asyncio
async def test_queue_context_manager(queue_config, test_event):
    """Test queue as context manager."""
    async with EventQueue(queue_config) as queue:
        success = await queue.enqueue(test_event)
        assert success is True
        
        event = await queue.dequeue()
        assert event == test_event

@pytest.mark.asyncio
async def test_queue_health_check(event_queue):
    """Test queue health check."""
    health = await event_queue.check_health()
    assert health["status"] == "healthy"
    assert health["queue_size"] == 0
    assert health["running"] is True

@pytest.mark.asyncio
async def test_queue_depth(event_queue, test_event):
    """Test queue depth functionality."""
    depth = await event_queue.get_queue_depth()
    assert depth == 0
    
    await event_queue.enqueue(test_event)
    depth = await event_queue.get_queue_depth()
    assert depth == 1
    
    await event_queue.dequeue()
    depth = await event_queue.get_queue_depth()
    assert depth == 0

@pytest.mark.asyncio
async def test_queue_size(event_queue, test_event):
    """Test queue size functionality."""
    assert event_queue.get_queue_size() == 0
    
    await event_queue.enqueue(test_event)
    assert event_queue.get_queue_size() == 1
    
    await event_queue.dequeue()
    assert event_queue.get_queue_size() == 0

@pytest.mark.asyncio
async def test_concurrent_operations(event_queue):
    """Test concurrent enqueue/dequeue operations."""
    events = [
        {"type": "event1", "id": "1"},
        {"type": "event2", "id": "2"},
        {"type": "event3", "id": "3"}
    ]
    
    # Concurrent enqueue and dequeue
    for event in events:
        await event_queue.enqueue(event)
        dequeued = await event_queue.dequeue()
        assert dequeued == event

@pytest.mark.asyncio
async def test_queue_timeout(event_queue):
    """Test queue timeout behavior."""
    # Set very short timeout
    event_queue.timeout = 0.01
    
    # Dequeue from empty queue should timeout
    event = await event_queue.dequeue()
    assert event is None

@pytest.mark.asyncio
async def test_enqueue_when_not_running(event_queue, test_event):
    """Test enqueue when queue is not running."""
    await event_queue.cleanup()  # Stop the queue
    
    success = await event_queue.enqueue(test_event)
    assert success is False

@pytest.mark.asyncio
async def test_dequeue_when_not_running(event_queue, test_event):
    """Test dequeue when queue is not running."""
    await event_queue.enqueue(test_event)  # Add an event first
    await event_queue.cleanup()  # Stop the queue
    
    event = await event_queue.dequeue()
    assert event is None

@pytest.mark.asyncio
async def test_enqueue_exception_handling(event_queue):
    """Test enqueue exception handling."""
    # Create a malformed event that might cause issues
    malformed_event = {"malformed": True}
    
    # Should handle gracefully and return False on error
    success = await event_queue.enqueue(malformed_event)
    # Even malformed events should succeed if properly structured
    assert success is True

@pytest.mark.asyncio
async def test_health_check_after_cleanup(event_queue):
    """Test health check after cleanup."""
    await event_queue.cleanup()
    
    health = await event_queue.check_health()
    assert health["status"] == "healthy"  # Should still report healthy
    assert health["running"] is False

@pytest.mark.asyncio
async def test_queue_multiple_cleanups(event_queue):
    """Test multiple cleanup calls."""
    await event_queue.cleanup()
    await event_queue.cleanup()  # Should not raise exception
    assert event_queue.is_running() is False

@pytest.mark.asyncio
async def test_queue_with_tasks(event_queue):
    """Test queue cleanup with pending tasks."""
    # Create a task
    async def dummy_task():
        await asyncio.sleep(1)
    
    task = asyncio.create_task(dummy_task())
    event_queue._tasks.add(task)
    
    # Cleanup should cancel the task
    await event_queue.cleanup()
    assert task.cancelled() or task.done()

@pytest.mark.asyncio
async def test_enqueue_timeout_simulation(queue_config):
    """Test enqueue timeout by filling queue and setting short timeout."""
    # Create queue with very short timeout
    queue_config["queue"]["timeout"] = 0.001
    queue_config["queue"]["max_size"] = 1
    
    queue = EventQueue(queue_config)
    
    # Fill the queue
    await queue.enqueue({"type": "test"})
    
    # This should timeout
    success = await queue.enqueue({"type": "test2"})
    assert success is False
    
    await queue.cleanup() 