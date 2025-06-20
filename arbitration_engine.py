#!/usr/bin/env python3
"""
GitBridge Arbitration Engine
Phase: GBP22
Part: P22P1
Step: P22P1S1
Task: P22P1S1T1 - Central Arbitration Controller

Central controller to manage agent output conflicts.
Compare competing outputs, determine winner via strategy plugin,
dispatch fallback execution if needed.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P22P1 Schema]
"""

import json
import logging
import argparse
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import sys

logger = logging.getLogger(__name__)

@dataclass
class AgentOutput:
    """Represents an agent's output for arbitration."""
    agent_id: str
    task_id: str
    subtask_id: str
    output: Any
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: Optional[int] = None
    error_count: int = 0

@dataclass
class ArbitrationResult:
    """Represents the result of an arbitration decision."""
    winner_agent_id: str
    winning_output: Any
    confidence: float
    strategy_used: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    fallback_triggered: bool = False
    fallback_reason: Optional[str] = None

@dataclass
class ArbitrationConflict:
    """Represents a conflict between agent outputs."""
    conflict_id: str
    task_id: str
    subtask_id: str
    agent_outputs: List[AgentOutput]
    conflict_type: str  # "contradiction", "quality_dispute", "timeout", "error"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolution_strategy: Optional[str] = None

