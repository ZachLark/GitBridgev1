"""
Redis queue implementation for GitBridge MAS Lite.

This module provides a Redis-backed event queue implementation following
MAS Lite Protocol v2.1 queue requirements.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import redis.asyncio

from .queue import EventQueue
from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from .utils.logging import MASLogger

logger = MASLogger(__name__)

class RedisQueueError(Exception):
    """Base class for Redis queue errors."""
    pass

class RedisConnectionError(RedisQueueError):
    """Error raised when Redis connection fails."""
    pass

class RedisQueue(EventQueue):
    """Redis-backed event queue implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Redis queue.
        
        Args:
            config: Configuration dictionary containing Redis settings
                   Required keys:
                   - queue.redis_url: Redis connection URL
                   - queue.max_size: Maximum queue size
                   - queue.timeout: Operation timeout in seconds
        """
        self.redis_url = config["queue"]["redis_url"]
        self.max_size = config["queue"]["max_size"]
        self.timeout = config["queue"]["timeout"]
        self.queue_key = "gitbridge:events"
        self.processing_key = "gitbridge:processing"
        self.error_handler = ErrorHandler()
        self._running = True
        
        try:
            self.redis = redis.asyncio.from_url(self.redis_url)
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.CRITICAL,
                message=f"Failed to connect to Redis: {str(e)}",
                details={"error": str(e)}
            )
            raise RedisConnectionError(f"Failed to connect to Redis: {str(e)}")
            
    async def enqueue(self, event: Dict[str, Any]) -> bool:
        """Enqueue an event.
        
        Args:
            event: Event to enqueue
            
        Returns:
            bool: True if event enqueued successfully
        """
        if not self._running:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.ERROR,
                message="Queue is not running",
                details={"event": event}
            )
            return False
            
        try:
            # Check queue size
            size = await self.redis.llen(self.queue_key)
            if size >= self.max_size:
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.QUEUE,
                    severity=ErrorSeverity.WARNING,
                    message="Queue is full",
                    details={
                        "event": event,
                        "max_size": self.max_size
                    }
                )
                return False
                
            # Enqueue event
            async with asyncio.timeout(self.timeout):
                await self.redis.lpush(self.queue_key, json.dumps(event))
                logger.info(
                    "Event enqueued",
                    extra={
                        "event_type": event.get("type"),
                        "queue_size": size + 1
                    }
                )
                return True
                
        except asyncio.TimeoutError:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.WARNING,
                message="Enqueue operation timed out",
                details={
                    "event": event,
                    "timeout": self.timeout
                }
            )
            return False
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to enqueue event: {str(e)}",
                details={
                    "event": event,
                    "error": str(e)
                }
            )
            return False
            
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """Dequeue an event.
        
        Returns:
            Optional[Dict[str, Any]]: Event if available, None otherwise
        """
        if not self._running:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.ERROR,
                message="Queue is not running"
            )
            return None
            
        try:
            # Try to dequeue with timeout
            async with asyncio.timeout(self.timeout):
                # Use pipeline to ensure atomicity
                async with self.redis.pipeline() as pipe:
                    # Move event from queue to processing list
                    await pipe.brpop(self.queue_key, timeout=self.timeout)
                    await pipe.lpush(self.processing_key, "placeholder")
                    result = await pipe.execute()
                    
                if not result[0]:  # Timeout
                    # Remove placeholder from processing list
                    await self.redis.lpop(self.processing_key)
                    return None
                    
                # Parse event
                try:
                    _, event_json = result[0]
                    event = json.loads(event_json)
                    logger.info(
                        "Event dequeued",
                        extra={
                            "event_type": event.get("type"),
                            "queue_size": await self.redis.llen(self.queue_key)
                        }
                    )
                    return event
                except json.JSONDecodeError:
                    # Remove invalid event from processing list
                    await self.redis.lrem(self.processing_key, 1, event_json)
                    error_id = str(uuid.uuid4())
                    self.error_handler.handle_error(
                        error_id=error_id,
                        category=ErrorCategory.QUEUE,
                        severity=ErrorSeverity.ERROR,
                        message="Invalid JSON in queue",
                        details={"event_json": event_json}
                    )
                    return None
                    
        except asyncio.TimeoutError:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.WARNING,
                message="Dequeue operation timed out",
                details={"timeout": self.timeout}
            )
            return None
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to dequeue event: {str(e)}",
                details={"error": str(e)}
            )
            return None
            
    async def cleanup(self) -> None:
        """Clean up queue resources."""
        try:
            self._running = False
            # Clear queues
            await self.redis.delete(self.queue_key)
            await self.redis.delete(self.processing_key)
            # Close Redis connection
            await self.redis.close()
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to clean up queue: {str(e)}",
                details={"error": str(e)}
            )
            
    def get_queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            int: Current queue size
        """
        try:
            return self.redis.llen(self.queue_key)
        except Exception:
            return 0
            
    def is_running(self) -> bool:
        """Check if queue is running.
        
        Returns:
            bool: True if queue is running
        """
        return self._running 