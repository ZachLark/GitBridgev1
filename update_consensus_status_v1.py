#!/usr/bin/env python3
"""
Update Consensus Status Script for GitBridge Project.

This script allows updating the consensus status of tasks in the MAS Lite system,
maintaining an audit trail of status changes in the status_history array.

MAS Lite Protocol v2.1 Compliance:
- Maintains atomic status updates
- Preserves status history with UTC timestamps
- Validates against approved status values
- Ensures data integrity with proper file locking
- Supports future extension points for API integration

Future Development (TODO):
- Phase 10: Support for batch updates via JSON input file
  - Add BatchUpdateRequest schema
  - Implement validation for bulk operations
  - Add rollback support for failed batches

- Phase 12: Support for REST endpoint writeback
  - Implement async status notification
  - Add webhook support for status changes
  - Integrate with event bus system

- API Integration:
  Function: update_status(task_id: str, new_status: str)
  - Add proper error handling
  - Implement retry logic
  - Add proper logging
"""

import json
import sys
import fcntl
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, NoReturn, Tuple

# Uncomment for future logging integration
# from mas_error import log_error


class ConsensusStatusError(Exception):
    """Base exception for consensus status update errors."""


class TaskNotFoundError(ConsensusStatusError):
    """Exception raised when task_id is not found."""


class InvalidStatusError(ConsensusStatusError):
    """Exception raised when status value is invalid."""


def load_log_file(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load and parse the MAS log file with proper locking.

    Args:
        log_path: Path to the log file

    Returns:
        List of task entries from the log file

    Raises:
        FileNotFoundError: If the log file doesn't exist
        json.JSONDecodeError: If the log file contains invalid JSON
        IOError: If there are issues reading the file
    """
    try:
        with log_path.open('r', encoding='utf-8') as f:
            # Acquire shared lock for reading
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Log file must contain a JSON array")
                return data
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Log file not found: {log_path}") from exc
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse log file: {e.msg}", e.doc, e.pos
        ) from e


def save_log_file(log_path: Path, data: List[Dict[str, Any]]) -> None:
    """
    Save the updated log data back to file with proper locking.

    Args:
        log_path: Path to the log file
        data: List of task entries to save

    Raises:
        IOError: If there's an error writing to the file
    """
    try:
        with log_path.open('r+', encoding='utf-8') as f:
            # Acquire exclusive lock for writing
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                # Truncate file and write new data
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2, ensure_ascii=False)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except IOError as e:
        raise IOError(f"Failed to write to log file: {str(e)}") from e


def validate_status(status: str) -> bool:
    """
    Validate that the status is one of the allowed values.

    Args:
        status: Status string to validate

    Returns:
        True if status is valid, False otherwise
    """
    return status.lower() in ["approved", "rejected"]


def update_task_status(
    task_id: str,
    new_status: str,
    log_data: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], int]:
    """
    Update the consensus status of a task and its status history.

    Args:
        task_id: ID of the task to update
        new_status: New consensus status ('approved' or 'rejected')
        log_data: List of task entries from the log file

    Returns:
        Tuple of (updated task entry, index in log_data)

    Raises:
        TaskNotFoundError: If task_id is not found
        InvalidStatusError: If new_status is not valid
    """
    if not validate_status(new_status):
        raise InvalidStatusError(
            "Status must be 'approved' or 'rejected'"
        )

    new_status = new_status.lower()
    current_time = datetime.now(timezone.utc).isoformat()

    for idx, entry in enumerate(log_data):
        if entry.get("task_id") == task_id:
            # Update consensus status
            entry["consensus"] = new_status
            # Add to status history
            if "status_history" not in entry:
                entry["status_history"] = []
            entry["status_history"].append({
                "status": new_status,
                "timestamp": current_time
            })
            return entry, idx

    raise TaskNotFoundError(f"Task '{task_id}' not found")


def update_status_interactive() -> None:
    """
    Interactive CLI function for updating task status.

    This function handles user input and provides feedback.

    Raises:
        Various exceptions that are caught in main()
    """
    log_path = Path("mas_log.json")

    # Get user input
    task_id = input("Enter task_id: ").strip()
    if not task_id:
        raise ValueError("Task ID cannot be empty")

    new_status = input("Enter new status (approved/rejected): ").strip()
    if not new_status:
        raise ValueError("Status cannot be empty")

    # Load existing log data
    log_data = load_log_file(log_path)

    # Update task status and save
    _, _ = update_task_status(task_id, new_status, log_data)
    save_log_file(log_path, log_data)

    print(f"✅ Updated {task_id} to status \"{new_status.lower()}\"")


def handle_error(error: Exception) -> NoReturn:
    """
    Handle errors uniformly across the application.

    Args:
        error: The exception to handle

    Returns:
        Never returns, always exits with status 1
    """
    error_msg = str(error).strip() or error.__class__.__name__
    # Uncomment for future logging integration
    # log_error(
    #     task_id="system",
    #     error_message=f"Status update error: {error_msg}",
    #     phase_id="P7P5"
    # )
    print(f"Error: {error_msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """Main function for CLI operation."""
    try:
        update_status_interactive()
    except (ConsensusStatusError, ValueError, IOError, json.JSONDecodeError) as e:
        handle_error(e)


if __name__ == "__main__":
    main()
