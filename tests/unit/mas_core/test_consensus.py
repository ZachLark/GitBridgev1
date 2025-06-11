"""
Unit tests for consensus management.
"""

import asyncio
import pytest
from datetime import datetime, timezone
from mas_core.consensus import (
    ConsensusManager,
    ConsensusRound,
    ConsensusState,
    VoteType,
    ValidationError,
    ConsensusTimeoutError
)

@pytest.fixture
def consensus_config():
    """Test consensus configuration."""
    return {
        "consensus": {
            "timeout": 5,
            "required_nodes": 3
        }
    }

@pytest.fixture
def consensus_manager(consensus_config):
    """Test consensus manager instance."""
    return ConsensusManager(consensus_config)

@pytest.fixture
def consensus_round():
    """Test consensus round instance."""
    current_time = datetime.now(timezone.utc).isoformat()
    return ConsensusRound(
        round_id="test_round_001",
        task_id="test_task_001",
        state=ConsensusState.Pending,
        votes={},
        created_at=current_time,
        updated_at=current_time,
        required_nodes=3
    )

@pytest.mark.asyncio
async def test_consensus_round_validation(consensus_round):
    """Test consensus round validation."""
    # Valid round should not raise
    consensus_round.validate()

    # Test invalid task ID
    invalid_round = ConsensusRound(
        round_id="test_round_001",
        task_id="",
        state=ConsensusState.Pending,
        votes={},
        created_at=consensus_round.created_at,
        updated_at=consensus_round.updated_at,
        required_nodes=3
    )
    with pytest.raises(ValidationError, match="Task ID is required"):
        invalid_round.validate()

    # Test invalid round ID
    invalid_round = ConsensusRound(
        round_id="",
        task_id="test_task_001",
        state=ConsensusState.Pending,
        votes={},
        created_at=consensus_round.created_at,
        updated_at=consensus_round.updated_at,
        required_nodes=3
    )
    with pytest.raises(ValidationError, match="Round ID is required"):
        invalid_round.validate()

@pytest.mark.asyncio
async def test_get_consensus_success(consensus_manager):
    """Test successful consensus."""
    task_id = "test_task_001"
    consensus_task = asyncio.create_task(consensus_manager.get_consensus(task_id))
    
    # Wait a bit for the round to be created
    await asyncio.sleep(0.1)
    
    # Get the round ID
    round_id = list(consensus_manager.rounds.keys())[0]
    
    # Cast votes
    await consensus_manager.vote(round_id, "node_0", VoteType.Approve)
    await consensus_manager.vote(round_id, "node_1", VoteType.Approve)
    await consensus_manager.vote(round_id, "node_2", VoteType.Approve)
    
    # Get consensus result
    consensus_round = await consensus_task
    assert consensus_round.state == ConsensusState.Approved

@pytest.mark.asyncio
async def test_get_consensus_rejection(consensus_manager):
    """Test consensus rejection."""
    task_id = "test_task_002"
    consensus_task = asyncio.create_task(consensus_manager.get_consensus(task_id))
    
    # Wait a bit for the round to be created
    await asyncio.sleep(0.1)
    
    # Get the round ID
    round_id = list(consensus_manager.rounds.keys())[0]
    
    # Cast votes
    await consensus_manager.vote(round_id, "node_0", VoteType.Reject)
    await consensus_manager.vote(round_id, "node_1", VoteType.Reject)
    await consensus_manager.vote(round_id, "node_2", VoteType.Reject)
    
    # Get consensus result
    consensus_round = await consensus_task
    assert consensus_round.state == ConsensusState.Rejected

@pytest.mark.asyncio
async def test_get_consensus_timeout(consensus_manager):
    """Test consensus timeout."""
    task_id = "test_task_003"
    with pytest.raises(ConsensusTimeoutError):
        await consensus_manager.get_consensus(task_id)

@pytest.mark.asyncio
async def test_vote_validation(consensus_manager):
    """Test vote validation."""
    task_id = "test_task_004"
    consensus_task = asyncio.create_task(consensus_manager.get_consensus(task_id))
    
    # Wait a bit for the round to be created
    await asyncio.sleep(0.1)
    
    # Get the round ID
    round_id = list(consensus_manager.rounds.keys())[0]
    
    # Test invalid round ID
    success = await consensus_manager.vote("invalid", "node_1", VoteType.Approve)
    assert success is False
    
    # Test invalid vote type
    success = await consensus_manager.vote(round_id, "node_1", "invalid_vote")
    assert success is False

@pytest.mark.asyncio
async def test_cleanup(consensus_manager):
    """Test cleanup functionality."""
    # Create multiple consensus rounds
    task_ids = ["task_001", "task_002", "task_003"]
    consensus_tasks = []
    
    for task_id in task_ids:
        consensus_tasks.append(asyncio.create_task(consensus_manager.get_consensus(task_id)))
    
    # Wait a bit for rounds to be created
    await asyncio.sleep(0.1)
    
    # Verify rounds exist
    assert len(consensus_manager.rounds) == len(task_ids)
    
    # Run cleanup
    await consensus_manager.cleanup()
    
    # Verify rounds are cleaned up
    assert len(consensus_manager.rounds) == 0

