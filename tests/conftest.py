#!/usr/bin/env python3
"""Shared test fixtures and utilities for GitBridge tests."""

import pytest
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Any, Generator, Tuple
from datetime import datetime, timezone

from generate_task_chain import TaskParams, generate_single_task

@pytest.fixture
def test_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        # Create standard directories
        (workspace / "outputs").mkdir()
        (workspace / "logs").mkdir()
        yield workspace

@pytest.fixture
def sample_task_params() -> TaskParams:
    """Create a sample TaskParams instance."""
    return TaskParams(
        phase_id="P8TEST",
        task_counter=1,
        description="Test task",
        priority_level="high",
        sections_reviewed=["1.1", "2.0"]
    )

@pytest.fixture
def sample_task(sample_task_params) -> Dict[str, Any]:
    """Create a sample task dictionary."""
    return generate_single_task(sample_task_params)

@pytest.fixture
def task_batch() -> List[Dict[str, Any]]:
    """Create a batch of sample tasks."""
    tasks = []
    for i in range(5):
        params = TaskParams(
            phase_id="P8TEST",
            task_counter=i,
            description=f"Batch task {i}",
            priority_level="high" if i < 2 else "medium",
            sections_reviewed=["1.1", "2.0"] if i % 2 == 0 else ["3.0", "4.0"]
        )
        tasks.append(generate_single_task(params))
    return tasks

@pytest.fixture
def mock_log_file(test_workspace, task_batch) -> Tuple[Path, List[Dict[str, Any]]]:
    """Create a mock log file with sample tasks."""
    log_path = test_workspace / "logs" / "mas_log.json"
    with log_path.open('w', encoding='utf-8') as f:
        json.dump(task_batch, f, indent=2)
    return log_path, task_batch

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "property: mark test as a property-based test"
    )
    config.addinivalue_line(
        "markers",
        "performance: mark test as a performance test"
    )

def pytest_collection_modifyitems(items):
    """Add markers based on test location and type."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "property" in item.name:
            item.add_marker(pytest.mark.property)
        if "performance" in item.name:
            item.add_marker(pytest.mark.performance) 