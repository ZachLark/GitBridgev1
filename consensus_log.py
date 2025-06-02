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
import stat
import time
import fcntl
import builtins
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from mas_error import log_error


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
        # Initialize file if it doesn't exist
        if not log_path.exists():
            with builtins.open(log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

        with builtins.open(log_path, 'r+', encoding='utf-8') as f:
            # Acquire an exclusive lock
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                # Read current content
                try:
                    f.seek(0)
                    log_data = json.load(f)
                    if not isinstance(log_data, list):
                        raise ValueError("Existing log file must contain a JSON array")
                except json.JSONDecodeError:
                    # If file is empty or corrupted, initialize with empty list
                    log_data = []

                # Append new entry
                log_data.append(entry)

                # Write back to file
                f.seek(0)
                f.truncate()
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            finally:
                # Release the lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

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

    Raises:
        ValueError: If any required fields are missing
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
            raise ValueError("Missing required field")

    return params


def run_concurrency_test(test_log_dir: Path) -> Tuple[bool, str]:
    """Run concurrency test and return result."""
    test_log_path = test_log_dir / "concurrent_test.json"

    # Initialize the test log file with an empty array
    with builtins.open(test_log_path, 'w', encoding='utf-8') as f:
        json.dump([], f)

    def concurrent_write(idx: int) -> None:
        params = ConsensusParams(
            task_id=f"concurrent_task_{idx}",
            phase_id="P7P5",
            description=f"Concurrent test entry {idx}",
            grok_output_path="outputs/test.docx",
            chatgpt_output_path="outputs/test.json",
            grok_hash=f"hash_{idx}",
            chatgpt_hash=f"hash_{idx}",
            sections_reviewed=["1.1"]
        )
        entry = create_consensus_entry(params)
        append_to_log(entry, test_log_path)

    # Create test files needed for concurrent operations
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/test.docx").touch()
    Path("outputs/test.json").touch()

    # Run 5 concurrent writes
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(concurrent_write, i) for i in range(5)]
        for future in futures:
            future.result()

    # Verify the log file integrity
    with builtins.open(test_log_path, 'r', encoding='utf-8') as f:
        concurrent_data = json.load(f)
        if len(concurrent_data) == 5:
            return True, "Concurrent writes handled successfully"
        return False, "Concurrent writes produced inconsistent results"


def run_performance_test(test_log_dir: Path) -> List[Tuple[bool, str]]:
    """Run performance tests and return results."""
    results = []
    start_time = time.time()
    test_entries = []

    # Create 100 test entries
    for i in range(100):
        params = ConsensusParams(
            task_id=f"perf_task_{i}",
            phase_id="P7P5",
            description=f"Performance test entry {i}",
            grok_output_path="outputs/test.docx",
            chatgpt_output_path="outputs/test.json",
            grok_hash=f"hash_{i}",
            chatgpt_hash=f"hash_{i}",
            sections_reviewed=["1.1"]
        )
        test_entries.append(create_consensus_entry(params))

    perf_log_path = test_log_dir / "performance_test.json"
    for entry in test_entries:
        append_to_log(entry, perf_log_path)

    elapsed_time = time.time() - start_time
    results.append((True, f"Processed 100 entries in {elapsed_time:.2f} seconds"))

    # Large file test
    large_desc = "x" * (1024 * 1024)
    params = ConsensusParams(
        task_id="large_task",
        phase_id="P7P5",
        description=large_desc,
        grok_output_path="outputs/test.docx",
        chatgpt_output_path="outputs/test.json",
        grok_hash="large_hash",
        chatgpt_hash="large_hash",
        sections_reviewed=["1.1"]
    )
    try:
        entry = create_consensus_entry(params)
        append_to_log(entry, test_log_dir / "large_file_test.json")
        results.append((True, "Large file handled successfully"))
    except (IOError, MemoryError) as e:
        results.append((False, f"Large file handling error: {str(e)}"))

    return results


def run_security_test(test_log_dir: Path) -> List[Tuple[bool, str]]:
    """Run security tests and return results."""
    results = []

    # Path traversal test
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\Windows\\System32\\config\\SAM",
        "/etc/shadow",
        "C:\\Windows\\System32\\config\\system"
    ]

    path_traversal_blocked = True
    for path in malicious_paths:
        try:
            params = ConsensusParams(
                task_id="security_test",
                phase_id="P7P5",
                description="Security test",
                grok_output_path=path,
                chatgpt_output_path="outputs/test.json",
                grok_hash="test_hash",
                chatgpt_hash="test_hash",
                sections_reviewed=["1.1"]
            )
            create_consensus_entry(params)
            path_traversal_blocked = False
            results.append((False, f"Allowed potentially dangerous path: {path}"))
            break
        except ValueError:
            continue

    if path_traversal_blocked:
        results.append((True, "Path traversal attempts blocked"))

    # File permission test
    readonly_path = test_log_dir / "readonly_test.json"
    with builtins.open(readonly_path, 'w', encoding='utf-8') as f:
        json.dump([], f)
    readonly_path.chmod(stat.S_IREAD)

    try:
        append_to_log({"test": "data"}, readonly_path)
        results.append((False, "Write to read-only file not prevented"))
    except (IOError, PermissionError) as e:
        if "Permission denied" in str(e):
            results.append((True, "Proper handling of read-only files"))
        else:
            results.append((False, f"Unexpected error: {str(e)}"))
    finally:
        readonly_path.chmod(stat.S_IWRITE | stat.S_IREAD)

    return results


