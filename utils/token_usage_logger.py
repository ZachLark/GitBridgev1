#!/usr/bin/env python3
"""
GitBridge Token Usage Logger
Task: P20P6B - Grok Integration Enhancements

Centralized token usage tracking system for SmartRouter's dynamic load balancing.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [token-usage] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/usage_grok.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TokenUsageRecord:
    """Token usage record for a single API call."""
    timestamp: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency: float
    success: bool
    error: Optional[str] = None

class TokenUsageLogger:
    """Centralized token usage tracking system."""
    
    def __init__(self, log_file: str = 'logs/usage_grok.log'):
        """
        Initialize token usage logger.
        
        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
        self._lock = Lock()  # Thread-safe logging
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Cost per token rates (can be updated via environment variables)
        self.cost_rates = {
            'grok-3-mini': float(os.getenv('GROK_MINI_COST_PER_1K', '0.002')),
            'grok-3-fast': float(os.getenv('GROK_FAST_COST_PER_1K', '0.004')),
            'gpt-4o': float(os.getenv('GPT4O_COST_PER_1K', '0.01'))
        }
        
    def log_usage(self, usage_data: Dict[str, Any], model: str,
                provider: str, latency: float, success: bool,
                error: Optional[str] = None) -> None:
        """
        Log token usage data.
        
        Args:
            usage_data: Token usage statistics
            model: Model identifier
            provider: API provider (e.g., 'xai', 'openai')
            latency: API call latency in seconds
            success: Whether the API call succeeded
            error: Error message if the call failed
        """
        try:
            # Calculate cost
            cost_per_1k = self.cost_rates.get(model, 0.002)  # Default to grok-3-mini rate
            total_tokens = usage_data.get('total_tokens', 0)
            cost = (total_tokens / 1000) * cost_per_1k
            
            # Create usage record
            record = TokenUsageRecord(
                timestamp=datetime.now().isoformat(),
                model=model,
                provider=provider,
                prompt_tokens=usage_data.get('prompt_tokens', 0),
                completion_tokens=usage_data.get('completion_tokens', 0),
                total_tokens=total_tokens,
                cost_usd=cost,
                latency=latency,
                success=success,
                error=error
            )
            
            # Log to file (thread-safe)
            with self._lock:
                with open(self.log_file, 'a') as f:
                    json.dump(asdict(record), f)
                    f.write('\n')
                    
            # Log summary
            logger.info(
                f"Token usage logged - Model: {model}, "
                f"Tokens: {total_tokens}, Cost: ${cost:.4f}, "
                f"Latency: {latency:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Failed to log token usage: {str(e)}")
            
    def get_usage_summary(self, provider: Optional[str] = None,
                       model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage summary statistics.
        
        Args:
            provider: Filter by provider
            model: Filter by model
            
        Returns:
            Dict containing usage statistics
        """
        summary = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "total_calls": 0,
            "successful_calls": 0,
            "average_latency": 0.0,
            "by_model": {}
        }
        
        try:
            with open(self.log_file, 'r') as f:
                total_latency = 0.0
                
                for line in f:
                    record = json.loads(line)
                    
                    # Apply filters
                    if provider and record['provider'] != provider:
                        continue
                    if model and record['model'] != model:
                        continue
                        
                    # Update summary
                    summary["total_cost"] += record["cost_usd"]
                    summary["total_tokens"] += record["total_tokens"]
                    summary["total_calls"] += 1
                    if record["success"]:
                        summary["successful_calls"] += 1
                    total_latency += record["latency"]
                    
                    # Update model-specific stats
                    model_key = record["model"]
                    if model_key not in summary["by_model"]:
                        summary["by_model"][model_key] = {
                            "total_tokens": 0,
                            "total_cost": 0.0,
                            "calls": 0
                        }
                    summary["by_model"][model_key]["total_tokens"] += record["total_tokens"]
                    summary["by_model"][model_key]["total_cost"] += record["cost_usd"]
                    summary["by_model"][model_key]["calls"] += 1
                    
                # Calculate average latency
                if summary["total_calls"] > 0:
                    summary["average_latency"] = total_latency / summary["total_calls"]
                    
        except FileNotFoundError:
            logger.warning(f"Usage log file not found: {self.log_file}")
            
        return summary

# Global instance
token_logger = TokenUsageLogger()

def log_token_usage(*args, **kwargs):
    """Global function to log token usage."""
    return token_logger.log_usage(*args, **kwargs) 