"""
Error handling for GitBridge MAS Lite implementation.

This module provides centralized error handling functionality for GitBridge's
event processing system, following MAS Lite Protocol v2.1 error handling requirements.
"""

import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from .utils.logging import MASLogger

logger = MASLogger(__name__)

class ErrorCategory(str, Enum):
    """Error categories."""
    TASK = "task"
    QUEUE = "queue"
    CONSENSUS = "consensus"
    METRICS = "metrics"
    SYSTEM = "system"

class ErrorSeverity(str, Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MASError:
    """MAS error data structure."""
    error_id: str
    error_type: ErrorCategory
    message: str
    timestamp: str
    context: Dict[str, Any]
    severity: ErrorSeverity
    task_id: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False

class ErrorHandler:
    """Error handler."""
    
    def __init__(self):
        """Initialize error handler."""
        self.error_log: List[MASError] = []
        
    def handle_error(
        self,
        error_id: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        message: str,
        details: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> bool:
        """Handle an error.
        
        Args:
            error_id: Unique error identifier
            category: Error category
            severity: Error severity
            message: Error message
            details: Error details
            task_id: Optional task identifier
            
        Returns:
            bool: True if error handled successfully
        """
        try:
            error = MASError(
                error_id=error_id,
                error_type=category,
                message=message,
                timestamp=datetime.now(timezone.utc).isoformat(),
                context=details,
                severity=severity,
                task_id=task_id
            )
            
            self.error_log.append(error)
            return True
            
        except Exception:
            return False
            
    def get_errors_by_category(self, category: ErrorCategory) -> List[MASError]:
        """Get errors by category.
        
        Args:
            category: Error category
            
        Returns:
            List[MASError]: List of errors
        """
        return [error for error in self.error_log if error.error_type == category]
        
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[MASError]:
        """Get errors by severity.
        
        Args:
            severity: Error severity
            
        Returns:
            List[MASError]: List of errors
        """
        return [error for error in self.error_log if error.severity == severity]
        
    def get_errors_by_task(self, task_id: str) -> List[MASError]:
        """Get errors by task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List[MASError]: List of errors
        """
        return [error for error in self.error_log if error.task_id == task_id]
        
    def clear_errors(self) -> None:
        """Clear error log."""
        self.error_log.clear()
        
    def get_error_count(self) -> int:
        """Get total error count.
        
        Returns:
            int: Total number of errors
        """
        return len(self.error_log)
        
    def get_error(self, error_id: str) -> Optional[MASError]:
        """Get error by ID.
        
        Args:
            error_id: Error identifier
            
        Returns:
            Optional[MASError]: Error if found, None otherwise
        """
        for error in self.error_log:
            if error.error_id == error_id:
                return error
        return None 