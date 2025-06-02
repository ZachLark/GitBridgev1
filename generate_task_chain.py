#!/usr/bin/env python3
"""
Task Chain Generator for GitBridge MAS Protocol System.

This script generates and manages task chains for the MAS Lite Protocol v2.1,
creating properly structured JSON entries for consensus tasks across phases.

Features:
- Interactive CLI-driven task generation
- Batch mode support (--batch)
- Atomic file operations with proper locking
- Full MAS Lite Protocol v2.1 compliance
- Extensible for future protocol versions
- Task chain summarization and analytics

Future Development (TODO):
- Add --preview flag to display entries before writing
- Add --errorsim flag to simulate malformed tasks/paths
- Add --logfile arg to override default mas_log.json
- Add unit test suite with pytest
- Add task chain log generation (task_chain_log.json)
- Add plugin system for v2.2+ field extensions
- Add performance optimizations for 50+ task generation
- Add batch import/export functionality
"""

import json
import sys
import fcntl
import random
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, NoReturn, Optional, Tuple
from dataclasses import dataclass, field
import itertools
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor
import signal
import resource
from contextlib import contextmanager
from collections import Counter
import threading


# Constants for task generation
PRIORITY_LEVELS = ["low", "medium", "high"]
SECTION_CODES = ["1.1", "1.2", "2.0", "2.1", "3.0", "3.1", "4.0"]
DEFAULT_DESCRIPTIONS = [
    "Review code changes for consensus approval",
    "Validate architectural changes",
    "Assess performance impact",
    "Review security implications",
    "Evaluate documentation updates"
]

# Default agent assignments as per MAS Protocol v2.1
DEFAULT_AGENT_ASSIGNMENT = {
    "grok": "generate_draft",
    "chatgpt": "review_draft"
}

