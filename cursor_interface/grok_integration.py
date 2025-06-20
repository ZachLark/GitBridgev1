#!/usr/bin/env python3
"""
GitBridge Grok Cursor Integration
Task: P20P6S3 - Grok Cursor Integration

This module integrates Grok 3 responses with the Cursor workspace.
Routes high-confidence Grok responses to .task.md files using the shared translator.

Author: GitBridge Development Team
Date: 2025-01-11
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports
from cursor_interface.translator import CursorTranslator
from cursor_interface.cursor_formats import CursorFileType, ConfidenceLevel
from utils.schema_validator import GPT4oEventSchema
from clients.grok_client import GrokResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/grok_cursor_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GrokCursorIntegration:
    """
    Integration handler for Grok 3 responses to Cursor workspace.
    
    This class routes Grok responses to Cursor files, with special handling
    for high-confidence responses that are routed to .task.md files.
    """
    
    def __init__(self, workspace_dir: str = "cursor_workspace"):
        """
        Initialize the Grok Cursor integration.
        
        Args:
            workspace_dir: Directory for Cursor workspace files
        """
        self.translator = CursorTranslator(workspace_dir)
        self.integration_stats = {
            "total_processed": 0,
            "successful_translations": 0,
            "failed_translations": 0,
            "task_files_created": 0,
            "files_created": []
        }
        
        logger.info(f"✅ GrokCursorIntegration initialized with workspace: {workspace_dir}")
    
    def process_grok_response(self, grok_response: GrokResponse, 
                            original_event: GPT4oEventSchema,
                            context: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a Grok response and create corresponding Cursor files.
        
        Args:
            grok_response: Grok 3 response object
            original_event: Original event that generated the response
            context: Optional additional context
            
        Returns:
            Dict containing processing results
        """
        self.integration_stats["total_processed"] += 1
        
        logger.info(f"🔄 Processing Grok response for event: {original_event.event_id}")
        
        if not grok_response.success:
            logger.error(f"❌ Cannot process failed Grok response: {grok_response.error_message}")
            return {
                "success": False,
                "error": grok_response.error_message,
                "files_created": []
            }
        
        try:
            # Convert GrokResponse to GPT4oResponse format for compatibility
            from tests.test_gpt4o_connection import GPT4oResponse
            
            gpt4o_response = GPT4oResponse(
                content=grok_response.content,
                model=grok_response.model,
                usage=grok_response.usage,
                finish_reason=grok_response.finish_reason,
                response_time=grok_response.response_time,
                success=grok_response.success
            )
            
            # Determine if this should be a high-confidence task
            is_high_confidence = self._assess_grok_confidence(grok_response)
            
            # Route to Cursor translator with task preference
            if is_high_confidence:
                logger.info("🎯 Routing high-confidence Grok response to .task.md")
                result = self.translator.translate_gpt_response(
                    gpt4o_response, original_event, context, requested_output="task"
                )
            else:
                result = self.translator.translate_gpt_response(
                    gpt4o_response, original_event, context
                )
            
            if result["success"]:
                self.integration_stats["successful_translations"] += 1
                self.integration_stats["files_created"].extend(result["files_created"])
                
                # Track task file creation
                if result["file_type"] == "task":
                    self.integration_stats["task_files_created"] += 1
                
                logger.info(f"✅ Successfully created Cursor file: {result['file_path']}")
                
                # Log integration success
                self._log_integration_success(original_event, grok_response, result)
                
                return {
                    "success": True,
                    "integration_id": f"grok_int_{int(datetime.now().timestamp())}",
                    "translation_result": result,
                    "cursor_file_created": True,
                    "file_path": result["file_path"],
                    "file_type": result["file_type"],
                    "high_confidence": is_high_confidence
                }
            
            else:
                self.integration_stats["failed_translations"] += 1
                
                logger.error(f"❌ Failed to create Cursor file: {result['error']}")
                
                # Log integration failure
                self._log_integration_failure(original_event, grok_response, result)
                
                return {
                    "success": False,
                    "integration_id": f"grok_int_{int(datetime.now().timestamp())}",
                    "error": result["error"],
                    "cursor_file_created": False
                }
                
        except Exception as e:
            self.integration_stats["failed_translations"] += 1
            
            error_msg = f"Grok Cursor integration failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "files_created": []
            }
    
    def _assess_grok_confidence(self, grok_response: GrokResponse) -> bool:
        """
        Assess if a Grok response should be considered high confidence.
        
        Args:
            grok_response: Grok response to assess
            
        Returns:
            bool: True if high confidence, False otherwise
        """
        content_lower = grok_response.content.lower()
        
        # High confidence indicators
        high_confidence_indicators = [
            "definitely", "certainly", "should", "must", "highly recommend",
            "implement", "add", "create", "update", "fix", "improve",
            "task", "action", "next step", "priority", "urgent"
        ]
        
        # Low confidence indicators
        low_confidence_indicators = [
            "maybe", "consider", "might", "possibly", "could",
            "suggestion", "idea", "thought", "perhaps"
        ]
        
        # Count indicators
        high_count = sum(1 for indicator in high_confidence_indicators if indicator in content_lower)
        low_count = sum(1 for indicator in low_confidence_indicators if indicator in content_lower)
        
        # Determine confidence
        if high_count > low_count:
            return True
        elif high_count == low_count:
            # Default to high confidence for Grok (as per requirements)
            return True
        else:
            return False
    
    def _log_integration_success(self, original_event: GPT4oEventSchema,
                                grok_response: GrokResponse,
                                translation_result: Dict[str, Any]) -> None:
        """Log successful integration."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "grok_integration_success",
            "original_event_id": original_event.event_id,
            "source": original_event.source.value,
            "grok_model": grok_response.model,
            "grok_response_time": grok_response.response_time,
            "cursor_file_path": translation_result["file_path"],
            "cursor_file_type": translation_result["file_type"],
            "high_confidence": translation_result.get("high_confidence", False)
        }
        
        with open('logs/grok_cursor_integration.log', 'a') as f:
            f.write(f"\n{json.dumps(log_entry, indent=2)}\n")
    
    def _log_integration_failure(self, original_event: GPT4oEventSchema,
                                grok_response: GrokResponse,
                                translation_result: Dict[str, Any]) -> None:
        """Log failed integration."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "grok_integration_failure",
            "original_event_id": original_event.event_id,
            "source": original_event.source.value,
            "grok_model": grok_response.model,
            "error": translation_result["error"]
        }
        
        with open('logs/grok_cursor_integration.log', 'a') as f:
            f.write(f"\n{json.dumps(log_entry, indent=2)}\n")
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        return {
            **self.integration_stats,
            "success_rate": (
                self.integration_stats["successful_translations"] / 
                max(self.integration_stats["total_processed"], 1)
            ),
            "task_file_rate": (
                self.integration_stats["task_files_created"] / 
                max(self.integration_stats["successful_translations"], 1)
            ),
            "workspace_files": len(self.translator.list_workspace_files())
        }
    
    def cleanup_workspace(self, days: int = 7) -> int:
        """Clean up old workspace files."""
        return self.translator.cleanup_old_files(days)


