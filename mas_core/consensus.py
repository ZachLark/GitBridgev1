"""
MAS Consensus Module.

This module implements the consensus management system for the MAS Lite Protocol v2.1,
handling voting, state transitions, and consensus resolution for tasks.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
from .utils.validation import validate_task_id, ValidationError
from .utils.logging import MASLogger
from .metrics import MetricsCollector

class ConsensusState(str, Enum):
    """Possible states for consensus."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEADLOCKED = "deadlocked"
    TIMEOUT = "timeout"

class VoteType(str, Enum):
    """Possible vote types."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"

@dataclass
class Vote:
    """Represents a single vote in the consensus process."""
    agent_id: str
    vote_type: VoteType
    timestamp: str
    comment: Optional[str] = None

@dataclass
class ConsensusRound:
    """Represents a single round of consensus voting."""
    round_id: str
    start_time: str
    votes: Dict[str, Vote]
    state: ConsensusState
    end_time: Optional[str] = None
    resolution: Optional[str] = None

class ConsensusManager:
    """Manages consensus process for tasks."""

    def __init__(self, required_votes: int = 2, timeout_seconds: int = 300) -> None:
        """
        Initialize consensus manager.

        Args:
            required_votes: Number of votes required for consensus
            timeout_seconds: Seconds before consensus times out
        """
        self.logger = MASLogger("consensus")
        self.metrics = MetricsCollector()
        self.required_votes = required_votes
        self.timeout_seconds = timeout_seconds
        self.consensus_rounds: Dict[str, List[ConsensusRound]] = {}
        self.active_voters: Dict[str, Set[str]] = {}  # task_id -> set of agent_ids

    @metrics.track_consensus_timing
    def start_consensus(self, task_id: str, eligible_voters: List[str]) -> bool:
        """
        Start a new consensus round for a task.

        Args:
            task_id: Task identifier
            eligible_voters: List of agent IDs eligible to vote

        Returns:
            bool: True if consensus round started successfully

        Raises:
            ValidationError: If task_id is invalid
        """
        if not validate_task_id(task_id):
            raise ValidationError(f"Invalid task_id: {task_id}")

        round_id = f"round_{len(self.consensus_rounds.get(task_id, []))}"
        timestamp = datetime.now(timezone.utc).isoformat()

        new_round = ConsensusRound(
            round_id=round_id,
            start_time=timestamp,
            votes={},
            state=ConsensusState.IN_PROGRESS
        )

        if task_id not in self.consensus_rounds:
            self.consensus_rounds[task_id] = []
        self.consensus_rounds[task_id].append(new_round)
        self.active_voters[task_id] = set(eligible_voters)

        self.logger.log_consensus(
            task_id=task_id,
            status="started",
            votes={}
        )
        return True

    def submit_vote(
        self, task_id: str, agent_id: str, vote: VoteType, comment: Optional[str] = None
    ) -> bool:
        """
        Submit a vote for the current consensus round.

        Args:
            task_id: Task identifier
            agent_id: Voting agent's identifier
            vote: Vote type
            comment: Optional comment with the vote

        Returns:
            bool: True if vote was accepted

        Raises:
            ValidationError: If inputs are invalid
            ValueError: If consensus round not found
        """
        if not validate_task_id(task_id):
            raise ValidationError(f"Invalid task_id: {task_id}")

        if task_id not in self.consensus_rounds:
            raise ValueError(f"No active consensus round for task {task_id}")

        current_round = self.consensus_rounds[task_id][-1]
        if current_round.state != ConsensusState.IN_PROGRESS:
            return False

        if agent_id not in self.active_voters[task_id]:
            raise ValidationError(f"Agent {agent_id} not eligible to vote on task {task_id}")

        # Record vote
        current_round.votes[agent_id] = Vote(
            agent_id=agent_id,
            vote_type=vote,
            timestamp=datetime.now(timezone.utc).isoformat(),
            comment=comment
        )

        self.logger.log_consensus(
            task_id=task_id,
            status="vote_received",
            votes={agent_id: vote.value}
        )

        # Check if we have all required votes
        if len(current_round.votes) >= self.required_votes:
            self._resolve_consensus(task_id)

        return True

    def _resolve_consensus(self, task_id: str) -> None:
        """
        Resolve consensus based on submitted votes.

        Args:
            task_id: Task identifier
        """
        current_round = self.consensus_rounds[task_id][-1]
        approve_count = sum(1 for v in current_round.votes.values() 
                          if v.vote_type == VoteType.APPROVE)
        reject_count = sum(1 for v in current_round.votes.values() 
                         if v.vote_type == VoteType.REJECT)

        timestamp = datetime.now(timezone.utc).isoformat()
        current_round.end_time = timestamp

        # Determine consensus
        if approve_count > reject_count:
            current_round.state = ConsensusState.APPROVED
            current_round.resolution = "Approved by majority"
        elif reject_count > approve_count:
            current_round.state = ConsensusState.REJECTED
            current_round.resolution = "Rejected by majority"
        else:
            current_round.state = ConsensusState.DEADLOCKED
            current_round.resolution = "No majority achieved"

        self.logger.log_consensus(
            task_id=task_id,
            status=current_round.state.value,
            votes={v.agent_id: v.vote_type.value for v in current_round.votes.values()}
        )

        # Update metrics
        if current_round.state in {ConsensusState.APPROVED, ConsensusState.REJECTED}:
            self.metrics.record_consensus_round(
                (datetime.fromisoformat(timestamp) - 
                 datetime.fromisoformat(current_round.start_time)).total_seconds()
            )
        else:
            self.metrics.record_consensus_failure()

    def get_consensus_state(self, task_id: str) -> Dict[str, Any]:
        """
        Get the current consensus state for a task.

        Args:
            task_id: Task identifier

        Returns:
            Dict containing consensus state information

        Raises:
            ValueError: If task not found
        """
        if task_id not in self.consensus_rounds:
            raise ValueError(f"No consensus rounds found for task {task_id}")

        current_round = self.consensus_rounds[task_id][-1]
        return {
            "task_id": task_id,
            "round_id": current_round.round_id,
            "state": current_round.state.value,
            "votes": {
                v.agent_id: {
                    "vote": v.vote_type.value,
                    "timestamp": v.timestamp,
                    "comment": v.comment
                } for v in current_round.votes.values()
            },
            "start_time": current_round.start_time,
            "end_time": current_round.end_time,
            "resolution": current_round.resolution,
            "total_rounds": len(self.consensus_rounds[task_id])
        }

    def get_consensus_history(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete consensus history for a task.

        Args:
            task_id: Task identifier

        Returns:
            List of consensus rounds and their details

        Raises:
            ValueError: If task not found
        """
        if task_id not in self.consensus_rounds:
            raise ValueError(f"No consensus rounds found for task {task_id}")

        return [
            {
                "round_id": round.round_id,
                "state": round.state.value,
                "votes": {
                    v.agent_id: {
                        "vote": v.vote_type.value,
                        "timestamp": v.timestamp,
                        "comment": v.comment
                    } for v in round.votes.values()
                },
                "start_time": round.start_time,
                "end_time": round.end_time,
                "resolution": round.resolution
            }
            for round in self.consensus_rounds[task_id]
        ] 