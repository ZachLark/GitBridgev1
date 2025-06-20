#!/usr/bin/env python3
"""
GitBridge Arbitration Log Viewer
Phase: GBP22
Part: P22P3
Step: P22P3S1
Task: P22P3S1T1 - Arbitration Log Viewer Implementation

Developer tool for reviewing arbitration outcomes.
CLI/terminal-based visualization of conflict history,
filters by task, agent, timestamp, exportable JSON and CSV logs.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P22P3 Schema]
"""

import json
import logging
import argparse
import csv
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

@dataclass
class LogViewerConfig:
    """Configuration for the log viewer."""
    max_display_items: int = 50
    date_format: str = "%Y-%m-%d %H:%M:%S"
    show_details: bool = False
    color_output: bool = True

class ArbitrationLogViewer:
    """
    Developer tool for reviewing arbitration outcomes.
    
    Phase: GBP22
    Part: P22P3
    Step: P22P3S1
    Task: P22P3S1T1 - Core Implementation
    
    Features:
    - CLI/terminal-based visualization
    - Filters by task, agent, timestamp
    - Exportable JSON and CSV logs
    - Conflict history analysis
    """
    
    def __init__(self, log_path: str = "arbitration_logs.json", config: Optional[LogViewerConfig] = None):
        """
        Initialize arbitration log viewer.
        
        Args:
            log_path: Path to arbitration logs file
            config: Viewer configuration
        """
        self.log_path = Path(log_path)
        self.config = config or LogViewerConfig()
        self.log_data: Optional[Dict[str, Any]] = None
        
        logger.info(f"[P22P3S1T1] ArbitrationLogViewer initialized with log: {log_path}")
        
    def load_logs(self) -> bool:
        """
        Load arbitration logs from file.
        
        Returns:
            bool: True if loading successful
        """
        if not self.log_path.exists():
            logger.warning(f"[P22P3S1T1] Log file {self.log_path} does not exist")
            return False
            
        try:
            with open(self.log_path, 'r') as f:
                self.log_data = json.load(f)
                
            logger.info(f"[P22P3S1T1] Loaded {self.log_data.get('total_conflicts', 0)} conflicts and {self.log_data.get('total_results', 0)} results")
            return True
            
        except Exception as e:
            logger.error(f"[P22P3S1T1] Failed to load logs: {e}")
            return False
            
    def filter_results(
        self,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        strategy: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        conflict_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter arbitration results based on criteria.
        
        Args:
            task_id: Filter by task ID
            agent_id: Filter by agent ID
            strategy: Filter by strategy used
            start_time: Filter by start time (ISO format)
            end_time: Filter by end time (ISO format)
            conflict_type: Filter by conflict type
            limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Filtered results
        """
        if self.log_data is None:
            return []
            
        results = self.log_data.get("results", [])
        filtered_results = []
        
        for result in results:
            # Apply filters
            if task_id and not self._result_matches_task(result, task_id):
                continue
            if agent_id and result.get("winner_agent_id") != agent_id:
                continue
            if strategy and result.get("strategy_used") != strategy:
                continue
            if start_time and result.get("timestamp", "") < start_time:
                continue
            if end_time and result.get("timestamp", "") > end_time:
                continue
            if conflict_type and not self._result_matches_conflict_type(result, conflict_type):
                continue
                
            filtered_results.append(result)
            
        # Apply limit
        if limit:
            filtered_results = filtered_results[-limit:]
            
        return filtered_results
        
    def _result_matches_task(self, result: Dict[str, Any], task_id: str) -> bool:
        """Check if result matches task ID."""
        # Look through conflicts to find matching task
        conflicts = self.log_data.get("conflicts", [])
        for conflict in conflicts:
            if conflict.get("task_id") == task_id:
                # Check if this result corresponds to this conflict
                if result.get("winner_agent_id") in [output.get("agent_id") for output in conflict.get("agent_outputs", [])]:
                    return True
        return False
        
    def _result_matches_conflict_type(self, result: Dict[str, Any], conflict_type: str) -> bool:
        """Check if result matches conflict type."""
        # Look through conflicts to find matching type
        conflicts = self.log_data.get("conflicts", [])
        for conflict in conflicts:
            if conflict.get("conflict_type") == conflict_type:
                # Check if this result corresponds to this conflict
                if result.get("winner_agent_id") in [output.get("agent_id") for output in conflict.get("agent_outputs", [])]:
                    return True
        return False
        
    def display_results(self, results: List[Dict[str, Any]], show_details: bool = False):
        """
        Display arbitration results in terminal.
        
        Args:
            results: Results to display
            show_details: Whether to show detailed information
        """
        if not results:
            print("📋 No results found matching criteria")
            return
            
        print(f"📊 Arbitration Results ({len(results)} items):")
        print("=" * 80)
        
        for i, result in enumerate(results[-self.config.max_display_items:], 1):
            timestamp = result.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime(self.config.date_format)
                except:
                    pass
                    
            print(f"{i:3d}. [{timestamp}] {result.get('winner_agent_id', 'Unknown')} wins")
            print(f"     Strategy: {result.get('strategy_used', 'Unknown')}")
            print(f"     Confidence: {result.get('confidence', 0):.2f}")
            
            if result.get("fallback_triggered"):
                print(f"     ⚠️  Fallback triggered: {result.get('fallback_reason', 'Unknown')}")
                
            if show_details:
                print(f"     Output: {str(result.get('winning_output', ''))[:100]}...")
                if result.get("metadata"):
                    print(f"     Metadata: {result.get('metadata')}")
                    
            print()
            
        if len(results) > self.config.max_display_items:
            print(f"... and {len(results) - self.config.max_display_items} more results")
            
    def display_conflicts(self, conflicts: List[Dict[str, Any]], show_details: bool = False):
        """
        Display arbitration conflicts in terminal.
        
        Args:
            conflicts: Conflicts to display
            show_details: Whether to show detailed information
        """
        if not conflicts:
            print("📋 No conflicts found matching criteria")
            return
            
        print(f"⚔️  Arbitration Conflicts ({len(conflicts)} items):")
        print("=" * 80)
        
        for i, conflict in enumerate(conflicts[-self.config.max_display_items:], 1):
            timestamp = conflict.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime(self.config.date_format)
                except:
                    pass
                    
            print(f"{i:3d}. [{timestamp}] {conflict.get('conflict_type', 'Unknown')} conflict")
            print(f"     Task: {conflict.get('task_id', 'Unknown')} / {conflict.get('subtask_id', 'Unknown')}")
            print(f"     Agents: {len(conflict.get('agent_outputs', []))} agents involved")
            print(f"     Strategy: {conflict.get('resolution_strategy', 'Unknown')}")
            
            if show_details:
                for j, output in enumerate(conflict.get("agent_outputs", [])):
                    print(f"       {j+1}. {output.get('agent_id', 'Unknown')} (conf: {output.get('confidence', 0):.2f})")
                    
            print()
            
        if len(conflicts) > self.config.max_display_items:
            print(f"... and {len(conflicts) - self.config.max_display_items} more conflicts")
            
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about arbitration logs.
        
        Returns:
            Dict[str, Any]: Statistics
        """
        if self.log_data is None:
            return {"error": "No logs loaded"}
            
        results = self.log_data.get("results", [])
        conflicts = self.log_data.get("conflicts", [])
        
        # Strategy usage
        strategy_counts = {}
        for result in results:
            strategy = result.get("strategy_used", "unknown")
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
        # Agent wins
        agent_wins = {}
        for result in results:
            agent = result.get("winner_agent_id", "unknown")
            agent_wins[agent] = agent_wins.get(agent, 0) + 1
            
        # Conflict types
        conflict_types = {}
        for conflict in conflicts:
            conflict_type = conflict.get("conflict_type", "unknown")
            conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
            
        # Fallback usage
        fallback_count = sum(1 for result in results if result.get("fallback_triggered", False))
        
        # Time analysis
        timestamps = [result.get("timestamp") for result in results if result.get("timestamp")]
        if timestamps:
            try:
                times = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
                times.sort()
                time_span = times[-1] - times[0] if len(times) > 1 else None
            except:
                time_span = None
        else:
            time_span = None
            
        return {
            "total_results": len(results),
            "total_conflicts": len(conflicts),
            "strategy_usage": strategy_counts,
            "agent_wins": agent_wins,
            "conflict_types": conflict_types,
            "fallback_count": fallback_count,
            "time_span": str(time_span) if time_span else None,
            "average_confidence": sum(r.get("confidence", 0) for r in results) / len(results) if results else 0
        }
        
    def export_logs(
        self,
        output_path: str,
        format: str = "json",
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        strategy: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        conflict_type: Optional[str] = None
    ) -> bool:
        """
        Export filtered logs to file.
        
        Args:
            output_path: Path to output file
            format: Export format (json, csv)
            task_id: Filter by task ID
            agent_id: Filter by agent ID
            strategy: Filter by strategy
            start_time: Filter by start time
            end_time: Filter by end time
            conflict_type: Filter by conflict type
            
        Returns:
            bool: True if export successful
        """
        try:
            # Filter results
            results = self.filter_results(
                task_id=task_id,
                agent_id=agent_id,
                strategy=strategy,
                start_time=start_time,
                end_time=end_time,
                conflict_type=conflict_type
            )
            
            if format.lower() == "json":
                export_data = {
                    "export_timestamp": datetime.now(timezone.utc).isoformat(),
                    "total_results": len(results),
                    "filters": {
                        "task_id": task_id,
                        "agent_id": agent_id,
                        "strategy": strategy,
                        "start_time": start_time,
                        "end_time": end_time,
                        "conflict_type": conflict_type
                    },
                    "results": results
                }
                
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                    
            elif format.lower() == "csv":
                with open(output_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Header
                    writer.writerow([
                        'timestamp', 'winner_agent_id', 'strategy_used', 'confidence',
                        'fallback_triggered', 'fallback_reason', 'winning_output'
                    ])
                    
                    # Data
                    for result in results:
                        writer.writerow([
                            result.get('timestamp', ''),
                            result.get('winner_agent_id', ''),
                            result.get('strategy_used', ''),
                            result.get('confidence', 0),
                            result.get('fallback_triggered', False),
                            result.get('fallback_reason', ''),
                            str(result.get('winning_output', ''))[:100]
                        ])
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            logger.info(f"[P22P3S1T1] Exported {len(results)} results to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"[P22P3S1T1] Failed to export logs: {e}")
            return False
            
    def search_logs(self, query: str) -> List[Dict[str, Any]]:
        """
        Search logs for specific text.
        
        Args:
            query: Search query
            
        Returns:
            List[Dict[str, Any]]: Matching results
        """
        if self.log_data is None:
            return []
            
        results = self.log_data.get("results", [])
        matching_results = []
        
        query_lower = query.lower()
        
        for result in results:
            # Search in various fields
            searchable_text = [
                str(result.get("winner_agent_id", "")),
                str(result.get("strategy_used", "")),
                str(result.get("winning_output", "")),
                str(result.get("fallback_reason", ""))
            ]
            
            if any(query_lower in text.lower() for text in searchable_text):
                matching_results.append(result)
                
        return matching_results

def main():
    """Main function for CLI interface."""
    parser = argparse.ArgumentParser(description='GitBridge Arbitration Log Viewer')
    parser.add_argument('--log-file', default='arbitration_logs.json', help='Path to log file')
    parser.add_argument('--list', action='store_true', help='List all results')
    parser.add_argument('--conflicts', action='store_true', help='Show conflicts instead of results')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--search', help='Search for specific text')
    parser.add_argument('--export', help='Export to specified file')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    parser.add_argument('--details', action='store_true', help='Show detailed information')
    parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # Filters
    parser.add_argument('--task-id', help='Filter by task ID')
    parser.add_argument('--agent-id', help='Filter by agent ID')
    parser.add_argument('--strategy', help='Filter by strategy')
    parser.add_argument('--start-time', help='Filter by start time (ISO format)')
    parser.add_argument('--end-time', help='Filter by end time (ISO format)')
    parser.add_argument('--conflict-type', help='Filter by conflict type')
    
    args = parser.parse_args()
    
    viewer = ArbitrationLogViewer(args.log_file)
    
    if not viewer.load_logs():
        print(f"❌ Failed to load logs from {args.log_file}")
        return 1
        
    if args.stats:
        stats = viewer.get_statistics()
        print("📊 Arbitration Statistics:")
        print(f"  Total Results: {stats['total_results']}")
        print(f"  Total Conflicts: {stats['total_conflicts']}")
        print(f"  Fallback Count: {stats['fallback_count']}")
        print(f"  Average Confidence: {stats['average_confidence']:.2f}")
        
        if stats['time_span']:
            print(f"  Time Span: {stats['time_span']}")
            
        print("\nStrategy Usage:")
        for strategy, count in stats['strategy_usage'].items():
            print(f"  {strategy}: {count}")
            
        print("\nAgent Wins:")
        for agent, wins in stats['agent_wins'].items():
            print(f"  {agent}: {wins}")
            
        print("\nConflict Types:")
        for conflict_type, count in stats['conflict_types'].items():
            print(f"  {conflict_type}: {count}")
            
    elif args.search:
        results = viewer.search_logs(args.search)
        print(f"🔍 Search results for '{args.search}': {len(results)} matches")
        viewer.display_results(results, args.details)
        
    elif args.export:
        success = viewer.export_logs(
            output_path=args.export,
            format=args.format,
            task_id=args.task_id,
            agent_id=args.agent_id,
            strategy=args.strategy,
            start_time=args.start_time,
            end_time=args.end_time,
            conflict_type=args.conflict_type
        )
        if success:
            print(f"✅ Exported logs to {args.export}")
        else:
            print("❌ Failed to export logs")
            
    elif args.conflicts:
        # Show conflicts
        conflicts = viewer.log_data.get("conflicts", [])
        if args.limit:
            conflicts = conflicts[-args.limit:]
        viewer.display_conflicts(conflicts, args.details)
        
    elif args.list:
        # Show results
        results = viewer.filter_results(
            task_id=args.task_id,
            agent_id=args.agent_id,
            strategy=args.strategy,
            start_time=args.start_time,
            end_time=args.end_time,
            conflict_type=args.conflict_type,
            limit=args.limit
        )
        viewer.display_results(results, args.details)
        
    else:
        # Default: show recent results
        results = viewer.filter_results(limit=10)
        viewer.display_results(results, args.details)
        
        print("\nAvailable commands:")
        print("  --list: Show all results")
        print("  --conflicts: Show conflicts")
        print("  --stats: Show statistics")
        print("  --search <query>: Search logs")
        print("  --export <file>: Export logs")
        print("  --details: Show detailed information")

if __name__ == "__main__":
    main() 