class ArbitrationPluginBase:
    """
    Base class for arbitration strategy plugins.
    
    Phase: GBP22
    Part: P22P1
    Step: P22P1S1
    Task: P22P1S1T1 - Plugin Base Implementation
    """
    
    @property
    def strategy_name(self) -> str:
        """Return the name of this arbitration strategy."""
        raise NotImplementedError
        
    @property
    def strategy_version(self) -> str:
        """Return the version of this arbitration strategy."""
        return "1.0.0"
        
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration for this strategy."""
        return True
        
    def arbitrate(
        self, 
        conflict: ArbitrationConflict, 
        config: Optional[Dict[str, Any]] = None
    ) -> ArbitrationResult:
        """
        Arbitrate between conflicting agent outputs.
        
        Args:
            conflict: The conflict to resolve
            config: Optional configuration for the strategy
            
        Returns:
            ArbitrationResult: The arbitration decision
        """
        raise NotImplementedError

class ArbitrationEngine:
    """
    Central arbitration engine for managing agent output conflicts.
    
    Phase: GBP22
    Part: P22P1
    Step: P22P1S1
    Task: P22P1S1T1 - Core Implementation
    
    Features:
    - Load and manage arbitration strategy plugins
    - Compare competing agent outputs
    - Determine winners via strategy plugins
    - Dispatch fallback execution when needed
    - Log all arbitration decisions
    """
    
    def __init__(self, plugins_dir: str = "plugins/arbitration", config_path: str = "arbitration_config.json"):
        """
        Initialize arbitration engine.
        
        Args:
            plugins_dir: Directory containing arbitration strategy plugins
            config_path: Path to arbitration configuration file
        """
        self.plugins_dir = Path(plugins_dir)
        self.config_path = Path(config_path)
        self.strategies: Dict[str, ArbitrationPluginBase] = {}
        self.conflicts_log: List[ArbitrationConflict] = []
        self.results_log: List[ArbitrationResult] = []
        
        # Ensure plugins directory exists
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Load strategy plugins
        self._load_strategies()
        
        logger.info(f"[P22P1S1T1] ArbitrationEngine initialized with {len(self.strategies)} strategies")
        
    def _load_config(self) -> Dict[str, Any]:
        """Load arbitration configuration."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"[P22P1S1T1] Loaded arbitration config from {self.config_path}")
                return config
            except Exception as e:
                logger.warning(f"[P22P1S1T1] Failed to load config: {e}")
                
        # Default configuration
        default_config = {
            "default_strategy": "majority_vote",
            "fallback_strategy": "confidence_weight",
            "timeout_ms": 30000,
            "max_retries": 3,
            "logging": {
                "enabled": True,
                "level": "INFO"
            }
        }
        
        # Save default config
        self._save_config(default_config)
        return default_config
        
    def _save_config(self, config: Dict[str, Any]):
        """Save arbitration configuration."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"[P22P1S1T1] Saved arbitration config to {self.config_path}")
        except Exception as e:
            logger.error(f"[P22P1S1T1] Failed to save config: {e}")
            
    def _load_strategies(self):
        """Load arbitration strategy plugins."""
        if not self.plugins_dir.exists():
            logger.warning(f"[P22P1S1T1] Plugins directory {self.plugins_dir} does not exist")
            return
            
        for plugin_file in self.plugins_dir.glob("strategy_*.py"):
            try:
                # Load plugin module
                spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find strategy class
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, ArbitrationPluginBase) and 
                        attr != ArbitrationPluginBase):
                        
                        strategy = attr()
                        self.strategies[strategy.strategy_name] = strategy
                        logger.info(f"[P22P1S1T1] Loaded strategy: {strategy.strategy_name}")
                        break
                        
            except Exception as e:
                logger.error(f"[P22P1S1T1] Failed to load strategy from {plugin_file}: {e}")
                
    def register_strategy(self, strategy: ArbitrationPluginBase) -> bool:
        """
        Register a new arbitration strategy.
        
        Args:
            strategy: Arbitration strategy to register
            
        Returns:
            bool: True if registration successful
        """
        try:
            self.strategies[strategy.strategy_name] = strategy
            logger.info(f"[P22P1S1T1] Registered strategy: {strategy.strategy_name}")
            return True
        except Exception as e:
            logger.error(f"[P22P1S1T1] Failed to register strategy: {e}")
            return False
            
    def arbitrate_conflict(
        self, 
        agent_outputs: List[AgentOutput], 
        task_id: str,
        subtask_id: str,
        strategy_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> ArbitrationResult:
        """
        Arbitrate between conflicting agent outputs.
        
        Args:
            agent_outputs: List of agent outputs to arbitrate
            task_id: Task ID
            subtask_id: Subtask ID
            strategy_name: Name of strategy to use (default from config)
            config: Optional configuration for the strategy
            
        Returns:
            ArbitrationResult: The arbitration decision
        """
        if len(agent_outputs) < 2:
            raise ValueError("At least 2 agent outputs required for arbitration")
            
        # Create conflict
        conflict_id = f"conflict_{len(self.conflicts_log) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conflict = ArbitrationConflict(
            conflict_id=conflict_id,
            task_id=task_id,
            subtask_id=subtask_id,
            agent_outputs=agent_outputs,
            conflict_type=self._determine_conflict_type(agent_outputs)
        )
        
        # Log conflict
        self.conflicts_log.append(conflict)
        
        # Determine strategy
        if strategy_name is None:
            strategy_name = self.config.get("default_strategy", "majority_vote")
            
        if strategy_name not in self.strategies:
            logger.warning(f"[P22P1S1T1] Strategy {strategy_name} not found, using fallback")
            strategy_name = self.config.get("fallback_strategy", "confidence_weight")
            
        strategy = self.strategies[strategy_name]
        conflict.resolution_strategy = strategy_name
        
        # Perform arbitration
        try:
            result = strategy.arbitrate(conflict, config)
            result.strategy_used = strategy_name
            
            # Log result
            self.results_log.append(result)
            
            logger.info(f"[P22P1S1T1] Arbitration completed: {result.winner_agent_id} wins using {strategy_name}")
            return result
            
        except Exception as e:
            logger.error(f"[P22P1S1T1] Arbitration failed: {e}")
            
            # Fallback to simple confidence-based selection
            return self._fallback_arbitration(conflict, e)
            
    def _determine_conflict_type(self, agent_outputs: List[AgentOutput]) -> str:
        """Determine the type of conflict between agent outputs."""
        # Check for errors
        error_outputs = [output for output in agent_outputs if output.error_count > 0]
        if error_outputs:
            return "error"
            
        # Check for timeouts
        timeout_outputs = [output for output in agent_outputs if output.execution_time_ms and output.execution_time_ms > self.config.get("timeout_ms", 30000)]
        if timeout_outputs:
            return "timeout"
            
        # Check for contradictions (different outputs)
        outputs = [str(output.output) for output in agent_outputs]
        if len(set(outputs)) > 1:
            return "contradiction"
            
        # Check for quality disputes (different confidence levels)
        confidences = [output.confidence for output in agent_outputs]
        if max(confidences) - min(confidences) > 0.3:  # 30% confidence difference
            return "quality_dispute"
            
        return "minor_dispute"
        
    def _fallback_arbitration(self, conflict: ArbitrationConflict, error: Exception) -> ArbitrationResult:
        """Fallback arbitration when primary strategy fails."""
        # Simple confidence-based selection
        best_output = max(conflict.agent_outputs, key=lambda x: x.confidence)
        
        result = ArbitrationResult(
            winner_agent_id=best_output.agent_id,
            winning_output=best_output.output,
            confidence=best_output.confidence,
            strategy_used="fallback_confidence",
            fallback_triggered=True,
            fallback_reason=str(error)
        )
        
        self.results_log.append(result)
        logger.info(f"[P22P1S1T1] Fallback arbitration: {best_output.agent_id} wins")
        return result
        
    def get_arbitration_history(
        self,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        strategy: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ArbitrationResult]:
        """
        Get arbitration history with optional filters.
        
        Args:
            task_id: Filter by task ID
            agent_id: Filter by agent ID
            strategy: Filter by strategy used
            limit: Maximum number of results
            
        Returns:
            List[ArbitrationResult]: Filtered arbitration results
        """
        results = self.results_log
        
        if task_id:
            results = [r for r in results if any(
                output.task_id == task_id for output in self.conflicts_log if r.winner_agent_id in [o.agent_id for o in output.agent_outputs]
            )]
            
        if agent_id:
            results = [r for r in results if r.winner_agent_id == agent_id]
            
        if strategy:
            results = [r for r in results if r.strategy_used == strategy]
            
        if limit:
            results = results[-limit:]
            
        return results
        
    def export_arbitration_logs(self, output_path: str = "arbitration_logs.json") -> bool:
        """
        Export arbitration logs to file.
        
        Args:
            output_path: Path to output file
            
        Returns:
            bool: True if export successful
        """
        try:
            export_data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_conflicts": len(self.conflicts_log),
                "total_results": len(self.results_log),
                "strategies_loaded": list(self.strategies.keys()),
                "conflicts": [asdict(conflict) for conflict in self.conflicts_log],
                "results": [asdict(result) for result in self.results_log]
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
                
            logger.info(f"[P22P1S1T1] Exported arbitration logs to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"[P22P1S1T1] Failed to export logs: {e}")
            return False
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get arbitration statistics."""
        if not self.results_log:
            return {"total_arbitrations": 0}
            
        # Strategy usage
        strategy_counts = {}
        for result in self.results_log:
            strategy_counts[result.strategy_used] = strategy_counts.get(result.strategy_used, 0) + 1
            
        # Agent wins
        agent_wins = {}
        for result in self.results_log:
            agent_wins[result.winner_agent_id] = agent_wins.get(result.winner_agent_id, 0) + 1
            
        # Fallback usage
        fallback_count = sum(1 for result in self.results_log if result.fallback_triggered)
        
        return {
            "total_arbitrations": len(self.results_log),
            "strategy_usage": strategy_counts,
            "agent_wins": agent_wins,
            "fallback_count": fallback_count,
            "strategies_loaded": len(self.strategies)
        }

