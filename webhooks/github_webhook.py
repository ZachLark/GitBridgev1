#!/usr/bin/env python3
"""
GitBridge GitHub Webhook → GPT-4o Integration
Task: P20P3S1 - GitHub Webhook → GPT-4o Integration

This module provides a webhook handler that receives GitHub events,
converts them to structured GPT-4o event payloads, and routes them
to the GPT-4o client for real-time AI processing.

Author: GitBridge Development Team
Date: 2025-01-11
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import asdict

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Third-party imports
from flask import Flask, request, jsonify
import hmac
import hashlib

# Local imports
from utils.schema_validator import GPT4oEventSchema, EventSource, EventType, OutputType, ToneType, SchemaValidator
from tests.test_gpt4o_connection import GPT4oClient, GPT4oConfig, load_environment_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gpt_webhook_trace.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global variables
gpt_client = None
schema_validator = None


def initialize_services():
    """Initialize GPT-4o client and schema validator."""
    global gpt_client, schema_validator
    
    try:
        # Load configuration
        config = load_environment_config()
        gpt_client = GPT4oClient(config)
        schema_validator = SchemaValidator()
        
        logger.info("✅ Services initialized successfully")
        logger.info(f"GPT-4o Model: {config.model}")
        logger.info(f"GPT-4o Project: {config.project}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {str(e)}")
        raise


def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature for security.
    
    Args:
        payload: Raw request payload
        signature: GitHub signature header
        secret: Webhook secret from environment
        
    Returns:
        bool: True if signature is valid
    """
    if not secret:
        logger.warning("No webhook secret configured, skipping signature verification")
        return True
    
    expected_signature = f"sha256={hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()}"
    return hmac.compare_digest(signature, expected_signature)


def extract_github_context(github_event: Dict[str, Any], event_type: str) -> str:
    """
    Extract relevant context from GitHub event based on event type.
    
    Args:
        github_event: Raw GitHub webhook payload
        event_type: Type of GitHub event
        
    Returns:
        str: Formatted context string
    """
    context_parts = []
    
    if event_type == "pull_request":
        pr = github_event.get("pull_request", {})
        context_parts.extend([
            f"Repository: {github_event.get('repository', {}).get('full_name', 'Unknown')}",
            f"Pull Request #{pr.get('number', 'Unknown')}: {pr.get('title', 'No title')}",
            f"Author: @{pr.get('user', {}).get('login', 'Unknown')}",
            f"Branch: {pr.get('head', {}).get('ref', 'Unknown')} → {pr.get('base', {}).get('ref', 'Unknown')}",
            f"State: {pr.get('state', 'Unknown')}",
            f"Action: {github_event.get('action', 'Unknown')}",
            "",
            f"Description:",
            f"{pr.get('body', 'No description provided')}",
            ""
        ]
        )
        
        # Add changed files if available
        if 'files' in pr:
            context_parts.append("Files changed:")
            for file in pr['files']:
                context_parts.append(f"- {file.get('filename', 'Unknown')} ({file.get('status', 'Unknown')})")
            context_parts.append("")
    
    elif event_type == "push":
        repo = github_event.get("repository", {})
        context_parts.extend([
            f"Repository: {repo.get('full_name', 'Unknown')}",
            f"Branch: {github_event.get('ref', 'Unknown')}",
            f"Pusher: @{github_event.get('pusher', {}).get('name', 'Unknown')}",
            f"Commits: {len(github_event.get('commits', []))}",
            ""
        ])
        
        # Add commit messages
        commits = github_event.get('commits', [])
        if commits:
            context_parts.append("Recent commits:")
            for commit in commits[-3:]:  # Last 3 commits
                context_parts.append(f"- {commit.get('message', 'No message').split(chr(10))[0]}")
            context_parts.append("")
    
    elif event_type == "issues":
        issue = github_event.get("issue", {})
        context_parts.extend([
            f"Repository: {github_event.get('repository', {}).get('full_name', 'Unknown')}",
            f"Issue #{issue.get('number', 'Unknown')}: {issue.get('title', 'No title')}",
            f"Author: @{issue.get('user', {}).get('login', 'Unknown')}",
            f"State: {issue.get('state', 'Unknown')}",
            f"Action: {github_event.get('action', 'Unknown')}",
            "",
            f"Description:",
            f"{issue.get('body', 'No description provided')}",
            ""
        ])
    
    else:
        # Generic fallback
        context_parts.extend([
            f"Repository: {github_event.get('repository', {}).get('full_name', 'Unknown')}",
            f"Event Type: {event_type}",
            f"Action: {github_event.get('action', 'Unknown')}",
            "",
            f"Raw Event Data:",
            f"{json.dumps(github_event, indent=2)}"
        ])
    
    return "\n".join(context_parts)


def determine_goal_and_output(event_type: str, action: str) -> tuple[str, OutputType, ToneType]:
    """
    Determine the goal and output format based on GitHub event type and action.
    
    Args:
        event_type: GitHub event type
        action: GitHub event action
        
    Returns:
        tuple: (goal, output_type, tone)
    """
    if event_type == "pull_request":
        if action in ["opened", "synchronize"]:
            return (
                "Review this pull request for code quality, security best practices, and potential issues. Provide actionable feedback for the author.",
                OutputType.PR_COMMENT,
                ToneType.REVIEWER
            )
        elif action == "closed":
            return (
                "Summarize the changes made in this pull request and provide a brief assessment of the overall impact.",
                OutputType.SUMMARY,
                ToneType.CONCISE
            )
        else:
            return (
                f"Analyze this pull request {action} event and provide relevant insights.",
                OutputType.REVIEW_FEEDBACK,
                ToneType.HELPFUL
            )
    
    elif event_type == "push":
        return (
            "Summarize the changes made in this push and identify any potential issues or improvements.",
            OutputType.SUMMARY,
            ToneType.TECHNICAL
        )
    
    elif event_type == "issues":
        if action == "opened":
            return (
                "Analyze this issue and provide suggestions for resolution or next steps.",
                OutputType.RECOMMENDATION,
                ToneType.HELPFUL
            )
        else:
            return (
                f"Analyze this issue {action} event and provide relevant insights.",
                OutputType.DIAGNOSTIC,
                ToneType.TECHNICAL
            )
    
    else:
        return (
            f"Analyze this {event_type} event and provide relevant insights.",
            OutputType.SUMMARY,
            ToneType.CONCISE
        )


