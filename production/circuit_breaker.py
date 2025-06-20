#!/usr/bin/env python3
"""
GitBridge Circuit Breaker Pattern
Task: P20P7S5C - Production Hardening

Circuit breaker implementation for SmartRouter production hardening.
Provides automatic failover and recovery mechanisms for provider failures.

Author: GitBridge Development Team
Date: 2025-06-19
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5        # Number of failures before opening circuit
    recovery_timeout: float = 60.0    # Time to wait before attempting recovery (seconds)
    expected_exception: type = Exception  # Exception type to count as failures
    success_threshold: int = 2        # Number of successes to close circuit
    timeout: float = 30.0             # Request timeout (seconds)
    max_failures_per_minute: int = 10  # Max failures per minute before opening


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for production hardening.
    
    Features:
    - Automatic failure detection and circuit opening
    - Configurable recovery timeouts
    - Half-open state for safe recovery testing
    - Rate limiting based on failure frequency
    - Thread-safe operation
    - Comprehensive monitoring and metrics
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker (usually provider name)
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config
        
        # State management
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._last_success_time = None
        self._circuit_opened_time = None
        
        # Failure tracking for rate limiting
        self._recent_failures = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Monitoring
        self._total_requests = 0
        self._total_failures = 0
        self._total_successes = 0
        self._total_timeouts = 0
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {config}")
        
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state
            
    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self.state == CircuitState.OPEN
        
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self.state == CircuitState.CLOSED
        
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self.state == CircuitState.HALF_OPEN
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        with self._lock:
            self._total_requests += 1
            
            # Check if circuit is open
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._set_half_open()
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Last failure: {self._last_failure_time}"
                    )
            
            # Check if circuit is half-open
            if self._state == CircuitState.HALF_OPEN:
                # Only allow one request in half-open state
                if self._success_count > 0:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is HALF_OPEN. "
                        f"Testing recovery with limited requests."
                    )
        
        # Execute function with timeout
        start_time = time.time()
        try:
            result = self._execute_with_timeout(func, *args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure(e)
            raise
            
    def _execute_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout."""
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=self.config.timeout)
            except concurrent.futures.TimeoutError:
                self._total_timeouts += 1
                raise TimeoutError(f"Function execution timed out after {self.config.timeout}s")
                
    def _on_success(self):
        """Handle successful execution."""
        with self._lock:
            self._success_count += 1
            self._total_successes += 1
            self._last_success_time = datetime.now(timezone.utc)
            
            # Reset failure count
            self._failure_count = 0
            
            # If in half-open state and enough successes, close circuit
            if self._state == CircuitState.HALF_OPEN:
                if self._success_count >= self.config.success_threshold:
                    self._set_closed()
                    logger.info(f"Circuit breaker '{self.name}' closed after {self._success_count} successful calls")
                    
    def _on_failure(self, exception: Exception):
        """Handle failed execution."""
        with self._lock:
            self._failure_count += 1
            self._total_failures += 1
            self._last_failure_time = datetime.now(timezone.utc)
            
            # Reset success count
            self._success_count = 0
            
            # Add to recent failures for rate limiting
            self._recent_failures.append(self._last_failure_time)
            
            # Clean old failures (older than 1 minute)
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=1)
            self._recent_failures = [
                f for f in self._recent_failures 
                if f > cutoff_time
            ]
            
            # Check if circuit should open
            if self._should_open_circuit():
                self._set_open()
                logger.warning(
                    f"Circuit breaker '{self.name}' opened after {self._failure_count} failures. "
                    f"Recent failures: {len(self._recent_failures)}"
                )
                
    def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened."""
        # Check failure threshold
        if self._failure_count >= self.config.failure_threshold:
            return True
            
        # Check rate limiting
        if len(self._recent_failures) >= self.config.max_failures_per_minute:
            return True
            
        return False
        
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if not self._circuit_opened_time:
            return False
            
        elapsed = (datetime.now(timezone.utc) - self._circuit_opened_time).total_seconds()
        return elapsed >= self.config.recovery_timeout
        
    def _set_open(self):
        """Set circuit to open state."""
        self._state = CircuitState.OPEN
        self._circuit_opened_time = datetime.now(timezone.utc)
        
    def _set_half_open(self):
        """Set circuit to half-open state."""
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
        self._failure_count = 0
        logger.info(f"Circuit breaker '{self.name}' set to HALF_OPEN for recovery testing")
        
    def _set_closed(self):
        """Set circuit to closed state."""
        self._state = CircuitState.CLOSED
        self._circuit_opened_time = None
        self._success_count = 0
        self._failure_count = 0
        
    def force_open(self):
        """Force circuit to open state."""
        with self._lock:
            self._set_open()
            logger.warning(f"Circuit breaker '{self.name}' forced to OPEN state")
            
    def force_close(self):
        """Force circuit to closed state."""
        with self._lock:
            self._set_closed()
            logger.info(f"Circuit breaker '{self.name}' forced to CLOSED state")
            
    def reset(self):
        """Reset circuit breaker to initial state."""
        with self._lock:
            self._set_closed()
            self._recent_failures.clear()
            self._total_requests = 0
            self._total_failures = 0
            self._total_successes = 0
            self._total_timeouts = 0
            logger.info(f"Circuit breaker '{self.name}' reset to initial state")
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        with self._lock:
            total_requests = self._total_requests
            success_rate = (
                self._total_successes / total_requests if total_requests > 0 else 1.0
            )
            
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self._failure_count,
                'success_count': self._success_count,
                'total_requests': total_requests,
                'total_failures': self._total_failures,
                'total_successes': self._total_successes,
                'total_timeouts': self._total_timeouts,
                'success_rate': success_rate,
                'recent_failures_count': len(self._recent_failures),
                'last_failure_time': self._last_failure_time.isoformat() if self._last_failure_time else None,
                'last_success_time': self._last_success_time.isoformat() if self._last_success_time else None,
                'circuit_opened_time': self._circuit_opened_time.isoformat() if self._circuit_opened_time else None,
                'config': {
                    'failure_threshold': self.config.failure_threshold,
                    'recovery_timeout': self.config.recovery_timeout,
                    'success_threshold': self.config.success_threshold,
                    'timeout': self.config.timeout,
                    'max_failures_per_minute': self.config.max_failures_per_minute
                }
            }
            
    @contextmanager
    def context(self):
        """Context manager for circuit breaker."""
        try:
            yield self
        finally:
            pass


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.
    
    Features:
    - Centralized management of multiple circuit breakers
    - Global metrics and monitoring
    - Bulk operations for all circuit breakers
    """
    
    def __init__(self):
        """Initialize circuit breaker manager."""
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
        
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create a circuit breaker.
        
        Args:
            name: Circuit breaker name
            config: Configuration (optional, uses default if not provided)
            
        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name not in self._circuit_breakers:
                if config is None:
                    config = CircuitBreakerConfig()
                self._circuit_breakers[name] = CircuitBreaker(name, config)
                
            return self._circuit_breakers[name]
            
    def remove_circuit_breaker(self, name: str):
        """Remove a circuit breaker."""
        with self._lock:
            if name in self._circuit_breakers:
                del self._circuit_breakers[name]
                logger.info(f"Circuit breaker '{name}' removed from manager")
                
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all circuit breakers."""
        with self._lock:
            metrics = {
                'total_circuit_breakers': len(self._circuit_breakers),
                'circuit_breakers': {},
                'summary': {
                    'total_requests': 0,
                    'total_failures': 0,
                    'total_successes': 0,
                    'open_circuits': 0,
                    'closed_circuits': 0,
                    'half_open_circuits': 0
                }
            }
            
            for name, cb in self._circuit_breakers.items():
                cb_metrics = cb.get_metrics()
                metrics['circuit_breakers'][name] = cb_metrics
                
                # Update summary
                summary = metrics['summary']
                summary['total_requests'] += cb_metrics['total_requests']
                summary['total_failures'] += cb_metrics['total_failures']
                summary['total_successes'] += cb_metrics['total_successes']
                
                if cb_metrics['state'] == 'open':
                    summary['open_circuits'] += 1
                elif cb_metrics['state'] == 'closed':
                    summary['closed_circuits'] += 1
                elif cb_metrics['state'] == 'half_open':
                    summary['half_open_circuits'] += 1
                    
            return metrics
            
    def reset_all(self):
        """Reset all circuit breakers."""
        with self._lock:
            for cb in self._circuit_breakers.values():
                cb.reset()
            logger.info("All circuit breakers reset")
            
    def force_close_all(self):
        """Force close all circuit breakers."""
        with self._lock:
            for cb in self._circuit_breakers.values():
                cb.force_close()
            logger.info("All circuit breakers forced to CLOSED state")
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        metrics = self.get_all_metrics()
        summary = metrics['summary']
        
        total_circuits = len(self._circuit_breakers)
        healthy_circuits = summary['closed_circuits']
        unhealthy_circuits = summary['open_circuits'] + summary['half_open_circuits']
        
        health_score = healthy_circuits / total_circuits if total_circuits > 0 else 1.0
        
        return {
            'status': 'healthy' if health_score >= 0.8 else 'degraded' if health_score >= 0.5 else 'unhealthy',
            'health_score': health_score,
            'total_circuits': total_circuits,
            'healthy_circuits': healthy_circuits,
            'unhealthy_circuits': unhealthy_circuits,
            'open_circuits': summary['open_circuits'],
            'half_open_circuits': summary['half_open_circuits'],
            'overall_success_rate': (
                summary['total_successes'] / summary['total_requests'] 
                if summary['total_requests'] > 0 else 1.0
            )
        }


# Global circuit breaker manager
_circuit_breaker_manager = CircuitBreakerManager()


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get a circuit breaker from the global manager."""
    return _circuit_breaker_manager.get_circuit_breaker(name, config)


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager."""
    return _circuit_breaker_manager


if __name__ == "__main__":
    # Test circuit breaker
    import random
    
    def unreliable_function():
        """Function that fails randomly."""
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Random failure")
        return "Success"
    
    # Create circuit breaker
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=10.0,
        success_threshold=2
    )
    
    cb = get_circuit_breaker("test_provider", config)
    
    print("Testing circuit breaker...")
    for i in range(10):
        try:
            result = cb.call(unreliable_function)
            print(f"Call {i+1}: {result}")
        except Exception as e:
            print(f"Call {i+1}: Failed - {e}")
            
        print(f"Circuit state: {cb.state.value}")
        print(f"Failure count: {cb._failure_count}")
        print(f"Success count: {cb._success_count}")
        print("---")
        time.sleep(1)
        
    # Print metrics
    print("Final metrics:")
    print(json.dumps(cb.get_metrics(), indent=2)) 