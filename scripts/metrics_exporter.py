"""
Metrics exporter for GitBridge.
Implements Prometheus metrics and alerts for Redis queue monitoring.
"""

import time
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import yaml
from typing import Dict, Any

class MetricsExporter:
    def __init__(self, config_path: str = "webhook_config.yaml"):
        self.config = self._load_config(config_path)
        self._setup_metrics()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_metrics(self):
        """Initialize Prometheus metrics."""
        # Queue metrics
        self.queue_depth = Gauge('redis_queue_depth', 'Current queue depth')
        self.queue_depth_max = Gauge('redis_queue_depth_max', 'Maximum queue depth')
        
        # Processing metrics
        self.processing_time = Histogram('redis_processing_time_seconds',
                                       'Event processing time in seconds',
                                       buckets=[.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0])
        
        # Error metrics
        self.error_counter = Counter('redis_errors_total', 'Total number of errors')
        self.retry_counter = Counter('redis_retries_total', 'Total number of retries')
        self.dropout_rate = Gauge('redis_dropout_rate', 'Event dropout rate')
        
        # Alert metrics
        self.retry_alert = Gauge('redis_retry_alert', 'Retry count exceeds threshold')
        self.queue_full_alert = Gauge('redis_queue_full_alert', 'Queue is near capacity')
        self.error_rate_alert = Gauge('redis_error_rate_alert', 'Error rate exceeds threshold')
        
        # Performance metrics
        self.latency = Histogram('redis_latency_seconds',
                               'Operation latency in seconds',
                               buckets=[.001, .005, .01, .025, .05, .075, .1, .25, .5])
    
    def start_server(self, port: int = None):
        """Start the Prometheus metrics server."""
        if port is None:
            port = self.config['metrics']['prometheus_port']
        start_http_server(port)
    
    def update_queue_metrics(self, depth: int, max_size: int):
        """Update queue-related metrics."""
        self.queue_depth.set(depth)
        self.queue_depth_max.set(max_size)
        
        # Alert if queue is over 80% full
        if depth > max_size * 0.8:
            self.queue_full_alert.set(1)
        else:
            self.queue_full_alert.set(0)
    
    def record_processing_time(self, duration: float):
        """Record event processing time."""
        self.processing_time.observe(duration)
        self.latency.observe(duration)
    
    def record_error(self, error_type: str):
        """Record an error occurrence."""
        self.error_counter.labels(type=error_type).inc()
        
        # Calculate error rate over last minute
        error_rate = self.error_counter._value.get() / 60
        if error_rate > self.config['metrics']['alert_thresholds']['error_rate']:
            self.error_rate_alert.set(1)
    
    def record_retry(self, count: int):
        """Record retry attempt and check threshold."""
        self.retry_counter.inc()
        
        if count > self.config['metrics']['alert_thresholds']['retry_count']:
            self.retry_alert.set(1)
        else:
            self.retry_alert.set(0)
    
    def record_dropout(self, rate: float):
        """Record event dropout rate."""
        self.dropout_rate.set(rate)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics."""
        return {
            'queue_depth': self.queue_depth._value.get(),
            'processing_time_avg': self.processing_time._sum.get() / max(self.processing_time._count.get(), 1),
            'error_count': self.error_counter._value.get(),
            'retry_count': self.retry_counter._value.get(),
            'dropout_rate': self.dropout_rate._value.get(),
            'alerts': {
                'retry_threshold': bool(self.retry_alert._value.get()),
                'queue_full': bool(self.queue_full_alert._value.get()),
                'error_rate': bool(self.error_rate_alert._value.get())
            }
        } 