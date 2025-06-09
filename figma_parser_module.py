"""
Figma Parser Module for GitBridge Phase 18.

This module provides parsing functionality for Figma webhook payloads,
implementing MAS Lite Protocol v2.1 data structures and validation.

Author: GitBridge Team
MAS Lite Protocol v2.1 Compliance: Yes
"""

import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Configure logging for this module
logger = logging.getLogger(__name__)

def parse_figma_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Figma webhook payload and return standardized data structure.
    
    This function processes incoming Figma webhook data and converts it to
    a standardized format compatible with MAS Lite Protocol v2.1.
    
    Args:
        payload (Dict[str, Any]): Raw Figma webhook payload
        
    Returns:
        Dict[str, Any]: Parsed and standardized data structure
        
    Raises:
        ValueError: If payload is invalid or missing required fields
        TypeError: If payload is not a dictionary
    """
    if not isinstance(payload, dict):
        raise TypeError("Payload must be a dictionary")
    
    if not payload:
        raise ValueError("Payload cannot be empty")
    
    # Generate MAS Lite Protocol v2.1 compliant SHA256 hash
    payload_str = str(sorted(payload.items()))
    payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
    
    # Extract core Figma event data
    event_type = payload.get('event_type', 'unknown')
    timestamp = payload.get('timestamp', datetime.now(timezone.utc).isoformat())
    
    # Build standardized response structure
    parsed_data = {
        'mas_lite_version': '2.1',
        'event_metadata': {
            'event_type': event_type,
            'timestamp': timestamp,
            'source': 'figma_webhook',
            'payload_hash': payload_hash
        },
        'figma_data': {
            'file_key': payload.get('file_key'),
            'file_name': payload.get('file_name'),
            'team_id': payload.get('team_id'),
            'user_id': payload.get('triggered_by', {}).get('id') if payload.get('triggered_by') else None,
            'event_type': event_type,
            'description': payload.get('description', ''),
            'raw_payload': payload
        },
        'processing_status': {
            'parsed_at': datetime.now(timezone.utc).isoformat(),
            'status': 'success',
            'parser_version': '1.0.0'
        }
    }
    
    # Validate required fields based on event type
    if event_type in ['file_update', 'file_comment', 'file_version_update']:
        if not parsed_data['figma_data']['file_key']:
            logger.warning(f"Missing file_key for event type: {event_type}")
    
    # Log successful parsing
    logger.info(f"Successfully parsed Figma payload: {event_type} event with hash {payload_hash[:8]}...")
    
    return parsed_data


def validate_figma_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Validate Figma webhook signature for security.
    
    Args:
        payload (str): Raw webhook payload string
        signature (str): Figma webhook signature
        secret (str): Webhook secret key
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    try:
        # Figma uses HMAC-SHA256 for webhook signatures
        import hmac
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures securely
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    except Exception as e:
        logger.error(f"Error validating webhook signature: {e}")
        return False 