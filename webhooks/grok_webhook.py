#!/usr/bin/env python3
"""
GitBridge Grok Webhook Handler
Task: P20P7S4 - Live Workflow Integration

This module handles webhook requests using SmartRouter for intelligent provider selection.
Translates events using GPT4oEventSchema and routes to optimal AI provider.

Author: GitBridge Development Team
Date: 2025-06-19
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
from utils.ai_router import ask_ai, get_router_metrics
from utils.schema_validator import GPT4oEventSchema, SchemaValidator
from cursor_interface.translator import CursorTranslator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [gbtestgrok] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/grok_webhook_trace.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class GrokWebhookHandler:
    """
    Handler for Grok webhook requests using SmartRouter.
    
    This class processes webhook events, validates them against the schema,
    sends them to the optimal AI provider via SmartRouter, and routes responses to Cursor.
    """
    
    def __init__(self):
        """Initialize the Grok webhook handler with SmartRouter integration."""
        self.schema_validator = SchemaValidator()
        self.cursor_translator = CursorTranslator()
        
        logger.info("✅ GrokWebhookHandler initialized with SmartRouter integration")
    
    def process_webhook(self, event_data: Dict[str, Any], 
                       event_type: str, 
                       source: str = "github") -> Dict[str, Any]:
        """
        Process a webhook event and send to optimal AI provider via SmartRouter.
        
        Args:
            event_data: Raw webhook payload
            event_type: Type of event (pull_request, push, etc.)
            source: Source platform (github, gitlab, etc.)
            
        Returns:
            Dict containing processing results
        """
        try:
            # Create event ID
            event_id = f"smartrouter_{source}_{event_type}_{int(datetime.now().timestamp())}"
            
            # Convert to GPT4oEventSchema
            event = self._create_grok_event(event_data, event_type, source, event_id)
            
            # Validate event
            validated_event = self.schema_validator.validate_event(event.dict())
            
            # Create prompt for AI
            prompt = self._create_ai_prompt(validated_event)
            
            # Send to optimal AI provider via SmartRouter
            ai_response = ask_ai(
                prompt=prompt,
                task_type="webhook_processing",
                strategy="hybrid"  # Use hybrid strategy for webhook processing
            )
            
            # Log the request
            self._log_webhook_request(validated_event, ai_response)
            
            # Route to Cursor (high-confidence responses to .task.md)
            cursor_result = self._route_to_cursor(ai_response, validated_event)
            
            return {
                "success": True,
                "event_id": event_id,
                "ai_response": {
                    "content": ai_response.content,
                    "provider": ai_response.provider.value,
                    "model": ai_response.model,
                    "response_time": ai_response.response_time,
                    "tokens": ai_response.usage.get('total_tokens', 0),
                    "routing_confidence": ai_response.routing_decision.confidence
                },
                "cursor_file_created": cursor_result["success"],
                "cursor_file_path": cursor_result.get("file_path")
            }
                
        except Exception as e:
            error_msg = f"SmartRouter webhook processing failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                "success": False,
                "error": error_msg
            }
    
    def _create_grok_event(self, event_data: Dict[str, Any], 
                          event_type: str, 
                          source: str, 
                          event_id: str) -> GPT4oEventSchema:
        """
        Create a GPT4oEventSchema event for AI processing.
        
        Args:
            event_data: Raw webhook payload
            event_type: Type of event
            source: Source platform
            event_id: Unique event identifier
            
        Returns:
            GPT4oEventSchema: Validated event
        """
        from utils.schema_validator import EventSource, EventType, OutputType
        
        # Map event type to schema enum
        event_type_map = {
            "pull_request": EventType.PULL_REQUEST,
            "push": EventType.PUSH,
            "issue": EventType.ISSUE,
            "comment": EventType.PULL_REQUEST_REVIEW  # Use closest available type
        }
        
        # Map source to schema enum
        source_map = {
            "github": EventSource.GITHUB,
            "gitlab": EventSource.WEBHOOK,  # Use WEBHOOK as fallback
            "bitbucket": EventSource.WEBHOOK  # Use WEBHOOK as fallback
        }
        
        # Create event
        context = json.dumps(event_data, indent=2)
        goal = f"Analyze this {event_type} event from {source} and provide actionable development tasks or insights."
        
        event = GPT4oEventSchema(
            event_id=event_id,
            source=source_map.get(source, EventSource.GITHUB),
            event_type=event_type_map.get(event_type, EventType.PULL_REQUEST),
            session_id=f"smartrouter_session_{int(datetime.now().timestamp())}",
            context=context,
            goal=goal,
            requested_output=OutputType.RECOMMENDATION,  # AI responses default to recommendations
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return event
    
    def _create_ai_prompt(self, event: GPT4oEventSchema) -> str:
        """
        Create a prompt for AI based on the event.
        
        Args:
            event: Validated event schema
            
        Returns:
            str: Formatted prompt for AI
        """
        # Base prompt template
        base_prompt = f"""You are an AI assistant helping with development tasks.

