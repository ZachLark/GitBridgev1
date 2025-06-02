#!/usr/bin/env python3
"""
Error Logging Module for GitBridge Project.

This module provides centralized error logging functionality for the MAS Lite system,
tracking system and agent-level exceptions with task and phase traceability.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any


def load_error_log(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load and parse the error log file.

    Args:
        log_path: Path to the error log file

    Returns:
        List of error entries from the log file

    Raises:
        json.JSONDecodeError: If the log file contains invalid JSON
    """
    try:
        if not log_path.exists():
            return []
        
        with log_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Error log file must contain a JSON array")
            return data
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse error log file: {e.msg}", e.doc, e.pos
        ) from e


def save_error_log(log_path: Path, data: List[Dict[str, Any]]) -> None:
    """
    Save the updated error log data back to file.

    Args:
        log_path: Path to the error log file
        data: List of error entries to save

    Raises:
        IOError: If there's an error writing to the file
        PermissionError: If the process lacks write permission
    """
    try:
        with log_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (IOError, PermissionError) as e:
        print(f"Failed to write to error log file: {str(e)}", file=sys.stderr)
        raise


def log_error(task_id: str, error_message: str, phase_id: Optional[str] = None) -> None:
    """
    Log an error event to the centralized error log file.

    This function appends a new error entry to error_log.json with the current UTC
    timestamp and provided error details. If the file doesn't exist, it will be created.

    Args:
        task_id: Identifier of the task where the error occurred
        error_message: Description of the error
        phase_id: Optional identifier of the phase where the error occurred

    Raises:
        ValueError: If task_id or error_message is empty
        IOError: If there's an error reading or writing the log file
        json.JSONDecodeError: If the existing log file contains invalid JSON
        PermissionError: If the process lacks necessary file permissions
    """
    # Input validation
    if not task_id or not task_id.strip():
        raise ValueError("task_id cannot be empty")
    if not error_message or not error_message.strip():
        raise ValueError("error_message cannot be empty")

    log_path = Path("error_log.json")

    try:
        # Load existing log data or initialize new list
        log_data = load_error_log(log_path)

        # Create new error entry
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id.strip(),
            "error": error_message.strip()
        }

        # Add phase_id if provided
        if phase_id and phase_id.strip():
            error_entry["phase_id"] = phase_id.strip()

        # Append new entry and save
        log_data.append(error_entry)
        save_error_log(log_path, log_data)

    except (ValueError, IOError, json.JSONDecodeError, PermissionError) as e:
        print(f"Error logging failed: {str(e)}", file=sys.stderr)
        raise


if __name__ == "__main__":
    # Example usage when run as a script
    try:
        log_error(
            task_id="example_task",
            error_message="Example error message",
            phase_id="P1"
        )
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1) 