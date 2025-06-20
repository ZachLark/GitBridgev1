#!/usr/bin/env python3
"""
GitBridge SmartRouter Core Implementation
Phase: GBP20
Part: P20P7
Step: P20P7S3
Task: P20P7S3T1 - SmartRouter Core Implementation

Intelligent routing system for AI provider selection based on:
- Cost optimization
- Performance metrics
- Availability monitoring
- Load balancing

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [Corrected P20P7 Schema]
"""

import os
import json
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import statistics

from clients.openai_client import OpenAIClient, OpenAIResponse
from clients.grok_client import GrokClient, GrokResponse
from utils.token_usage_logger import log_token_usage

# Configure logging with P20P7 schema
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [P20P7S3] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/smartrouter.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ProviderType(Enum):
    """Available AI providers."""
    OPENAI = "openai"
    GROK = "grok"

class RoutingStrategy(Enum):
    """Routing strategies for provider selection."""
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    AVAILABILITY_OPTIMIZED = "availability_optimized"
    HYBRID = "hybrid"
    ROUND_ROBIN = "round_robin"

@dataclass
class ProviderMetrics:
    """Metrics for a single provider."""
    avg_latency: float = 0.0
    success_rate: float = 1.0
    availability_score: float = 1.0
    total_requests: int = 0
    failed_requests: int = 0
    avg_cost_per_1k_tokens: float = 0.01
    last_request_time: Optional[datetime] = None
    is_healthy: bool = True
    consecutive_failures: int = 0
    max_consecutive_failures: int = 3

@dataclass
class RoutingDecision:
    """Decision made by the router."""
    provider: ProviderType
    strategy: RoutingStrategy
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    metrics_used: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SmartRouterResponse:
    """Response from SmartRouter."""
    content: str
    provider: ProviderType
    response_time: float
    usage: Dict[str, Any]
    routing_decision: RoutingDecision
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RetryScoreboard:
    """Track retry performance and route degradations."""
    total_retries: int = 0
    successful_retries: int = 0
    failed_retries: int = 0
    route_degradations: int = 0
    last_retry_time: Optional[datetime] = None
    retry_history: List[Dict[str, Any]] = field(default_factory=list)