def main():
    """Main function for testing arbitration engine."""
    parser = argparse.ArgumentParser(description='GitBridge Arbitration Engine')
    parser.add_argument('--test', action='store_true', help='Run test arbitration')
    parser.add_argument('--stats', action='store_true', help='Show arbitration statistics')
    parser.add_argument('--export', help='Export arbitration logs to specified file')
    parser.add_argument('--strategy', help='Test specific strategy')
    
    args = parser.parse_args()
    
    engine = ArbitrationEngine()
    
    if args.stats:
        stats = engine.get_statistics()
        print("📊 Arbitration Statistics:")
        print(f"  Total arbitrations: {stats['total_arbitrations']}")
        print(f"  Strategies loaded: {stats['strategies_loaded']}")
        print(f"  Strategy usage: {stats['strategy_usage']}")
        print(f"  Agent wins: {stats['agent_wins']}")
        print(f"  Fallback count: {stats['fallback_count']}")
        
    elif args.export:
        success = engine.export_arbitration_logs(args.export)
        if success:
            print(f"✅ Arbitration logs exported to {args.export}")
        else:
            print("❌ Failed to export logs")
            
    elif args.test:
        print("🧪 Testing arbitration engine...")
        
        # Create test agent outputs
        outputs = [
            AgentOutput(
                agent_id="openai_gpt4o",
                task_id="test_task",
                subtask_id="test_subtask",
                output="The answer is 42",
                confidence=0.85,
                execution_time_ms=1500
            ),
            AgentOutput(
                agent_id="grok_3",
                task_id="test_task",
                subtask_id="test_subtask",
                output="The answer is 42",
                confidence=0.92,
                execution_time_ms=1200
            ),
            AgentOutput(
                agent_id="cursor_assistant",
                task_id="test_task",
                subtask_id="test_subtask",
                output="The answer is 43",
                confidence=0.78,
                execution_time_ms=2000
            )
        ]
        
        # Perform arbitration
        result = engine.arbitrate_conflict(outputs, "test_task", "test_subtask", args.strategy)
        
        print(f"🏆 Arbitration Result:")
        print(f"  Winner: {result.winner_agent_id}")
        print(f"  Output: {result.winning_output}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Strategy: {result.strategy_used}")
        print(f"  Fallback: {result.fallback_triggered}")
        
    else:
        print("🔍 Arbitration Engine Demo")
        print("Available commands:")
        print("  --test: Run test arbitration")
        print("  --stats: Show statistics")
        print("  --export <file>: Export logs")
        print("  --strategy <name>: Test specific strategy")

if __name__ == "__main__":
    main() 