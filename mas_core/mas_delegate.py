"""
Module for delegating tasks to an API and logging the results.

This module provides functionality to load and validate task templates,
delegate tasks to a specified API endpoint, and log the responses.
"""
import json
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path
import requests
from requests.exceptions import HTTPError, Timeout, RequestException

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
    except (json.JSONDecodeError, IOError) as e:
        raise ValueError(f"Failed to read or parse JSON from {path}: {e}") from e

    required_fields = ["task_id", "description", "assignee", "max_cycles", "token_budget"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Split the long line into two for readability
    task_id = data["task_id"]
    if not isinstance(task_id, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", task_id):
        raise ValueError("task_id must be a 64-character hexadecimal string")

    if not isinstance(data["description"], str) or not data["description"].strip():
        raise ValueError("description must be a non-empty string")

    if not isinstance(data["assignee"], str) or not data["assignee"].strip():
        raise ValueError("assignee must be a non-empty string")

    try:
        data["max_cycles"] = int(data["max_cycles"])
        if data["max_cycles"] <= 0:
            raise ValueError("max_cycles must be a positive integer")
    except (ValueError, TypeError) as e:
        raise ValueError("max_cycles must be convertible to a positive integer") from e

    try:
        data["token_budget"] = int(data["token_budget"])
        if data["token_budget"] <= 0:
            raise ValueError("token_budget must be a positive integer")
    except (ValueError, TypeError) as e:
        raise ValueError("token_budget must be convertible to a positive integer") from e

    return data

def delegate_task(task: dict, api_url: str) -> dict:
    """Delegate a task to the API and return the response."""
    print(f"Sending payload to {api_url}: {json.dumps(task)}")
    try:
        response = requests.post(api_url, json=task, timeout=10)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        raise RuntimeError(f"HTTP error occurred: {str(e)}") from e
    except Timeout as e:
        raise RuntimeError("Request timed out") from e
    except RequestException as e:
        raise RuntimeError(f"Error during request: {str(e)}") from e

def log_task(task: dict, log_path: Path) -> None:
    """Log task details to a JSON file with a timestamp."""
    log_entry = task.copy()
    log_entry["timestamp"] = datetime.now().isoformat()
    
    # Write each entry as a single line for atomic appends
    with log_path.open('a') as f:
        json.dump(log_entry, f)
        f.write('\n')

def main():
    """Main function to handle task delegation."""
    parser = argparse.ArgumentParser(description="Delegate tasks to an API.")
    parser.add_argument("--task-file", type=str, required=True, help="Path to task JSON file")
    parser.add_argument("--api-url", type=str, required=True, help="API URL to delegate task")
    parser.add_argument("--log-file", type=str, required=True, help="Path to log file")
    args = parser.parse_args()

    task_path = Path(args.task_file)
    log_path = Path(args.log_file)

    try:
        task = load_and_validate_task(task_path)
        api_response = delegate_task(task, args.api_url)
        log_task(api_response, log_path)
        print(json.dumps(api_response))
        sys.exit(0)
    except (ValueError, RuntimeError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

# Ensure a final newline is present
