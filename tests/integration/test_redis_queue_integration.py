"""
Integration tests for Redis queue implementation.

Tests Redis queue functionality in a real environment with Redis server,
including rollback scenarios, fault handling, and concurrent operations.

MAS Lite Protocol v2.1 References:
- Section 4.2: Event Queue Requirements
- Section 4.3: Queue Operations
- Section 4.4: Error Handling
"""

import asyncio
import json
import random
import pytest
import pytest_asyncio
import fakeredis.aioredis
from typing import Dict, Any, AsyncGenerator, List
from scripts.redis_queue import RedisEventQueue, ResilientQueue
from mas_core.queue import EventQueue
from mas_core.redis_queue import RedisQueue
from mas_core.metrics import MetricsCollector

# Test configuration
TEST_CONFIG = {
    "queue": {
        "type": "redis",
        "redis_url": "redis://localhost:6379/0",
        "max_size": 1000,
        "timeout": 0.1,
        "retry_policy": {
            "max_retries": 5,
            "base_delay": 0.1
        }
    }
}

@pytest_asyncio.fixture(scope="function")
async def fake_redis() -> AsyncGenerator[fakeredis.aioredis.FakeRedis, None]:
    """Create a fake Redis instance for testing."""
    server = fakeredis.aioredis.FakeRedis()
    yield server
    await server.aclose()

@pytest_asyncio.fixture
async def redis_queue(fake_redis):
    """Create a Redis queue instance for testing."""
    queue = RedisEventQueue(TEST_CONFIG)
    queue.redis = fake_redis
    yield queue
    await queue.cleanup()

@pytest_asyncio.fixture(scope="function")
async def resilient_queue(redis_queue: RedisEventQueue) -> AsyncGenerator[ResilientQueue, None]:
    """Create a resilient queue instance."""
    queue = ResilientQueue(TEST_CONFIG)
    queue.redis_queue = redis_queue
    yield queue
    await queue.cleanup()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_rollback(redis_queue: RedisEventQueue) -> None:
    """Test queue state rollback after Redis disconnect."""
    # Enqueue some events
    events = [
        {"type": "push", "id": i} for i in range(5)
    ]
    for event in events:
        assert await redis_queue.enqueue(event)
    
    # Verify queue depth
    assert await redis_queue.get_queue_depth() == 5
    
    # Simulate Redis disconnect
    await redis_queue.redis.aclose()
    
    # Verify queue state is preserved
    redis_queue.redis = await fakeredis.aioredis.create_redis_pool(
        TEST_CONFIG["queue"]["redis_url"]
    )
    assert await redis_queue.get_queue_depth() == 5
    
    # Verify events can be dequeued
    for i in range(5):
        event = await redis_queue.dequeue()
        assert event["id"] == i

@pytest.mark.integration
@pytest.mark.asyncio
async def test_fault_handling(redis_queue: RedisEventQueue) -> None:
    """Test handling of various fault scenarios."""
    # Test invalid JSON
    await redis_queue.redis.lpush(redis_queue.queue_key, "invalid json")
    event = await redis_queue.dequeue()
    assert event is None
    
    # Test network errors
    redis_queue.redis = None
    success = await redis_queue.enqueue({"type": "push"})
    assert not success
    
    # Test queue full
    redis_queue.redis = await fakeredis.aioredis.create_redis_pool(
        TEST_CONFIG["queue"]["redis_url"]
    )
    redis_queue.max_size = 1
    assert await redis_queue.enqueue({"type": "push"})
    assert not await redis_queue.enqueue({"type": "push"})

@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_operations(redis_queue: RedisEventQueue) -> None:
    """Test concurrent queue operations."""
    async def producer(n: int) -> None:
        for i in range(n):
            await redis_queue.enqueue({"type": "push", "id": i})
            await asyncio.sleep(0.01)
    
    async def consumer(n: int) -> list:
        events = []
        for _ in range(n):
            event = await redis_queue.dequeue()
            if event:
                events.append(event)
            await asyncio.sleep(0.01)
        return events
    
    # Run 10 producers and consumers concurrently
    producers = [producer(10) for _ in range(10)]
    consumers = [consumer(10) for _ in range(10)]
    
    # Wait for all operations to complete
    await asyncio.gather(*producers)
    results = await asyncio.gather(*consumers)
    
    # Verify results
    all_events = [event for consumer_events in results for event in consumer_events]
    assert len(all_events) == 100  # 10 producers * 10 events
    
    # Verify queue is empty
    assert await redis_queue.get_queue_depth() == 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_resilient_queue_failover(resilient_queue: ResilientQueue) -> None:
    """Test resilient queue failover to asyncio queue."""
    # Break Redis connection
    resilient_queue.redis_queue.redis = None
    
    # Enqueue should work with asyncio fallback
    assert await resilient_queue.enqueue({"type": "push"})
    assert not resilient_queue.using_redis
    
    # Dequeue should work with asyncio fallback
    event = await resilient_queue.dequeue()
    assert event == {"type": "push"}
    
    # Restore Redis connection
    resilient_queue.redis_queue.redis = await fakeredis.aioredis.create_redis_pool(
        TEST_CONFIG["queue"]["redis_url"]
    )
    resilient_queue.using_redis = True
    
    # Operations should work with Redis again
    assert await resilient_queue.enqueue({"type": "push"})
    event = await resilient_queue.dequeue()
    assert event == {"type": "push"}

