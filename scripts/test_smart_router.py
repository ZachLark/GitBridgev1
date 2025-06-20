#!/usr/bin/env python3
"""
GitBridge SmartRouter Test Script
Task: P20P7S3 - SmartRouter Core Logic Implementation

Comprehensive testing and dry-run capabilities for the SmartRouter system.
Tests all routing strategies, failover mechanisms, and performance metrics.

Author: GitBridge Development Team
Date: 2025-06-19
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smart_router.smart_router import (
    SmartRouter,
    RoutingStrategy,
    ProviderType,
    SmartRouterResponse
)

def test_routing_strategies(router: SmartRouter, test_prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Test all routing strategies with sample prompts.
    
    Args:
        router: SmartRouter instance
        test_prompts: List of test prompts with metadata
        
    Returns:
        Dict containing test results
    """
    results = {
        'strategies': {},
        'total_tests': 0,
        'successful_tests': 0,
        'failed_tests': 0
    }
    
    strategies = [
        RoutingStrategy.COST_OPTIMIZED,
        RoutingStrategy.PERFORMANCE_OPTIMIZED,
        RoutingStrategy.AVAILABILITY_OPTIMIZED,
        RoutingStrategy.HYBRID
    ]
    
    for strategy in strategies:
        print(f"\n🧪 Testing Strategy: {strategy.value}")
        print("=" * 50)
        
        router.set_strategy(strategy)
        strategy_results = {
            'provider_selections': {},
            'avg_confidence': 0.0,
            'avg_response_time': 0.0,
            'total_requests': 0,
            'successful_requests': 0
        }
        
        total_confidence = 0.0
        total_response_time = 0.0
        
        for i, test_case in enumerate(test_prompts):
            print(f"  Test {i+1}: {test_case['task_type']}")
            
            try:
                start_time = time.time()
                response = router.route_request(
                    prompt=test_case['prompt'],
                    task_type=test_case['task_type'],
                    max_tokens=test_case.get('max_tokens'),
                    temperature=test_case.get('temperature')
                )
                response_time = time.time() - start_time
                
                # Update statistics
                provider = response.routing_decision.selected_provider.value
                strategy_results['provider_selections'][provider] = strategy_results['provider_selections'].get(provider, 0) + 1
                
                total_confidence += response.routing_decision.confidence
                total_response_time += response_time
                strategy_results['total_requests'] += 1
                strategy_results['successful_requests'] += 1
                
                print(f"    ✅ {provider} (confidence: {response.routing_decision.confidence:.2f}, time: {response_time:.2f}s)")
                print(f"    📝 {response.routing_decision.reasoning}")
                
            except Exception as e:
                strategy_results['total_requests'] += 1
                print(f"    ❌ Failed: {str(e)}")
                
            results['total_tests'] += 1
            
        # Calculate averages
        if strategy_results['successful_requests'] > 0:
            strategy_results['avg_confidence'] = total_confidence / strategy_results['successful_requests']
            strategy_results['avg_response_time'] = total_response_time / strategy_results['successful_requests']
            results['successful_tests'] += 1
        else:
            results['failed_tests'] += 1
            
        results['strategies'][strategy.value] = strategy_results
        
    return results

