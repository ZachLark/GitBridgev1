"""
Consensus management for GitBridge MAS Lite implementation.

This module provides consensus management functionality for GitBridge's event processing
system, following MAS Lite Protocol v2.1 consensus requirements.

MAS Lite Protocol v2.1 References:
- Section 5.2: Consensus Requirements
- Section 5.3: Node Agreement
- Section 5.4: Error Handling
"""

import asyncio
import logging
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass
from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from .utils.logging import MASLogger

logger = MASLogger(__name__)

class ConsensusState(str, Enum):
    """Consensus states."""
    Pending = "pending"
    Approved = "approved"
    Rejected = "rejected"

class VoteType(str, Enum):
    """Vote types."""
    Approve = "approve"
    Reject = "reject"
    Abstain = "abstain"

class ConsensusError(Exception):
    """Base class for consensus-related errors."""
    pass

class ConsensusTimeoutError(ConsensusError):
    """Error raised when consensus times out."""
    pass

class ValidationError(ConsensusError):
    """Error raised when consensus validation fails."""
    pass

@dataclass
class ConsensusRound:
    """Consensus round data structure."""
    round_id: str
    task_id: str
    state: ConsensusState
    votes: Dict[str, VoteType]
    created_at: str
    updated_at: str
    required_nodes: int
    
    def validate(self) -> None:
        """Validate consensus round.
        
        Raises:
            ValidationError: If validation fails
        """
        if not self.round_id:
            raise ValidationError("Round ID is required")
            
        if not self.task_id:
            raise ValidationError("Task ID is required")
            
        if not isinstance(self.state, ConsensusState):
            raise ValidationError("Invalid consensus state")
            
        if not isinstance(self.votes, dict):
            raise ValidationError("Votes must be a dictionary")
            
        if not isinstance(self.required_nodes, int) or self.required_nodes <= 0:
            raise ValidationError("Required nodes must be a positive integer")
            
        try:
            datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            datetime.fromisoformat(self.updated_at.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValidationError(f"Invalid timestamp format: {str(e)}")
            
        for node_id, vote in self.votes.items():
            if not isinstance(node_id, str):
                raise ValidationError("Node ID must be a string")
            if not isinstance(vote, VoteType):
                raise ValidationError("Invalid vote type")

class ConsensusManager:
    """Consensus manager."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize consensus manager.

        Args:
            config: Configuration dictionary containing consensus settings
                   Required keys:
                   - consensus.timeout: Operation timeout in seconds
                   - consensus.required_nodes: Number of nodes required for consensus
        """
        self.timeout = config["consensus"]["timeout"]
        self.required_nodes = config["consensus"]["required_nodes"]
        self.rounds: Dict[str, ConsensusRound] = {}
        self.error_handler = ErrorHandler()

    async def get_consensus(self, task_id: str) -> ConsensusRound:
        """Get consensus for task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            ConsensusRound: Consensus round
            
        Raises:
            ConsensusTimeoutError: If consensus times out
        """
        try:
            # Create new consensus round
            round_id = str(uuid.uuid4())
            current_time = datetime.now(timezone.utc).isoformat()
            
            consensus_round = ConsensusRound(
                round_id=round_id,
                task_id=task_id,
                state=ConsensusState.Pending,
                votes={},
                created_at=current_time,
                updated_at=current_time,
                required_nodes=self.required_nodes
            )
            
            try:
                consensus_round.validate()
            except ValidationError as e:
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.CONSENSUS,
                    severity=ErrorSeverity.ERROR,
                    message=f"Invalid consensus round: {str(e)}",
                    details={
                        "task_id": task_id,
                        "round_id": round_id,
                        "error": str(e)
                    }
                )
                raise
                
            self.rounds[round_id] = consensus_round
            
            # Wait for consensus with timeout
            async with asyncio.timeout(self.timeout):
                while True:
                    # Check if consensus reached
                    approve_votes = sum(1 for vote in consensus_round.votes.values() if vote == VoteType.Approve)
                    reject_votes = sum(1 for vote in consensus_round.votes.values() if vote == VoteType.Reject)
                    
                    if approve_votes >= self.required_nodes:
                        consensus_round.state = ConsensusState.Approved
                        break
                    elif reject_votes >= self.required_nodes:
                        consensus_round.state = ConsensusState.Rejected
                        break
                    elif len(consensus_round.votes) >= self.required_nodes:
                        # We have enough votes but no consensus
                        raise ConsensusTimeoutError(f"Consensus timeout for task {task_id}")
                        
                    await asyncio.sleep(0.1)
                    
                consensus_round.updated_at = datetime.now(timezone.utc).isoformat()
                return consensus_round
                
        except asyncio.TimeoutError:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.CONSENSUS,
                severity=ErrorSeverity.ERROR,
                message=f"Consensus timeout for task {task_id}",
                details={
                    "task_id": task_id,
                    "round_id": round_id,
                    "timeout": self.timeout
                }
            )
            raise ConsensusTimeoutError(f"Consensus timeout for task {task_id}")
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.CONSENSUS,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to get consensus: {str(e)}",
                details={
                    "task_id": task_id,
                    "error": str(e)
                }
            )
            raise
            
    async def vote(self, round_id: str, node_id: str, vote: VoteType) -> bool:
        """Cast a vote.
        
        Args:
            round_id: Consensus round identifier
            node_id: Node identifier
            vote: Vote type
            
        Returns:
            bool: True if vote cast successfully
        """
        try:
            if round_id not in self.rounds:
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.CONSENSUS,
                    severity=ErrorSeverity.ERROR,
                    message=f"Invalid consensus round: {round_id}",
                    details={
                        "round_id": round_id,
                        "node_id": node_id
                    }
                )
                return False
                
            consensus_round = self.rounds[round_id]
            consensus_round.votes[node_id] = vote
            consensus_round.updated_at = datetime.now(timezone.utc).isoformat()
            
            try:
                consensus_round.validate()
            except ValidationError as e:
                error_id = str(uuid.uuid4())
                self.error_handler.handle_error(
                    error_id=error_id,
                    category=ErrorCategory.CONSENSUS,
                    severity=ErrorSeverity.ERROR,
                    message=f"Invalid vote: {str(e)}",
                    details={
                        "round_id": round_id,
                        "node_id": node_id,
                        "vote": vote,
                        "error": str(e)
                    }
                )
                return False
                
            logger.info(
                f"Vote cast for round {round_id}",
                extra={
                    "round_id": round_id,
                    "node_id": node_id,
                    "vote": vote
                }
            )
            return True
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.CONSENSUS,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to cast vote: {str(e)}",
                details={
                    "round_id": round_id,
                    "node_id": node_id,
                    "vote": vote,
                    "error": str(e)
                }
            )
            return False
            
    async def cleanup(self) -> None:
        """Clean up consensus resources."""
        try:
            # Clear consensus rounds
            self.rounds.clear()
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.CONSENSUS,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to clean up consensus manager: {str(e)}",
                details={"error": str(e)}
            ) 