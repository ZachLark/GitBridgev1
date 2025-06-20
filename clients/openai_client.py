#!/usr/bin/env python3
"""
GitBridge OpenAI API Client
Phase: GBP20
Part: P20P7
Step: P20P7S2
Task: P20P7S2T1 - OpenAI Parity Layer

This module provides a client for interacting with OpenAI API.
Implements the GitBridge integration with GPT-4o and other OpenAI models.

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
        logging.FileHandler('logs/openai_integration_trace.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class OpenAIResponse:
    """Response from OpenAI API."""
    content: str
    usage: Dict[str, Any]
    model: str
    response_time: float
    timestamp: str
    metadata: Dict[str, Any]

class OpenAIClient:
    """
    OpenAI API client with optimization features.
    
    Phase: GBP20
    Part: P20P7
    Step: P20P7S2
    Task: P20P7S2T1 - Core Implementation
    
    Features:
    - Multi-source credential fallback
    - Configurable model selection
    - Centralized token usage logging
    - Health monitoring
    - Retry mechanisms
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the OpenAI client with fallback credential system.
        
        Args:
            api_key: OpenAI API key. If not provided, checks multiple sources in order:
                    1. Environment variable (os.environ)
                    2. .env file
                    3. GitHub Actions secrets
            model: OpenAI model to use. If not provided, uses environment variable or default
        """
        # Multi-source credential fallback system
        self.api_key = self._get_credentials(api_key)
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # OpenAI-specific configuration
        self.model = self._get_model_config(model)
        self.project = os.getenv('OPENAI_PROJECT', 'gitbridge')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
        
        # Log configuration
        logger.info(f"[P20P7S2T1] OpenAIClient initialized with model: {self.model}")
        logger.info(f"[P20P7S2T1] Project: {self.project}, Max tokens: {self.max_tokens}")
        
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
            logger.info("[P20P7S2T1] Using API key from constructor parameter")
            return api_key
            
        # Priority 2: Environment variable
        env_key = os.getenv('OPENAI_API_KEY')
        if env_key:
            logger.info("[P20P7S2T1] Using API key from environment variable")
            return env_key
            
        # Priority 3: .env file (already loaded by load_dotenv())
        env_file_key = os.getenv('OPENAI_API_KEY')
        if env_file_key:
            logger.info("[P20P7S2T1] Using API key from .env file")
            return env_file_key
            
        # Priority 4: GitHub Actions secrets
        github_key = os.getenv('GITHUB_OPENAI_API_KEY')
        if github_key:
            logger.info("[P20P7S2T1] Using API key from GitHub Actions secrets")
            return github_key
            
        raise ValueError(
            "No OpenAI API key found. Please provide one via:\n"
            "1. Constructor parameter\n"
            "2. OPENAI_API_KEY environment variable\n"
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
            logger.info(f"[P20P7S2T1] Using model from constructor: {model}")
            return model
            
        # Priority 2: Environment variable
        env_model = os.getenv('OPENAI_MODEL')
        if env_model:
            logger.info(f"[P20P7S2T1] Using model from environment: {env_model}")
            return env_model
            
        # Priority 3: Default
        default_model = 'gpt-4o'
        logger.info(f"[P20P7S2T1] Using default model: {default_model}")
        return default_model
        
    def test_connection(self) -> OpenAIResponse:
        """
        Test the connection to OpenAI API.
        
        Returns:
            OpenAIResponse: Test response
        """
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello, GitBridge! Please respond with 'OpenAI connection successful.'"}],
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
                provider='openai',
                latency=response_time,
                success=True
            )
            
            result = OpenAIResponse(
                content=content,
                usage=usage,
                model=self.model,
                response_time=response_time,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={'test_connection': True}
            )
            
            logger.info(f"[P20P7S2T1] OpenAI connection test successful - {response_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"[P20P7S2T1] OpenAI connection test failed: {str(e)}")
            raise
            
    def generate_response(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_message: Optional[str] = None
    ) -> OpenAIResponse:
        """
        Generate a response from OpenAI.
        
        Args:
            prompt: Input prompt for OpenAI
            max_tokens: Maximum tokens for response (defaults to self.max_tokens)
            temperature: Temperature for response (defaults to self.temperature)
            system_message: Optional system message
            
        Returns:
            OpenAIResponse: Generated response
        """
        try:
            start_time = time.time()
            
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature
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
                provider='openai',
                latency=response_time,
                success=True
            )
            
            result = OpenAIResponse(
                content=content,
                usage=usage,
                model=self.model,
                response_time=response_time,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={'prompt_length': len(prompt)}
            )
            
            logger.info(f"[P20P7S2T1] OpenAI response generated - {response_time:.2f}s, {usage['total_tokens']} tokens")
            return result
            
        except Exception as e:
            logger.error(f"[P20P7S2T1] OpenAI response generation failed: {str(e)}")
            raise
            
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get available OpenAI models.
        
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
            logger.error(f"[P20P7S2T1] Failed to get OpenAI models: {str(e)}")
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

def test_openai_connection():
    """Test OpenAI connection and model validation."""
    try:
        client = OpenAIClient()
        response = client.test_connection()
        print(f"✅ OpenAI connection successful")
        print(f"   Model: {response.model}")
        print(f"   Response time: {response.response_time:.2f}s")
        print(f"   Tokens used: {response.usage['total_tokens']}")
        return True
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

def main():
    """Main function for testing."""
    print("Testing OpenAI Client...")
    success = test_openai_connection()
    if success:
        print("OpenAI client is ready for use!")
    else:
        print("OpenAI client needs configuration.")
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 