CHUNK_SIZE = 10  # Number of tasks to write at once

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] %(message)s',
    handlers=[
        logging.FileHandler('task_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def random_sections() -> List[str]:
    """Generate a random list of section codes."""
    return random.sample(SECTION_CODES, k=random.randint(1, 3))


def copy_agent_assignment() -> Dict[str, str]:
    """Create a copy of the default agent assignment."""
    return DEFAULT_AGENT_ASSIGNMENT.copy()


def random_description() -> str:
    """Generate a random description."""
    return random.choice(DEFAULT_DESCRIPTIONS)


def random_priority() -> str:
    """Generate a random priority level."""
    return random.choice(PRIORITY_LEVELS)


@dataclass
class TaskParams:
    """Data class for task parameters with validation."""
    phase_id: str
    task_counter: int
    description: str = field(default_factory=random_description)
    consensus: str = "pending"
    priority_level: str = field(default_factory=random_priority)
    sections_reviewed: List[str] = field(default_factory=random_sections)
    agent_assignment: Dict[str, str] = field(default_factory=copy_agent_assignment)

    def __post_init__(self) -> None:
        """Validate parameters after initialization."""
        if not self.phase_id:
            raise ValueError("phase_id cannot be empty")
        if not isinstance(self.task_counter, int) or self.task_counter < 0:
            raise ValueError("task_counter must be a non-negative integer")
        if self.priority_level not in PRIORITY_LEVELS:
            raise ValueError(f"priority_level must be one of {PRIORITY_LEVELS}")


class TaskGenerationError(Exception):
    """Base exception for task generation errors."""


class LogFileError(TaskGenerationError):
    """Exception for log file related errors."""


class ResourceExceededError(Exception):
    """Raised when resource limits are exceeded."""


@contextmanager
def resource_limit(memory_mb=1000, timeout_sec=30):
    """Set resource limits for the operation."""
    def handle_timeout(signum, frame):
        raise TimeoutError("Operation timed out")

    # Set memory limit
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        new_limit = min(memory_mb * 1024 * 1024, hard)
        resource.setrlimit(resource.RLIMIT_AS, (new_limit, hard))
    except ValueError:
        logger.warning("Could not set memory limit - continuing without limit")
        pass  # Continue without memory limit in test environments

    # Set timeout only in main thread
    is_main_thread = threading.current_thread() is threading.main_thread()
    if is_main_thread:
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(timeout_sec)

    try:
        yield
    finally:
        if is_main_thread:
            signal.alarm(0)
        try:
            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
        except ValueError:
            pass  # Ignore errors when resetting limits


def generate_task_id(phase_id: str, counter: int) -> str:
    """
    Generate a unique task ID.

    Args:
        phase_id: The phase identifier
        counter: Task counter within the phase

    Returns:
        Formatted task ID string
    """
    return f"task_{phase_id}_{counter:03d}"


def generate_output_paths(task_id: str) -> Dict[str, str]:
    """
    Generate output file paths with placeholder hashes.

    Args:
        task_id: The task identifier

    Returns:
        Dictionary of output paths with placeholder hashes
    """
    return {
        "grok_draft": f"outputs/{task_id}_grok.docx#sha256=placeholder",
        "review_notes": f"outputs/{task_id}_review.md#sha256=placeholder"
    }


def generate_single_task(params: TaskParams) -> Dict[str, Any]:
    """
    Generate a single task entry.

    Args:
        params: TaskParams instance with task parameters

    Returns:
        Dictionary containing the task entry

    Raises:
        TaskGenerationError: If task generation fails
    """
    try:
        current_time = datetime.now(timezone.utc).isoformat()
        task_id = generate_task_id(params.phase_id, params.task_counter)

        return {
            "task_id": task_id,
            "phase_id": params.phase_id,
            "description": params.description,
            "timestamp": current_time,
            "consensus": params.consensus,
            "status_history": [
                {
                    "status": "pending",
                    "timestamp": current_time
                }
            ],
            "agent_assignment": params.agent_assignment,
            "outputs": generate_output_paths(task_id),
            "priority_level": params.priority_level,
            "sections_reviewed": sorted(params.sections_reviewed)
        }
    except (ValueError, KeyError, TypeError) as e:
        raise TaskGenerationError(f"Failed to generate task: {str(e)}") from e


def load_log_file(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load the existing log file with proper locking.

    Args:
        log_path: Path to the log file

    Returns:
        List of existing task entries

    Raises:
        LogFileError: If there are issues reading the file
    """
    try:
        if not log_path.exists():
            return []

        with log_path.open('r', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Log file must contain a JSON array")
                return data
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (json.JSONDecodeError, IOError) as e:
        raise LogFileError(f"Failed to read log file: {str(e)}") from e


def write_to_log(log_path: Path, entries: List[Dict[str, Any]]) -> None:
    """Write task entries with resource limits and monitoring."""
    try:
        with resource_limit():
            # Ensure the outputs directory exists
            output_dir = log_path.parent / "outputs"
            output_dir.mkdir(exist_ok=True, parents=True)

            # Process entries in chunks
            chunks = [entries[i:i + CHUNK_SIZE] for i in range(0, len(entries), CHUNK_SIZE)]
            
            with tqdm(total=len(entries), desc="Writing tasks") as pbar:
                for chunk in chunks:
                    # Use a single exclusive lock for the entire read-modify-write operation
                    with log_path.open('r+' if log_path.exists() else 'w', encoding='utf-8') as f:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                        try:
                            logger.debug("Acquired exclusive lock for atomic read-write")
                            
                            # Read existing entries
                            try:
                                f.seek(0)
                                existing_entries = json.load(f) if log_path.exists() and log_path.stat().st_size > 0 else []
                                if not isinstance(existing_entries, list):
                                    raise ValueError("Log file must contain a JSON array")
                            except json.JSONDecodeError:
                                logger.warning("JSON decode error, resetting file")
                                existing_entries = []
                            
                            # Deduplicate entries based on task_id
                            task_ids = {task["task_id"] for task in existing_entries}
                            new_entries = [
                                task for task in chunk
                                if task["task_id"] not in task_ids
                            ]
                            
                            # Write updated content
                            f.seek(0)
                            f.truncate()
                            json.dump(existing_entries + new_entries, f, indent=2, ensure_ascii=False)
                            
                            logger.info(f"Successfully wrote chunk of {len(new_entries)} tasks")
                            pbar.update(len(chunk))
                        finally:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                            logger.debug("Released exclusive lock")

            logger.info(f"✅ Successfully wrote {len(entries)} tasks to {log_path}")
    except TimeoutError:
        logger.error("Task writing operation timed out")
        raise LogFileError("Operation timed out")
    except MemoryError:
        logger.error("Memory limit exceeded")
        raise ResourceExceededError("Memory limit exceeded")
    except (IOError, OSError) as e:
        logger.error(f"Failed to write to log file: {e}")
        raise LogFileError(f"Failed to write to log file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while writing to log: {e}")
        raise LogFileError(f"Unexpected error while writing to log: {e}")


def handle_error(error: Exception) -> NoReturn:
    """
    Handle errors uniformly across the application.

    Args:
        error: The exception to handle

    Returns:
        Never returns, always exits with status 1
    """
    error_msg = str(error).strip() or error.__class__.__name__
    print(f"❌ Error: {error_msg}", file=sys.stderr)
    sys.exit(1)


def generate_tasks_interactive() -> None:
    """
    Generate tasks interactively based on user input.

    This function handles the interactive CLI workflow for task generation.
    """
    try:
        # Get user input
        phase_id = input("Enter phase ID: ").strip()
        if not phase_id:
            raise ValueError("Phase ID cannot be empty")

        task_count = input("Enter number of tasks to generate: ").strip()
        try:
            task_count = int(task_count)
            if task_count < 1:
                raise ValueError("Task count must be a positive integer")
        except ValueError as exc:
            raise ValueError("Task count must be a positive integer") from exc

        # Generate tasks
        tasks = []
        print(f"🔄 Generating {task_count} tasks for phase {phase_id}...")

        for i in range(task_count):
            params = TaskParams(phase_id=phase_id, task_counter=i)
            task = generate_single_task(params)
            tasks.append(task)
            print(f"  ✓ Generated task {task['task_id']}")

        # Write to log file
        log_path = Path("mas_log.json")
        write_to_log(log_path, tasks)

    except (ValueError, TaskGenerationError, LogFileError) as e:
        handle_error(e)


def generate_tasks_batch(config_file: Path) -> None:
    """Generate tasks in batch mode with monitoring."""
    try:
        with resource_limit(memory_mb=2000, timeout_sec=60):
            logger.info(f"Starting batch task generation from config: {config_file}")
            with config_file.open('r', encoding='utf-8') as f:
                config = json.load(f)

            phase_id = config.get('phase_id')
            task_count = config.get('task_count')

            if not phase_id or not isinstance(task_count, int) or task_count < 1:
                raise ValueError("Config must specify valid phase_id and task_count")

            custom_descriptions = config.get('descriptions', DEFAULT_DESCRIPTIONS)
            custom_priorities = config.get('priority_levels', PRIORITY_LEVELS)
            custom_sections = config.get('sections', None)

            logger.info(f"Generating {task_count} tasks for phase {phase_id}")
            tasks = []

            # Use ThreadPoolExecutor for parallel task generation
            with ThreadPoolExecutor() as executor:
                def generate_task(i):
                    logger.debug(f"Generating task {i}")
                    params = TaskParams(
                        phase_id=phase_id,
                        task_counter=i,
                        description=random.choice(custom_descriptions),
                        priority_level=random.choice(custom_priorities)
                    )
                    if custom_sections:
                        params.sections_reviewed = random.choice(custom_sections)
                    return generate_single_task(params)

                tasks = list(executor.map(generate_task, range(task_count)))

            log_path = Path("mas_log.json")
            write_to_log(log_path, tasks)

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Error in batch processing: {str(e)}")
        handle_error(e)
    except (TimeoutError, MemoryError) as e:
        logger.error(f"Resource limit exceeded: {str(e)}")
        raise ResourceExceededError(str(e))


@dataclass
class TaskChainSummary:
    """Summary statistics for a task chain."""
    phase_id: str
    total_tasks: int
    priority_distribution: Dict[str, int]
    section_coverage: Dict[str, int]
    consensus_status: Dict[str, int]
    agent_distribution: Dict[str, Dict[str, int]]
    start_time: str
    end_time: str
    completion_rate: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary format."""
        return {
            "phase_id": self.phase_id,
            "total_tasks": self.total_tasks,
            "priority_distribution": self.priority_distribution,
            "section_coverage": self.section_coverage,
            "consensus_status": self.consensus_status,
            "agent_distribution": self.agent_distribution,
            "time_range": {
                "start": self.start_time,
                "end": self.end_time
            },
            "completion_rate": self.completion_rate
        }


def summarize_task_chain(tasks: List[Dict[str, Any]], phase_id: Optional[str] = None) -> TaskChainSummary:
    """
    Generate a summary of the task chain.

    Args:
        tasks: List of task entries
        phase_id: Optional phase ID to filter tasks

    Returns:
        TaskChainSummary object with statistics
    """
    if not tasks:
        raise ValueError("No tasks provided for summarization")

    # Filter by phase if specified
    if phase_id:
        tasks = [t for t in tasks if t.get("phase_id") == phase_id]
        if not tasks:
            raise ValueError(f"No tasks found for phase {phase_id}")

    # Extract phase ID from first task if not specified
    phase_id = phase_id or tasks[0].get("phase_id")

    # Calculate priority distribution
    priority_dist = Counter(task.get("priority_level", "unknown") for task in tasks)

    # Calculate section coverage
    section_coverage = Counter(
        section
        for task in tasks
        for section in task.get("sections_reviewed", [])
    )

    # Calculate consensus status distribution
    consensus_dist = Counter(task.get("consensus", "unknown") for task in tasks)

    # Calculate agent distribution
    agent_dist: Dict[str, Dict[str, int]] = {}
    for task in tasks:
        for agent, role in task.get("agent_assignment", {}).items():
            if agent not in agent_dist:
                agent_dist[agent] = Counter()
            agent_dist[agent][role] += 1

    # Calculate time range
    timestamps = [
        datetime.fromisoformat(task["timestamp"])
        for task in tasks
        if "timestamp" in task
    ]
    start_time = min(timestamps).isoformat() if timestamps else "unknown"
    end_time = max(timestamps).isoformat() if timestamps else "unknown"

    # Calculate completion rate
    completed = sum(1 for task in tasks if task.get("consensus") in ["approved", "rejected"])
    completion_rate = (completed / len(tasks)) * 100 if tasks else 0

    return TaskChainSummary(
        phase_id=phase_id,
        total_tasks=len(tasks),
        priority_distribution=dict(priority_dist),
        section_coverage=dict(section_coverage),
        consensus_status=dict(consensus_dist),
        agent_distribution=agent_dist,
        start_time=start_time,
        end_time=end_time,
        completion_rate=completion_rate
    )


def write_summary_to_file(summary: TaskChainSummary, output_path: Optional[Path] = None) -> None:
    """
    Write task chain summary to a file.

    Args:
        summary: TaskChainSummary object
        output_path: Optional custom output path
    """
    if output_path is None:
        output_path = Path(f"task_chain_summary_{summary.phase_id}.json")

    try:
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(summary.to_dict(), f, indent=2)
        logger.info(f"✅ Summary written to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write summary: {e}")
        raise LogFileError(f"Failed to write summary: {e}")


def main() -> None:
    """Main function for CLI operation."""
    parser = argparse.ArgumentParser(
        description="Generate task chains for MAS Protocol system"
    )
    parser.add_argument(
        "--batch",
        type=str,
        help="Path to batch configuration file"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview tasks without writing to file"
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Generate and save task chain summary"
    )
    parser.add_argument(
        "--phase",
        type=str,
        help="Phase ID to summarize (optional)"
    )
    args = parser.parse_args()

    if args.summarize:
        try:
            log_path = Path("mas_log.json")
            tasks = load_log_file(log_path)
            summary = summarize_task_chain(tasks, args.phase)
            write_summary_to_file(summary)
            
            # Print summary to console
            print("\n📊 Task Chain Summary")
            print("===================")
            print(f"Phase: {summary.phase_id}")
            print(f"Total Tasks: {summary.total_tasks}")
            print(f"Completion Rate: {summary.completion_rate:.1f}%")
            print("\nPriority Distribution:")
            for priority, count in summary.priority_distribution.items():
                print(f"  {priority}: {count}")
            print("\nConsensus Status:")
            for status, count in summary.consensus_status.items():
                print(f"  {status}: {count}")
            print("\nSection Coverage:")
            for section, count in summary.section_coverage.items():
                print(f"  {section}: {count}")
            print("\nTime Range:")
            print(f"  Start: {summary.start_time}")
            print(f"  End: {summary.end_time}")
        except (ValueError, LogFileError) as e:
            handle_error(e)
        return

    if args.batch:
        config_path = Path(args.batch)
        if not config_path.exists():
            handle_error(ValueError(f"Config file not found: {args.batch}"))
        generate_tasks_batch(config_path)
    else:
        generate_tasks_interactive()


if __name__ == "__main__":
    main()
