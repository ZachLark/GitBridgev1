# GBP15 AI Router Architecture

## Overview
The GBP15 AI Router provides enhanced task routing capabilities with debug layer, CLI hooks, and MASLite integration placeholders. This document outlines the architecture and specifications for these enhancements.

## Debug Layer
### Error Codes
- `ERR_ROUTING_001`: Agent Not Found
- `ERR_ROUTING_002`: Invalid Task ID
- `ERR_ROUTING_003`: Invalid Agent ID
- `ERR_ROUTING_004`: Routing Failed
- `ERR_ROUTING_005`: Agent Capacity Exceeded
- `ERR_ROUTING_006`: Agent Status Invalid
- `ERR_ROUTING_007`: Task Already Assigned
- `ERR_ROUTING_008`: Task Queue Full
- `ERR_ROUTING_009`: Agent Not Responding
- `ERR_ROUTING_010`: MASLite Integration Error

### Performance Optimizations
- TTL Cache for task tracking (1000 tasks, 1-hour TTL)
- Compressed JSON logging with rotation
- Latency tracking for all operations
- Early consensus calculation
- Efficient error response handling

### Retry Logic
- Maximum retries: 3
- Retry delay: 200ms
- Exponential backoff: Optional (configurable)

### Logging
- Location: `logs/ai_router_log.json`
- Format: Compressed JSON structured logging
- Fields:
  ```json
  {
    "operation": "<operation_type>",
    "task_id": "<task_id>",
    "agent": "<agent_id>",
    "timestamp": "<iso_timestamp>",
    "error_code": "<error_code>",
    "latency_ms": "<latency_ms>"
  }
  ```
- Log rotation:
  - Max file size: 10MB
  - Backup count: 5
  - Compression: Enabled

## Performance Metrics
### Target Latencies
- Task routing: <100ms
- Agent registration: <50ms
- Status updates: <30ms
- CLI operations: <150ms
- Overall system: <350ms (optimized from 500ms)

### Monitoring
- Operation-specific latency tracking
- Agent performance metrics
- Task processing statistics
- Error rate monitoring
- Queue depth tracking

## CLI Hooks
### Commands
1. Route Task
   ```bash
   gbp --route <task_id> <agent>
   ```
   Example:
   ```bash
   gbp --route task_001 agent1
   ```

2. Get Agent Status
   ```bash
   gbp --status <agent>
   ```
   Example:
   ```bash
   gbp --status agent1
   ```

3. Register Agent
   ```bash
   gbp --register <agent> <capacity>
   ```
   Example:
   ```bash
   gbp --register agent1 10
   ```

4. Get Metrics
   ```bash
   gbp --metrics
   ```

### Output Format
All CLI commands return JSON-formatted output using orjson for improved performance:
```json
{
  "task_id": "task_001",
  "agent": "agent1",
  "status": "routed",
  "capacity_remaining": 9,
  "total_tasks_processed": 15,
  "latency_ms": 45
}
```

## Agent Management
### Registration
- Agents must register before accepting tasks
- Default capacity: 10 concurrent tasks
- Status tracking: active/inactive
- Performance metrics tracking
- Last active timestamp

### Capacity Management
- Dynamic capacity updates
- Task counting and limits
- Automatic task cleanup
- TTL-based cache eviction
- Warning threshold monitoring

## Error Handling
### Validation
- Task ID validation
- Agent ID validation
- Capacity checks
- Status validation
- Task duplication checks

### Recovery
- Retry mechanism for capacity issues
- Error logging with latency
- Status preservation
- Automatic cleanup
- Rate limiting

## Integration Points
### Task Generator
- Receives routed tasks
- Validates task parameters
- Manages task lifecycle
- Performance tracking

### MAS Core
- Agent registration
- Task distribution
- Status updates
- Protocol compliance

## Example Usage
### Task Routing with Metrics
```python
router = AIRouter()
await router.register_agent("agent1", capacity=10)
result = await router.route_task("task_001", "agent1")
print(f"Routing latency: {result['latency_ms']}ms")
```

### Status Check with Performance
```python
status = await router.get_agent_status("agent1")
print(f"Agent Status: {status['status']}")
print(f"Tasks: {len(status['tasks'])}/{status['capacity']}")
print(f"Total processed: {status['total_tasks_processed']}")
print(f"Response time: {status['latency_ms']}ms")
```

### MASLite Integration
```python
result = await router.route_to_maslite("task_001", "agent1")
assert result["protocol_version"] == "2.1"
```

## Performance Considerations
- Lock-based concurrency control
- TTL cache for task tracking
- Compressed logging
- Early consensus calculation
- Efficient error handling
- Latency monitoring
- Rate limiting

## Future Enhancements (GBP18)
1. Full MASLite integration
2. Advanced routing algorithms
3. Load balancing
4. Agent health monitoring
5. Task prioritization
6. Predictive scaling
7. Real-time analytics 