"""Utility functions for processing JSON files in the MAS system.

This module provides functionality for reading and processing JSON files
according to MAS Lite Protocol v2.1 specifications.
"""

import json
import requests
from typing import List, Dict, Any
from pathlib import Path
from requests.exceptions import RequestException, Timeout
from .logging import MASLogger

# Initialize logger
logger = MASLogger("json_processor")

# Constants
WEBHOOK_TIMEOUT = 30  # seconds


def filter_pending_invites(filepath: str) -> List[str]:
    """Read a newline-delimited JSON file and filter for pending invites.

    This function processes a newline-delimited JSON file (NDJSON), filtering
    for entries where status is "pending" and returns their invite_ids.

    Args:
        filepath: The path to the newline-delimited JSON file.

    Returns:
        List[str]: A list of invite_ids for entries with pending status.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    pending_invite_ids = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip():  # Skip empty lines
                    entry = json.loads(line)
                    if entry.get('status') == 'pending':
                        invite_id = entry.get('invite_id')
                        if invite_id:
                            pending_invite_ids.append(invite_id)
                            print(f"Found pending invite: {invite_id}")
    
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON at line {e.lineno}: {e.msg}")
        raise
    
    return pending_invite_ids


def validate_json_file(filepath: str) -> List[Dict[str, Any]]:
    """Validate and parse a newline-delimited JSON file.

    This function reads a file line by line, validates each line as JSON,
    and collects all valid JSON objects. Invalid entries are logged but do not
    cause the function to fail.

    Args:
        filepath: Path to the newline-delimited JSON file to validate.

    Returns:
        List[Dict[str, Any]]: List of valid JSON objects from the file.
                             Returns empty list if file doesn't exist or contains no valid JSON.
    """
    valid_objects = []
    file_path = Path(filepath)

    if not file_path.exists():
        logger.error(
            f"File not found: {filepath}",
            extra={"filepath": str(file_path)}
        )
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                try:
                    json_obj = json.loads(line)
                    valid_objects.append(json_obj)
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Invalid JSON at line {line_num}",
                        extra={
                            "line_number": line_num,
                            "error": str(e),
                            "line_content": line[:100]  # First 100 chars for context
                        }
                    )

        logger.info(
            f"Successfully processed JSON file",
            extra={
                "filepath": str(file_path),
                "valid_objects_count": len(valid_objects),
                "total_lines": line_num
            }
        )

    except Exception as e:
        logger.error(
            f"Error processing file: {str(e)}",
            extra={
                "filepath": str(file_path),
                "error_type": type(e).__name__
            }
        )
        return []

    return valid_objects 


def write_pending_invites(json_list: List[Dict[str, Any]], output_path: str) -> bool:
    """Write pending invite entries to a JSON Lines file.

    This function filters a list of JSON objects for entries with status="pending"
    and writes them to a file in JSON Lines format (one object per line).

    Args:
        json_list: List of JSON objects to filter and write
        output_path: Path where the output file should be written

    Returns:
        bool: True if writing was successful, False otherwise

    Example:
        >>> data = [
        ...     {"id": 1, "status": "pending", "name": "Alice"},
        ...     {"id": 2, "status": "approved", "name": "Bob"},
        ...     {"id": 3, "status": "pending", "name": "Charlie"}
        ... ]
        >>> write_pending_invites(data, "pending_invites.jsonl")
        True
    """
    if not json_list:
        logger.warning(
            "Empty JSON list provided",
            extra={"output_path": output_path}
        )
        return False

    try:
        # Filter for pending entries
        pending_entries = [
            entry for entry in json_list
            if isinstance(entry, dict) and entry.get("status") == "pending"
        ]

        if not pending_entries:
            logger.info(
                "No pending entries found in the input list",
                extra={"total_entries": len(json_list)}
            )
            return False

        # Create directory if it doesn't exist
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write filtered entries to file
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in pending_entries:
                json_line = json.dumps(entry, ensure_ascii=False)
                f.write(json_line + '\n')

        logger.info(
            "Successfully wrote pending entries to file",
            extra={
                "output_path": str(output_path),
                "total_entries": len(json_list),
                "pending_entries": len(pending_entries)
            }
        )
        return True

    except TypeError as e:
        logger.error(
            "Invalid JSON object encountered",
            extra={
                "error": str(e),
                "output_path": str(output_path)
            }
        )
        return False

    except IOError as e:
        logger.error(
            "Failed to write to output file",
            extra={
                "error": str(e),
                "output_path": str(output_path)
            }
        )
        return False

    except Exception as e:
        logger.error(
            "Unexpected error while writing pending invites",
            extra={
                "error_type": type(e).__name__,
                "error": str(e),
                "output_path": str(output_path)
            }
        )
        return False 


def trigger_webhook(data: Dict[str, Any], url: str) -> bool:
    """Send a webhook POST request with JSON payload.

    This function sends an HTTP POST request to the specified URL with the provided
    data as JSON payload. It follows MAS Lite Protocol v2.1 specifications for
    webhook communication.

    Args:
        data: Dictionary containing the JSON payload to send
        url: Target URL for the webhook POST request

    Returns:
        bool: True if request was successful (status code 200), False otherwise

    Example:
        >>> data = {"event": "invite_created", "id": "123"}
        >>> success = trigger_webhook(data, "https://api.example.com/webhook")
        >>> print(success)
        True
    """
    if not data or not url:
        logger.error(
            "Invalid webhook parameters",
            extra={
                "url": url,
                "has_data": bool(data)
            }
        )
        return False

    try:
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'MAS-Lite/2.1'
        }

        # Send POST request
        response = requests.post(
            url,
            json=data,  # automatically handles JSON encoding
            headers=headers,
            timeout=WEBHOOK_TIMEOUT
        )

        # Log response details
        logger.info(
            f"Webhook response received",
            extra={
                "url": url,
                "status_code": response.status_code,
                "response_length": len(response.text),
                "elapsed_ms": response.elapsed.total_seconds() * 1000
            }
        )

        # Check if request was successful
        if response.status_code == 200:
            return True
        else:
            logger.error(
                f"Webhook request failed with status {response.status_code}",
                extra={
                    "url": url,
                    "status_code": response.status_code,
                    "response_text": response.text[:200]  # First 200 chars of response
                }
            )
            return False

    except Timeout:
        logger.error(
            f"Webhook request timed out after {WEBHOOK_TIMEOUT} seconds",
            extra={
                "url": url,
                "timeout": WEBHOOK_TIMEOUT
            }
        )
        return False

    except RequestException as e:
        logger.error(
            "Webhook request failed",
            extra={
                "url": url,
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )
        return False

    except Exception as e:
        logger.error(
            "Unexpected error during webhook request",
            extra={
                "url": url,
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )
        return False 