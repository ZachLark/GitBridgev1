"""
Event queue management for GitBridge MAS Lite implementation.

This module provides event queue management functionality for GitBridge's event processing
system, following MAS Lite Protocol v2.1 event queue requirements.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from .utils.logging import MASLogger

logger = MASLogger(__name__)

class QueueError(Exception):
    """Base class for queue-related errors."""
    pass

class QueueTimeoutError(QueueError):
    """Error raised when queue operation times out."""
    pass

class QueueFullError(QueueError):
    """Error raised when queue is full."""
    pass

class EventQueue:
    """Event queue."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize event queue.

        Args:
            config: Configuration dictionary containing queue settings
                   Required keys:
                   - queue.max_size: Maximum queue size
                   - queue.timeout: Operation timeout in seconds
        """
        self.max_size = config["queue"]["max_size"]
        self.timeout = config["queue"]["timeout"]
        self.queue = asyncio.Queue(maxsize=self.max_size)
        self.error_handler = ErrorHandler()
        self._running = True
        self._tasks = set()
        
    async def __aenter__(self):
        """Async context manager entry."""
        self._running = True
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self._running = False
        # Cancel any pending tasks
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
    async def enqueue(self, event: Dict[str, Any]) -> bool:
        """Enqueue an event.
        
        Args:
            event: Event to enqueue
            
        Returns:
            bool: True if event enqueued successfully
            
        Raises:
            QueueFullError: If queue is full
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
            # Try to enqueue with timeout
            async with asyncio.timeout(self.timeout):
                await self.queue.put(event)
                logger.info(
                    "Event enqueued",
                    extra={
                        "event_type": event.get("type"),
                        "queue_size": self.queue.qsize()
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
            
        except asyncio.QueueFull:
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
            
        Raises:
            QueueTimeoutError: If dequeue operation times out
        """
        if not self._running:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.ERROR,
                message="Queue is not running",
                details={"queue_size": self.queue.qsize()}
            )
            return None
            
        try:
            # Try to dequeue with timeout
            async with asyncio.timeout(self.timeout):
                event = await self.queue.get()
                self.queue.task_done()
                logger.info(
                    "Event dequeued",
                    extra={
                        "event_type": event.get("type"),
                        "queue_size": self.queue.qsize()
                    }
                )
                return event
                
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
            # Cancel any pending tasks
            for task in self._tasks:
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to clean up event queue: {str(e)}",
                details={"error": str(e)}
            )
            
    def get_queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            int: Current queue size
        """
        return self.queue.qsize()
        
    def is_running(self) -> bool:
        """Check if queue is running.
        
        Returns:
            bool: True if queue is running
        """
        return self._running
        
    async def get_queue_depth(self) -> int:
        """Get current queue depth.
        
        Returns:
            int: Current queue depth
        """
        return self.queue.qsize()
        
    async def check_health(self) -> Dict[str, Any]:
        """Check queue health.
        
        Returns:
            Dict[str, Any]: Health check result
        """
        try:
            queue_size = self.queue.qsize()
            return {
                "status": "healthy",
                "queue_size": queue_size,
                "running": self._running
            }
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to check queue health: {str(e)}",
                details={"error": str(e)}
            )
            return {
                "status": "unhealthy",
                "error": str(e)
            } 