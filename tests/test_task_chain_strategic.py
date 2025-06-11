"""
Strategic TaskChain tests to boost coverage from 83% to 90%+.

Targets specific missing lines:
- Lines 221-249: Consensus logic and timeout handling
- Lines 272-285: Error handling in update_task_state  
- Lines 321, 326-328: Cleanup exception handling
- Line 191: Concurrent task limit enforcement

MAS Lite Protocol v2.1 compliant task chain tests.
"""

import pytest
import asyncio
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from mas_core.task_chain import (
    TaskChainManager, TaskState, TaskMetadata, TaskSource,
    ConcurrentTaskLimitError, TaskNotFoundError, InvalidStateTransitionError
)
from mas_core.consensus import ConsensusManager, ConsensusState, ConsensusTimeoutError
from mas_core.error_handler import ErrorHandler, ErrorCategory


@pytest.fixture
def config():
    """Test configuration for TaskChain."""
    return {
        "task_chain": {
            "states": ["Created", "InProgress", "Blocked", "Resolved", "Failed"],
            "max_concurrent": 2,  # Low limit for testing
            "consensus_required": True
        },
        "consensus": {
            "timeout": 1,
            "required_nodes": 3
        }
    }


@pytest.mark.asyncio
class TestTaskChainStrategic:
    """Strategic tests targeting missing coverage lines."""

    async def test_consensus_failures_comprehensive(self, config):
        """Test lines 221-249: Comprehensive consensus failure scenarios."""
        task_chain = TaskChainManager(config)
        
        # Create a task and move it to InProgress state first (valid transition to Resolved)
        task_id = "test-consensus-task"
        await task_chain.create_task(task_id, {"type": "consensus_test"})
        # Move to InProgress so we can transition to Resolved
        await task_chain.update_task_state(task_id, TaskState.InProgress)
        
        # Test 1: Consensus rejection (lines 223-227)
        with patch.object(task_chain.consensus_manager, 'get_consensus') as mock_consensus:
            # Mock consensus returning rejected state
            mock_consensus_result = MagicMock()
            mock_consensus_result.state = ConsensusState.Rejected
            mock_consensus.return_value = mock_consensus_result
            
            # This should trigger the consensus rejection path
            result = await task_chain.update_task_state(task_id, TaskState.Resolved)
            assert result is False
            
            # Verify error was logged
            errors = task_chain.error_handler.get_errors_by_category(ErrorCategory.CONSENSUS)
            # Note: This test path doesn't log errors, it just returns False
        
        # Test 2: Consensus timeout with asyncio.TimeoutError (lines 229-237)
        # Reset task state for next test
        task_chain.tasks[task_id].state = TaskState.InProgress
        
        with patch('asyncio.timeout') as mock_timeout:
            mock_timeout.side_effect = asyncio.TimeoutError()
            
            result = await task_chain.update_task_state(task_id, TaskState.Resolved)
            assert result is False
            
            # Verify timeout error was logged
            errors = task_chain.error_handler.get_errors_by_category(ErrorCategory.CONSENSUS)
            assert len(errors) > 0
            assert "timeout" in errors[-1].message.lower()
        
        # Test 3: ConsensusTimeoutError exception (lines 239-247)
        # Reset task state for next test
        task_chain.tasks[task_id].state = TaskState.InProgress
        
        with patch.object(task_chain.consensus_manager, 'get_consensus') as mock_consensus:
            mock_consensus.side_effect = ConsensusTimeoutError("Test consensus timeout")
            
            result = await task_chain.update_task_state(task_id, TaskState.Resolved)
            assert result is False
            
            # Verify ConsensusTimeoutError was logged
            errors = task_chain.error_handler.get_errors_by_category(ErrorCategory.CONSENSUS)
            assert len(errors) > 0
            assert "Test consensus timeout" in errors[-1].message

    async def test_concurrent_task_limit_enforcement(self, config):
        """Test line 191: Concurrent task limit enforcement."""
        task_chain = TaskChainManager(config)
        
        # Create tasks up to the limit (max_concurrent = 2)
        task_ids = []
        for i in range(config["task_chain"]["max_concurrent"]):
            task_id = f"concurrent-task-{i}"
            success = await task_chain.create_task(task_id, {"type": "test", "index": i})
            assert success is True
            task_ids.append(task_id)
        
        # Verify we're at the limit
        active_tasks = task_chain._get_active_tasks()
        assert len(active_tasks) == config["task_chain"]["max_concurrent"]
        
        # Try to create one more task - this should trigger line 191
        with pytest.raises(ConcurrentTaskLimitError):
            await task_chain.create_task("overflow-task", {"type": "overflow"})
        
        # Verify error was logged before exception was raised
        errors = task_chain.error_handler.get_errors_by_category(ErrorCategory.TASK)
        task_errors = [e for e in errors if "Failed to create task" in e.message]
        assert len(task_errors) > 0

    async def test_cleanup_exception_handling(self, config):
        """Test lines 321, 326-328: Cleanup exception handling."""
        task_chain = TaskChainManager(config)
        
        # Create some completed tasks
        task_ids = []
        for i in range(3):
            task_id = f"cleanup-task-{i}"
            await task_chain.create_task(task_id, {"type": "cleanup_test"})
            # Manually set some to completed states
            task_chain.tasks[task_id].state = TaskState.Resolved if i % 2 == 0 else TaskState.Failed
            task_ids.append(task_id)
        
        # Test cleanup with consensus manager exception (lines 326-328)
        with patch.object(task_chain.consensus_manager, 'cleanup') as mock_cleanup:
            mock_cleanup.side_effect = Exception("Consensus cleanup failed")
            
            # This should trigger the exception handling in cleanup
            await task_chain.cleanup()
            
            # Verify error was logged (line 327-328)
            errors = task_chain.error_handler.get_errors_by_category(ErrorCategory.TASK)
            cleanup_errors = [e for e in errors if "Failed to clean up task chain" in e.message]
            assert len(cleanup_errors) > 0
            assert "Consensus cleanup failed" in cleanup_errors[-1].context["error"]

    async def test_state_validation_errors(self, config):
        """Test lines 272-285: State validation and error handling."""
        task_chain = TaskChainManager(config)
        
        # Create a task for testing
        task_id = "state-validation-task"
        await task_chain.create_task(task_id, {"type": "state_test"})
        
        # Test invalid state transition (lines 272-285)
        # Try to go from Created directly to Failed (invalid transition)
        with pytest.raises(InvalidStateTransitionError):
            await task_chain.update_task_state(task_id, TaskState.Failed)
        
        # Verify error was logged before exception
        errors = task_chain.error_handler.get_errors_by_category(ErrorCategory.TASK)
        state_errors = [e for e in errors if "Invalid state transition" in e.message]
        assert len(state_errors) > 0
        
        # Test update_task_state with non-existent task
        with pytest.raises(TaskNotFoundError):
            await task_chain.update_task_state("non-existent-task", TaskState.InProgress)
        
        # Verify error was logged
        errors = task_chain.error_handler.get_errors_by_category(ErrorCategory.TASK)
        not_found_errors = [e for e in errors if "not found" in e.message]
        assert len(not_found_errors) > 0

    async def test_task_creation_edge_cases(self, config):
        """Additional test to ensure comprehensive coverage of create_task error paths."""
        task_chain = TaskChainManager(config)
        
        # Test with empty task_id (should raise ValueError)
        with pytest.raises(ValueError):
            await task_chain.create_task("", {"type": "test"})
        
        # Test with empty data (should raise ValueError)
        with pytest.raises(ValueError):
            await task_chain.create_task("test-task", {})
        
        # Test exception handling in create_task with non-validation error
        with patch.object(task_chain, '_get_current_time') as mock_time:
            mock_time.side_effect = Exception("Time service failed")
            
            # This should trigger general exception handling and return False
            result = await task_chain.create_task("exception-task", {"type": "test"})
            assert result is False
            
            # Verify error was logged
            errors = task_chain.error_handler.get_errors_by_category(ErrorCategory.TASK)
            time_errors = [e for e in errors if "Time service failed" in e.context.get("error", "")]
            assert len(time_errors) > 0 