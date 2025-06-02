"""
MAS Task Chain Module.

This module implements the task lifecycle management system for the MAS Lite Protocol v2.1,
handling task state transitions, dependencies, and integration with consensus and GitHub events.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import json
import hashlib
import asyncio
import logging
from pydantic import BaseModel, Field

from .consensus import ConsensusManager, ConsensusState
from .utils.logging import MASLogger
from .utils.validation import ValidationError, validate_task_id
from .metrics import MetricsCollector

# Configure logging
logger = logging.getLogger(__name__)

class TaskState(str, Enum):
    """Possible states for a task in its lifecycle."""
    CREATED = "created"
    WEBHOOK_RECEIVED = "webhook_received"
    SIGNATURE_VALIDATED = "signature_validated"
    IN_PROGRESS = "in_progress"
    CONSENSUS_PENDING = "consensus_pending"
    RESOLVED = "resolved"
    FAILED = "failed"

class TaskSource(str, Enum):
    """Possible sources for task creation."""
    GITHUB_PUSH = "github_push"
    GITHUB_PR = "github_pull_request"
    GITHUB_ISSUE = "github_issue"
    MANUAL = "manual"
    SYSTEM = "system"

@dataclass
class TaskDependency:
    """Represents a dependency between tasks."""
    parent_id: str
    child_id: str
    dependency_type: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class Task:
    """Represents a task in the MAS system."""
    task_id: str
    title: str
    description: str
    state: TaskState
    source: TaskSource
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]
    parent_tasks: Set[str] = field(default_factory=set)
    child_tasks: Set[str] = field(default_factory=set)
    assignees: Set[str] = field(default_factory=set)
    consensus_required: bool = True

class TaskMetadata(BaseModel):
    """Task metadata model."""
    task_id: str
    agent: Optional[str] = None
    parent_task_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: TaskState = TaskState.CREATED
    retry_count: int = 0
    error_message: Optional[str] = None

class TaskChain:
    """Manages task lifecycle and state transitions."""
    
    def __init__(self, consensus_manager, mas_logger, config: Dict[str, Any]):
        """
        Initialize TaskChain.
        
        Args:
            consensus_manager: ConsensusManager instance for state transitions
            mas_logger: MASLogger instance for task history
            config: Configuration dictionary from webhook_config.yaml
        """
        self.consensus_manager = consensus_manager
        self.mas_logger = mas_logger
        self.config = config
        self.tasks: Dict[str, TaskMetadata] = {}
        self.max_concurrent = config.get("task_chain", {}).get("max_concurrent", 10)
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        
    async def create_task(self, task_id: str, agent: Optional[str] = None,
                         parent_task_id: Optional[str] = None) -> TaskMetadata:
        """
        Create a new task and initialize its metadata.
        
        Args:
            task_id: Unique task identifier
            agent: Optional agent identifier
            parent_task_id: Optional parent task identifier
            
        Returns:
            TaskMetadata: Created task metadata
        """
        metadata = TaskMetadata(
            task_id=task_id,
            agent=agent,
            parent_task_id=parent_task_id
        )
        self.tasks[task_id] = metadata
        
        # Log task creation
        await self.mas_logger.log_event(
            "task_created",
            {
                "task_id": task_id,
                "agent": agent,
                "parent_task_id": parent_task_id,
                "timestamp": metadata.created_at.isoformat()
            }
        )
        
        return metadata
        
    async def transition_state(self, task_id: str, new_state: TaskState,
                             error_message: Optional[str] = None) -> bool:
        """
        Transition task to a new state.
        
        Args:
            task_id: Task identifier
            new_state: Target state
            error_message: Optional error message for failed states
            
        Returns:
            bool: True if transition successful
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
            
        task = self.tasks[task_id]
        old_state = task.status
        task.status = new_state
        task.updated_at = datetime.utcnow()
        
        if new_state == TaskState.FAILED:
            task.error_message = error_message
            
        # Log state transition
        await self.mas_logger.log_event(
            "task_state_transition",
            {
                "task_id": task_id,
                "old_state": old_state,
                "new_state": new_state,
                "timestamp": task.updated_at.isoformat(),
                "error_message": error_message
            }
        )
        
        return True
        
    async def process_consensus_result(self, task_id: str,
                                     consensus_result: Dict[str, Any]) -> bool:
        """
        Process consensus result and update task state.
        
        Args:
            task_id: Task identifier
            consensus_result: Consensus manager result
            
        Returns:
            bool: True if processing successful
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
            
        task = self.tasks[task_id]
        
        # Update task based on consensus result
        if consensus_result.get("status") == "approved":
            await self.transition_state(task_id, TaskState.RESOLVED)
        else:
            await self.transition_state(
                task_id,
                TaskState.FAILED,
                error_message=consensus_result.get("reason")
            )
            
        return True
        
    async def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve task history from MASLogger.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List[Dict[str, Any]]: Task history events
        """
        return await self.mas_logger.get_events(
            event_filter={"task_id": task_id}
        )
        
    def get_task_metadata(self, task_id: str) -> Optional[TaskMetadata]:
        """
        Get task metadata.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[TaskMetadata]: Task metadata if found
        """
        return self.tasks.get(task_id)
        
    async def cleanup_task(self, task_id: str):
        """
        Clean up task resources and metadata.
        
        Args:
            task_id: Task identifier
        """
        if task_id in self.tasks:
            await self.mas_logger.log_event(
                "task_cleanup",
                {
                    "task_id": task_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            del self.tasks[task_id]

class TaskChainManager:
    """Manages task lifecycle and dependencies."""

    def __init__(self) -> None:
        """Initialize task chain manager."""
        self.logger = MASLogger("task_chain")
        self.metrics = MetricsCollector()
        self.consensus_manager = ConsensusManager()
        self.tasks: Dict[str, Task] = {}
        self.dependencies: List[TaskDependency] = []

    def _generate_task_id(self, title: str, source: TaskSource) -> str:
        """
        Generate a unique task ID.

        Args:
            title: Task title
            source: Task source

        Returns:
            str: Unique task ID
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"{title}{source.value}{timestamp}"
        return f"task_{hashlib.sha256(hash_input.encode()).hexdigest()[:8]}"

    @metrics.track_task_timing
    def create_task(
        self,
        title: str,
        description: str,
        source: TaskSource,
        metadata: Dict[str, Any],
        parent_tasks: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        consensus_required: bool = True
    ) -> str:
        """
        Create a new task.

        Args:
            title: Task title
            description: Task description
            source: Task source
            metadata: Additional task metadata
            parent_tasks: List of parent task IDs
            assignees: List of assignee IDs
            consensus_required: Whether consensus is required

        Returns:
            str: Created task ID

        Raises:
            ValidationError: If parent tasks don't exist
        """
        task_id = self._generate_task_id(title, source)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Validate parent tasks
        if parent_tasks:
            for parent_id in parent_tasks:
                if parent_id not in self.tasks:
                    raise ValidationError(f"Parent task {parent_id} does not exist")

        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            state=TaskState.CREATED,
            source=source,
            created_at=timestamp,
            updated_at=timestamp,
            metadata=metadata,
            parent_tasks=set(parent_tasks or []),
            assignees=set(assignees or []),
            consensus_required=consensus_required
        )

        self.tasks[task_id] = task

        # Create dependencies
        if parent_tasks:
            for parent_id in parent_tasks:
                self.add_dependency(parent_id, task_id, "blocked_by")
                self.tasks[parent_id].child_tasks.add(task_id)

        self.logger.log_task(
            task_id=task_id,
            action="created",
            details={
                "title": title,
                "source": source.value,
                "parent_tasks": list(task.parent_tasks),
                "assignees": list(task.assignees)
            }
        )

        return task_id

    def add_dependency(self, parent_id: str, child_id: str, dependency_type: str) -> None:
        """
        Add a dependency between tasks.

        Args:
            parent_id: Parent task ID
            child_id: Child task ID
            dependency_type: Type of dependency

        Raises:
            ValidationError: If tasks don't exist or would create a cycle
        """
        if parent_id not in self.tasks or child_id not in self.tasks:
            raise ValidationError("Both parent and child tasks must exist")

        if self._would_create_cycle(parent_id, child_id):
            raise ValidationError("Adding this dependency would create a cycle")

        dependency = TaskDependency(
            parent_id=parent_id,
            child_id=child_id,
            dependency_type=dependency_type
        )
        self.dependencies.append(dependency)

        self.logger.log_task(
            task_id=child_id,
            action="dependency_added",
            details={"parent_id": parent_id, "type": dependency_type}
        )

    def _would_create_cycle(self, parent_id: str, child_id: str) -> bool:
        """
        Check if adding a dependency would create a cycle.

        Args:
            parent_id: Parent task ID
            child_id: Child task ID

        Returns:
            bool: True if adding the dependency would create a cycle
        """
        visited = set()

        def dfs(task_id: str) -> bool:
            if task_id == parent_id:
                return True
            if task_id in visited:
                return False
            visited.add(task_id)
            return any(dfs(child) for child in self.tasks[task_id].child_tasks)

        return dfs(child_id)

    def update_task_state(
        self, task_id: str, new_state: TaskState, details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update task state.

        Args:
            task_id: Task ID
            new_state: New task state
            details: Additional details about the state change

        Returns:
            bool: True if state was updated

        Raises:
            ValidationError: If task doesn't exist
        """
        if task_id not in self.tasks:
            raise ValidationError(f"Task {task_id} does not exist")

        task = self.tasks[task_id]
        old_state = task.state
        task.state = new_state
        task.updated_at = datetime.now(timezone.utc).isoformat()

        self.logger.log_task(
            task_id=task_id,
            action="state_updated",
            details={
                "old_state": old_state.value,
                "new_state": new_state.value,
                **(details or {})
            }
        )

        # If moving to consensus pending, start consensus
        if new_state == TaskState.CONSENSUS_PENDING and task.consensus_required:
            self.consensus_manager.start_consensus(task_id, list(task.assignees))

        # If resolved, check and update child tasks
        if new_state == TaskState.RESOLVED:
            self._update_child_tasks(task_id)

        return True

    def _update_child_tasks(self, task_id: str) -> None:
        """
        Update child tasks when a parent task is resolved.

        Args:
            task_id: Parent task ID
        """
        task = self.tasks[task_id]
        for child_id in task.child_tasks:
            child_task = self.tasks[child_id]
            # Check if all parent tasks are resolved
            if all(self.tasks[pid].state == TaskState.RESOLVED 
                  for pid in child_task.parent_tasks):
                self.update_task_state(
                    child_id,
                    TaskState.IN_PROGRESS,
                    {"reason": "All parent tasks resolved"}
                )

    def get_task_state(self, task_id: str) -> Dict[str, Any]:
        """
        Get task state and details.

        Args:
            task_id: Task ID

        Returns:
            Dict containing task state and details

        Raises:
            ValidationError: If task doesn't exist
        """
        if task_id not in self.tasks:
            raise ValidationError(f"Task {task_id} does not exist")

        task = self.tasks[task_id]
        consensus_state = None
        if task.state == TaskState.CONSENSUS_PENDING:
            try:
                consensus_state = self.consensus_manager.get_consensus_state(task_id)
            except ValueError:
                pass

        return {
            "task_id": task.task_id,
            "title": task.title,
            "state": task.state.value,
            "source": task.source.value,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "parent_tasks": list(task.parent_tasks),
            "child_tasks": list(task.child_tasks),
            "assignees": list(task.assignees),
            "consensus_required": task.consensus_required,
            "consensus_state": consensus_state,
            "metadata": task.metadata
        }

    def get_task_dependencies(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get task dependencies.

        Args:
            task_id: Task ID

        Returns:
            List of dependencies

        Raises:
            ValidationError: If task doesn't exist
        """
        if task_id not in self.tasks:
            raise ValidationError(f"Task {task_id} does not exist")

        return [
            {
                "parent_id": dep.parent_id,
                "child_id": dep.child_id,
                "type": dep.dependency_type,
                "created_at": dep.created_at
            }
            for dep in self.dependencies
            if dep.parent_id == task_id or dep.child_id == task_id
        ]

    def handle_consensus_result(self, task_id: str) -> None:
        """
        Handle consensus result for a task.

        Args:
            task_id: Task ID

        Raises:
            ValidationError: If task doesn't exist
        """
        if task_id not in self.tasks:
            raise ValidationError(f"Task {task_id} does not exist")

        task = self.tasks[task_id]
        if task.state != TaskState.CONSENSUS_PENDING:
            return

        try:
            consensus_state = self.consensus_manager.get_consensus_state(task_id)
            if consensus_state["state"] == ConsensusState.APPROVED.value:
                self.update_task_state(
                    task_id,
                    TaskState.RESOLVED,
                    {"consensus": "approved"}
                )
            elif consensus_state["state"] == ConsensusState.REJECTED.value:
                self.update_task_state(
                    task_id,
                    TaskState.FAILED,
                    {"consensus": "rejected"}
                )
        except ValueError:
            # No consensus state found, task remains in current state
            pass 