def create_gpt4o_event(github_event: Dict[str, Any], event_type: str) -> GPT4oEventSchema:
    """
    Convert GitHub event to GPT4oEventSchema format.
    
    Args:
        github_event: Raw GitHub webhook payload
        event_type: GitHub event type
        
    Returns:
        GPT4oEventSchema: Structured event for GPT-4o
    """
    # Extract metadata
    action = github_event.get('action', 'unknown')
    repo = github_event.get('repository', {})
    repo_name = repo.get('full_name', 'unknown')
    
    # Generate event ID
    event_id = f"gh_{event_type}_{action}_{int(time.time())}"
    
    # Determine goal and output format
    goal, output_type, tone = determine_goal_and_output(event_type, action)
    
    # Extract context
    context = extract_github_context(github_event, event_type)
    
    # Create event schema
    event = GPT4oEventSchema(
        event_id=event_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        source=EventSource.GITHUB,
        event_type=EventType(event_type),
        context=context,
        goal=goal,
        tone=tone,
        requested_output=output_type,
        priority=7,  # Medium priority for GitHub events
        tags=[event_type, action, "github"],
        metadata={
            "repository": repo_name,
            "action": action,
            "event_type": event_type,
            "github_event_id": github_event.get('id'),
            "sender": github_event.get('sender', {}).get('login')
        },
        session_id=f"webhook_{int(time.time())}"
    )
    
    return event


@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    """
    GitHub webhook endpoint that processes events and routes them to GPT-4o.
    """
    start_time = time.time()
    
    try:
        # Get request data
        payload = request.get_data()
        signature = request.headers.get('X-Hub-Signature-256', '')
        
        # Verify signature
        webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET', '')
        if not verify_github_signature(payload, signature, webhook_secret):
            logger.warning("❌ Invalid GitHub signature")
            return jsonify({"error": "Invalid signature"}), 401
        
        # Parse JSON payload
        github_event = request.get_json()
        if not github_event:
            logger.error("❌ Invalid JSON payload")
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Extract event type
        event_type = request.headers.get('X-GitHub-Event', 'unknown')
        logger.info(f"📥 Received GitHub {event_type} event")
        
        # Convert to GPT4oEventSchema
        gpt_event = create_gpt4o_event(github_event, event_type)
        
        # Validate schema
        try:
            schema_validator.validate_event(gpt_event.to_dict())
            logger.info(f"✅ Event schema validation passed")
        except Exception as e:
            logger.error(f"❌ Event schema validation failed: {str(e)}")
            return jsonify({"error": "Invalid event schema"}), 400
        
        # Send to GPT-4o
        logger.info(f"🤖 Sending event to GPT-4o...")
        response = gpt_client.send_message(
            messages=[{"role": "user", "content": gpt_event.to_prompt_string()}],
            system_prompt="You are a helpful AI assistant for the GitBridge project. Provide clear, actionable responses based on the event context."
        )
        
        # Log response
        processing_time = time.time() - start_time
        logger.info(f"✅ GPT-4o response received in {processing_time:.2f}s")
        
        if response.success:
            logger.info(f"📝 GPT-4o Response: {response.content[:200]}...")
            
            # Log full trace
            trace_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_id": gpt_event.event_id,
                "github_event_type": event_type,
                "processing_time": processing_time,
                "gpt_response": response.content,
                "gpt_model": response.model,
                "gpt_usage": response.usage,
                "success": True
            }
            
            with open('logs/gpt_webhook_trace.log', 'a') as f:
                f.write(f"\n{json.dumps(trace_data, indent=2)}\n")
            
            return jsonify({
                "success": True,
                "event_id": gpt_event.event_id,
                "processing_time": processing_time,
                "gpt_response": response.content[:500] + "..." if len(response.content) > 500 else response.content
            })
        
        else:
            logger.error(f"❌ GPT-4o request failed: {response.error_message}")
            return jsonify({
                "success": False,
                "error": response.error_message
            }), 500
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Webhook processing error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "processing_time": processing_time
        }), 500


@app.route('/webhook/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gpt_client_ready": gpt_client is not None
    })


def main():
    """Main function to run the webhook server."""
    print("🚀 GitBridge GitHub Webhook → GPT-4o Integration")
    print("Task: P20P3S1 - GitHub Webhook → GPT-4o Integration")
    print("=" * 60)
    
    try:
        # Initialize services
        initialize_services()
        
        # Run Flask app
        port = int(os.getenv('WEBHOOK_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        print(f"🌐 Starting webhook server on port {port}")
        print(f"📝 Logs will be written to logs/gpt_webhook_trace.log")
        print(f"🔗 GitHub webhook endpoint: http://localhost:{port}/webhook/github")
        print(f"❤️  Health check endpoint: http://localhost:{port}/webhook/health")
        print("-" * 60)
        
        app.run(host='0.0.0.0', port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"❌ Failed to start webhook server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 