#!/usr/bin/env python3
"""
GitBridge Fallback Policy Editor
Phase: GBP22
Part: P22P2
Step: P22P2S1
Task: P22P2S1T1 - Fallback Policy Editor Implementation

CLI + JSON-based editor for editing fallback strategies.
Define agent fallback chains (per task type), allow live updates,
validate schema.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P22P2 Schema]
"""

import json
import logging
import argparse
import sys
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
import jsonschema

logger = logging.getLogger(__name__)

@dataclass
class FallbackChain:
    """Represents a fallback chain for a specific task type."""
    task_type: str
    primary_agent: str
    fallback_agents: List[str]
    max_retries: int = 3
    timeout_ms: int = 30000
    strategy: str = "sequential"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FallbackPolicy:
    """Represents a complete fallback policy configuration."""
    policy_id: str
    name: str
    description: str
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    fallback_chains: Dict[str, FallbackChain] = field(default_factory=dict)
    global_settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class FallbackPolicyEditor:
    """
    CLI and JSON-based editor for fallback policies.
    
    Phase: GBP22
    Part: P22P2
    Step: P22P2S1
    Task: P22P2S1T1 - Core Implementation
    
    Features:
    - Define agent fallback chains per task type
    - Live updates and validation
    - Schema validation
    - Interactive CLI editing
    """
    
    def __init__(self, config_path: str = "fallback_policies.json"):
        """
        Initialize fallback policy editor.
        
        Args:
            config_path: Path to fallback policies configuration file
        """
        self.config_path = Path(config_path)
        self.schema = self._get_schema()
        self.policy: Optional[FallbackPolicy] = None
        
        logger.info(f"[P22P2S1T1] FallbackPolicyEditor initialized with config: {config_path}")
        
    def _get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for fallback policy validation."""
        return {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "version": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
                "fallback_chains": {
                    "type": "object",
                    "patternProperties": {
                        "^.*$": {
                            "type": "object",
                            "properties": {
                                "task_type": {"type": "string"},
                                "primary_agent": {"type": "string"},
                                "fallback_agents": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "max_retries": {"type": "integer", "minimum": 1},
                                "timeout_ms": {"type": "integer", "minimum": 1000},
                                "strategy": {"type": "string", "enum": ["sequential", "parallel", "weighted"]},
                                "metadata": {"type": "object"}
                            },
                            "required": ["task_type", "primary_agent", "fallback_agents"]
                        }
                    }
                },
                "global_settings": {"type": "object"},
                "metadata": {"type": "object"}
            },
            "required": ["policy_id", "name", "description", "fallback_chains"]
        }
        
    def load_policy(self) -> Optional[FallbackPolicy]:
        """
        Load fallback policy from file.
        
        Returns:
            FallbackPolicy or None if loading failed
        """
        if not self.config_path.exists():
            logger.info(f"[P22P2S1T1] Creating new fallback policy at {self.config_path}")
            return self._create_default_policy()
            
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                
            # Validate schema
            jsonschema.validate(instance=data, schema=self.schema)
            
            # Convert to FallbackPolicy object
            fallback_chains = {}
            for task_type, chain_data in data.get("fallback_chains", {}).items():
                fallback_chains[task_type] = FallbackChain(**chain_data)
                
            self.policy = FallbackPolicy(
                policy_id=data["policy_id"],
                name=data["name"],
                description=data["description"],
                version=data.get("version", "1.0.0"),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                fallback_chains=fallback_chains,
                global_settings=data.get("global_settings", {}),
                metadata=data.get("metadata", {})
            )
            
            logger.info(f"[P22P2S1T1] Loaded fallback policy: {self.policy.name}")
            return self.policy
            
        except Exception as e:
            logger.error(f"[P22P2S1T1] Failed to load policy: {e}")
            return None
            
    def _create_default_policy(self) -> FallbackPolicy:
        """Create a default fallback policy."""
        policy = FallbackPolicy(
            policy_id=f"policy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Default Fallback Policy",
            description="Default fallback policy for GitBridge multi-agent system",
            fallback_chains={
                "code_review": FallbackChain(
                    task_type="code_review",
                    primary_agent="openai_gpt4o",
                    fallback_agents=["grok_3", "cursor_assistant"],
                    strategy="sequential"
                ),
                "analysis": FallbackChain(
                    task_type="analysis",
                    primary_agent="grok_3",
                    fallback_agents=["openai_gpt4o", "cursor_assistant"],
                    strategy="sequential"
                ),
                "general": FallbackChain(
                    task_type="general",
                    primary_agent="openai_gpt4o",
                    fallback_agents=["grok_3", "cursor_assistant"],
                    strategy="sequential"
                )
            },
            global_settings={
                "default_timeout_ms": 30000,
                "default_max_retries": 3,
                "enable_logging": True
            }
        )
        
        self.policy = policy
        self.save_policy()
        return policy
        
    def save_policy(self) -> bool:
        """
        Save fallback policy to file.
        
        Returns:
            bool: True if save successful
        """
        if self.policy is None:
            logger.error("[P22P2S1T1] No policy to save")
            return False
            
        try:
            # Update timestamp
            self.policy.updated_at = datetime.now(timezone.utc)
            
            # Convert to dictionary
            data = asdict(self.policy)
            
            # Validate before saving
            jsonschema.validate(instance=data, schema=self.schema)
            
            # Save to file
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            logger.info(f"[P22P2S1T1] Saved fallback policy to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"[P22P2S1T1] Failed to save policy: {e}")
            return False
            
    def add_fallback_chain(
        self,
        task_type: str,
        primary_agent: str,
        fallback_agents: List[str],
        max_retries: int = 3,
        timeout_ms: int = 30000,
        strategy: str = "sequential",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a new fallback chain.
        
        Args:
            task_type: Type of task for this chain
            primary_agent: Primary agent ID
            fallback_agents: List of fallback agent IDs
            max_retries: Maximum number of retries
            timeout_ms: Timeout in milliseconds
            strategy: Fallback strategy (sequential, parallel, weighted)
            metadata: Additional metadata
            
        Returns:
            bool: True if addition successful
        """
        if self.policy is None:
            logger.error("[P22P2S1T1] No policy loaded")
            return False
            
        try:
            chain = FallbackChain(
                task_type=task_type,
                primary_agent=primary_agent,
                fallback_agents=fallback_agents,
                max_retries=max_retries,
                timeout_ms=timeout_ms,
                strategy=strategy,
                metadata=metadata or {}
            )
            
            self.policy.fallback_chains[task_type] = chain
            logger.info(f"[P22P2S1T1] Added fallback chain for task type: {task_type}")
            return True
            
        except Exception as e:
            logger.error(f"[P22P2S1T1] Failed to add fallback chain: {e}")
            return False
            
    def remove_fallback_chain(self, task_type: str) -> bool:
        """
        Remove a fallback chain.
        
        Args:
            task_type: Task type to remove
            
        Returns:
            bool: True if removal successful
        """
        if self.policy is None:
            logger.error("[P22P2S1T1] No policy loaded")
            return False
            
        if task_type in self.policy.fallback_chains:
            del self.policy.fallback_chains[task_type]
            logger.info(f"[P22P2S1T1] Removed fallback chain for task type: {task_type}")
            return True
        else:
            logger.warning(f"[P22P2S1T1] Task type {task_type} not found")
            return False
            
    def update_fallback_chain(
        self,
        task_type: str,
        primary_agent: Optional[str] = None,
        fallback_agents: Optional[List[str]] = None,
        max_retries: Optional[int] = None,
        timeout_ms: Optional[int] = None,
        strategy: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing fallback chain.
        
        Args:
            task_type: Task type to update
            primary_agent: New primary agent (optional)
            fallback_agents: New fallback agents (optional)
            max_retries: New max retries (optional)
            timeout_ms: New timeout (optional)
            strategy: New strategy (optional)
            metadata: New metadata (optional)
            
        Returns:
            bool: True if update successful
        """
        if self.policy is None:
            logger.error("[P22P2S1T1] No policy loaded")
            return False
            
        if task_type not in self.policy.fallback_chains:
            logger.error(f"[P22P2S1T1] Task type {task_type} not found")
            return False
            
        try:
            chain = self.policy.fallback_chains[task_type]
            
            if primary_agent is not None:
                chain.primary_agent = primary_agent
            if fallback_agents is not None:
                chain.fallback_agents = fallback_agents
            if max_retries is not None:
                chain.max_retries = max_retries
            if timeout_ms is not None:
                chain.timeout_ms = timeout_ms
            if strategy is not None:
                chain.strategy = strategy
            if metadata is not None:
                chain.metadata.update(metadata)
                
            logger.info(f"[P22P2S1T1] Updated fallback chain for task type: {task_type}")
            return True
            
        except Exception as e:
            logger.error(f"[P22P2S1T1] Failed to update fallback chain: {e}")
            return False
            
    def get_fallback_chain(self, task_type: str) -> Optional[FallbackChain]:
        """
        Get a fallback chain by task type.
        
        Args:
            task_type: Task type to retrieve
            
        Returns:
            FallbackChain or None if not found
        """
        if self.policy is None:
            return None
            
        return self.policy.fallback_chains.get(task_type)
        
    def list_fallback_chains(self) -> List[str]:
        """
        List all available fallback chains.
        
        Returns:
            List[str]: List of task types
        """
        if self.policy is None:
            return []
            
        return list(self.policy.fallback_chains.keys())
        
    def validate_policy(self) -> Dict[str, Any]:
        """
        Validate the current policy.
        
        Returns:
            Dict[str, Any]: Validation results
        """
        if self.policy is None:
            return {"valid": False, "errors": ["No policy loaded"]}
            
        errors = []
        warnings = []
        
        # Check for duplicate task types
        task_types = list(self.policy.fallback_chains.keys())
        if len(task_types) != len(set(task_types)):
            errors.append("Duplicate task types found")
            
        # Check each chain
        for task_type, chain in self.policy.fallback_chains.items():
            # Check for duplicate agents
            agents = [chain.primary_agent] + chain.fallback_agents
            if len(agents) != len(set(agents)):
                errors.append(f"Duplicate agents in chain for {task_type}")
                
            # Check for empty fallback agents
            if not chain.fallback_agents:
                warnings.append(f"No fallback agents for {task_type}")
                
            # Check timeout
            if chain.timeout_ms < 1000:
                warnings.append(f"Very short timeout ({chain.timeout_ms}ms) for {task_type}")
                
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    def export_policy(self, output_path: str) -> bool:
        """
        Export policy to a different file.
        
        Args:
            output_path: Path to export file
            
        Returns:
            bool: True if export successful
        """
        if self.policy is None:
            logger.error("[P22P2S1T1] No policy to export")
            return False
            
        try:
            data = asdict(self.policy)
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            logger.info(f"[P22P2S1T1] Exported policy to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"[P22P2S1T1] Failed to export policy: {e}")
            return False

def main():
    """Main function for CLI interface."""
    parser = argparse.ArgumentParser(description='GitBridge Fallback Policy Editor')
    parser.add_argument('--config', default='fallback_policies.json', help='Configuration file path')
    parser.add_argument('--list', action='store_true', help='List all fallback chains')
    parser.add_argument('--show', help='Show fallback chain for specific task type')
    parser.add_argument('--add', nargs=4, metavar=('TASK_TYPE', 'PRIMARY_AGENT', 'FALLBACK_AGENTS', 'STRATEGY'), help='Add new fallback chain')
    parser.add_argument('--remove', help='Remove fallback chain for task type')
    parser.add_argument('--update', nargs=3, metavar=('TASK_TYPE', 'FIELD', 'VALUE'), help='Update fallback chain field')
    parser.add_argument('--validate', action='store_true', help='Validate current policy')
    parser.add_argument('--export', help='Export policy to specified file')
    parser.add_argument('--interactive', action='store_true', help='Start interactive mode')
    
    args = parser.parse_args()
    
    editor = FallbackPolicyEditor(args.config)
    policy = editor.load_policy()
    
    if policy is None:
        print("❌ Failed to load policy")
        return 1
        
    if args.list:
        print("📋 Fallback Chains:")
        for task_type in editor.list_fallback_chains():
            chain = editor.get_fallback_chain(task_type)
            print(f"  {task_type}: {chain.primary_agent} -> {', '.join(chain.fallback_agents)} ({chain.strategy})")
            
    elif args.show:
        chain = editor.get_fallback_chain(args.show)
        if chain:
            print(f"🔍 Fallback Chain for {args.show}:")
            print(f"  Primary Agent: {chain.primary_agent}")
            print(f"  Fallback Agents: {', '.join(chain.fallback_agents)}")
            print(f"  Strategy: {chain.strategy}")
            print(f"  Max Retries: {chain.max_retries}")
            print(f"  Timeout: {chain.timeout_ms}ms")
        else:
            print(f"❌ Task type '{args.show}' not found")
            
    elif args.add:
        task_type, primary_agent, fallback_agents_str, strategy = args.add
        fallback_agents = fallback_agents_str.split(',')
        
        success = editor.add_fallback_chain(
            task_type=task_type,
            primary_agent=primary_agent,
            fallback_agents=fallback_agents,
            strategy=strategy
        )
        
        if success:
            print(f"✅ Added fallback chain for {task_type}")
            editor.save_policy()
        else:
            print("❌ Failed to add fallback chain")
            
    elif args.remove:
        success = editor.remove_fallback_chain(args.remove)
        if success:
            print(f"✅ Removed fallback chain for {args.remove}")
            editor.save_policy()
        else:
            print(f"❌ Failed to remove fallback chain for {args.remove}")
            
    elif args.update:
        task_type, field, value = args.update
        success = False
        
        if field == "primary_agent":
            success = editor.update_fallback_chain(task_type, primary_agent=value)
        elif field == "fallback_agents":
            agents = value.split(',')
            success = editor.update_fallback_chain(task_type, fallback_agents=agents)
        elif field == "strategy":
            success = editor.update_fallback_chain(task_type, strategy=value)
        elif field == "max_retries":
            success = editor.update_fallback_chain(task_type, max_retries=int(value))
        elif field == "timeout_ms":
            success = editor.update_fallback_chain(task_type, timeout_ms=int(value))
        else:
            print(f"❌ Unknown field: {field}")
            
        if success:
            print(f"✅ Updated {field} for {task_type}")
            editor.save_policy()
        else:
            print(f"❌ Failed to update {field} for {task_type}")
            
    elif args.validate:
        validation = editor.validate_policy()
        if validation["valid"]:
            print("✅ Policy is valid")
        else:
            print("❌ Policy has errors:")
            for error in validation["errors"]:
                print(f"  - {error}")
                
        if validation["warnings"]:
            print("⚠️  Warnings:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")
                
    elif args.export:
        success = editor.export_policy(args.export)
        if success:
            print(f"✅ Policy exported to {args.export}")
        else:
            print("❌ Failed to export policy")
            
    elif args.interactive:
        print("🔧 Interactive Fallback Policy Editor")
        print("Type 'help' for available commands")
        
        while True:
            try:
                command = input("\n> ").strip()
                
                if command == "help":
                    print("Available commands:")
                    print("  list - List all fallback chains")
                    print("  show <task_type> - Show specific chain")
                    print("  add <task_type> <primary> <fallbacks> <strategy> - Add chain")
                    print("  remove <task_type> - Remove chain")
                    print("  validate - Validate policy")
                    print("  save - Save policy")
                    print("  quit - Exit")
                    
                elif command == "list":
                    for task_type in editor.list_fallback_chains():
                        chain = editor.get_fallback_chain(task_type)
                        print(f"  {task_type}: {chain.primary_agent} -> {', '.join(chain.fallback_agents)}")
                        
                elif command.startswith("show "):
                    task_type = command[5:]
                    chain = editor.get_fallback_chain(task_type)
                    if chain:
                        print(f"Primary: {chain.primary_agent}")
                        print(f"Fallbacks: {', '.join(chain.fallback_agents)}")
                        print(f"Strategy: {chain.strategy}")
                    else:
                        print(f"Task type '{task_type}' not found")
                        
                elif command == "validate":
                    validation = editor.validate_policy()
                    if validation["valid"]:
                        print("✅ Policy is valid")
                    else:
                        print("❌ Policy has errors")
                        for error in validation["errors"]:
                            print(f"  - {error}")
                            
                elif command == "save":
                    if editor.save_policy():
                        print("✅ Policy saved")
                    else:
                        print("❌ Failed to save policy")
                        
                elif command == "quit":
                    break
                    
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                
    else:
        print("🔧 Fallback Policy Editor")
        print("Available commands:")
        print("  --list: List all fallback chains")
        print("  --show <task_type>: Show specific chain")
        print("  --add <task_type> <primary> <fallbacks> <strategy>: Add chain")
        print("  --remove <task_type>: Remove chain")
        print("  --validate: Validate policy")
        print("  --export <file>: Export policy")
        print("  --interactive: Start interactive mode")

if __name__ == "__main__":
    main() 