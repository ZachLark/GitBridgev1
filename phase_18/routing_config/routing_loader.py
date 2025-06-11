# P18P7S1 – Routing Configuration Loader

"""
GitBridge Phase 18P7 - Routing Configuration Loader

This module handles loading, validating, and managing AI routing configurations
for the GitBridge MAS system. Includes JSON schema validation, error detection,
and hot reload capabilities.

Author: GitBridge MAS Integration Team
Phase: 18P7 - Routing Configurator
MAS Lite Protocol: v2.1 Compliance
"""

import json
import os
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Built-in validation without external dependencies
JSONSCHEMA_AVAILABLE = False  # Using built-in validation instead


@dataclass
class RoutingConfigValidationResult:
    """Results of routing configuration validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    circular_references: List[str] = field(default_factory=list)
    missing_models: List[str] = field(default_factory=list)
    validation_timestamp: str = ""
    
    def __post_init__(self):
        if not self.validation_timestamp:
            self.validation_timestamp = datetime.now(timezone.utc).isoformat()


class RoutingConfigLoader:
    """
    Comprehensive routing configuration loader with validation and monitoring.
    
    Handles JSON schema validation, circular reference detection, model registry
    validation, and hot reload capabilities for AI routing configurations.
    """
    
    def __init__(self, config_path: str = "ai_routing_config.json", 
                 schema_path: str = "routing_schema.json"):
        """Initialize the routing configuration loader"""
        self.config_path = Path(config_path)
        self.schema_path = Path(schema_path)
        self.current_config = None
        self.schema = None
        self.file_checksum = None
        self.last_loaded = None
        
        # Load schema if available (for reference, using built-in validation)
        if self.schema_path.exists():
            self._load_schema()
        else:
            print(f"⚠️  Schema file not found at {self.schema_path}, using built-in validation")
        
        print(f"🔧 RoutingConfigLoader initialized for {self.config_path}")
    
    def _load_schema(self) -> bool:
        """Load the JSON schema for reference"""
        try:
            with open(self.schema_path, 'r') as f:
                self.schema = json.load(f)
            
            print(f"✅ Schema reference loaded from {self.schema_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load schema: {e}")
            self.schema = None
            return False
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of configuration file"""
        if not file_path.exists():
            return ""
        
        with open(file_path, 'rb') as f:
            content = f.read()
            return hashlib.md5(content).hexdigest()
    
    def has_file_changed(self) -> bool:
        """Check if configuration file has changed since last load"""
        current_checksum = self._calculate_file_checksum(self.config_path)
        return current_checksum != self.file_checksum
    
    def load_config(self, force_reload: bool = False) -> Tuple[Optional[Dict], RoutingConfigValidationResult]:
        """
        Load routing configuration with validation.
        
        Args:
            force_reload (bool): Force reload even if file hasn't changed
            
        Returns:
            Tuple[Optional[Dict], RoutingConfigValidationResult]: Config and validation results
        """
        if not force_reload and not self.has_file_changed():
            print("📋 Configuration file unchanged, using cached config")
            return self.current_config, RoutingConfigValidationResult(is_valid=True)
        
        print(f"📂 Loading routing configuration from {self.config_path}")
        
        if not self.config_path.exists():
            error = f"Configuration file not found: {self.config_path}"
            print(f"❌ {error}")
            return None, RoutingConfigValidationResult(
                is_valid=False,
                errors=[error]
            )
        
        try:
            # Load JSON configuration
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Update file tracking
            self.file_checksum = self._calculate_file_checksum(self.config_path)
            self.last_loaded = datetime.now(timezone.utc)
            
            # Validate configuration
            validation_result = self.validate_config(config)
            
            if validation_result.is_valid:
                self.current_config = config
                print(f"✅ Configuration loaded successfully")
            else:
                print(f"❌ Configuration validation failed:")
                for error in validation_result.errors:
                    print(f"   - {error}")
            
            return config, validation_result
            
        except json.JSONDecodeError as e:
            error = f"Invalid JSON in configuration file: {e}"
            print(f"❌ {error}")
            return None, RoutingConfigValidationResult(
                is_valid=False,
                errors=[error]
            )
        except Exception as e:
            error = f"Failed to load configuration: {e}"
            print(f"❌ {error}")
            return None, RoutingConfigValidationResult(
                is_valid=False,
                errors=[error]
            )
    
    def validate_config(self, config: Dict[str, Any]) -> RoutingConfigValidationResult:
        """
        Comprehensive validation of routing configuration.
        
        Args:
            config (Dict[str, Any]): Configuration to validate
            
        Returns:
            RoutingConfigValidationResult: Detailed validation results
        """
        result = RoutingConfigValidationResult(is_valid=True)
        
        # 1. Built-in Structure Validation
        structure_errors = self._validate_structure(config)
        if structure_errors:
            result.is_valid = False
            result.errors.extend(structure_errors)
        else:
            print("✅ Configuration structure validation passed")
        
        # 2. Circular Reference Detection
        circular_refs = self._detect_circular_references(config)
        if circular_refs:
            result.is_valid = False
            result.circular_references = circular_refs
            result.errors.extend([f"Circular reference detected: {ref}" for ref in circular_refs])
        
        # 3. Model Registry Validation
        missing_models = self._validate_model_references(config)
        if missing_models:
            result.is_valid = False
            result.missing_models = missing_models
            result.errors.extend([f"Model not found in registry: {model}" for model in missing_models])
        
        # 4. Policy Consistency Validation
        policy_errors = self._validate_policy_consistency(config)
        if policy_errors:
            result.is_valid = False
            result.errors.extend(policy_errors)
        
        # 5. Timeout and Threshold Validation
        threshold_warnings = self._validate_thresholds(config)
        result.warnings.extend(threshold_warnings)
        
        print(f"📊 Validation complete: {len(result.errors)} errors, {len(result.warnings)} warnings")
        return result

    def _validate_structure(self, config: Dict[str, Any]) -> List[str]:
        """Built-in structure validation without external dependencies"""
        errors = []
        
        # Check required top-level sections
        required_sections = ["routing_metadata", "global_settings", "routing_policies", "model_registry"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Validate routing_metadata
        if "routing_metadata" in config:
            metadata = config["routing_metadata"]
            required_metadata = ["config_version", "created_date", "last_updated", "schema_version"]
            for field in required_metadata:
                if field not in metadata:
                    errors.append(f"Missing required field in routing_metadata: {field}")
        
        # Validate global_settings
        if "global_settings" in config:
            settings = config["global_settings"]
            required_settings = ["default_timeout_seconds", "max_fallback_depth", "enable_hot_reload"]
            for field in required_settings:
                if field not in settings:
                    errors.append(f"Missing required field in global_settings: {field}")
            
            # Validate timeout value
            if "default_timeout_seconds" in settings:
                timeout = settings["default_timeout_seconds"]
                if not isinstance(timeout, int) or timeout < 30 or timeout > 600:
                    errors.append("default_timeout_seconds must be integer between 30 and 600")
        
        # Validate routing_policies
        if "routing_policies" in config:
            policies = config["routing_policies"]
            if not isinstance(policies, dict) or len(policies) == 0:
                errors.append("routing_policies must be non-empty dictionary")
            
            for policy_name, policy in policies.items():
                if not isinstance(policy, dict):
                    errors.append(f"Policy {policy_name} must be a dictionary")
                    continue
                
                required_policy_fields = ["route_id", "description", "enabled", "primary_model", "fallback_chain", "escalation_flags"]
                for field in required_policy_fields:
                    if field not in policy:
                        errors.append(f"Missing required field in policy {policy_name}: {field}")
                
                # Validate primary_model structure
                if "primary_model" in policy:
                    primary = policy["primary_model"]
                    required_model_fields = ["model_id", "provider", "timeout_seconds", "confidence_threshold"]
                    for field in required_model_fields:
                        if field not in primary:
                            errors.append(f"Missing required field in {policy_name}.primary_model: {field}")
                
                # Validate fallback_chain structure
                if "fallback_chain" in policy:
                    fallbacks = policy["fallback_chain"]
                    if not isinstance(fallbacks, list):
                        errors.append(f"fallback_chain in policy {policy_name} must be a list")
                    else:
                        for i, fallback in enumerate(fallbacks):
                            if not isinstance(fallback, dict):
                                errors.append(f"Fallback {i} in policy {policy_name} must be a dictionary")
                                continue
                            
                            required_fallback_fields = ["model_id", "provider", "timeout_seconds", "confidence_threshold", "trigger_conditions"]
                            for field in required_fallback_fields:
                                if field not in fallback:
                                    errors.append(f"Missing required field in {policy_name}.fallback_chain[{i}]: {field}")
        
        # Validate model_registry
        if "model_registry" in config:
            registry = config["model_registry"]
            if not isinstance(registry, dict) or len(registry) == 0:
                errors.append("model_registry must be non-empty dictionary")
            
            for model_id, model_info in registry.items():
                if not isinstance(model_info, dict):
                    errors.append(f"Model {model_id} info must be a dictionary")
                    continue
                
                required_model_fields = ["provider", "model_name", "api_endpoint", "cost_per_1k_tokens"]
                for field in required_model_fields:
                    if field not in model_info:
                        errors.append(f"Missing required field in model {model_id}: {field}")
        
        return errors
    
    def _detect_circular_references(self, config: Dict[str, Any]) -> List[str]:
        """Detect circular references in fallback chains"""
        circular_refs = []
        
        routing_policies = config.get("routing_policies", {})
        
        for policy_name, policy in routing_policies.items():
            fallback_chain = policy.get("fallback_chain", [])
            
            # Check for circular references within each fallback chain
            seen_models = set()
            chain_models = []
            
            # Add primary model
            primary_model = policy.get("primary_model", {}).get("model_id")
            if primary_model:
                seen_models.add(primary_model)
                chain_models.append(primary_model)
            
            # Check fallback chain
            for fallback in fallback_chain:
                model_id = fallback.get("model_id")
                if model_id:
                    if model_id in seen_models:
                        circular_ref = f"{policy_name}: {' → '.join(chain_models)} → {model_id}"
                        circular_refs.append(circular_ref)
                        print(f"🔄 Circular reference detected: {circular_ref}")
                    else:
                        seen_models.add(model_id)
                        chain_models.append(model_id)
        
        return circular_refs
    
    def _validate_model_references(self, config: Dict[str, Any]) -> List[str]:
        """Validate that all referenced models exist in model registry"""
        model_registry = config.get("model_registry", {})
        routing_policies = config.get("routing_policies", {})
        
        referenced_models = set()
        missing_models = []
        
        # Collect all referenced models
        for policy_name, policy in routing_policies.items():
            # Primary model
            primary_model = policy.get("primary_model", {}).get("model_id")
            if primary_model:
                referenced_models.add(primary_model)
            
            # Fallback chain models
            for fallback in policy.get("fallback_chain", []):
                fallback_model = fallback.get("model_id")
                if fallback_model:
                    referenced_models.add(fallback_model)
        
        # Check if all referenced models exist in registry
        for model_id in referenced_models:
            if model_id not in model_registry and model_id != "human_escalation":
                missing_models.append(model_id)
                print(f"🔍 Missing model in registry: {model_id}")
        
        return missing_models
    
    def _validate_policy_consistency(self, config: Dict[str, Any]) -> List[str]:
        """Validate policy consistency and logical constraints"""
        errors = []
        routing_policies = config.get("routing_policies", {})
        
        for policy_name, policy in routing_policies.items():
            # Check enabled policies have valid configurations
            if policy.get("enabled", False):
                primary_model = policy.get("primary_model", {})
                
                # Validate confidence thresholds are decreasing in fallback chain
                last_confidence = primary_model.get("confidence_threshold", 1.0)
                
                for i, fallback in enumerate(policy.get("fallback_chain", [])):
                    current_confidence = fallback.get("confidence_threshold", 0.0)
                    
                    if current_confidence >= last_confidence:
                        errors.append(
                            f"Policy {policy_name}: Fallback confidence threshold should decrease "
                            f"(fallback {i}: {current_confidence} >= previous: {last_confidence})"
                        )
                    
                    last_confidence = current_confidence
                
                # Validate timeout consistency
                last_timeout = primary_model.get("timeout_seconds", 0)
                
                for i, fallback in enumerate(policy.get("fallback_chain", [])):
                    current_timeout = fallback.get("timeout_seconds", 0)
                    
                    if current_timeout > last_timeout:
                        errors.append(
                            f"Policy {policy_name}: Fallback timeout should not exceed primary "
                            f"(fallback {i}: {current_timeout} > primary: {last_timeout})"
                        )
        
        return errors
    
    def _validate_thresholds(self, config: Dict[str, Any]) -> List[str]:
        """Validate threshold values and generate warnings for potential issues"""
        warnings = []
        routing_policies = config.get("routing_policies", {})
        
        for policy_name, policy in routing_policies.items():
            escalation_flags = policy.get("escalation_flags", {})
            escalation_threshold = escalation_flags.get("escalation_threshold", 0.5)
            
            # Warn if escalation threshold is very low (might cause excessive escalations)
            if escalation_threshold < 0.2:
                warnings.append(
                    f"Policy {policy_name}: Very low escalation threshold ({escalation_threshold}) "
                    "may cause excessive human escalations"
                )
            
            # Warn if escalation threshold is very high (might miss important escalations)
            if escalation_threshold > 0.8:
                warnings.append(
                    f"Policy {policy_name}: Very high escalation threshold ({escalation_threshold}) "
                    "may miss important escalations"
                )
            
            # Check for reasonable timeout values
            primary_timeout = policy.get("primary_model", {}).get("timeout_seconds", 120)
            if primary_timeout < 30:
                warnings.append(
                    f"Policy {policy_name}: Very short primary timeout ({primary_timeout}s) "
                    "may cause premature fallbacks"
                )
            
            if primary_timeout > 300:
                warnings.append(
                    f"Policy {policy_name}: Very long primary timeout ({primary_timeout}s) "
                    "may cause poor user experience"
                )
        
        return warnings
    
    def get_route_info(self, route_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific route"""
        if not self.current_config:
            return None
        
        routing_policies = self.current_config.get("routing_policies", {})
        return routing_policies.get(route_name)
    
    def list_available_routes(self) -> List[str]:
        """List all available routing policies"""
        if not self.current_config:
            return []
        
        routing_policies = self.current_config.get("routing_policies", {})
        return [
            name for name, policy in routing_policies.items()
            if policy.get("enabled", False)
        ]
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model"""
        if not self.current_config:
            return None
        
        model_registry = self.current_config.get("model_registry", {})
        return model_registry.get(model_id)
    
    def export_config_summary(self) -> Dict[str, Any]:
        """Export a summary of the current configuration"""
        if not self.current_config:
            return {"error": "No configuration loaded"}
        
        routing_policies = self.current_config.get("routing_policies", {})
        model_registry = self.current_config.get("model_registry", {})
        
        summary = {
            "config_metadata": self.current_config.get("routing_metadata", {}),
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "file_checksum": self.file_checksum,
            "total_policies": len(routing_policies),
            "enabled_policies": len([p for p in routing_policies.values() if p.get("enabled", False)]),
            "total_models": len(model_registry),
            "policies": {}
        }
        
        # Add policy summaries
        for name, policy in routing_policies.items():
            fallback_chain = policy.get("fallback_chain", [])
            summary["policies"][name] = {
                "enabled": policy.get("enabled", False),
                "primary_model": policy.get("primary_model", {}).get("model_id"),
                "fallback_count": len(fallback_chain),
                "fallback_models": [f.get("model_id") for f in fallback_chain],
                "escalation_enabled": policy.get("escalation_flags", {}).get("enable_human_escalation", False)
            }
        
        return summary


def run_config_tests():
    """
    Comprehensive test suite for routing configuration loader.
    
    Tests schema validation, circular reference detection, and configuration loading.
    """
    print("\n🧪 Running Routing Configuration Tests")
    print("=" * 50)
    
    loader = RoutingConfigLoader()
    
    # Test 1: Load and validate current configuration
    print("\n📋 Test 1: Loading Current Configuration")
    config, validation_result = loader.load_config()
    
    # Generate summary regardless of validation status
    summary = loader.export_config_summary() if config else None
    
    if validation_result.is_valid:
        print("✅ Configuration loaded and validated successfully")
        
        # Display summary
        if summary:
            print(f"   📊 Summary:")
            print(f"      - Total Policies: {summary['total_policies']}")
            print(f"      - Enabled Policies: {summary['enabled_policies']}")
            print(f"      - Total Models: {summary['total_models']}")
            print(f"      - Available Routes: {', '.join(loader.list_available_routes())}")
    else:
        print("❌ Configuration validation failed")
        for error in validation_result.errors:
            print(f"      - {error}")
    
    # Test 2: Circular Reference Detection
    print("\n🔄 Test 2: Circular Reference Detection")
    if validation_result.circular_references:
        print("⚠️  Circular references detected:")
        for ref in validation_result.circular_references:
            print(f"      - {ref}")
    else:
        print("✅ No circular references detected")
    
    # Test 3: Model Registry Validation
    print("\n🔍 Test 3: Model Registry Validation")
    if validation_result.missing_models:
        print("⚠️  Missing models in registry:")
        for model in validation_result.missing_models:
            print(f"      - {model}")
    else:
        print("✅ All referenced models found in registry")
    
    # Test 4: Individual Route Testing
    print("\n🛤️  Test 4: Individual Route Testing")
    for route_name in loader.list_available_routes():
        route_info = loader.get_route_info(route_name)
        if route_info:
            primary_model = route_info.get("primary_model", {}).get("model_id")
            fallback_count = len(route_info.get("fallback_chain", []))
            print(f"   📍 Route '{route_name}': {primary_model} + {fallback_count} fallbacks")
    
    # Test 5: File Change Detection
    print("\n📁 Test 5: File Change Detection")
    file_changed = loader.has_file_changed()
    print(f"   File changed since last load: {'Yes' if file_changed else 'No'}")
    
    print(f"\n📊 Test Summary:")
    print(f"   Configuration Valid: {'✅ Yes' if validation_result.is_valid else '❌ No'}")
    print(f"   Errors Found: {len(validation_result.errors)}")
    print(f"   Warnings: {len(validation_result.warnings)}")
    print(f"   Schema Available: {'✅ Yes' if JSONSCHEMA_AVAILABLE and loader.schema else '❌ No'}")
    
    return {
        "config_loaded": config is not None,
        "validation_passed": validation_result.is_valid,
        "errors": validation_result.errors,
        "warnings": validation_result.warnings,
        "summary": summary if config else None
    }


if __name__ == "__main__":
    """
    Main CLI entry point for routing configuration testing.
    
    Run comprehensive tests of the routing configuration loader.
    """
    test_results = run_config_tests() 