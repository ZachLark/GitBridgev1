#!/usr/bin/env python3
"""
GitBridge Grok 3 API Client
Phase: GBP20
Part: P20P7
Step: P20P7S2
Task: P20P7S2T2 - Grok Enhancement Wrap-Up

This module provides a client for interacting with Grok 3 API via xAI.
Implements the GitBridge integration with Grok 3 Mini model.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [Corrected P20P7 Schema]
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass
from functools import wraps

import requests
from openai import OpenAI
from dotenv import load_dotenv

from utils.token_usage_logger import log_token_usage

# Load environment variables
load_dotenv()

# Configure logging with P20P7 schema
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [P20P7S2] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('erudite-flask-api/gbtestgrok/logs/grok_webhook_trace.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class GrokAPIError(Exception):
    """Base exception for Grok API errors."""
    pass

class GrokConnectionError(GrokAPIError):
    """Exception for connection-related errors."""
    pass

class GrokResponseError(GrokAPIError):
    """Exception for response-related errors."""
    pass

class GrokRateLimitError(GrokAPIError):
    """Exception for rate limit errors."""
    pass

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except GrokRateLimitError as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"[P20P7S2T2] Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        logger.error(f"[P20P7S2T2] Max retries exceeded for rate limit: {e}")
                        raise
                except GrokConnectionError as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"[P20P7S2T2] Connection error, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        logger.error(f"[P20P7S2T2] Max retries exceeded for connection error: {e}")
                        raise
                except Exception as e:
                    # Don't retry other exceptions
                    logger.error(f"[P20P7S2T2] Non-retryable error: {e}")
                    raise
                    
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

@dataclass
class GrokResponse:
    """Response from Grok API."""
    content: str
    usage: Dict[str, Any]
    model: str
    response_time: float
    timestamp: str
    metadata: Dict[str, Any]

class GrokClient:
    """
    Grok 3 API client with optimization features.
    
    Phase: GBP20
    Part: P20P7
    Step: P20P7S2
    Task: P20P7S2T2 - Core Implementation
    
    Features:
    - Multi-source credential fallback
    - Configurable model selection
    - Centralized token usage logging
    - Retry mechanisms with exponential backoff
    - Enhanced error handling
    - Health monitoring
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the Grok client with fallback credential system.
        
        Args:
            api_key: xAI API key. If not provided, checks multiple sources in order:
                    1. Environment variable (os.environ)
                    2. .env file
                    3. GitHub Actions secrets
            model: Grok model to use. If not provided, uses environment variable or default
        """
        # Multi-source credential fallback system
        self.api_key = self._get_credentials(api_key)
        
        # Initialize OpenAI client (xAI uses OpenAI-compatible API)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1"
        )
        
        # Grok-specific configuration
        self.model = self._get_model_config(model)
        self.project = os.getenv('XAI_PROJECT', 'gbtestgrok')
        self.max_tokens = int(os.getenv('GROK_MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('GROK_TEMPERATURE', '0.4'))
        self.reasoning_effort = os.getenv('GROK_REASONING_EFFORT', 'high')
        
        # Log configuration with model validation
        logger.info(f"[P20P7S2T2] GrokClient initialized with model: {self.model}")
        logger.info(f"[P20P7S2T2] Project: {self.project}, Max tokens: {self.max_tokens}")
        logger.info(f"[P20P7S2T2] Reasoning effort: {self.reasoning_effort}")
        
        # Validate model selection
        self._validate_model_selection()
        
    def _validate_model_selection(self) -> None:
        """Validate and log the selected model configuration."""
        if self.model != 'grok-3-mini':
            logger.warning(f"[P20P7S2T2] Non-default model selected: {self.model}")
            logger.info(f"[P20P7S2T2] Consider using 'grok-3-mini' for optimal cost/performance balance")
        else:
            logger.info(f"[P20P7S2T2] Using recommended model: {self.model}")
            
    def _get_credentials(self, api_key: Optional[str]) -> str:
        """
        Multi-source credential fallback system.
        
        Args:
            api_key: Direct API key if provided
            
        Returns:
            str: Valid API key
            
        Raises:
            ValueError: If no valid API key found
        """
        # Priority 1: Direct constructor parameter
        if api_key:
            logger.info("[P20P7S2T2] Using API key from constructor parameter")
            return api_key
            
        # Priority 2: Environment variable
        env_key = os.getenv('XAI_API_KEY')
        if env_key:
            logger.info("[P20P7S2T2] Using API key from environment variable")
            return env_key
            
        # Priority 3: .env file (already loaded by load_dotenv())
        env_file_key = os.getenv('XAI_API_KEY')
        if env_file_key:
            logger.info("[P20P7S2T2] Using API key from .env file")
            return env_file_key
            
        # Priority 4: GitHub Actions secrets
        github_key = os.getenv('GITHUB_XAI_API_KEY')
        if github_key:
            logger.info("[P20P7S2T2] Using API key from GitHub Actions secrets")
            return github_key
            
        raise ValueError(
            "No xAI API key found. Please provide one via:\n"
            "1. Constructor parameter\n"
            "2. XAI_API_KEY environment variable\n"
            "3. .env file\n"
            "4. GitHub Actions secrets"
        )
        
    def _get_model_config(self, model: Optional[str]) -> str:
        """
        Get model configuration with fallback.
        
        Args:
            model: Model name if provided
            
        Returns:
            str: Model name to use
        """
        # Priority 1: Direct constructor parameter
        if model:
            logger.info(f"[P20P7S2T2] Using model from constructor: {model}")
            return model
            
        # Priority 2: Environment variable
        env_model = os.getenv('GROK_MODEL')
        if env_model:
            logger.info(f"[P20P7S2T2] Using model from environment: {env_model}")
            return env_model
            
        # Priority 3: Default
        default_model = 'grok-3-mini'
        logger.info(f"[P20P7S2T2] Using default model: {default_model}")
        return default_model
        
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def test_connection(self) -> GrokResponse:
        """
        Test the connection to Grok API.
        
        Returns:
            GrokResponse: Test response
        """
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello, GitBridge! Please respond with 'Grok 3 connection successful.'"}],
                max_tokens=50,
                temperature=0.1
            )
            
            response_time = time.time() - start_time
            
            # Extract response data
            content = response.choices[0].message.content
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            # Log token usage
            log_token_usage(
                usage_data=usage,
                model=self.model,
                provider='grok',
                latency=response_time,
                success=True
            )
            
            result = GrokResponse(
                content=content,
                usage=usage,
                model=self.model,
                response_time=response_time,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={'test_connection': True}
            )
            
            logger.info(f"[P20P7S2T2] Grok connection test successful - {response_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"[P20P7S2T2] Grok connection test failed: {str(e)}")
            self._handle_api_error(e)
            
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def generate_response(self, prompt: str, max_tokens: Optional[int] = None) -> GrokResponse:
        """
        Generate a response from Grok 3.
        
        Args:
            prompt: Input prompt for Grok
            max_tokens: Maximum tokens for response (defaults to self.max_tokens)
            
        Returns:
            GrokResponse: Generated response
        """
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.max_tokens,
                temperature=self.temperature
            )
            
            response_time = time.time() - start_time
            
            # Extract response data
            content = response.choices[0].message.content
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            # Log token usage
            log_token_usage(
                usage_data=usage,
                model=self.model,
                provider='grok',
                latency=response_time,
                success=True
            )
            
            result = GrokResponse(
                content=content,
                usage=usage,
                model=self.model,
                response_time=response_time,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={'prompt_length': len(prompt)}
            )
            
            logger.info(f"[P20P7S2T2] Grok response generated - {response_time:.2f}s, {usage['total_tokens']} tokens")
            return result
            
        except Exception as e:
            logger.error(f"[P20P7S2T2] Grok response generation failed: {str(e)}")
            self._handle_api_error(e)
            
    def _handle_api_error(self, error: Exception) -> None:
        """
        Handle API errors with appropriate exception types.
        
        Args:
            error: The original exception
            
        Raises:
            Appropriate GrokAPIError subclass
        """
        error_str = str(error).lower()
        
        if 'rate limit' in error_str or '429' in error_str:
            raise GrokRateLimitError(f"Rate limit exceeded: {error}")
        elif 'connection' in error_str or 'timeout' in error_str:
            raise GrokConnectionError(f"Connection error: {error}")
        elif 'response' in error_str or '400' in error_str or '500' in error_str:
            raise GrokResponseError(f"Response error: {error}")
        else:
            raise GrokAPIError(f"Unexpected error: {error}")
            
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get available Grok models.
        
        Returns:
            List[Dict[str, Any]]: Available models
        """
        try:
            models = self.client.models.list()
            return [
                {
                    'id': model.id,
                    'object': model.object,
                    'created': model.created,
                    'owned_by': model.owned_by
                }
                for model in models.data
            ]
        except Exception as e:
            logger.error(f"[P20P7S2T2] Failed to get Grok models: {str(e)}")
            raise
            
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (approximate).
        
        Args:
            text: Text to estimate
            
        Returns:
            int: Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4
        
    def get_cost_estimate(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            float: Estimated cost in USD
        """
        # Grok-3-mini pricing (approximate)
        prompt_cost_per_1k = 0.002
        completion_cost_per_1k = 0.008
        
        prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
        completion_cost = (completion_tokens / 1000) * completion_cost_per_1k
        
        return prompt_cost + completion_cost

def test_grok_connection():
    """Test Grok connection and model validation."""
    try:
        client = GrokClient()
        response = client.test_connection()
        print(f"✅ Grok connection successful")
        print(f"   Model: {response.model}")
        print(f"   Response time: {response.response_time:.2f}s")
        print(f"   Tokens used: {response.usage['total_tokens']}")
        return True
    except Exception as e:
        print(f"❌ Grok connection failed: {e}")
        return False

def main():
    """Main function for testing."""
    print("Testing Grok Client...")
    success = test_grok_connection()
    if success:
        print("Grok client is ready for use!")
    else:
        print("Grok client needs configuration.")
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 