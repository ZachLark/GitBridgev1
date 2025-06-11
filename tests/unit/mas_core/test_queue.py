"""
Unit tests for queue interface.
"""

import pytest
from abc import ABC
from mas_core.queue import EventQueue

class ConcreteEventQueue(EventQueue):
    """Concrete implementation of EventQueue for testing."""
    
    def __init__(self):
        self.queue = []
        self.running = True
        
    async def enqueue(self, event) -> bool:
        """Enqueue an event."""
        if not self.running:
            return False
        self.queue.append(event)
        return True
        
    async def dequeue(self):
        """Dequeue an event."""
        if not self.running or not self.queue:
            return None
        return self.queue.pop(0)
        
    async def cleanup(self) -> None:
        """Clean up queue resources."""
        self.queue.clear()
        self.running = False
        
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return len(self.queue)
        
    def is_running(self) -> bool:
        """Check if queue is running."""
        return self.running

@pytest.fixture
def concrete_queue():
    """Concrete queue instance for testing."""
    return ConcreteEventQueue()

@pytest.fixture
def test_event():
    """Test event."""
    return {
        "type": "test_event",
        "id": "test_001",
        "data": {"key": "value"}
    }

def test_queue_is_abstract():
    """Test that EventQueue is abstract."""
    assert EventQueue.__abstractmethods__ == {
        'enqueue', 'dequeue', 'cleanup', 'get_queue_size', 'is_running'
    }
    
    # Cannot instantiate abstract class
    with pytest.raises(TypeError):
        EventQueue()

@pytest.mark.asyncio
async def test_concrete_implementation(concrete_queue, test_event):
    """Test concrete implementation of EventQueue."""
    # Test initial state
    assert concrete_queue.is_running() is True
    assert concrete_queue.get_queue_size() == 0
    
    # Test enqueue
    success = await concrete_queue.enqueue(test_event)
    assert success is True
    assert concrete_queue.get_queue_size() == 1
    
    # Test dequeue
    event = await concrete_queue.dequeue()
    assert event == test_event
    assert concrete_queue.get_queue_size() == 0
    
    # Test cleanup
    await concrete_queue.cleanup()
    assert concrete_queue.is_running() is False
    assert concrete_queue.get_queue_size() == 0

@pytest.mark.asyncio
async def test_queue_after_cleanup(concrete_queue, test_event):
    """Test queue behavior after cleanup."""
    await concrete_queue.cleanup()
    
    # Cannot enqueue after cleanup
    success = await concrete_queue.enqueue(test_event)
    assert success is False
    
    # Cannot dequeue after cleanup
    event = await concrete_queue.dequeue()
    assert event is None

@pytest.mark.asyncio
async def test_dequeue_empty_queue(concrete_queue):
    """Test dequeue from empty queue."""
    event = await concrete_queue.dequeue()
    assert event is None

@pytest.mark.asyncio
async def test_multiple_events(concrete_queue):
    """Test multiple events in queue."""
    events = [
        {"type": "event1", "id": "1"},
        {"type": "event2", "id": "2"},
        {"type": "event3", "id": "3"}
    ]
    
    # Enqueue multiple events
    for event in events:
        success = await concrete_queue.enqueue(event)
        assert success is True
        
    assert concrete_queue.get_queue_size() == 3
    
    # Dequeue events in FIFO order
    for expected_event in events:
        event = await concrete_queue.dequeue()
        assert event == expected_event
        
    assert concrete_queue.get_queue_size() == 0 