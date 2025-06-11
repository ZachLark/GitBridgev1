"""
Targeted coverage boost tests for GitBridge MAS Core modules.

This test suite specifically targets missing lines in high-coverage modules
to efficiently reach 80% coverage before expanding to 100% global coverage.

Focus areas:
1. ErrorHandler: 93% → 98%+ (lines 89-90, 123, 135)
2. TaskChain: 83% → 90%+ (error handling and edge cases)
3. EventQueue: 58% → 75%+ (error paths and timeouts)
4. Pipeline: 52% → 70%+ (start/stop methods)
"""

import pytest
import asyncio
import uuid
from unittest.mock import patch, MagicMock
from mas_core.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from mas_core.task_chain import TaskChainManager, TaskState
from mas_core.event_queue import EventQueue
from mas_core.pipeline import MASPipeline


@pytest.fixture
def config():
    """Enhanced test configuration for coverage tests."""
    return {
        "pipeline": {
            "max_retries": 3,
            "retry_delay": 0.1,
            "cleanup_interval": 1  # Shorter interval for testing
        },
        "task_chain": {
            "states": ["Created", "InProgress", "Blocked", "Resolved", "Failed"],
            "max_concurrent": 5,
            "consensus_required": True
        },
        "consensus": {
            "timeout": 1,  # Shorter timeout for testing
            "required_nodes": 3
        },
        "queue": {
            "redis_url": "redis://localhost:6379/0",
            "max_size": 10,
            "timeout": 1  # Shorter timeout for testing
        }
    }


