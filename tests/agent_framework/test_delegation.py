#!/usr/bin/env python3
"""Test suite for agent delegation system."""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Set

from agent_framework.router import DelegationRouter, RoutePolicy, CLIDelegator
from agent_framework.communication import AgentCommunicator, AgentMessage
from agent_framework.agent import TaskProcessingAgent, AgentCapability

@pytest.fixture
async def router():
    """Create a test router instance."""
    router = DelegationRouter()
    
    # Register test policies
    router.register_policy(RoutePolicy(
        capability_name="test_capability",
        priority=1,
        requirements={"python", "test"},
        max_concurrent=2,
        timeout_seconds=30
    ))
    
    yield router

@pytest.fixture
async def test_agent():
    """Create a test agent instance."""
    capabilities = [
        AgentCapability(
            name="test_capability",
            handler=lambda x: x,
            requirements=["python", "test"],
            description="Test capability"
        )
    ]
    
    agent = TaskProcessingAgent("test_agent_1", capabilities)
    await agent.initialize()
    
    yield agent
    
    await agent.shutdown()

@pytest.fixture
async def communicator():
    """Create a test communicator instance."""
    return AgentCommunicator("test_agent_1")

async def test_policy_registration(router):
    """Test policy registration and validation."""
    policy = RoutePolicy(
        capability_name="new_capability",
        priority=2,
        requirements={"python", "advanced"},
        max_concurrent=5,
        timeout_seconds=60
    )
    
    router.register_policy(policy)
    assert "new_capability" in router.policies
    assert router.policies["new_capability"].priority == 2
    assert router.policies["new_capability"].max_concurrent == 5

async def test_agent_registration(router):
    """Test agent registration and capability matching."""
    router.register_agent("test_agent_1", ["test_capability"])
    assert "test_agent_1" in router.agent_loads
    assert "test_capability" in router.active_routes
    assert "test_agent_1" in router.active_routes["test_capability"]

async def test_task_delegation(router):
    """Test task delegation process."""
    router.register_agent("test_agent_1", ["test_capability"])
    
    task = {
        "task_id": "test_task_1",
        "type": "test_capability",
        "requirements": ["python", "test"],
        "data": {"test": "data"}
    }
    
    agent_id = await router.delegate_task(task)
    assert agent_id == "test_agent_1"
    assert router.agent_loads["test_agent_1"] == 1

async def test_load_balancing(router):
    """Test load balancing between agents."""
    # Register multiple agents
    agents = ["agent_1", "agent_2", "agent_3"]
    for agent_id in agents:
        router.register_agent(agent_id, ["test_capability"])
    
    # Create multiple tasks
    tasks = []
    for i in range(6):
        tasks.append({
            "task_id": f"task_{i}",
            "type": "test_capability",
            "requirements": ["python", "test"],
            "data": {"test": "data"}
        })
    
    # Delegate tasks
    assignments = []
    for task in tasks:
        agent_id = await router.delegate_task(task)
        assignments.append(agent_id)
    
    # Verify load distribution
    loads = [assignments.count(agent_id) for agent_id in agents]
    assert max(loads) - min(loads) <= 1  # Load should be balanced

async def test_agent_communication(communicator):
    """Test agent communication system."""
    # Register message handler
    received_messages = []
    
    async def test_handler(message: AgentMessage):
        received_messages.append(message)
        return {"status": "received"}
    
    communicator.register_handler("test_message", test_handler)
    
    # Send test message
    response = await communicator.send_message(
        recipient_id="test_agent_2",
        message_type="test_message",
        content={"test": "data"},
        requires_response=True
    )
    
    assert response is not None
    assert len(received_messages) == 0  # No messages received yet
    
    # Process incoming messages
    message_processor = asyncio.create_task(communicator.process_incoming_messages())
    await asyncio.sleep(2)  # Allow time for processing
    
    # Verify message handling
    assert len(received_messages) > 0
    message_processor.cancel()

async def test_cli_delegation(router):
    """Test CLI-based task delegation."""
    cli = CLIDelegator(router)
    router.register_agent("test_agent_1", ["test_capability"])
    
    # Create test task file
    task_file = Path("test_tasks.json")
    tasks = [
        {
            "task_id": "cli_task_1",
            "type": "test_capability",
            "requirements": ["python", "test"],
            "data": {"test": "data"}
        },
        {
            "task_id": "cli_task_2",
            "type": "test_capability",
            "requirements": ["python", "test"],
            "data": {"test": "more_data"}
        }
    ]
    
    with task_file.open('w') as f:
        json.dump(tasks, f)
    
    # Test delegation
    success = await cli.delegate_from_file(task_file)
    assert success
    
    # Verify delegation results
    result_file = Path("delegation_test_tasks.json")
    assert result_file.exists()
    
    with result_file.open('r') as f:
        results = json.load(f)
    
    assert len(results) == 2
    assert all(r["delegated_to"] == "test_agent_1" for r in results)
    
    # Cleanup
    task_file.unlink()
    result_file.unlink()

async def test_end_to_end_delegation(router, test_agent, communicator):
    """Test end-to-end task delegation and processing."""
    # Register agent with router
    router.register_agent(test_agent.agent_id, ["test_capability"])
    
    # Create and register communication handler
    async def task_handler(message: AgentMessage):
        task = message.content
        success = await test_agent.process_task(task)
        return {"success": success}
    
    communicator.register_handler("task_assignment", task_handler)
    
    # Create test task
    task = {
        "task_id": "end_to_end_task",
        "type": "test_capability",
        "requirements": ["python", "test"],
        "data": {"test": "end_to_end"}
    }
    
    # Delegate task
    agent_id = await router.delegate_task(task)
    assert agent_id == test_agent.agent_id
    
    # Verify agent state
    assert test_agent.state.tasks_processed == 1
    assert len(test_agent.state.completed_tasks) == 1
    assert test_agent.state.completed_tasks[0]["task_id"] == "end_to_end_task"

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 