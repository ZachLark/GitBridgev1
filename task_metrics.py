#!/usr/bin/env python3
"""Metrics collection for task chain generator."""

import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime, timezone

@dataclass
class TaskMetrics:
    """Metrics for task generation and writing."""
    total_tasks: int = 0
    failed_tasks: int = 0
    avg_generation_time: float = 0.0
    avg_write_time: float = 0.0
    peak_memory_usage: float = 0.0
    concurrent_writes: int = 0
    errors: List[str] = field(default_factory=list)
    last_run: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MetricsCollector:
    """Collect and store metrics about task generation."""
    
    def __init__(self, metrics_file: Path = Path("task_metrics.json")):
        self.metrics_file = metrics_file
        self.current_metrics = TaskMetrics()
        self._load_metrics()
    
    def _load_metrics(self):
        """Load existing metrics from file."""
        if self.metrics_file.exists():
            with self.metrics_file.open('r') as f:
                data = json.load(f)
                self.current_metrics = TaskMetrics(**data)
    
    def _save_metrics(self):
        """Save current metrics to file."""
        with self.metrics_file.open('w') as f:
            json.dump(self.current_metrics.__dict__, f, indent=2)
    
    def record_generation(self, count: int, duration: float):
        """Record task generation metrics."""
        self.current_metrics.total_tasks += count
        self.current_metrics.avg_generation_time = (
            (self.current_metrics.avg_generation_time * 
             (self.current_metrics.total_tasks - count) +
             duration * count) / self.current_metrics.total_tasks
        )
        self._save_metrics()
    
    def record_write(self, duration: float, is_concurrent: bool = False):
        """Record write operation metrics."""
        if is_concurrent:
            self.current_metrics.concurrent_writes += 1
        self.current_metrics.avg_write_time = (
            (self.current_metrics.avg_write_time * 
             self.current_metrics.total_tasks +
             duration) / (self.current_metrics.total_tasks + 1)
        )
        self._save_metrics()
    
    def record_error(self, error: str):
        """Record an error occurrence."""
        self.current_metrics.failed_tasks += 1
        self.current_metrics.errors.append(f"{datetime.now(timezone.utc).isoformat()}: {error}")
        self._save_metrics()
    
    def record_memory_usage(self, memory_mb: float):
        """Record peak memory usage."""
        self.current_metrics.peak_memory_usage = max(
            self.current_metrics.peak_memory_usage,
            memory_mb
        )
        self._save_metrics()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        return {
            "total_tasks": self.current_metrics.total_tasks,
            "success_rate": (
                (self.current_metrics.total_tasks - self.current_metrics.failed_tasks) /
                self.current_metrics.total_tasks * 100 if self.current_metrics.total_tasks > 0 else 0
            ),
            "avg_generation_time": self.current_metrics.avg_generation_time,
            "avg_write_time": self.current_metrics.avg_write_time,
            "peak_memory_mb": self.current_metrics.peak_memory_usage,
            "concurrent_writes": self.current_metrics.concurrent_writes,
            "recent_errors": self.current_metrics.errors[-5:] if self.current_metrics.errors else []
        } 