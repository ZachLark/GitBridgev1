"""
Unit tests for validation utilities.
"""

import pytest
from datetime import datetime, timezone
from mas_core.utils.validation import (
    validate_task_id,
    validate_timestamp,
    validate_task,
    validate_agent_assignment,
    validate_consensus_vote,
    generate_task_id,
    ValidationError
)

class TestValidateTaskId:
    """Test task ID validation."""
    
    def test_valid_task_ids(self):
        """Test valid task ID formats."""
        valid_ids = [
            "task_123",
            "abc123",
            "test-task",
            "task_with_underscores",
            "task-with-dashes",
            "a",
            "1234567890abcdef"
        ]
        
        for task_id in valid_ids:
            assert validate_task_id(task_id) is True
            
    def test_invalid_task_ids(self):
        """Test invalid task ID formats."""
        invalid_ids = [
            "",  # empty
            "task with spaces",  # spaces
            "task@with@symbols",  # invalid symbols
            "task#with#hash",  # hash symbols
            "a" * 65,  # too long
            "task.with.dots",  # dots
            "task/with/slashes"  # slashes
        ]
        
        for task_id in invalid_ids:
            assert validate_task_id(task_id) is False

class TestValidateTimestamp:
    """Test timestamp validation."""
    
    def test_valid_timestamps(self):
        """Test valid timestamp formats."""
        valid_timestamps = [
            "2023-12-01T10:00:00",
            "2023-12-01T10:00:00.123456",
            "2023-12-01T10:00:00+00:00",
            "2023-12-01T10:00:00.123456+00:00",
            datetime.now(timezone.utc).isoformat()
        ]
        
        for timestamp in valid_timestamps:
            assert validate_timestamp(timestamp) is True
            
    def test_invalid_timestamps(self):
        """Test invalid timestamp formats."""
        invalid_timestamps = [
            "not a timestamp",
            "2023-13-01T10:00:00",  # invalid month
            "2023-12-32T10:00:00",  # invalid day
            "2023-12-01T25:00:00",  # invalid hour
            "2023/12/01 10:00:00",  # wrong format
            "",  # empty
            "123456789"  # just numbers
        ]
        
        for timestamp in invalid_timestamps:
            assert validate_timestamp(timestamp) is False

class TestValidateTask:
    """Test task validation."""
    
    @pytest.fixture
    def valid_task(self):
        """Valid task fixture."""
        return {
            "task_id": "test_task_001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "description": "Test task description",
            "priority_level": "medium",
            "consensus": "pending",
            "agent_assignment": {
                "agent_001": "generate_draft",
                "agent_002": "review_draft"
            }
        }
    
    def test_valid_task(self, valid_task):
        """Test validation of valid task."""
        # Should not raise exception
        validate_task(valid_task)
    
    def test_missing_required_fields(self, valid_task):
        """Test missing required fields."""
        required_fields = [
            "task_id", "timestamp", "description", 
            "priority_level", "consensus", "agent_assignment"
        ]
        
        for field in required_fields:
            task = valid_task.copy()
            del task[field]
            
            with pytest.raises(ValidationError, match=f"Missing required field: {field}"):
                validate_task(task)
    
    def test_invalid_field_types(self, valid_task):
        """Test invalid field types."""
        type_tests = [
            ("task_id", 123),
            ("timestamp", 123),
            ("description", 123),
            ("priority_level", 123),
            ("consensus", 123),
            ("agent_assignment", "not a dict")
        ]
        
        for field, invalid_value in type_tests:
            task = valid_task.copy()
            task[field] = invalid_value
            
            with pytest.raises(ValidationError, match=f"Invalid type for {field}"):
                validate_task(task)
    
    def test_invalid_task_id(self, valid_task):
        """Test invalid task ID."""
        task = valid_task.copy()
        task["task_id"] = "invalid task id with spaces"
        
        with pytest.raises(ValidationError, match="Invalid task_id format"):
            validate_task(task)
    
    def test_invalid_timestamp(self, valid_task):
        """Test invalid timestamp."""
        task = valid_task.copy()
        task["timestamp"] = "not a timestamp"
        
        with pytest.raises(ValidationError, match="Invalid timestamp format"):
            validate_task(task)
    
    def test_invalid_priority_level(self, valid_task):
        """Test invalid priority level."""
        task = valid_task.copy()
        task["priority_level"] = "invalid_priority"
        
        with pytest.raises(ValidationError, match="Invalid priority_level"):
            validate_task(task)
    
    def test_invalid_consensus_state(self, valid_task):
        """Test invalid consensus state."""
        task = valid_task.copy()
        task["consensus"] = "invalid_consensus"
        
        with pytest.raises(ValidationError, match="Invalid consensus state"):
            validate_task(task)

