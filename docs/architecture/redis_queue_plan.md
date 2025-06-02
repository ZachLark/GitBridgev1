# GitBridge GBP13 Redis Queue Integration Plan

## Overview

This document outlines the plan for integrating Redis as the queue backend for GitBridge's event processing system, replacing the current `asyncio.Queue` implementation in `event_queue.py`.

## 1. Dependencies

```python
# requirements.txt additions
aioredis==2.0.1
redis==5.0.1
```

## 2. Architecture Changes

### 2.1 Redis Queue Implementation

```python
from aioredis import Redis
from typing import Optional, Dict, Any

class RedisEventQueue:
    """Redis-backed event queue implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Redis queue."""
        self.redis = Redis.from_url(
            config["queue"]["redis_url"],
            encoding="utf-8",
            decode_responses=True
        )
        self.queue_key = "gitbridge:events"
        self.processing_key = "gitbridge:processing"
        self.max_size = config["queue"]["max_size"]
        self.timeout = config["queue"]["timeout"]
        
    async def enqueue(self, payload: Dict[str, Any]) -> bool:
        """Enqueue webhook payload to Redis."""
        if await self.redis.llen(self.queue_key) >= self.max_size:
            return False
            
        await self.redis.lpush(
            self.queue_key,
            json.dumps(payload)
        )
        return True
        
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """Dequeue and process webhook payload from Redis."""
        try:
            # Atomic move from queue to processing
            payload = await self.redis.brpoplpush(
                self.queue_key,
                self.processing_key,
                timeout=self.timeout
            )
            if not payload:
                return None
                
            return json.loads(payload)
            
        except Exception as e:
            logger.error(f"Redis dequeue error: {str(e)}")
            return None
```

### 2.2 Factory Pattern Integration

```python
class QueueFactory:
    """Queue implementation factory."""
    
    @staticmethod
    def create_queue(config: Dict[str, Any]) -> Union[EventQueue, RedisEventQueue]:
        """Create queue instance based on configuration."""
        queue_type = config["queue"]["type"]
        if queue_type == "redis":
            return RedisEventQueue(config)
        return EventQueue(config)  # Default asyncio implementation
```

## 3. Configuration Updates

```yaml
# webhook_config.yaml
queue:
  type: "redis"  # or "asyncio" for backward compatibility
  redis_url: "redis://localhost:6379/0"
  max_size: 10000
  timeout: 30
  retry_policy:
    max_retries: 3
    base_delay: 1
```

## 4. Migration Strategy

### 4.1 Phase 1: Development
1. Implement `RedisEventQueue` class
2. Add unit tests
3. Update configuration
4. Add Redis health checks

### 4.2 Phase 2: Testing
1. Run integration tests
2. Benchmark performance
3. Test failure scenarios
4. Validate metrics

### 4.3 Phase 3: Deployment
1. Deploy Redis instance
2. Update configuration
3. Monitor performance
4. Enable gradual rollout

## 5. Testing Plan

### 5.1 Unit Tests
```python
# tests/unit/mas_core/test_redis_queue.py

import pytest
from mas_core.queue import RedisEventQueue

@pytest.mark.asyncio
async def test_redis_enqueue():
    queue = RedisEventQueue(config)
    payload = {"event_type": "push", "repo": "test/repo"}
    
    success = await queue.enqueue(payload)
    assert success
    assert await queue.get_queue_depth() == 1

@pytest.mark.asyncio
async def test_redis_dequeue():
    queue = RedisEventQueue(config)
    payload = {"event_type": "push", "repo": "test/repo"}
    
    await queue.enqueue(payload)
    result = await queue.dequeue()
    
    assert result == payload
    assert await queue.get_queue_depth() == 0
```

### 5.2 Integration Tests
```python
@pytest.mark.integration
async def test_redis_queue_flow():
    queue = RedisEventQueue(config)
    task_chain = TaskChain(consensus_manager, mas_logger, config)
    
    # Test end-to-end flow
    payload = create_test_payload()
    await queue.enqueue(payload)
    
    result = await queue.dequeue()
    task = await task_chain.create_task(
        task_id=generate_task_id(),
        agent=result["user"]
    )
    
    assert task.state == TaskState.CREATED
```

## 6. Performance Targets

### 6.1 Latency Goals
- Queue operations: <5ms
- End-to-end flow: <300ms
- Target improvement: 15-20%

### 6.2 Resource Usage
- Memory: <256MB per Redis instance
- CPU: <10% average load
- Network: <5MB/s peak throughput

## 7. Monitoring

### 7.1 Redis Metrics
```yaml
metrics:
  - name: redis_queue_depth
    type: gauge
    threshold: 1000
    
  - name: redis_operation_latency
    type: histogram
    buckets: [1, 2, 5, 10, 20, 50]
    
  - name: redis_error_rate
    type: counter
    alert_threshold: 1%
```

### 7.2 Health Checks
```python
async def check_redis_health():
    """Check Redis connection and queue health."""
    try:
        await redis.ping()
        depth = await redis.llen("gitbridge:events")
        processing = await redis.llen("gitbridge:processing")
        
        return {
            "status": "healthy",
            "queue_depth": depth,
            "processing": processing
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 8. Rollback Plan

### 8.1 Automatic Fallback
```python
class ResilientQueue:
    """Queue with automatic fallback to asyncio."""
    
    def __init__(self, config):
        self.redis_queue = RedisEventQueue(config)
        self.async_queue = EventQueue(config)
        
    async def enqueue(self, payload):
        try:
            return await self.redis_queue.enqueue(payload)
        except Exception:
            logger.warning("Falling back to asyncio queue")
            return await self.async_queue.enqueue(payload)
```

### 8.2 Manual Rollback
1. Update configuration to use `asyncio` queue
2. Drain Redis queue
3. Process remaining items
4. Switch to asyncio implementation

## 9. Timeline

### Week 1 (June 3-7)
- Implement Redis queue
- Write unit tests
- Update configuration

### Week 2 (June 10-14)
- Integration testing
- Performance testing
- Documentation updates

### Week 3 (June 17-21)
- Staging deployment
- Monitoring setup
- Performance tuning

### Week 4 (June 24-28)
- Production deployment
- Performance validation
- Final documentation

## 10. Success Criteria

1. Latency improvement: 15-20%
2. Zero data loss during migration
3. Successful failover testing
4. All tests passing
5. Documentation complete
6. Monitoring operational 