# GitBridge Webhook Event Flow Walkthrough

This document walks through the complete flow of a GitHub webhook event through the GitBridge system, from initial POST to MAS task creation.

## Example Event: Pull Request Opening

We'll follow a pull request "opened" event (see `webhook_post_example.json`) through the entire system.

### 1. Initial Webhook Receipt

```http
POST /webhook
Host: api.gitbridge.com
X-GitHub-Event: pull_request
X-Hub-Signature-256: sha256=...
X-GitHub-Delivery: 72d3162e-cc78-11e3-81ab-4c9367dc0958
Content-Type: application/json

{
  "action": "opened",
  "pull_request": {
    "title": "Amazing new feature",
    "number": 1,
    ...
  }
}
```

### 2. Rate Limiting Check

1. Request hits rate limiter first
2. Redis check for current limits:
   ```redis
   GET rate_limit:webhook:repo_1296269
   ```
3. If within limits, increment counter:
   ```redis
   INCR rate_limit:webhook:repo_1296269
   EXPIRE rate_limit:webhook:repo_1296269 3600
   ```

### 3. Security Validation

1. IP whitelist check against GitHub's published ranges
2. Signature validation:
   ```python
   expected = hmac.new(
       webhook_secret.encode(),
       request.body,
       hashlib.sha256
   ).hexdigest()
   assert hmac.compare_digest(signature, expected)
   ```
3. Payload structure validation

### 4. Event Processing

1. Event type identification (`pull_request`)
2. Action filtering (`opened`)
3. Queue insertion:
   ```python
   await event_queue.put({
       'type': 'pull_request',
       'action': 'opened',
       'repo': 'octocat/Hello-World',
       'number': 1,
       'title': 'Amazing new feature'
   })
   ```

### 5. Task Generation

1. Event processor picks up queued event
2. Generates MAS task:
   ```python
   task = {
       'type': 'review_pull_request',
       'priority': 'high',
       'metadata': {
           'repo': 'octocat/Hello-World',
           'pr_number': 1,
           'title': 'Amazing new feature',
           'author': 'octocat'
       },
       'protocol_version': '2.1'
   }
   ```

### 6. MAS Integration

1. Task submission to MAS:
   ```python
   response = await mas_client.submit_task(
       task_type='review_pull_request',
       payload=task,
       callback_url='https://api.gitbridge.com/mas/callback'
   )
   ```

2. Task tracking initialization:
   ```python
   await task_tracker.create({
       'task_id': response.task_id,
       'status': 'pending',
       'github_event_id': '72d3162e-cc78-11e3-81ab-4c9367dc0958',
       'created_at': datetime.utcnow()
   })
   ```

### 7. Metrics & Monitoring

Throughout the process, metrics are collected:

```python
# Request timing
webhook_request_duration.observe(duration_ms)

# Queue depth
event_queue_depth.set(current_depth)

# Event counts
webhook_events_total.labels(
    type='pull_request',
    action='opened',
    status='success'
).inc()
```

### 8. Collaboration Features

1. Notification dispatch:
   ```python
   await notifier.send({
       'channel': '#gitbridge-reviews',
       'message': 'New PR: Amazing new feature',
       'url': 'https://github.com/octocat/Hello-World/pull/1'
   })
   ```

2. Documentation update:
   ```python
   await doc_manager.record_event({
       'type': 'pull_request',
       'repo': 'octocat/Hello-World',
       'number': 1,
       'timestamp': '2011-01-26T19:01:12Z'
   })
   ```

## Error Handling

At each stage, errors are caught and handled appropriately:

1. Rate limit exceeded → 429 response
2. Invalid signature → 401 response
3. Invalid payload → 400 response
4. Processing error → Queue retry
5. MAS error → Task retry with backoff

## Monitoring

The entire flow can be monitored through:

1. Prometheus metrics at `/metrics`
2. Grafana dashboard "GitBridge Webhook Flow"
3. Structured logs with correlation IDs
4. Audit trail in security logs

## Development Testing

To test this flow locally:

1. Start mock services:
   ```bash
   docker-compose up redis prometheus grafana
   ```

2. Send test webhook:
   ```bash
   ./dev_tools/send_test_webhook.py \
     --event pull_request \
     --payload docs/examples/webhook_post_example.json
   ```

3. Monitor flow:
   ```bash
   tail -f logs/webhook.log | jq .
   ``` 