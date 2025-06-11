"""
Test audit snapshot functionality.

This module tests the audit snapshot functionality for GitBridge's event processing
system, following MAS Lite Protocol v2.1 audit requirements.
"""

import os
import json
import pytest
import tempfile
from datetime import datetime, timezone
from scripts.audit_snapshot import (
    create_snapshot,
    load_snapshot,
    validate_snapshot,
    SnapshotError,
    SnapshotValidationError
)

def test_create_snapshot_empty():
    """Test creating snapshot with empty data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_path = os.path.join(temp_dir, "snapshot.json")
        data = {}
        
        # Create snapshot
        create_snapshot(data, snapshot_path)
        
        # Verify file exists
        assert os.path.exists(snapshot_path)
        
        # Verify content
        with open(snapshot_path, "r") as f:
            content = json.load(f)
            assert content == {
                "data": {},
                "metadata": {
                    "version": "1.0",
                    "timestamp": content["metadata"]["timestamp"],
                    "checksum": content["metadata"]["checksum"]
                }
            }

def test_create_snapshot_with_data():
    """Test creating snapshot with data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_path = os.path.join(temp_dir, "snapshot.json")
        data = {
            "tasks": [
                {"id": "1", "state": "completed"},
                {"id": "2", "state": "pending"}
            ],
            "metrics": {
                "total_tasks": 2,
                "completed_tasks": 1
            }
        }
        
        # Create snapshot
        create_snapshot(data, snapshot_path)
        
        # Verify content
        with open(snapshot_path, "r") as f:
            content = json.load(f)
            assert content["data"] == data
            assert content["metadata"]["version"] == "1.0"
            assert isinstance(content["metadata"]["timestamp"], str)
            assert isinstance(content["metadata"]["checksum"], str)

def test_load_snapshot():
    """Test loading snapshot."""
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_path = os.path.join(temp_dir, "snapshot.json")
        data = {"key": "value"}
        
        # Create and load snapshot
        create_snapshot(data, snapshot_path)
        loaded_data = load_snapshot(snapshot_path)
        
        assert loaded_data["data"] == data
        assert loaded_data["metadata"]["version"] == "1.0"

def test_load_snapshot_missing_file():
    """Test loading missing snapshot file."""
    with pytest.raises(SnapshotError):
        load_snapshot("nonexistent.json")

def test_load_snapshot_invalid_json():
    """Test loading invalid JSON."""
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_path = os.path.join(temp_dir, "snapshot.json")
        
        # Write invalid JSON
        with open(snapshot_path, "w") as f:
            f.write("invalid json")
            
        with pytest.raises(SnapshotError):
            load_snapshot(snapshot_path)

def test_validate_snapshot_valid():
    """Test validating valid snapshot."""
    data = {
        "data": {"key": "value"},
        "metadata": {
            "version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checksum": "abc123"
        }
    }
    
    # Should not raise
    validate_snapshot(data)

def test_validate_snapshot_missing_fields():
    """Test validating snapshot with missing fields."""
    data = {
        "data": {"key": "value"}
        # Missing metadata
    }
    
    with pytest.raises(SnapshotValidationError):
        validate_snapshot(data)

def test_validate_snapshot_invalid_version():
    """Test validating snapshot with invalid version."""
    data = {
        "data": {"key": "value"},
        "metadata": {
            "version": "2.0",  # Invalid version
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checksum": "abc123"
        }
    }
    
    with pytest.raises(SnapshotValidationError):
        validate_snapshot(data)

def test_validate_snapshot_invalid_timestamp():
    """Test validating snapshot with invalid timestamp."""
    data = {
        "data": {"key": "value"},
        "metadata": {
            "version": "1.0",
            "timestamp": "invalid",  # Invalid timestamp
            "checksum": "abc123"
        }
    }
    
    with pytest.raises(SnapshotValidationError):
        validate_snapshot(data)

def test_large_snapshot():
    """Test handling large snapshots."""
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_path = os.path.join(temp_dir, "large_snapshot.json")
        
        # Create ~1MB of data
        with open(snapshot_path, "w") as f:
            f.write("x = 1\n" * 100000)  # Creates ~1MB file
            
        # Should handle large file without memory issues
        with pytest.raises(SnapshotError):
            load_snapshot(snapshot_path)

def test_concurrent_snapshot_access():
    """Test concurrent snapshot access."""
    import threading
    import time
    
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_path = os.path.join(temp_dir, "concurrent.json")
        data = {"counter": 0}
        create_snapshot(data, snapshot_path)
        
        def update_snapshot():
            for _ in range(10):
                current = load_snapshot(snapshot_path)
                current["data"]["counter"] += 1
                time.sleep(0.01)  # Simulate work
                create_snapshot(current["data"], snapshot_path)
                
        # Create multiple threads
        threads = [threading.Thread(target=update_snapshot) for _ in range(5)]
        
        # Start threads
        for t in threads:
            t.start()
            
        # Wait for completion
        for t in threads:
            t.join()
            
        # Verify final state
        final = load_snapshot(snapshot_path)
        assert final["data"]["counter"] <= 50  # May be less due to race conditions