#!/usr/bin/env python3
import argparse
import json
import re
import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import requests


def load_and_validate_task(path: Path) -> dict:
    """
    Load a JSON task template from a file and validate its schema.
    - task_id: 64-character hex string
    - description: non-empty string
    - assignee: non-empty string
    - max_cycles: positive integer
    - token_budget: positive integer
    """
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        raise ValueError(f"Failed to read or parse JSON from {path}: {e}")

    required_fields = ["task_id", "description", "assignee", "max_cycles", "token_budget"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(data["task_id"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", data["task_id"]):
        raise ValueError("task_id must be a 64-character hexadecimal string")

    if not isinstance(data["description"], str) or not data["description"].strip():
        raise ValueError("description must be a non-empty string")

    if not isinstance(data["assignee"], str) or not data["assignee"].strip():
        raise ValueError("assignee must be a non-empty string")

    if not isinstance(data["max_cycles"], int) or data["max_cycles"] <= 0:
        raise ValueError("max_cycles must be a positive integer")

    if not isinstance(data["token_budget"], int) or data["token_budget"] <= 0:
        raise ValueError("token_budget must be a positive integer")

    return data


def delegate_task(task: dict, api_url: str) -> dict:
    """
    Delegate the task to the remote API via POST to /collaborate.
    Returns the parsed JSON response.
    """
    url = api_url.rstrip("/") + "/collaborate"
    try:
        response = requests.post(url, json=task, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Request timed out: {e}")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error during request: {e}")

    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON response: {e}")


def log_task(entry: dict, log_path: Path) -> None:
    """
    Append a log record as a single JSON line to the log file, using atomic replace.
    Record includes: task_id, assignee, timestamp (ISO8601), max_cycles, token_budget, cycle_count.
    """
    record = {
        "task_id": entry["task_id"],
        "assignee": entry["assignee"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "max_cycles": entry["max_cycles"],
        "token_budget": entry["token_budget"],
        "cycle_count": entry["cycle_count"],
    }

    log_dir = log_path.parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Write to a temp file in the same directory then atomically replace
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(log_dir)) as tf:
        temp_name = tf.name
        # Copy existing log if present
        if log_path.exists():
            with log_path.open("r") as lf:
                for line in lf:
                    tf.write(line)
        # Append new record
        tf.write(json.dumps(record) + "\n")

    os.replace(temp_name, str(log_path))


def main():
    parser = argparse.ArgumentParser(description="Delegate a task and log the result.")
    parser.add_argument(
        "--task-file",
        type=Path,
        required=True,
        help="Path to the task_template.json file",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        required=True,
        help="Base URL of the remote API (e.g. http://localhost:5000)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        required=True,
        help="Path to the JSON lines log file",
    )

    args = parser.parse_args()

    try:
        task = load_and_validate_task(args.task_file)
        result = delegate_task(task, args.api_url)
        log_task(result, args.log_file)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()