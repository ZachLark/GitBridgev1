#!/usr/bin/env python3
"""
GitBridge Real-Time Arbitration Dashboard
Phase: GBP22
Part: P22P5
Step: P22P5S2
Task: P22P5S2T1 - Real-Time Dashboard CLI Prototype

Real-time dashboard for monitoring and controlling arbitration system.
Provides live metrics, visualization, and manual override capabilities.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P22P5 Schema]
"""

import json
import time
import argparse
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(__file__))

from arbitration_engine import ArbitrationEngine, AgentOutput, ArbitrationResult

class RealTimeArbitrationDashboard:
    """
    Real-time arbitration dashboard CLI.
    
    Phase: GBP22
    Part: P22P5
    Step: P22P5S2
    Task: P22P5S2T1 - Core Implementation
    
    Features:
    - Real-time metrics display
    - Live arbitration monitoring
    - Manual override capabilities
    - Performance visualization
    - System health monitoring
    """
    
    def __init__(self, config_path: str = "arbitration_config.json"):
        """Initialize the dashboard."""
        self.config_path = Path(config_path)
        self.engine = ArbitrationEngine(config_path=str(self.config_path))
        self.running = False
        self.refresh_interval = 2.0  # seconds
        self.metrics_history = []
        self.max_history_size = 100
        
        # Dashboard state
        self.current_arbitrations = []
        self.system_status = "healthy"
        self.last_update = datetime.now(timezone.utc)
        
    def start_dashboard(self):
        """Start the real-time dashboard."""
        self.running = True
        print("🚀 GitBridge Real-Time Arbitration Dashboard")
        print("=" * 50)
        print("Press Ctrl+C to exit")
        print()
        
        try:
            while self.running:
                self._update_display()
                time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped by user")
            self.running = False
            
    def _update_display(self):
        """Update the dashboard display."""
        # Clear screen (works on most terminals)
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Get current metrics
        metrics = self._collect_metrics()
        self.metrics_history.append(metrics)
        
        # Keep history size manageable
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
            
        # Display dashboard
        self._display_header()
        self._display_system_status(metrics)
        self._display_performance_metrics(metrics)
        self._display_strategy_usage(metrics)
        self._display_agent_performance(metrics)
        self._display_recent_arbitrations(metrics)
        self._display_controls()
        
        self.last_update = datetime.now(timezone.utc)
        
    def _display_header(self):
        """Display dashboard header."""
        print("🚀 GitBridge Real-Time Arbitration Dashboard")
        print("=" * 50)
        print(f"Last Update: {self.last_update.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Refresh Interval: {self.refresh_interval}s")
        print()
        
    def _display_system_status(self, metrics: Dict[str, Any]):
        """Display system status."""
        print("📊 SYSTEM STATUS")
        print("-" * 20)
        
        status = metrics.get("system_status", "unknown")
        status_icon = "🟢" if status == "healthy" else "🟡" if status == "degraded" else "🔴"
        
        print(f"Overall Status: {status_icon} {status.upper()}")
        print(f"Active Arbitrations: {metrics.get('active_arbitrations', 0)}")
        print(f"Queue Length: {metrics.get('queue_length', 0)}")
        print(f"System Uptime: {metrics.get('uptime_seconds', 0)}s")
        print()
        
    def _display_performance_metrics(self, metrics: Dict[str, Any]):
        """Display performance metrics."""
        print("⚡ PERFORMANCE METRICS")
        print("-" * 25)
        
        perf = metrics.get("performance", {})
        print(f"Avg Response Time: {perf.get('avg_response_time_ms', 0):.0f}ms")
        print(f"Arbitrations/min: {perf.get('arbitrations_per_minute', 0):.1f}")
        print(f"Error Rate: {perf.get('error_rate', 0):.2%}")
        print(f"Timeout Rate: {perf.get('timeout_rate', 0):.2%}")
        print(f"Fallback Rate: {perf.get('fallback_rate', 0):.2%}")
        print()
        
    def _display_strategy_usage(self, metrics: Dict[str, Any]):
        """Display strategy usage statistics."""
        print("🎯 STRATEGY USAGE")
        print("-" * 18)
        
        strategies = metrics.get("strategy_usage", {})
        total_usage = sum(strategies.values()) if strategies else 1
        
        for strategy, count in strategies.items():
            percentage = (count / total_usage * 100) if total_usage > 0 else 0
            bar_length = int(percentage / 5)  # 5% per character
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"{strategy:15} {bar} {percentage:5.1f}% ({count})")
        print()
        
    def _display_agent_performance(self, metrics: Dict[str, Any]):
        """Display agent performance statistics."""
        print("🤖 AGENT PERFORMANCE")
        print("-" * 22)
        
        agents = metrics.get("agent_performance", {})
        
        print(f"{'Agent':<15} {'Win Rate':<10} {'Avg Conf':<10} {'Error Rate':<10}")
        print("-" * 50)
        
        for agent_id, perf in agents.items():
            win_rate = perf.get("win_rate", 0)
            avg_conf = perf.get("avg_confidence", 0)
            error_rate = perf.get("error_rate", 0)
            
            print(f"{agent_id:<15} {win_rate:<10.1%} {avg_conf:<10.1%} {error_rate:<10.1%}")
        print()
        
    def _display_recent_arbitrations(self, metrics: Dict[str, Any]):
        """Display recent arbitrations."""
        print("📋 RECENT ARBITRATIONS")
        print("-" * 25)
        
        recent = metrics.get("recent_arbitrations", [])
        
        if not recent:
            print("No recent arbitrations")
        else:
            print(f"{'Time':<12} {'Task':<15} {'Winner':<15} {'Strategy':<15} {'Confidence':<10}")
            print("-" * 70)
            
            for arb in recent[:5]:  # Show last 5
                timestamp = arb.get("timestamp", "")
                task_id = arb.get("task_id", "")
                winner = arb.get("winner_agent_id", "")
                strategy = arb.get("strategy_used", "")
                confidence = arb.get("confidence", 0)
                
                print(f"{timestamp:<12} {task_id:<15} {winner:<15} {strategy:<15} {confidence:<10.1%}")
        print()
        
    def _display_controls(self):
        """Display control options."""
        print("🎮 CONTROLS")
        print("-" * 10)
        print("Commands: [r]efresh, [s]tatus, [m]etrics, [h]elp, [q]uit")
        print("Manual Override: [o]verride <conflict_id> <agent_id>")
        print("Strategy Change: [c]hange <task_type> <strategy>")
        print()
        
    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        try:
            # Get basic statistics
            stats = self.engine.get_statistics()
            
            # Calculate performance metrics
            total_arbitrations = stats.get("total_arbitrations", 0)
            total_errors = stats.get("total_errors", 0)
            total_timeouts = stats.get("total_timeouts", 0)
            total_fallbacks = stats.get("total_fallbacks", 0)
            
            error_rate = total_errors / total_arbitrations if total_arbitrations > 0 else 0
            timeout_rate = total_timeouts / total_arbitrations if total_arbitrations > 0 else 0
            fallback_rate = total_fallbacks / total_arbitrations if total_arbitrations > 0 else 0
            
            # Get recent arbitrations
            recent_arbitrations = self.engine.get_arbitration_history(limit=5)
            
            # Calculate strategy usage
            strategy_usage = {}
            for result in self.engine.results_log:
                strategy = result.strategy_used
                strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
                
            # Calculate agent performance
            agent_performance = {}
            agent_wins = {}
            agent_confidences = {}
            agent_errors = {}
            
            for result in self.engine.results_log:
                agent_id = result.winner_agent_id
                agent_wins[agent_id] = agent_wins.get(agent_id, 0) + 1
                
                if agent_id not in agent_confidences:
                    agent_confidences[agent_id] = []
                agent_confidences[agent_id].append(result.confidence)
                
            for conflict in self.engine.conflicts_log:
                for output in conflict.agent_outputs:
                    agent_id = output.agent_id
                    if agent_id not in agent_errors:
                        agent_errors[agent_id] = 0
                    agent_errors[agent_id] += output.error_count
                    
            # Calculate agent metrics
            for agent_id in set(agent_wins.keys()) | set(agent_errors.keys()):
                wins = agent_wins.get(agent_id, 0)
                total_participations = sum(1 for c in self.engine.conflicts_log 
                                         for o in c.agent_outputs if o.agent_id == agent_id)
                win_rate = wins / total_participations if total_participations > 0 else 0
                
                confidences = agent_confidences.get(agent_id, [])
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                errors = agent_errors.get(agent_id, 0)
                error_rate = errors / total_participations if total_participations > 0 else 0
                
                agent_performance[agent_id] = {
                    "win_rate": win_rate,
                    "avg_confidence": avg_confidence,
                    "error_rate": error_rate
                }
                
            return {
                "system_status": self._determine_system_status(error_rate, timeout_rate),
                "active_arbitrations": len([c for c in self.engine.conflicts_log 
                                          if c.timestamp > datetime.now(timezone.utc).replace(second=0, microsecond=0)]),
                "queue_length": 0,  # Would need queue implementation
                "uptime_seconds": int((datetime.now(timezone.utc) - self.engine.conflicts_log[0].timestamp).total_seconds()) if self.engine.conflicts_log else 0,
                "performance": {
                    "avg_response_time_ms": stats.get("avg_response_time_ms", 0),
                    "arbitrations_per_minute": stats.get("arbitrations_per_minute", 0),
                    "error_rate": error_rate,
                    "timeout_rate": timeout_rate,
                    "fallback_rate": fallback_rate
                },
                "strategy_usage": strategy_usage,
                "agent_performance": agent_performance,
                "recent_arbitrations": [
                    {
                        "timestamp": result.timestamp.strftime("%H:%M:%S"),
                        "task_id": result.metadata.get("task_id", ""),
                        "winner_agent_id": result.winner_agent_id,
                        "strategy_used": result.strategy_used,
                        "confidence": result.confidence
                    }
                    for result in recent_arbitrations
                ]
            }
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            return {
                "system_status": "error",
                "active_arbitrations": 0,
                "queue_length": 0,
                "uptime_seconds": 0,
                "performance": {},
                "strategy_usage": {},
                "agent_performance": {},
                "recent_arbitrations": []
            }
            
    def _determine_system_status(self, error_rate: float, timeout_rate: float) -> str:
        """Determine overall system status."""
        if error_rate > 0.1 or timeout_rate > 0.2:
            return "critical"
        elif error_rate > 0.05 or timeout_rate > 0.1:
            return "degraded"
        else:
            return "healthy"
            
    def manual_override(self, conflict_id: str, agent_id: str) -> bool:
        """Manually override an arbitration decision."""
        try:
            # Find the conflict
            conflict = None
            for c in self.engine.conflicts_log:
                if c.conflict_id == conflict_id:
                    conflict = c
                    break
                    
            if not conflict:
                print(f"❌ Conflict {conflict_id} not found")
                return False
                
            # Find the agent output
            agent_output = None
            for output in conflict.agent_outputs:
                if output.agent_id == agent_id:
                    agent_output = output
                    break
                    
            if not agent_output:
                print(f"❌ Agent {agent_id} not found in conflict {conflict_id}")
                return False
                
            # Create override result
            override_result = ArbitrationResult(
                winner_agent_id=agent_id,
                winning_output=agent_output.output,
                confidence=agent_output.confidence,
                strategy_used="manual_override",
                metadata={
                    "original_conflict_id": conflict_id,
                    "override_reason": "manual_override",
                    "override_timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Add to results log
            self.engine.results_log.append(override_result)
            
            print(f"✅ Manual override applied: {agent_id} wins conflict {conflict_id}")
            return True
            
        except Exception as e:
            print(f"❌ Manual override failed: {e}")
            return False
            
    def change_strategy(self, task_type: str, strategy: str) -> bool:
        """Change the default strategy for a task type."""
        try:
            # Update configuration
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                if "task_type_strategies" not in config:
                    config["task_type_strategies"] = {}
                    
                if task_type not in config["task_type_strategies"]:
                    config["task_type_strategies"][task_type] = {}
                    
                config["task_type_strategies"][task_type]["primary"] = strategy
                config["task_type_strategies"][task_type]["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                    
                print(f"✅ Strategy changed for {task_type}: {strategy}")
                return True
            else:
                print("❌ Configuration file not found")
                return False
                
        except Exception as e:
            print(f"❌ Strategy change failed: {e}")
            return False

def main():
    """Main entry point for the dashboard."""
    parser = argparse.ArgumentParser(description="GitBridge Real-Time Arbitration Dashboard")
    parser.add_argument("--config", default="arbitration_config.json", help="Path to arbitration config")
    parser.add_argument("--refresh", type=float, default=2.0, help="Refresh interval in seconds")
    parser.add_argument("--command", help="Execute single command and exit")
    
    args = parser.parse_args()
    
    dashboard = RealTimeArbitrationDashboard(config_path=args.config)
    dashboard.refresh_interval = args.refresh
    
    if args.command:
        # Execute single command
        if args.command == "status":
            metrics = dashboard._collect_metrics()
            print(json.dumps(metrics, indent=2))
        elif args.command == "metrics":
            stats = dashboard.engine.get_statistics()
            print(json.dumps(stats, indent=2))
        else:
            print(f"Unknown command: {args.command}")
    else:
        # Start interactive dashboard
        dashboard.start_dashboard()

if __name__ == "__main__":
    main() 