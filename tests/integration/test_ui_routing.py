"""
Integration tests for UI and routing functionality.
Tests the interaction between UI components and the routing system.

MAS Lite Protocol v2.1 References:
- Section 5.1: Agent Routing
- Section 5.2: Task Distribution
- Section 6.1: UI Integration
"""

import asyncio
import pytest
import pytest_asyncio
from typing import Dict, Any, List
from scripts.task_generator import TaskGenerator, Task
from scripts.ai_router import AIRouter, AgentInfo

# Test configuration
TEST_CONFIG = {
    "routing": {
        "max_concurrent_tasks": 5,
        "task_timeout": 10.0,
        "retry_attempts": 2
    }
}

@pytest.fixture
async def task_generator():
    """Create a task generator instance for testing."""
    generator = TaskGenerator()
    yield generator
    # Cleanup any remaining tasks
    tasks = await generator.get_processing_tasks()
    for task_id in tasks:
        await generator.cleanup_task(task_id)

@pytest.fixture
def ai_router():
    """Create an AI router instance."""
    return AIRouter(TEST_CONFIG)

@pytest_asyncio.fixture
async def test_agents(ai_router) -> List[AgentInfo]:
    """Create and register test agents."""
    agents = [
        AgentInfo(
            id=f"agent_{i}",
            capabilities=["test", "mock"],
            status="available"
        )
        for i in range(3)
    ]
    
    for agent in agents:
        await ai_router.register_agent(agent)
    
    return agents

@pytest.mark.integration
@pytest.mark.asyncio
async def test_task_routing_flow(task_generator, ai_router, test_agents):
    """Test end-to-end task routing flow."""
    # Create and process task
    task_id = "test_task_1"
    task = await task_generator.process_event(
        task_id,
        "test",
        {"data": "test_payload"}
    )
    
    # Route task
    route_result = await task_generator.route_task(task_id, test_agents[0].id)
    assert route_result["status"] == "pending"
    assert route_result["task_id"] == task_id
    assert route_result["agent_target"] == test_agents[0].id
    
    # Verify MAS routing
    mas_result = await ai_router.route_to_mas({
        "id": task_id,
        "type": "test",
        "payload": task.payload
    })
    assert mas_result["status"] in ["pending", "error"]
    assert mas_result["task_id"] == task_id

