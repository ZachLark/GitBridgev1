#!/usr/bin/env python3
"""Test suite for task chain summarization."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from generate_task_chain import (
    TaskChainSummary,
    summarize_task_chain,
    write_summary_to_file,
    TaskParams,
    generate_single_task
)

@pytest.fixture
def sample_tasks():
    """Create a sample set of tasks for testing."""
    tasks = []
    phase_id = "P7TEST"
    
    # Create tasks with different priorities and statuses
    priorities = ["high", "medium", "low"]
    statuses = ["pending", "approved", "rejected"]
    sections = [["1.1", "1.2"], ["2.0", "2.1"], ["3.0", "3.1"], ["4.0"]]
    
    for i in range(10):
        params = TaskParams(
            phase_id=phase_id,
            task_counter=i,
            priority_level=priorities[i % len(priorities)],
            sections_reviewed=sections[i % len(sections)]
        )
        task = generate_single_task(params)
        
        # Set different consensus statuses
        if i < 3:
            task["consensus"] = "approved"
        elif i < 5:
            task["consensus"] = "rejected"
        
        tasks.append(task)
    
    return tasks

def test_summarize_task_chain(sample_tasks):
    """Test task chain summarization."""
    summary = summarize_task_chain(sample_tasks)
    
    # Test basic attributes
    assert summary.phase_id == "P7TEST"
    assert summary.total_tasks == 10
    
    # Test priority distribution
    assert set(summary.priority_distribution.keys()) == {"high", "medium", "low"}
    assert sum(summary.priority_distribution.values()) == 10
    
    # Test consensus status
    assert summary.consensus_status["approved"] == 3
    assert summary.consensus_status["rejected"] == 2
    assert summary.consensus_status["pending"] == 5
    
    # Test completion rate
    assert summary.completion_rate == 50.0  # (3 + 2) / 10 * 100
    
    # Test section coverage
    assert all(section in summary.section_coverage for section in ["1.1", "1.2", "2.0", "2.1", "3.0", "3.1", "4.0"])
    
    # Test agent distribution
    assert "grok" in summary.agent_distribution
    assert "chatgpt" in summary.agent_distribution
    assert summary.agent_distribution["grok"]["generate_draft"] == 10
    assert summary.agent_distribution["chatgpt"]["review_draft"] == 10

def test_summarize_empty_tasks():
    """Test summarization with empty task list."""
    with pytest.raises(ValueError, match="No tasks provided for summarization"):
        summarize_task_chain([])

def test_summarize_specific_phase(sample_tasks):
    """Test summarization for specific phase."""
    # Test with existing phase
    summary = summarize_task_chain(sample_tasks, "P7TEST")
    assert summary.phase_id == "P7TEST"
    assert summary.total_tasks == 10
    
    # Test with non-existent phase
    with pytest.raises(ValueError, match="No tasks found for phase"):
        summarize_task_chain(sample_tasks, "NONEXISTENT")

def test_write_summary_to_file(sample_tasks, tmp_path):
    """Test writing summary to file."""
    summary = summarize_task_chain(sample_tasks)
    output_path = tmp_path / "test_summary.json"
    
    # Test writing
    write_summary_to_file(summary, output_path)
    assert output_path.exists()
    
    # Test content
    import json
    with output_path.open('r') as f:
        data = json.load(f)
        assert data["phase_id"] == summary.phase_id
        assert data["total_tasks"] == summary.total_tasks
        assert data["priority_distribution"] == summary.priority_distribution
        assert data["completion_rate"] == summary.completion_rate

def test_summary_time_range(sample_tasks):
    """Test time range calculation in summary."""
    summary = summarize_task_chain(sample_tasks)
    
    # Verify time format
    start = datetime.fromisoformat(summary.start_time)
    end = datetime.fromisoformat(summary.end_time)
    
    # Verify chronological order
    assert start <= end

if __name__ == "__main__":
    pytest.main([__file__]) 