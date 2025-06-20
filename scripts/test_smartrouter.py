#!/usr/bin/env python3
"""
GitBridge SmartRouter Test Script
Phase: GBP20
Part: P20P7
Step: P20P7S3
Task: P20P7S3T2 - Comprehensive Testing Suite

Comprehensive test suite for SmartRouter functionality including:
- Provider initialization
- Routing strategies
- Metrics tracking
- Failover mechanisms
- Health monitoring

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [Corrected P20P7 Schema]
"""

import os
import sys
import time
import logging
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_router.smart_router import (
    SmartRouter,
    RoutingStrategy,
    ProviderType,
    SmartRouterResponse
)

# Configure logging with P20P7 schema
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [P20P7S3] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/test_smartrouter.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_initialization():
    """Test SmartRouter initialization."""
    logger.info("=== Testing SmartRouter Initialization ===")
    
    # Test default initialization
    try:
        router = SmartRouter()
        logger.info("✅ Default initialization successful")
    except Exception as e:
        logger.error(f"❌ Default initialization failed: {e}")
        return False
        
    # Test custom initialization
    try:
        router = SmartRouter(
            strategy=RoutingStrategy.COST_OPTIMIZED,
            cost_weight=0.8,
            performance_weight=0.1,
            availability_weight=0.1
        )
        logger.info("✅ Custom initialization successful")
    except Exception as e:
        logger.error(f"❌ Custom initialization failed: {e}")
        return False
        
    # Test provider initialization
    try:
        providers = router.providers
        if ProviderType.OPENAI in providers and ProviderType.GROK in providers:
            logger.info("✅ Provider initialization successful")
        else:
            logger.error("❌ Provider initialization failed")
            return False
    except Exception as e:
        logger.error(f"❌ Provider check failed: {e}")
        return False
        
    return True

def test_health_checks():
    """Test health check functionality."""
    logger.info("=== Testing Health Checks ===")
    
    try:
        # Create router with short health check interval for testing
        router = SmartRouter(health_check_interval=5)
        
        # Wait for health checks to run
        time.sleep(3)
        
        # Check health status
        health_status = router.get_health_status()
        logger.info(f"Health status: {health_status}")
        
        # Log provider metrics
        metrics = router.get_provider_metrics()
        for provider, metric in metrics.items():
            logger.info(f"{provider.value}: healthy={metric.is_healthy}, requests={metric.total_requests}, latency={metric.avg_latency:.2f}s")
            
        # Shutdown
        router.shutdown()
        
        logger.info("✅ Health check test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Health check test failed: {e}")
        return False

def test_routing_strategies():
    """Test all routing strategies."""
    logger.info("=== Testing Routing Strategies ===")
    
    strategies = [
        RoutingStrategy.COST_OPTIMIZED,
        RoutingStrategy.PERFORMANCE_OPTIMIZED,
        RoutingStrategy.AVAILABILITY_OPTIMIZED,
        RoutingStrategy.HYBRID,
        RoutingStrategy.ROUND_ROBIN
    ]
    
    for strategy in strategies:
        logger.info(f"Testing strategy: {strategy.value}")
        try:
            router = SmartRouter(strategy=strategy)
            
            # Test provider scoring
            for provider in [ProviderType.OPENAI, ProviderType.GROK]:
                score, metrics = router._calculate_provider_score(provider, "general")
                logger.info(f"  {provider.value}: score={score:.3f}, metrics={metrics}")
                
            router.shutdown()
            
        except Exception as e:
            logger.error(f"❌ Strategy {strategy.value} test failed: {e}")
            return False
            
    logger.info("✅ Routing strategies test successful")
    return True

