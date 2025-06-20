# GitBridge SmartRouter

**Task**: P20P7S3 - SmartRouter Call Structure and Timeout Arbitration Logic  
**Date**: 2025-06-19  
**Status**: Preliminary Scaffolding (P20P6 must be complete before full implementation)  

---

## 🎯 **Overview**

SmartRouter is GitBridge's intelligent request routing system that arbitrates between multiple AI providers (GPT-4o and Grok 3) based on performance, cost, and availability metrics. This component ensures optimal AI service selection for each request.

---

## 🔄 **Call Structure**

### **Request Flow**
```
1. GitHub Webhook → SmartRouter
2. SmartRouter → Provider Selection Logic
3. Selected Provider → AI Service (GPT-4o or Grok 3)
4. AI Response → SmartRouter
5. SmartRouter → Cursor Integration
```

### **Provider Selection Criteria**
```python
class ProviderSelectionCriteria:
    cost_per_token: float          # Cost optimization
    response_time_threshold: float # Performance threshold
    availability_score: float      # Uptime percentage
    model_capability: str          # Model-specific features
    current_load: float           # Current provider load
```

### **MAS Lite Protocol v2.1 Routing Fields**
```python
class SmartRouterRequest:
    event_id: str                    # Original event identifier
    source: EventSource              # Event source (github, gitlab, etc.)
    event_type: EventType            # Event type (pr, push, issue, etc.)
    requested_output: RequestedOutput # Desired output format
    routing_preferences: dict        # User/provider preferences
    timeout_seconds: int             # Request timeout
    fallback_provider: str           # Fallback provider
    cost_budget: float               # Maximum cost per request
    performance_requirement: str     # Speed vs quality preference
```

---

## ⏱️ **Timeout Arbitration Logic**

### **Multi-Tier Timeout Strategy**
```python
class TimeoutArbitration:
    def __init__(self):
        self.primary_timeout = 5.0    # Primary provider timeout
        self.fallback_timeout = 3.0   # Fallback provider timeout
        self.total_timeout = 8.0      # Maximum total time
        
    def arbitrate_request(self, request: SmartRouterRequest) -> AIResponse:
        # 1. Try primary provider
        try:
            response = self.call_primary_provider(request, self.primary_timeout)
            return response
        except TimeoutError:
            # 2. Try fallback provider
            try:
                response = self.call_fallback_provider(request, self.fallback_timeout)
                return response
            except TimeoutError:
                # 3. Return cached response or error
                return self.get_cached_response(request)
```

### **Provider-Specific Timeouts**
```python
PROVIDER_TIMEOUTS = {
    "gpt-4o": {
        "primary": 5.0,
        "fallback": 3.0,
        "retry_attempts": 2
    },
    "grok-3": {
        "primary": 4.0,
        "fallback": 2.5,
        "retry_attempts": 3
    }
}
```

### **Load Balancing Logic**
```python
class LoadBalancer:
    def select_provider(self, request: SmartRouterRequest) -> str:
        # Calculate provider scores
        gpt4o_score = self.calculate_provider_score("gpt-4o", request)
        grok3_score = self.calculate_provider_score("grok-3", request)
        
        # Select best provider
        if gpt4o_score > grok3_score:
            return "gpt-4o"
        else:
            return "grok-3"
    
    def calculate_provider_score(self, provider: str, request: SmartRouterRequest) -> float:
        # Weighted scoring based on multiple factors
        cost_score = self.get_cost_score(provider, request)
        performance_score = self.get_performance_score(provider)
        availability_score = self.get_availability_score(provider)
        
        return (cost_score * 0.3 + 
                performance_score * 0.4 + 
                availability_score * 0.3)
```

---

## 📊 **Performance Monitoring**

### **Metrics Collection**
```python
class SmartRouterMetrics:
    def __init__(self):
        self.provider_response_times = {}
        self.provider_success_rates = {}
        self.provider_costs = {}
        self.routing_decisions = {}
    
    def record_request(self, provider: str, response_time: float, 
                      success: bool, cost: float):
        """Record metrics for each request."""
        # Update response times
        if provider not in self.provider_response_times:
            self.provider_response_times[provider] = []
        self.provider_response_times[provider].append(response_time)
        
        # Update success rates
        if provider not in self.provider_success_rates:
            self.provider_success_rates[provider] = {"success": 0, "total": 0}
        self.provider_success_rates[provider]["total"] += 1
        if success:
            self.provider_success_rates[provider]["success"] += 1
        
        # Update costs
        if provider not in self.provider_costs:
            self.provider_costs[provider] = []
        self.provider_costs[provider].append(cost)
```

