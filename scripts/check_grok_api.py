#!/usr/bin/env python3
"""
GitBridge Grok API Health Check Tool
Task: P20P6B - Grok Integration Enhancements

CLI tool to validate Grok API connectivity, latency, and response format.
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
from clients.grok_client import GrokClient, GrokResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [gbtestgrok-health] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/grok_health.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_api_health(
    model: Optional[str] = None,
    max_latency: float = 2.0,
    retries: int = 3
) -> Dict[str, Any]:
    """
    Check Grok API health and performance.
    
    Args:
        model: Override default model
        max_latency: Maximum acceptable latency in seconds
        retries: Number of retry attempts
        
    Returns:
        Dict containing health check results
    """
    start_time = time.time()
    results = {
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "latency": None,
        "model": model or "grok-3-mini",
        "errors": []
    }
    
    try:
        # Initialize client
        client = GrokClient()
        if model:
            client.model = model
            
        # Test connection with retries
        for attempt in range(retries):
            try:
                response = client.test_connection()
                if response.success:
                    results["success"] = True
                    results["latency"] = response.response_time
                    results["usage"] = response.usage
                    break
                else:
                    results["errors"].append(f"Attempt {attempt + 1}: {response.error_message}")
            except Exception as e:
                results["errors"].append(f"Attempt {attempt + 1}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(1)  # Wait before retry
                    
        # Check latency threshold
        if results["success"] and results["latency"] > max_latency:
            results["warning"] = f"High latency: {results['latency']:.2f}s (threshold: {max_latency}s)"
            
    except Exception as e:
        results["errors"].append(f"Setup error: {str(e)}")
        
    results["total_time"] = time.time() - start_time
    return results

def main():
    """CLI entrypoint for Grok API health check."""
    parser = argparse.ArgumentParser(description="Check Grok API health and performance")
    parser.add_argument("--model", help="Override default model (default: grok-3-mini)")
    parser.add_argument("--max-latency", type=float, default=2.0,
                      help="Maximum acceptable latency in seconds (default: 2.0)")
    parser.add_argument("--retries", type=int, default=3,
                      help="Number of retry attempts (default: 3)")
    parser.add_argument("--json", action="store_true",
                      help="Output results in JSON format")
    args = parser.parse_args()
    
    # Run health check
    results = check_api_health(
        model=args.model,
        max_latency=args.max_latency,
        retries=args.retries
    )
    
    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n🔍 Grok API Health Check Results")
        print("=" * 40)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Success: {'✅' if results['success'] else '❌'}")
        print(f"Model: {results['model']}")
        if results["latency"]:
            print(f"Latency: {results['latency']:.2f}s")
        if results.get("warning"):
            print(f"⚠️  {results['warning']}")
        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - {error}")
        print(f"\nTotal check time: {results['total_time']:.2f}s")
        
    # Exit with appropriate status
    sys.exit(0 if results["success"] else 1)

if __name__ == "__main__":
    main() 