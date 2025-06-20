#!/usr/bin/env python3
"""
GitBridge AI Router Wrapper
Phase: GBP20
Part: P20P7
Step: P20P7S4
Task: P20P7S4T1 - Live Workflow Integration

High-level wrapper for SmartRouter integration into existing GitBridge workflows.
Provides simple interface for AI requests with automatic provider selection.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [Corrected P20P7 Schema]
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from smart_router.smart_router import (
    SmartRouter,
    RoutingStrategy,
    ProviderType,
    SmartRouterResponse
)

# Configure logging with P20P7 schema
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [P20P7S4] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_router.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global SmartRouter instance
_router = None

def get_router() -> SmartRouter:
    """
    Get or create the global SmartRouter instance.
    
    Returns:
        SmartRouter: Configured router instance
    """
    global _router
    if _router is None:
        # Get strategy from environment or use default
        strategy_name = os.getenv('SMARTROUTER_STRATEGY', 'hybrid')
        try:
            strategy = RoutingStrategy(strategy_name)
        except ValueError:
            logger.warning(f"[P20P7S4T1] Invalid strategy '{strategy_name}', using 'hybrid'")
            strategy = RoutingStrategy.HYBRID
            
        # Get weights from environment or use defaults
        cost_weight = float(os.getenv('SMARTROUTER_COST_WEIGHT', '0.4'))
        performance_weight = float(os.getenv('SMARTROUTER_PERFORMANCE_WEIGHT', '0.3'))
        availability_weight = float(os.getenv('SMARTROUTER_AVAILABILITY_WEIGHT', '0.3'))
        
        _router = SmartRouter(
            strategy=strategy,
            cost_weight=cost_weight,
            performance_weight=performance_weight,
            availability_weight=availability_weight
        )
        
        logger.info(f"[P20P7S4T1] SmartRouter initialized with strategy: {strategy.value}")
        
    return _router

def get_router_metadata() -> Dict[str, Any]:
    """
    Get live metrics about the routing configuration and current health states.
    
    Returns:
        Dict containing comprehensive router metadata
    """
    router = get_router()
    
    # Get provider metrics
    provider_metrics = router.get_provider_metrics()
    
    # Get health status
    health_status = router.get_health_status()
    
    # Get retry scoreboard
    retry_scoreboard = router.get_retry_scoreboard()
    
    # Get recent routing history
    routing_history = router.get_routing_history(limit=5)
    
    metadata = {
        'router_configuration': {
            'strategy': router.strategy.value,
            'cost_weight': router.cost_weight,
            'performance_weight': router.performance_weight,
            'availability_weight': router.availability_weight,
            'metrics_window': router.metrics_window
        },
        'provider_health': health_status,
        'provider_metrics': {
            provider.value: {
                'avg_latency': metric.avg_latency,
                'success_rate': metric.success_rate,
                'availability_score': metric.availability_score,
                'total_requests': metric.total_requests,
                'failed_requests': metric.failed_requests,
                'avg_cost_per_1k_tokens': metric.avg_cost_per_1k_tokens,
                'is_healthy': metric.is_healthy,
                'consecutive_failures': metric.consecutive_failures,
                'last_request_time': metric.last_request_time.isoformat() if metric.last_request_time else None
            }
            for provider, metric in provider_metrics.items()
        },
        'retry_performance': {
            'total_retries': retry_scoreboard.total_retries,
            'successful_retries': retry_scoreboard.successful_retries,
            'failed_retries': retry_scoreboard.failed_retries,
            'route_degradations': retry_scoreboard.route_degradations,
            'retry_success_rate': retry_scoreboard.successful_retries / max(retry_scoreboard.total_retries, 1),
            'last_retry_time': retry_scoreboard.last_retry_time.isoformat() if retry_scoreboard.last_retry_time else None,
            'recent_retries': retry_scoreboard.retry_history[-10:] if retry_scoreboard.retry_history else []
        },
        'recent_decisions': [
            {
                'timestamp': decision.timestamp.isoformat(),
                'provider': decision.provider.value,
                'strategy': decision.strategy.value,
                'confidence': decision.confidence,
                'reasoning': decision.reasoning
            }
            for decision in routing_history
        ],
        'timestamp': datetime.now().isoformat()
    }
    
    return metadata

def ask_ai(
    prompt: str,
    task_type: str = "general",
    strategy: Optional[str] = None,
    force_provider: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    system_message: Optional[str] = None
) -> SmartRouterResponse:
    """
    High-level function to ask AI for a response using SmartRouter.
    
    Args:
        prompt: Input prompt
        task_type: Type of task (e.g., "code_review", "analysis", "general")
        strategy: Override strategy for this request (optional)
        force_provider: Force specific provider ("openai" or "grok")
        max_tokens: Maximum tokens for response
        temperature: Temperature for response
        system_message: Optional system message
        
    Returns:
        SmartRouterResponse: Response from selected provider
        
    Raises:
        Exception: If all providers fail
    """
    router = get_router()
    
    # Override strategy if specified
    if strategy:
        try:
            router.set_strategy(RoutingStrategy(strategy))
            logger.info(f"[P20P7S4T1] Strategy overridden to: {strategy}")
        except ValueError:
            logger.warning(f"[P20P7S4T1] Invalid strategy '{strategy}', using current strategy")
            
    # Convert force_provider string to enum
    provider_enum = None
    if force_provider:
        try:
            provider_enum = ProviderType(force_provider.lower())
            logger.info(f"[P20P7S4T1] Forcing provider: {force_provider}")
        except ValueError:
            logger.warning(f"[P20P7S4T1] Invalid provider '{force_provider}', using automatic selection")
            
    # Log the request
    logger.info(f"[P20P7S4T1] AI request - Task: {task_type}, Strategy: {router.strategy.value}")
    logger.info(f"[P20P7S4T1] Prompt length: {len(prompt)} characters")
    
    try:
        # Route the request
        response = router.route_request(
            prompt=prompt,
            task_type=task_type,
            max_tokens=max_tokens,
            temperature=temperature,
            system_message=system_message,
            force_provider=provider_enum
        )
        
        # Log the response
        logger.info(
            f"[P20P7S4T1] Response received from {response.provider.value} "
            f"(confidence: {response.routing_decision.confidence:.2f}, "
            f"time: {response.response_time:.2f}s, "
            f"tokens: {response.usage.get('total_tokens', 0)})"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"[P20P7S4T1] AI request failed: {str(e)}")
        raise

def ask_ai_simple(prompt: str, task_type: str = "general") -> str:
    """
    Simple wrapper that returns just the content string.
    
    Args:
        prompt: Input prompt
        task_type: Type of task
        
    Returns:
        str: AI response content
    """
    response = ask_ai(prompt, task_type)
    return response.content

def get_router_metrics() -> Dict[str, Any]:
    """
    Get current SmartRouter metrics.
    
    Returns:
        Dict containing provider metrics
    """
    router = get_router()
    metrics = router.get_provider_metrics()
    
    return {
        provider.value: {
            'avg_latency': metric.avg_latency,
            'success_rate': metric.success_rate,
            'availability_score': metric.availability_score,
            'total_requests': metric.total_requests,
            'failed_requests': metric.failed_requests,
            'avg_cost_per_1k_tokens': metric.avg_cost_per_1k_tokens
        }
        for provider, metric in metrics.items()
    }

def get_routing_history(limit: int = 10) -> list:
    """
    Get recent routing decisions.
    
    Args:
        limit: Number of decisions to retrieve
        
    Returns:
        List of recent routing decisions
    """
    router = get_router()
    return router.get_routing_history(limit)

def set_router_strategy(strategy: str) -> None:
    """
    Change the SmartRouter strategy.
    
    Args:
        strategy: New strategy name
    """
    router = get_router()
    try:
        router.set_strategy(RoutingStrategy(strategy))
        logger.info(f"[P20P7S4T1] Router strategy changed to: {strategy}")
    except ValueError:
        logger.error(f"[P20P7S4T1] Invalid strategy: {strategy}")

def set_router_weights(cost: float, performance: float, availability: float) -> None:
    """
    Update the SmartRouter weights for hybrid strategy.
    
    Args:
        cost: Cost weight (0.0-1.0)
        performance: Performance weight (0.0-1.0)
        availability: Availability weight (0.0-1.0)
    """
    router = get_router()
    router.set_weights(cost, performance, availability)
    logger.info(f"[P20P7S4T1] Router weights updated - Cost: {cost}, Performance: {performance}, Availability: {availability}")

def code_review(code: str, context: str = "") -> str:
    """
    Perform code review using AI.
    
    Args:
        code: Code to review
        context: Additional context
        
    Returns:
        str: Review feedback
    """
    prompt = f"Please review this code:\n\n{code}\n\nContext: {context}\n\nProvide a detailed code review with suggestions for improvement."
    return ask_ai_simple(prompt, "code_review")

def analyze_text(text: str, analysis_type: str = "general") -> str:
    """
    Analyze text using AI.
    
    Args:
        text: Text to analyze
        analysis_type: Type of analysis
        
    Returns:
        str: Analysis results
    """
    prompt = f"Please analyze this text ({analysis_type} analysis):\n\n{text}\n\nProvide a comprehensive analysis."
    return ask_ai_simple(prompt, "analysis")

def generate_code(description: str, language: str = "python") -> str:
    """
    Generate code from description.
    
    Args:
        description: Code description
        language: Programming language
        
    Returns:
        str: Generated code
    """
    prompt = f"Please generate {language} code for the following description:\n\n{description}\n\nProvide complete, working code with comments."
    return ask_ai_simple(prompt, "code_generation")

def explain_concept(concept: str, level: str = "intermediate") -> str:
    """
    Explain a concept using AI.
    
    Args:
        concept: Concept to explain
        level: Explanation level (beginner, intermediate, advanced)
        
    Returns:
        str: Concept explanation
    """
    prompt = f"Please explain the concept of '{concept}' at a {level} level. Provide clear, comprehensive explanations with examples."
    return ask_ai_simple(prompt, "explanation") 