#!/usr/bin/env python3
"""
Configuration validator for GitBridge webhook system.
Validates the webhook_config.yaml file for correctness and completeness.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Union
import yaml
from pydantic import BaseModel, Field, validator
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class RedisConfig(BaseModel):
    """Redis configuration validation model."""
    host: str
    port: int
    db: int

    @validator('port')
    def validate_port(cls, v):
        if not 0 <= v <= 65535:
            raise ValueError('Port must be between 0 and 65535')
        return v

class RateLimiterConfig(BaseModel):
    """Rate limiter configuration validation model."""
    enabled: bool
    backend: str
    redis: RedisConfig
    limits: Dict[str, int]
    fallback: Dict[str, Union[bool, str]]

    @validator('backend')
    def validate_backend(cls, v):
        if v not in ['redis', 'memory']:
            raise ValueError('Backend must be either redis or memory')
        return v

class SecurityConfig(BaseModel):
    """Security configuration validation model."""
    enabled: bool
    ip_whitelist: Dict[str, Union[bool, int]]
    signature_validation: Dict[str, Union[bool, str]]
    audit: Dict[str, Union[bool, int]]

    @validator('signature_validation')
    def validate_signature_algo(cls, v):
        if v.get('algorithm') not in ['sha256', 'sha512']:
            raise ValueError('Signature algorithm must be sha256 or sha512')
        return v

class EventProcessorConfig(BaseModel):
    """Event processor configuration validation model."""
    enabled: bool
    queue: Dict[str, Union[str, int]]
    workers: Dict[str, int]
    filters: List[Dict[str, Union[str, List[str]]]]

class PerformanceMonitorConfig(BaseModel):
    """Performance monitor configuration validation model."""
    enabled: bool
    metrics: Dict[str, Dict[str, Union[bool, int]]]
    alerts: Dict[str, Union[bool, List[str], Dict[str, float]]]

class CollaborationConfig(BaseModel):
    """Collaboration features configuration validation model."""
    enabled: bool
    notifications: Dict[str, Dict[str, Union[bool, List[str], Dict[str, Union[str, int, bool]]]]]
    approvals: Dict[str, Union[bool, int]]

class DeveloperToolsConfig(BaseModel):
    """Developer tools configuration validation model."""
    enabled: bool
    webhook_tester: Dict[str, bool]
    event_replay: Dict[str, Union[bool, int]]

class MASIntegrationConfig(BaseModel):
    """MAS integration configuration validation model."""
    enabled: bool
    protocol_version: str
    task_generation: Dict[str, Union[bool, int]]
    agent_communication: Dict[str, int]

    @validator('protocol_version')
    def validate_protocol_version(cls, v):
        if v != "2.1":
            raise ValueError('Protocol version must be 2.1')
        return v

class SystemConfig(BaseModel):
    """System configuration validation model."""
    environment: str
    debug: bool
    log_level: str

    @validator('environment')
    def validate_environment(cls, v):
        if v not in ['development', 'staging', 'production']:
            raise ValueError('Environment must be development, staging, or production')
        return v

    @validator('log_level')
    def validate_log_level(cls, v):
        if v not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError('Invalid log level')
        return v

class WebhookConfig(BaseModel):
    """Main configuration validation model."""
    version: str
    system: SystemConfig
    rate_limiter: RateLimiterConfig
    security: SecurityConfig
    event_processor: EventProcessorConfig
    performance_monitor: PerformanceMonitorConfig
    collaboration: CollaborationConfig
    developer_tools: DeveloperToolsConfig
    mas_integration: MASIntegrationConfig
    profiles: Dict[str, Dict]

def validate_config(config_path: Path) -> Optional[WebhookConfig]:
    """
    Validate the webhook configuration file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Optional[WebhookConfig]: Validated configuration object if successful
    """
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Validate base configuration
        config = WebhookConfig(**config_data)
        
        # Additional validation logic
        environment = config.system.environment
        if environment == 'production':
            if config.system.debug:
                logger.warning('Debug mode is enabled in production environment')
            if not config.security.ip_whitelist['enabled']:
                logger.error('IP whitelist must be enabled in production')
                return None
        
        # Validate profile overrides
        for profile_name, profile_data in config.profiles.items():
            try:
                # Merge profile with base config and validate
                merged_config = {**config_data}
                merged_config.update(profile_data)
                WebhookConfig(**merged_config)
            except Exception as e:
                logger.error(f'Invalid profile {profile_name}: {str(e)}')
                return None
        
        logger.info('Configuration validation successful')
        return config
        
    except FileNotFoundError:
        logger.error(f'Configuration file not found: {config_path}')
    except yaml.YAMLError as e:
        logger.error(f'Invalid YAML format: {str(e)}')
    except Exception as e:
        logger.error(f'Validation error: {str(e)}')
    
    return None

def main():
    """Main entry point for the configuration validator."""
    config_path = Path(__file__).parent / 'webhook_config.yaml'
    config = validate_config(config_path)
    
    if config is None:
        sys.exit(1)
    
    # Output validated configuration details
    logger.info(f'Environment: {config.system.environment}')
    logger.info(f'MAS Protocol Version: {config.mas_integration.protocol_version}')
    logger.info(f'Available profiles: {", ".join(config.profiles.keys())}')

if __name__ == '__main__':
    main() 