@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_routing(task_generator, ai_router, test_agents):
    """Test concurrent task routing."""
    # Create multiple tasks
    tasks = []
    for i in range(10):
        task_id = f"concurrent_task_{i}"
        task = await task_generator.process_event(
            task_id,
            "test",
            {"data": f"payload_{i}"}
        )
        tasks.append(task)
    
    # Route tasks concurrently
    route_results = await asyncio.gather(*[
        task_generator.route_task(task.id, test_agents[i % len(test_agents)].id)
        for i, task in enumerate(tasks)
    ])
    
    # Verify results
    for i, result in enumerate(route_results):
        assert result["status"] == "pending"
        assert result["task_id"] == f"concurrent_task_{i}"
        assert result["agent_target"] == test_agents[i % len(test_agents)].id

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_capacity(task_generator, ai_router, test_agents):
    """Test agent capacity limits."""
    agent = test_agents[0]
    tasks = []
    
    # Create tasks up to capacity
    for i in range(TEST_CONFIG["routing"]["max_concurrent_tasks"] + 1):
        task_id = f"capacity_task_{i}"
        task = await task_generator.process_event(
            task_id,
            "test",
            {"data": f"payload_{i}"}
        )
        tasks.append(task)
        
        # Route to MAS
        result = await ai_router.route_to_mas({
            "id": task_id,
            "type": "test",
            "payload": task.payload
        })
        
        if i < TEST_CONFIG["routing"]["max_concurrent_tasks"]:
            assert result["status"] == "pending"
        else:
            assert result["status"] == "error"
            assert "capacity" in result["error"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_status_updates(task_generator, ai_router, test_agents):
    """Test agent status updates during routing."""
    agent = test_agents[0]
    
    # Update agent status
    await ai_router.update_agent_status(agent.id, "busy")
    
    # Attempt to route task
    task_id = "status_task"
    task = await task_generator.process_event(
        task_id,
        "test",
        {"data": "test_payload"}
    )
    
    route_result = await task_generator.route_task(task_id, agent.id)
    assert route_result["status"] == "pending"
    
    # Route to MAS
    mas_result = await ai_router.route_to_mas({
        "id": task_id,
        "type": "test",
        "payload": task.payload
    })
    
    # Should fail due to busy status
    assert mas_result["status"] == "error"
    
    # Update status back to available
    await ai_router.update_agent_status(agent.id, "available")
    
    # Retry routing
    mas_result = await ai_router.route_to_mas({
        "id": task_id,
        "type": "test",
        "payload": task.payload
    })
    
    assert mas_result["status"] == "pending"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling(task_generator, ai_router):
    """Test error handling in routing system."""
    # Try to route to non-existent agent
    task_id = "error_task"
    task = await task_generator.process_event(
        task_id,
        "test",
        {"data": "test_payload"}
    )
    
    route_result = await task_generator.route_task(task_id, "non_existent_agent")
    assert route_result["status"] == "error"
    assert "not found" in route_result.get("error", "")
    
    # Try to route invalid task
    mas_result = await ai_router.route_to_mas({
        "id": "invalid_task",
        # Missing required fields
    })
    assert mas_result["status"] == "error"

@pytest.mark.asyncio
async def test_task_generation(task_generator):
    """Test basic task generation."""
    task = await task_generator.process_event(
        "test_task_001",
        "test_type",
        {"data": "test"}
    )
    assert task.id == "test_task_001"
    assert task.type == "test_type"
    assert task.payload == {"data": "test"}
    assert task.votes == {}

@pytest.mark.asyncio
async def test_vote_sequence_consensus(task_generator):
    """Test vote sequence with clear consensus."""
    task_id = "test_task_002"
    await task_generator.process_event(task_id, "test_type", {"data": "test"})
    
    # Submit votes
    votes = {
        "agent1": 8,
        "agent2": 5,
        "agent3": 3
    }
    
    for agent_id, vote_value in votes.items():
        result = await task_generator.submit_vote(task_id, agent_id, vote_value)
        assert result["status"] == "accepted"
        assert result["task_id"] == task_id
    
    # Route task
    route_result = await task_generator.route_task(task_id, "agent1")
    assert route_result["status"] == "pending"
    assert route_result["agent_target"] == "agent1"
    assert route_result["vote_sequence"] == votes

@pytest.mark.asyncio
async def test_vote_sequence_tie_breaking(task_generator):
    """Test vote sequence tie-breaking."""
    task_id = "test_task_003"
    await task_generator.process_event(task_id, "test_type", {"data": "test"})
    
    # Submit equal votes
    votes = {
        "agent1": 5,
        "agent2": 5,
        "agent3": 3
    }
    
    for agent_id, vote_value in votes.items():
        await task_generator.submit_vote(task_id, agent_id, vote_value)
    
    # Route task - should select agent1 as it's the target
    route_result = await task_generator.route_task(task_id, "agent1")
    assert route_result["status"] == "pending"
    assert route_result["agent_target"] == "agent1"
    
    # Route to non-tied agent - should fail
    route_result = await task_generator.route_task(task_id, "agent3")
    assert route_result["status"] == "error"

@pytest.mark.asyncio
async def test_agent_unavailability(task_generator):
    """Test handling of unavailable agents."""
    task_id = "test_task_004"
    await task_generator.process_event(task_id, "test_type", {"data": "test"})
    
    # Submit votes for unavailable agents
    votes = {
        "offline_agent1": 8,
        "offline_agent2": 5
    }
    
    for agent_id, vote_value in votes.items():
        await task_generator.submit_vote(task_id, agent_id, vote_value)
    
    # Route to available agent
    route_result = await task_generator.route_task(task_id, "available_agent")
    assert route_result["status"] == "pending"
    assert route_result["agent_target"] == "available_agent"

@pytest.mark.asyncio
async def test_invalid_task_data(task_generator):
    """Test handling of invalid task data."""
    with pytest.raises(ValueError):
        await task_generator.process_event("", "test_type", {"data": "test"})
    
    with pytest.raises(ValueError):
        await task_generator.process_event("test_task", "", {"data": "test"})
    
    with pytest.raises(ValueError):
        await task_generator.process_event("test_task", "test_type", "invalid")

@pytest.mark.asyncio
async def test_concurrent_task_processing(task_generator):
    """Test concurrent task processing."""
    async def create_task(task_id: str) -> Task:
        return await task_generator.process_event(
            task_id,
            "test_type",
            {"data": f"test_{task_id}"}
        )
    
    # Create multiple tasks concurrently
    tasks = await asyncio.gather(*[
        create_task(f"concurrent_task_{i}")
        for i in range(5)
    ])
    
    assert len(tasks) == 5
    for i, task in enumerate(tasks):
        assert task.id == f"concurrent_task_{i}"
        assert task.payload["data"] == f"test_concurrent_task_{i}"

@pytest.mark.asyncio
async def test_vote_validation(task_generator):
    """Test vote value validation."""
    task_id = "test_task_005"
    await task_generator.process_event(task_id, "test_type", {"data": "test"})
    
    # Test invalid vote values
    with pytest.raises(ValueError):
        await task_generator.submit_vote(task_id, "agent1", -1)
    
    with pytest.raises(ValueError):
        await task_generator.submit_vote(task_id, "agent1", 11)
    
    # Test valid vote values
    result = await task_generator.submit_vote(task_id, "agent1", 5)
    assert result["status"] == "accepted"
    assert result["task_id"] == task_id
    assert result["current_votes"]["agent1"] == 5

@pytest.mark.asyncio
async def test_task_cleanup(task_generator):
    """Test task cleanup."""
    task_id = "test_task_006"
    await task_generator.process_event(task_id, "test_type", {"data": "test"})
    
    # Submit some votes
    await task_generator.submit_vote(task_id, "agent1", 5)
    await task_generator.submit_vote(task_id, "agent2", 3)
    
    # Verify task is processing
    assert task_generator.is_processing(task_id)
    
    # Clean up task
    await task_generator.cleanup_task(task_id)
    
    # Verify task is cleaned up
    assert not task_generator.is_processing(task_id)
    
    # Attempt to route cleaned up task
    route_result = await task_generator.route_task(task_id, "agent1")
    assert route_result["status"] == "error" 