class TestValidateAgentAssignment:
    """Test agent assignment validation."""
    
    def test_valid_assignment(self):
        """Test valid agent assignment."""
        assignment = {
            "agent_001": "generate_draft",
            "agent_002": "review_draft",
            "agent_003": "validate",
            "agent_004": "approve"
        }
        
        # Should not raise exception
        validate_agent_assignment(assignment)
    
    def test_empty_assignment(self):
        """Test empty agent assignment."""
        with pytest.raises(ValidationError, match="Empty agent assignment"):
            validate_agent_assignment({})
    
    def test_invalid_agent_id(self):
        """Test invalid agent ID."""
        assignments = [
            {123: "generate_draft"},  # non-string agent
            {"": "generate_draft"},   # empty agent
            {"   ": "generate_draft"} # whitespace only
        ]
        
        for assignment in assignments:
            with pytest.raises(ValidationError, match="Invalid agent identifier"):
                validate_agent_assignment(assignment)
    
    def test_invalid_role(self):
        """Test invalid agent role."""
        assignment = {"agent_001": "invalid_role"}
        
        with pytest.raises(ValidationError, match="Invalid agent role"):
            validate_agent_assignment(assignment)

class TestValidateConsensusVote:
    """Test consensus vote validation."""
    
    @pytest.fixture
    def valid_vote(self):
        """Valid vote fixture."""
        return {
            "task_id": "test_task_001",
            "agent_id": "agent_001",
            "vote": "approve",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def test_valid_vote(self, valid_vote):
        """Test validation of valid vote."""
        # Should not raise exception
        validate_consensus_vote(valid_vote)
    
    def test_missing_required_fields(self, valid_vote):
        """Test missing required fields in vote."""
        required_fields = ["task_id", "agent_id", "vote", "timestamp"]
        
        for field in required_fields:
            vote = valid_vote.copy()
            del vote[field]
            
            with pytest.raises(ValidationError, match=f"Missing required field in vote: {field}"):
                validate_consensus_vote(vote)
    
    def test_invalid_field_types(self, valid_vote):
        """Test invalid field types in vote."""
        type_tests = [
            ("task_id", 123),
            ("agent_id", 123),
            ("vote", 123),
            ("timestamp", 123)
        ]
        
        for field, invalid_value in type_tests:
            vote = valid_vote.copy()
            vote[field] = invalid_value
            
            with pytest.raises(ValidationError, match=f"Invalid type for vote field: {field}"):
                validate_consensus_vote(vote)
    
    def test_invalid_task_id_in_vote(self, valid_vote):
        """Test invalid task ID in vote."""
        vote = valid_vote.copy()
        vote["task_id"] = "invalid task id"
        
        with pytest.raises(ValidationError, match="Invalid task_id in vote"):
            validate_consensus_vote(vote)
    
    def test_invalid_timestamp_in_vote(self, valid_vote):
        """Test invalid timestamp in vote."""
        vote = valid_vote.copy()
        vote["timestamp"] = "not a timestamp"
        
        with pytest.raises(ValidationError, match="Invalid timestamp in vote"):
            validate_consensus_vote(vote)
    
    def test_invalid_vote_value(self, valid_vote):
        """Test invalid vote value."""
        vote = valid_vote.copy()
        vote["vote"] = "maybe"
        
        with pytest.raises(ValidationError, match="Invalid vote value"):
            validate_consensus_vote(vote)

class TestGenerateTaskId:
    """Test task ID generation."""
    
    def test_generate_task_id(self):
        """Test task ID generation."""
        task_id = generate_task_id()
        
        # Should be a string
        assert isinstance(task_id, str)
        
        # Should be valid according to our validation
        assert validate_task_id(task_id) is True
        
        # Should start with "task_"
        assert task_id.startswith("task_")
        
        # Should be unique (test with multiple generations)
        task_ids = [generate_task_id() for _ in range(10)]
        assert len(set(task_ids)) == 10  # All unique 