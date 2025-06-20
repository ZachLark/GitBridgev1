#!/usr/bin/env python3
"""
GitBridge GPT-4o Test Client
Task: P20P2S1 - GPT-4o Test Client (Python)

This module provides a test client for validating OpenAI GPT-4o API integration.
It includes comprehensive error handling, modular design, and extensibility
for future webhook triggers and Cursor log integrations.

Author: GitBridge Development Team
Date: 2025-01-11
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import time

# Third-party imports
import openai
from dotenv import load_dotenv
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class GPT4oConfig:
    """Configuration class for GPT-4o API settings."""
    api_key: str
    model: str
    project: str
    max_retries: int = 3
    timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 1000


@dataclass
class GPT4oResponse:
    """Response wrapper for GPT-4o API calls."""
    content: str
    model: str
    usage: Dict[str, Any]
    finish_reason: str
    response_time: float
    success: bool
    error_message: Optional[str] = None


class GPT4oError(Exception):
    """Custom exception for GPT-4o related errors."""
    pass


class GPT4oClient:
    """
    Modular GPT-4o client with comprehensive error handling and extensibility.
    
    This class provides a foundation for:
    - Direct API testing (current task)
    - Webhook integration (P20P3)
    - Cursor log integration (P20P4)
    - SmartRouter integration (P20P7)
    """
    
    def __init__(self, config: GPT4oConfig):
        """Initialize the GPT-4o client with configuration."""
        self.config = config
        import openai
        openai.api_key = config.api_key
        self.request_count = 0
        self.error_count = 0
        
    def validate_config(self) -> bool:
        """Validate the configuration before making API calls."""
        if not self.config.api_key:
            raise GPT4oError("OPENAI_API_KEY is required")
        
        if not self.config.api_key.startswith("sk-"):
            raise GPT4oError("Invalid API key format")
            
        if not self.config.model:
            raise GPT4oError("Model name is required")
            
        return True
    
    def _handle_rate_limit(self, retry_count: int) -> None:
        """Handle rate limiting with exponential backoff."""
        wait_time = min(2 ** retry_count, 60)  # Max 60 seconds
        logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
        time.sleep(wait_time)
    
    def _handle_api_error(self, error: Exception, retry_count: int) -> None:
        """Handle different types of API errors."""
        error_msg = str(error)
        
        if "401" in error_msg or "authentication" in error_msg.lower():
            raise GPT4oError("Authentication failed. Check your API key.")
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            if retry_count < self.config.max_retries:
                self._handle_rate_limit(retry_count)
                return
            else:
                raise GPT4oError("Rate limit exceeded after retries.")
        elif "model" in error_msg.lower():
            raise GPT4oError(f"Model '{self.config.model}' not found or not available.")
        elif "quota" in error_msg.lower():
            raise GPT4oError("API quota exceeded.")
        else:
            raise GPT4oError(f"API error: {error_msg}")
    
    def send_message(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str = "You are a helpful assistant."
    ) -> GPT4oResponse:
        """
        Send a message to GPT-4o and return the response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: System prompt to prepend to messages
            
        Returns:
            GPT4oResponse object with the API response
        """
        start_time = time.time()
        
        # Validate configuration
        self.validate_config()
        
        # Prepare messages with system prompt
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Retry logic
        for retry_count in range(self.config.max_retries + 1):
            try:
                logger.info(f"Sending request to {self.config.model} (attempt {retry_count + 1})")
                
                response = openai.chat.completions.create(
                    model=self.config.model,
                    messages=full_messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                
                response_time = time.time() - start_time
                self.request_count += 1
                
                logger.info(f"✅ Successfully received response in {response_time:.2f}s")
                
                return GPT4oResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    usage=response.usage.model_dump() if response.usage else {},
                    finish_reason=response.choices[0].finish_reason,
                    response_time=response_time,
                    success=True
                )
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ Error on attempt {retry_count + 1}: {str(e)}")
                
                if retry_count < self.config.max_retries:
                    self._handle_api_error(e, retry_count)
                else:
                    response_time = time.time() - start_time
                    return GPT4oResponse(
                        content="",
                        model=self.config.model,
                        usage={},
                        finish_reason="error",
                        response_time=response_time,
                        success=False,
                        error_message=str(e)
                    )
    
    def test_connection(self) -> GPT4oResponse:
        """Test the connection with a simple message."""
        test_messages = [
            {"role": "user", "content": "Hello! Please respond with 'GitBridge GPT-4o connection test successful' and provide a brief status of your capabilities."}
        ]
        
        return self.send_message(
            messages=test_messages,
            system_prompt="You are a helpful assistant for the GitBridge project. Provide concise, technical responses."
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics for monitoring."""
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "success_rate": (self.request_count - self.error_count) / max(self.request_count, 1),
            "model": self.config.model,
            "project": self.config.project
        }


def load_environment_config() -> GPT4oConfig:
    """Load configuration from environment variables."""
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    project = os.getenv("OPENAI_PROJECT", "gbtest")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    return GPT4oConfig(
        api_key=api_key,
        model=model,
        project=project
    )


def print_response(response: GPT4oResponse) -> None:
    """Print the response in a formatted way."""
    print("\n" + "="*60)
    print("GPT-4o API Response")
    print("="*60)
    
    if response.success:
        print(f"✅ Status: Success")
        print(f"🤖 Model: {response.model}")
        print(f"⏱️  Response Time: {response.response_time:.2f}s")
        print(f"📊 Finish Reason: {response.finish_reason}")
        
        if response.usage:
            print(f"📈 Usage: {json.dumps(response.usage, indent=2)}")
        
        print(f"\n💬 Response Content:")
        print("-" * 40)
        print(response.content)
        
    else:
        print(f"❌ Status: Failed")
        print(f"⏱️  Response Time: {response.response_time:.2f}s")
        print(f"🚨 Error: {response.error_message}")
    
    print("="*60)


def main():
    """Main function for CLI execution."""
    print("🚀 GitBridge GPT-4o Test Client")
    print("Task: P20P2S1 - GPT-4o Test Client (Python)")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = load_environment_config()
        print(f"✅ Configuration loaded:")
        print(f"   Model: {config.model}")
        print(f"   Project: {config.project}")
        print(f"   API Key: {config.api_key[:10]}...{config.api_key[-4:]}")
        
        # Initialize client
        print("\n🔧 Initializing GPT-4o client...")
        client = GPT4oClient(config)
        
        # Test connection
        print("\n🧪 Testing GPT-4o connection...")
        response = client.test_connection()
        
        # Print results
        print_response(response)
        
        # Print statistics
        stats = client.get_stats()
        print(f"\n📊 Client Statistics:")
        print(f"   Total Requests: {stats['request_count']}")
        print(f"   Errors: {stats['error_count']}")
        print(f"   Success Rate: {stats['success_rate']:.2%}")
        
        # Exit with appropriate code
        if response.success:
            print("\n🎉 Test completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Test failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"\n💥 Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 