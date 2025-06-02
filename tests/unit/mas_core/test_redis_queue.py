"""
Unit tests for Redis queue implementation.
Tests Redis-backed event queue functionality.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from mas_core.queue import RedisEventQueue, QueueFactory

@pytest.fixture
def config():
    """Test configuration fixture."""
    return {
        "queue": {
            "type": "redis",
            "redis_url": "redis://localhost:6379/0",
            "max_size": 100,
            "timeout": 5,
            "retry_policy": {
                "max_retries": 2,
                "base_delay": 0.1
            }
        }
    }

@pytest.fixture
def mock_redis():
    """Mock Redis client fixture."""
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    redis.llen = AsyncMock(return_value=0)
    redis.lpush = AsyncMock(return_value=True)
    redis.brpoplpush = AsyncMock(return_value=None)
    return redis

@pytest.fixture
async def redis_queue(config, mock_redis):
    """RedisEventQueue instance fixture."""
    with patch("aioredis.Redis.from_url", return_value=mock_redis):
        queue = RedisEventQueue(config)
        yield queue

@pytest.mark.asyncio
async def test_redis_queue_init(redis_queue):
    """Test queue initialization."""
    assert redis_queue.queue_key == "gitbridge:events"
    assert redis_queue.processing_key == "gitbridge:processing"
    assert redis_queue.max_size == 100
    assert redis_queue.timeout == 5

@pytest.mark.asyncio
async def test_redis_enqueue_success(redis_queue, mock_redis):
    """Test successful payload enqueue."""
    payload = {
        "event_type": "push",
        "repo": "test/repo",
        "user": "test_user"
    }
    
    success = await redis_queue.enqueue(payload)
    assert success
    
    mock_redis.lpush.assert_called_once_with(
        "gitbridge:events",
        json.dumps(payload)
    )

@pytest.mark.asyncio
async def test_redis_enqueue_queue_full(redis_queue, mock_redis):
    """Test enqueue when queue is full."""
    mock_redis.llen.return_value = 100
    
    success = await redis_queue.enqueue({"event_type": "push"})
    assert not success
    mock_redis.lpush.assert_not_called()

@pytest.mark.asyncio
async def test_redis_dequeue_success(redis_queue, mock_redis):
    """Test successful payload dequeue."""
    payload = {
        "event_type": "push",
        "repo": "test/repo"
    }
    mock_redis.brpoplpush.return_value = json.dumps(payload)
    
    result = await redis_queue.dequeue()
    assert result == payload
    
    mock_redis.brpoplpush.assert_called_once_with(
        "gitbridge:events",
        "gitbridge:processing",
        timeout=5
    )

@pytest.mark.asyncio
async def test_redis_dequeue_timeout(redis_queue, mock_redis):
    """Test dequeue timeout."""
    mock_redis.brpoplpush.return_value = None
    
    result = await redis_queue.dequeue()
    assert result is None

@pytest.mark.asyncio
async def test_redis_dequeue_error(redis_queue, mock_redis):
    """Test dequeue error handling."""
    mock_redis.brpoplpush.side_effect = Exception("Redis error")
    
    result = await redis_queue.dequeue()
    assert result is None

@pytest.mark.asyncio
async def test_queue_factory_redis(config):
    """Test queue factory creates Redis queue."""
    with patch("aioredis.Redis.from_url"):
        queue = QueueFactory.create_queue(config)
        assert isinstance(queue, RedisEventQueue)

@pytest.mark.asyncio
async def test_queue_factory_asyncio(config):
    """Test queue factory creates asyncio queue."""
    config["queue"]["type"] = "asyncio"
    queue = QueueFactory.create_queue(config)
    assert isinstance(queue, EventQueue)

@pytest.mark.asyncio
async def test_redis_health_check(redis_queue, mock_redis):
    """Test Redis health check."""
    mock_redis.llen.side_effect = [5, 2]  # queue_depth, processing
    
    health = await redis_queue.check_health()
    assert health["status"] == "healthy"
    assert health["queue_depth"] == 5
    assert health["processing"] == 2

@pytest.mark.asyncio
async def test_redis_health_check_unhealthy(redis_queue, mock_redis):
    """Test Redis health check when unhealthy."""
    mock_redis.ping.side_effect = Exception("Connection error")
    
    health = await redis_queue.check_health()
    assert health["status"] == "unhealthy"
    assert "error" in health 