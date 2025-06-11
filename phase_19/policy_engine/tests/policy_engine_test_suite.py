#!/usr/bin/env python3
"""
GitBridge Phase 19 - Policy Engine Test Suite

This module provides comprehensive testing for the unified policy engine,
including schema validation, profile loading, routing logic testing,
fallback escalation scenarios, and UID threading simulation.

Author: GitBridge MAS Integration Team
Phase: 19 - Unified Policy Engine
MAS Lite Protocol: v2.1 Compliance
"""

import json
import sys
import unittest
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib
import uuid
import logging


# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from injector.runtime_policy_injector import RuntimePolicyInjector
    POLICY_MODULES_AVAILABLE = True
    # Try to import CLI module, but continue if not available
    try:
        from cli.config_editor_cli import PolicyConfigEditor
        CLI_MODULE_AVAILABLE = True
    except ImportError:
        CLI_MODULE_AVAILABLE = False
        print("⚠️  CLI module not available - will skip CLI tests")
except ImportError as e:
    print(f"⚠️  Policy modules not available: {e}")
    POLICY_MODULES_AVAILABLE = False
    CLI_MODULE_AVAILABLE = False


class MockMASComponent:
    """Mock MAS component for testing policy injection."""
    
    def __init__(self, component_type: str):
        self.component_type = component_type
        self.timeout = 120
        self.max_concurrent_tasks = 20
        self.max_retries = 3
        self.retry_delay = 1.0
        self.lineage_depth = 5
        self.threading_strategy = "hierarchical"
        self.confidence_threshold = 0.7
        self.timeout_threshold = 120
        self.failure_threshold = 5
        self.recovery_timeout = 10.0
        self.error_rate_threshold = 0.2
        self.max_concurrent = 20
        
        # Track configuration changes
        self.config_history = []
    
    def log_config_change(self, attribute: str, old_value: Any, new_value: Any):
        """Log configuration changes for testing."""
        self.config_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attribute": attribute,
            "old_value": old_value,
            "new_value": new_value
        })