@pytest.mark.asyncio
async def test_mixed_votes(consensus_manager):
    """Test mixed voting scenario."""
    task_id = "test_task_005"
    consensus_task = asyncio.create_task(consensus_manager.get_consensus(task_id))
    
    # Wait a bit for the round to be created
    await asyncio.sleep(0.1)
    
    # Get the round ID
    round_id = list(consensus_manager.rounds.keys())[0]
    
    # Cast mixed votes
    await consensus_manager.vote(round_id, "node_1", VoteType.Approve)
    await consensus_manager.vote(round_id, "node_2", VoteType.Reject)
    await consensus_manager.vote(round_id, "node_3", VoteType.Abstain)
    await consensus_manager.vote(round_id, "node_4", VoteType.Approve)
    await consensus_manager.vote(round_id, "node_5", VoteType.Approve)
    
    # Get consensus result
    consensus_round = await consensus_task
    assert consensus_round.state == ConsensusState.Approved
    assert len(consensus_round.votes) == 5

@pytest.mark.asyncio
async def test_consensus_deadlock(consensus_manager):
    """Test consensus deadlock handling."""
    task_id = "test_task_006"
    consensus_task = asyncio.create_task(consensus_manager.get_consensus(task_id))
    
    # Wait a bit for the round to be created
    await asyncio.sleep(0.1)
    
    # Get the round ID
    round_id = list(consensus_manager.rounds.keys())[0]
    
    # Cast mixed votes that don't reach consensus
    await consensus_manager.vote(round_id, "node_1", VoteType.Approve)
    await consensus_manager.vote(round_id, "node_2", VoteType.Reject)
    await consensus_manager.vote(round_id, "node_3", VoteType.Abstain)
    
    # Wait for timeout
    with pytest.raises(ConsensusTimeoutError):
        await consensus_task
        
    # Verify the round is still in pending state
    assert consensus_manager.rounds[round_id].state == ConsensusState.Pending

@pytest.mark.asyncio
async def test_ineligible_voter(consensus_manager):
    """Test handling of ineligible voter."""
    task_id = "test_task_007"
    consensus_task = asyncio.create_task(consensus_manager.get_consensus(task_id))
    
    # Wait a bit for the round to be created
    await asyncio.sleep(0.1)
    
    # Get the round ID
    round_id = list(consensus_manager.rounds.keys())[0]
    
    # Cast vote from ineligible node
    success = await consensus_manager.vote(round_id, "invalid_node", VoteType.Approve)
    assert success is True  # The vote should be accepted but won't count towards consensus
    
    # Cancel the task
    consensus_task.cancel()
    try:
        await consensus_task
    except asyncio.CancelledError:
        pass

class TestConsensusManager:
    """Test ConsensusManager class."""

    @pytest.fixture
    def consensus_manager(self, consensus_config):
        """Test consensus manager instance."""
        return ConsensusManager(consensus_config)

    @pytest.mark.asyncio
    async def test_init(self, consensus_manager):
        """Test initialization."""
        assert consensus_manager.timeout == 5
        assert consensus_manager.required_nodes == 3
        assert isinstance(consensus_manager.rounds, dict)

    @pytest.mark.asyncio
    async def test_start_vote(self, consensus_manager):
        """Test starting a vote."""
        task_id = "test_task_001"
        consensus_task = asyncio.create_task(consensus_manager.get_consensus(task_id))
        
        # Wait a bit for the round to be created
        await asyncio.sleep(0.1)
        
        # Get the round ID
        round_id = list(consensus_manager.rounds.keys())[0]
        
        # Cast a vote
        success = await consensus_manager.vote(round_id, "node_1", VoteType.Approve)
        assert success is True
        
        # Cancel the task
        consensus_task.cancel()
        try:
            await consensus_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_cast_vote(self, consensus_manager):
        """Test casting a vote."""
        task_id = "test_task_002"
        consensus_task = asyncio.create_task(consensus_manager.get_consensus(task_id))
        
        # Wait a bit for the round to be created
        await asyncio.sleep(0.1)
        
        # Get the round ID
        round_id = list(consensus_manager.rounds.keys())[0]
        
        # Cast votes
        await consensus_manager.vote(round_id, "node_1", VoteType.Approve)
        await consensus_manager.vote(round_id, "node_2", VoteType.Approve)
        await consensus_manager.vote(round_id, "node_3", VoteType.Approve)
        
        # Get consensus result
        consensus_round = await consensus_task
        assert consensus_round.state == ConsensusState.Approved
        assert len(consensus_round.votes) == 3

    @pytest.mark.asyncio
    async def test_get_results(self, consensus_manager):
        """Test getting consensus results."""
        task_id = "test_task_003"
        consensus_task = asyncio.create_task(consensus_manager.get_consensus(task_id))
        
        # Wait a bit for the round to be created
        await asyncio.sleep(0.1)
        
        # Get the round ID
        round_id = list(consensus_manager.rounds.keys())[0]
        
        # Cast votes
        await consensus_manager.vote(round_id, "node_1", VoteType.Reject)
        await consensus_manager.vote(round_id, "node_2", VoteType.Reject)
        await consensus_manager.vote(round_id, "node_3", VoteType.Reject)
        
        # Get consensus result
        consensus_round = await consensus_task
        assert consensus_round.state == ConsensusState.Rejected
        assert len(consensus_round.votes) == 3 