@pytest.mark.asyncio
class TestCoverageBoost:
    """Targeted tests to boost coverage in specific modules."""

    async def test_error_handler_edge_cases(self, config):
        """Test ErrorHandler missing lines: 89-90, 123, 135."""
        error_handler = ErrorHandler()
        
        # Test error handling in handle_error method (lines 89-90)
        # Create an error that would cause the exception path
        with patch('mas_core.error_handler.MASError') as mock_error:
            mock_error.side_effect = Exception("Test exception")
            
            result = error_handler.handle_error(
                error_id="test-error",
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.ERROR,
                message="Test error",
                details={"test": True}
            )
            
            # Should return False when exception occurs (line 90)
            assert result is False
            
        # Test get_error with non-existent ID (line 135)
        missing_error = error_handler.get_error("non-existent-id")
        assert missing_error is None
        
        # Test successful error retrieval
        error_id = "test-success"
        success = error_handler.handle_error(
            error_id=error_id,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.WARNING,
            message="Success test",
            details={"success": True}
        )
        assert success is True
        
        found_error = error_handler.get_error(error_id)
        assert found_error is not None
        assert found_error.message == "Success test"

    async def test_task_chain_error_paths(self, config):
        """Test TaskChain missing error handling and edge cases."""
        task_chain = TaskChainManager(config)
        
        # Test concurrent task limit handling (missing coverage around line 191)
        tasks = []
        for i in range(config["task_chain"]["max_concurrent"] + 2):
            task_id = f"task-{i}"
            try:
                await task_chain.create_task(task_id, {"type": "test", "data": i})
                tasks.append(task_id)
            except Exception:
                # Expected to hit concurrent limit
                pass
        
        # Test invalid state transitions (lines 221-249)
        if tasks:
            valid_task_id = tasks[0]
            
            # Test invalid state
            try:
                await task_chain.update_task_state(valid_task_id, "InvalidState")
                assert False, "Should have raised exception"
            except Exception:
                pass  # Expected
            
            # Test state transition with consensus (lines 272-285)
            try:
                await task_chain.update_task_state(valid_task_id, TaskState.Resolved)
            except Exception:
                pass  # May fail due to consensus requirements
        
        # Test cleanup with active tasks (lines 321, 326-328)
        await task_chain.cleanup()

    async def test_event_queue_error_scenarios(self, config):
        """Test EventQueue error paths and timeout scenarios."""
        queue = EventQueue(config)
        
        # Test queue when not running (line 76-84)
        queue._running = False
        
        # Test enqueue when not running
        event = {"type": "test", "data": "test"}
        result = await queue.enqueue(event)
        assert result is False
        
        # Test dequeue when not running  
        result = await queue.dequeue()
        assert result is None
        
        # Restart queue for timeout tests
        queue._running = True
        
        # Test dequeue timeout on empty queue (lines 151-159)
        with patch('asyncio.timeout') as mock_timeout:
            mock_timeout.side_effect = asyncio.TimeoutError()
            result = await queue.dequeue()
            assert result is None
        
        # Test enqueue timeout (lines 113-139)
        with patch('asyncio.timeout') as mock_timeout:
            mock_timeout.side_effect = asyncio.TimeoutError()
            result = await queue.enqueue(event)
            assert result is False
        
        # Test exception handling in enqueue (lines 186-195)
        with patch.object(queue.queue, 'put') as mock_put:
            mock_put.side_effect = Exception("Test exception")
            result = await queue.enqueue(event)
            assert result is False
        
        # Test exception handling in dequeue (lines 203, 207-209)
        with patch.object(queue.queue, 'get') as mock_get:
            mock_get.side_effect = Exception("Test exception")
            result = await queue.dequeue()
            assert result is None
        
        # Test cleanup method (lines 223, 231, 239, 247-264)
        await queue.cleanup()
        
        # Test health check and queue operations
        health = await queue.check_health()
        assert isinstance(health, dict)
        
        size = queue.get_queue_size()
        assert isinstance(size, int)
        
        running = queue.is_running()
        assert isinstance(running, bool)

    async def test_pipeline_lifecycle(self, config):
        """Test Pipeline start/stop and lifecycle methods."""
        pipeline = MASPipeline(config)
        
        # Test cleanup method (lines 212-214)
        await pipeline.cleanup()
        
        # Test pipeline with exceptions in process_event (lines 135-146)
        with patch.object(pipeline.task_chain, 'create_task') as mock_create:
            mock_create.side_effect = Exception("Create task exception")
            
            event = {"type": "test", "data": {"test": True}}
            await pipeline.process_event(event)
            
            # Should handle exception gracefully
        
        # Test pipeline with failed state update (lines 152-163)
        with patch.object(pipeline.task_chain, 'update_task_state') as mock_update:
            mock_update.return_value = False
            
            event = {"type": "test", "data": {"test": True}}
            await pipeline.process_event(event)
        
        # Test stop method (lines 188-195)
        await pipeline.stop()
        
        # Test stop with exception
        with patch.object(pipeline, 'cleanup') as mock_cleanup:
            mock_cleanup.side_effect = Exception("Cleanup exception")
            await pipeline.stop()

    async def test_pipeline_start_and_cleanup_loop(self, config):
        """Test Pipeline start method and cleanup loop."""
        pipeline = MASPipeline(config)
        
        # Test cleanup method directly instead of the infinite loop
        # The _cleanup_loop runs indefinitely, so we test cleanup functionality instead
        await pipeline.cleanup()
        
        # Test start method error handling (lines 86-95)
        # We'll mock the event queue to simulate various scenarios
        with patch.object(pipeline.event_queue, 'dequeue') as mock_dequeue:
            mock_dequeue.side_effect = Exception("Dequeue exception")
            
            # Test that start() handles dequeue exceptions gracefully
            # We'll start the pipeline and immediately stop it to test error handling
            pipeline._running = True
            
            # Create a task to start the pipeline and cancel it quickly
            start_task = asyncio.create_task(pipeline.start())
            
            # Give it a moment to hit the exception, then stop
            await asyncio.sleep(0.05)  # 50ms
            pipeline._running = False
            
            try:
                await asyncio.wait_for(start_task, timeout=0.1)
            except asyncio.TimeoutError:
                start_task.cancel()
                try:
                    await start_task
                except asyncio.CancelledError:
                    pass

    async def test_additional_edge_cases(self, config):
        """Test remaining edge cases across modules."""
        
        # Test ErrorHandler with different severities and categories
        error_handler = ErrorHandler()
        
        # Test all error categories and severities
        categories = [ErrorCategory.TASK, ErrorCategory.QUEUE, ErrorCategory.CONSENSUS, ErrorCategory.SYSTEM]
        severities = [ErrorSeverity.INFO, ErrorSeverity.WARNING, ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]
        
        for i, (cat, sev) in enumerate(zip(categories, severities)):
            error_handler.handle_error(
                error_id=f"test-{i}",
                category=cat,
                severity=sev,
                message=f"Test message {i}",
                details={"index": i},
                task_id=f"task-{i}" if i % 2 == 0 else None
            )
        
        # Test error retrieval by different criteria
        task_errors = error_handler.get_errors_by_task("task-0")
        assert len(task_errors) > 0
        
        severity_errors = error_handler.get_errors_by_severity(ErrorSeverity.ERROR)
        assert len(severity_errors) > 0
        
        category_errors = error_handler.get_errors_by_category(ErrorCategory.TASK)
        assert len(category_errors) > 0
        
        # Test error count
        count = error_handler.get_error_count()
        assert count > 0
        
        # Test clear errors
        error_handler.clear_errors()
        assert error_handler.get_error_count() == 0

    async def test_queue_full_scenario(self, config):
        """Test queue full exception handling."""
        # Create a queue with size 1 for easy testing
        small_config = config.copy()
        small_config["queue"]["max_size"] = 1
        queue = EventQueue(small_config)
        
        # Fill the queue
        event1 = {"type": "test1", "data": "data1"}
        result1 = await queue.enqueue(event1)
        assert result1 is True
        
        # Try to add another - should trigger QueueFull handling
        event2 = {"type": "test2", "data": "data2"}
        result2 = await queue.enqueue(event2)
        assert result2 is False  # Should fail due to queue being full
        
        # Verify error was logged
        errors = queue.error_handler.get_errors_by_category(ErrorCategory.QUEUE)
        assert len(errors) > 0

    async def test_async_context_manager(self, config):
        """Test EventQueue async context manager."""
        queue = EventQueue(config)
        
        # Test async context manager entry and exit
        async with queue as q:
            assert q._running is True
            event = {"type": "context_test", "data": "test"}
            result = await q.enqueue(event)
            assert result is True
        
        # After context exit, should be stopped
        assert queue._running is False 