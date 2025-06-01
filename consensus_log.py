#!/usr/bin/env python3
"""
Consensus Log Script for GitBridge Project.

This script manages the logging of consensus data between AI agents (Grok and ChatGPT)
in the GitBridge project. It appends new entries to mas_log.json with proper validation
and error handling.
"""

import json
import sys
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ConsensusParams:
    """Data class to hold consensus entry parameters."""
    task_id: str
    phase_id: str
    description: str
    grok_output_path: str
    chatgpt_output_path: str
    grok_hash: str
    chatgpt_hash: str
    sections_reviewed: List[str]
    priority_level: Optional[str] = None


def create_consensus_entry(params: ConsensusParams) -> Dict[str, Any]:
    """
    Create a new consensus entry with the provided parameters and auto-populated fields.

    Args:
        params: ConsensusParams object containing all required fields

    Returns:
        Dict containing the consensus entry

    Raises:
        ValueError: If any required fields are missing or invalid
    """
    # Validate priority level if provided
    if params.priority_level and params.priority_level not in ["low", "medium", "high"]:
        raise ValueError("Priority level must be one of: low, medium, high")

    # Validate file paths
    if not os.path.exists(params.grok_output_path):
        raise ValueError(f"Grok output file not found: {params.grok_output_path}")
    if not os.path.exists(params.chatgpt_output_path):
        raise ValueError(f"ChatGPT output file not found: {params.chatgpt_output_path}")
    if not params.grok_output_path.endswith('.docx'):
        raise ValueError("Grok output must be a .docx file")
    if not params.chatgpt_output_path.endswith('.json'):
        raise ValueError("ChatGPT output must be a .json file")

    # Get current timestamp in ISO 8601 format with UTC offset
    current_time = datetime.now(timezone.utc).isoformat()

    return {
        "task_id": params.task_id,
        "phase_id": params.phase_id,
        "description": params.description,
        "timestamp": current_time,
        "consensus": "pending",
        "status_history": [
            {
                "status": "pending",
                "timestamp": current_time
            }
        ],
        "manual_notes": "",
        "agent_assignment": {
            "grok": "generate_draft",
            "chatgpt": "review_draft"
        },
        "outputs": {
            "grok": {
                "path": params.grok_output_path,
                "hash": params.grok_hash
            },
            "chatgpt": {
                "path": params.chatgpt_output_path,
                "hash": params.chatgpt_hash
            }
        },
        "sections_reviewed": params.sections_reviewed,
        "priority_level": params.priority_level or "medium"  # Default to medium if not specified
    }


def append_to_log(entry: Dict[str, Any], log_path: Path = Path("mas_log.json")) -> None:
    """
    Append a new entry to the consensus log file.

    Args:
        entry: Dictionary containing the consensus entry
        log_path: Path to the log file (defaults to mas_log.json in current directory)

    Raises:
        IOError: If there are issues reading or writing the log file
        json.JSONDecodeError: If the existing log file contains invalid JSON
    """
    try:
        if log_path.exists():
            with log_path.open('r', encoding='utf-8') as f:
                log_data = json.load(f)
                if not isinstance(log_data, list):
                    raise ValueError("Existing log file must contain a JSON array")
        else:
            log_data = []

        log_data.append(entry)

        with log_path.open('w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse existing log file: {e.msg}", e.doc, e.pos
        ) from e
    except IOError as e:
        raise IOError(f"Failed to read/write log file: {str(e)}") from e


def cli_input() -> ConsensusParams:
    """
    Get consensus entry parameters through command-line interaction.

    Returns:
        ConsensusParams object containing the input parameters
    """
    print("Enter consensus entry details:")
    sections = input("Sections reviewed (comma-separated): ").split(",")
    sections = [s.strip() for s in sections if s.strip()]
    
    priority = input(
        "Priority level (low/medium/high, press Enter for medium): "
    ).strip() or None

    params = ConsensusParams(
        task_id=input("Task ID: ").strip(),
        phase_id=input("Phase ID: ").strip(),
        description=input("Description: ").strip(),
        grok_output_path=input("Grok output path (.docx): ").strip(),
        chatgpt_output_path=input("ChatGPT output path (.json): ").strip(),
        grok_hash=input("Grok output hash: ").strip(),
        chatgpt_hash=input("ChatGPT output hash: ").strip(),
        sections_reviewed=sections,
        priority_level=priority
    )

    # Validate required fields
    for field in [
        params.task_id, params.phase_id, params.description,
        params.grok_output_path, params.chatgpt_output_path,
        params.grok_hash, params.chatgpt_hash
    ]:
        if not field:
            raise ValueError(f"Missing required field")

    return params


def main() -> None:
    """Main function for CLI operation."""
    try:
        params = cli_input()
        entry = create_consensus_entry(params)
        append_to_log(entry)
        print("Successfully added consensus entry to mas_log.json")
    except (ValueError, IOError, json.JSONDecodeError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 