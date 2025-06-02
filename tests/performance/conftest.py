#!/usr/bin/env python3
"""Shared fixtures and configuration for performance tests."""

import pytest
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any
import json
import psutil
import resource

@pytest.fixture(scope="session")
def performance_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace for performance tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "outputs").mkdir()
        (workspace / "logs").mkdir()
        yield workspace

@pytest.fixture(scope="function")
def cleanup_logs() -> Generator[None, None, None]:
    """Clean up any test log files after each test."""
    yield
    for log_file in Path(".").glob("*.json"):
        if log_file.name.startswith(("test_", "benchmark_", "stress_")):
            log_file.unlink(missing_ok=True)

@pytest.fixture(scope="session")
def resource_limits() -> Dict[str, int]:
    """Configure resource limits for performance tests."""
    # Get current limits
    curr_mem = resource.getrlimit(resource.RLIMIT_AS)[1]
    curr_fd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    curr_cpu = resource.getrlimit(resource.RLIMIT_CPU)[1]
    
    return {
        "memory_mb": min(1000, curr_mem // (1024 * 1024)) if curr_mem != resource.RLIM_INFINITY else 1000,
        "file_descriptors": min(1024, curr_fd) if curr_fd != resource.RLIM_INFINITY else 1024,
        "cpu_time": min(30, curr_cpu) if curr_cpu != resource.RLIM_INFINITY else 30
    }

@pytest.fixture(autouse=True)
def setup_resource_limits(resource_limits: Dict[str, int]) -> Generator[None, None, None]:
    """Set up resource limits before each test."""
    # Save original limits
    orig_mem = resource.getrlimit(resource.RLIMIT_AS)
    orig_fd = resource.getrlimit(resource.RLIMIT_NOFILE)
    orig_cpu = resource.getrlimit(resource.RLIMIT_CPU)
    
    try:
        # Set new limits, respecting system maximums
        mem_limit = resource_limits["memory_mb"] * 1024 * 1024
        fd_limit = resource_limits["file_descriptors"]
        cpu_limit = resource_limits["cpu_time"]
        
        # Only set limits if they don't exceed system maximums
        if orig_mem[1] != resource.RLIM_INFINITY and mem_limit <= orig_mem[1]:
            resource.setrlimit(resource.RLIMIT_AS, (mem_limit, orig_mem[1]))
        
        if orig_fd[1] != resource.RLIM_INFINITY and fd_limit <= orig_fd[1]:
            resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, orig_fd[1]))
        
        if orig_cpu[1] != resource.RLIM_INFINITY and cpu_limit <= orig_cpu[1]:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, orig_cpu[1]))
        
        yield
    finally:
        # Restore original limits
        if orig_mem[1] != resource.RLIM_INFINITY:
            resource.setrlimit(resource.RLIMIT_AS, orig_mem)
        if orig_fd[1] != resource.RLIM_INFINITY:
            resource.setrlimit(resource.RLIMIT_NOFILE, orig_fd)
        if orig_cpu[1] != resource.RLIM_INFINITY:
            resource.setrlimit(resource.RLIMIT_CPU, orig_cpu)

@pytest.fixture
def performance_metrics() -> Dict[str, float]:
    """Get current system performance metrics."""
    process = psutil.Process()
    return {
        "memory_percent": process.memory_percent(),
        "cpu_percent": process.cpu_percent(),
        "io_counters": process.io_counters()._asdict() if process.io_counters() else {},
        "num_threads": process.num_threads(),
        "num_fds": process.num_fds() if hasattr(process, "num_fds") else 0
    }

def pytest_configure(config):
    """Configure pytest for performance tests."""
    config.addinivalue_line(
        "markers",
        "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers",
        "benchmark: mark test as benchmark test"
    )

def pytest_runtest_setup(item):
    """Set up performance test environment."""
    if "performance" in item.keywords:
        # Ensure we have enough resources for performance tests
        process = psutil.Process()
        if process.memory_percent() > 80:
            pytest.skip("System memory usage too high")
        if process.cpu_percent() > 80:
            pytest.skip("System CPU usage too high") 