def test_failover_mechanisms(router: SmartRouter) -> Dict[str, Any]:
    """
    Test failover mechanisms by simulating provider failures.
    
    Args:
        router: SmartRouter instance
        
    Returns:
        Dict containing failover test results
    """
    print("\n🔄 Testing Failover Mechanisms")
    print("=" * 50)
    
    results = {
        'failover_tests': 0,
        'successful_failovers': 0,
        'failed_failovers': 0
    }
    
    # Test with a simple prompt
    test_prompt = "Hello, this is a failover test. Please respond briefly."
    
    # Test 1: Normal routing (both providers available)
    print("  Test 1: Normal routing (both providers available)")
    try:
        response = router.route_request(test_prompt, task_type="failover_test")
        print(f"    ✅ Success via {response.provider.value}")
        results['failover_tests'] += 1
        results['successful_failovers'] += 1
    except Exception as e:
        print(f"    ❌ Failed: {str(e)}")
        results['failover_tests'] += 1
        results['failed_failovers'] += 1
        
    # Test 2: Force OpenAI (simulate Grok failure)
    print("  Test 2: Force OpenAI routing")
    try:
        response = router.route_request(
            test_prompt,
            task_type="failover_test",
            force_provider=ProviderType.OPENAI
        )
        print(f"    ✅ Success via {response.provider.value}")
        results['failover_tests'] += 1
        results['successful_failovers'] += 1
    except Exception as e:
        print(f"    ❌ Failed: {str(e)}")
        results['failover_tests'] += 1
        results['failed_failovers'] += 1
        
    # Test 3: Force Grok (simulate OpenAI failure)
    print("  Test 3: Force Grok routing")
    try:
        response = router.route_request(
            test_prompt,
            task_type="failover_test",
            force_provider=ProviderType.GROK
        )
        print(f"    ✅ Success via {response.provider.value}")
        results['failover_tests'] += 1
        results['successful_failovers'] += 1
    except Exception as e:
        print(f"    ❌ Failed: {str(e)}")
        results['failover_tests'] += 1
        results['failed_failovers'] += 1
        
    return results

def test_performance_metrics(router: SmartRouter) -> Dict[str, Any]:
    """
    Test and display performance metrics.
    
    Args:
        router: SmartRouter instance
        
    Returns:
        Dict containing performance metrics
    """
    print("\n📊 Performance Metrics")
    print("=" * 50)
    
    metrics = router.get_provider_metrics()
    results = {}
    
    for provider_type, provider_metrics in metrics.items():
        print(f"  {provider_type.value.upper()}:")
        print(f"    Average Latency: {provider_metrics.avg_latency:.2f}s")
        print(f"    Success Rate: {provider_metrics.success_rate:.2%}")
        print(f"    Availability Score: {provider_metrics.availability_score:.2f}")
        print(f"    Total Requests: {provider_metrics.total_requests}")
        print(f"    Failed Requests: {provider_metrics.failed_requests}")
        print(f"    Cost per 1K tokens: ${provider_metrics.avg_cost_per_1k_tokens:.4f}")
        print()
        
        results[provider_type.value] = {
            'avg_latency': provider_metrics.avg_latency,
            'success_rate': provider_metrics.success_rate,
            'availability_score': provider_metrics.availability_score,
            'total_requests': provider_metrics.total_requests,
            'failed_requests': provider_metrics.failed_requests,
            'avg_cost_per_1k_tokens': provider_metrics.avg_cost_per_1k_tokens
        }
        
    return results

def test_routing_history(router: SmartRouter) -> None:
    """
    Display recent routing decisions.
    
    Args:
        router: SmartRouter instance
    """
    print("\n📋 Recent Routing Decisions")
    print("=" * 50)
    
    history = router.get_routing_history(limit=10)
    
    if not history:
        print("  No routing decisions found.")
        return
        
    for i, decision in enumerate(reversed(history)):
        print(f"  {i+1}. {decision['selected_provider']} ({decision['strategy']})")
        print(f"     Task: {decision['task_type']}")
        print(f"     Confidence: {decision['confidence']:.2f}")
        print(f"     Reasoning: {decision['reasoning']}")
        print(f"     Timestamp: {decision['timestamp']}")
        print()

