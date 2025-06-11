"""
Test webhook listener functionality.

This module tests the webhook listener functionality for GitBridge's event processing
system, following MAS Lite Protocol v2.1 webhook requirements.
"""

import os
import json
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from integrations.webhook_listener import app, commit_router
from mas_core.error_handler import ErrorCategory, ErrorSeverity

@pytest.fixture
def test_client():
    """Test client fixture."""
    return TestClient(app)

@pytest.fixture
def webhook_secret():
    """Webhook secret fixture."""
    return "test_secret"

@pytest.fixture
def mock_commit_router():
    """Mock commit router fixture."""
    with patch("integrations.webhook_listener.commit_router") as mock:
        yield mock

def generate_signature(payload: bytes, secret: str) -> str:
    """Generate webhook signature."""
    return "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

class TestWebhookListener:
    """Webhook listener test suite."""
    
    def test_missing_signature(self, test_client):
        """Test webhook without signature."""
        response = test_client.post("/webhook", json={})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid signature"
    
    def test_invalid_signature(self, test_client, webhook_secret):
        """Test webhook with invalid signature."""
        payload = json.dumps({"test": "data"}).encode()
        headers = {
            "X-Hub-Signature-256": "invalid",
            "X-GitHub-Event": "push"
        }
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": webhook_secret}):
            response = test_client.post(
                "/webhook",
                data=payload,
                headers=headers
            )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid signature"
    
    def test_valid_signature_no_commits(self, test_client, webhook_secret):
        """Test webhook with valid signature but no commits."""
        payload = json.dumps({"commits": []}).encode()
        signature = generate_signature(payload, webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push"
        }
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": webhook_secret}):
            response = test_client.post(
                "/webhook",
                data=payload,
                headers=headers
            )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["message"] == "No commits to process"
    
    def test_valid_push_event(self, test_client, webhook_secret, mock_commit_router):
        """Test valid push event processing."""
        # Mock commit router response
        mock_commit_router.route_commit.return_value = "test-task-id"
        
        # Create test payload
        payload = json.dumps({
            "commits": [
                {
                    "id": "test-commit-1",
                    "message": "Test commit 1"
                },
                {
                    "id": "test-commit-2",
                    "message": "Test commit 2"
                }
            ]
        }).encode()
        
        # Generate signature
        signature = generate_signature(payload, webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push"
        }
        
        # Send request
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": webhook_secret}):
            response = test_client.post(
                "/webhook",
                data=payload,
                headers=headers
            )
            
        # Verify response
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["message"] == "Processed 2 commits"
        assert len(response.json()["task_ids"]) == 2
        assert all(tid == "test-task-id" for tid in response.json()["task_ids"])
        
        # Verify commit router calls
        assert mock_commit_router.route_commit.call_count == 2
    
    def test_non_push_event(self, test_client, webhook_secret):
        """Test non-push event handling."""
        payload = json.dumps({"test": "data"}).encode()
        signature = generate_signature(payload, webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "issues"
        }
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": webhook_secret}):
            response = test_client.post(
                "/webhook",
                data=payload,
                headers=headers
            )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["message"] == "Ignored issues event"
    
    def test_missing_event_type(self, test_client, webhook_secret):
        """Test missing event type header."""
        payload = json.dumps({"test": "data"}).encode()
        signature = generate_signature(payload, webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature
        }
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": webhook_secret}):
            response = test_client.post(
                "/webhook",
                data=payload,
                headers=headers
            )
        assert response.status_code == 400
        assert response.json()["detail"] == "Missing event type"
    
    def test_get_task_status(self, test_client, mock_commit_router):
        """Test task status retrieval."""
        # Mock task status
        mock_commit_router.get_task_status.return_value = {
            "task_id": "test-task",
            "state": "InProgress"
        }
        
        # Get existing task
        response = test_client.get("/task/test-task")
        assert response.status_code == 200
        assert response.json()["task_id"] == "test-task"
        assert response.json()["state"] == "InProgress"
        
        # Get non-existent task
        mock_commit_router.get_task_status.return_value = None
        response = test_client.get("/task/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    
    def test_server_error_handling(self, test_client, webhook_secret, mock_commit_router):
        """Test server error handling."""
        # Mock commit router to raise exception
        mock_commit_router.route_commit.side_effect = Exception("Test error")
        
        # Create test payload
        payload = json.dumps({
            "commits": [{"id": "test-commit", "message": "Test commit"}]
        }).encode()
        
        # Generate signature
        signature = generate_signature(payload, webhook_secret)
        headers = {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push"
        }
        
        # Send request
        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": webhook_secret}):
            response = test_client.post(
                "/webhook",
                data=payload,
                headers=headers
            )
            
        # Verify response
        assert response.status_code == 500
        assert response.json()["detail"] == "Internal server error" 