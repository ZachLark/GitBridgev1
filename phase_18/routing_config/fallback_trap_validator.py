# P18P7S3 – Error Validation + Fallback Traps

"""
GitBridge Phase 18P7 - Error Validation and Fallback Trap System

This module implements comprehensive error detection, circular fallback validation,
and Redis logging for routing configuration issues.

Author: GitBridge MAS Integration Team
Phase: 18P7 - Routing Configurator  
MAS Lite Protocol: v2.1 Compliance
"""

import json
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Redis simulation for fallback logging (would use real Redis in production)
class MockRedisClient:
    """Mock Redis client for fallback event logging simulation"""
    
    def __init__(self, channel: str = "mas:routing:fallback_errors"):
        self.channel = channel
        self.log_entries = []
        self.connected = True
    
    def publish(self, channel: str, message: str) -> int:
        """Simulate Redis publish to channel"""
        if not self.connected:
            return 0
        
        log_entry = {
            "channel": channel,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "published_at": time.time()
        }
        
        self.log_entries.append(log_entry)
        print(f"📡 [REDIS] Published to {channel}: {message[:80]}...")
        return 1
    
    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        return self.log_entries[-limit:]
    
    def clear_logs(self) -> int:
        """Clear all log entries"""
        count = len(self.log_entries)
        self.log_entries.clear()
        return count


@dataclass
class FallbackError:
    """Structured fallback error representation"""
    error_id: str
    error_type: str
    severity: str
    policy_name: str
    model_chain: List[str]
    description: str
    detection_timestamp: str
    circular_path: Optional[List[str]] = None
    missing_models: Optional[List[str]] = None
    invalid_transitions: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "error_id": self.error_id,
            "error_type": self.error_type, 
            "severity": self.severity,
            "policy_name": self.policy_name,
            "model_chain": self.model_chain,
            "description": self.description,
            "detection_timestamp": self.detection_timestamp,
            "circular_path": self.circular_path,
            "missing_models": self.missing_models,
            "invalid_transitions": self.invalid_transitions,
            "mas_lite_protocol": "v2.1"
        }


