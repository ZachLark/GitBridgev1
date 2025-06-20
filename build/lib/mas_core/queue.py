"""
Queue interface for GitBridge MAS Lite implementation.

This module provides the base queue interface that all queue implementations
must follow according to MAS Lite Protocol v2.1 requirements.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class EventQueue(ABC):
    """Abstract base class for event queues."""
    
    @abstractmethod
    async def enqueue(self, event: Dict[str, Any]) -> bool:
        """Enqueue an event.
        
        Args:
            event: Event to enqueue
            
        Returns:
            bool: True if event enqueued successfully
        """
        pass
        
    @abstractmethod
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """Dequeue an event.
        
        Returns:
            Optional[Dict[str, Any]]: Event if available, None otherwise
        """
        pass
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up queue resources."""
        pass
        
    @abstractmethod
    def get_queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            int: Current queue size
        """
        pass
        
    @abstractmethod
    def is_running(self) -> bool:
        """Check if queue is running.
        
        Returns:
            bool: True if queue is running
        """
        pass 