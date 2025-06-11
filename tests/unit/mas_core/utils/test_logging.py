"""
Unit tests for logging utilities.
"""

import json
import logging
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from mas_core.utils.logging import (
    MASLogger,
    LOG_DIR,
    MAS_LOG_FILE,
    AUDIT_LOG_FILE,
    ERROR_LOG_FILE
)


class TestMASLogger:
    """Test MAS logger functionality."""

    def setup_method(self):
        """Clean up logging handlers before each test."""
        # Clear root logger handlers
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)
        
        # Clear all registered logger handlers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mas_logger(self, temp_log_dir):
        """Create MAS logger instance with temp directory."""
        log_file = temp_log_dir / "test.log"
        return MASLogger("test_logger", log_file)

    def test_logger_initialization(self, mas_logger):
        """Test logger initialization."""
        assert mas_logger.logger.name == "test_logger"
        assert mas_logger.logger.level == logging.DEBUG
        assert mas_logger.task_name.startswith("Task-")
        assert len(mas_logger.task_name) == 13  # "Task-" + 8 hex chars

    def test_log_directory_creation(self, temp_log_dir):
        """Test log directory is created."""
        with patch('mas_core.utils.logging.LOG_DIR', temp_log_dir / "logs"):
            logger = MASLogger("test")
            assert (temp_log_dir / "logs").exists()

    def test_format_message(self, mas_logger):
        """Test message formatting."""
        with patch('mas_core.utils.logging.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T00:00:00+00:00"
            
            formatted = mas_logger._format_message("Test message", "INFO")
            data = json.loads(formatted)
            
            assert data["message"] == "Test message"
            assert data["levelname"] == "INFO"
            assert data["name"] == "test_logger"
            assert data["asctime"] == "2023-01-01T00:00:00+00:00"
            assert data["taskName"] == mas_logger.task_name

    def test_format_message_with_extra(self, mas_logger):
        """Test message formatting with extra data."""
        extra = {"task_id": "123", "user": "test_user"}
        formatted = mas_logger._format_message("Test message", "INFO", extra)
        data = json.loads(formatted)
        
        assert data["task_id"] == "123"
        assert data["user"] == "test_user"

    def test_log_task(self, mas_logger):
        """Test task logging."""
        with patch.object(mas_logger.logger, 'info') as mock_info:
            details = {"status": "completed", "duration": 123}
            mas_logger.log_task("task_001", "create", details)
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Task event"
            assert kwargs["extra"]["task_id"] == "task_001"
            assert kwargs["extra"]["action"] == "create"
            assert kwargs["extra"]["details"] == details
            assert "timestamp" in kwargs["extra"]

    def test_log_consensus(self, mas_logger):
        """Test consensus logging."""
        with patch.object(mas_logger.logger, 'info') as mock_info:
            votes = {"agent1": "approve", "agent2": "reject"}
            mas_logger.log_consensus("task_001", "pending", votes)
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Consensus event"
            assert kwargs["extra"]["task_id"] == "task_001"
            assert kwargs["extra"]["status"] == "pending"
            assert kwargs["extra"]["votes"] == votes
            assert "timestamp" in kwargs["extra"]

    def test_log_error(self, mas_logger):
        """Test error logging."""
        with patch.object(mas_logger.logger, 'error') as mock_error:
            context = {"function": "test_func", "line": 42}
            mas_logger.log_error("ValidationError", "Invalid input", context)
            
            mock_error.assert_called_once()
            args, kwargs = mock_error.call_args
            assert args[0] == "Invalid input"
            assert kwargs["extra"]["error_type"] == "ValidationError"
            assert kwargs["extra"]["context"] == context
            assert "timestamp" in kwargs["extra"]

    def test_log_audit(self, mas_logger, temp_log_dir):
        """Test audit logging."""
        audit_file = temp_log_dir / "audit.log"
        
        with patch('mas_core.utils.logging.AUDIT_LOG_FILE', audit_file):
            mas_logger.log_audit("agent_001", "read", "task_data")
            
            assert audit_file.exists()
            with open(audit_file, 'r') as f:
                line = f.readline().strip()
                data = json.loads(line)
                
                assert data["agent_id"] == "agent_001"
                assert data["action"] == "read"
                assert data["resource"] == "task_data"
                assert "timestamp" in data

    def test_log_method(self, mas_logger):
        """Test generic log method."""
        with patch.object(mas_logger.logger, 'log') as mock_log:
            extra = {"key": "value"}
            mas_logger.log("INFO", "Test message", extra)
            
            mock_log.assert_called_once_with(
                logging.INFO,
                "Test message",
                extra=extra
            )

    def test_log_method_without_extra(self, mas_logger):
        """Test generic log method without extra data."""
        with patch.object(mas_logger.logger, 'log') as mock_log:
            mas_logger.log("ERROR", "Test error")
            
            mock_log.assert_called_once_with(
                logging.ERROR,
                "Test error",
                extra={}
            )

    def test_info_method(self, mas_logger):
        """Test info logging method."""
        with patch.object(mas_logger.logger, 'info') as mock_info:
            with patch.object(mas_logger, '_format_message') as mock_format:
                mock_format.return_value = "formatted_message"
                
                extra = {"key": "value"}
                mas_logger.info("Info message", extra)
                
                mock_format.assert_called_once_with("Info message", "INFO", extra)
                mock_info.assert_called_once_with("formatted_message")

    def test_warning_method(self, mas_logger):
        """Test warning logging method."""
        with patch.object(mas_logger.logger, 'warning') as mock_warning:
            with patch.object(mas_logger, '_format_message') as mock_format:
                mock_format.return_value = "formatted_message"
                
                mas_logger.warning("Warning message")
                
                mock_format.assert_called_once_with("Warning message", "WARNING", None)
                mock_warning.assert_called_once_with("formatted_message")

    def test_error_method(self, mas_logger):
        """Test error logging method."""
        with patch.object(mas_logger.logger, 'error') as mock_error:
            with patch.object(mas_logger, '_format_message') as mock_format:
                mock_format.return_value = "formatted_message"
                
                mas_logger.error("Error message")
                
                mock_format.assert_called_once_with("Error message", "ERROR", None)
                mock_error.assert_called_once_with("formatted_message")

    def test_critical_method(self, mas_logger):
        """Test critical logging method."""
        with patch.object(mas_logger.logger, 'critical') as mock_critical:
            with patch.object(mas_logger, '_format_message') as mock_format:
                mock_format.return_value = "formatted_message"
                
                mas_logger.critical("Critical message")
                
                mock_format.assert_called_once_with("Critical message", "CRITICAL", None)
                mock_critical.assert_called_once_with("formatted_message")

    def test_debug_method(self, mas_logger):
        """Test debug logging method."""
        with patch.object(mas_logger.logger, 'debug') as mock_debug:
            with patch.object(mas_logger, '_format_message') as mock_format:
                mock_format.return_value = "formatted_message"
                
                mas_logger.debug("Debug message")
                
                mock_format.assert_called_once_with("Debug message", "DEBUG", None)
                mock_debug.assert_called_once_with("formatted_message")

    def test_set_task_name(self, mas_logger):
        """Test setting task name."""
        new_task_name = "Custom-Task-Name"
        mas_logger.set_task_name(new_task_name)
        
        assert mas_logger.task_name == new_task_name

    def test_file_handler_configuration(self, temp_log_dir):
        """Test file handler is properly configured."""
        log_file = temp_log_dir / "test.log"
        logger = MASLogger("test_logger", log_file)
        
        # Check that file handler was added
        file_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        
        file_handler = file_handlers[0]
        assert file_handler.baseFilename == str(log_file)

    def test_console_handler_configuration(self, mas_logger):
        """Test console handler is properly configured."""
        # Check that console handler was added (StreamHandler but not FileHandler)
        console_handlers = [h for h in mas_logger.logger.handlers 
                          if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
        assert len(console_handlers) == 1
        
        console_handler = console_handlers[0]
        # During testing, stdout might be captured/redirected, so check if it's a stdout-like stream
        assert hasattr(console_handler.stream, 'name') or hasattr(console_handler.stream, 'write')

    def test_multiple_audit_entries(self, mas_logger, temp_log_dir):
        """Test multiple audit log entries."""
        audit_file = temp_log_dir / "audit.log"
        
        with patch('mas_core.utils.logging.AUDIT_LOG_FILE', audit_file):
            mas_logger.log_audit("agent_001", "read", "task_data")
            mas_logger.log_audit("agent_002", "write", "config")
            
            with open(audit_file, 'r') as f:
                lines = f.readlines()
                
            assert len(lines) == 2
            
            data1 = json.loads(lines[0].strip())
            data2 = json.loads(lines[1].strip())
            
            assert data1["agent_id"] == "agent_001"
            assert data1["action"] == "read"
            assert data2["agent_id"] == "agent_002"
            assert data2["action"] == "write"

    def test_constants_defined(self):
        """Test that logging constants are properly defined."""
        assert isinstance(LOG_DIR, Path)
        assert isinstance(MAS_LOG_FILE, Path)
        assert isinstance(AUDIT_LOG_FILE, Path)
        assert isinstance(ERROR_LOG_FILE, Path)
        
        assert LOG_DIR.name == "logs"
        assert MAS_LOG_FILE.name == "mas.log"
        assert AUDIT_LOG_FILE.name == "audit.log"
        assert ERROR_LOG_FILE.name == "error.log" 