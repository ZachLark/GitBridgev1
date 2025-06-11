"""
Webhook listener for GitBridge MAS Lite.

This module provides webhook handling functionality for GitBridge's event processing
system, following MAS Lite Protocol v2.1 webhook requirements.
"""

import os
import json
import hmac
import hashlib
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .commit_router import CommitRouter
from mas_core.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from mas_core.utils.logging import MASLogger

logger = MASLogger(__name__)

# Load configuration
config = {
    "router": {
        "max_concurrent": 5,
        "consensus_required": True
    },
    "task_chain": {
        "states": ["Created", "InProgress", "Blocked", "Resolved", "Failed"],
        "max_concurrent": 5,
        "consensus_required": True
    },
    "consensus": {
        "timeout": 5,
        "required_nodes": 3
    }
}

# Initialize components
commit_router = CommitRouter(config)
error_handler = ErrorHandler()
security = HTTPBasic()

# Create FastAPI app
app = FastAPI(title="GitBridge Webhook Listener")

async def verify_signature(request: Request) -> bool:
    """Verify webhook signature.
    
    Args:
        request: FastAPI request
        
    Returns:
        bool: True if signature is valid
    """
    try:
        # Get webhook secret from environment
        webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
        if not webhook_secret:
            logger.error("GITHUB_WEBHOOK_SECRET environment variable not set")
            return False
            
        # Get signature from headers
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            logger.error("Missing X-Hub-Signature-256 header")
            return False
            
        # Calculate expected signature
        body = await request.body()
        expected_signature = "sha256=" + hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        error_id = str(uuid.uuid4())
        error_handler.handle_error(
            error_id=error_id,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.ERROR,
            message=f"Failed to verify signature: {str(e)}",
            details={"error": str(e)}
        )
        return False

@app.post("/webhook")
async def receive_webhook(request: Request) -> Dict[str, Any]:
    """Receive webhook event.
    
    Args:
        request: FastAPI request
        
    Returns:
        Dict[str, Any]: Response data
    """
    try:
        # Verify signature
        if not await verify_signature(request):
            raise HTTPException(status_code=401, detail="Invalid signature")
            
        # Parse event data
        event_data = await request.json()
        
        # Get event type
        event_type = request.headers.get("X-GitHub-Event")
        if not event_type:
            raise HTTPException(status_code=400, detail="Missing event type")
            
        # Process event
        if event_type == "push":
            # Get commit data
            commits = event_data.get("commits", [])
            if not commits:
                return {"status": "success", "message": "No commits to process"}
                
            # Process each commit
            task_ids = []
            for commit in commits:
                task_id = await commit_router.route_commit(commit)
                if task_id:
                    task_ids.append(task_id)
                    
            return {
                "status": "success",
                "message": f"Processed {len(task_ids)} commits",
                "task_ids": task_ids
            }
            
        else:
            return {
                "status": "success",
                "message": f"Ignored {event_type} event"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        error_id = str(uuid.uuid4())
        error_handler.handle_error(
            error_id=error_id,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.ERROR,
            message=f"Failed to process webhook: {str(e)}",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/task/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get task status.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Dict[str, Any]: Task status
    """
    try:
        status = await commit_router.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        error_id = str(uuid.uuid4())
        error_handler.handle_error(
            error_id=error_id,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.ERROR,
            message=f"Failed to get task status: {str(e)}",
            details={
                "task_id": task_id,
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail="Internal server error") 