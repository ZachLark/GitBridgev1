"""
Unit tests for error handler.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from mas_core.error_handler import (
    ErrorHandler,
    MASError,
    ErrorCategory,
    ErrorSeverity
)


class TestErrorHandler:
    """Test error handler functionality."""

    @pytest.fixture
    def error_handler(self):
        """Create error handler instance."""
        return ErrorHandler()

    @pytest.fixture
    def sample_error_data(self):
        """Provide sample error data."""
        return {
            "error_id": "err_001",
            "category": ErrorCategory.TASK,
            "severity": ErrorSeverity.ERROR,
            "message": "Test error",
            "details": {"test": "context"},
            "task_id": "task_001"
        }

    def test_error_handler_initialization(self, error_handler):
        """Test error handler initialization."""
        assert error_handler.error_log == []
        assert error_handler.get_error_count() == 0

    def test_handle_error_success(self, error_handler, sample_error_data):
        """Test successful error handling."""
        result = error_handler.handle_error(**sample_error_data)
        
        assert result is True
        assert error_handler.get_error_count() == 1
        
        error = error_handler.get_error("err_001")
        assert error is not None
        assert error.error_id == "err_001"
        assert error.error_type == ErrorCategory.TASK
        assert error.severity == ErrorSeverity.ERROR
        assert error.message == "Test error"
        assert error.context == {"test": "context"}
        assert error.task_id == "task_001"
        assert error.recovery_attempted is False
        assert error.recovery_successful is False

    def test_handle_error_without_task_id(self, error_handler):
        """Test error handling without task ID."""
        result = error_handler.handle_error(
            error_id="err_002",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            message="System error",
            details={"component": "database"}
        )
        
        assert result is True
        error = error_handler.get_error("err_002")
        assert error.task_id is None

    def test_handle_multiple_errors(self, error_handler):
        """Test handling multiple errors."""
        errors_data = [
            {
                "error_id": "err_001",
                "category": ErrorCategory.TASK,
                "severity": ErrorSeverity.ERROR,
                "message": "Task error",
                "details": {}
            },
            {
                "error_id": "err_002",
                "category": ErrorCategory.QUEUE,
                "severity": ErrorSeverity.WARNING,
                "message": "Queue warning",
                "details": {}
            },
            {
                "error_id": "err_003",
                "category": ErrorCategory.CONSENSUS,
                "severity": ErrorSeverity.CRITICAL,
                "message": "Consensus failure",
                "details": {}
            }
        ]
        
        for error_data in errors_data:
            result = error_handler.handle_error(**error_data)
            assert result is True
        
        assert error_handler.get_error_count() == 3

    def test_get_errors_by_category(self, error_handler):
        """Test getting errors by category."""
        # Add errors of different categories
        error_handler.handle_error(
            "err_001", ErrorCategory.TASK, ErrorSeverity.ERROR, "Task error 1", {}
        )
        error_handler.handle_error(
            "err_002", ErrorCategory.TASK, ErrorSeverity.WARNING, "Task error 2", {}
        )
        error_handler.handle_error(
            "err_003", ErrorCategory.QUEUE, ErrorSeverity.ERROR, "Queue error", {}
        )
        
        task_errors = error_handler.get_errors_by_category(ErrorCategory.TASK)
        queue_errors = error_handler.get_errors_by_category(ErrorCategory.QUEUE)
        
        assert len(task_errors) == 2
        assert len(queue_errors) == 1
        assert all(error.error_type == ErrorCategory.TASK for error in task_errors)
        assert all(error.error_type == ErrorCategory.QUEUE for error in queue_errors)

    def test_get_errors_by_severity(self, error_handler):
        """Test getting errors by severity."""
        # Add errors of different severities
        error_handler.handle_error(
            "err_001", ErrorCategory.TASK, ErrorSeverity.ERROR, "Error 1", {}
        )
        error_handler.handle_error(
            "err_002", ErrorCategory.TASK, ErrorSeverity.ERROR, "Error 2", {}
        )
        error_handler.handle_error(
            "err_003", ErrorCategory.TASK, ErrorSeverity.WARNING, "Warning", {}
        )
        error_handler.handle_error(
            "err_004", ErrorCategory.TASK, ErrorSeverity.CRITICAL, "Critical", {}
        )
        
        error_errors = error_handler.get_errors_by_severity(ErrorSeverity.ERROR)
        warning_errors = error_handler.get_errors_by_severity(ErrorSeverity.WARNING)
        critical_errors = error_handler.get_errors_by_severity(ErrorSeverity.CRITICAL)
        
        assert len(error_errors) == 2
        assert len(warning_errors) == 1
        assert len(critical_errors) == 1

    def test_get_errors_by_task(self, error_handler):
        """Test getting errors by task."""
        # Add errors for different tasks
        error_handler.handle_error(
            "err_001", ErrorCategory.TASK, ErrorSeverity.ERROR, "Error 1", {}, "task_001"
        )
        error_handler.handle_error(
            "err_002", ErrorCategory.TASK, ErrorSeverity.ERROR, "Error 2", {}, "task_001"
        )
        error_handler.handle_error(
            "err_003", ErrorCategory.TASK, ErrorSeverity.ERROR, "Error 3", {}, "task_002"
        )
        error_handler.handle_error(
            "err_004", ErrorCategory.TASK, ErrorSeverity.ERROR, "Error 4", {}
        )
        
        task_001_errors = error_handler.get_errors_by_task("task_001")
        task_002_errors = error_handler.get_errors_by_task("task_002")
        task_003_errors = error_handler.get_errors_by_task("task_003")
        
        assert len(task_001_errors) == 2
        assert len(task_002_errors) == 1
        assert len(task_003_errors) == 0

    def test_get_error_by_id(self, error_handler):
        """Test getting error by ID."""
        error_handler.handle_error(
            "err_001", ErrorCategory.TASK, ErrorSeverity.ERROR, "Test error", {"key": "value"}
        )
        
        error = error_handler.get_error("err_001")
        assert error is not None
        assert error.error_id == "err_001"
        assert error.message == "Test error"
        
        # Test non-existent error
        non_existent = error_handler.get_error("err_999")
        assert non_existent is None

    def test_clear_errors(self, error_handler):
        """Test clearing errors."""
        # Add some errors
        error_handler.handle_error(
            "err_001", ErrorCategory.TASK, ErrorSeverity.ERROR, "Error 1", {}
        )
        error_handler.handle_error(
            "err_002", ErrorCategory.QUEUE, ErrorSeverity.WARNING, "Error 2", {}
        )
        
        assert error_handler.get_error_count() == 2
        
        error_handler.clear_errors()
        
        assert error_handler.get_error_count() == 0
        assert error_handler.error_log == []

    def test_error_categories(self):
        """Test error categories enum."""
        assert ErrorCategory.TASK == "task"
        assert ErrorCategory.QUEUE == "queue"
        assert ErrorCategory.CONSENSUS == "consensus"
        assert ErrorCategory.METRICS == "metrics"
        assert ErrorCategory.SYSTEM == "system"

    def test_error_severities(self):
        """Test error severities enum."""
        assert ErrorSeverity.INFO == "info"
        assert ErrorSeverity.WARNING == "warning"
        assert ErrorSeverity.ERROR == "error"
        assert ErrorSeverity.CRITICAL == "critical"

    def test_mas_error_dataclass(self):
        """Test MASError dataclass."""
        error = MASError(
            error_id="test_001",
            error_type=ErrorCategory.TASK,
            message="Test message",
            timestamp="2023-01-01T00:00:00Z",
            context={"key": "value"},
            severity=ErrorSeverity.ERROR,
            task_id="task_001"
        )
        
        assert error.error_id == "test_001"
        assert error.error_type == ErrorCategory.TASK
        assert error.message == "Test message"
        assert error.timestamp == "2023-01-01T00:00:00Z"
        assert error.context == {"key": "value"}
        assert error.severity == ErrorSeverity.ERROR
        assert error.task_id == "task_001"
        assert error.recovery_attempted is False
        assert error.recovery_successful is False

    def test_mas_error_defaults(self):
        """Test MASError default values."""
        error = MASError(
            error_id="test_001",
            error_type=ErrorCategory.TASK,
            message="Test message",
            timestamp="2023-01-01T00:00:00Z",
            context={},
            severity=ErrorSeverity.ERROR
        )
        
        assert error.task_id is None
        assert error.recovery_attempted is False
        assert error.recovery_successful is False

    def test_error_timestamp_format(self, error_handler):
        """Test that error timestamps are in ISO format."""
        error_handler.handle_error(
            "err_001", ErrorCategory.TASK, ErrorSeverity.ERROR, "Test error", {}
        )
        
        error = error_handler.get_error("err_001")
        assert error is not None
        
        # Verify timestamp can be parsed as ISO format
        try:
            datetime.fromisoformat(error.timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

    def test_handle_error_exception_handling(self, error_handler):
        """Test error handling when an exception occurs."""
        # Mock datetime to raise an exception, forcing the exception handling path
        with patch('mas_core.error_handler.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("Datetime error")
            result = error_handler.handle_error(
                "err_001",
                ErrorCategory.TASK,
                ErrorSeverity.ERROR,
                "Test message",
                {}
            )
            # The method should return False when an exception occurs
            assert result is False

    def test_empty_category_filters(self, error_handler):
        """Test filtering with no matching errors."""
        error_handler.handle_error(
            "err_001", ErrorCategory.TASK, ErrorSeverity.ERROR, "Test error", {}
        )
        
        # Test categories with no errors
        queue_errors = error_handler.get_errors_by_category(ErrorCategory.QUEUE)
        consensus_errors = error_handler.get_errors_by_category(ErrorCategory.CONSENSUS)
        
        assert len(queue_errors) == 0
        assert len(consensus_errors) == 0

    def test_empty_severity_filters(self, error_handler):
        """Test filtering with no matching severities."""
        error_handler.handle_error(
            "err_001", ErrorCategory.TASK, ErrorSeverity.ERROR, "Test error", {}
        )
        
        # Test severities with no errors
        info_errors = error_handler.get_errors_by_severity(ErrorSeverity.INFO)
        critical_errors = error_handler.get_errors_by_severity(ErrorSeverity.CRITICAL)
        
        assert len(info_errors) == 0
        assert len(critical_errors) == 0 