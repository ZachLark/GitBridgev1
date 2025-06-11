"""
Task chain management for GitBridge MAS Lite implementation.

This module provides task chain management functionality for GitBridge's event processing
system, following MAS Lite Protocol v2.1 task chain requirements.

MAS Lite Protocol v2.1 References:
- Section 3.2: Task Chain Requirements
- Section 3.3: State Transitions
- Section 3.4: Error Handling
"""

import asyncio
import logging
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from .consensus import ConsensusManager, ConsensusState, ConsensusTimeoutError
from .metrics import MetricsCollector
from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from .utils.logging import MASLogger
from dataclasses import dataclass

logger = MASLogger(__name__)
metrics_collector = MetricsCollector()

class TaskState(str, Enum):
    """Task states."""
    Created = "Created"
    InProgress = "InProgress"
    Blocked = "Blocked"
    Resolved = "Resolved"
    Failed = "Failed"

class TaskSource(str, Enum):
    """Task sources."""
    Manual = "manual"
    Webhook = "webhook"
    Scheduler = "scheduler"
    Pipeline = "pipeline"
    System = "system"

class TaskError(Exception):
    """Base class for task-related errors."""
    pass

class TaskNotFoundError(TaskError):
    """Error raised when task is not found."""
    pass

class InvalidStateTransitionError(TaskError):
    """Error raised for invalid state transitions."""
    pass

class ConcurrentTaskLimitError(TaskError):
    """Error raised when concurrent task limit is exceeded."""
    pass

@dataclass
class TaskMetadata:
    """Task metadata."""
    created_by: str
    assigned_to: Optional[str] = None
    priority: str = "medium"
    tags: List[str] = None
    source: TaskSource = TaskSource.Manual
    
    def __post_init__(self):
        """Initialize mutable fields."""
        if self.tags is None:
            self.tags = []

@dataclass
class Task:
    """Task data structure."""
    task_id: str
    state: TaskState
    data: Dict[str, Any]
    created_at: str
    updated_at: str
    metadata: TaskMetadata
    error: Optional[Dict[str, Any]] = None