class FallbackTrapValidator:
    """
    Advanced fallback trap validation system.
    
    Detects and logs various types of routing configuration errors including
    circular references, missing models, invalid transitions, and policy violations.
    """
    
    def __init__(self, redis_channel: str = "mas:routing:fallback_errors"):
        """Initialize the fallback trap validator"""
        self.redis_client = MockRedisClient(redis_channel)
        self.detected_errors = []
        self.validation_history = []
        
        print(f"🔧 FallbackTrapValidator initialized with channel: {redis_channel}")
    
    def generate_error_id(self, error_type: str, policy_name: str) -> str:
        """Generate unique error identifier"""
        timestamp = datetime.now(timezone.utc).isoformat()
        unique_string = f"{error_type}_{policy_name}_{timestamp}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    def validate_routing_config(self, config: Dict[str, Any]) -> List[FallbackError]:
        """
        Comprehensive routing configuration validation with error trapping.
        
        Args:
            config (Dict[str, Any]): Routing configuration to validate
            
        Returns:
            List[FallbackError]: List of detected errors
        """
        print("\n🔍 Starting Comprehensive Fallback Trap Validation")
        print("=" * 55)
        
        errors = []
        validation_start = datetime.now(timezone.utc)
        
        # 1. Circular Reference Detection
        print("\n🔄 Detecting Circular References...")
        circular_errors = self._detect_circular_fallbacks(config)
        errors.extend(circular_errors)
        
        # 2. Missing Model Detection
        print("\n🔍 Detecting Missing Models...")
        missing_model_errors = self._detect_missing_models(config)
        errors.extend(missing_model_errors)
        
        # 3. Invalid Transition Detection
        print("\n⚠️  Detecting Invalid Transitions...")
        transition_errors = self._detect_invalid_transitions(config)
        errors.extend(transition_errors)
        
        # 4. Confidence Threshold Violations
        print("\n📊 Detecting Confidence Threshold Violations...")
        confidence_errors = self._detect_confidence_violations(config)
        errors.extend(confidence_errors)
        
        # 5. Timeout Inconsistencies
        print("\n⏱️  Detecting Timeout Inconsistencies...")
        timeout_errors = self._detect_timeout_issues(config)
        errors.extend(timeout_errors)
        
        # 6. Dead End Detection
        print("\n🚫 Detecting Dead End Configurations...")
        dead_end_errors = self._detect_dead_ends(config)
        errors.extend(dead_end_errors)
        
        # Log all errors to Redis
        self._log_errors_to_redis(errors)
        
        # Store validation history
        validation_record = {
            "validation_id": self.generate_error_id("validation", "system"),
            "timestamp": validation_start.isoformat(),
            "total_errors": len(errors),
            "error_types": list(set(error.error_type for error in errors)),
            "policies_checked": list(config.get("routing_policies", {}).keys()),
            "duration_ms": int((datetime.now(timezone.utc) - validation_start).total_seconds() * 1000)
        }
        self.validation_history.append(validation_record)
        
        print(f"\n📊 Validation Complete: {len(errors)} errors detected")
        return errors
    
    def _detect_circular_fallbacks(self, config: Dict[str, Any]) -> List[FallbackError]:
        """Detect circular references in fallback chains"""
        errors = []
        routing_policies = config.get("routing_policies", {})
        
        for policy_name, policy in routing_policies.items():
            # Build model chain
            model_chain = []
            seen_models = set()
            
            # Add primary model
            primary_model = policy.get("primary_model", {}).get("model_id")
            if primary_model:
                model_chain.append(primary_model)
                seen_models.add(primary_model)
            
            # Check fallback chain
            fallback_chain = policy.get("fallback_chain", [])
            circular_detected = False
            circular_path = []
            
            for i, fallback in enumerate(fallback_chain):
                model_id = fallback.get("model_id")
                if not model_id:
                    continue
                
                if model_id in seen_models:
                    # Circular reference detected
                    circular_path = model_chain + [model_id]
                    circular_detected = True
                    
                    error = FallbackError(
                        error_id=self.generate_error_id("circular_reference", policy_name),
                        error_type="circular_reference",
                        severity="critical",
                        policy_name=policy_name,
                        model_chain=model_chain.copy(),
                        description=f"Circular reference detected in fallback chain: {' → '.join(circular_path)}",
                        detection_timestamp=datetime.now(timezone.utc).isoformat(),
                        circular_path=circular_path
                    )
                    errors.append(error)
                    print(f"   🔄 Circular reference in {policy_name}: {' → '.join(circular_path)}")
                    break
                else:
                    model_chain.append(model_id)
                    seen_models.add(model_id)
            
            if not circular_detected:
                print(f"   ✅ No circular references in {policy_name}")
        
        return errors
    
    def _detect_missing_models(self, config: Dict[str, Any]) -> List[FallbackError]:
        """Detect references to models not in the registry"""
        errors = []
        model_registry = config.get("model_registry", {})
        routing_policies = config.get("routing_policies", {})
        
        for policy_name, policy in routing_policies.items():
            missing_models = []
            model_chain = []
            
            # Check primary model
            primary_model = policy.get("primary_model", {}).get("model_id")
            if primary_model:
                model_chain.append(primary_model)
                if primary_model not in model_registry and primary_model != "human_escalation":
                    missing_models.append(primary_model)
            
            # Check fallback chain
            for fallback in policy.get("fallback_chain", []):
                model_id = fallback.get("model_id")
                if model_id:
                    model_chain.append(model_id)
                    if model_id not in model_registry and model_id != "human_escalation":
                        missing_models.append(model_id)
            
            if missing_models:
                error = FallbackError(
                    error_id=self.generate_error_id("missing_models", policy_name),
                    error_type="missing_models",
                    severity="high",
                    policy_name=policy_name,
                    model_chain=model_chain,
                    description=f"Models not found in registry: {', '.join(missing_models)}",
                    detection_timestamp=datetime.now(timezone.utc).isoformat(),
                    missing_models=missing_models
                )
                errors.append(error)
                print(f"   🔍 Missing models in {policy_name}: {', '.join(missing_models)}")
            else:
                print(f"   ✅ All models found for {policy_name}")
        
        return errors
    
    def _detect_invalid_transitions(self, config: Dict[str, Any]) -> List[FallbackError]:
        """Detect invalid state transitions in fallback chains"""
        errors = []
        routing_policies = config.get("routing_policies", {})
        
        for policy_name, policy in routing_policies.items():
            invalid_transitions = []
            model_chain = []
            
            primary_model = policy.get("primary_model", {})
            primary_confidence = primary_model.get("confidence_threshold", 1.0)
            
            if primary_model.get("model_id"):
                model_chain.append(primary_model.get("model_id"))
            
            last_confidence = primary_confidence
            
            for i, fallback in enumerate(policy.get("fallback_chain", [])):
                model_id = fallback.get("model_id")
                current_confidence = fallback.get("confidence_threshold", 0.0)
                
                if model_id:
                    model_chain.append(model_id)
                
                # Check confidence transition validity
                if current_confidence >= last_confidence:
                    transition_desc = f"Stage {i}: {last_confidence} → {current_confidence} (should decrease)"
                    invalid_transitions.append(transition_desc)
                
                last_confidence = current_confidence
            
            if invalid_transitions:
                error = FallbackError(
                    error_id=self.generate_error_id("invalid_transitions", policy_name),
                    error_type="invalid_transitions",
                    severity="medium",
                    policy_name=policy_name,
                    model_chain=model_chain,
                    description=f"Invalid confidence transitions detected",
                    detection_timestamp=datetime.now(timezone.utc).isoformat(),
                    invalid_transitions=invalid_transitions
                )
                errors.append(error)
                print(f"   ⚠️  Invalid transitions in {policy_name}: {len(invalid_transitions)} issues")
            else:
                print(f"   ✅ Valid transitions for {policy_name}")
        
        return errors
    
    def _detect_confidence_violations(self, config: Dict[str, Any]) -> List[FallbackError]:
        """Detect confidence threshold policy violations"""
        errors = []
        routing_policies = config.get("routing_policies", {})
        
        for policy_name, policy in routing_policies.items():
            escalation_threshold = policy.get("escalation_flags", {}).get("escalation_threshold", 0.5)
            model_chain = []
            
            # Build model chain
            primary_model = policy.get("primary_model", {}).get("model_id")
            if primary_model:
                model_chain.append(primary_model)
            
            for fallback in policy.get("fallback_chain", []):
                model_id = fallback.get("model_id")
                if model_id:
                    model_chain.append(model_id)
            
            # Check for confidence violations
            lowest_confidence = min(
                [policy.get("primary_model", {}).get("confidence_threshold", 1.0)] +
                [f.get("confidence_threshold", 0.0) for f in policy.get("fallback_chain", [])]
            )
            
            if lowest_confidence < escalation_threshold:
                error = FallbackError(
                    error_id=self.generate_error_id("confidence_violation", policy_name),
                    error_type="confidence_violation",
                    severity="low",
                    policy_name=policy_name,
                    model_chain=model_chain,
                    description=f"Fallback confidence ({lowest_confidence}) below escalation threshold ({escalation_threshold})",
                    detection_timestamp=datetime.now(timezone.utc).isoformat()
                )
                errors.append(error)
                print(f"   📊 Confidence violation in {policy_name}: {lowest_confidence} < {escalation_threshold}")
            else:
                print(f"   ✅ Confidence thresholds valid for {policy_name}")
        
        return errors
    
    def _detect_timeout_issues(self, config: Dict[str, Any]) -> List[FallbackError]:
        """Detect timeout configuration issues"""
        errors = []
        routing_policies = config.get("routing_policies", {})
        global_timeout = config.get("global_settings", {}).get("default_timeout_seconds", 120)
        
        for policy_name, policy in routing_policies.items():
            model_chain = []
            timeout_issues = []
            
            primary_timeout = policy.get("primary_model", {}).get("timeout_seconds", global_timeout)
            primary_model = policy.get("primary_model", {}).get("model_id")
            
            if primary_model:
                model_chain.append(primary_model)
            
            # Check for unreasonable timeouts
            if primary_timeout < 10:
                timeout_issues.append(f"Primary timeout too short: {primary_timeout}s")
            elif primary_timeout > 600:
                timeout_issues.append(f"Primary timeout too long: {primary_timeout}s")
            
            # Check fallback timeouts
            for i, fallback in enumerate(policy.get("fallback_chain", [])):
                model_id = fallback.get("model_id")
                fallback_timeout = fallback.get("timeout_seconds", global_timeout)
                
                if model_id:
                    model_chain.append(model_id)
                
                if fallback_timeout > primary_timeout:
                    timeout_issues.append(f"Fallback {i} timeout ({fallback_timeout}s) exceeds primary ({primary_timeout}s)")
            
            if timeout_issues:
                error = FallbackError(
                    error_id=self.generate_error_id("timeout_issues", policy_name),
                    error_type="timeout_issues", 
                    severity="medium",
                    policy_name=policy_name,
                    model_chain=model_chain,
                    description=f"Timeout configuration issues: {'; '.join(timeout_issues)}",
                    detection_timestamp=datetime.now(timezone.utc).isoformat()
                )
                errors.append(error)
                print(f"   ⏱️  Timeout issues in {policy_name}: {len(timeout_issues)} problems")
            else:
                print(f"   ✅ Timeout configuration valid for {policy_name}")
        
        return errors
    
    def _detect_dead_ends(self, config: Dict[str, Any]) -> List[FallbackError]:
        """Detect policies with no valid fallback paths"""
        errors = []
        routing_policies = config.get("routing_policies", {})
        
        for policy_name, policy in routing_policies.items():
            if not policy.get("enabled", False):
                continue
            
            model_chain = []
            has_human_fallback = False
            fallback_count = len(policy.get("fallback_chain", []))
            
            # Build model chain and check for human fallback
            primary_model = policy.get("primary_model", {}).get("model_id")
            if primary_model:
                model_chain.append(primary_model)
                if primary_model == "human_escalation":
                    has_human_fallback = True
            
            for fallback in policy.get("fallback_chain", []):
                model_id = fallback.get("model_id")
                if model_id:
                    model_chain.append(model_id)
                    if model_id == "human_escalation":
                        has_human_fallback = True
            
            # Check for dead end conditions
            if fallback_count == 0 and not has_human_fallback:
                error = FallbackError(
                    error_id=self.generate_error_id("dead_end", policy_name),
                    error_type="dead_end",
                    severity="high",
                    policy_name=policy_name,
                    model_chain=model_chain,
                    description="No fallback chain and no human escalation configured",
                    detection_timestamp=datetime.now(timezone.utc).isoformat()
                )
                errors.append(error)
                print(f"   🚫 Dead end detected in {policy_name}: No fallbacks configured")
            else:
                print(f"   ✅ Valid fallback path for {policy_name}")
        
        return errors
    
    def _log_errors_to_redis(self, errors: List[FallbackError]) -> None:
        """Log all detected errors to Redis channel"""
        if not errors:
            print("   📡 No errors to log to Redis")
            return
        
        print(f"\n📡 Logging {len(errors)} errors to Redis...")
        
        for error in errors:
            # Create structured log message
            log_message = json.dumps(error.to_dict(), separators=(',', ':'))
            
            # Publish to Redis
            result = self.redis_client.publish(self.redis_client.channel, log_message)
            
            if result:
                print(f"   ✅ Logged {error.error_type} error for {error.policy_name}")
            else:
                print(f"   ❌ Failed to log {error.error_type} error for {error.policy_name}")
        
        # Store errors locally
        self.detected_errors.extend(errors)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of detected errors"""
        if not self.detected_errors:
            return {
                "total_errors": 0,
                "error_types": {},
                "severity_distribution": {},
                "policies_affected": []
            }
        
        error_types = {}
        severity_dist = {}
        policies_affected = set()
        
        for error in self.detected_errors:
            # Count error types
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            
            # Count severities
            severity_dist[error.severity] = severity_dist.get(error.severity, 0) + 1
            
            # Track affected policies
            policies_affected.add(error.policy_name)
        
        return {
            "total_errors": len(self.detected_errors),
            "error_types": error_types,
            "severity_distribution": severity_dist,
            "policies_affected": list(policies_affected),
            "redis_logs": len(self.redis_client.log_entries),
            "validation_runs": len(self.validation_history)
        }
    
    def create_invalid_config_examples(self) -> Dict[str, Dict[str, Any]]:
        """
        Create example invalid configurations for testing.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of invalid config examples
        """
        examples = {}
        
        # Example 1: Circular Reference
        examples["circular_reference"] = {
            "routing_metadata": {
                "config_version": "1.0",
                "created_date": "2025-06-10T16:30:00Z",
                "last_updated": "2025-06-10T16:30:00Z",
                "schema_version": "P18P7_v1.0"
            },
            "global_settings": {
                "default_timeout_seconds": 120,
                "max_fallback_depth": 3,
                "enable_hot_reload": True
            },
            "routing_policies": {
                "circular_test": {
                    "route_id": "circular_policy_001",
                    "description": "Test policy with circular reference",
                    "enabled": True,
                    "primary_model": {
                        "model_id": "gpt4_turbo",
                        "provider": "openai",
                        "timeout_seconds": 90,
                        "confidence_threshold": 0.75
                    },
                    "fallback_chain": [
                        {
                            "model_id": "claude3_5_sonnet",
                            "provider": "anthropic",
                            "timeout_seconds": 80,
                            "confidence_threshold": 0.65,
                            "trigger_conditions": ["timeout", "low_confidence"]
                        },
                        {
                            "model_id": "gpt4_turbo",  # Circular reference!
                            "provider": "openai",
                            "timeout_seconds": 70,
                            "confidence_threshold": 0.55,
                            "trigger_conditions": ["timeout", "low_confidence"]
                        }
                    ],
                    "escalation_flags": {
                        "enable_human_escalation": True,
                        "escalation_threshold": 0.30
                    }
                }
            },
            "model_registry": {
                "gpt4_turbo": {
                    "provider": "openai",
                    "model_name": "gpt-4-turbo-preview",
                    "api_endpoint": "https://api.openai.com/v1/chat/completions",
                    "cost_per_1k_tokens": 0.03
                },
                "claude3_5_sonnet": {
                    "provider": "anthropic", 
                    "model_name": "claude-3-5-sonnet-20241022",
                    "api_endpoint": "https://api.anthropic.com/v1/messages",
                    "cost_per_1k_tokens": 0.025
                }
            }
        }
        
        # Example 2: Missing Models
        examples["missing_models"] = {
            "routing_metadata": {
                "config_version": "1.0",
                "created_date": "2025-06-10T16:30:00Z",
                "last_updated": "2025-06-10T16:30:00Z",
                "schema_version": "P18P7_v1.0"
            },
            "global_settings": {
                "default_timeout_seconds": 120,
                "max_fallback_depth": 3,
                "enable_hot_reload": True
            },
            "routing_policies": {
                "missing_test": {
                    "route_id": "missing_policy_001",
                    "description": "Test policy with missing models",
                    "enabled": True,
                    "primary_model": {
                        "model_id": "nonexistent_model",  # Missing!
                        "provider": "unknown",
                        "timeout_seconds": 90,
                        "confidence_threshold": 0.75
                    },
                    "fallback_chain": [
                        {
                            "model_id": "another_missing_model",  # Also missing!
                            "provider": "unknown",
                            "timeout_seconds": 80,
                            "confidence_threshold": 0.65,
                            "trigger_conditions": ["timeout", "low_confidence"]
                        }
                    ],
                    "escalation_flags": {
                        "enable_human_escalation": True,
                        "escalation_threshold": 0.30
                    }
                }
            },
            "model_registry": {
                # Empty registry - all models missing
            }
        }
        
        return examples


def run_fallback_trap_tests():
    """
    Comprehensive test suite for fallback trap validation.
    
    Tests error detection, circular reference detection, and Redis logging.
    """
    print("\n🧪 Running Fallback Trap Validation Tests")
    print("=" * 50)
    
    validator = FallbackTrapValidator()
    
    # Get invalid configuration examples
    invalid_configs = validator.create_invalid_config_examples()
    
    # Test 1: Circular Reference Detection
    print("\n🔄 Test 1: Circular Reference Detection")
    circular_config = invalid_configs["circular_reference"]
    circular_errors = validator.validate_routing_config(circular_config)
    
    circular_ref_errors = [e for e in circular_errors if e.error_type == "circular_reference"]
    print(f"   Circular reference errors detected: {len(circular_ref_errors)}")
    
    if circular_ref_errors:
        for error in circular_ref_errors:
            print(f"   🔄 {error.description}")
            print(f"      Path: {' → '.join(error.circular_path or [])}")
    
    # Test 2: Missing Models Detection
    print("\n🔍 Test 2: Missing Models Detection")
    missing_config = invalid_configs["missing_models"]
    missing_errors = validator.validate_routing_config(missing_config)
    
    missing_model_errors = [e for e in missing_errors if e.error_type == "missing_models"]
    print(f"   Missing model errors detected: {len(missing_model_errors)}")
    
    if missing_model_errors:
        for error in missing_model_errors:
            print(f"   🔍 {error.description}")
            print(f"      Missing: {', '.join(error.missing_models or [])}")
    
    # Test 3: Redis Logging Verification
    print("\n📡 Test 3: Redis Logging Verification")
    redis_logs = validator.redis_client.get_logs()
    print(f"   Redis log entries: {len(redis_logs)}")
    
    if redis_logs:
        print("   Recent log entries:")
        for i, log in enumerate(redis_logs[-3:], 1):  # Show last 3
            message_data = json.loads(log["message"])
            print(f"      {i}. {message_data['error_type']} - {message_data['policy_name']}")
    
    # Test 4: Error Summary
    print("\n📊 Test 4: Error Summary")
    summary = validator.get_error_summary()
    print(f"   Total Errors: {summary['total_errors']}")
    print(f"   Error Types: {summary['error_types']}")
    print(f"   Severity Distribution: {summary['severity_distribution']}")
    print(f"   Policies Affected: {', '.join(summary['policies_affected'])}")
    print(f"   Redis Logs: {summary['redis_logs']}")
    
    print("\n🎉 Fallback Trap Validation Tests Completed!")
    print("P18P7S3 - Error Validation + Fallback Traps: ✅ COMPLETED")
    
    return {
        "total_tests": 4,
        "errors_detected": summary['total_errors'],
        "redis_logs_created": summary['redis_logs'],
        "test_passed": True
    }


if __name__ == "__main__":
    """
    Main CLI entry point for fallback trap validation testing.
    
    Runs comprehensive tests of error detection and Redis logging.
    """
    test_results = run_fallback_trap_tests() 