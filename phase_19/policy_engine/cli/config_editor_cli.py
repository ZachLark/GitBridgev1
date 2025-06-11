#!/usr/bin/env python3
"""
GitBridge Phase 19 - Policy Configuration Editor CLI

Interactive command-line interface for creating, editing, validating, and managing
unified policy configurations with dynamic schema loading, template generation,
and comprehensive validation.

Author: GitBridge MAS Integration Team
Phase: 19 - Unified Policy Engine
MAS Lite Protocol: v2.1 Compliance
"""

import json
import sys
import os
import argparse
import tempfile
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import hashlib
import uuid


class PolicyConfigEditor:
    """Interactive policy configuration editor with schema validation."""
    
    def __init__(self):
        """Initialize the policy configuration editor."""
        self.base_dir = Path(__file__).parent.parent
        self.schema_path = self.base_dir / "schema" / "unified_policy_schema.json"
        self.default_profiles_dir = self.base_dir / "config" / "default_profiles"
        self.custom_profiles_dir = self.base_dir / "config" / "custom"
        
        # Ensure custom profiles directory exists
        self.custom_profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Load schema for validation
        self.schema = self._load_schema()
        
        # Determine preferred editor
        self.editor = self._get_preferred_editor()
    
    def _load_schema(self) -> Optional[Dict[str, Any]]:
        """Load the unified policy schema."""
        try:
            if not self.schema_path.exists():
                print(f"❌ Schema file not found: {self.schema_path}")
                return None
            
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            return schema
        except Exception as e:
            print(f"❌ Failed to load schema: {e}")
            return None
    
    def _get_preferred_editor(self) -> str:
        """Determine the user's preferred text editor."""
        # Check environment variables in order of preference
        for env_var in ['VISUAL', 'EDITOR']:
            editor = os.environ.get(env_var)
            if editor:
                return editor
        
        # Default fallback editors
        default_editors = ['nano', 'vim', 'vi', 'code', 'gedit']
        
        for editor in default_editors:
            if shutil.which(editor):
                return editor
        
        # Last resort
        return 'nano'
    
    def _generate_profile_template(self, profile_type: str) -> Dict[str, Any]:
        """Generate a policy profile template based on type."""
        current_time = datetime.now(timezone.utc).isoformat()
        profile_id = f"{profile_type}_policy_{uuid.uuid4().hex[:8]}"
        
        # Base template structure
        template = {
            "policy_metadata": {
                "policy_id": profile_id,
                "version": "1.0.0",
                "created_at": current_time,
                "profile_type": profile_type,
                "description": f"Custom {profile_type} profile for GitBridge MAS",
                "__comment": f"Generated {profile_type} profile template"
            },
            "execution_profile": {
                "name": profile_type,
                "priority": 5,
                "timeout_seconds": 120,
                "max_concurrent_tasks": 20,
                "memory_limit_mb": 256,
                "enable_debug": False,
                "__comment": "Execution settings for this profile"
            },
            "routing": {
                "primary_model": {
                    "model_id": "gpt-4o",
                    "provider": "openai",
                    "timeout_seconds": 60,
                    "confidence_threshold": 0.8,
                    "max_tokens": 4096,
                    "temperature": 0.3
                },
                "fallback_chain": [
                    {
                        "model_id": "claude-3-sonnet",
                        "provider": "anthropic",
                        "timeout_seconds": 45,
                        "confidence_threshold": 0.75,
                        "max_tokens": 4096,
                        "temperature": 0.3,
                        "fallback_conditions": ["timeout", "low_confidence", "error"],
                        "priority": 1
                    }
                ],
                "selection_strategy": "confidence",
                "load_balancing": {
                    "enabled": False,
                    "algorithm": "round_robin",
                    "weights": {}
                },
                "__comment": "Primary routing configuration with fallback chain"
            },
            "fallbacks": {
                "escalation_thresholds": {
                    "confidence_threshold": 0.7,
                    "timeout_threshold": 120,
                    "error_rate_threshold": 0.2,
                    "latency_threshold_ms": 5000
                },
                "retry_policy": {
                    "max_retries": 3,
                    "base_delay_ms": 1000,
                    "backoff_multiplier": 2.0,
                    "jitter_enabled": True
                },
                "circuit_breaker": {
                    "failure_threshold": 5,
                    "recovery_timeout_ms": 30000,
                    "half_open_max_calls": 3
                },
                "__comment": "Fallback escalation and recovery policies"
            },
            "uid_lineage": {
                "threading_strategy": "hierarchical",
                "lineage_depth": 5,
                "uid_format": {
                    "pattern": "{timestamp}_{entropy}_{agent_id}_{sequence}_{parent_ref}",
                    "components": ["timestamp", "entropy", "agent_id", "sequence", "parent_ref"],
                    "separator": "_"
                },
                "persistence": {
                    "enabled": True,
                    "storage_backend": "redis",
                    "retention_hours": 168
                },
                "__comment": "UID lineage tracking and persistence configuration"
            },
            "logging": {
                "level": "INFO",
                "format": "structured",
                "outputs": [
                    {
                        "type": "console",
                        "enabled": True
                    },
                    {
                        "type": "file",
                        "enabled": True,
                        "path": f"/logs/{profile_type}/smartrepo_{profile_type}.log",
                        "rotation": {
                            "enabled": True,
                            "max_size_mb": 50,
                            "backup_count": 10
                        }
                    }
                ],
                "fields": {
                    "include_timestamp": True,
                    "include_thread_id": True,
                    "include_process_id": False,
                    "include_uid_lineage": True,
                    "mas_lite_compliance": True
                },
                "__comment": "Logging configuration with MAS Lite Protocol v2.1 compliance"
            },
            "output": {
                "format": {
                    "type": "json",
                    "encoding": "utf-8",
                    "pretty_print": True,
                    "compression": {
                        "enabled": False,
                        "algorithm": "gzip"
                    }
                },
                "delivery": {
                    "method": "asynchronous",
                    "reliability": "at_least_once",
                    "batch_size": 10,
                    "flush_interval_ms": 1000
                },
                "validation": {
                    "enabled": True,
                    "schema_validation": True,
                    "checksum_enabled": True,
                    "mas_lite_compliance": True
                },
                "__comment": "Output formatting and delivery configuration"
            }
        }
        
        # Customize template based on profile type
        if profile_type == "audit":
            template["execution_profile"]["priority"] = 8
            template["execution_profile"]["timeout_seconds"] = 300
            template["execution_profile"]["max_concurrent_tasks"] = 10
            template["execution_profile"]["enable_debug"] = True
            template["logging"]["level"] = "DEBUG"
            template["logging"]["format"] = "json"
            template["uid_lineage"]["persistence"]["retention_hours"] = 8760  # 1 year
            template["output"]["delivery"]["method"] = "synchronous"
            template["output"]["delivery"]["reliability"] = "exactly_once"
            
        elif profile_type == "realtime":
            template["execution_profile"]["priority"] = 10
            template["execution_profile"]["timeout_seconds"] = 30
            template["execution_profile"]["max_concurrent_tasks"] = 50
            template["logging"]["level"] = "WARNING"
            template["uid_lineage"]["persistence"]["retention_hours"] = 24
            template["fallbacks"]["retry_policy"]["max_retries"] = 1
            
        elif profile_type == "diagnostic":
            template["execution_profile"]["priority"] = 5
            template["execution_profile"]["timeout_seconds"] = 600
            template["execution_profile"]["max_concurrent_tasks"] = 5
            template["execution_profile"]["enable_debug"] = True
            template["logging"]["level"] = "DEBUG"
            template["logging"]["outputs"].extend([
                {
                    "type": "redis",
                    "enabled": True
                },
                {
                    "type": "syslog",
                    "enabled": True
                }
            ])
            template["fallbacks"]["retry_policy"]["max_retries"] = 8
            
        elif profile_type == "stress":
            template["execution_profile"]["priority"] = 3
            template["execution_profile"]["timeout_seconds"] = 60
            template["execution_profile"]["max_concurrent_tasks"] = 100
            template["logging"]["level"] = "ERROR"
            template["logging"]["format"] = "plain"
            template["uid_lineage"]["persistence"]["retention_hours"] = 1
            template["output"]["delivery"]["batch_size"] = 100
        
        return template
    
    def _validate_policy(self, policy_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate policy against schema."""
        errors = []
        
        if not self.schema:
            errors.append("Schema not available for validation")
            return False, errors
        
        try:
            # Basic structure validation
            required_sections = self.schema.get("required", [])
            for section in required_sections:
                if section not in policy_data:
                    errors.append(f"Missing required section: {section}")
            
            # Validate policy metadata
            if "policy_metadata" in policy_data:
                metadata = policy_data["policy_metadata"]
                required_metadata = ["policy_id", "version", "profile_type", "description"]
                for field in required_metadata:
                    if field not in metadata:
                        errors.append(f"Missing metadata field: {field}")
            
            # Validate execution profile
            if "execution_profile" in policy_data:
                profile = policy_data["execution_profile"]
                if "name" in profile and "policy_metadata" in policy_data:
                    if profile["name"] != policy_data["policy_metadata"]["profile_type"]:
                        errors.append("Profile name must match metadata profile_type")
                
                # Validate numeric ranges
                if "priority" in profile:
                    priority = profile["priority"]
                    if not isinstance(priority, int) or not (1 <= priority <= 10):
                        errors.append("Priority must be integer between 1-10")
                
                if "timeout_seconds" in profile:
                    timeout = profile["timeout_seconds"]
                    if not isinstance(timeout, int) or timeout <= 0:
                        errors.append("Timeout must be positive integer")
            
            # Validate routing configuration
            if "routing" in policy_data:
                routing = policy_data["routing"]
                if "primary_model" not in routing:
                    errors.append("Primary model configuration required")
                
                if "fallback_chain" in routing:
                    fallback_chain = routing["fallback_chain"]
                    if not isinstance(fallback_chain, list):
                        errors.append("Fallback chain must be a list")
                    elif len(fallback_chain) > 5:
                        errors.append("Fallback chain cannot exceed 5 models")
            
            # Validate UID lineage
            if "uid_lineage" in policy_data:
                uid_config = policy_data["uid_lineage"]
                if "uid_format" in uid_config:
                    uid_format = uid_config["uid_format"]
                    if "components" in uid_format:
                        components = uid_format["components"]
                        valid_components = ["timestamp", "entropy", "agent_id", "sequence", "parent_ref"]
                        for component in components:
                            if component not in valid_components:
                                errors.append(f"Invalid UID component: {component}")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _backup_profile(self, profile_path: Path) -> Optional[Path]:
        """Create a backup of an existing profile."""
        if not profile_path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = profile_path.with_suffix(f".backup_{timestamp}.json")
        
        try:
            shutil.copy2(profile_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"⚠️  Failed to create backup: {e}")
            return None
    
    def _restore_from_backup(self, profile_path: Path, backup_path: Path) -> bool:
        """Restore profile from backup."""
        try:
            shutil.copy2(backup_path, profile_path)
            return True
        except Exception as e:
            print(f"❌ Failed to restore from backup: {e}")
            return False
    
    def _edit_file_interactive(self, file_path: Path) -> bool:
        """Open file in user's preferred editor."""
        try:
            # Launch editor
            result = subprocess.run([self.editor, str(file_path)], check=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Failed to launch editor '{self.editor}': {e}")
            print("💡 Try setting EDITOR environment variable to your preferred editor")
            return False
    
    def create_policy(self, profile_name: str, profile_type: str) -> bool:
        """Create a new policy configuration."""
        print(f"🆕 Creating new {profile_type} policy: {profile_name}")
        
        # Validate profile type
        valid_types = ["audit", "realtime", "diagnostic", "stress", "custom"]
        if profile_type not in valid_types:
            print(f"❌ Invalid profile type: {profile_type}")
            print(f"💡 Valid types: {', '.join(valid_types)}")
            return False
        
        # Check if profile already exists
        profile_path = self.custom_profiles_dir / f"{profile_name}.json"
        if profile_path.exists():
            print(f"❌ Profile already exists: {profile_name}")
            print(f"💡 Use 'edit' command to modify existing profile")
            return False
        
        try:
            # Generate template
            template = self._generate_profile_template(profile_type)
            
            # Update profile ID to match the name
            template["policy_metadata"]["policy_id"] = f"{profile_name}_{uuid.uuid4().hex[:8]}"
            template["policy_metadata"]["description"] = f"Custom {profile_type} profile: {profile_name}"
            
            # Save template to file
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Created policy template: {profile_path}")
            print(f"📝 Template type: {profile_type}")
            print(f"🔧 Use 'edit {profile_name}' to customize the configuration")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create policy: {e}")
            return False
    
    def edit_policy(self, profile_name: str) -> bool:
        """Edit an existing policy configuration."""
        print(f"✏️  Editing policy: {profile_name}")
        
        # Check custom profiles first
        profile_path = self.custom_profiles_dir / f"{profile_name}.json"
        
        # If not in custom, check if it's a default profile
        if not profile_path.exists():
            default_path = self.default_profiles_dir / f"{profile_name}.json"
            if default_path.exists():
                print(f"📋 {profile_name} is a default profile")
                response = input("📤 Copy to custom profiles for editing? (y/N): ").strip().lower()
                if response == 'y':
                    try:
                        shutil.copy2(default_path, profile_path)
                        print(f"✅ Copied to custom profiles: {profile_path}")
                    except Exception as e:
                        print(f"❌ Failed to copy profile: {e}")
                        return False
                else:
                    print("❌ Cannot edit default profiles directly")
                    return False
            else:
                print(f"❌ Profile not found: {profile_name}")
                print("💡 Use 'list-profiles' to see available profiles")
                print("💡 Use 'create' to create a new profile")
                return False
        
        # Create backup before editing
        backup_path = self._backup_profile(profile_path)
        if backup_path:
            print(f"💾 Backup created: {backup_path.name}")
        
        # Validate before editing
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                policy_data = json.load(f)
            
            is_valid, errors = self._validate_policy(policy_data)
            if not is_valid:
                print("⚠️  Profile has validation issues:")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"   • {error}")
                if len(errors) > 5:
                    print(f"   ... and {len(errors) - 5} more issues")
                
                response = input("📝 Continue editing anyway? (y/N): ").strip().lower()
                if response != 'y':
                    return False
        
        except Exception as e:
            print(f"⚠️  Could not validate profile before editing: {e}")
        
        # Launch editor
        print(f"🚀 Opening in {self.editor}...")
        print("💡 Save and close the editor when finished")
        
        edit_success = self._edit_file_interactive(profile_path)
        
        if not edit_success:
            print("❌ Editor session failed")
            if backup_path:
                print("🔄 Restoring from backup...")
                self._restore_from_backup(profile_path, backup_path)
            return False
        
        # Validate after editing
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                edited_data = json.load(f)
            
            is_valid, errors = self._validate_policy(edited_data)
            
            if is_valid:
                print("✅ Policy validation passed")
                print(f"💾 Changes saved to: {profile_path}")
                return True
            else:
                print("❌ Policy validation failed:")
                for error in errors:
                    print(f"   • {error}")
                
                response = input("🔄 Restore from backup? (Y/n): ").strip().lower()
                if response != 'n' and backup_path:
                    self._restore_from_backup(profile_path, backup_path)
                    print("✅ Restored from backup")
                else:
                    print("⚠️  Invalid policy saved - use 'validate' to check issues")
                
                return False
        
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON syntax: {e}")
            if backup_path:
                response = input("🔄 Restore from backup? (Y/n): ").strip().lower()
                if response != 'n':
                    self._restore_from_backup(profile_path, backup_path)
                    print("✅ Restored from backup")
            return False
        
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False
    
    def validate_policy(self, profile_name: str) -> bool:
        """Validate a policy configuration."""
        print(f"🔍 Validating policy: {profile_name}")
        
        # Find the profile
        profile_path = self.custom_profiles_dir / f"{profile_name}.json"
        if not profile_path.exists():
            profile_path = self.default_profiles_dir / f"{profile_name}.json"
            if not profile_path.exists():
                print(f"❌ Profile not found: {profile_name}")
                return False
        
        try:
            # Load and validate
            with open(profile_path, 'r', encoding='utf-8') as f:
                policy_data = json.load(f)
            
            is_valid, errors = self._validate_policy(policy_data)
            
            if is_valid:
                print("✅ Policy validation passed")
                
                # Show policy summary
                metadata = policy_data.get("policy_metadata", {})
                execution = policy_data.get("execution_profile", {})
                
                print(f"📋 Policy Summary:")
                print(f"   ID: {metadata.get('policy_id', 'N/A')}")
                print(f"   Type: {metadata.get('profile_type', 'N/A')}")
                print(f"   Version: {metadata.get('version', 'N/A')}")
                print(f"   Priority: {execution.get('priority', 'N/A')}")
                print(f"   Timeout: {execution.get('timeout_seconds', 'N/A')}s")
                print(f"   Max Tasks: {execution.get('max_concurrent_tasks', 'N/A')}")
                
                return True
            else:
                print(f"❌ Policy validation failed ({len(errors)} issues):")
                for i, error in enumerate(errors, 1):
                    print(f"   {i}. {error}")
                
                return False
        
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON syntax: {e}")
            return False
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False
    
    def list_profiles(self) -> None:
        """List all available policy profiles."""
        print("📋 Available Policy Profiles")
        print("=" * 50)
        
        # List default profiles
        print("\n🔒 Default Profiles:")
        default_profiles = []
        if self.default_profiles_dir.exists():
            for profile_file in sorted(self.default_profiles_dir.glob("*.json")):
                profile_name = profile_file.stem
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        policy_data = json.load(f)
                    
                    metadata = policy_data.get("policy_metadata", {})
                    execution = policy_data.get("execution_profile", {})
                    
                    profile_info = {
                        "name": profile_name,
                        "type": metadata.get("profile_type", "unknown"),
                        "priority": execution.get("priority", "N/A"),
                        "description": metadata.get("description", "No description")
                    }
                    default_profiles.append(profile_info)
                    
                except Exception as e:
                    default_profiles.append({
                        "name": profile_name,
                        "type": "error",
                        "priority": "N/A",
                        "description": f"Error loading: {e}"
                    })
        
        if default_profiles:
            for profile in default_profiles:
                print(f"   📁 {profile['name']} ({profile['type']}) - Priority {profile['priority']}")
                print(f"      {profile['description']}")
                print()
        else:
            print("   (No default profiles found)")
        
        # List custom profiles
        print("\n✏️  Custom Profiles:")
        custom_profiles = []
        if self.custom_profiles_dir.exists():
            for profile_file in sorted(self.custom_profiles_dir.glob("*.json")):
                profile_name = profile_file.stem
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        policy_data = json.load(f)
                    
                    metadata = policy_data.get("policy_metadata", {})
                    execution = policy_data.get("execution_profile", {})
                    
                    # Check if valid
                    is_valid, _ = self._validate_policy(policy_data)
                    status = "✅" if is_valid else "❌"
                    
                    profile_info = {
                        "name": profile_name,
                        "type": metadata.get("profile_type", "unknown"),
                        "priority": execution.get("priority", "N/A"),
                        "description": metadata.get("description", "No description"),
                        "status": status,
                        "modified": profile_file.stat().st_mtime
                    }
                    custom_profiles.append(profile_info)
                    
                except Exception as e:
                    custom_profiles.append({
                        "name": profile_name,
                        "type": "error",
                        "priority": "N/A",
                        "description": f"Error loading: {e}",
                        "status": "❌",
                        "modified": 0
                    })
        
        if custom_profiles:
            # Sort by modification time (newest first)
            custom_profiles.sort(key=lambda x: x['modified'], reverse=True)
            
            for profile in custom_profiles:
                print(f"   {profile['status']} {profile['name']} ({profile['type']}) - Priority {profile['priority']}")
                print(f"      {profile['description']}")
                print()
        else:
            print("   (No custom profiles found)")
        
        # Usage hints
        print("\n💡 Usage:")
        print("   • Create new profile: create <name> --type <type>")
        print("   • Edit profile: edit <name>")
        print("   • Validate profile: validate <name>")
        print("   • Profile types: audit, realtime, diagnostic, stress, custom")


def main():
    """CLI entry point for policy configuration editor."""
    parser = argparse.ArgumentParser(
        description="GitBridge Policy Configuration Editor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create my-audit-config --type audit
  %(prog)s edit my-audit-config
  %(prog)s validate my-audit-config
  %(prog)s list-profiles

Profile Types:
  audit      - Comprehensive compliance logging (high priority, long timeout)
  realtime   - High-performance processing (max priority, short timeout)
  diagnostic - Debug and troubleshooting (medium priority, long timeout)  
  stress     - Load testing and stress scenarios (low priority, high concurrency)
  custom     - General purpose customizable profile

Environment Variables:
  EDITOR     - Preferred text editor (default: nano)
  VISUAL     - Alternative editor specification
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new policy configuration')
    create_parser.add_argument('name', help='Name for the new policy profile')
    create_parser.add_argument('--type', '-t', required=True, 
                              choices=['audit', 'realtime', 'diagnostic', 'stress', 'custom'],
                              help='Type of profile to create')
    
    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit existing policy configuration')
    edit_parser.add_argument('name', help='Name of policy profile to edit')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate policy configuration')
    validate_parser.add_argument('name', help='Name of policy profile to validate')
    
    # List profiles command
    list_parser = subparsers.add_parser('list-profiles', help='List all available policy profiles')
    
    # Version
    parser.add_argument('--version', action='version', version='GitBridge Policy Editor v1.0.0')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize editor
    try:
        editor = PolicyConfigEditor()
    except Exception as e:
        print(f"❌ Failed to initialize policy editor: {e}")
        return 1
    
    # Execute command
    success = True
    
    try:
        if args.command == 'create':
            success = editor.create_policy(args.name, args.type)
        
        elif args.command == 'edit':
            success = editor.edit_policy(args.name)
        
        elif args.command == 'validate':
            success = editor.validate_policy(args.name)
        
        elif args.command == 'list-profiles':
            editor.list_profiles()
        
        else:
            print(f"❌ Unknown command: {args.command}")
            success = False
    
    except KeyboardInterrupt:
        print("\n🚫 Operation cancelled by user")
        success = False
    except Exception as e:
        print(f"❌ Command failed: {e}")
        success = False
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 