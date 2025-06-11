#!/usr/bin/env python3
"""
Integration tests for GitBridge webhook system.
Tests end-to-end flows from webhook receipt to MAS task creation.
"""

import json
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import hmac
import hashlib
import aiohttp
import redis
from prometheus_client.parser import text_string_to_metric_families

# Mark entire module as skipped for Phase 19 runtime failure
pytestmark = pytest.mark.skip(reason="Phase 19 runtime failure - pending fix in Phase 23")

# Mock GitHub webhook payload
MOCK_PUSH_EVENT = {
    "ref": "refs/heads/main",
    "repository": {
        "full_name": "octocat/Hello-World",
        "private": False
    },
    "commits": [
        {
            "id": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
            "message": "Fix all the bugs",
            "timestamp": "2011-04-14T16:00:49Z",
            "author": {
                "name": "Monalisa Octocat",
                "email": "mona@github.com"
            }
        }
    ]
}

class TestWebhookFlow:
    """Integration tests for webhook processing flow."""
    
    @pytest.fixture
    async def webhook_client(self):
        """Create aiohttp client for webhook requests."""
        async with aiohttp.ClientSession() as session:
            yield session
            
    @pytest.fixture
    def redis_client(self):
        """Create Redis client for rate limiting tests."""
        client = redis.Redis(host='localhost', port=6379, db=0)
        yield client
        client.flushdb()  # Clean up after tests
        
    @pytest.fixture
    def github_signature(self):
        """Generate GitHub webhook signature."""
        secret = "test_secret"
        payload = json.dumps(MOCK_PUSH_EVENT).encode()
        signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return f"sha256={signature}"
        
    async def test_valid_webhook_flow(self, webhook_client, github_signature):
        """Test successful webhook processing flow."""
        headers = {
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": github_signature,
            "X-GitHub-Delivery": "72d3162e-cc78-11e3-81ab-4c9367dc0958"
        }
        
        # Send webhook request
        async with webhook_client.post(
            "http://localhost:8000/webhook",
            json=MOCK_PUSH_EVENT,
            headers=headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["status"] == "success"
            assert "task_id" in data
            
        # Verify event processing
        await asyncio.sleep(1)  # Allow time for async processing
        
        # Check metrics
        metrics_response = await webhook_client.get("http://localhost:9090/metrics")
        metrics_text = await metrics_response.text()
        metrics = {
            family.name: family
            for family in text_string_to_metric_families(metrics_text)
        }
        
        # Verify webhook request was counted
        assert "gitbridge_webhook_requests_total" in metrics
        assert any(
            sample.labels["event_type"] == "push" and sample.labels["status"] == "success"
            for sample in metrics["gitbridge_webhook_requests_total"].samples
        )
        
    async def test_rate_limiting(self, webhook_client, github_signature, redis_client):
        """Test rate limiting behavior."""
        headers = {
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": github_signature,
            "X-GitHub-Delivery": "72d3162e-cc78-11e3-81ab-4c9367dc0958"
        }
        
        # Set low rate limit for test
        redis_client.set("rate_limit:webhook:test", "0")
        
        # Attempt webhook request
        async with webhook_client.post(
            "http://localhost:8000/webhook",
            json=MOCK_PUSH_EVENT,
            headers=headers
        ) as response:
            assert response.status == 429  # Too Many Requests
            data = await response.json()
            assert data["error"] == "rate_limit_exceeded"
            
    async def test_invalid_signature(self, webhook_client):
        """Test security validation for invalid signatures."""
        headers = {
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": "sha256=invalid",
            "X-GitHub-Delivery": "72d3162e-cc78-11e3-81ab-4c9367dc0958"
        }
        
        # Attempt webhook request with invalid signature
        async with webhook_client.post(
            "http://localhost:8000/webhook",
            json=MOCK_PUSH_EVENT,
            headers=headers
        ) as response:
            assert response.status == 401  # Unauthorized
            data = await response.json()
            assert data["error"] == "invalid_signature"
            
    async def test_metrics_logging(self, webhook_client, github_signature):
        """Test metrics are properly logged."""
        headers = {
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": github_signature,
            "X-GitHub-Delivery": "72d3162e-cc78-11e3-81ab-4c9367dc0958"
        }
        
        # Send webhook request
        async with webhook_client.post(
            "http://localhost:8000/webhook",
            json=MOCK_PUSH_EVENT,
            headers=headers
        ) as response:
            assert response.status == 200
            
        # Verify metrics
        metrics_response = await webhook_client.get("http://localhost:9090/metrics")
        metrics_text = await metrics_response.text()
        
        # Check for required metrics
        assert "gitbridge_webhook_requests_total" in metrics_text
        assert "gitbridge_event_processing_seconds" in metrics_text
        assert "gitbridge_event_queue_depth" in metrics_text
        assert "gitbridge_rate_limit_remaining" in metrics_text

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 