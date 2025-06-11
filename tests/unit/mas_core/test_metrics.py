"""
Unit tests for metrics collection and monitoring.
"""

import asyncio
import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock
from mas_core.metrics import (
    MetricsCollector,
    TaskMetrics,
    ConsensusMetrics,
    SystemMetrics
)

@pytest.fixture
def metrics_collector():
    """Test metrics collector instance."""
    return MetricsCollector()

@pytest.fixture
def task_metrics():
    """Test task metrics instance."""
    return TaskMetrics()

@pytest.fixture
def consensus_metrics():
    """Test consensus metrics instance."""
    return ConsensusMetrics()

@pytest.fixture
def system_metrics():
    """Test system metrics instance."""
    return SystemMetrics()

class TestTaskMetrics:
    """Test task metrics data structure."""
    
    def test_task_metrics_initialization(self, task_metrics):
        """Test task metrics default initialization."""
        assert task_metrics.total_tasks == 0
        assert task_metrics.completed_tasks == 0
        assert task_metrics.failed_tasks == 0
        assert task_metrics.current_concurrent == 0
        assert task_metrics.max_concurrent_seen == 0
        assert task_metrics.avg_completion_time == 0.0
        assert task_metrics.task_times == []
        
    def test_task_metrics_post_init(self):
        """Test task metrics post initialization."""
        metrics = TaskMetrics()
        assert isinstance(metrics.task_times, list)
        assert len(metrics.task_times) == 0

class TestConsensusMetrics:
    """Test consensus metrics data structure."""
    
    def test_consensus_metrics_initialization(self, consensus_metrics):
        """Test consensus metrics default initialization."""
        assert consensus_metrics.total_rounds == 0
        assert consensus_metrics.successful_consensus == 0
        assert consensus_metrics.failed_consensus == 0
        assert consensus_metrics.avg_consensus_time == 0.0
        assert consensus_metrics.consensus_times == []
        
    def test_consensus_metrics_post_init(self):
        """Test consensus metrics post initialization."""
        metrics = ConsensusMetrics()
        assert isinstance(metrics.consensus_times, list)
        assert len(metrics.consensus_times) == 0

class TestSystemMetrics:
    """Test system metrics data structure."""
    
    def test_system_metrics_initialization(self, system_metrics):
        """Test system metrics default initialization."""
        assert system_metrics.cpu_usage == 0.0
        assert system_metrics.memory_usage == 0.0
        assert system_metrics.disk_usage == 0.0
        assert system_metrics.network_io == {"sent": 0.0, "received": 0.0}
        
    def test_system_metrics_post_init(self):
        """Test system metrics post initialization."""
        metrics = SystemMetrics()
        assert isinstance(metrics.network_io, dict)
        assert "sent" in metrics.network_io
        assert "received" in metrics.network_io

