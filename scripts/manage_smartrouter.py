#!/usr/bin/env python3
"""
GitBridge SmartRouter Management CLI
Task: P20P7S4 - Live Workflow Integration

Command-line interface for managing SmartRouter strategies, testing integration,
and monitoring provider performance.

Author: GitBridge Development Team
Date: 2025-06-19
"""

import os
import sys
import argparse
import logging
from typing import Optional

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ai_router import (
    ask_ai, get_router_metrics, get_routing_history,
    set_router_strategy, set_router_weights,
    code_review, analyze_text, generate_code, explain_concept
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [gbtest] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/smartrouter_cli.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def test_integration(prompt: str, task_type: str = "general") -> None:
    """
    Test SmartRouter integration with a simple prompt.
    
    Args:
        prompt: Test prompt
        task_type: Type of task
    """
    print(f"🤖 Testing SmartRouter Integration")
    print(f"Task: P20P7S4 - Live Workflow Integration")
    print("=" * 60)
    
    try:
        print(f"📝 Prompt: {prompt}")
        print(f"🏷️ Task Type: {task_type}")
        print()
        
        # Test the integration
        response = ask_ai(prompt, task_type)
        
        print("✅ Integration Test Results:")
        print(f"   Provider: {response.provider.value}")
        print(f"   Model: {response.model}")
        print(f"   Response Time: {response.response_time:.2f}s")
        print(f"   Tokens: {response.usage.get('total_tokens', 0)}")
        print(f"   Routing Confidence: {response.routing_decision.confidence:.2f}")
        print(f"   Strategy: {response.routing_decision.strategy.value}")
        print(f"   Reasoning: {response.routing_decision.reasoning}")
        print()
        print("📄 Response Content:")
        print("-" * 40)
        print(response.content)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        logger.error(f"Integration test failed: {str(e)}")


def show_metrics() -> None:
    """Display current SmartRouter metrics."""
    print("📊 SmartRouter Metrics")
    print("=" * 40)
    
    try:
        metrics = get_router_metrics()
        
        for provider, metric in metrics.items():
            print(f"\n🔹 {provider.upper()}:")
            print(f"   Average Latency: {metric['avg_latency']:.2f}s")
            print(f"   Success Rate: {metric['success_rate']:.2%}")
            print(f"   Availability Score: {metric['availability_score']:.2f}")
            print(f"   Total Requests: {metric['total_requests']}")
            print(f"   Failed Requests: {metric['failed_requests']}")
            print(f"   Avg Cost per 1K Tokens: ${metric['avg_cost_per_1k_tokens']:.4f}")
            
    except Exception as e:
        print(f"❌ Failed to get metrics: {str(e)}")


def show_routing_history(limit: int = 10) -> None:
    """Display recent routing decisions."""
    print(f"📋 Recent Routing History (Last {limit})")
    print("=" * 50)
    
    try:
        history = get_routing_history(limit)
        
        if not history:
            print("No routing history available.")
            return
            
        for i, decision in enumerate(history, 1):
            print(f"\n{i}. {decision['timestamp']}")
            print(f"   Provider: {decision['selected_provider']}")
            print(f"   Strategy: {decision['strategy']}")
            print(f"   Confidence: {decision['confidence']:.2f}")
            print(f"   Reasoning: {decision['reasoning']}")
            
    except Exception as e:
        print(f"❌ Failed to get routing history: {str(e)}")


def test_task_functions() -> None:
    """Test convenience task functions."""
    print("🧪 Testing Task Functions")
    print("=" * 40)
    
    # Test code review
    print("\n1. Testing Code Review:")
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    """
    try:
        review = code_review(code, "Check for performance issues")
        print("✅ Code review successful")
        print(f"   Response length: {len(review)} characters")
    except Exception as e:
        print(f"❌ Code review failed: {str(e)}")
    
    # Test text analysis
    print("\n2. Testing Text Analysis:")
    text = "The quick brown fox jumps over the lazy dog."
    try:
        analysis = analyze_text(text, "sentiment")
        print("✅ Text analysis successful")
        print(f"   Response length: {len(analysis)} characters")
    except Exception as e:
        print(f"❌ Text analysis failed: {str(e)}")
    
    # Test code generation
    print("\n3. Testing Code Generation:")
    try:
        generated = generate_code("A function to calculate factorial", "python")
        print("✅ Code generation successful")
        print(f"   Response length: {len(generated)} characters")
    except Exception as e:
        print(f"❌ Code generation failed: {str(e)}")
    
    # Test concept explanation
    print("\n4. Testing Concept Explanation:")
    try:
        explanation = explain_concept("machine learning", "beginner")
        print("✅ Concept explanation successful")
        print(f"   Response length: {len(explanation)} characters")
    except Exception as e:
        print(f"❌ Concept explanation failed: {str(e)}")


def set_strategy(strategy: str) -> None:
    """Set SmartRouter strategy."""
    print(f"⚙️ Setting SmartRouter Strategy: {strategy}")
    print("=" * 50)
    
    try:
        set_router_strategy(strategy)
        print(f"✅ Strategy set to: {strategy}")
        
        # Show updated metrics
        show_metrics()
        
    except Exception as e:
        print(f"❌ Failed to set strategy: {str(e)}")


def set_weights(cost: float, performance: float, availability: float) -> None:
    """Set SmartRouter weights for hybrid strategy."""
    print(f"⚖️ Setting SmartRouter Weights")
    print("=" * 40)
    print(f"Cost: {cost}, Performance: {performance}, Availability: {availability}")
    
    try:
        set_router_weights(cost, performance, availability)
        print("✅ Weights updated successfully")
        
        # Show updated metrics
        show_metrics()
        
    except Exception as e:
        print(f"❌ Failed to set weights: {str(e)}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="GitBridge SmartRouter Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manage_smartrouter.py test "Explain AI routing"
  python scripts/manage_smartrouter.py metrics
  python scripts/manage_smartrouter.py history --limit 5
  python scripts/manage_smartrouter.py strategy --name cost_optimized
  python scripts/manage_smartrouter.py weights --cost 0.6 --performance 0.2 --availability 0.2
  python scripts/manage_smartrouter.py tasks
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test integration command
    test_parser = subparsers.add_parser('test', help='Test SmartRouter integration')
    test_parser.add_argument('prompt', help='Test prompt')
    test_parser.add_argument('--task-type', default='general', help='Task type')
    
    # Metrics command
    subparsers.add_parser('metrics', help='Show SmartRouter metrics')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show routing history')
    history_parser.add_argument('--limit', type=int, default=10, help='Number of entries')
    
    # Strategy command
    strategy_parser = subparsers.add_parser('strategy', help='Set SmartRouter strategy')
    strategy_parser.add_argument('--name', required=True, 
                                choices=['cost_optimized', 'performance_optimized', 
                                       'availability_optimized', 'hybrid'],
                                help='Strategy name')
    
    # Weights command
    weights_parser = subparsers.add_parser('weights', help='Set hybrid strategy weights')
    weights_parser.add_argument('--cost', type=float, required=True, help='Cost weight (0-1)')
    weights_parser.add_argument('--performance', type=float, required=True, help='Performance weight (0-1)')
    weights_parser.add_argument('--availability', type=float, required=True, help='Availability weight (0-1)')
    
    # Tasks command
    subparsers.add_parser('tasks', help='Test convenience task functions')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("🤖 GitBridge SmartRouter Management CLI")
    print("Task: P20P7S4 - Live Workflow Integration")
    print("=" * 60)
    
    try:
        if args.command == 'test':
            test_integration(args.prompt, args.task_type)
        elif args.command == 'metrics':
            show_metrics()
        elif args.command == 'history':
            show_routing_history(args.limit)
        elif args.command == 'strategy':
            set_strategy(args.name)
        elif args.command == 'weights':
            set_weights(args.cost, args.performance, args.availability)
        elif args.command == 'tasks':
            test_task_functions()
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
    except Exception as e:
        print(f"❌ CLI error: {str(e)}")
        logger.error(f"CLI error: {str(e)}")


if __name__ == "__main__":
    main() 