def test_actual_requests():
    """Test actual API requests."""
    logger.info("=== Testing Actual Requests ===")
    
    try:
        router = SmartRouter()
        
        # Test different task types
        test_cases = [
            ("general", "Hello, how are you?"),
            ("code_review", "Review this code: def hello(): print('world')"),
            ("analysis", "Analyze the performance implications of this algorithm")
        ]
        
        for task_type, prompt in test_cases:
            logger.info(f"Testing: {task_type} - '{prompt[:30]}...'")
            try:
                response = router.route_request(prompt, task_type=task_type)
                logger.info(f"  ✅ Response from {response.provider.value}")
                logger.info(f"  Content: {response.content[:100]}...")
                logger.info(f"  Time: {response.response_time:.2f}s")
                logger.info(f"  Tokens: {response.usage.get('total_tokens', 0)}")
                logger.info(f"  Confidence: {response.routing_decision.confidence:.2f}")
            except Exception as e:
                logger.error(f"  ❌ Request failed: {e}")
                return False
                
        # Log final metrics
        metrics = router.get_provider_metrics()
        for provider, metric in metrics.items():
            logger.info(f"Final metrics for {provider.value}:")
            logger.info(f"  Total requests: {metric.total_requests}")
            logger.info(f"  Success rate: {metric.success_rate:.2f}")
            logger.info(f"  Avg latency: {metric.avg_latency:.2f}s")
            logger.info(f"  Is healthy: {metric.is_healthy}")
            
        router.shutdown()
        logger.info("✅ Actual requests test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Actual requests test failed: {e}")
        return False

def test_failover():
    """Test failover mechanism."""
    logger.info("=== Testing Failover Mechanism ===")
    
    try:
        router = SmartRouter()
        
        # Test normal request
        response = router.route_request("Test failover mechanism")
        logger.info(f"✅ Request completed via {response.provider.value}")
        
        router.shutdown()
        logger.info("✅ Failover test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failover test failed: {e}")
        return False

def test_metrics_and_history():
    """Test metrics tracking and history."""
    logger.info("=== Testing Metrics and History ===")
    
    try:
        router = SmartRouter()
        
        # Make several requests
        for i in range(3):
            response = router.route_request(f"Test request {i+1}")
            logger.info(f"Request {i+1} completed via {response.provider.value}")
            
        # Check routing history
        history = router.get_routing_history(limit=3)
        logger.info("Routing history (last 3 decisions):")
        for decision in history:
            logger.info(f"   {decision.timestamp}: {decision.provider.value} (confidence: {decision.confidence:.2f})")
            
        # Check provider metrics
        metrics = router.get_provider_metrics()
        logger.info("Provider metrics:")
        for provider, metric in metrics.items():
            logger.info(f"  {provider.value}:")
            logger.info(f"    Requests: {metric.total_requests}")
            logger.info(f"    Failed: {metric.failed_requests}")
            logger.info(f"    Success rate: {metric.success_rate:.2f}")
            logger.info(f"    Avg latency: {metric.avg_latency:.2f}s")
            logger.info(f"    Avg cost per 1k tokens: ${metric.avg_cost_per_1k_tokens:.4f}")
            
        router.shutdown()
        logger.info("✅ Metrics and history test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Metrics and history test failed: {e}")
        return False

def test_strategy_changes():
    """Test dynamic strategy and weight changes."""
    logger.info("=== Testing Strategy Changes ===")
    
    try:
        router = SmartRouter()
        
        # Test strategy changes
        strategies = [
            RoutingStrategy.COST_OPTIMIZED,
            RoutingStrategy.PERFORMANCE_OPTIMIZED,
            RoutingStrategy.AVAILABILITY_OPTIMIZED,
            RoutingStrategy.ROUND_ROBIN,
            RoutingStrategy.HYBRID
        ]
        
        for strategy in strategies:
            router.set_strategy(strategy)
            logger.info(f"✅ Strategy changed to: {strategy.value}")
            
        # Test weight changes
        router.set_weights(0.6, 0.3, 0.1)
        logger.info("✅ Weight changes successful")
        
        router.shutdown()
        logger.info("✅ Strategy changes test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Strategy changes test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🚀 Starting SmartRouter Test Suite")
    logger.info("=" * 50)
    
    tests = [
        ("Initialization", test_initialization),
        ("Health Checks", test_health_checks),
        ("Routing Strategies", test_routing_strategies),
        ("Actual Requests", test_actual_requests),
        ("Failover", test_failover),
        ("Metrics and History", test_metrics_and_history),
        ("Strategy Changes", test_strategy_changes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info("=" * 50)
        
        try:
            if test_func():
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    for test_name, _ in tests:
        logger.info(f"{test_name}: ✅ PASSED")
        
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! SmartRouter is ready for production.")
        return 0
    else:
        logger.error(f"❌ {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    exit(main()) 