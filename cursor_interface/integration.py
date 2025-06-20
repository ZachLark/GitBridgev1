#!/usr/bin/env python3
"""
GitBridge Cursor Integration Handler
Task: P20P4S3 - Simulate File Drop into Cursor Workspace

This module integrates the GitHub webhook with the Cursor translator,
completing the full GPT-4o → Cursor feedback loop.

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
from utils.schema_validator import GPT4oEventSchema
from tests.test_gpt4o_connection import GPT4oResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cursor_integration_trace.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CursorIntegrationHandler:
    """
    Integration handler that processes GPT-4o responses and creates Cursor files.
    
    This class serves as the bridge between the webhook system and Cursor workspace,
    handling the complete flow from GPT-4o response to Cursor file creation.
    """
    
    def __init__(self, workspace_dir: str = "cursor_workspace"):
        """
        Initialize the integration handler.
        
        Args:
            workspace_dir: Directory for Cursor workspace files
        """
        self.translator = CursorTranslator(workspace_dir)
        self.integration_stats = {
            "total_processed": 0,
            "successful_translations": 0,
            "failed_translations": 0,
            "files_created": []
        }
        
        logger.info("✅ CursorIntegrationHandler initialized")
    
    def process_gpt_response(self, gpt_response: GPT4oResponse, 
                           original_event: GPT4oEventSchema,
                           context: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a GPT-4o response and create corresponding Cursor files.
        
        Args:
            gpt_response: GPT-4o response object
            original_event: Original event that generated the response
            context: Optional additional context
            
        Returns:
            Dict containing processing results
        """
        self.integration_stats["total_processed"] += 1
        
        logger.info(f"🔄 Processing GPT response for event: {original_event.event_id}")
        
        # Translate GPT response to Cursor file
        translation_result = self.translator.translate_gpt_response(
            gpt_response, original_event, context
        )
        
        if translation_result["success"]:
            self.integration_stats["successful_translations"] += 1
            self.integration_stats["files_created"].extend(translation_result["files_created"])
            
            logger.info(f"✅ Successfully created Cursor file: {translation_result['file_path']}")
            
            # Log integration success
            self._log_integration_success(original_event, gpt_response, translation_result)
            
            return {
                "success": True,
                "integration_id": f"int_{int(datetime.now().timestamp())}",
                "translation_result": translation_result,
                "cursor_file_created": True,
                "file_path": translation_result["file_path"]
            }
        
        else:
            self.integration_stats["failed_translations"] += 1
            
            logger.error(f"❌ Failed to create Cursor file: {translation_result['error']}")
            
            # Log integration failure
            self._log_integration_failure(original_event, gpt_response, translation_result)
            
            return {
                "success": False,
                "integration_id": f"int_{int(datetime.now().timestamp())}",
                "error": translation_result["error"],
                "cursor_file_created": False
            }
    
    def _log_integration_success(self, original_event: GPT4oEventSchema,
                                gpt_response: GPT4oResponse,
                                translation_result: Dict[str, Any]) -> None:
        """Log successful integration."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "integration_success",
            "original_event_id": original_event.event_id,
            "source": original_event.source.value,
            "gpt_model": gpt_response.model,
            "gpt_response_time": gpt_response.response_time,
            "cursor_file_path": translation_result["file_path"],
            "cursor_file_type": translation_result["file_type"],
            "confidence": translation_result["confidence"]
        }
        
        with open('logs/cursor_integration_trace.log', 'a') as f:
            f.write(f"\n{json.dumps(log_entry, indent=2)}\n")
    
    def _log_integration_failure(self, original_event: GPT4oEventSchema,
                                gpt_response: GPT4oResponse,
                                translation_result: Dict[str, Any]) -> None:
        """Log failed integration."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "integration_failure",
            "original_event_id": original_event.event_id,
            "source": original_event.source.value,
            "gpt_model": gpt_response.model,
            "error": translation_result["error"]
        }
        
        with open('logs/cursor_integration_trace.log', 'a') as f:
            f.write(f"\n{json.dumps(log_entry, indent=2)}\n")
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        return {
            **self.integration_stats,
            "success_rate": (
                self.integration_stats["successful_translations"] / 
                max(self.integration_stats["total_processed"], 1)
            ),
            "workspace_files": len(self.translator.list_workspace_files())
        }
    
    def cleanup_workspace(self, days: int = 7) -> int:
        """Clean up old workspace files."""
        return self.translator.cleanup_old_files(days)


