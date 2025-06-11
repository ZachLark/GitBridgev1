"""
MAS Metrics Module.

This module provides performance tracking and system health monitoring for the
MAS Lite Protocol v2.1 implementation, including task metrics, consensus metrics,
and system resource utilization.
"""

import time
import psutil
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from functools import wraps
import statistics
from .utils.logging import MASLogger
import uuid
from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity

logger = MASLogger(__name__)

@dataclass
class TaskMetrics:
    """Task-related performance metrics."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    current_concurrent: int = 0
    max_concurrent_seen: int = 0
    avg_completion_time: float = 0.0
    task_times: List[float] = None
    
    def __post_init__(self):
        """Initialize mutable fields."""
        self.task_times = []

@dataclass
class ConsensusMetrics:
    """Consensus-related performance metrics."""
    total_rounds: int = 0
    successful_consensus: int = 0
    failed_consensus: int = 0
    avg_consensus_time: float = 0.0
    consensus_times: List[float] = None
    
    def __post_init__(self):
        """Initialize mutable fields."""
        self.consensus_times = []

@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: Dict[str, float] = None
    
    def __post_init__(self):
        """Initialize mutable fields."""
        self.network_io = {"sent": 0.0, "received": 0.0}

class MetricsCollector:
    """Metrics collection and monitoring."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.task_metrics = TaskMetrics()
        self.consensus_metrics = ConsensusMetrics()
        self.system_metrics = SystemMetrics()
        self.error_handler = ErrorHandler()
        
    def track_task_timing(self, func: Callable) -> Callable:
        """Decorator to track task timing metrics.
        
        Args:
            func: Function to track
            
        Returns:
            Wrapped function
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                # Track concurrent tasks
                self.task_metrics.current_concurrent += 1
                self.task_metrics.max_concurrent_seen = max(
                    self.task_metrics.max_concurrent_seen,
                    self.task_metrics.current_concurrent
                )
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Update metrics on success
                if result:
                    self.task_metrics.completed_tasks += 1
                else:
                    self.task_metrics.failed_tasks += 1
                    
                return result
                
            except Exception as e:
                # Update failure metrics
                self.task_metrics.failed_tasks += 1
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.METRICS,
                    severity=ErrorSeverity.ERROR,
                    message=f"Task execution failed: {str(e)}",
                    details={"error": str(e)}
                )
                raise
                
            finally:
                # Always update timing metrics
                end_time = time.time()
                execution_time = end_time - start_time
                self.task_metrics.task_times.append(execution_time)
                self.task_metrics.avg_completion_time = statistics.mean(self.task_metrics.task_times)
                self.task_metrics.total_tasks += 1
                self.task_metrics.current_concurrent -= 1
                
        return wrapper
        
    def track_consensus_timing(self, func: Callable) -> Callable:
        """Decorator to track consensus timing metrics.
        
        Args:
            func: Function to track
            
        Returns:
            Wrapped function
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Update metrics on success
                self.consensus_metrics.successful_consensus += 1
                return result
                
            except Exception as e:
                # Update failure metrics
                self.consensus_metrics.failed_consensus += 1
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.METRICS,
                    severity=ErrorSeverity.ERROR,
                    message=f"Consensus failed: {str(e)}",
                    details={"error": str(e)}
                )
                raise
                
            finally:
                # Always update timing metrics
                end_time = time.time()
                execution_time = end_time - start_time
                self.consensus_metrics.consensus_times.append(execution_time)
                self.consensus_metrics.avg_consensus_time = statistics.mean(self.consensus_metrics.consensus_times)
                self.consensus_metrics.total_rounds += 1
                
        return wrapper
        
    def update_system_metrics(self):
        """Update system resource metrics."""
        try:
            # CPU usage
            self.system_metrics.cpu_usage = psutil.cpu_percent()
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_metrics.memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_metrics.disk_usage = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            self.system_metrics.network_io = {
                "sent": network.bytes_sent,
                "received": network.bytes_recv
            }
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.METRICS,
                severity=ErrorSeverity.WARNING,
                message=f"Failed to update system metrics: {str(e)}",
                details={"error": str(e)}
            )
            
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics.
        
        Returns:
            Dict containing metrics summary
        """
        self.update_system_metrics()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_metrics": {
                "total": self.task_metrics.total_tasks,
                "completed": self.task_metrics.completed_tasks,
                "failed": self.task_metrics.failed_tasks,
                "current_concurrent": self.task_metrics.current_concurrent,
                "max_concurrent": self.task_metrics.max_concurrent_seen,
                "avg_completion_time": self.task_metrics.avg_completion_time
            },
            "consensus_metrics": {
                "total_rounds": self.consensus_metrics.total_rounds,
                "successful": self.consensus_metrics.successful_consensus,
                "failed": self.consensus_metrics.failed_consensus,
                "avg_consensus_time": self.consensus_metrics.avg_consensus_time
            },
            "system_metrics": {
                "cpu_usage": self.system_metrics.cpu_usage,
                "memory_usage": self.system_metrics.memory_usage,
                "disk_usage": self.system_metrics.disk_usage,
                "network_io": self.system_metrics.network_io
            }
        }

    def log_metrics(self) -> None:
        """Log current metrics to the MAS logger."""
        metrics = self.get_metrics_summary()
        logger.logger.info(
            "System metrics update",
            extra={"metrics": metrics}
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics.

        Returns:
            Dict[str, Any]: Metrics data
        """
        return {
            "task_metrics": self.task_metrics,
            "consensus_metrics": self.consensus_metrics,
            "system_metrics": self.system_metrics
        }

    def get_metrics_by_function(self, function_name: str) -> List[Dict[str, Any]]:
        """Get metrics by function.

        Args:
            function_name: Function name

        Returns:
            List[Dict[str, Any]]: List of metrics
        """
        return [
            metric for metric in self.get_metrics().values()
            if isinstance(metric, dict) and metric.get("function") == function_name
        ]

    def clear_metrics(self) -> None:
        """Clear metrics."""
        self.task_metrics = TaskMetrics()
        self.consensus_metrics = ConsensusMetrics()
        self.system_metrics = SystemMetrics() 