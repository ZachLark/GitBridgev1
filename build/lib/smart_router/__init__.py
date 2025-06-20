#!/usr/bin/env python3
"""
GitBridge SmartRouter Module
Task: P20P7S3 - SmartRouter Core Logic Implementation

Intelligent arbitration system for routing between AI providers.
"""

from .smart_router import (
    SmartRouter,
    SmartRouterResponse,
    RoutingStrategy,
    ProviderType,
    RoutingDecision,
    ProviderMetrics
)

__version__ = "1.0.0"
__author__ = "GitBridge Development Team"
__all__ = [
    "SmartRouter",
    "SmartRouterResponse", 
    "RoutingStrategy",
    "ProviderType",
    "RoutingDecision",
    "ProviderMetrics"
] 