"""
GitBridge Phase 18 - Figma Webhook Server.

Flask server that listens for Figma webhook POST events, processes them through
the parser module, and saves results to figma_invites.json.

Implements MAS Lite Protocol v2.1 compliance and follows GitBridge
recursive validation principles.

Author: GitBridge Team
Phase: 18 (Segment 2 - SmartRepo Core + Demo Readiness)
MAS Lite Protocol v2.1 Compliance: Yes
"""

from flask import Flask, request, jsonify
import logging
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from figma_parser_module import parse_figma_payload, validate_figma_webhook_signature

# Initialize Flask application
app = Flask(__name__)

# Configure logging with INFO and ERROR levels as specified
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/figma_webhook.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Configuration constants
FIGMA_OUTPUT_FILE = "figma_invites.json"
WEBHOOK_SECRET_ENV = "FIGMA_WEBHOOK_SECRET"


def ensure_logs_directory() -> None:
    """Ensure logs directory exists for webhook logging."""
    if not os.path.exists('logs'):
        os.makedirs('logs')
        logger.info("Created logs directory for webhook logging")


def validate_webhook_security(payload_data: str, headers: Dict[str, str]) -> bool:
    """
    Validate webhook security using signature verification.
    
    Args:
        payload_data (str): Raw payload data
        headers (Dict[str, str]): Request headers
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    webhook_secret = os.environ.get(WEBHOOK_SECRET_ENV)
    
    # Skip signature validation if no secret is configured (development mode)
    if not webhook_secret:
        logger.warning("No FIGMA_WEBHOOK_SECRET configured - skipping signature validation")
        return True
    
    signature = headers.get('X-Figma-Signature', '')
    if not signature:
        logger.error("Missing X-Figma-Signature header")
        return False
    
    return validate_figma_webhook_signature(payload_data, signature, webhook_secret)


def save_parsed_data_atomically(parsed_data: Dict[str, Any]) -> bool:
    """
    Save parsed data to figma_invites.json atomically to prevent corruption.
    
    Args:
        parsed_data (Dict[str, Any]): Parsed Figma data to save
        
    Returns:
        bool: True if save successful, False otherwise
    """
    try:
        # Load existing data if file exists
        existing_data = []
        if os.path.exists(FIGMA_OUTPUT_FILE):
            try:
                with open(FIGMA_OUTPUT_FILE, "r", encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]  # Convert single object to list
            except json.JSONDecodeError:
                logger.warning(f"Existing {FIGMA_OUTPUT_FILE} contains invalid JSON - starting fresh")
                existing_data = []
        
        # Append new data
        existing_data.append(parsed_data)
        
        # Write atomically using temporary file
        temp_file = f"{FIGMA_OUTPUT_FILE}.tmp"
        with open(temp_file, "w", encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        os.rename(temp_file, FIGMA_OUTPUT_FILE)
        
        logger.info(f"Successfully saved parsed data to {FIGMA_OUTPUT_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save parsed data: {e}")
        # Clean up temporary file if it exists
        if os.path.exists(f"{FIGMA_OUTPUT_FILE}.tmp"):
            try:
                os.remove(f"{FIGMA_OUTPUT_FILE}.tmp")
            except OSError:
                pass
        return False


@app.route('/figma-webhook', methods=['POST'])
def handle_figma_webhook():
    """
    Handle incoming Figma webhook POST requests.
    
    This endpoint:
    1. Validates the incoming JSON payload
    2. Verifies webhook signature for security
    3. Calls parse_figma_payload() from figma_parser_module
    4. Saves the parsed result to figma_invites.json
    5. Returns appropriate JSON status response
    
    Returns:
        JSON response with status and appropriate HTTP status code
    """
    try:
        # Step 1: Validate incoming JSON payload
        raw_data = request.get_data(as_text=True)
        if not raw_data:
            logger.warning("Received empty request body")
            return jsonify({
                "error": "Empty request body",
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 400
        
        try:
            payload = request.get_json(force=True)
        except Exception as json_error:
            logger.error(f"Invalid JSON payload: {json_error}")
            return jsonify({
                "error": "Invalid JSON payload",
                "details": str(json_error),
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 400
        
        if not payload:
            logger.warning("Received null or empty JSON payload")
            return jsonify({
                "error": "Null or empty JSON payload",
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 400
        
        logger.info(f"Received Figma webhook with event type: {payload.get('event_type', 'unknown')}")
        
        # Step 2: Verify webhook signature for security
        if not validate_webhook_security(raw_data, dict(request.headers)):
            logger.error("Webhook signature validation failed")
            return jsonify({
                "error": "Invalid webhook signature",
                "status": "unauthorized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 401
        
        # Step 3: Process the payload with parser module
        try:
            parsed_data = parse_figma_payload(payload)
            logger.info(f"Successfully parsed Figma payload: {parsed_data['event_metadata']['payload_hash'][:8]}...")
        except (ValueError, TypeError) as parse_error:
            logger.error(f"Payload parsing failed: {parse_error}")
            return jsonify({
                "error": "Payload parsing failed",
                "details": str(parse_error),
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 400
        
        # Step 4: Save parsed data to output JSON file atomically
        if not save_parsed_data_atomically(parsed_data):
            logger.error("Failed to save parsed data to file")
            return jsonify({
                "error": "Failed to save parsed data",
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500
        
        # Step 5: Return successful JSON status to Figma
        success_response = {
            "status": "success",
            "message": "Webhook processed successfully",
            "event_type": parsed_data['figma_data']['event_type'],
            "payload_hash": parsed_data['event_metadata']['payload_hash'][:8],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mas_lite_version": "2.1"
        }
        
        logger.info(f"Successfully processed Figma webhook: {parsed_data['figma_data']['event_type']}")
        return jsonify(success_response), 200
        
    except Exception as e:
        # Comprehensive error handling for any unexpected exceptions
        error_message = f"Unexpected error during webhook processing: {e}"
        logger.error(error_message, exc_info=True)  # Include stack trace
        
        return jsonify({
            "error": "Internal server error",
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring and deployment validation.
    
    Returns:
        JSON response indicating server health status
    """
    try:
        # Basic health indicators
        health_status = {
            "status": "healthy",
            "service": "figma-webhook-server",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mas_lite_version": "2.1",
            "figma_output_file_exists": os.path.exists(FIGMA_OUTPUT_FILE),
            "logs_directory_exists": os.path.exists('logs')
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with proper JSON response."""
    return jsonify({
        "error": "Endpoint not found",
        "status": "error",
        "available_endpoints": ["/figma-webhook", "/health"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors."""
    return jsonify({
        "error": "Method not allowed",
        "status": "error",
        "allowed_methods": ["POST"] if request.endpoint == 'handle_figma_webhook' else ["GET"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 405


if __name__ == '__main__':
    # Recursive validation step 1: Ensure proper initialization
    ensure_logs_directory()
    
    # Recursive validation step 2: Log startup configuration
    webhook_secret_configured = bool(os.environ.get(WEBHOOK_SECRET_ENV))
    logger.info(f"Starting Figma Webhook Server - Phase 18")
    logger.info(f"Webhook secret configured: {webhook_secret_configured}")
    logger.info(f"Output file: {FIGMA_OUTPUT_FILE}")
    logger.info(f"Listening on port 5005 for Figma webhooks")
    
    # Recursive validation step 3: Production-ready server configuration
    try:
        app.run(
            host="0.0.0.0",  # Accept connections from any IP
            port=5005,       # As specified in requirements
            debug=False,     # Production mode
            threaded=True    # Handle concurrent requests
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise 