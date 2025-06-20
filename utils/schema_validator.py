#!/usr/bin/env python3
"""
GitBridge GPT-4o Event Format Schema Validator
Task: P20P2S2 - Define GPT-4o Event Format Schema

This module provides schema validation for standardized JSON events sent to GPT-4o.
It ensures consistency across GitHub webhooks, Cursor integrations, and manual inputs.

Author: GitBridge Development Team
Date: 2025-01-11
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum

# Third-party imports
from pydantic import BaseModel, Field, validator, root_validator
import jsonschema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventSource(str, Enum):
    """Valid event sources for GPT-4o processing."""
    GITHUB = "github"
    CURSOR = "cursor"
    MANUAL = "manual"
    WEBHOOK = "webhook"
    PALM = "palm"  # For PALMv1.5 integration


class EventType(str, Enum):
    """Valid event types for different scenarios."""
    # GitHub events
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    PULL_REQUEST_REVIEW = "pull_request_review"
    ISSUE = "issue"
    COMMIT = "commit"
    
    # Cursor events
    TEST_LOG = "test_log"
    DEVELOPER_NOTE = "developer_note"
    CODE_REVIEW = "code_review"
    ERROR_LOG = "error_log"
    PERFORMANCE_LOG = "performance_log"
    
    # System events
    MANUAL_REQUEST = "manual_request"
    SCHEDULED_TASK = "scheduled_task"
    ESCALATION = "escalation"


class OutputType(str, Enum):
    """Valid output types that GPT-4o can generate."""
    SUMMARY = "summary"
    CODE_PATCH = "code_patch"
    PR_COMMENT = "pr_comment"
    REVIEW_FEEDBACK = "review_feedback"
    DIAGNOSTIC = "diagnostic"
    RECOMMENDATION = "recommendation"
    DOCUMENTATION = "documentation"
    FIX_SUGGESTION = "fix_suggestion"


class ToneType(str, Enum):
    """Valid tone options for GPT-4o responses."""
    BLUNT = "blunt"
    STRATEGIC = "strategic"
    REVIEWER = "reviewer"
    HELPFUL = "helpful"
    TECHNICAL = "technical"
    CONCISE = "concise"
    DETAILED = "detailed"
    COACHING = "coaching"


class GPT4oEventSchema(BaseModel):
    """
    Standardized schema for events sent to GPT-4o.
    
    This schema ensures consistency across all GitBridge AI interactions
    and provides clear structure for prompt engineering and response parsing.
    """
    
    # Core identification
    event_id: str = Field(..., description="Unique identifier for this event")
    timestamp: str = Field(..., description="ISO 8601 timestamp of event creation")
    source: EventSource = Field(..., description="Source system generating the event")
    event_type: EventType = Field(..., description="Type of event being processed")
    
    # Content and context
    context: str = Field(..., min_length=1, max_length=50000, 
                        description="Multi-line string containing relevant information")
    goal: str = Field(..., min_length=1, max_length=1000,
                     description="Concise description of what we want GPT to do")
    
    # Optional configuration
    tone: Optional[ToneType] = Field(None, description="Desired tone for GPT response")
    requested_output: Optional[OutputType] = Field(None, description="Expected output format")
    
    # Metadata for tracking and routing
    priority: Optional[int] = Field(1, ge=1, le=10, description="Priority level (1-10)")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, 
                                              description="Additional metadata")
    
    # MAS Lite Protocol v2.1 compliance
    protocol_version: str = Field("2.1", description="MAS Lite Protocol version")
    session_id: Optional[str] = Field(None, description="Session identifier for correlation")
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Validate ISO 8601 timestamp format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('timestamp must be in ISO 8601 format')
    
    @validator('event_id')
    def validate_event_id(cls, v):
        """Validate event ID format."""
        if not v or len(v) < 8:
            raise ValueError('event_id must be at least 8 characters')
        return v
    
    @root_validator
    def validate_context_goal_relationship(cls, values):
        """Ensure context and goal are properly related."""
        context = values.get('context', '')
        goal = values.get('goal', '')
        
        if context and goal:
            # Basic validation that goal references context content
            if len(context) < 10 and len(goal) > 100:
                raise ValueError('Goal should not be longer than context for short contexts')
        
        return values
    
    def to_prompt_string(self) -> str:
        """
        Convert the event to a structured prompt string for GPT-4o.
        
        Returns:
            str: Formatted prompt string ready for ChatCompletion
        """
        prompt_parts = [
            f"# GitBridge Event Processing",
            f"Event ID: {self.event_id}",
            f"Source: {self.source.value}",
            f"Type: {self.event_type.value}",
            f"Timestamp: {self.timestamp}",
            "",
            f"## Goal",
            f"{self.goal}",
            ""
        ]
        
        if self.tone:
            prompt_parts.append(f"## Tone Requirement")
            prompt_parts.append(f"Please respond in a {self.tone.value} tone.")
            prompt_parts.append("")
        
        if self.requested_output:
            prompt_parts.append(f"## Expected Output")
            prompt_parts.append(f"Format your response as: {self.requested_output.value}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            f"## Context",
            f"{self.context}",
            "",
            f"## Response"
        ])
        
        return "\n".join(prompt_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.dict()
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class SchemaValidator:
    """Utility class for validating GPT-4o event schemas."""
    
    def __init__(self):
        self.json_schema = self._generate_json_schema()
    
    def _generate_json_schema(self) -> Dict[str, Any]:
        """Generate JSON schema from Pydantic model, patching optional fields to allow null."""
        schema = GPT4oEventSchema.schema()
        # Patch optional fields to allow null
        nullable_fields = [
            'session_id', 'tone', 'requested_output', 'tags', 'metadata'
        ]
        for field in nullable_fields:
            if field in schema['properties'] and 'type' in schema['properties'][field]:
                orig_type = schema['properties'][field]['type']
                if isinstance(orig_type, list):
                    if 'null' not in orig_type:
                        schema['properties'][field]['type'].append('null')
                else:
                    schema['properties'][field]['type'] = [orig_type, 'null']
        return schema
    
    def validate_event(self, event_data: Dict[str, Any]) -> GPT4oEventSchema:
        """
        Validate event data against the schema.
        
        Args:
            event_data: Dictionary containing event data
            
        Returns:
            GPT4oEventSchema: Validated event object
            
        Raises:
            ValueError: If validation fails
        """
        try:
            return GPT4oEventSchema(**event_data)
        except Exception as e:
            raise ValueError(f"Event validation failed: {str(e)}")
    
    def validate_json_schema(self, event_data: Dict[str, Any]) -> bool:
        """
        Validate using JSON schema (alternative to Pydantic).
        
        Args:
            event_data: Dictionary containing event data
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            jsonschema.validate(event_data, self.json_schema)
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"JSON schema validation failed: {str(e)}")
            return False