def simulate_grok_to_cursor_flow():
    """Simulate the complete Grok → Cursor flow."""
    from utils.schema_validator import create_sample_events
    from clients.grok_client import GrokResponse
    
    print("🔄 Simulating Grok → Cursor Flow")
    print("=" * 50)
    
    # Create sample event
    samples = create_sample_events()
    sample_event = samples['github_pr']
    
    print(f"📥 Sample GitHub event: {sample_event.event_id}")
    print(f"   Source: {sample_event.source.value}")
    print(f"   Type: {sample_event.event_type.value}")
    
    # Simulate Grok response
    mock_grok_response = GrokResponse(
        content="""Based on this pull request, here are the immediate tasks that need to be completed:

**High Priority Tasks:**
1. Add comprehensive input validation to the JWT token handler
2. Implement proper token expiration checks with configurable timeouts
3. Add rate limiting middleware for authentication endpoints
4. Create integration tests for the authentication flow

**Security Enhancements:**
1. Add logging for security events and failed authentication attempts
2. Implement proper error handling without exposing sensitive information
3. Add audit trail for token generation and validation

**Testing Requirements:**
1. Create unit tests for all authentication functions
2. Add load testing for rate limiting functionality
3. Test error scenarios and edge cases

**Documentation Updates:**
1. Update API documentation with authentication requirements
2. Create deployment guide for production security settings
3. Document rate limiting configuration options

These tasks should be implemented before merging to ensure security compliance.""",
        model="llama3-70b-8192",
        usage={"total_tokens": 300, "prompt_tokens": 150, "completion_tokens": 150},
        finish_reason="stop",
        response_time=2.8,
        success=True
    )
    
    print(f"🤖 Simulated Grok response ({mock_grok_response.response_time:.1f}s)")
    print(f"   Model: {mock_grok_response.model}")
    print(f"   Tokens: {mock_grok_response.usage['total_tokens']}")
    
    # Process through Grok Cursor integration
    integration = GrokCursorIntegration()
    result = integration.process_grok_response(mock_grok_response, sample_event)
    
    if result["success"]:
        print(f"✅ Cursor file created successfully!")
        print(f"   File: {result['file_path']}")
        print(f"   Type: {result['file_type']}")
        print(f"   High Confidence: {result['high_confidence']}")
    else:
        print(f"❌ Failed to create Cursor file: {result['error']}")
    
    # Show integration stats
    stats = integration.get_integration_stats()
    print(f"\n📊 Integration Statistics:")
    print(f"   Total processed: {stats['total_processed']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    print(f"   Task file rate: {stats['task_file_rate']:.1%}")
    print(f"   Files created: {len(stats['files_created'])}")
    
    return result


def main():
    """Main function for testing and demonstration."""
    print("🎯 GitBridge Grok Cursor Integration")
    print("Task: P20P6S3 - Grok Cursor Integration")
    print("=" * 60)
    
    # Check environment
    if not os.getenv('GROK_API_KEY'):
        print("⚠️  GROK_API_KEY not found in environment")
        print("   Please set GROK_API_KEY in your .env file")
        return
    
    # Simulate the complete flow
    result = simulate_grok_to_cursor_flow()
    
    # Show workspace files
    integration = GrokCursorIntegration()
    files = integration.translator.list_workspace_files()
    
    print(f"\n📂 Cursor Workspace Files ({len(files)} total):")
    for file_info in files:
        print(f"  - {file_info['filename']} ({file_info['size']} bytes)")
        print(f"    Created: {file_info['created']}")
    
    print(f"\n✅ Grok Cursor integration complete!")
    print(f"📁 Files written to: cursor_workspace/")
    print(f"📝 Logs written to: logs/grok_cursor_integration.log")
    print(f"🔄 Ready for SmartRouter integration (P20P7)")


if __name__ == "__main__":
    main() 