Event Type: {event.event_type.value}
Source: {event.source.value}
Requested Output: {event.requested_output.value if event.requested_output else 'recommendation'}

Please analyze this event and provide actionable development tasks or insights.

Event Data:
{event.context}

Instructions:
1. Focus on practical, actionable tasks
2. Be specific and detailed
3. Consider security, performance, and best practices
4. Provide clear next steps
5. Format your response as a structured task list

Please provide your analysis and recommendations:"""
        
        return base_prompt
    
    def _route_to_cursor(self, ai_response, event: GPT4oEventSchema) -> Dict[str, Any]:
        """
        Route AI response to Cursor workspace.
        Args:
            ai_response: Response from AI provider
            event: Original event
        Returns:
            Dict containing routing results
        """
        try:
            # Only route high-confidence responses to Cursor
            if ai_response.routing_decision.confidence >= 0.7:
                # Construct GPT4oResponse for translation
                from tests.test_gpt4o_connection import GPT4oResponse
                gpt4o_response = GPT4oResponse(
                    content=ai_response.content,
                    model=ai_response.model,
                    usage=ai_response.usage,
                    finish_reason="stop",
                    response_time=ai_response.response_time,
                    success=True,
                    error_message=None
                )
                cursor_result = self.cursor_translator.translate_gpt_response(
                    gpt4o_response, event
                )
                logger.info(f"✅ Routed to Cursor: {cursor_result.get('file_path', 'unknown')}")
                return cursor_result
            else:
                logger.info(f"⚠️ Skipped Cursor routing (confidence: {ai_response.routing_decision.confidence:.2f})")
                return {"success": False, "reason": "low_confidence"}
        except Exception as e:
            logger.error(f"❌ Cursor routing failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _log_webhook_request(self, event: GPT4oEventSchema, 
                           ai_response) -> None:
        """
        Log webhook request details.
        
        Args:
            event: Validated event
            ai_response: Response from AI provider
        """
        logger.info(f"📝 Webhook processed - Event: {event.event_id}")
        logger.info(f"   Provider: {ai_response.provider.value}")
        logger.info(f"   Model: {ai_response.model}")
        logger.info(f"   Response Time: {ai_response.response_time:.2f}s")
        logger.info(f"   Tokens: {ai_response.usage.get('total_tokens', 0)}")
        logger.info(f"   Routing Confidence: {ai_response.routing_decision.confidence:.2f}")
        logger.info(f"   Strategy: {ai_response.routing_decision.strategy.value}")
        
        # Log routing decision reasoning
        logger.info(f"   Reasoning: {ai_response.routing_decision.reasoning}")
        
        # Log provider metrics
        metrics = get_router_metrics()
        for provider, metric in metrics.items():
            logger.info(f"   {provider.upper()} - Latency: {metric['avg_latency']:.2f}s, "
                       f"Success: {metric['success_rate']:.2%}")


def create_sample_grok_webhook():
    """Create a sample Grok webhook for testing."""
    handler = GrokWebhookHandler()
    
    # Sample GitHub pull request event
    sample_event = {
        "repository": {
            "name": "gitbridge",
            "full_name": "user/gitbridge"
        },
        "pull_request": {
            "title": "Add authentication feature",
            "body": "This PR implements JWT-based authentication for the API endpoints.",
            "number": 123,
            "files": [
                {"filename": "auth.py", "status": "added"},
                {"filename": "test_auth.py", "status": "added"}
            ]
        },
        "sender": {
            "login": "developer"
        }
    }
    
    # Process webhook
    result = handler.process_webhook(sample_event, "pull_request", "github")
    
    return result


def main():
    """Main function for testing and demonstration."""
    print("🔄 GitBridge Grok Webhook Handler")
    print("Task: P20P7S4 - Live Workflow Integration")
    print("=" * 60)
    
    # Check environment
    if not os.getenv('XAI_API_KEY'):
        print("⚠️  XAI_API_KEY not found in environment")
        print("   Please set XAI_API_KEY in your .env file")
        return
    
    # Test webhook processing
    print("\n🧪 Testing Grok webhook processing...")
    result = create_sample_grok_webhook()
    
    if result["success"]:
        print(f"✅ Webhook processing successful!")
        print(f"   Event ID: {result['event_id']}")
        print(f"   AI Model: {result['ai_response']['model']}")
        print(f"   Response Time: {result['ai_response']['response_time']:.2f}s")
        print(f"   Tokens: {result['ai_response']['tokens']}")
        print(f"   Cursor File Created: {result['cursor_file_created']}")
        if result.get('cursor_file_path'):
            print(f"   Cursor File: {result['cursor_file_path']}")
    else:
        print(f"❌ Webhook processing failed: {result['error']}")
    
    print("\n✅ Grok webhook handler ready for integration!")
    print("📝 Logs will be written to logs/grok_webhook_trace.log")
    print("🔄 Ready for Cursor integration (P20P6S3)")


if __name__ == "__main__":
    main() 