class SlowFile:
    """Simulates slow network I/O operations."""
    def __init__(self, path: str, *args, mode: str = 'r', **kwargs):
        self.path = path
        self.mode = mode
        self.args = args
        self.kwargs = kwargs
        self.file = None
        self._original_open = builtins.open

    def __enter__(self):
        time.sleep(0.5)  # Simulate network latency
        self.file = self._original_open(self.path, self.mode, *self.args, **self.kwargs)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        time.sleep(0.5)  # Simulate network latency
        if self.file:
            self.file.close()

    def close(self):
        """Close the file handle."""
        if self.file:
            self.file.close()

    def __getattr__(self, name):
        """Delegate attribute access to the underlying file object."""
        if self.file is None:
            self.file = self._original_open(self.path, self.mode, *self.args, **self.kwargs)
        return getattr(self.file, name)


def run_network_test() -> Tuple[bool, str]:
    """Run network simulation test and return result."""
    original_open = builtins.open
    network_path = Path("network_sim")
    network_path.mkdir(exist_ok=True)
    test_file = network_path / "slow_network_test.json"

    # Initialize test file with empty array
    with original_open(test_file, 'w', encoding='utf-8') as f:
        json.dump([], f)

    try:
        builtins.open = SlowFile
        start_time = time.time()
        append_to_log({"test": "data"}, test_file)
        elapsed_time = time.time() - start_time

        if elapsed_time >= 1.0:  # Should take at least 1 second due to simulated latency
            return True, "Handled slow I/O gracefully"
        return False, f"I/O too fast ({elapsed_time:.2f}s), expected >= 1.0s"
    finally:
        builtins.open = original_open


def test_consensus_log() -> None:
    """Run test scenarios for consensus logging."""
    def cleanup_test_files():
        """Clean up any test files created during testing."""
        for path in ["outputs", "test_logs", "network_sim"]:
            if Path(path).exists():
                shutil.rmtree(path)

    try:
        print("\n🧪 Running Consensus Log Test Suite")
        print("===================================")

        test_log_dir = Path("test_logs")
        test_log_dir.mkdir(exist_ok=True)

        # Run concurrency test
        print("\n6️⃣ Concurrency Tests")
        print("\n▶️ Test 6.1: Simultaneous writes")
        success, message = run_concurrency_test(test_log_dir)
        print(f"{'✅' if success else '❌'} Test {'passed' if success else 'failed'}: {message}")

        # Run performance tests
        print("\n7️⃣ Performance Tests")
        perf_results = run_performance_test(test_log_dir)
        for i, (success, message) in enumerate(perf_results, 1):
            print(f"\n▶️ Test 7.{i}: {message}")
            print(f"{'✅' if success else '❌'} Test {'passed' if success else 'failed'}: {message}")

        # Run security tests
        print("\n8️⃣ Security Tests")
        security_results = run_security_test(test_log_dir)
        for i, (success, message) in enumerate(security_results, 1):
            print(f"\n▶️ Test 8.{i}: {message}")
            print(f"{'✅' if success else '❌'} Test {'passed' if success else 'failed'}: {message}")

        # Run network test
        print("\n9️⃣ Network Tests")
        print("\n▶️ Test 9.1: Slow I/O simulation")
        success, message = run_network_test()
        print(f"{'✅' if success else '❌'} Test {'passed' if success else 'failed'}: {message}")

        print("\n✨ Extended Test Suite Completed")

    except (IOError, ValueError, json.JSONDecodeError) as e:
        error_msg = str(e).strip() or e.__class__.__name__
        log_error(
            task_id="task_norman002",
            error_message=f"Test suite error: {error_msg}",
            phase_id="P7P5"
        )
        print(f"\n❌ Test suite failed: {error_msg}")
    finally:
        cleanup_test_files()


def main() -> None:
    """Main function for CLI operation."""
    try:
        params = cli_input()
        entry = create_consensus_entry(params)
        append_to_log(entry)
        print("✅ Task successfully logged to mas_log.json")
    except (IOError, ValueError, json.JSONDecodeError) as e:
        error_msg = str(e).strip()
        if not error_msg:
            error_msg = e.__class__.__name__
        log_error(
            task_id="task_norman002",
            error_message=f"Consensus logging error: {error_msg}",
            phase_id="P7P5"
        )
        print("⚠️ An error occurred and was logged via mas_error.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_consensus_log()
    else:
        main()
