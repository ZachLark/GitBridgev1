# Flask UI Access Instructions
Date: June 3, 2025 – 15:00 PDT

## Overview
This document provides instructions for accessing and using the Flask UI for GBP14-15 components. The UI provides access to task routing, CLI hooks, and metrics visualization.

## Local Deployment

### Prerequisites
1. Python 3.13.3
2. Redis server running locally
3. Environment variables set:
   ```bash
   export GITBRIDGE_ENV=development
   export REDIS_HOST=localhost
   export REDIS_PORT=6379
   export FLASK_SECRET_KEY=your_secret_key
   ```

### Setup Steps
1. Install dependencies:
   ```bash
   pip install -r requirements-webhook.txt
   ```

2. Start Redis server (if not running):
   ```bash
   redis-server
   ```

3. Launch Flask server:
   ```bash
   python -m scripts.run_server.py
   ```

4. Access UI:
   - URL: http://localhost:8888
   - Default credentials:
     - Username: admin
     - Password: gbp_admin_2025

## UI Features

### 1. Task Management
- **Route**: `/tasks`
- **Features**:
  - View task queue
  - Monitor task status
  - View task details
  - Cancel tasks
  - Retry failed tasks

### 2. Agent Management
- **Route**: `/agents`
- **Features**:
  - Register new agents
  - View agent status
  - Monitor agent capacity
  - View agent metrics

### 3. Vote Sequence
- **Route**: `/votes`
- **Features**:
  - View vote history
  - Monitor consensus status
  - View vote distribution
  - Export vote data

### 4. Metrics Dashboard
- **Route**: `/metrics`
- **Features**:
  - Real-time queue depth
  - Latency metrics
  - Error rates
  - Resource utilization
  - Performance graphs

### 5. CLI Integration
- **Route**: `/cli`
- **Features**:
  - Web-based CLI interface
  - Command history
  - Auto-completion
  - Help documentation

## API Documentation

### Task API
```yaml
POST /api/v1/tasks
- Create new task
- Requires authentication
- Returns task ID

GET /api/v1/tasks/{task_id}
- Get task status
- Requires authentication
- Returns task details
```

### Agent API
```yaml
POST /api/v1/agents
- Register new agent
- Requires authentication
- Returns agent ID

GET /api/v1/agents/{agent_id}
- Get agent status
- Requires authentication
- Returns agent details
```

### Metrics API
```yaml
GET /api/v1/metrics
- Get system metrics
- Requires authentication
- Returns metrics data
```

## Authentication

### Token-based Authentication
1. Get token:
   ```bash
   curl -X POST http://localhost:8888/api/v1/auth/token \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "gbp_admin_2025"}'
   ```

2. Use token:
   ```bash
   curl http://localhost:8888/api/v1/tasks \
     -H "Authorization: Bearer {token}"
   ```

### Session Management
- Session timeout: 1 hour
- Max concurrent sessions: 5
- Auto-refresh enabled

## Troubleshooting

### Common Issues
1. Connection Refused
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Check Flask server
   ps aux | grep run_server.py
   ```

2. Authentication Failed
   ```bash
   # Reset admin password
   python scripts/reset_admin.py
   ```

3. Metrics Not Loading
   ```bash
   # Clear metrics cache
   redis-cli del metrics:*
   ```

## Security Notes
1. Change default credentials immediately
2. Use HTTPS in production
3. Enable rate limiting
4. Monitor access logs

## Support
For technical support:
- Email: support@gitbridge.erudite.com
- Slack: #gbp-support
- Documentation: http://localhost:8888/docs 