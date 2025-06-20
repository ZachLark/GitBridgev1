#!/usr/bin/env python3
"""
GitBridge OpenAI API Health Check Tool
Task: P20P7S2A - OpenAI Parity Layer

CLI tool to validate OpenAI API connectivity, latency, and response format.
"""

import os
import sys
import time
import json
import logging
import argparse
from typing import Dict, Any, Optional
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clients.openai_client import OpenAIClient, OpenAIResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [P20P7S2A-health] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/openai_healthcheck.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_api_health(
    model: Optional[str] = None,
    max_latency: float = 2.0,
    retries: int = 3,
    output_format: str = 'human'
) -> Dict[str, Any]:
    """
    Check OpenAI API health and performance.
    
    Args:
        model: OpenAI model to test
        max_latency: Maximum acceptable latency in seconds
        retries: Number of retry attempts
        output_format: Output format ('json' or 'human')
        
    Returns:
        Dict containing health check results
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'provider': 'OpenAI',
        'model': model or 'gpt-4o',
        'status': 'unknown',
        'latency': 0.0,
        'retries': 0,
        'error': None,
        'response': None,
        'usage': None
    }
    
    client = None
    for attempt in range(retries):
        try:
            logger.info(f"OpenAI health check attempt {attempt + 1}/{retries}")
            
            # Initialize client
            client = OpenAIClient(model=model)
            results['retries'] = attempt + 1
            
            # Test connection
            start_time = time.time()
            response = client.test_connection()
            latency = time.time() - start_time
            
            # Update results
            results['status'] = 'healthy'
            results['latency'] = latency
            results['response'] = response.content
            results['usage'] = response.usage
            
            # Check latency
            if latency > max_latency:
                results['status'] = 'slow'
                logger.warning(f"OpenAI API latency ({latency:.2f}s) exceeds threshold ({max_latency}s)")
            else:
                logger.info(f"OpenAI API health check successful - {latency:.2f}s")
                
            break
            
        except Exception as e:
            error_msg = str(e)
            results['error'] = error_msg
            results['retries'] = attempt + 1
            
            logger.error(f"OpenAI health check attempt {attempt + 1} failed: {error_msg}")
            
            if attempt < retries - 1:
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                results['status'] = 'failed'
                logger.error("OpenAI health check failed after all retries")
                
    return results

def main():
    """CLI entrypoint for OpenAI health check."""
    parser = argparse.ArgumentParser(
        description="OpenAI API Health Check Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic health check:
    %(prog)s
    
  Check with specific model:
    %(prog)s --model gpt-4o-mini
    
  JSON output:
    %(prog)s --format json
    
  Custom latency threshold:
    %(prog)s --max-latency 1.5
"""
    )
    
    parser.add_argument(
        '--model',
        help='OpenAI model to test (default: gpt-4o)'
    )
    parser.add_argument(
        '--max-latency',
        type=float,
        default=2.0,
        help='Maximum acceptable latency in seconds (default: 2.0)'
    )
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='Number of retry attempts (default: 3)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'human'],
        default='human',
        help='Output format (default: human)'
    )
    
    args = parser.parse_args()
    
    # Run health check
    results = check_api_health(
        model=args.model,
        max_latency=args.max_latency,
        retries=args.retries,
        output_format=args.format
    )
    
    # Output results
    if args.format == 'json':
        print(json.dumps(results, indent=2))
    else:
        print("\n" + "="*50)
        print("OpenAI API Health Check Results")
        print("="*50)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Provider: {results['provider']}")
        print(f"Model: {results['model']}")
        print(f"Status: {results['status'].upper()}")
        print(f"Latency: {results['latency']:.2f}s")
        print(f"Retries: {results['retries']}")
        
        if results['error']:
            print(f"Error: {results['error']}")
        else:
            print(f"Response: {results['response']}")
            if results['usage']:
                usage = results['usage']
                print(f"Usage: {usage['total_tokens']} tokens "
                      f"({usage['prompt_tokens']} prompt, {usage['completion_tokens']} completion)")
        
        print("="*50)
        
        # Exit with appropriate code
        if results['status'] == 'healthy':
            sys.exit(0)
        elif results['status'] == 'slow':
            sys.exit(1)
        else:
            sys.exit(2)

if __name__ == "__main__":
    main() 