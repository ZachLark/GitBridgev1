"""Integration tests for the invite processing workflow.

This module tests the complete workflow of validating JSON files,
filtering for pending invites, and writing them to a new file.
Tests the integration between validate_json_file, filter_pending_invites,
and write_pending_invites functions.
"""

import json
import pytest
from pathlib import Path
from typing import List, Dict, Any
from mas_core.utils.json_processor import (
    validate_json_file,
    filter_pending_invites,
    write_pending_invites
)


@pytest.fixture
def sample_invites() -> List[Dict[str, Any]]:
    """Create a list of valid invite entries with mixed statuses."""
    return [
        {"invite_id": "inv_001", "status": "pending", "user": "alice", "date": "2024-01-20"},
        {"invite_id": "inv_002", "status": "approved", "user": "bob", "date": "2024-01-19"},
        {"invite_id": "inv_003", "status": "pending", "user": "charlie", "date": "2024-01-18"},
        {"invite_id": "inv_004", "status": "processed", "user": "dave", "date": "2024-01-17"},
        {"invite_id": "inv_005", "status": "pending", "user": "eve", "date": "2024-01-16"},
        {"invite_id": "inv_006", "status": "approved", "user": "frank", "date": "2024-01-15"},
        {"invite_id": "inv_007", "status": "pending", "user": "grace", "date": "2024-01-14"},
        {"invite_id": "inv_008", "status": "processed", "user": "henry", "date": "2024-01-13"},
        {"invite_id": "inv_009", "status": "approved", "user": "ivy", "date": "2024-01-12"},
        {"invite_id": "inv_010", "status": "processed", "user": "jack", "date": "2024-01-11"}
    ]


@pytest.fixture
def input_jsonl_file(tmp_path, sample_invites) -> Path:
    """Create a test JSONL file with valid, invalid, and missing field entries."""
    file_path = tmp_path / "test_invites.jsonl"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        # Write 10 valid entries
        for invite in sample_invites:
            f.write(json.dumps(invite) + '\n')
        
        # Write 3 malformed JSON lines
        f.write('{"invite_id": "inv_011", status: "pending"}\n')  # Missing quotes
        f.write('{"invite_id": "inv_012", "status": "pending",}\n')  # Trailing comma
        f.write('{"invite_id": "inv_013" "status": "pending"}\n')  # Missing comma
        
        # Write 2 entries with missing required fields
        f.write('{"invite_id": "inv_014"}\n')  # Missing status
        f.write('{"status": "pending"}\n')  # Missing invite_id
    
    return file_path


def test_full_invite_workflow(tmp_path, input_jsonl_file, sample_invites, caplog):
    """Test the complete workflow of validating, filtering, and writing invites."""
    # Given: An output path for pending invites
    output_path = tmp_path / "pending" / "filtered_invites.jsonl"
    
    # When: We validate the input file
    valid_entries = validate_json_file(str(input_jsonl_file))
    
    # Then: We should have exactly 10 valid entries
    assert len(valid_entries) == 10, f"Expected 10 valid entries, got {len(valid_entries)}"
    
    # And: The valid entries should match our sample data
    assert valid_entries == sample_invites
    
    # When: We filter for pending invites
    pending_ids = filter_pending_invites(str(input_jsonl_file))
    
    # Then: We should have exactly 4 pending invites
    expected_pending_ids = ["inv_001", "inv_003", "inv_005", "inv_007"]
    assert pending_ids == expected_pending_ids, \
        f"Expected {expected_pending_ids}, got {pending_ids}"
    
    # When: We write the pending entries to a new file
    pending_entries = [
        entry for entry in valid_entries
        if entry["invite_id"] in pending_ids
    ]
    success = write_pending_invites(pending_entries, str(output_path))
    
    # Then: The write operation should succeed
    assert success, "write_pending_invites should return True"
    
    # And: The output file should exist
    assert output_path.exists(), "Output file should be created"
    
    # And: The output file should contain exactly 4 entries
    written_entries = []
    with open(output_path, 'r', encoding='utf-8') as f:
        for line in f:
            written_entries.append(json.loads(line))
    
    assert len(written_entries) == 4, \
        f"Expected 4 entries in output file, got {len(written_entries)}"
    
    # And: All written entries should have status "pending"
    assert all(entry["status"] == "pending" for entry in written_entries), \
        "All written entries should have status 'pending'"


def test_workflow_with_empty_input(tmp_path):
    """Test workflow behavior with an empty input file."""
    # Given: An empty input file
    input_path = tmp_path / "empty.jsonl"
    input_path.touch()
    output_path = tmp_path / "output.jsonl"
    
    # When: We run the workflow
    valid_entries = validate_json_file(str(input_path))
    pending_ids = filter_pending_invites(str(input_path))
    success = write_pending_invites(valid_entries, str(output_path))
    
    # Then: Each step should handle empty input gracefully
    assert valid_entries == [], "validate_json_file should return empty list"
    assert pending_ids == [], "filter_pending_invites should return empty list"
    assert not success, "write_pending_invites should return False for empty input"


def test_workflow_with_nested_output_path(tmp_path, sample_invites):
    """Test workflow with a deeply nested output path."""
    # Given: A deeply nested output path
    nested_path = tmp_path / "a" / "b" / "c" / "d" / "output.jsonl"
    
    # When: We write pending entries
    pending_entries = [
        entry for entry in sample_invites
        if entry["status"] == "pending"
    ]
    success = write_pending_invites(pending_entries, str(nested_path))
    
    # Then: The operation should succeed
    assert success, "write_pending_invites should handle nested paths"
    assert nested_path.exists(), "Nested directories should be created"


def test_workflow_preserves_utf8(tmp_path):
    """Test that the workflow preserves UTF-8 characters."""
    # Given: Input data with UTF-8 characters
    input_path = tmp_path / "utf8.jsonl"
    output_path = tmp_path / "utf8_output.jsonl"
    
    utf8_data = [
        {"invite_id": "inv_001", "status": "pending", "user": "José"},
        {"invite_id": "inv_002", "status": "pending", "user": "María"},
        {"invite_id": "inv_003", "status": "approved", "user": "André"}
    ]
    
    with open(input_path, 'w', encoding='utf-8') as f:
        for entry in utf8_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # When: We run the workflow
    valid_entries = validate_json_file(str(input_path))
    success = write_pending_invites(valid_entries, str(output_path))
    
    # Then: UTF-8 characters should be preserved
    assert success, "write_pending_invites should succeed with UTF-8"
    
    with open(output_path, 'r', encoding='utf-8') as f:
        written_entries = [json.loads(line) for line in f]
    
    expected_users = ["José", "María"]
    actual_users = [entry["user"] for entry in written_entries]
    assert actual_users == expected_users, \
        "UTF-8 characters should be preserved in output"


def test_workflow_error_handling(tmp_path):
    """Test error handling in the workflow."""
    # Given: A read-only directory
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    output_path = readonly_dir / "output.jsonl"
    readonly_dir.chmod(0o444)  # Make directory read-only
    
    # And: Some valid input data
    input_data = [{"invite_id": "inv_001", "status": "pending"}]
    
    # When/Then: Writing to a read-only directory should fail gracefully
    success = write_pending_invites(input_data, str(output_path))
    assert not success, "write_pending_invites should return False for permission error"
    
    # Cleanup: Reset directory permissions
    readonly_dir.chmod(0o755) 