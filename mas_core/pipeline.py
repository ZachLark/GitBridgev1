"""
MAS Pipeline implementation for GitBridge.

This module provides the main pipeline implementation for GitBridge's event processing
system, integrating event queue, task chain, and consensus management.

MAS Lite Protocol v2.1 References:
- Section 2.2: Pipeline Requirements
- Section 2.3: Event Processing
- Section 2.4: Error Handling
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from .event_queue import EventQueue
from .task_chain import TaskChainManager, TaskState, TaskNotFoundError, InvalidStateTransitionError, ConcurrentTaskLimitError
from .consensus import ConsensusManager
from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from .utils.logging import MASLogger
from .utils.validation import validate_task

logger = MASLogger(__name__)

class MASPipeline:
    """MAS pipeline implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize pipeline.
        
        Args:
            config: Configuration dictionary containing pipeline settings
                   Required keys:
                   - pipeline.max_retries: Maximum retry attempts
                   - pipeline.retry_delay: Delay between retries in seconds
                   - pipeline.cleanup_interval: Cleanup interval in seconds
        """
        self.max_retries = config["pipeline"]["max_retries"]
        self.retry_delay = config["pipeline"]["retry_delay"]
        self.cleanup_interval = config["pipeline"]["cleanup_interval"]
        self.event_queue = EventQueue(config)
        self.task_chain = TaskChainManager(config)
        self.error_handler = ErrorHandler()
        self._running = True
        
    async def start(self) -> None:
        """Start pipeline processing."""
        try:
            logger.info("Starting MAS pipeline")
            self._running = True
            
            # Start cleanup task
            asyncio.create_task(self._cleanup_loop())
            
            # Process events
            while self._running:
                try:
                    event = await self.event_queue.dequeue()
                    if event:
                        await self._process_event(event)
                    else:
                        # Prevent busy-wait when no events available
                        await asyncio.sleep(0.01)  # 10ms delay
                except Exception as e:
                    error_id = str(uuid.uuid4())
                    self.error_handler.handle_error(
                        error_id=error_id,
                        category=ErrorCategory.SYSTEM,
                        severity=ErrorSeverity.ERROR,
                        message=f"Failed to process event: {str(e)}",
                        details={"error": str(e)}
                    )
                    await asyncio.sleep(self.retry_delay)
                    
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"Pipeline error: {str(e)}",
                details={"error": str(e)}
            )
            raise
            
    async def stop(self) -> None:
        """Stop pipeline processing."""
        try:
            logger.info("Stopping MAS pipeline")
            self._running = False
            
            # Clean up resources
            await self.cleanup()
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to stop pipeline: {str(e)}",
                details={"error": str(e)}
            )
            
    async def process_event(self, event: Dict[str, Any]) -> None:
        """Process an event (public interface).
        
        Args:
            event: Event to process
        """
        await self._process_event(event)
            
    async def _process_event(self, event: Dict[str, Any]) -> None:
        """Process an event.
        
        Args:
            event: Event to process
        """
        try:
            # Basic event validation
            if not isinstance(event, dict) or not event.get("type"):
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.TASK,
                    severity=ErrorSeverity.ERROR,
                    message="Invalid event format",
                    details={"event": event}
                )
                return
                
            # Create task
            task_id = str(uuid.uuid4())
            success = await self.task_chain.create_task(task_id, event)
            
            if not success:
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.TASK,
                    severity=ErrorSeverity.ERROR,
                    message="Failed to create task",
                    details={
                        "task_id": task_id,
                        "event": event
                    }
                )
                return
                
            # Update task state
            success = await self.task_chain.update_task_state(task_id, TaskState.InProgress)
            
            if not success:
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.TASK,
                    severity=ErrorSeverity.ERROR,
                    message="Failed to update task state",
                    details={
                        "task_id": task_id,
                        "target_state": TaskState.InProgress
                    }
                )
                return
                
            logger.info(
                f"Processed event for task {task_id}",
                extra={
                    "task_id": task_id,
                    "event_type": event.get("type")
                }
            )
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to process event: {str(e)}",
                details={
                    "event": event,
                    "error": str(e)
                }
            )
            
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup task."""
        try:
            while self._running:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup()
                
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.ERROR,
                message=f"Cleanup loop error: {str(e)}",
                details={"error": str(e)}
            )
            
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Clean up event queue
            await self.event_queue.cleanup()
            
            # Clean up task chain
            await self.task_chain.cleanup()
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to clean up pipeline: {str(e)}",
                details={"error": str(e)}
            ) 