class TaskChainManager:
    """Task chain manager."""
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        TaskState.Created: {TaskState.InProgress},
        TaskState.InProgress: {TaskState.Blocked, TaskState.Resolved, TaskState.Failed},
        TaskState.Blocked: {TaskState.InProgress},
        TaskState.Resolved: set(),  # Terminal state
        TaskState.Failed: set()     # Terminal state
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize task chain.
        
        Args:
            config: Configuration dictionary containing task chain settings
                   Required keys:
                   - task_chain.states: List of valid states
                   - task_chain.max_concurrent: Maximum concurrent tasks
                   - task_chain.consensus_required: Whether consensus is required
        """
        self.states = [TaskState(state) for state in config["task_chain"]["states"]]
        self.max_concurrent = config["task_chain"]["max_concurrent"]
        self.consensus_required = config["task_chain"]["consensus_required"]
        self.tasks: Dict[str, Task] = {}
        self.consensus_manager = ConsensusManager(config)
        self.error_handler = ErrorHandler()
        
    def _get_active_tasks(self) -> List[Task]:
        """Get list of active tasks (not in terminal states)."""
        return [task for task in self.tasks.values() if task.state not in [TaskState.Resolved, TaskState.Failed]]
        
    def _get_current_time(self) -> str:
        """Get current time in ISO format."""
        return datetime.now(timezone.utc).isoformat()
        
    def _is_valid_transition(self, current_state: TaskState, target_state: TaskState) -> bool:
        """Check if state transition is valid.
        
        Args:
            current_state: Current task state
            target_state: Target task state
            
        Returns:
            bool: True if transition is valid
        """
        return target_state in self.VALID_TRANSITIONS[current_state]
        
    @metrics_collector.track_task_timing
    async def create_task(self, task_id: str, data: Dict[str, Any], metadata: Optional[TaskMetadata] = None) -> bool:
        """Create a new task.
        
        Args:
            task_id: Unique task identifier
            data: Task data
            metadata: Optional task metadata
            
        Returns:
            bool: True if task created successfully
            
        Raises:
            ConcurrentTaskLimitError: If max concurrent tasks exceeded
            ValueError: If task data is invalid
        """
        try:
            if not task_id or not data:
                raise ValueError("Task ID and data are required")
                
            active_tasks = self._get_active_tasks()
            if len(active_tasks) >= self.max_concurrent:
                raise ConcurrentTaskLimitError("Maximum concurrent tasks exceeded")
                
            current_time = self._get_current_time()
            
            # Create default metadata if not provided
            if metadata is None:
                metadata = TaskMetadata(created_by="system", source=TaskSource.System)
                
            self.tasks[task_id] = Task(
                task_id=task_id,
                state=TaskState.Created,
                data=data,
                created_at=current_time,
                updated_at=current_time,
                metadata=metadata
            )
            
            logger.info(f"Created task {task_id}", extra={"task_id": task_id})
            return True
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to create task: {str(e)}",
                details={
                    "task_id": task_id,
                    "error": str(e)
                }
            )
            if isinstance(e, (ConcurrentTaskLimitError, ValueError)):
                raise
            return False
            
    async def update_task_state(self, task_id: str, target_state: TaskState) -> bool:
        """Update task state.
        
        Args:
            task_id: Task identifier
            target_state: Target state
            
        Returns:
            bool: True if state updated successfully
            
        Raises:
            TaskNotFoundError: If task not found
            InvalidStateTransitionError: If state transition invalid
        """
        try:
            if task_id not in self.tasks:
                raise TaskNotFoundError(f"Task {task_id} not found")
                
            task = self.tasks[task_id]
            
            # Validate state transition
            if not self._is_valid_transition(task.state, target_state):
                raise InvalidStateTransitionError(
                    f"Invalid state transition: {task.state} -> {target_state}"
                )
            
            # Check if consensus required for this transition
            if self.consensus_required and target_state == TaskState.Resolved:
                try:
                    async with asyncio.timeout(self.consensus_manager.timeout):
                        consensus = await self.consensus_manager.get_consensus(task_id)
                        if consensus.state != ConsensusState.Approved:
                            logger.warning(
                                f"Consensus not reached for task {task_id}",
                                extra={"task_id": task_id, "consensus_state": consensus.state}
                            )
                            return False
                except asyncio.TimeoutError:
                    error_id = str(uuid.uuid4())
                    self.error_handler.handle_error(
                        error_id=error_id,
                        category=ErrorCategory.CONSENSUS,
                        severity=ErrorSeverity.ERROR,
                        message=f"Consensus timeout for task {task_id}",
                        details={"task_id": task_id}
                    )
                    return False
                except ConsensusTimeoutError as e:
                    error_id = str(uuid.uuid4())
                    self.error_handler.handle_error(
                        error_id=error_id,
                        category=ErrorCategory.CONSENSUS,
                        severity=ErrorSeverity.ERROR,
                        message=str(e),
                        details={"task_id": task_id}
                    )
                    return False
                
            # Update task state
            task.state = target_state
            task.updated_at = self._get_current_time()
            
            logger.info(
                f"Updated task {task_id} state to {target_state}",
                extra={"task_id": task_id, "state": target_state}
            )
            return True
            
        except (TaskNotFoundError, InvalidStateTransitionError) as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.ERROR,
                message=str(e),
                details={"task_id": task_id}
            )
            raise
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to update task state: {str(e)}",
                details={
                    "task_id": task_id,
                    "target_state": target_state,
                    "error": str(e)
                }
            )
            return False
            
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task if found, None otherwise
        """
        return self.tasks.get(task_id)
        
    async def list_tasks(self, state: Optional[TaskState] = None) -> List[Task]:
        """List tasks, optionally filtered by state.
        
        Args:
            state: Optional state to filter by
            
        Returns:
            List of tasks
        """
        if state:
            return [task for task in self.tasks.values() if task.state == state]
        return list(self.tasks.values())
        
    async def cleanup(self) -> None:
        """Clean up completed tasks."""
        try:
            # Remove completed tasks
            completed_task_ids = [
                task_id for task_id, task in self.tasks.items()
                if task.state in [TaskState.Resolved, TaskState.Failed]
            ]
            
            for task_id in completed_task_ids:
                del self.tasks[task_id]
            
            # Clean up consensus manager
            await self.consensus_manager.cleanup()
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to clean up task chain: {str(e)}",
                details={"error": str(e)}
            ) 