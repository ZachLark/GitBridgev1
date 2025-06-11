"""
Unit tests for JSON processor utilities.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests
from requests.exceptions import RequestException, Timeout

from mas_core.utils.json_processor import (
    filter_pending_invites,
    validate_json_file,
    write_pending_invites,
    trigger_webhook,
    WEBHOOK_TIMEOUT
)


class TestFilterPendingInvites:
    """Test filter_pending_invites function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_filter_pending_invites_success(self, temp_dir):
        """Test successful filtering of pending invites."""
        test_file = temp_dir / "test.jsonl"
        
        # Create test data
        test_data = [
            {"invite_id": "inv_001", "status": "pending", "user": "alice"},
            {"invite_id": "inv_002", "status": "approved", "user": "bob"},
            {"invite_id": "inv_003", "status": "pending", "user": "charlie"},
            {"invite_id": "inv_004", "status": "rejected", "user": "david"}
        ]
        
        # Write test data to file
        with open(test_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        # Test the function
        result = filter_pending_invites(str(test_file))
        
        assert result == ["inv_001", "inv_003"]

    def test_filter_pending_invites_empty_file(self, temp_dir):
        """Test with empty file."""
        test_file = temp_dir / "empty.jsonl"
        test_file.touch()
        
        result = filter_pending_invites(str(test_file))
        assert result == []

    def test_filter_pending_invites_no_pending(self, temp_dir):
        """Test with no pending invites."""
        test_file = temp_dir / "no_pending.jsonl"
        
        test_data = [
            {"invite_id": "inv_001", "status": "approved", "user": "alice"},
            {"invite_id": "inv_002", "status": "rejected", "user": "bob"}
        ]
        
        with open(test_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        result = filter_pending_invites(str(test_file))
        assert result == []

    def test_filter_pending_invites_missing_invite_id(self, temp_dir):
        """Test with entries missing invite_id."""
        test_file = temp_dir / "missing_id.jsonl"
        
        test_data = [
            {"status": "pending", "user": "alice"},  # No invite_id
            {"invite_id": "inv_002", "status": "pending", "user": "bob"}
        ]
        
        with open(test_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        result = filter_pending_invites(str(test_file))
        assert result == ["inv_002"]

    def test_filter_pending_invites_file_not_found(self):
        """Test with non-existent file."""
        with pytest.raises(FileNotFoundError):
            filter_pending_invites("non_existent_file.jsonl")

    def test_filter_pending_invites_invalid_json(self, temp_dir):
        """Test with invalid JSON."""
        test_file = temp_dir / "invalid.jsonl"
        
        with open(test_file, 'w') as f:
            f.write('{"valid": "json"}\n')
            f.write('invalid json line\n')
        
        with pytest.raises(json.JSONDecodeError):
            filter_pending_invites(str(test_file))

    def test_filter_pending_invites_empty_lines(self, temp_dir):
        """Test with empty lines in file."""
        test_file = temp_dir / "with_empty_lines.jsonl"
        
        with open(test_file, 'w') as f:
            f.write('{"invite_id": "inv_001", "status": "pending"}\n')
            f.write('\n')  # Empty line
            f.write('{"invite_id": "inv_002", "status": "pending"}\n')
            f.write('   \n')  # Whitespace line
        
        result = filter_pending_invites(str(test_file))
        assert result == ["inv_001", "inv_002"]


class TestValidateJsonFile:
    """Test validate_json_file function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_validate_json_file_success(self, temp_dir):
        """Test successful validation of JSON file."""
        test_file = temp_dir / "valid.jsonl"
        
        test_data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"}
        ]
        
        with open(test_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')
        
        result = validate_json_file(str(test_file))
        assert len(result) == 3
        assert result == test_data

    def test_validate_json_file_not_found(self, temp_dir):
        """Test with non-existent file."""
        result = validate_json_file(str(temp_dir / "non_existent.jsonl"))
        assert result == []

    def test_validate_json_file_mixed_valid_invalid(self, temp_dir):
        """Test with mix of valid and invalid JSON lines."""
        test_file = temp_dir / "mixed.jsonl"
        
        with open(test_file, 'w') as f:
            f.write('{"id": 1, "name": "Alice"}\n')
            f.write('invalid json line\n')
            f.write('{"id": 2, "name": "Bob"}\n')
            f.write('another invalid line\n')
            f.write('{"id": 3, "name": "Charlie"}\n')
        
        result = validate_json_file(str(test_file))
        assert len(result) == 3
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
        assert result[2]["name"] == "Charlie"

    def test_validate_json_file_empty_lines(self, temp_dir):
        """Test with empty lines."""
        test_file = temp_dir / "with_empty.jsonl"
        
        with open(test_file, 'w') as f:
            f.write('{"id": 1}\n')
            f.write('\n')
            f.write('   \n')
            f.write('{"id": 2}\n')
        
        result = validate_json_file(str(test_file))
        assert len(result) == 2

    def test_validate_json_file_exception_handling(self, temp_dir):
        """Test exception handling during file processing."""
        test_file = temp_dir / "test.jsonl"
        test_file.write_text('{"valid": "json"}\n')
        
        # Mock open to raise an exception
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = validate_json_file(str(test_file))
            assert result == []


class TestWritePendingInvites:
    """Test write_pending_invites function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_write_pending_invites_success(self, temp_dir):
        """Test successful writing of pending invites."""
        output_file = temp_dir / "output.jsonl"
        
        test_data = [
            {"id": 1, "status": "pending", "name": "Alice"},
            {"id": 2, "status": "approved", "name": "Bob"},
            {"id": 3, "status": "pending", "name": "Charlie"},
            {"id": 4, "status": "rejected", "name": "David"}
        ]
        
        result = write_pending_invites(test_data, str(output_file))
        assert result is True
        
        # Verify file contents
        assert output_file.exists()
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        line1_data = json.loads(lines[0].strip())
        line2_data = json.loads(lines[1].strip())
        
        assert line1_data["name"] == "Alice"
        assert line2_data["name"] == "Charlie"

    def test_write_pending_invites_empty_list(self, temp_dir):
        """Test with empty input list."""
        output_file = temp_dir / "output.jsonl"
        
        result = write_pending_invites([], str(output_file))
        assert result is False

    def test_write_pending_invites_no_pending(self, temp_dir):
        """Test with no pending entries."""
        output_file = temp_dir / "output.jsonl"
        
        test_data = [
            {"id": 1, "status": "approved", "name": "Alice"},
            {"id": 2, "status": "rejected", "name": "Bob"}
        ]
        
        result = write_pending_invites(test_data, str(output_file))
        assert result is False

    def test_write_pending_invites_create_directory(self, temp_dir):
        """Test directory creation."""
        output_file = temp_dir / "subdir" / "output.jsonl"
        
        test_data = [
            {"id": 1, "status": "pending", "name": "Alice"}
        ]
        
        result = write_pending_invites(test_data, str(output_file))
        assert result is True
        assert output_file.parent.exists()
        assert output_file.exists()

    def test_write_pending_invites_invalid_json(self, temp_dir):
        """Test with non-serializable objects."""
        output_file = temp_dir / "output.jsonl"
        
        # Create data with non-serializable object
        test_data = [
            {"id": 1, "status": "pending", "func": lambda x: x}  # Non-serializable
        ]
        
        result = write_pending_invites(test_data, str(output_file))
        assert result is False

    def test_write_pending_invites_io_error(self, temp_dir):
        """Test IO error handling."""
        # Try to write to a directory instead of a file
        output_path = temp_dir / "existing_dir"
        output_path.mkdir()
        
        test_data = [
            {"id": 1, "status": "pending", "name": "Alice"}
        ]
        
        result = write_pending_invites(test_data, str(output_path))
        assert result is False

    def test_write_pending_invites_non_dict_entries(self, temp_dir):
        """Test with non-dictionary entries."""
        output_file = temp_dir / "output.jsonl"
        
        test_data = [
            {"id": 1, "status": "pending", "name": "Alice"},
            "not a dict",  # Invalid entry
            {"id": 2, "status": "pending", "name": "Bob"}
        ]
        
        result = write_pending_invites(test_data, str(output_file))
        assert result is True
        
        # Should only write the valid dict entries with pending status
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2

    def test_write_pending_invites_unexpected_exception(self, temp_dir):
        """Test unexpected exception handling."""
        output_file = temp_dir / "output.jsonl"
        
        test_data = [
            {"id": 1, "status": "pending", "name": "Alice"}
        ]
        
        # Mock Path to raise an unexpected exception
        with patch('mas_core.utils.json_processor.Path') as mock_path:
            mock_path.side_effect = ValueError("Unexpected path error")
            
            result = write_pending_invites(test_data, str(output_file))
            assert result is False


class TestTriggerWebhook:
    """Test trigger_webhook function."""

    def test_trigger_webhook_success(self):
        """Test successful webhook trigger."""
        test_data = {"event": "test", "id": "123"}
        test_url = "https://example.com/webhook"
        
        with patch('mas_core.utils.json_processor.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.elapsed.total_seconds.return_value = 0.5
            mock_post.return_value = mock_response
            
            result = trigger_webhook(test_data, test_url)
            
            assert result is True
            mock_post.assert_called_once_with(
                test_url,
                json=test_data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'MAS-Lite/2.1'
                },
                timeout=WEBHOOK_TIMEOUT
            )

    def test_trigger_webhook_invalid_parameters(self):
        """Test with invalid parameters."""
        # Empty data
        result = trigger_webhook({}, "https://example.com")
        assert result is False
        
        # Empty URL
        result = trigger_webhook({"test": "data"}, "")
        assert result is False
        
        # None data
        result = trigger_webhook(None, "https://example.com")
        assert result is False
        
        # None URL
        result = trigger_webhook({"test": "data"}, None)
        assert result is False

    def test_trigger_webhook_non_200_status(self):
        """Test webhook with non-200 status code."""
        test_data = {"event": "test"}
        test_url = "https://example.com/webhook"
        
        with patch('mas_core.utils.json_processor.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_response.elapsed.total_seconds.return_value = 0.3
            mock_post.return_value = mock_response
            
            result = trigger_webhook(test_data, test_url)
            assert result is False

    def test_trigger_webhook_timeout(self):
        """Test webhook timeout."""
        test_data = {"event": "test"}
        test_url = "https://example.com/webhook"
        
        with patch('mas_core.utils.json_processor.requests.post') as mock_post:
            mock_post.side_effect = Timeout("Request timed out")
            
            result = trigger_webhook(test_data, test_url)
            assert result is False

    def test_trigger_webhook_request_exception(self):
        """Test webhook request exception."""
        test_data = {"event": "test"}
        test_url = "https://example.com/webhook"
        
        with patch('mas_core.utils.json_processor.requests.post') as mock_post:
            mock_post.side_effect = RequestException("Connection error")
            
            result = trigger_webhook(test_data, test_url)
            assert result is False

    def test_trigger_webhook_unexpected_exception(self):
        """Test webhook unexpected exception."""
        test_data = {"event": "test"}
        test_url = "https://example.com/webhook"
        
        with patch('mas_core.utils.json_processor.requests.post') as mock_post:
            mock_post.side_effect = ValueError("Unexpected error")
            
            result = trigger_webhook(test_data, test_url)
            assert result is False

    def test_webhook_timeout_constant(self):
        """Test that webhook timeout constant is defined."""
        assert WEBHOOK_TIMEOUT == 30 