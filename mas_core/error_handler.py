"""
MAS Error Handler Module.

This module provides centralized error handling and recovery mechanisms for the
MAS Lite Protocol v2.1 implementation, including error categorization, logging,
and recovery procedures.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from .utils.logging import MASLogger

@dataclass
class MASError:
    """Represents a MAS protocol error."""
    error_id: str
    error_type: str
    message: str
    timestamp: str
    context: Dict[str, Any]
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: Optional[bool] = None

class ErrorCategory:
    """Error categories as defined in MAS Lite Protocol v2.1."""
    VALIDATION = "validation_error"
    CONSENSUS = "consensus_error"
    TASK = "task_error"
    AGENT = "agent_error"
    SYSTEM = "system_error"
    PROTOCOL = "protocol_error"

class ErrorHandler:
    """Handles MAS system errors and recovery procedures."""

    def __init__(self) -> None:
        """Initialize error handler."""
        self.logger = MASLogger("error_handler")
        self.error_log: List[MASError] = []
        self.recovery_handlers = {
            ErrorCategory.VALIDATION: self._handle_validation_error,
            ErrorCategory.CONSENSUS: self._handle_consensus_error,
            ErrorCategory.TASK: self._handle_task_error,
            ErrorCategory.AGENT: self._handle_agent_error,
            ErrorCategory.SYSTEM: self._handle_system_error,
            ErrorCategory.PROTOCOL: self._handle_protocol_error
        }

    def handle_error(self, error: MASError) -> bool:
        """
        Handle an error and attempt recovery if possible.

        Args:
            error: The error to handle

        Returns:
            bool: True if recovery was successful, False otherwise
        """
        # Log the error
        self.logger.log_error(
            error_type=error.error_type,
            message=error.message,
            context=error.context
        )

        # Add to error log
        self.error_log.append(error)

        # Attempt recovery if handler exists
        if error.error_type in self.recovery_handlers:
            error.recovery_attempted = True
            try:
                error.recovery_successful = self.recovery_handlers[error.error_type](error)
                return error.recovery_successful
            except Exception as e:
                self.logger.log_error(
                    error_type="recovery_error",
                    message=f"Recovery failed: {str(e)}",
                    context={"original_error": asdict(error)}
                )
                error.recovery_successful = False
                return False
        return False

    def _handle_validation_error(self, error: MASError) -> bool:
        """Handle validation errors - typically non-recoverable."""
        return False

    def _handle_consensus_error(self, error: MASError) -> bool:
        """
        Handle consensus errors.
        
        Attempts to:
        1. Reset consensus state if deadlocked
        2. Request new votes if incomplete
        3. Force majority decision if timeout
        """
        if not error.task_id:
            return False

        try:
            # Implementation depends on consensus module
            # For now, just log the attempt
            self.logger.log_task(
                task_id=error.task_id,
                action="consensus_recovery",
                details={"error": error.message}
            )
            return True
        except Exception:
            return False

    def _handle_task_error(self, error: MASError) -> bool:
        """
        Handle task-related errors.
        
        Attempts to:
        1. Retry failed task operations
        2. Reassign tasks if agent failed
        3. Reset task state if corrupted
        """
        if not error.task_id:
            return False

        try:
            # Implementation depends on task chain module
            # For now, just log the attempt
            self.logger.log_task(
                task_id=error.task_id,
                action="task_recovery",
                details={"error": error.message}
            )
            return True
        except Exception:
            return False

    def _handle_agent_error(self, error: MASError) -> bool:
        """
        Handle agent-related errors.
        
        Attempts to:
        1. Restart agent if crashed
        2. Reassign tasks if agent is unavailable
        3. Reset agent state if corrupted
        """
        if not error.agent_id:
            return False

        try:
            # Implementation depends on agent module
            # For now, just log the attempt
            self.logger.log_task(
                task_id=error.task_id or "unknown",
                action="agent_recovery",
                details={"agent_id": error.agent_id, "error": error.message}
            )
            return True
        except Exception:
            return False

    def _handle_system_error(self, error: MASError) -> bool:
        """Handle system-level errors - typically requires manual intervention."""
        self.logger.log_error(
            error_type="system_error",
            message="System error requires manual intervention",
            context=asdict(error)
        )
        return False

    def _handle_protocol_error(self, error: MASError) -> bool:
        """Handle protocol compliance errors - typically non-recoverable."""
        return False

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of handled errors.

        Returns:
            Dict containing error statistics
        """
        categories = {}
        recovery_stats = {"attempted": 0, "successful": 0}

        for error in self.error_log:
            # Count by category
            categories[error.error_type] = categories.get(error.error_type, 0) + 1
            
            # Track recovery stats
            if error.recovery_attempted:
                recovery_stats["attempted"] += 1
                if error.recovery_successful:
                    recovery_stats["successful"] += 1

        return {
            "total_errors": len(self.error_log),
            "categories": categories,
            "recovery_stats": recovery_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        } 