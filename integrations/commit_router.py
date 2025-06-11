"""
Commit router for GitBridge MAS Lite.

This module provides commit routing functionality for GitBridge's event processing
system, following MAS Lite Protocol v2.1 routing requirements.
"""

import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from mas_core.task_chain import TaskChainManager, TaskState, TaskSource
from mas_core.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from mas_core.utils.logging import MASLogger

logger = MASLogger(__name__)

class CommitRouter:
    """Commit router."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize router.
        
        Args:
            config: Configuration dictionary containing router settings
                   Required keys:
                   - router.max_concurrent: Maximum concurrent tasks
                   - router.consensus_required: Whether consensus is required
        """
        self.config = config
        self.task_manager = TaskChainManager(config)
        self.error_handler = ErrorHandler()
        
    async def route_commit(self, commit_data: Dict[str, Any]) -> Optional[str]:
        """Route commit to task.
        
        Args:
            commit_data: Commit data
            
        Returns:
            Optional[str]: Task ID if routing successful
        """
        try:
            # Validate commit data
            if not commit_data:
                raise ValueError("Empty commit data")
                
            if "sha" not in commit_data:
                raise ValueError("Missing commit SHA")
                
            if "message" not in commit_data:
                raise ValueError("Missing commit message")
                
            # Create task
            task_id = str(uuid.uuid4())
            task_data = {
                "type": "commit",
                "commit_sha": commit_data["sha"],
                "commit_message": commit_data["message"],
                "author": commit_data.get("author", {}).get("name"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            success = await self.task_manager.create_task(
                task_id=task_id,
                data=task_data,
                metadata={
                    "created_by": "commit_router",
                    "source": TaskSource.Webhook
                }
            )
            
            if not success:
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.TASK,
                    severity=ErrorSeverity.ERROR,
                    message="Failed to create task for commit",
                    details={
                        "commit_sha": commit_data["sha"],
                        "task_id": task_id
                    }
                )
                return None
                
            # Update task state
            success = await self.task_manager.update_task_state(task_id, TaskState.InProgress)
            
            if not success:
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.TASK,
                    severity=ErrorSeverity.ERROR,
                    message="Failed to update task state",
                    details={
                        "commit_sha": commit_data["sha"],
                        "task_id": task_id,
                        "target_state": TaskState.InProgress
                    }
                )
                return None
                
            logger.info(
                f"Routed commit {commit_data['sha']} to task {task_id}",
                extra={
                    "commit_sha": commit_data["sha"],
                    "task_id": task_id
                }
            )
            return task_id
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to route commit: {str(e)}",
                details={
                    "commit_data": commit_data,
                    "error": str(e)
                }
            )
            return None
            
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Task status if found
        """
        try:
            task = await self.task_manager.get_task(task_id)
            if not task:
                return None
                
            return {
                "task_id": task.task_id,
                "state": task.state,
                "commit_sha": task.data.get("commit_sha"),
                "created_at": task.created_at,
                "updated_at": task.updated_at
            }
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to get task status: {str(e)}",
                details={
                    "task_id": task_id,
                    "error": str(e)
                }
            )
            return None
            
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            await self.task_manager.cleanup()
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to clean up commit router: {str(e)}",
                details={"error": str(e)}
            ) 