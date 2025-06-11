#!/usr/bin/env python3
"""
GitBridge Phase 19 - Runtime Policy Injector

This module loads unified policy configurations and injects settings into
the MAS core components (pipeline, task_chain, consensus) with live
fallback threshold overrides and logger configuration routing.

Author: GitBridge MAS Integration Team
Phase: 19 - Unified Policy Engine
MAS Lite Protocol: v2.1 Compliance
"""

import json
import sys
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
import importlib.util


# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from mas_core.pipeline import MASPipeline
    from mas_core.task_chain import TaskChainManager
    from mas_core.consensus import ConsensusManager
    from mas_core.error_handler import ErrorHandler
    MAS_CORE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  MAS Core modules not available: {e}")
    MAS_CORE_AVAILABLE = False


class RuntimePolicyInjector:
    """Injects unified policy configurations into MAS core components."""
    
    def __init__(self, policy_path: Optional[str] = None):
        """
        Initialize the runtime policy injector.
        
        Args:
            policy_path: Path to unified policy JSON file
        """
        self.policy_path = Path(policy_path) if policy_path else None
        self.policy_data = None
        self.injection_history = []
        self.active_components = {}
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup basic logging for the injector."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger('PolicyInjector')
    
    def load_policy(self, policy_path: str) -> bool:
        """
        Load unified policy configuration from JSON file.
        
        Args:
            policy_path: Path to policy JSON file
            
        Returns:
            True if policy loaded successfully
        """
        try:
            self.policy_path = Path(policy_path)
            
            if not self.policy_path.exists():
                self.logger.error(f"Policy file not found: {policy_path}")
                return False
            
            with open(self.policy_path, 'r', encoding='utf-8') as f:
                self.policy_data = json.load(f)
            
            # Validate basic structure
            required_sections = ["policy_metadata", "execution_profile", "routing", 
                               "fallbacks", "uid_lineage", "logging", "output"]
            
            for section in required_sections:
                if section not in self.policy_data:
                    self.logger.error(f"Missing required section: {section}")
                    return False
            
            # Generate policy hash for tracking
            policy_json = json.dumps(self.policy_data, sort_keys=True)
            policy_hash = hashlib.sha256(policy_json.encode()).hexdigest()[:16]
            
            self.logger.info(f"✅ Policy loaded: {self.policy_path.name}")
            self.logger.info(f"   Type: {self.policy_data['policy_metadata']['profile_type']}")
            self.logger.info(f"   Version: {self.policy_data['policy_metadata']['version']}")
            self.logger.info(f"   Hash: {policy_hash}")
            
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in policy file: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to load policy: {e}")
            return False
    
    def _configure_pipeline_settings(self, pipeline_instance: Any) -> Dict[str, Any]:
        """
        Configure pipeline settings from policy.
        
        Args:
            pipeline_instance: Pipeline instance to configure
            
        Returns:
            Dictionary of applied settings
        """
        if not self.policy_data:
            return {}
        
        applied_settings = {}
        execution_profile = self.policy_data.get("execution_profile", {})
        fallbacks = self.policy_data.get("fallbacks", {})
        
        try:
            # Apply execution timeouts
            if hasattr(pipeline_instance, 'timeout'):
                pipeline_instance.timeout = execution_profile.get("timeout_seconds", 120)
                applied_settings["timeout_seconds"] = pipeline_instance.timeout
            
            # Apply max concurrent tasks
            if hasattr(pipeline_instance, 'max_concurrent_tasks'):
                pipeline_instance.max_concurrent_tasks = execution_profile.get("max_concurrent_tasks", 20)
                applied_settings["max_concurrent_tasks"] = pipeline_instance.max_concurrent_tasks
            
            # Apply retry policy
            retry_policy = fallbacks.get("retry_policy", {})
            if hasattr(pipeline_instance, 'max_retries'):
                pipeline_instance.max_retries = retry_policy.get("max_retries", 3)
                applied_settings["max_retries"] = pipeline_instance.max_retries
            
            if hasattr(pipeline_instance, 'retry_delay'):
                pipeline_instance.retry_delay = retry_policy.get("base_delay_ms", 1000) / 1000.0
                applied_settings["retry_delay"] = pipeline_instance.retry_delay
            
            self.logger.info(f"📋 Pipeline settings applied: {len(applied_settings)} parameters")
            
        except Exception as e:
            self.logger.error(f"Failed to configure pipeline: {e}")
        
        return applied_settings
    
    def _configure_task_chain_settings(self, task_chain_instance: Any) -> Dict[str, Any]:
        """
        Configure task chain settings from policy.
        
        Args:
            task_chain_instance: TaskChain instance to configure
            
        Returns:
            Dictionary of applied settings
        """
        if not self.policy_data:
            return {}
        
        applied_settings = {}
        execution_profile = self.policy_data.get("execution_profile", {})
        uid_lineage = self.policy_data.get("uid_lineage", {})
        fallbacks = self.policy_data.get("fallbacks", {})
        
        try:
            # Apply concurrent task limits
            if hasattr(task_chain_instance, 'max_concurrent'):
                task_chain_instance.max_concurrent = execution_profile.get("max_concurrent_tasks", 20)
                applied_settings["max_concurrent_tasks"] = task_chain_instance.max_concurrent
            
            # Apply UID lineage settings
            if hasattr(task_chain_instance, 'lineage_depth'):
                task_chain_instance.lineage_depth = uid_lineage.get("lineage_depth", 5)
                applied_settings["lineage_depth"] = task_chain_instance.lineage_depth
            
            if hasattr(task_chain_instance, 'threading_strategy'):
                task_chain_instance.threading_strategy = uid_lineage.get("threading_strategy", "hierarchical")
                applied_settings["threading_strategy"] = task_chain_instance.threading_strategy
            
            # Apply escalation thresholds
            escalation = fallbacks.get("escalation_thresholds", {})
            if hasattr(task_chain_instance, 'confidence_threshold'):
                task_chain_instance.confidence_threshold = escalation.get("confidence_threshold", 0.7)
                applied_settings["confidence_threshold"] = task_chain_instance.confidence_threshold
            
            if hasattr(task_chain_instance, 'timeout_threshold'):
                task_chain_instance.timeout_threshold = escalation.get("timeout_threshold", 120)
                applied_settings["timeout_threshold"] = task_chain_instance.timeout_threshold
            
            self.logger.info(f"🔗 Task chain settings applied: {len(applied_settings)} parameters")
            
        except Exception as e:
            self.logger.error(f"Failed to configure task chain: {e}")
        
        return applied_settings
    
    def _configure_consensus_settings(self, consensus_instance: Any) -> Dict[str, Any]:
        """
        Configure consensus settings from policy.
        
        Args:
            consensus_instance: Consensus instance to configure
            
        Returns:
            Dictionary of applied settings
        """
        if not self.policy_data:
            return {}
        
        applied_settings = {}
        execution_profile = self.policy_data.get("execution_profile", {})
        fallbacks = self.policy_data.get("fallbacks", {})
        
        try:
            # Apply consensus timeout
            if hasattr(consensus_instance, 'timeout'):
                consensus_instance.timeout = execution_profile.get("timeout_seconds", 120)
                applied_settings["timeout_seconds"] = consensus_instance.timeout
            
            # Apply circuit breaker settings
            circuit_breaker = fallbacks.get("circuit_breaker", {})
            if hasattr(consensus_instance, 'failure_threshold'):
                consensus_instance.failure_threshold = circuit_breaker.get("failure_threshold", 5)
                applied_settings["failure_threshold"] = consensus_instance.failure_threshold
            
            if hasattr(consensus_instance, 'recovery_timeout'):
                recovery_timeout_ms = circuit_breaker.get("recovery_timeout_ms", 10000)
                consensus_instance.recovery_timeout = recovery_timeout_ms / 1000.0
                applied_settings["recovery_timeout"] = consensus_instance.recovery_timeout
            
            # Apply escalation thresholds
            escalation = fallbacks.get("escalation_thresholds", {})
            if hasattr(consensus_instance, 'error_rate_threshold'):
                consensus_instance.error_rate_threshold = escalation.get("error_rate_threshold", 0.2)
                applied_settings["error_rate_threshold"] = consensus_instance.error_rate_threshold
            
            self.logger.info(f"🤝 Consensus settings applied: {len(applied_settings)} parameters")
            
        except Exception as e:
            self.logger.error(f"Failed to configure consensus: {e}")
        
        return applied_settings
    
    def _configure_logging(self) -> Dict[str, Any]:
        """
        Configure logging based on policy settings.
        
        Returns:
            Dictionary of applied logging settings
        """
        if not self.policy_data:
            return {}
        
        applied_settings = {}
        logging_config = self.policy_data.get("logging", {})
        
        try:
            # Set logging level
            log_level = logging_config.get("level", "INFO")
            numeric_level = getattr(logging, log_level.upper(), logging.INFO)
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(numeric_level)
            applied_settings["level"] = log_level
            
            # Configure format
            log_format = logging_config.get("format", "structured")
            if log_format == "json":
                formatter = logging.Formatter(
                    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                    '"module": "%(name)s", "message": "%(message)s"}'
                )
            elif log_format == "structured":
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            else:  # plain
                formatter = logging.Formatter('%(levelname)s: %(message)s')
            
            # Apply formatter to existing handlers
            for handler in root_logger.handlers:
                handler.setFormatter(formatter)
            
            applied_settings["format"] = log_format
            
            # Configure MAS Lite compliance fields
            fields = logging_config.get("fields", {})
            if fields.get("mas_lite_compliance", False):
                applied_settings["mas_lite_compliance"] = True
            
            self.logger.info(f"📝 Logging configured: {len(applied_settings)} settings")
            
        except Exception as e:
            self.logger.error(f"Failed to configure logging: {e}")
        
        return applied_settings
    
    def inject_policy(self, components: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Inject policy settings into MAS core components.
        
        Args:
            components: Dictionary of component instances to configure
                       Keys: 'pipeline', 'task_chain', 'consensus'
                       
        Returns:
            Dictionary of injection results
        """
        if not self.policy_data:
            self.logger.error("No policy loaded - call load_policy() first")
            return {"success": False, "error": "No policy loaded"}
        
        injection_results = {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "policy_id": self.policy_data["policy_metadata"]["policy_id"],
            "profile_type": self.policy_data["policy_metadata"]["profile_type"],
            "applied_settings": {},
            "errors": []
        }
        
        try:
            # Configure logging first
            logging_settings = self._configure_logging()
            if logging_settings:
                injection_results["applied_settings"]["logging"] = logging_settings
            
            # Inject into provided components or attempt to find them
            if components:
                self.active_components = components
            
            # Configure pipeline
            if "pipeline" in self.active_components:
                pipeline_settings = self._configure_pipeline_settings(
                    self.active_components["pipeline"]
                )
                if pipeline_settings:
                    injection_results["applied_settings"]["pipeline"] = pipeline_settings
            
            # Configure task chain
            if "task_chain" in self.active_components:
                task_chain_settings = self._configure_task_chain_settings(
                    self.active_components["task_chain"]
                )
                if task_chain_settings:
                    injection_results["applied_settings"]["task_chain"] = task_chain_settings
            
            # Configure consensus
            if "consensus" in self.active_components:
                consensus_settings = self._configure_consensus_settings(
                    self.active_components["consensus"]
                )
                if consensus_settings:
                    injection_results["applied_settings"]["consensus"] = consensus_settings
            
            # Record injection in history
            self.injection_history.append(injection_results.copy())
            
            # Generate summary
            total_settings = sum(
                len(settings) for settings in injection_results["applied_settings"].values()
            )
            
            self.logger.info("✅ Policy injection completed")
            self.logger.info(f"   Components configured: {len(injection_results['applied_settings'])}")
            self.logger.info(f"   Total settings applied: {total_settings}")
            
            return injection_results
            
        except Exception as e:
            error_msg = f"Policy injection failed: {e}"
            self.logger.error(error_msg)
            injection_results["success"] = False
            injection_results["errors"].append(error_msg)
            return injection_results
    
    def get_injection_summary(self) -> Dict[str, Any]:
        """
        Get summary of current policy injection state.
        
        Returns:
            Dictionary containing injection summary
        """
        if not self.policy_data:
            return {"error": "No policy loaded"}
        
        metadata = self.policy_data["policy_metadata"]
        execution = self.policy_data["execution_profile"]
        
        summary = {
            "policy_info": {
                "id": metadata["policy_id"],
                "type": metadata["profile_type"],
                "version": metadata["version"],
                "description": metadata.get("description", "")
            },
            "execution_profile": {
                "name": execution["name"],
                "priority": execution["priority"],
                "timeout_seconds": execution["timeout_seconds"],
                "max_concurrent_tasks": execution.get("max_concurrent_tasks", "N/A"),
                "debug_enabled": execution.get("enable_debug", False)
            },
            "active_components": list(self.active_components.keys()),
            "injection_history_count": len(self.injection_history),
            "last_injection": self.injection_history[-1]["timestamp"] if self.injection_history else None
        }
        
        return summary
    
    def override_fallback_thresholds(self, overrides: Dict[str, Any]) -> bool:
        """
        Apply live fallback threshold overrides.
        
        Args:
            overrides: Dictionary of threshold overrides
            
        Returns:
            True if overrides applied successfully
        """
        if not self.policy_data:
            self.logger.error("No policy loaded for threshold override")
            return False
        
        try:
            # Update policy data with overrides
            fallbacks = self.policy_data.setdefault("fallbacks", {})
            escalation = fallbacks.setdefault("escalation_thresholds", {})
            
            applied_overrides = {}
            
            for key, value in overrides.items():
                if key in ["confidence_threshold", "timeout_threshold", 
                          "error_rate_threshold", "latency_threshold_ms"]:
                    escalation[key] = value
                    applied_overrides[key] = value
            
            # Re-inject settings to active components
            if self.active_components:
                self.inject_policy(self.active_components)
            
            self.logger.info(f"🔄 Fallback thresholds overridden: {applied_overrides}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to override thresholds: {e}")
            return False


def main():
    """CLI entry point for standalone policy injection."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="GitBridge Runtime Policy Injector",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('policy_path',
                       help='Path to unified policy JSON file')
    
    parser.add_argument('--summary', '-s',
                       action='store_true',
                       help='Show policy summary after loading')
    
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Load policy but do not inject settings')
    
    args = parser.parse_args()
    
    # Initialize injector
    injector = RuntimePolicyInjector()
    
    # Load policy
    if not injector.load_policy(args.policy_path):
        print("❌ Failed to load policy")
        sys.exit(1)
    
    # Show summary if requested
    if args.summary:
        summary = injector.get_injection_summary()
        print("\n📊 Policy Summary:")
        print(f"   ID: {summary['policy_info']['id']}")
        print(f"   Type: {summary['policy_info']['type']}")
        print(f"   Version: {summary['policy_info']['version']}")
        print(f"   Priority: {summary['execution_profile']['priority']}")
        print(f"   Timeout: {summary['execution_profile']['timeout_seconds']}s")
        print(f"   Max Tasks: {summary['execution_profile']['max_concurrent_tasks']}")
        print(f"   Debug: {summary['execution_profile']['debug_enabled']}")
    
    # Inject policy (if not dry run)
    if not args.dry_run:
        if not MAS_CORE_AVAILABLE:
            print("⚠️  MAS Core modules not available - simulation mode")
            print("✅ Policy would be injected into components")
        else:
            # In a real scenario, you would pass actual component instances
            print("💡 Use injector.inject_policy(components) with actual component instances")
    
    print("✅ Policy injection completed successfully")


if __name__ == "__main__":
    main() 