def run_dry_run(router: SmartRouter, prompt: str, task_type: str = "test") -> None:
    """
    Run a dry run without making actual API calls.
    
    Args:
        router: SmartRouter instance
        prompt: Test prompt
        task_type: Task type
    """
    print(f"\n🔍 Dry Run: {task_type}")
    print("=" * 50)
    print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    
    # Update provider health (this will make actual health checks)
    print("  Updating provider health...")
    router._update_provider_health()
    
    # Make routing decision without executing
    print("  Making routing decision...")
    decision = router._make_routing_decision(prompt, task_type, None)
    
    print(f"  Selected Provider: {decision.selected_provider.value}")
    print(f"  Strategy: {decision.strategy.value}")
    print(f"  Confidence: {decision.confidence:.2f}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Estimated Cost: ${decision.estimated_cost:.4f}")
    print(f"  Estimated Latency: {decision.estimated_latency:.2f}s")
    
    if decision.alternative_provider:
        print(f"  Alternative Provider: {decision.alternative_provider.value}")

def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="SmartRouter Test Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Run all tests:
    %(prog)s --all
    
  Test specific strategy:
    %(prog)s --strategy cost_optimized
    
  Dry run with custom prompt:
    %(prog)s --dry-run "Explain quantum computing"
    
  Performance test only:
    %(prog)s --performance
"""
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all tests'
    )
    parser.add_argument(
        '--strategy',
        choices=['cost_optimized', 'performance_optimized', 'availability_optimized', 'hybrid'],
        help='Test specific routing strategy'
    )
    parser.add_argument(
        '--dry-run',
        metavar='PROMPT',
        help='Run dry run with custom prompt'
    )
    parser.add_argument(
        '--performance',
        action='store_true',
        help='Show performance metrics only'
    )
    parser.add_argument(
        '--failover',
        action='store_true',
        help='Test failover mechanisms'
    )
    parser.add_argument(
        '--history',
        action='store_true',
        help='Show routing history'
    )
    
    args = parser.parse_args()
    
    # Initialize SmartRouter
    print("🤖 GitBridge SmartRouter Test Suite")
    print("Task: P20P7S3 - SmartRouter Core Logic Implementation")
    print("=" * 60)
    
    router = SmartRouter()
    
    # Test prompts
    test_prompts = [
        {
            'prompt': 'Write a brief explanation of machine learning.',
            'task_type': 'explanation',
            'max_tokens': 200
        },
        {
            'prompt': 'Review this code: def hello(): print("Hello, World!")',
            'task_type': 'code_review',
            'max_tokens': 300
        },
        {
            'prompt': 'Analyze the benefits of renewable energy sources.',
            'task_type': 'analysis',
            'max_tokens': 400
        },
        {
            'prompt': 'Create a simple Python function to calculate fibonacci numbers.',
            'task_type': 'code_generation',
            'max_tokens': 250
        }
    ]
    
    # Run tests based on arguments
    if args.dry_run:
        run_dry_run(router, args.dry_run)
        
    elif args.performance:
        test_performance_metrics(router)
        
    elif args.failover:
        test_failover_mechanisms(router)
        
    elif args.history:
        test_routing_history(router)
        
    elif args.strategy:
        strategy = RoutingStrategy(args.strategy)
        router.set_strategy(strategy)
        test_routing_strategies(router, test_prompts)
        
    elif args.all or not any([args.strategy, args.dry_run, args.performance, args.failover, args.history]):
        # Run comprehensive test suite
        print("Running comprehensive test suite...")
        
        # Test all strategies
        strategy_results = test_routing_strategies(router, test_prompts)
        
        # Test failover
        failover_results = test_failover_mechanisms(router)
        
        # Show performance metrics
        performance_results = test_performance_metrics(router)
        
        # Show routing history
        test_routing_history(router)
        
        # Summary
        print("\n📈 Test Summary")
        print("=" * 50)
        print(f"Total Tests: {strategy_results['total_tests']}")
        print(f"Successful: {strategy_results['successful_tests']}")
        print(f"Failed: {strategy_results['failed_tests']}")
        print(f"Failover Tests: {failover_results['failover_tests']}")
        print(f"Successful Failovers: {failover_results['successful_failovers']}")
        
    print("\n✅ SmartRouter testing complete!")

if __name__ == "__main__":
    main() 