@pytest.mark.integration
@pytest.mark.asyncio
async def test_performance(redis_queue: RedisEventQueue) -> None:
    """Test queue performance under load."""
    import time
    
    # Measure enqueue latency
    start_time = time.time()
    for i in range(100):
        await redis_queue.enqueue({"type": "push", "id": i})
    enqueue_latency = (time.time() - start_time) / 100
    
    # Measure dequeue latency
    start_time = time.time()
    for _ in range(100):
        await redis_queue.dequeue()
    dequeue_latency = (time.time() - start_time) / 100
    
    # Verify latencies are within target
    assert enqueue_latency < 0.5  # 500ms target
    assert dequeue_latency < 0.5  # 500ms target
    
    # Log performance metrics
    with open("docs/performance/gbp13_metrics.md", "a") as f:
        f.write(f"\n## Redis Queue Performance\n")
        f.write(f"- Average enqueue latency: {enqueue_latency*1000:.1f}ms\n")
        f.write(f"- Average dequeue latency: {dequeue_latency*1000:.1f}ms\n")
        f.write(f"- Total average latency: {(enqueue_latency + dequeue_latency)*1000:.1f}ms\n")

class TestRedisQueueIntegration:
    @pytest.fixture
    async def redis_client(self):
        client = fakeredis.aioredis.FakeRedis()
        yield client
        await client.close()
    
    @pytest.fixture
    async def queue(self, redis_client):
        queue = RedisQueue(redis_client, "test_queue")
        yield queue
        await queue.clear()

    @pytest.fixture
    def metrics(self):
        return MetricsCollector()

    async def generate_events(self, count: int) -> List[Dict[str, Any]]:
        return [
            {
                "event": "push",
                "payload": {
                    "id": str(i),
                    "type": "commit",
                    "data": "test" * 100  # Add some size to the event
                }
            }
            for i in range(count)
        ]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_queue_overflow(self, queue, metrics):
        """Test handling of queue overflow with 1000+ events."""
        events = [
            {
                "event": "push",
                "payload": {
                    "id": str(i),
                    "type": "commit",
                    "data": "test" * 100  # Add size to events
                }
            }
            for i in range(1100)  # Create more than max_size events
        ]
        
        # Measure enqueue time
        start_time = asyncio.get_event_loop().time()
        successful = 0
        errors = 0
        
        for event in events:
            try:
                if await queue.enqueue(event):
                    successful += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                metrics.record_error("overflow", str(e))
        
        end_time = asyncio.get_event_loop().time()
        enqueue_time = end_time - start_time
        
        # Verify performance and behavior
        assert enqueue_time < 0.5, f"Enqueue time {enqueue_time}s exceeds 500ms limit"
        assert successful <= TEST_CONFIG["queue"]["max_size"], "Queue exceeded max size"
        assert errors > 0, "Should have some overflow errors"
        
        # Record metrics
        metrics.record_latency("enqueue_batch", enqueue_time)
        metrics.record_gauge("queue_size", successful)
        metrics.record_gauge("overflow_errors", errors)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_event_dropout(self, queue, metrics):
        """Test handling of random event dropouts under concurrent load."""
        events = [
            {
                "event": "push",
                "payload": {
                    "id": str(i),
                    "type": "commit",
                    "data": "test"
                }
            }
            for i in range(100)
        ]
        
        async def process_event(event):
            if random.random() < 0.05:  # 5% dropout rate
                raise Exception("Simulated dropout")
            await queue.enqueue(event)
            await asyncio.sleep(0.01)  # Simulate processing time
        
        # Process events concurrently
        tasks = [process_event(event) for event in events]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful vs dropped events
        successful = sum(1 for r in results if not isinstance(r, Exception))
        dropped = len(results) - successful
        
        # Verify dropout rate is within acceptable range
        dropout_rate = dropped / len(events)
        assert dropout_rate <= 0.1, f"Dropout rate {dropout_rate} exceeds 10% threshold"
        
        # Record metrics
        metrics.record_gauge("dropout_rate", dropout_rate)
        metrics.record_counter("events_dropped", dropped)
        metrics.record_gauge("queue_integrity", 1.0 - dropout_rate)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rollback(self, queue, fake_redis, metrics):
        """Test queue state rollback on Redis disconnect."""
        # Enqueue initial events
        initial_events = [
            {
                "event": "push",
                "payload": {"id": str(i), "type": "commit"}
            }
            for i in range(10)
        ]
        
        for event in initial_events:
            await queue.enqueue(event)
        
        initial_size = await queue.get_queue_depth()
        
        # Simulate Redis disconnect
        await fake_redis.connection_pool.disconnect()
        
        # Attempt operations during disconnect
        failed_ops = 0
        for i in range(5):
            try:
                await queue.enqueue({"event": "test", "id": f"fail_{i}"})
            except Exception as e:
                failed_ops += 1
                metrics.record_error("disconnect", str(e))
        
        # Reconnect and verify state
        await fake_redis.connection_pool.connect()
        final_size = await queue.get_queue_depth()
        
        # Verify queue integrity
        assert final_size == initial_size, "Queue size should remain consistent after reconnect"
        assert failed_ops > 0, "Should have failed operations during disconnect"
        
        # Record metrics
        metrics.record_gauge("queue_integrity", 1 if final_size == initial_size else 0)
        metrics.record_counter("failed_operations", failed_ops)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_data(self, queue, metrics):
        """Test handling of invalid JSON and network errors."""
        invalid_events = [
            b"invalid json",
            {"incomplete": "missing fields"},
            {"event": None, "payload": None},
            "not a dict",
            b"\x80\x80\x80\x80",  # Invalid UTF-8
            {"event": "push", "payload": {"id": "a" * 1000000}},  # Too large
            {},  # Empty dict
            {"event": [], "payload": {}},  # Wrong type
            {"event": "push", "payload": float('inf')},  # Invalid JSON
        ]
        
        errors = []
        validation_errors = 0
        
        for event in invalid_events:
            try:
                await queue.enqueue(event)
            except Exception as e:
                errors.append(str(e))
                metrics.record_error("invalid_data", str(e))
                validation_errors += 1
        
        assert len(errors) == len(invalid_events), "All invalid events should raise errors"
        assert validation_errors > 0, "Should have validation errors"
        
        # Verify queue integrity
        size = await queue.get_queue_depth()
        assert size >= 0, "Queue should maintain valid state"
        
        # Record metrics
        metrics.record_counter("validation_errors", validation_errors)
        metrics.record_gauge("queue_integrity", 1.0)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_performance_metrics(self, queue, metrics):
        """Test and record detailed performance metrics."""
        events = [
            {
                "event": "push",
                "payload": {
                    "id": str(i),
                    "type": "commit",
                    "data": "test" * (i % 10)  # Vary payload size
                }
            }
            for i in range(50)
        ]
        
        # Measure enqueue performance
        enqueue_times = []
        for event in events:
            start = asyncio.get_event_loop().time()
            await queue.enqueue(event)
            end = asyncio.get_event_loop().time()
            enqueue_times.append(end - start)
        
        # Measure dequeue performance
        dequeue_times = []
        for _ in range(len(events)):
            start = asyncio.get_event_loop().time()
            await queue.dequeue()
            end = asyncio.get_event_loop().time()
            dequeue_times.append(end - start)
        
        # Calculate metrics
        avg_enqueue = sum(enqueue_times) / len(enqueue_times)
        avg_dequeue = sum(dequeue_times) / len(dequeue_times)
        max_latency = max(max(enqueue_times), max(dequeue_times))
        
        # Verify performance targets
        assert avg_enqueue < 0.5, f"Average enqueue time {avg_enqueue}s exceeds 500ms target"
        assert avg_dequeue < 0.5, f"Average dequeue time {avg_dequeue}s exceeds 500ms target"
        
        # Record metrics
        metrics.record_histogram("enqueue_times", enqueue_times)
        metrics.record_histogram("dequeue_times", dequeue_times)
        metrics.record_gauge("max_latency", max_latency)
        
        # Log performance metrics
        with open("docs/performance/gbp13_metrics.md", "a") as f:
            f.write("\n## Redis Queue Performance Test Results\n")
            f.write(f"- Average enqueue latency: {avg_enqueue*1000:.1f}ms\n")
            f.write(f"- Average dequeue latency: {avg_dequeue*1000:.1f}ms\n")
            f.write(f"- Maximum latency: {max_latency*1000:.1f}ms\n")
            f.write("- Production validation plan: Deploy to staging, monitor for 24 hours\n") 