def simulate_webhook_to_cursor_flow():
    """Simulate the complete webhook → GPT-4o → Cursor flow."""
    from utils.schema_validator import create_sample_events
    from tests.test_gpt4o_connection import GPT4oResponse
    
    print("🔄 Simulating Webhook → GPT-4o → Cursor Flow")
    print("=" * 50)
    
    # Create sample event (simulating webhook)
    samples = create_sample_events()
    sample_event = samples['github_pr']
    
    print(f"📥 Simulated GitHub webhook event: {sample_event.event_id}")
    print(f"   Source: {sample_event.source.value}")
    print(f"   Type: {sample_event.event_type.value}")
    
    # Simulate GPT-4o response
    mock_gpt_response = GPT4oResponse(
        content="""This pull request looks good overall, but I have a few suggestions for improvement:

**Security Considerations:**
1. Add input validation to the JWT token handler
2. Implement proper token expiration checks
3. Add rate limiting for authentication endpoints

**Code Quality:**
1. Consider adding more comprehensive error handling
2. The test coverage could be expanded to include edge cases
3. Documentation is well written and clear

**Recommendations:**
- Implement the security improvements before merging
- Add integration tests for the authentication flow
- Consider adding logging for security events""",
        model="gpt-4o",
        usage={"total_tokens": 250, "prompt_tokens": 150, "completion_tokens": 100},
        finish_reason="stop",
        response_time=3.2,
        success=True
    )
    
    print(f"🤖 Simulated GPT-4o response ({mock_gpt_response.response_time:.1f}s)")
    print(f"   Model: {mock_gpt_response.model}")
    print(f"   Tokens: {mock_gpt_response.usage['total_tokens']}")
    
    # Process through Cursor integration
    integration_handler = CursorIntegrationHandler()
    result = integration_handler.process_gpt_response(mock_gpt_response, sample_event)
    
    if result["success"]:
        print(f"✅ Cursor file created successfully!")
        print(f"   File: {result['file_path']}")
        print(f"   Type: {result['translation_result']['file_type']}")
        print(f"   Confidence: {result['translation_result']['confidence']}")
    else:
        print(f"❌ Failed to create Cursor file: {result['error']}")
    
    # Show integration stats
    stats = integration_handler.get_integration_stats()
    print(f"\n📊 Integration Statistics:")
    print(f"   Total processed: {stats['total_processed']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    print(f"   Files created: {len(stats['files_created'])}")
    
    return result


def main():
    """Main function for testing and demonstration."""
    print("🎯 GitBridge Cursor Integration Handler")
    print("Task: P20P4S3 - Simulate File Drop into Cursor Workspace")
    print("=" * 60)
    
    # Simulate the complete flow
    result = simulate_webhook_to_cursor_flow()
    
    # Show workspace files
    integration_handler = CursorIntegrationHandler()
    files = integration_handler.translator.list_workspace_files()
    
    print(f"\n📂 Cursor Workspace Files ({len(files)} total):")
    for file_info in files:
        print(f"  - {file_info['filename']} ({file_info['size']} bytes)")
        print(f"    Created: {file_info['created']}")
    
    print(f"\n✅ Cursor integration complete!")
    print(f"📁 Files written to: cursor_workspace/")
    print(f"📝 Logs written to: logs/cursor_integration_trace.log")
    print(f"🔄 Ready for SmartRouter integration (P20P7)")


if __name__ == "__main__":
    main() 