class PolicyEngineTestSuite(unittest.TestCase):
    """Test suite for unified policy engine functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_dir = Path(__file__).parent.parent
        cls.default_profiles_dir = cls.test_dir / "config" / "default_profiles"
        cls.schema_path = cls.test_dir / "schema" / "unified_policy_schema.json"
        
        # Create temporary test directory
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="policy_test_"))
        cls.temp_profiles_dir = cls.temp_dir / "test_profiles"
        cls.temp_profiles_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🧪 Test environment setup at: {cls.temp_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)
            print(f"🧹 Test environment cleaned up")
    
    def setUp(self):
        """Set up individual test."""
        self.maxDiff = None
        
        # Configure test logging
        logging.basicConfig(level=logging.WARNING)
        self.test_logger = logging.getLogger(f"test_{self._testMethodName}")
    
    def test_01_schema_validation(self):
        """Test that the unified policy schema is valid JSON Schema."""
        print("🔍 Testing schema validation...")
        
        # Check schema file exists
        self.assertTrue(self.schema_path.exists(), 
                       f"Schema file not found: {self.schema_path}")
        
        # Load and validate schema
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        # Check required schema fields
        required_schema_fields = ["$schema", "title", "type", "properties", "required"]
        for field in required_schema_fields:
            self.assertIn(field, schema_data, f"Missing schema field: {field}")
        
        # Check required properties exist
        required_properties = ["policy_metadata", "execution_profile", "routing", 
                             "fallbacks", "uid_lineage", "logging", "output"]
        
        for prop in required_properties:
            self.assertIn(prop, schema_data["properties"], 
                         f"Missing required property: {prop}")
            self.assertIn(prop, schema_data["required"], 
                         f"Property not in required list: {prop}")
        
        print("✅ Schema validation passed")
    
    def test_02_load_default_profiles(self):
        """Test loading default execution profiles."""
        print("📂 Testing default profile loading...")
        
        expected_profiles = ["audit.json", "realtime.json", "diagnostic.json", "stress.json"]
        
        for profile_name in expected_profiles:
            profile_path = self.default_profiles_dir / profile_name
            
            # Check file exists
            self.assertTrue(profile_path.exists(), 
                           f"Default profile not found: {profile_name}")
            
            # Load and validate JSON
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # Check required sections
            required_sections = ["policy_metadata", "execution_profile", "routing", 
                               "fallbacks", "uid_lineage", "logging", "output"]
            
            for section in required_sections:
                self.assertIn(section, profile_data, 
                             f"Missing section in {profile_name}: {section}")
            
            # Validate profile type consistency
            metadata = profile_data["policy_metadata"]
            execution = profile_data["execution_profile"]
            
            profile_type = metadata["profile_type"]
            execution_name = execution["name"]
            
            self.assertEqual(profile_type, execution_name, 
                           f"Profile type mismatch in {profile_name}: {profile_type} != {execution_name}")
            
            print(f"   ✅ {profile_name}: {profile_type} profile loaded successfully")
        
        print("✅ Default profile loading passed")
    
    def test_03_routing_key_structure(self):
        """Test routing configuration key structure matches schema."""
        print("🔀 Testing routing key structure...")
        
        # Load audit profile for testing
        audit_path = self.default_profiles_dir / "audit.json"
        with open(audit_path, 'r', encoding='utf-8') as f:
            audit_data = json.load(f)
        
        routing_config = audit_data["routing"]
        
        # Check primary model structure
        primary_model = routing_config["primary_model"]
        required_primary_fields = ["model_id", "provider", "timeout_seconds", 
                                 "confidence_threshold", "max_tokens", "temperature"]
        
        for field in required_primary_fields:
            self.assertIn(field, primary_model, 
                         f"Missing primary model field: {field}")
        
        # Check fallback chain structure
        fallback_chain = routing_config["fallback_chain"]
        self.assertIsInstance(fallback_chain, list, "Fallback chain must be a list")
        self.assertGreater(len(fallback_chain), 0, "Fallback chain cannot be empty")
        
        for i, fallback in enumerate(fallback_chain):
            required_fallback_fields = ["model_id", "provider", "timeout_seconds", 
                                      "confidence_threshold", "fallback_conditions", "priority"]
            
            for field in required_fallback_fields:
                self.assertIn(field, fallback, 
                             f"Missing fallback[{i}] field: {field}")
            
            # Check fallback conditions are valid
            valid_conditions = ["timeout", "low_confidence", "error", "rate_limit", "unavailable"]
            for condition in fallback["fallback_conditions"]:
                self.assertIn(condition, valid_conditions, 
                             f"Invalid fallback condition: {condition}")
        
        # Check selection strategy
        valid_strategies = ["confidence", "performance", "cost", "balanced"]
        selection_strategy = routing_config["selection_strategy"]
        self.assertIn(selection_strategy, valid_strategies, 
                     f"Invalid selection strategy: {selection_strategy}")
        
        print("✅ Routing key structure validation passed")
    
    def test_04_fallback_escalation_logic(self):
        """Test fallback escalation logic for invalid input scenarios."""
        print("⚡ Testing fallback escalation logic...")
        
        # Load diagnostic profile for testing (has aggressive retry policy)
        diagnostic_path = self.default_profiles_dir / "diagnostic.json"
        with open(diagnostic_path, 'r', encoding='utf-8') as f:
            diagnostic_data = json.load(f)
        
        fallbacks_config = diagnostic_data["fallbacks"]
        
        # Test escalation thresholds
        escalation = fallbacks_config["escalation_thresholds"]
        
        # Confidence threshold should be between 0 and 1
        confidence_threshold = escalation["confidence_threshold"]
        self.assertGreaterEqual(confidence_threshold, 0.0, 
                               "Confidence threshold must be >= 0")
        self.assertLessEqual(confidence_threshold, 1.0, 
                            "Confidence threshold must be <= 1")
        
        # Timeout threshold should be positive
        timeout_threshold = escalation["timeout_threshold"]
        self.assertGreater(timeout_threshold, 0, 
                          "Timeout threshold must be positive")
        
        # Error rate threshold should be between 0 and 1
        error_rate_threshold = escalation["error_rate_threshold"]
        self.assertGreaterEqual(error_rate_threshold, 0.0, 
                               "Error rate threshold must be >= 0")
        self.assertLessEqual(error_rate_threshold, 1.0, 
                            "Error rate threshold must be <= 1")
        
        # Test retry policy
        retry_policy = fallbacks_config["retry_policy"]
        
        max_retries = retry_policy["max_retries"]
        self.assertGreaterEqual(max_retries, 0, "Max retries must be >= 0")
        self.assertLessEqual(max_retries, 10, "Max retries should be reasonable (<= 10)")
        
        base_delay = retry_policy["base_delay_ms"]
        self.assertGreater(base_delay, 0, "Base delay must be positive")
        
        backoff_multiplier = retry_policy["backoff_multiplier"]
        self.assertGreaterEqual(backoff_multiplier, 1.0, 
                               "Backoff multiplier must be >= 1.0")
        
        # Test circuit breaker
        circuit_breaker = fallbacks_config["circuit_breaker"]
        
        failure_threshold = circuit_breaker["failure_threshold"]
        self.assertGreater(failure_threshold, 0, 
                          "Failure threshold must be positive")
        
        recovery_timeout = circuit_breaker["recovery_timeout_ms"]
        self.assertGreater(recovery_timeout, 0, 
                          "Recovery timeout must be positive")
        
        # Test escalation logic simulation
        test_scenarios = [
            {"confidence": 0.3, "should_escalate": True},   # Low confidence
            {"confidence": 0.8, "should_escalate": False},  # High confidence
            {"error_rate": 0.1, "should_escalate": True},   # High error rate (> 0.05)
            {"error_rate": 0.01, "should_escalate": False}, # Low error rate
        ]
        
        for scenario in test_scenarios:
            if "confidence" in scenario:
                should_escalate = scenario["confidence"] < confidence_threshold
                self.assertEqual(should_escalate, scenario["should_escalate"], 
                               f"Confidence escalation logic failed for {scenario}")
            
            if "error_rate" in scenario:
                should_escalate = scenario["error_rate"] > error_rate_threshold
                self.assertEqual(should_escalate, scenario["should_escalate"], 
                               f"Error rate escalation logic failed for {scenario}")
        
        print("✅ Fallback escalation logic validation passed")
    
    def test_05_uid_threading_simulation(self):
        """Test UID threading with policy overrides."""
        print("🔗 Testing UID threading simulation...")
        
        # Load audit profile (has hierarchical threading)
        audit_path = self.default_profiles_dir / "audit.json"
        with open(audit_path, 'r', encoding='utf-8') as f:
            audit_data = json.load(f)
        
        uid_config = audit_data["uid_lineage"]
        
        # Test UID format configuration
        uid_format = uid_config["uid_format"]
        pattern = uid_format["pattern"]
        components = uid_format["components"]
        separator = uid_format["separator"]
        
        # Validate components
        valid_components = ["timestamp", "entropy", "agent_id", "sequence", "parent_ref"]
        for component in components:
            self.assertIn(component, valid_components, 
                         f"Invalid UID component: {component}")
        
        # Simulate UID generation based on pattern
        def generate_test_uid(parent_uid: Optional[str] = None) -> str:
            """Generate test UID based on pattern."""
            timestamp = str(int(datetime.now(timezone.utc).timestamp()))
            entropy = str(uuid.uuid4())[:8]
            agent_id = "testagent"
            sequence = "001"
            parent_ref = parent_uid[:8] if parent_uid else "root"
            
            component_values = {
                "timestamp": timestamp,
                "entropy": entropy,
                "agent_id": agent_id,
                "sequence": sequence,
                "parent_ref": parent_ref
            }
            
            # Build UID from components - only use components specified in the format
            uid_parts = []
            for component in components:
                if component in component_values:
                    uid_parts.append(component_values[component])
                else:
                    # Skip components not available for this UID generation
                    pass
            
            return separator.join(uid_parts)
        
        # Test hierarchical threading
        threading_strategy = uid_config["threading_strategy"]
        lineage_depth = uid_config["lineage_depth"]
        
        if threading_strategy == "hierarchical":
            # Generate UID chain
            uid_chain = []
            parent_uid = None
            
            for level in range(min(3, lineage_depth)):  # Test up to 3 levels
                new_uid = generate_test_uid(parent_uid)
                uid_chain.append(new_uid)
                parent_uid = new_uid
                
                # Validate UID structure
                uid_parts = new_uid.split(separator)
                self.assertEqual(len(uid_parts), len(components), 
                               f"UID component count mismatch: {new_uid}")
                
                # Check parent reference (except for root)
                if level > 0:
                    parent_ref_index = components.index("parent_ref")
                    parent_ref = uid_parts[parent_ref_index]
                    expected_parent_ref = uid_chain[level-1][:8]
                    self.assertEqual(parent_ref, expected_parent_ref, 
                                   f"Parent reference mismatch at level {level}")
            
            print(f"   ✅ Generated {len(uid_chain)} UIDs in hierarchical chain")
            for i, uid in enumerate(uid_chain):
                print(f"      Level {i}: {uid}")
        
        # Test persistence configuration
        persistence = uid_config["persistence"]
        self.assertIsInstance(persistence["enabled"], bool, 
                             "Persistence enabled must be boolean")
        
        valid_backends = ["redis", "file", "memory"]
        storage_backend = persistence["storage_backend"]
        self.assertIn(storage_backend, valid_backends, 
                     f"Invalid storage backend: {storage_backend}")
        
        if persistence["enabled"]:
            retention_hours = persistence["retention_hours"]
            self.assertGreater(retention_hours, 0, 
                              "Retention hours must be positive")
        
        print("✅ UID threading simulation passed")
    
    def test_06_logger_output_formatting_policy(self):
        """Test logger output formatting policy validation."""
        print("📝 Testing logger output formatting policy...")
        
        # Test different profile logging configurations
        profile_tests = [
            ("audit.json", "DEBUG", "json", True),      # Full logging
            ("realtime.json", "WARNING", "structured", False),  # Minimal logging
            ("diagnostic.json", "DEBUG", "json", True), # Comprehensive logging
            ("stress.json", "ERROR", "plain", False),   # Minimal logging
        ]
        
        for profile_name, expected_level, expected_format, expected_compliance in profile_tests:
            profile_path = self.default_profiles_dir / profile_name
            
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            logging_config = profile_data["logging"]
            
            # Test logging level
            log_level = logging_config["level"]
            self.assertEqual(log_level, expected_level, 
                           f"Unexpected log level in {profile_name}: {log_level}")
            
            # Test logging format
            log_format = logging_config["format"]
            self.assertEqual(log_format, expected_format, 
                           f"Unexpected log format in {profile_name}: {log_format}")
            
            # Test outputs configuration
            outputs = logging_config["outputs"]
            self.assertIsInstance(outputs, list, "Outputs must be a list")
            self.assertGreater(len(outputs), 0, "Must have at least one output")
            
            # Validate output types
            valid_output_types = ["console", "file", "redis", "syslog"]
            for output in outputs:
                output_type = output["type"]
                self.assertIn(output_type, valid_output_types, 
                             f"Invalid output type: {output_type}")
                
                enabled = output["enabled"]
                self.assertIsInstance(enabled, bool, 
                                    "Output enabled must be boolean")
                
                # Check file output has path
                if output_type == "file" and enabled:
                    self.assertIn("path", output, 
                                 "File output must have path")
                    
                    # Check rotation configuration if present
                    if "rotation" in output:
                        rotation = output["rotation"]
                        if rotation.get("enabled", False):
                            self.assertIn("max_size_mb", rotation, 
                                         "Rotation must specify max_size_mb")
                            self.assertIn("backup_count", rotation, 
                                         "Rotation must specify backup_count")
            
            # Test fields configuration
            fields = logging_config["fields"]
            mas_lite_compliance = fields.get("mas_lite_compliance", False)
            self.assertEqual(mas_lite_compliance, expected_compliance, 
                           f"Unexpected MAS Lite compliance in {profile_name}")
            
            print(f"   ✅ {profile_name}: {log_level}/{log_format}/MAS:{expected_compliance}")
        
        print("✅ Logger output formatting policy validation passed")
    
    @unittest.skipUnless(POLICY_MODULES_AVAILABLE, "Policy modules not available")
    def test_07_policy_injector_integration(self):
        """Test policy injector with mock components."""
        print("💉 Testing policy injector integration...")
        
        # Create temporary test policy
        test_policy = {
            "policy_metadata": {
                "policy_id": "test_policy_001",
                "version": "1.0.0",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "profile_type": "custom",
                "description": "Test policy for integration testing"
            },
            "execution_profile": {
                "name": "custom",
                "priority": 7,
                "timeout_seconds": 180,
                "max_concurrent_tasks": 15,
                "memory_limit_mb": 256,
                "enable_debug": True
            },
            "routing": {
                "primary_model": {
                    "model_id": "test-model",
                    "provider": "local",
                    "timeout_seconds": 60,
                    "confidence_threshold": 0.8,
                    "max_tokens": 1024,
                    "temperature": 0.5
                },
                "fallback_chain": [
                    {
                        "model_id": "test-fallback",
                        "provider": "local",
                        "timeout_seconds": 30,
                        "confidence_threshold": 0.7,
                        "max_tokens": 512,
                        "temperature": 0.5,
                        "fallback_conditions": ["timeout", "error"],
                        "priority": 1
                    }
                ],
                "selection_strategy": "confidence",
                "load_balancing": {"enabled": False, "algorithm": "round_robin", "weights": {}}
            },
            "fallbacks": {
                "escalation_thresholds": {
                    "confidence_threshold": 0.6,
                    "timeout_threshold": 180,
                    "error_rate_threshold": 0.25,
                    "latency_threshold_ms": 9000
                },
                "retry_policy": {
                    "max_retries": 4,
                    "base_delay_ms": 750,
                    "backoff_multiplier": 1.8,
                    "jitter_enabled": True
                },
                "circuit_breaker": {
                    "failure_threshold": 4,
                    "recovery_timeout_ms": 15000,
                    "half_open_max_calls": 5
                }
            },
            "uid_lineage": {
                "threading_strategy": "hierarchical",
                "lineage_depth": 7,
                "uid_format": {
                    "pattern": "{timestamp}_{entropy}_{agent_id}",
                    "components": ["timestamp", "entropy", "agent_id"],
                    "separator": "_"
                },
                "persistence": {
                    "enabled": True,
                    "storage_backend": "memory",
                    "retention_hours": 48
                }
            },
            "logging": {
                "level": "INFO",
                "format": "structured",
                "outputs": [{"type": "console", "enabled": True}],
                "fields": {
                    "include_timestamp": True,
                    "include_thread_id": True,
                    "include_process_id": False,
                    "include_uid_lineage": True,
                    "mas_lite_compliance": True
                }
            },
            "output": {
                "format": {"type": "json", "encoding": "utf-8", "pretty_print": True, "compression": {"enabled": False}},
                "delivery": {"method": "synchronous", "reliability": "exactly_once", "batch_size": 1, "flush_interval_ms": 0},
                "validation": {"enabled": True, "schema_validation": True, "checksum_enabled": False, "mas_lite_compliance": True}
            }
        }
        
        # Write test policy to file
        test_policy_path = self.temp_profiles_dir / "test_policy.json"
        with open(test_policy_path, 'w', encoding='utf-8') as f:
            json.dump(test_policy, f, indent=2)
        
        # Initialize injector
        injector = RuntimePolicyInjector()
        
        # Load test policy
        load_success = injector.load_policy(str(test_policy_path))
        self.assertTrue(load_success, "Failed to load test policy")
        
        # Create mock components
        mock_components = {
            "pipeline": MockMASComponent("pipeline"),
            "task_chain": MockMASComponent("task_chain"),
            "consensus": MockMASComponent("consensus")
        }
        
        # Store original values for comparison
        original_values = {}
        for name, component in mock_components.items():
            original_values[name] = {
                "timeout": component.timeout,
                "max_concurrent_tasks": component.max_concurrent_tasks,
                "confidence_threshold": component.confidence_threshold
            }
        
        # Inject policy
        injection_results = injector.inject_policy(mock_components)
        
        # Validate injection results
        self.assertTrue(injection_results["success"], 
                       f"Policy injection failed: {injection_results.get('errors', [])}")
        self.assertEqual(injection_results["policy_id"], "test_policy_001")
        self.assertEqual(injection_results["profile_type"], "custom")
        
        # Check that settings were applied
        applied_settings = injection_results["applied_settings"]
        self.assertIn("pipeline", applied_settings, "Pipeline settings not applied")
        self.assertIn("task_chain", applied_settings, "Task chain settings not applied")
        self.assertIn("consensus", applied_settings, "Consensus settings not applied")
        
        # Verify specific setting changes
        pipeline = mock_components["pipeline"]
        self.assertEqual(pipeline.timeout, 180, "Pipeline timeout not updated")
        self.assertEqual(pipeline.max_concurrent_tasks, 15, "Pipeline max_concurrent_tasks not updated")
        
        task_chain = mock_components["task_chain"]
        self.assertEqual(task_chain.lineage_depth, 7, "Task chain lineage_depth not updated")
        self.assertEqual(task_chain.confidence_threshold, 0.6, "Task chain confidence_threshold not updated")
        
        consensus = mock_components["consensus"]
        self.assertEqual(consensus.timeout, 180, "Consensus timeout not updated")
        self.assertEqual(consensus.failure_threshold, 4, "Consensus failure_threshold not updated")
        
        # Test threshold override
        override_success = injector.override_fallback_thresholds({
            "confidence_threshold": 0.5,
            "timeout_threshold": 200
        })
        
        self.assertTrue(override_success, "Threshold override failed")
        
        # Verify overrides were applied
        self.assertEqual(task_chain.confidence_threshold, 0.5, "Confidence threshold override not applied")
        
        # Get injection summary
        summary = injector.get_injection_summary()
        self.assertEqual(summary["policy_info"]["id"], "test_policy_001")
        self.assertEqual(len(summary["active_components"]), 3)
        self.assertGreater(summary["injection_history_count"], 0)
        
        print("✅ Policy injector integration test passed")
    
    def test_08_performance_profile_comparison(self):
        """Test performance characteristics across different profiles."""
        print("⚡ Testing performance profile comparison...")
        
        profiles = ["audit", "realtime", "diagnostic", "stress"]
        profile_metrics = {}
        
        for profile_name in profiles:
            profile_path = self.default_profiles_dir / f"{profile_name}.json"
            
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            execution = profile_data["execution_profile"]
            fallbacks = profile_data["fallbacks"]
            logging_config = profile_data["logging"]
            
            metrics = {
                "priority": execution["priority"],
                "timeout_seconds": execution["timeout_seconds"],
                "max_concurrent_tasks": execution["max_concurrent_tasks"],
                "max_retries": fallbacks["retry_policy"]["max_retries"],
                "base_delay_ms": fallbacks["retry_policy"]["base_delay_ms"],
                "logging_level": logging_config["level"],
                "debug_enabled": execution.get("enable_debug", False)
            }
            
            profile_metrics[profile_name] = metrics
            print(f"   📊 {profile_name}: Priority={metrics['priority']}, "
                  f"Timeout={metrics['timeout_seconds']}s, "
                  f"MaxTasks={metrics['max_concurrent_tasks']}, "
                  f"Retries={metrics['max_retries']}")
        
        # Validate performance expectations
        # Realtime should have highest priority and lowest timeouts
        self.assertEqual(profile_metrics["realtime"]["priority"], 10, 
                        "Realtime should have highest priority")
        self.assertLessEqual(profile_metrics["realtime"]["timeout_seconds"], 
                            profile_metrics["audit"]["timeout_seconds"],
                            "Realtime should have shorter timeout than audit")
        
        # Stress should have highest concurrency
        self.assertGreaterEqual(profile_metrics["stress"]["max_concurrent_tasks"], 
                               max(m["max_concurrent_tasks"] for n, m in profile_metrics.items() if n != "stress"),
                               "Stress should have highest max_concurrent_tasks")
        
        # Diagnostic should have most retries
        self.assertGreaterEqual(profile_metrics["diagnostic"]["max_retries"], 
                               max(m["max_retries"] for n, m in profile_metrics.items() if n != "diagnostic"),
                               "Diagnostic should have most retries")
        
        # Audit should have debug enabled
        self.assertTrue(profile_metrics["audit"]["debug_enabled"], 
                       "Audit should have debug enabled")
        
        # Realtime and stress should have debug disabled for performance
        self.assertFalse(profile_metrics["realtime"]["debug_enabled"], 
                        "Realtime should have debug disabled")
        self.assertFalse(profile_metrics["stress"]["debug_enabled"], 
                        "Stress should have debug disabled")
        
        print("✅ Performance profile comparison passed")


def run_test_suite():
    """Run the complete policy engine test suite."""
    print("🚀 Starting GitBridge Policy Engine Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(PolicyEngineTestSuite)
    
    # Configure test runner
    test_runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=True
    )
    
    # Run tests
    test_results = test_runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏁 Test Suite Summary")
    print(f"   Tests run: {test_results.testsRun}")
    print(f"   Failures: {len(test_results.failures)}")
    print(f"   Errors: {len(test_results.errors)}")
    print(f"   Skipped: {len(test_results.skipped)}")
    
    if test_results.failures:
        print("\n❌ Failures:")
        for test, traceback in test_results.failures:
            print(f"   - {test}: {traceback}")
    
    if test_results.errors:
        print("\n💥 Errors:")
        for test, traceback in test_results.errors:
            print(f"   - {test}: {traceback}")
    
    # Return success status
    success = len(test_results.failures) == 0 and len(test_results.errors) == 0
    
    if success:
        print("\n✅ All tests passed! Policy Engine is ready for production.")
    else:
        print("\n❌ Some tests failed. Please review and fix issues.")
    
    return success


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1) 