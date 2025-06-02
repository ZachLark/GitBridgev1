#!/usr/bin/env python3
"""Property-based test suite for task chain generation and summarization."""

import pytest
from hypothesis import given, strategies as st, settings, note
from datetime import datetime, timezone
from typing import List, Dict, Any
from generate_task_chain import (
    TaskParams,
    generate_single_task,
    summarize_task_chain,
    PRIORITY_LEVELS,
    SECTION_CODES
)

# Custom Hypothesis strategies
@st.composite
def task_params_strategy(draw):
    """Generate valid TaskParams instances."""
    return TaskParams(
        phase_id=draw(st.from_regex(r'P[0-9][A-Z]TEST')),
        task_counter=draw(st.integers(min_value=0, max_value=1000)),
        priority_level=draw(st.sampled_from(PRIORITY_LEVELS)),
        sections_reviewed=draw(st.lists(
            st.sampled_from(SECTION_CODES),
            min_size=1,
            max_size=3,
            unique=True
        ))
    )

@st.composite
def task_list_strategy(draw):
    """Generate lists of valid tasks."""
    task_count = draw(st.integers(min_value=1, max_value=100))
    tasks = []
    for i in range(task_count):
        params = draw(task_params_strategy())
        task = generate_single_task(params)
        # Randomly set consensus status
        task["consensus"] = draw(st.sampled_from(["pending", "approved", "rejected"]))
        tasks.append(task)
    return tasks

# Property-based tests
@settings(max_examples=100, deadline=None)
@given(tasks=task_list_strategy())
def test_summary_completeness_property(tasks):
    """Test that summary contains all tasks and maintains data integrity."""
    summary = summarize_task_chain(tasks)
    
    # Property 1: Total tasks match
    assert summary.total_tasks == len(tasks)
    
    # Property 2: All priorities are accounted for
    total_priorities = sum(summary.priority_distribution.values())
    assert total_priorities == len(tasks)
    
    # Property 3: Completion rate calculation is accurate
    completed = sum(1 for t in tasks if t["consensus"] in ["approved", "rejected"])
    expected_rate = (completed / len(tasks)) * 100
    assert abs(summary.completion_rate - expected_rate) < 0.001
    
    # Property 4: Section coverage includes all sections
    all_sections = {s for t in tasks for s in t["sections_reviewed"]}
    assert all_sections == set(summary.section_coverage.keys())
    
    # Property 5: Agent distribution matches task assignments
    for task in tasks:
        for agent, role in task["agent_assignment"].items():
            assert agent in summary.agent_distribution
            assert role in summary.agent_distribution[agent]

@settings(max_examples=50)
@given(tasks=task_list_strategy())
def test_time_range_property(tasks):
    """Test that time range properties are maintained."""
    summary = summarize_task_chain(tasks)
    
    # Convert timestamps to datetime objects
    task_times = [
        datetime.fromisoformat(task["timestamp"])
        for task in tasks
    ]
    summary_start = datetime.fromisoformat(summary.start_time)
    summary_end = datetime.fromisoformat(summary.end_time)
    
    # Property 1: Summary time range encompasses all task timestamps
    assert summary_start <= min(task_times)
    assert summary_end >= max(task_times)
    
    # Property 2: Time range is chronologically valid
    assert summary_start <= summary_end

@settings(max_examples=50)
@given(
    tasks=task_list_strategy(),
    phase=st.from_regex(r'P[0-9][A-Z]TEST')
)
def test_phase_filtering_property(tasks, phase):
    """Test phase filtering properties."""
    # Set some tasks to the target phase
    for i, task in enumerate(tasks):
        if i % 2 == 0:  # Set every other task to target phase
            task["phase_id"] = phase
    
    # Get summary for specific phase
    phase_tasks = [t for t in tasks if t["phase_id"] == phase]
    if phase_tasks:
        summary = summarize_task_chain(tasks, phase)
        
        # Property 1: Only includes tasks from specified phase
        assert summary.phase_id == phase
        assert summary.total_tasks == len(phase_tasks)
        
        # Property 2: Priority distribution matches phase tasks
        total_priorities = sum(summary.priority_distribution.values())
        assert total_priorities == len(phase_tasks)
    else:
        # Property 3: Raises error when no tasks match phase
        with pytest.raises(ValueError, match=f"No tasks found for phase {phase}"):
            summarize_task_chain(tasks, phase)

@settings(max_examples=50)
@given(tasks=task_list_strategy())
def test_invariant_properties(tasks):
    """Test invariant properties of task summaries."""
    summary = summarize_task_chain(tasks)
    
    # Property 1: Priority levels are valid
    assert all(p in PRIORITY_LEVELS for p in summary.priority_distribution)
    
    # Property 2: Section codes are valid
    assert all(s in SECTION_CODES for s in summary.section_coverage)
    
    # Property 3: Consensus status values are valid
    valid_statuses = {"pending", "approved", "rejected"}
    assert all(s in valid_statuses for s in summary.consensus_status)
    
    # Property 4: Completion rate is between 0 and 100
    assert 0 <= summary.completion_rate <= 100
    
    # Property 5: Agent roles are consistent
    for agent_roles in summary.agent_distribution.values():
        assert all(role in ["generate_draft", "review_draft"] for role in agent_roles)

if __name__ == "__main__":
    pytest.main([__file__]) 