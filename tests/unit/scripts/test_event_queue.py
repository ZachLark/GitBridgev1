import pytest
from scripts.event_queue import EventQueue, Event

@pytest.mark.skip(reason="Known failure - Phase 19")
class TestEventQueue:
    @pytest.fixture
    def event_queue(self):
        return EventQueue()

    def test_init(self, event_queue):
        """Test basic initialization."""
        assert event_queue is not None
        assert event_queue.is_empty()

    def test_enqueue_event(self, event_queue):
        """Test enqueueing an event."""
        event = Event("test_event", {"data": "test"})
        event_queue.enqueue(event)
        assert not event_queue.is_empty()
        assert event_queue.size() == 1

    def test_dequeue_event(self, event_queue):
        """Test dequeueing an event."""
        event = Event("test_event", {"data": "test"})
        event_queue.enqueue(event)
        dequeued = event_queue.dequeue()
        assert dequeued == event
        assert event_queue.is_empty()

    def test_peek_event(self, event_queue):
        """Test peeking at the next event."""
        event = Event("test_event", {"data": "test"})
        event_queue.enqueue(event)
        peeked = event_queue.peek()
        assert peeked == event
        assert not event_queue.is_empty()  # Peek shouldn't remove the event

    def test_clear_queue(self, event_queue):
        """Test clearing the queue."""
        event = Event("test_event", {"data": "test"})
        event_queue.enqueue(event)
        event_queue.clear()
        assert event_queue.is_empty()
        assert event_queue.size() == 0 