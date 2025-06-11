"""
Audit snapshot functionality for GitBridge MAS Lite.

This module provides functionality to create and validate audit snapshots
following MAS Lite Protocol v2.1 audit requirements.
"""

import json
import hashlib
import os
from typing import Dict, Any
from datetime import datetime, timezone

class SnapshotError(Exception):
    """Base class for snapshot-related errors."""
    pass

class SnapshotValidationError(SnapshotError):
    """Error raised when snapshot validation fails."""
    pass

def _calculate_checksum(data: Dict[str, Any]) -> str:
    """Calculate SHA-256 checksum of data.
    
    Args:
        data: Data to calculate checksum for
        
    Returns:
        str: Hexadecimal checksum
    """
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()

def _validate_timestamp(timestamp: str) -> bool:
    """Validate ISO format timestamp.
    
    Args:
        timestamp: Timestamp to validate
        
    Returns:
        bool: True if valid
    """
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False

def create_snapshot(data: Dict[str, Any], output_path: str) -> None:
    """Create audit snapshot.
    
    Args:
        data: Data to include in snapshot
        output_path: Path to save snapshot to
        
    Raises:
        SnapshotError: If snapshot creation fails
    """
    try:
        # Create snapshot structure
        snapshot = {
            "data": data,
            "metadata": {
                "version": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checksum": None  # Will be calculated after
            }
        }
        
        # Calculate checksum
        snapshot["metadata"]["checksum"] = _calculate_checksum(data)
        
        # Save snapshot
        with open(output_path, "w") as f:
            json.dump(snapshot, f, indent=2)
            
    except Exception as e:
        raise SnapshotError(f"Failed to create snapshot: {str(e)}")

def load_snapshot(input_path: str) -> Dict[str, Any]:
    """Load audit snapshot.
    
    Args:
        input_path: Path to load snapshot from
        
    Returns:
        Dict[str, Any]: Loaded snapshot
        
    Raises:
        SnapshotError: If snapshot loading fails
    """
    try:
        # Check if file exists
        if not os.path.exists(input_path):
            raise SnapshotError(f"Snapshot file not found: {input_path}")
            
        # Load snapshot
        with open(input_path, "r") as f:
            snapshot = json.load(f)
            
        # Validate snapshot
        validate_snapshot(snapshot)
        
        return snapshot
        
    except json.JSONDecodeError as e:
        raise SnapshotError(f"Invalid JSON in snapshot: {str(e)}")
    except Exception as e:
        raise SnapshotError(f"Failed to load snapshot: {str(e)}")

def validate_snapshot(snapshot: Dict[str, Any]) -> None:
    """Validate audit snapshot.
    
    Args:
        snapshot: Snapshot to validate
        
    Raises:
        SnapshotValidationError: If validation fails
    """
    try:
        # Check required fields
        if "data" not in snapshot:
            raise SnapshotValidationError("Missing data field")
            
        if "metadata" not in snapshot:
            raise SnapshotValidationError("Missing metadata field")
            
        metadata = snapshot["metadata"]
        
        # Check metadata fields
        if "version" not in metadata:
            raise SnapshotValidationError("Missing version field")
            
        if metadata["version"] != "1.0":
            raise SnapshotValidationError("Invalid version")
            
        if "timestamp" not in metadata:
            raise SnapshotValidationError("Missing timestamp field")
            
        if not _validate_timestamp(metadata["timestamp"]):
            raise SnapshotValidationError("Invalid timestamp format")
            
        if "checksum" not in metadata:
            raise SnapshotValidationError("Missing checksum field")
            
        # Verify checksum
        calculated_checksum = _calculate_checksum(snapshot["data"])
        if calculated_checksum != metadata["checksum"]:
            raise SnapshotValidationError("Checksum mismatch")
            
    except SnapshotValidationError:
        raise
    except Exception as e:
        raise SnapshotValidationError(f"Validation failed: {str(e)}") 