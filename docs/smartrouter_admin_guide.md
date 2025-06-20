# GitBridge SmartRouter Administrator Guide

**Task: P20P7S5D - Documentation & Training**

**Version:** 2.0  
**Date:** 2025-06-19  
**Author:** GitBridge Development Team

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [Routing Strategies](#routing-strategies)
6. [Monitoring & Observability](#monitoring--observability)
7. [Production Hardening](#production-hardening)
8. [Troubleshooting](#troubleshooting)
9. [Performance Optimization](#performance-optimization)
10. [API Reference](#api-reference)
11. [Best Practices](#best-practices)

---

## Overview

The GitBridge SmartRouter is an intelligent AI provider arbitration system that automatically routes requests between multiple AI providers (OpenAI, Grok) based on cost, performance, availability, and task requirements.

### Key Features

- **Multi-Strategy Routing**: Cost-optimized, performance-optimized, availability-optimized, hybrid, and adaptive routing
- **Real-Time Health Monitoring**: Continuous provider health checks with automatic failover
- **Performance Analytics**: Comprehensive metrics and performance windows with decay curves
- **Circuit Breaker Pattern**: Automatic failure detection and recovery mechanisms
- **Production Hardening**: Rate limiting, stress testing, and monitoring dashboards
- **Prometheus Integration**: Standard metrics export for monitoring systems

### System Requirements

- Python 3.13.3+
- OpenAI API key
- Grok API key (optional)
- 4GB RAM minimum (8GB recommended)
- Network connectivity to AI providers

---

## Architecture

### Core Components

```
SmartRouter
├── Provider Clients
│   ├── OpenAIClient
│   └── GrokClient
├── Routing Engine
│   ├── Strategy Selector
│   ├── Performance Analyzer
│   └── Decision Logger
├── Health Monitor
│   ├── Provider Health Checks
│   └── Circuit Breaker
├── Metrics Collector
│   ├── Performance Windows
│   ├── Cost Tracker
│   └── Analytics Engine
└── Monitoring Dashboard
    ├── Flask Web UI
    ├── Prometheus Metrics
    └── Real-time Visualizations
```

### Data Flow

1. **Request Reception**: Incoming requests are received by the SmartRouter
2. **Health Check**: Provider health status is verified
3. **Strategy Selection**: Routing strategy determines provider selection criteria
4. **Provider Selection**: Optimal provider is selected based on strategy and metrics
5. **Request Execution**: Request is sent to selected provider
6. **Response Processing**: Response is processed and metrics updated
7. **Failover Handling**: If primary provider fails, automatic failover occurs
8. **Metrics Update**: Performance metrics and decision logs are updated

---

## Installation & Setup

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd GitBridgev1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. API Key Configuration

Create a `.env` file in the project root:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ORG_ID=your_organization_id_here

# Grok Configuration
GROK_API_KEY=your_grok_api_key_here
GROK_ORG_ID=your_grok_org_id_here

# SmartRouter Configuration
SMARTROUTER_STRATEGY=adaptive
SMARTROUTER_COST_WEIGHT=0.4
SMARTROUTER_PERFORMANCE_WEIGHT=0.3
SMARTROUTER_AVAILABILITY_WEIGHT=0.3
```

### 3. Directory Structure

```
GitBridgev1/
├── smart_router/
│   ├── smart_router.py          # Core SmartRouter implementation
│   └── __init__.py
├── clients/
│   ├── openai_client.py         # OpenAI client
│   ├── grok_client.py           # Grok client
│   └── __init__.py
├── production/
│   ├── circuit_breaker.py       # Circuit breaker implementation
│   └── stress_test.py           # Stress testing framework
├── monitoring/
│   ├── dashboard.py             # Flask monitoring dashboard
│   └── templates/
├── scripts/
│   ├── latency_visualizer.py    # Real-time latency visualization
│   └── demo_smartrouter_flow.sh # Demo script
├── docs/
│   └── smartrouter_admin_guide.md
├── logs/                        # Generated log files
├── tests/                       # Test files
└── requirements.txt
```

---

## Configuration

### SmartRouter Configuration

```python
from smart_router.smart_router import SmartRouter, RoutingStrategy

# Basic configuration
router = SmartRouter(
    strategy=RoutingStrategy.ADAPTIVE,
    cost_weight=0.4,
    performance_weight=0.3,
    availability_weight=0.3,
    max_retries=3,
    performance_window_size=100,
    decay_factor=0.95
)
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | None | Yes |
| `GROK_API_KEY` | Grok API key | None | No |
| `SMARTROUTER_STRATEGY` | Default routing strategy | `adaptive` | No |
| `SMARTROUTER_COST_WEIGHT` | Cost optimization weight | `0.4` | No |
| `SMARTROUTER_PERFORMANCE_WEIGHT` | Performance weight | `0.3` | No |
| `SMARTROUTER_AVAILABILITY_WEIGHT` | Availability weight | `0.3` | No |

### Circuit Breaker Configuration

```python
from production.circuit_breaker import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=5,        # Failures before opening circuit
    recovery_timeout=60.0,      # Seconds to wait before recovery
    success_threshold=2,        # Successes to close circuit
    timeout=30.0,               # Request timeout
    max_failures_per_minute=10  # Rate limiting
)
```

---

## Routing Strategies

### 1. Adaptive (Recommended)

**Description**: Dynamically adjusts routing based on real-time performance data using decay curves and retry effectiveness scoring.

**Best For**: Production environments with variable load and provider performance.

**Configuration**:
```python
router = SmartRouter(strategy=RoutingStrategy.ADAPTIVE)
```

**Features**:
- Dynamic weighting based on recent performance
- Retry effectiveness scoring
- Performance window analysis
- Automatic strategy adjustment

### 2. Cost Optimized

**Description**: Prioritizes cost efficiency over performance and availability.

**Best For**: Budget-conscious applications with predictable load.

**Configuration**:
```python
router = SmartRouter(strategy=RoutingStrategy.COST_OPTIMIZED)
```

### 3. Performance Optimized

**Description**: Prioritizes response time and latency over cost.

**Best For**: Real-time applications requiring fast responses.

**Configuration**:
```python
router = SmartRouter(strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED)
```

### 4. Availability Optimized

**Description**: Prioritizes provider availability and reliability.

**Best For**: Critical applications requiring high uptime.

**Configuration**:
```python
router = SmartRouter(strategy=RoutingStrategy.AVAILABILITY_OPTIMIZED)
```

### 5. Hybrid

**Description**: Combines multiple factors with configurable weights.

**Best For**: Custom requirements balancing multiple priorities.

**Configuration**:
```python
router = SmartRouter(
    strategy=RoutingStrategy.HYBRID,
    cost_weight=0.4,
    performance_weight=0.3,
    availability_weight=0.3
)
```

---

## Monitoring & Observability

### 1. Web Dashboard

Start the monitoring dashboard:

```bash
python monitoring/dashboard.py --host 0.0.0.0 --port 5000
```

**Features**:
- Real-time performance metrics
- Provider health status
- Routing decision visualization
- Budget analysis
- Interactive controls

**Access URLs**:
- Dashboard: `http://localhost:5000`
- Health Check: `http://localhost:5000/health`
- Prometheus Metrics: `http://localhost:5000/metrics`

### 2. Prometheus Metrics

The dashboard exports standard Prometheus metrics:

```prometheus
# Request metrics
smartrouter_requests_total{provider="openai",status="success"}
smartrouter_request_duration_seconds{provider="openai"}

# Provider health
smartrouter_provider_health{provider="openai"}

# Routing decisions
smartrouter_routing_decisions_total{strategy="adaptive",provider="openai"}

# Cost tracking
smartrouter_cost_total{provider="openai"}
smartrouter_tokens_total{provider="openai"}
```

### 3. Real-time Latency Visualization

```bash
python scripts/latency_visualizer.py --strategy adaptive
```

**Features**:
- Live latency trend graphs
- Provider performance comparison
- Adaptive score tracking
- Routing decision history

### 4. Log Files

Log files are stored in the `logs/` directory:

- `smart_router.log`: Main SmartRouter logs
- `router_decisions.jsonl`: Routing decision history
- `router_metrics.json`: Performance metrics
- `token_usage.log`: Token usage tracking

---

## Production Hardening

### 1. Circuit Breaker Pattern

The SmartRouter includes automatic circuit breaker functionality:

```python
from production.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig

# Configure circuit breaker
config = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=60.0,
    success_threshold=2,
    timeout=30.0
)

# Get circuit breaker
cb = get_circuit_breaker("provider_name", config)

# Use with function calls
result = cb.call(provider_function, *args, **kwargs)
```

### 2. Stress Testing

Run comprehensive stress tests:

```bash
# Basic load test
python production/stress_test.py --test-type basic --duration 60 --users 10

# High load test
python production/stress_test.py --test-type high --duration 120 --users 50

# Full test suite
python production/stress_test.py --test-type full
```

**Test Types**:
- `basic`: 10 concurrent users, 5 RPS
- `high`: 50 concurrent users, 20 RPS
- `stress`: 100 concurrent users, 50 RPS
- `failure`: Simulated failure scenarios
- `full`: Complete test suite

### 3. Rate Limiting

Configure rate limiting in your deployment:

```python
# Example with Flask-Limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

### 4. Health Checks

Implement health check endpoints:

```python
@app.route('/health')
def health():
    status = router.get_provider_status()
    healthy_providers = sum(
        1 for provider_data in status['providers'].values()
        if provider_data['available']
    )
    
    if healthy_providers > 0:
        return jsonify({'status': 'healthy'})
    else:
        return jsonify({'status': 'unhealthy'}), 503
```

---

## Troubleshooting

### Common Issues

#### 1. Provider Initialization Failures

**Symptoms**: "No AI providers could be initialized" error

**Causes**:
- Missing API keys
- Invalid API keys
- Network connectivity issues

**Solutions**:
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $GROK_API_KEY

# Test API connectivity
python -c "import openai; openai.api_key='your_key'; print(openai.Model.list())"
```

#### 2. High Failure Rates

**Symptoms**: Circuit breaker opening frequently

**Causes**:
- Provider API limits exceeded
- Network timeouts
- Invalid request parameters

**Solutions**:
```python
# Check provider health
status = router.get_provider_status()
print(json.dumps(status, indent=2))

# Adjust circuit breaker settings
config = CircuitBreakerConfig(
    failure_threshold=10,  # Increase threshold
    recovery_timeout=120.0,  # Increase recovery time
    timeout=60.0  # Increase request timeout
)
```

#### 3. Performance Degradation

**Symptoms**: High latency, low throughput

**Causes**:
- Provider overload
- Network congestion
- Inefficient routing strategy

**Solutions**:
```python
# Switch to performance-optimized strategy
router.set_strategy(RoutingStrategy.PERFORMANCE_OPTIMIZED)

# Check performance metrics
metrics = router.get_enhanced_metrics()
print(f"Average latency: {metrics['overall_performance']['avg_latency']:.2f}s")
```

#### 4. Cost Overruns

**Symptoms**: Unexpected high costs

**Causes**:
- Inefficient token usage
- Wrong provider selection
- Retry loops

**Solutions**:
```python
# Switch to cost-optimized strategy
router.set_strategy(RoutingStrategy.COST_OPTIMIZED)

# Check cost analysis
analysis = dashboard.get_budget_analysis()
print(f"Total cost: ${analysis['total_cost']:.4f}")
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('smart_router').setLevel(logging.DEBUG)
```

### Performance Profiling

Use the built-in performance profiler:

```python
# Enable performance profiling
router.enable_profiling()

# Run requests
for i in range(100):
    response = router.route_request("Test request")

# Get profiling results
profile_data = router.get_profiling_data()
print(json.dumps(profile_data, indent=2))
```

---

## Performance Optimization

### 1. Strategy Selection

**For High-Throughput Applications**:
```python
router = SmartRouter(strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED)
```

**For Cost-Sensitive Applications**:
```python
router = SmartRouter(strategy=RoutingStrategy.COST_OPTIMIZED)
```

**For Production Environments**:
```python
router = SmartRouter(strategy=RoutingStrategy.ADAPTIVE)
```

### 2. Performance Window Tuning

```python
router = SmartRouter(
    performance_window_size=200,  # Larger window for stability
    decay_factor=0.98  # Slower decay for smoother transitions
)
```

### 3. Circuit Breaker Optimization

```python
config = CircuitBreakerConfig(
    failure_threshold=3,  # Faster failure detection
    recovery_timeout=30.0,  # Faster recovery
    success_threshold=1  # Single success to close circuit
)
```

### 4. Caching Strategies

Implement response caching for repeated requests:

```python
import hashlib
import json
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_route_request(prompt_hash, task_type, max_tokens):
    return router.route_request(prompt, task_type, max_tokens)

def route_with_caching(prompt, task_type, max_tokens):
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    return cached_route_request(prompt_hash, task_type, max_tokens)
```

---

## API Reference

### SmartRouter Class

#### Constructor

```python
SmartRouter(
    strategy: RoutingStrategy = RoutingStrategy.ADAPTIVE,
    cost_weight: float = 0.4,
    performance_weight: float = 0.3,
    availability_weight: float = 0.3,
    max_retries: int = 3,
    performance_window_size: int = 100,
    decay_factor: float = 0.95
)
```

#### Methods

##### `route_request()`

Route a request to the optimal provider.

```python
response = router.route_request(
    prompt: str,
    task_type: str = "general",
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    system_message: Optional[str] = None,
    force_provider: Optional[ProviderType] = None
) -> SmartRouterResponse
```

##### `get_enhanced_metrics()`

Get comprehensive performance metrics.

```python
metrics = router.get_enhanced_metrics() -> Dict[str, Any]
```

##### `get_routing_analytics()`

Get routing decision analytics.

```python
analytics = router.get_routing_analytics() -> Dict[str, Any]
```

##### `set_strategy()`

Change routing strategy dynamically.

```python
router.set_strategy(RoutingStrategy.ADAPTIVE)
```

##### `set_weights()`

Update routing weights dynamically.

```python
router.set_weights(cost_weight=0.5, performance_weight=0.3, availability_weight=0.2)
```

##### `reset_metrics()`

Reset all performance metrics.

```python
router.reset_metrics()
```

### Response Objects

#### SmartRouterResponse

```python
@dataclass
class SmartRouterResponse:
    content: str
    provider: ProviderType
    model: str
    usage: Dict[str, Any]
    response_time: float
    timestamp: str
    routing_decision: RoutingDecision
    metadata: Dict[str, Any]
```

#### RoutingDecision

```python
@dataclass
class RoutingDecision:
    timestamp: str
    strategy: RoutingStrategy
    selected_provider: ProviderType
    alternative_provider: Optional[ProviderType]
    reasoning: str
    confidence: float
    task_type: str
    estimated_cost: float
    estimated_latency: float
    adaptive_factors: Dict[str, float]
```

---

## Best Practices

### 1. Strategy Selection

- **Use Adaptive strategy** for production environments
- **Use Cost Optimized** for budget-conscious applications
- **Use Performance Optimized** for real-time applications
- **Use Availability Optimized** for critical systems

### 2. Monitoring

- **Set up Prometheus monitoring** for production deployments
- **Monitor circuit breaker states** regularly
- **Track cost metrics** to prevent overruns
- **Set up alerts** for high failure rates

### 3. Configuration

- **Use environment variables** for sensitive configuration
- **Test circuit breaker settings** in staging environments
- **Adjust performance windows** based on load patterns
- **Monitor and tune weights** based on actual usage

### 4. Error Handling

- **Implement proper exception handling** in your application
- **Use circuit breakers** to prevent cascade failures
- **Monitor retry patterns** to identify issues
- **Set up dead letter queues** for failed requests

### 5. Performance

- **Use connection pooling** for HTTP clients
- **Implement request caching** for repeated queries
- **Monitor memory usage** and implement cleanup
- **Use async/await** for high-throughput applications

### 6. Security

- **Rotate API keys** regularly
- **Use least privilege** for API access
- **Monitor API usage** for anomalies
- **Implement rate limiting** to prevent abuse

### 7. Deployment

- **Use containerization** (Docker) for consistent deployments
- **Implement health checks** for load balancers
- **Use blue-green deployments** for zero-downtime updates
- **Monitor resource usage** and scale accordingly

---

## Support & Maintenance

### Log Rotation

Configure log rotation to prevent disk space issues:

```bash
# Add to /etc/logrotate.d/smartrouter
/path/to/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
}
```

### Backup Strategy

Regularly backup configuration and metrics:

```bash
#!/bin/bash
# backup_smartrouter.sh
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "smartrouter_backup_$DATE.tar.gz" \
    logs/ \
    .env \
    monitoring/templates/
```

### Updates

Keep the SmartRouter updated:

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Test after updates
python -m pytest tests/

# Deploy with zero downtime
# (Use blue-green deployment strategy)
```

---

## Conclusion

The GitBridge SmartRouter provides a robust, scalable solution for AI provider arbitration. By following this guide, you can deploy and maintain a production-ready SmartRouter system that optimizes cost, performance, and availability while providing comprehensive monitoring and observability.

For additional support, refer to the project documentation or contact the development team.

---

**Document Version:** 2.0  
**Last Updated:** 2025-06-19  
**Next Review:** 2025-07-19 