### **Health Checks**
```python
class ProviderHealthCheck:
    def check_provider_health(self, provider: str) -> dict:
        """Check provider health and availability."""
        try:
            # Test provider with simple request
            response = self.test_provider(provider, timeout=2.0)
            return {
                "provider": provider,
                "status": "healthy",
                "response_time": response.response_time,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "provider": provider,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
```

---

## 🔧 **Configuration**

### **SmartRouter Settings**
```python
SMARTROUTER_CONFIG = {
    "enabled": True,
    "default_provider": "gpt-4o",
    "fallback_provider": "grok-3",
    "timeout_strategy": "tiered",
    "load_balancing": True,
    "cost_optimization": True,
    "performance_threshold": 3.0,
    "health_check_interval": 300,  # 5 minutes
    "metrics_retention_days": 30
}
```

### **Provider Configuration**
```python
PROVIDER_CONFIG = {
    "gpt-4o": {
        "api_endpoint": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
        "max_tokens": 1000,
        "temperature": 0.7,
        "cost_per_1k_tokens": 0.005,
        "rate_limit": 3500  # requests per minute
    },
    "grok-3": {
        "api_endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama3-70b-8192",
        "max_tokens": 1000,
        "temperature": 0.7,
        "cost_per_1k_tokens": 0.002,
        "rate_limit": 5000  # requests per minute
    }
}
```

---

## 🚨 **Error Handling**

### **Fallback Strategies**
```python
class FallbackStrategy:
    def handle_provider_failure(self, failed_provider: str, 
                               request: SmartRouterRequest) -> AIResponse:
        """Handle provider failures with intelligent fallback."""
        
        # 1. Try alternative provider
        alternative_provider = self.get_alternative_provider(failed_provider)
        try:
            return self.call_provider(alternative_provider, request)
        except Exception as e:
            # 2. Use cached response
            cached_response = self.get_cached_response(request)
            if cached_response:
                return cached_response
            
            # 3. Return error response
            return self.create_error_response(request, str(e))
```

### **Circuit Breaker Pattern**
```python
class CircuitBreaker:
    def __init__(self, provider: str):
        self.provider = provider
        self.failure_count = 0
        self.failure_threshold = 5
        self.timeout = 60  # seconds
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self.should_attempt_reset():
                self.state = "half-open"
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker open for {self.provider}")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

---

## 📈 **Future Implementation Plan**

### **Phase 1: Basic Routing (P20P7S1)**
- [ ] Implement basic provider selection
- [ ] Add timeout handling
- [ ] Create health checks
- [ ] Add metrics collection

### **Phase 2: Advanced Features (P20P7S2)**
- [ ] Implement load balancing
- [ ] Add cost optimization
- [ ] Create circuit breaker pattern
- [ ] Add caching layer

### **Phase 3: Optimization (P20P7S3)**
- [ ] Implement A/B testing
- [ ] Add machine learning routing
- [ ] Create performance analytics
- [ ] Add predictive routing

---

## ⚠️ **Important Notes**

### **Dependencies**
- **P20P6 (Grok 3 Integration)** must be complete before full implementation
- Requires working GPT-4o integration (P20P2S1)
- Requires webhook system (P20P3S1)
- Requires Cursor integration (P20P4)

### **Current Status**
- ✅ **Scaffolding**: Basic structure and documentation
- ✅ **Design**: Call structure and timeout logic defined
- 🚫 **Implementation**: Waiting for P20P6 completion
- 🚫 **Testing**: Cannot test without Grok integration

### **Next Steps**
1. Complete P20P6 (Grok 3 Integration)
2. Implement SmartRouter core functionality
3. Add provider selection logic
4. Implement timeout arbitration
5. Add monitoring and metrics
6. Test end-to-end integration

---

*This scaffolding provides the foundation for SmartRouter implementation once Grok 3 integration (P20P6) is complete.* 