class TestMetricsCollector:
    """Test metrics collector functionality."""
    
    def test_metrics_collector_initialization(self, metrics_collector):
        """Test metrics collector initialization."""
        assert isinstance(metrics_collector.task_metrics, TaskMetrics)
        assert isinstance(metrics_collector.consensus_metrics, ConsensusMetrics)
        assert isinstance(metrics_collector.system_metrics, SystemMetrics)
        assert metrics_collector.error_handler is not None
        
    @pytest.mark.asyncio
    async def test_track_task_timing_success(self, metrics_collector):
        """Test task timing decorator with successful execution."""
        @metrics_collector.track_task_timing
        async def mock_task():
            await asyncio.sleep(0.01)  # Small delay to measure
            return True
            
        # Execute tracked function
        result = await mock_task()
        
        # Verify results
        assert result is True
        assert metrics_collector.task_metrics.total_tasks == 1
        assert metrics_collector.task_metrics.completed_tasks == 1
        assert metrics_collector.task_metrics.failed_tasks == 0
        assert metrics_collector.task_metrics.current_concurrent == 0
        assert metrics_collector.task_metrics.max_concurrent_seen == 1
        assert len(metrics_collector.task_metrics.task_times) == 1
        assert metrics_collector.task_metrics.avg_completion_time > 0
        
    @pytest.mark.asyncio
    async def test_track_task_timing_failure_result(self, metrics_collector):
        """Test task timing decorator with false result."""
        @metrics_collector.track_task_timing
        async def mock_task():
            return False
            
        # Execute tracked function
        result = await mock_task()
        
        # Verify results
        assert result is False
        assert metrics_collector.task_metrics.total_tasks == 1
        assert metrics_collector.task_metrics.completed_tasks == 0
        assert metrics_collector.task_metrics.failed_tasks == 1
        
    @pytest.mark.asyncio
    async def test_track_task_timing_exception(self, metrics_collector):
        """Test task timing decorator with exception."""
        @metrics_collector.track_task_timing
        async def mock_task():
            raise ValueError("Test error")
            
        # Execute tracked function and expect exception
        with pytest.raises(ValueError, match="Test error"):
            await mock_task()
        
        # Verify metrics updated correctly
        assert metrics_collector.task_metrics.total_tasks == 1
        assert metrics_collector.task_metrics.completed_tasks == 0
        assert metrics_collector.task_metrics.failed_tasks == 1
        assert metrics_collector.task_metrics.current_concurrent == 0
        
    @pytest.mark.asyncio
    async def test_track_consensus_timing_success(self, metrics_collector):
        """Test consensus timing decorator with successful execution."""
        @metrics_collector.track_consensus_timing
        async def mock_consensus():
            await asyncio.sleep(0.01)
            return {"result": "approved"}
            
        # Execute tracked function
        result = await mock_consensus()
        
        # Verify results
        assert result == {"result": "approved"}
        assert metrics_collector.consensus_metrics.total_rounds == 1
        assert metrics_collector.consensus_metrics.successful_consensus == 1
        assert metrics_collector.consensus_metrics.failed_consensus == 0
        assert len(metrics_collector.consensus_metrics.consensus_times) == 1
        assert metrics_collector.consensus_metrics.avg_consensus_time > 0
        
    @pytest.mark.asyncio
    async def test_track_consensus_timing_exception(self, metrics_collector):
        """Test consensus timing decorator with exception."""
        @metrics_collector.track_consensus_timing
        async def mock_consensus():
            raise RuntimeError("Consensus timeout")
            
        # Execute tracked function and expect exception
        with pytest.raises(RuntimeError, match="Consensus timeout"):
            await mock_consensus()
        
        # Verify metrics updated correctly
        assert metrics_collector.consensus_metrics.total_rounds == 1
        assert metrics_collector.consensus_metrics.successful_consensus == 0
        assert metrics_collector.consensus_metrics.failed_consensus == 1
        
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    def test_update_system_metrics_success(self, mock_net, mock_disk, mock_memory, mock_cpu, metrics_collector):
        """Test successful system metrics update."""
        # Mock system calls
        mock_cpu.return_value = 25.5
        mock_memory.return_value = MagicMock(percent=60.2)
        mock_disk.return_value = MagicMock(percent=45.8)
        mock_net.return_value = MagicMock(bytes_sent=1024, bytes_recv=2048)
        
        # Update metrics
        metrics_collector.update_system_metrics()
        
        # Verify results
        assert metrics_collector.system_metrics.cpu_usage == 25.5
        assert metrics_collector.system_metrics.memory_usage == 60.2
        assert metrics_collector.system_metrics.disk_usage == 45.8
        assert metrics_collector.system_metrics.network_io["sent"] == 1024
        assert metrics_collector.system_metrics.network_io["received"] == 2048
        
    @patch('psutil.cpu_percent')
    def test_update_system_metrics_exception(self, mock_cpu, metrics_collector):
        """Test system metrics update with exception."""
        # Mock exception
        mock_cpu.side_effect = Exception("System error")
        
        # Update metrics should handle exception gracefully
        metrics_collector.update_system_metrics()
        
        # Metrics should remain at default values
        assert metrics_collector.system_metrics.cpu_usage == 0.0
        
    @patch('mas_core.metrics.MetricsCollector.update_system_metrics')
    def test_get_metrics_summary(self, mock_update, metrics_collector):
        """Test metrics summary generation."""
        # Set up test data
        metrics_collector.task_metrics.total_tasks = 10
        metrics_collector.task_metrics.completed_tasks = 8
        metrics_collector.task_metrics.failed_tasks = 2
        metrics_collector.task_metrics.current_concurrent = 3
        metrics_collector.task_metrics.max_concurrent_seen = 5
        metrics_collector.task_metrics.avg_completion_time = 1.25
        
        metrics_collector.consensus_metrics.total_rounds = 5
        metrics_collector.consensus_metrics.successful_consensus = 4
        metrics_collector.consensus_metrics.failed_consensus = 1
        metrics_collector.consensus_metrics.avg_consensus_time = 2.5
        
        metrics_collector.system_metrics.cpu_usage = 30.0
        metrics_collector.system_metrics.memory_usage = 65.0
        
        # Get summary
        summary = metrics_collector.get_metrics_summary()
        
        # Verify structure and content
        assert "timestamp" in summary
        assert "task_metrics" in summary
        assert "consensus_metrics" in summary
        assert "system_metrics" in summary
        
        # Verify task metrics
        task_metrics = summary["task_metrics"]
        assert task_metrics["total"] == 10
        assert task_metrics["completed"] == 8
        assert task_metrics["failed"] == 2
        assert task_metrics["current_concurrent"] == 3
        assert task_metrics["max_concurrent"] == 5
        assert task_metrics["avg_completion_time"] == 1.25
        
        # Verify consensus metrics
        consensus_metrics = summary["consensus_metrics"]
        assert consensus_metrics["total_rounds"] == 5
        assert consensus_metrics["successful"] == 4
        assert consensus_metrics["failed"] == 1
        assert consensus_metrics["avg_consensus_time"] == 2.5
        
        # Verify system metrics
        system_metrics = summary["system_metrics"]
        assert system_metrics["cpu_usage"] == 30.0
        assert system_metrics["memory_usage"] == 65.0
        
    def test_log_metrics(self, metrics_collector):
        """Test metrics logging functionality."""
        with patch.object(metrics_collector, 'get_metrics_summary') as mock_summary:
            mock_summary.return_value = {"test": "data"}
            
            # Should not raise exception
            metrics_collector.log_metrics()
            
            # Should call get_metrics_summary
            mock_summary.assert_called_once()
            
    def test_get_metrics(self, metrics_collector):
        """Test get_metrics method."""
        metrics = metrics_collector.get_metrics()
        
        assert "task_metrics" in metrics
        assert "consensus_metrics" in metrics
        assert "system_metrics" in metrics
        assert isinstance(metrics["task_metrics"], TaskMetrics)
        assert isinstance(metrics["consensus_metrics"], ConsensusMetrics)
        assert isinstance(metrics["system_metrics"], SystemMetrics)
        
    def test_get_metrics_by_function(self, metrics_collector):
        """Test get_metrics_by_function method."""
        # This method has limited functionality in current implementation
        result = metrics_collector.get_metrics_by_function("test_function")
        assert isinstance(result, list)
        
    def test_clear_metrics(self, metrics_collector):
        """Test metrics clearing functionality."""
        # Set some test data
        metrics_collector.task_metrics.total_tasks = 10
        metrics_collector.consensus_metrics.total_rounds = 5
        metrics_collector.system_metrics.cpu_usage = 50.0
        
        # Clear metrics
        metrics_collector.clear_metrics()
        
        # Verify all metrics are reset
        assert metrics_collector.task_metrics.total_tasks == 0
        assert metrics_collector.consensus_metrics.total_rounds == 0
        assert metrics_collector.system_metrics.cpu_usage == 0.0
        
    @pytest.mark.asyncio
    async def test_concurrent_task_tracking(self, metrics_collector):
        """Test concurrent task tracking."""
        @metrics_collector.track_task_timing
        async def slow_task(duration):
            await asyncio.sleep(duration)
            return True
            
        # Start multiple tasks concurrently
        tasks = [
            asyncio.create_task(slow_task(0.05)),
            asyncio.create_task(slow_task(0.05)),
            asyncio.create_task(slow_task(0.05))
        ]
        
        # Wait for completion
        await asyncio.gather(*tasks)
        
        # Verify metrics
        assert metrics_collector.task_metrics.total_tasks == 3
        assert metrics_collector.task_metrics.completed_tasks == 3
        assert metrics_collector.task_metrics.max_concurrent_seen >= 2  # Should track concurrent execution
        assert metrics_collector.task_metrics.current_concurrent == 0  # Should be 0 after completion
        
    @pytest.mark.asyncio
    async def test_mixed_task_results(self, metrics_collector):
        """Test tracking of mixed success/failure results."""
        @metrics_collector.track_task_timing
        async def variable_task(should_succeed, should_raise=False):
            if should_raise:
                raise ValueError("Intentional error")
            return should_succeed
            
        # Execute various scenarios
        result1 = await variable_task(True)  # Success
        result2 = await variable_task(False)  # Failure (False result)
        
        try:
            await variable_task(True, should_raise=True)  # Exception
        except ValueError:
            pass
            
        # Verify metrics
        assert metrics_collector.task_metrics.total_tasks == 3
        assert metrics_collector.task_metrics.completed_tasks == 1
        assert metrics_collector.task_metrics.failed_tasks == 2 