class SmartRouter:
    """
    Intelligent routing system for AI provider selection.
    
    Phase: GBP20
    Part: P20P7
    Step: P20P7S3
    Task: P20P7S3T1 - Core Implementation
    
    Features:
    - Multi-strategy routing (cost, performance, availability, hybrid)
    - Real-time metrics tracking
    - Automatic failover
    - Load balancing
    - Health monitoring
    - Retry scoreboard tracking
    - Routing decision logging
    """
    
    def __init__(
        self,
        strategy: RoutingStrategy = RoutingStrategy.HYBRID,
        cost_weight: float = 0.4,
        performance_weight: float = 0.3,
        availability_weight: float = 0.3,
        metrics_window: int = 100,
        health_check_interval: int = 60
    ):
        """
        Initialize SmartRouter.
        
        Args:
            strategy: Routing strategy to use
            cost_weight: Weight for cost optimization (0.0-1.0)
            performance_weight: Weight for performance optimization (0.0-1.0)
            availability_weight: Weight for availability optimization (0.0-1.0)
            metrics_window: Number of recent requests to track
            health_check_interval: Health check interval in seconds
        """
        self.strategy = strategy
        self.cost_weight = cost_weight
        self.performance_weight = performance_weight
        self.availability_weight = availability_weight
        self.metrics_window = metrics_window
        
        # Initialize providers
        self.providers = {
            ProviderType.OPENAI: OpenAIClient(),
            ProviderType.GROK: GrokClient()
        }
        
        # Initialize metrics
        self.provider_metrics = {
            ProviderType.OPENAI: ProviderMetrics(),
            ProviderType.GROK: ProviderMetrics()
        }
        
        # Request history for metrics calculation
        self.request_history = {
            ProviderType.OPENAI: deque(maxlen=metrics_window),
            ProviderType.GROK: deque(maxlen=metrics_window)
        }
        
        # Routing decision history
        self.routing_history = deque(maxlen=1000)
        
        # Retry scoreboard
        self.retry_scoreboard = RetryScoreboard()
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Health check thread
        self._health_check_thread = None
        self._stop_health_check = threading.Event()
        self._start_health_check_thread(health_check_interval)
        
        # Feedback loop
        self._feedback_history = {}
        self._scoring_trends = {}
        
        logger.info(f"[P20P7S3T1] SmartRouter initialized with strategy: {strategy.value}")
        logger.info(f"[P20P7S3T1] Weights - Cost: {cost_weight}, Performance: {performance_weight}, Availability: {availability_weight}")
        
    def _start_health_check_thread(self, interval: int) -> None:
        """Start background health check thread."""
        def health_check_loop():
            while not self._stop_health_check.wait(interval):
                try:
                    self._perform_health_checks()
                except Exception as e:
                    logger.error(f"[P20P7S3T1] Health check error: {e}")
                    
        self._health_check_thread = threading.Thread(target=health_check_loop, daemon=True)
        self._health_check_thread.start()
        logger.info(f"[P20P7S3T1] Health check thread started (interval: {interval}s)")
        
    def _perform_health_checks(self) -> None:
        """Perform health checks on all providers."""
        with self._lock:
            for provider_type, client in self.providers.items():
                try:
                    start_time = time.time()
                    if provider_type == ProviderType.OPENAI:
                        response = client.test_connection()
                    else:
                        response = client.test_connection()
                    
                    response_time = time.time() - start_time
                    
                    # Update metrics
                    metrics = self.provider_metrics[provider_type]
                    metrics.is_healthy = True
                    metrics.consecutive_failures = 0
                    metrics.last_request_time = datetime.now()
                    
                    # Update latency (rolling average)
                    if len(self.request_history[provider_type]) > 0:
                        latencies = [req['latency'] for req in self.request_history[provider_type]]
                        metrics.avg_latency = statistics.mean(latencies)
                    else:
                        metrics.avg_latency = response_time
                        
                    logger.debug(f"[P20P7S3T1] Health check passed for {provider_type.value} (latency: {response_time:.2f}s)")
                    
                except Exception as e:
                    logger.warning(f"[P20P7S3T1] Health check failed for {provider_type.value}: {e}")
                    metrics = self.provider_metrics[provider_type]
                    metrics.consecutive_failures += 1
                    metrics.is_healthy = metrics.consecutive_failures < metrics.max_consecutive_failures
                    
    def _log_routing_decision(self, decision: RoutingDecision, response_time: float, 
                            usage: Dict[str, Any], fallback_used: bool = False) -> None:
        """
        Log routing decision to JSONL file.
        
        Args:
            decision: The routing decision made
            response_time: Response time in seconds
            usage: Token usage data
            fallback_used: Whether this was a failover decision
        """
        try:
            decision_log = {
                'timestamp': decision.timestamp.isoformat(),
                'strategy': decision.strategy.value,
                'provider_selected': decision.provider.value,
                'latency': response_time,
                'cost': usage.get('total_tokens', 0) * 0.01 / 1000 if decision.provider == ProviderType.OPENAI else usage.get('total_tokens', 0) * 0.005 / 1000,
                'fallback_used': fallback_used,
                'reason_for_selection': decision.reasoning,
                'confidence': decision.confidence,
                'tokens_used': usage.get('total_tokens', 0),
                'metrics_used': decision.metrics_used
            }
            
            # Ensure logs directory exists
            os.makedirs('logs', exist_ok=True)
            
            # Write to JSONL file
            with open('logs/routing_decision.jsonl', 'a') as f:
                json.dump(decision_log, f)
                f.write('\n')
                
            logger.debug(f"[P20P7S3T1] Routing decision logged: {decision.provider.value} (confidence: {decision.confidence:.2f})")
            
        except Exception as e:
            logger.error(f"[P20P7S3T1] Failed to log routing decision: {e}")
            
    def _update_retry_scoreboard(self, success: bool, original_provider: ProviderType, 
                                final_provider: ProviderType) -> None:
        """
        Update retry scoreboard with retry attempt results.
        
        Args:
            success: Whether the retry was successful
            original_provider: Provider that failed initially
            final_provider: Provider that succeeded (if any)
        """
        with self._lock:
            self.retry_scoreboard.total_retries += 1
            self.retry_scoreboard.last_retry_time = datetime.now()
            
            if success:
                self.retry_scoreboard.successful_retries += 1
                if original_provider != final_provider:
                    self.retry_scoreboard.route_degradations += 1
            else:
                self.retry_scoreboard.failed_retries += 1
                
            # Add to retry history
            retry_record = {
                'timestamp': datetime.now().isoformat(),
                'success': success,
                'original_provider': original_provider.value,
                'final_provider': final_provider.value if success else None,
                'route_degradation': original_provider != final_provider if success else False
            }
            self.retry_scoreboard.retry_history.append(retry_record)
            
            # Keep only last 100 retry records
            if len(self.retry_scoreboard.retry_history) > 100:
                self.retry_scoreboard.retry_history = self.retry_scoreboard.retry_history[-100:]
                
            logger.info(f"[P20P7S3T1] Retry scoreboard updated - Success: {success}, "
                       f"Total: {self.retry_scoreboard.total_retries}, "
                       f"Success Rate: {self.retry_scoreboard.successful_retries/self.retry_scoreboard.total_retries:.2f}")
        
    def _calculate_provider_score(
        self,
        provider: ProviderType,
        task_type: str = "general"
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate provider score based on current strategy.
        
        Args:
            provider: Provider to score
            task_type: Type of task being performed
            
        Returns:
            Tuple of (score, metrics_used)
        """
        metrics = self.provider_metrics[provider]
        
        if not metrics.is_healthy:
            return 0.0, {"reason": "Provider unhealthy"}
            
        # Base scores for different strategies
        cost_score = 1.0 - (metrics.avg_cost_per_1k_tokens / 0.02)  # Normalize to 0-1
        performance_score = 1.0 - min(metrics.avg_latency / 5.0, 1.0)  # Normalize to 0-1
        availability_score = metrics.success_rate
        
        # Task-specific adjustments
        if task_type == "code_review":
            # Code review benefits from reasoning capabilities
            if provider == ProviderType.GROK:
                performance_score *= 1.1  # Grok has better reasoning
        elif task_type == "analysis":
            # Analysis benefits from cost efficiency
            cost_score *= 1.2
        elif task_type == "general":
            # General tasks use balanced scoring
            pass
            
        # Calculate weighted score based on strategy
        if self.strategy == RoutingStrategy.COST_OPTIMIZED:
            score = cost_score
            metrics_used = {"cost_score": cost_score}
        elif self.strategy == RoutingStrategy.PERFORMANCE_OPTIMIZED:
            score = performance_score
            metrics_used = {"performance_score": performance_score}
        elif self.strategy == RoutingStrategy.AVAILABILITY_OPTIMIZED:
            score = availability_score
            metrics_used = {"availability_score": availability_score}
        elif self.strategy == RoutingStrategy.HYBRID:
            score = (
                self.cost_weight * cost_score +
                self.performance_weight * performance_score +
                self.availability_weight * availability_score
            )
            metrics_used = {
                "cost_score": cost_score,
                "performance_score": performance_score,
                "availability_score": availability_score,
                "weights": {
                    "cost": self.cost_weight,
                    "performance": self.performance_weight,
                    "availability": self.availability_weight
                }
            }
        elif self.strategy == RoutingStrategy.ROUND_ROBIN:
            # Round robin uses request count for scoring
            total_requests = sum(m.total_requests for m in self.provider_metrics.values())
            if total_requests == 0:
                score = 1.0
            else:
                score = 1.0 - (metrics.total_requests / total_requests)
            metrics_used = {"request_ratio": metrics.total_requests / max(total_requests, 1)}
        else:
            score = 0.0
            metrics_used = {"error": "Unknown strategy"}
            
        return max(0.0, min(1.0, score)), metrics_used
        
    def _select_provider(
        self,
        task_type: str = "general",
        force_provider: Optional[ProviderType] = None
    ) -> Tuple[ProviderType, RoutingDecision]:
        """
        Select the best provider for the request.
        
        Args:
            task_type: Type of task being performed
            force_provider: Force specific provider (optional)
            
        Returns:
            Tuple of (selected_provider, routing_decision)
        """
        if force_provider:
            if force_provider in self.providers and self.provider_metrics[force_provider].is_healthy:
                decision = RoutingDecision(
                    provider=force_provider,
                    strategy=self.strategy,
                    confidence=1.0,
                    reasoning=f"Forced provider: {force_provider.value}"
                )
                return force_provider, decision
            else:
                logger.warning(f"[P20P7S3T1] Forced provider {force_provider.value} is not available, using automatic selection")
                
        # Calculate scores for all healthy providers
        provider_scores = {}
        for provider in self.providers:
            if self.provider_metrics[provider].is_healthy:
                score, metrics_used = self._calculate_provider_score(provider, task_type)
                provider_scores[provider] = (score, metrics_used)
                
        if not provider_scores:
            raise Exception("No healthy providers available")
            
        # Select provider with highest score
        best_provider = max(provider_scores.keys(), key=lambda p: provider_scores[p][0])
        best_score, metrics_used = provider_scores[best_provider]
        
        # Calculate confidence based on score difference
        if len(provider_scores) > 1:
            scores = [score for score, _ in provider_scores.values()]
            max_score = max(scores)
            min_score = min(scores)
            if max_score > min_score:
                confidence = (best_score - min_score) / (max_score - min_score)
            else:
                confidence = 1.0
        else:
            confidence = 1.0
            
        decision = RoutingDecision(
            provider=best_provider,
            strategy=self.strategy,
            confidence=confidence,
            reasoning=f"Selected {best_provider.value} with score {best_score:.3f}",
            metrics_used=metrics_used
        )
        
        return best_provider, decision
        
    def _update_metrics(
        self,
        provider: ProviderType,
        response_time: float,
        success: bool,
        usage: Dict[str, Any]
    ) -> None:
        """
        Update provider metrics after a request.
        
        Args:
            provider: Provider used
            response_time: Response time in seconds
            success: Whether request succeeded
            usage: Token usage data
        """
        with self._lock:
            metrics = self.provider_metrics[provider]
            
            # Update request counts
            metrics.total_requests += 1
            if not success:
                metrics.failed_requests += 1
                metrics.consecutive_failures += 1
            else:
                metrics.consecutive_failures = 0
                
            # Update health status
            metrics.is_healthy = metrics.consecutive_failures < metrics.max_consecutive_failures
            
            # Update success rate
            if metrics.total_requests > 0:
                metrics.success_rate = (metrics.total_requests - metrics.failed_requests) / metrics.total_requests
                
            # Update latency
            request_record = {
                'latency': response_time,
                'timestamp': datetime.now(),
                'success': success
            }
            self.request_history[provider].append(request_record)
            
            # Calculate rolling average latency
            if len(self.request_history[provider]) > 0:
                latencies = [req['latency'] for req in self.request_history[provider]]
                metrics.avg_latency = statistics.mean(latencies)
                
            # Update cost metrics
            if usage and 'total_tokens' in usage:
                total_tokens = usage['total_tokens']
                # Estimate cost (this could be improved with actual cost data)
                if provider == ProviderType.OPENAI:
                    estimated_cost = (total_tokens / 1000) * 0.01  # GPT-4o rate
                else:
                    estimated_cost = (total_tokens / 1000) * 0.005  # Grok rate
                    
                # Update average cost per 1k tokens
                if metrics.total_requests > 0:
                    current_avg = metrics.avg_cost_per_1k_tokens
                    new_avg = (current_avg * (metrics.total_requests - 1) + estimated_cost * 1000 / total_tokens) / metrics.total_requests
                    metrics.avg_cost_per_1k_tokens = new_avg
                    
            metrics.last_request_time = datetime.now()
            
    def route_request(
        self,
        prompt: str,
        task_type: str = "general",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_message: Optional[str] = None,
        force_provider: Optional[ProviderType] = None
    ) -> SmartRouterResponse:
        """
        Route a request to the best available provider.
        
        Args:
            prompt: Input prompt
            task_type: Type of task
            max_tokens: Maximum tokens for response
            temperature: Temperature for response
            system_message: Optional system message
            force_provider: Force specific provider
            
        Returns:
            SmartRouterResponse: Response from selected provider
            
        Raises:
            Exception: If all providers fail
        """
        start_time = time.time()
        
        # Select provider
        provider, decision = self._select_provider(task_type, force_provider)
        client = self.providers[provider]
        
        logger.info(f"[P20P7S3T1] Routing request to {provider.value} (confidence: {decision.confidence:.2f})")
        
        # Try the selected provider
        try:
            if provider == ProviderType.OPENAI:
                response = client.generate_response(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_message=system_message
                )
            else:
                response = client.generate_response(
                    prompt=prompt,
                    max_tokens=max_tokens
                )
                
            response_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(provider, response_time, True, response.usage)
            
            # Create SmartRouter response
            smart_response = SmartRouterResponse(
                content=response.content,
                provider=provider,
                response_time=response_time,
                usage=response.usage,
                routing_decision=decision,
                metadata={
                    'task_type': task_type,
                    'prompt_length': len(prompt),
                    'model': response.model
                }
            )
            
            # Store routing decision
            self.routing_history.append(decision)
            
            # Log routing decision
            self._log_routing_decision(decision, response_time, response.usage, fallback_used=False)
            
            logger.info(
                f"[P20P7S3T1] Request completed via {provider.value} "
                f"(time: {response_time:.2f}s, tokens: {response.usage.get('total_tokens', 0)})"
            )
            
            return smart_response
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"[P20P7S3T1] Request failed via {provider.value}: {e}")
            
            # Update metrics
            self._update_metrics(provider, response_time, False, {})
            
            # Try failover to other providers
            other_providers = [p for p in self.providers if p != provider and self.provider_metrics[p].is_healthy]
            
            for failover_provider in other_providers:
                try:
                    logger.info(f"[P20P7S3T1] Attempting failover to {failover_provider.value}")
                    failover_client = self.providers[failover_provider]
                    
                    if failover_provider == ProviderType.OPENAI:
                        failover_response = failover_client.generate_response(
                            prompt=prompt,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            system_message=system_message
                        )
                    else:
                        failover_response = failover_client.generate_response(
                            prompt=prompt,
                            max_tokens=max_tokens
                        )
                        
                    failover_time = time.time() - start_time
                    
                    # Update metrics
                    self._update_metrics(failover_provider, failover_time, True, failover_response.usage)
                    
                    # Update retry scoreboard
                    self._update_retry_scoreboard(True, provider, failover_provider)
                    
                    # Create failover decision
                    failover_decision = RoutingDecision(
                        provider=failover_provider,
                        strategy=self.strategy,
                        confidence=0.5,  # Lower confidence for failover
                        reasoning=f"Failover from {provider.value} to {failover_provider.value}"
                    )
                    
                    # Create SmartRouter response
                    smart_response = SmartRouterResponse(
                        content=failover_response.content,
                        provider=failover_provider,
                        response_time=failover_time,
                        usage=failover_response.usage,
                        routing_decision=failover_decision,
                        metadata={
                            'task_type': task_type,
                            'prompt_length': len(prompt),
                            'model': failover_response.model,
                            'failover': True,
                            'original_provider': provider.value
                        }
                    )
                    
                    # Store routing decision
                    self.routing_history.append(failover_decision)
                    
                    # Log routing decision
                    self._log_routing_decision(failover_decision, failover_time, failover_response.usage, fallback_used=True)
                    
                    logger.info(
                        f"[P20P7S3T1] Failover successful via {failover_provider.value} "
                        f"(time: {failover_time:.2f}s, tokens: {failover_response.usage.get('total_tokens', 0)})"
                    )
                    
                    return smart_response
                    
                except Exception as failover_error:
                    logger.error(f"[P20P7S3T1] Failover to {failover_provider.value} also failed: {failover_error}")
                    self._update_metrics(failover_provider, time.time() - start_time, False, {})
                    
            # All providers failed - update retry scoreboard
            self._update_retry_scoreboard(False, provider, provider)
            
            # All providers failed
            raise Exception(f"All providers failed. Original error: {e}")
            
    def set_strategy(self, strategy: RoutingStrategy) -> None:
        """Change the routing strategy."""
        self.strategy = strategy
        logger.info(f"[P20P7S3T1] Routing strategy changed to: {strategy.value}")
        
    def set_weights(self, cost: float, performance: float, availability: float) -> None:
        """Update the weights for hybrid strategy."""
        total = cost + performance + availability
        if total > 0:
            self.cost_weight = cost / total
            self.performance_weight = performance / total
            self.availability_weight = availability / total
            logger.info(f"[P20P7S3T1] Weights updated - Cost: {self.cost_weight:.2f}, Performance: {self.performance_weight:.2f}, Availability: {self.availability_weight:.2f}")
        else:
            logger.warning("[P20P7S3T1] Invalid weights provided (sum must be > 0)")
            
    def get_provider_metrics(self) -> Dict[ProviderType, ProviderMetrics]:
        """Get current provider metrics."""
        with self._lock:
            return self.provider_metrics.copy()
            
    def get_routing_history(self, limit: int = 10) -> List[RoutingDecision]:
        """Get recent routing decisions."""
        with self._lock:
            return list(self.routing_history)[-limit:]
            
    def get_health_status(self) -> Dict[str, bool]:
        """Get health status of all providers."""
        with self._lock:
            return {provider.value: metrics.is_healthy for provider, metrics in self.provider_metrics.items()}
            
    def get_retry_scoreboard(self) -> RetryScoreboard:
        """Get current retry scoreboard."""
        with self._lock:
            return self.retry_scoreboard
            
    def reset_metrics(self) -> None:
        """Reset all provider metrics."""
        with self._lock:
            for provider in self.provider_metrics:
                self.provider_metrics[provider] = ProviderMetrics()
                self.request_history[provider].clear()
            self.routing_history.clear()
            self.retry_scoreboard = RetryScoreboard()
            logger.info("[P20P7S3T1] All metrics reset")
            
    def shutdown(self) -> None:
        """Shutdown the SmartRouter."""
        self._stop_health_check.set()
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5)
        logger.info("[P20P7S3T1] SmartRouter shutdown complete")

    def submit_feedback(self, provider: str, feedback: dict) -> None:
        """
        Capture post-response feedback for a provider and update scoring trends.
        Phase: GBP20, Part: P20P8, Step: P20P8S2
        Args:
            provider (str): Provider name (e.g., 'openai', 'grok')
            feedback (dict): Feedback dict with keys like 'relevance', 'accuracy', 'satisfaction', etc.
        """
        if provider not in self._feedback_history:
            self._feedback_history[provider] = []
        self._feedback_history[provider].append({
            'timestamp': datetime.utcnow().isoformat(),
            **feedback
        })
        # Optionally, update scoring trends immediately
        self._update_scoring_trends(provider)

    def _update_scoring_trends(self, provider: str) -> None:
        """Update per-provider scoring trends based on feedback history."""
        history = self._feedback_history.get(provider, [])
        if not history:
            return
        # Calculate rolling averages for each feedback metric
        metrics = {}
        for key in history[0].keys():
            if key == 'timestamp':
                continue
            values = [entry[key] for entry in history if key in entry]
            if values:
                metrics[key] = sum(values) / len(values)
        self._scoring_trends[provider] = metrics

    def get_router_metadata(self) -> dict:
        metadata = {
            'provider_metrics': self.get_provider_metrics(),
            'routing_history': self.get_routing_history(),
            'health_status': self.get_health_status(),
            'retry_scoreboard': self.get_retry_scoreboard(),
            'scoring_trends': getattr(self, '_scoring_trends', {})
        }
        return metadata

# Global instance for easy access
_global_router = None

def get_smart_router() -> SmartRouter:
    """Get or create the global SmartRouter instance."""
    global _global_router
    if _global_router is None:
        _global_router = SmartRouter()
    return _global_router

def route_request(*args, **kwargs) -> SmartRouterResponse:
    """Convenience function to route a request using the global router."""
    return get_smart_router().route_request(*args, **kwargs)