def create_sample_events() -> Dict[str, GPT4oEventSchema]:
    """
    Create sample events for testing and documentation.
    
    Returns:
        Dict containing sample events
    """
    samples = {}
    
    # Sample 1: GitHub Pull Request
    samples['github_pr'] = GPT4oEventSchema(
        event_id="gh_pr_12345_20250111_001",
        timestamp=datetime.now(timezone.utc).isoformat(),
        source=EventSource.GITHUB,
        event_type=EventType.PULL_REQUEST,
        context="""Repository: octocat/Hello-World
Pull Request #123: Add user authentication feature
Author: @alice-dev
Branch: feature/user-auth -> main

Changes:
- Added JWT token authentication
- Implemented user login/logout endpoints
- Added password hashing with bcrypt
- Created user model with SQLAlchemy

Files changed:
- src/auth/jwt_handler.py (new)
- src/models/user.py (new)
- src/routes/auth.py (new)
- tests/test_auth.py (new)

The PR includes comprehensive tests and documentation.""",
        goal="Review this pull request for security best practices, code quality, and potential issues. Provide actionable feedback for the author.",
        tone=ToneType.REVIEWER,
        requested_output=OutputType.PR_COMMENT,
        priority=7,
        tags=["security", "authentication", "backend"],
        metadata={
            "repo": "octocat/Hello-World",
            "pr_number": 123,
            "author": "alice-dev",
            "base_branch": "main",
            "head_branch": "feature/user-auth"
        }
    )
    
    # Sample 2: Cursor Test Failure Log
    samples['cursor_test_failure'] = GPT4oEventSchema(
        event_id="cursor_test_20250111_002",
        timestamp=datetime.now(timezone.utc).isoformat(),
        source=EventSource.CURSOR,
        event_type=EventType.TEST_LOG,
        context="""Test Suite: GitBridge Integration Tests
Failed Test: test_gpt4o_webhook_integration
Duration: 2.34s
Error: AssertionError: Expected response time < 2.0s, got 2.34s

Test Details:
- Endpoint: POST /webhook/gpt4o
- Payload: GitHub push event
- Expected: 200 OK with response time < 2.0s
- Actual: 200 OK with response time 2.34s

Stack Trace:
File "tests/test_webhook_integration.py", line 45, in test_gpt4o_webhook_integration
    assert response_time < 2.0, f"Response time {response_time}s exceeds 2.0s threshold"

Environment:
- Python 3.13.3
- OpenAI API: gpt-4o
- Redis: localhost:6379
- Load: Medium (5 concurrent requests)""",
        goal="Analyze this test failure and provide recommendations for improving response time. Consider if the 2.0s threshold is realistic and suggest optimizations.",
        tone=ToneType.TECHNICAL,
        requested_output=OutputType.DIAGNOSTIC,
        priority=5,
        tags=["performance", "testing", "webhook"],
        metadata={
            "test_suite": "GitBridge Integration Tests",
            "test_name": "test_gpt4o_webhook_integration",
            "failure_type": "performance",
            "environment": "development"
        }
    )
    
    return samples


def main():
    """Main function for testing and demonstration."""
    print("🔧 GitBridge GPT-4o Event Schema Validator")
    print("Task: P20P2S2 - Define GPT-4o Event Format Schema")
    print("=" * 60)
    
    # Create validator
    validator = SchemaValidator()
    
    # Generate sample events
    samples = create_sample_events()
    
    # Test validation
    print("\n📋 Testing Schema Validation...")
    for name, event in samples.items():
        try:
            # Validate the event
            validated_event = validator.validate_event(event.to_dict())
            print(f"✅ {name}: Valid")
            
            # Test JSON schema validation
            if validator.validate_json_schema(event.to_dict()):
                print(f"✅ {name}: JSON Schema Valid")
            else:
                print(f"❌ {name}: JSON Schema Invalid")
                
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
    
    # Display sample events
    print("\n📄 Sample Events:")
    for name, event in samples.items():
        print(f"\n--- {name.upper()} ---")
        print(f"Event ID: {event.event_id}")
        print(f"Source: {event.source.value}")
        print(f"Type: {event.event_type.value}")
        print(f"Goal: {event.goal}")
        print(f"Context Length: {len(event.context)} characters")
        
        # Show prompt string
        print(f"\nPrompt String Preview:")
        prompt = event.to_prompt_string()
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
    
    # Save samples to file
    print("\n💾 Saving sample events to 'sample_events.json'...")
    sample_data = {name: event.to_dict() for name, event in samples.items()}
    with open('sample_events.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("✅ Schema validation complete!")
    print("📁 Sample events saved to 'sample_events.json'")


if __name__ == "__main__":
    main() 