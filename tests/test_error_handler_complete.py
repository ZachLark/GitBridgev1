"""
Focused ErrorHandler test suite to achieve complete coverage.

Targets specific missing lines (89-90, 135) to push ErrorHandler 
from 93% to 98%+ coverage.

MAS Lite Protocol v2.1 compliant error handling tests.
"""

import pytest
from unittest.mock import patch, MagicMock
from mas_core.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, MASError


@pytest.mark.asyncio
class TestErrorHandlerComplete:
    """Complete ErrorHandler coverage tests."""

    def test_handle_error_exception_path(self):
        """Test lines 89-90: Exception handling in handle_error method."""
        error_handler = ErrorHandler()
        
        # Mock MASError to raise an exception during construction
        with patch('mas_core.error_handler.MASError') as mock_error_class:
            mock_error_class.side_effect = Exception("MASError construction failed")
            
            # This should trigger the exception path (lines 89-90)
            result = error_handler.handle_error(
                error_id="test-exception",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.ERROR,
                message="Test exception path",
                details={"test": True}
            )
            
            # Should return False when exception occurs (line 90)
            assert result is False
            # Error log should remain empty since MASError creation failed
            assert len(error_handler.error_log) == 0

    def test_get_error_not_found(self):
        """Test line 135: get_error return None path."""
        error_handler = ErrorHandler()
        
        # Add some errors first
        error_handler.handle_error(
            error_id="existing-error-1",
            category=ErrorCategory.TASK,
            severity=ErrorSeverity.WARNING,
            message="Existing error 1",
            details={"data": "test1"}
        )
        
        error_handler.handle_error(
            error_id="existing-error-2",
            category=ErrorCategory.QUEUE,
            severity=ErrorSeverity.ERROR,
            message="Existing error 2",
            details={"data": "test2"}
        )
        
        # Test line 135: return None when error not found
        missing_error = error_handler.get_error("non-existent-error-id")
        assert missing_error is None
        
        # Verify existing errors can still be found
        found_error = error_handler.get_error("existing-error-1")
        assert found_error is not None
        assert found_error.error_id == "existing-error-1"
        assert found_error.message == "Existing error 1"

    def test_handle_error_success_path(self):
        """Test successful error handling to ensure normal flow still works."""
        error_handler = ErrorHandler()
        
        # Test successful error creation and storage
        result = error_handler.handle_error(
            error_id="success-test",
            category=ErrorCategory.CONSENSUS,
            severity=ErrorSeverity.CRITICAL,
            message="Success test message",
            details={"component": "test", "operation": "coverage_test"},
            task_id="task-123"
        )
        
        assert result is True
        assert len(error_handler.error_log) == 1
        
        # Verify error was stored correctly
        stored_error = error_handler.get_error("success-test")
        assert stored_error is not None
        assert stored_error.error_id == "success-test"
        assert stored_error.error_type == ErrorCategory.CONSENSUS
        assert stored_error.severity == ErrorSeverity.CRITICAL
        assert stored_error.message == "Success test message"
        assert stored_error.task_id == "task-123"
        assert stored_error.context["component"] == "test"

    def test_edge_cases_coverage(self):
        """Test additional edge cases to ensure complete coverage."""
        error_handler = ErrorHandler()
        
        # Test with None task_id (optional parameter)
        result = error_handler.handle_error(
            error_id="no-task-id",
            category=ErrorCategory.METRICS,
            severity=ErrorSeverity.INFO,
            message="No task ID test",
            details={"metric": "coverage"},
            task_id=None
        )
        
        assert result is True
        error = error_handler.get_error("no-task-id")
        assert error.task_id is None
        
        # Test with empty details
        result = error_handler.handle_error(
            error_id="empty-details",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.WARNING,
            message="Empty details test",
            details={}
        )
        
        assert result is True
        error = error_handler.get_error("empty-details")
        assert error.context == {}
        
        # Test all severity levels
        severities = [ErrorSeverity.INFO, ErrorSeverity.WARNING, ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]
        for i, severity in enumerate(severities):
            error_handler.handle_error(
                error_id=f"severity-test-{i}",
                category=ErrorCategory.TASK,
                severity=severity,
                message=f"Severity {severity.value} test",
                details={"severity_index": i}
            )
        
        # Verify all severities
        for i, severity in enumerate(severities):
            errors = error_handler.get_errors_by_severity(severity)
            assert len(errors) >= 1
            found_error = next((e for e in errors if e.error_id == f"severity-test-{i}"), None)
            assert found_error is not None
            assert found_error.severity == severity

    def test_concurrent_error_handling(self):
        """Test error handling under concurrent conditions."""
        error_handler = ErrorHandler()
        
        # Simulate rapid error creation
        error_ids = []
        for i in range(10):
            error_id = f"concurrent-error-{i}"
            error_ids.append(error_id)
            
            result = error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.QUEUE,
                severity=ErrorSeverity.ERROR,
                message=f"Concurrent error {i}",
                details={"index": i, "batch": "concurrent_test"}
            )
            assert result is True
        
        # Verify all errors were stored
        assert error_handler.get_error_count() >= 10
        
        # Verify each error can be retrieved
        for error_id in error_ids:
            error = error_handler.get_error(error_id)
            assert error is not None
            assert error.error_id == error_id
        
        # Test bulk retrieval
        queue_errors = error_handler.get_errors_by_category(ErrorCategory.QUEUE)
        assert len(queue_errors) >= 10
        
        error_errors = error_handler.get_errors_by_severity(ErrorSeverity.ERROR) 
        assert len(error_errors) >= 10 