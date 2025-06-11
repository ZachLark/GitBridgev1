"""Unit tests for the filter_pending_invites function.

This module contains pytest test cases for testing the filter_pending_invites
function from the mas_core.utils.json_processor module.
"""

import json
import pytest
from pathlib import Path
from mas_core.utils.json_processor import filter_pending_invites


@pytest.fixture
def temp_jsonl_file(tmp_path):
    """Create a temporary JSONL file with mixed status entries."""
    test_data = [
        {"invite_id": "inv_001", "status": "pending", "user": "alice"},
        {"invite_id": "inv_002", "status": "approved", "user": "bob"},
        {"invite_id": "inv_003", "status": "pending", "user": "charlie"},
        {"invite_id": "inv_004", "status": "rejected", "user": "dave"},
        {"invite_id": "inv_005", "status": "pending", "user": "eve"}
    ]
    
    file_path = tmp_path / "test_invites.jsonl"
    with open(file_path, 'w', encoding='utf-8') as f:
        for entry in test_data:
            f.write(json.dumps(entry) + '\n')
    
    return file_path


@pytest.fixture
def empty_jsonl_file(tmp_path):
    """Create an empty JSONL file."""
    file_path = tmp_path / "empty_invites.jsonl"
    file_path.touch()
    return file_path


@pytest.fixture
def invalid_jsonl_file(tmp_path):
    """Create a JSONL file with some invalid JSON entries."""
    file_path = tmp_path / "invalid_invites.jsonl"
    with open(file_path, 'w', encoding='utf-8') as f:
        # Valid JSON
        f.write('{"invite_id": "inv_001", "status": "pending", "user": "alice"}\n')
        # Invalid JSON
        f.write('{"invite_id": "inv_002", status: pending}\n')
        # Valid JSON
        f.write('{"invite_id": "inv_003", "status": "pending", "user": "charlie"}\n')
        # Incomplete JSON
        f.write('{"invite_id": "inv_004", "status":')
    
    return file_path


def test_filter_pending_invites_valid_file(temp_jsonl_file):
    """Test filtering pending invites from a valid JSONL file."""
    # When: We filter pending invites from a valid file
    result = filter_pending_invites(str(temp_jsonl_file))
    
    # Then: Only pending invite IDs should be returned
    expected = ["inv_001", "inv_003", "inv_005"]
    assert result == expected, f"Expected {expected}, but got {result}"


def test_filter_pending_invites_empty_file(empty_jsonl_file):
    """Test filtering pending invites from an empty file."""
    # When: We filter pending invites from an empty file
    result = filter_pending_invites(str(empty_jsonl_file))
    
    # Then: An empty list should be returned
    assert result == [], "Expected empty list for empty file"


def test_filter_pending_invites_invalid_file(invalid_jsonl_file):
    """Test filtering pending invites from a file with invalid JSON."""
    # When: We filter pending invites from a file with invalid JSON
    with pytest.raises(json.JSONDecodeError):
        filter_pending_invites(str(invalid_jsonl_file))


def test_filter_pending_invites_nonexistent_file():
    """Test filtering pending invites from a nonexistent file."""
    # When: We try to filter pending invites from a nonexistent file
    with pytest.raises(FileNotFoundError):
        filter_pending_invites("nonexistent_file.jsonl")


def test_filter_pending_invites_missing_status(tmp_path):
    """Test filtering pending invites from entries with missing status field."""
    # Given: A file with entries missing status field
    file_path = tmp_path / "missing_status.jsonl"
    test_data = [
        {"invite_id": "inv_001", "status": "pending"},
        {"invite_id": "inv_002"},  # Missing status
        {"invite_id": "inv_003", "status": "pending"},
        {"status": "pending"},  # Missing invite_id
        {}  # Empty object
    ]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for entry in test_data:
            f.write(json.dumps(entry) + '\n')
    
    # When: We filter pending invites
    result = filter_pending_invites(str(file_path))
    
    # Then: Only entries with both invite_id and pending status should be returned
    expected = ["inv_001", "inv_003"]
    assert result == expected, f"Expected {expected}, but got {result}"


def test_filter_pending_invites_unicode(tmp_path):
    """Test filtering pending invites with Unicode characters."""
    # Given: A file with Unicode characters
    file_path = tmp_path / "unicode_invites.jsonl"
    test_data = [
        {"invite_id": "inv_001", "status": "pending", "user": "José"},
        {"invite_id": "inv_002", "status": "approved", "user": "María"},
        {"invite_id": "inv_003", "status": "pending", "user": "André"}
    ]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for entry in test_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # When: We filter pending invites
    result = filter_pending_invites(str(file_path))
    
    # Then: Unicode content should be handled correctly
    expected = ["inv_001", "inv_003"]
    assert result == expected, f"Expected {expected}, but got {result}" 