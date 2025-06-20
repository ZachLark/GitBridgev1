#!/usr/bin/env python3
"""
GitBridge Agent Visualization Tool
Phase: GBP21
Part: P21P6
Step: P21P6S1
Task: P21P6S1T1 - Agent Visualization Implementation

Build visual and CLI-based tool that maps:
- Agent contributions per task/subtask
- Logical relationships and lineage
- Confidence scores and attribution
- Timeline-based replay capability.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P21P6 Schema]
"""

import json
import logging
import sys
import os
import argparse
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class AgentContribution:
    """Represents an agent's contribution to a task."""
    agent_id: str
    agent_name: str
    task_id: str
    subtask_id: str
    contribution_type: str  # analysis, review, creation, etc.
    confidence_score: float
    completion_time: float
    token_usage: Dict[str, int]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskLineage:
    """Represents the lineage of a task through multiple agents."""
    task_id: str
    parent_task_id: Optional[str]
    agent_contributions: List[AgentContribution]
    dependencies: List[str] = field(default_factory=list)
    final_confidence: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class FilterCriteria:
    """Represents filtering criteria for visualization."""
    agent_ids: Optional[List[str]] = None
    agent_names: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    confidence_min: Optional[float] = None
    confidence_max: Optional[float] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    task_types: Optional[List[str]] = None
    contribution_types: Optional[List[str]] = None

class AgentVisualizer:
    """
    Agent visualization and audit tool.
    
    Phase: GBP21
    Part: P21P6
    Step: P21P6S1
    Task: P21P6S1T1 - Core Implementation
    
    Features:
    - Visualize agent contributions and relationships
    - Timeline-based replay system
    - Confidence and attribution mapping
    - CLI and export capabilities
    - Advanced filtering and querying
    """
    
    def __init__(self, memory_export_path: str = "integration_memory_export.json"):
        """
        Initialize the agent visualizer.
        
        Args:
            memory_export_path: Path to memory export JSON file
        """
        self.memory_data = self._load_memory_export(memory_export_path)
        self.task_lineages = self._build_task_lineages()
        self.agent_performance = self._calculate_agent_performance()
        
        logger.info("[P21P6S1T1] AgentVisualizer initialized")
        
    def _load_memory_export(self, export_path: str) -> List[Dict[str, Any]]:
        """Load memory export data."""
        try:
            with open(export_path, 'r') as f:
                data = json.load(f)
            logger.info(f"[P21P6S1T1] Loaded memory export with {len(data)} nodes")
            return data
        except Exception as e:
            logger.error(f"[P21P6S1T1] Failed to load memory export: {e}")
            return []
            
    def _build_task_lineages(self) -> Dict[str, TaskLineage]:
        """Build task lineages from memory data."""
        lineages = {}
        
        for node in self.memory_data:
            task_id = node.get('metadata', {}).get('subtask_id', node.get('node_id'))
            
            if task_id not in lineages:
                lineages[task_id] = TaskLineage(
                    task_id=task_id,
                    parent_task_id=node.get('metadata', {}).get('master_task_id'),
                    agent_contributions=[]
                )
                
            # Create agent contribution
            contribution = AgentContribution(
                agent_id=node['agent_id'],
                agent_name=self._get_agent_name(node['agent_id']),
                task_id=task_id,
                subtask_id=task_id,
                contribution_type=node['task_context'],
                confidence_score=node.get('result', {}).get('confidence_score', 0.0),
                completion_time=node.get('result', {}).get('completion_time', 0.0),
                token_usage=node.get('result', {}).get('token_usage', {}),
                timestamp=datetime.fromisoformat(node['timestamp']),
                metadata=node.get('metadata', {})
            )
            
            lineages[task_id].agent_contributions.append(contribution)
            
        # Calculate final confidence scores
        for lineage in lineages.values():
            if lineage.agent_contributions:
                confidences = [c.confidence_score for c in lineage.agent_contributions]
                lineage.final_confidence = sum(confidences) / len(confidences)
                
        return lineages
        
    def _get_agent_name(self, agent_id: str) -> str:
        """Get agent name from agent ID."""
        agent_names = {
            'openai_gpt4o': 'OpenAI',
            'grok_3': 'Grok',
            'cursor_assistant': 'Cursor',
            'grok_writer': 'GrokWriter',
            'chatgpt_gpt4': 'ChatGPT',
            'synthesizer_specialist': 'Synthesizer'
        }
        return agent_names.get(agent_id, agent_id)
        
    def _calculate_agent_performance(self) -> Dict[str, Dict[str, Any]]:
        """Calculate performance metrics for each agent."""
        performance = defaultdict(lambda: {
            'total_contributions': 0,
            'avg_confidence': 0.0,
            'total_tokens': 0,
            'avg_completion_time': 0.0,
            'task_types': set(),
            'contributions': []
        })
        
        for lineage in self.task_lineages.values():
            for contribution in lineage.agent_contributions:
                agent_id = contribution.agent_id
                perf = performance[agent_id]
                
                perf['total_contributions'] += 1
                perf['contributions'].append(contribution)
                perf['task_types'].add(contribution.contribution_type)
                perf['total_tokens'] += contribution.token_usage.get('total', 0)
                
        # Calculate averages
        for agent_id, perf in performance.items():
            if perf['total_contributions'] > 0:
                confidences = [c.confidence_score for c in perf['contributions']]
                completion_times = [c.completion_time for c in perf['contributions']]
                
                perf['avg_confidence'] = sum(confidences) / len(confidences)
                perf['avg_completion_time'] = sum(completion_times) / len(completion_times)
                perf['task_types'] = list(perf['task_types'])
                
        return dict(performance)
        
    def _parse_filter_criteria(self, filter_args: List[str]) -> FilterCriteria:
        """Parse filter arguments into FilterCriteria object."""
        criteria = FilterCriteria()
        
        for filter_arg in filter_args:
            if '=' in filter_arg:
                key, value = filter_arg.split('=', 1)
                
                if key == 'agent':
                    criteria.agent_names = [v.strip() for v in value.split(',')]
                elif key == 'role':
                    criteria.roles = [v.strip() for v in value.split(',')]
                elif key == 'confidence':
                    # Parse confidence range (e.g., ">0.9" or "0.5-0.8")
                    if '>' in value:
                        criteria.confidence_min = float(value.replace('>', ''))
                    elif '<' in value:
                        criteria.confidence_max = float(value.replace('<', ''))
                    elif '-' in value:
                        min_val, max_val = value.split('-')
                        criteria.confidence_min = float(min_val)
                        criteria.confidence_max = float(max_val)
                    else:
                        criteria.confidence_min = float(value)
                        criteria.confidence_max = float(value)
                elif key == 'date-range':
                    # Parse date range (e.g., "2025-06-19:2025-06-20")
                    if ':' in value:
                        start_str, end_str = value.split(':')
                        criteria.date_start = datetime.fromisoformat(start_str)
                        criteria.date_end = datetime.fromisoformat(end_str)
                elif key == 'task-type':
                    criteria.task_types = [v.strip() for v in value.split(',')]
                elif key == 'contribution-type':
                    criteria.contribution_types = [v.strip() for v in value.split(',')]
                    
        return criteria
        
    def _apply_filters(self, contributions: List[AgentContribution], criteria: FilterCriteria) -> List[AgentContribution]:
        """Apply filters to contributions."""
        filtered_contributions = []
        
        for contribution in contributions:
            # Agent name filter
            if criteria.agent_names and contribution.agent_name not in criteria.agent_names:
                continue
                
            # Agent ID filter
            if criteria.agent_ids and contribution.agent_id not in criteria.agent_ids:
                continue
                
            # Confidence filter
            if criteria.confidence_min is not None and contribution.confidence_score < criteria.confidence_min:
                continue
            if criteria.confidence_max is not None and contribution.confidence_score > criteria.confidence_max:
                continue
                
            # Date range filter
            if criteria.date_start and contribution.timestamp < criteria.date_start:
                continue
            if criteria.date_end and contribution.timestamp > criteria.date_end:
                continue
                
            # Task type filter
            if criteria.task_types and contribution.contribution_type not in criteria.task_types:
                continue
                
            # Contribution type filter
            if criteria.contribution_types and contribution.contribution_type not in criteria.contribution_types:
                continue
                
            filtered_contributions.append(contribution)
            
        return filtered_contributions
        
    def visualize_agent_contributions(self, task_id: Optional[str] = None, filter_criteria: Optional[FilterCriteria] = None) -> str:
        """Generate visual representation of agent contributions with optional filtering."""
        if task_id and task_id in self.task_lineages:
            lineage = self.task_lineages[task_id]
            return self._visualize_single_task(lineage, filter_criteria)
        else:
            return self._visualize_all_tasks(filter_criteria)
            
    def _visualize_single_task(self, lineage: TaskLineage, filter_criteria: Optional[FilterCriteria] = None) -> str:
        """Visualize a single task lineage with filtering."""
        output = []
        output.append(f"📋 Task: {lineage.task_id}")
        output.append(f"🎯 Final Confidence: {lineage.final_confidence:.2f}")
        output.append(f"📅 Created: {lineage.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")
        
        # Apply filters if provided
        contributions = lineage.agent_contributions
        if filter_criteria:
            contributions = self._apply_filters(contributions, filter_criteria)
            output.append(f"🔍 Filtered to {len(contributions)} contributions")
            output.append("")
        
        # Agent contributions timeline
        output.append("🕒 Agent Contributions Timeline:")
        output.append("=" * 50)
        
        sorted_contributions = sorted(contributions, key=lambda x: x.timestamp)
        
        for i, contribution in enumerate(sorted_contributions, 1):
            output.append(f"{i}. [{contribution.timestamp.strftime('%H:%M:%S')}] {contribution.agent_name}")
            output.append(f"   Type: {contribution.contribution_type}")
            output.append(f"   Confidence: {contribution.confidence_score:.2f}")
            output.append(f"   Time: {contribution.completion_time:.1f}s")
            output.append(f"   Tokens: {contribution.token_usage.get('total', 0)}")
            output.append("")
            
        return "\n".join(output)
        
    def _visualize_all_tasks(self, filter_criteria: Optional[FilterCriteria] = None) -> str:
        """Visualize all tasks and their agent contributions with filtering."""
        output = []
        output.append("🎯 GitBridge Agent Collaboration Overview")
        output.append("=" * 50)
        output.append("")
        
        # Apply filters to all contributions
        all_contributions = []
        for lineage in self.task_lineages.values():
            all_contributions.extend(lineage.agent_contributions)
            
        if filter_criteria:
            all_contributions = self._apply_filters(all_contributions, filter_criteria)
            output.append(f"🔍 Filtered to {len(all_contributions)} contributions")
            output.append("")
        
        # Summary statistics
        total_tasks = len(set(c.task_id for c in all_contributions))
        total_contributions = len(all_contributions)
        avg_confidence = sum(c.confidence_score for c in all_contributions) / total_contributions if total_contributions > 0 else 0
        
        output.append(f"📊 Summary:")
        output.append(f"   Total Tasks: {total_tasks}")
        output.append(f"   Total Contributions: {total_contributions}")
        output.append(f"   Average Confidence: {avg_confidence:.2f}")
        output.append("")
        
        # Agent performance (filtered)
        agent_stats = defaultdict(lambda: {
            'contributions': 0,
            'total_confidence': 0.0,
            'total_time': 0.0,
            'total_tokens': 0,
            'types': set()
        })
        
        for contribution in all_contributions:
            agent_id = contribution.agent_id
            stats = agent_stats[agent_id]
            stats['contributions'] += 1
            stats['total_confidence'] += contribution.confidence_score
            stats['total_time'] += contribution.completion_time
            stats['total_tokens'] += contribution.token_usage.get('total', 0)
            stats['types'].add(contribution.contribution_type)
            
        output.append("🤖 Agent Performance:")
        output.append("-" * 30)
        
        for agent_id, stats in agent_stats.items():
            agent_name = self._get_agent_name(agent_id)
            avg_confidence = stats['total_confidence'] / stats['contributions'] if stats['contributions'] > 0 else 0
            avg_time = stats['total_time'] / stats['contributions'] if stats['contributions'] > 0 else 0
            
            output.append(f"{agent_name}:")
            output.append(f"  Contributions: {stats['contributions']}")
            output.append(f"  Avg Confidence: {avg_confidence:.2f}")
            output.append(f"  Avg Time: {avg_time:.1f}s")
            output.append(f"  Total Tokens: {stats['total_tokens']}")
            output.append(f"  Task Types: {', '.join(stats['types'])}")
            output.append("")
            
        return "\n".join(output)
        
    def timeline_replay(self, task_id: Optional[str] = None, step_by_step: bool = False, filter_criteria: Optional[FilterCriteria] = None) -> str:
        """Generate timeline replay of agent activities with filtering."""
        output = []
        output.append("🕒 Timeline Replay")
        output.append("=" * 30)
        output.append("")
        
        # Collect all contributions
        all_contributions = []
        for lineage in self.task_lineages.values():
            if task_id is None or lineage.task_id == task_id:
                all_contributions.extend(lineage.agent_contributions)
                
        # Apply filters
        if filter_criteria:
            all_contributions = self._apply_filters(all_contributions, filter_criteria)
            output.append(f"🔍 Filtered to {len(all_contributions)} contributions")
            output.append("")
                
        # Sort by timestamp
        sorted_contributions = sorted(all_contributions, key=lambda x: x.timestamp)
        
        if step_by_step:
            output.append("Step-by-step replay (press Enter to continue):")
            output.append("")
            
            for i, contribution in enumerate(sorted_contributions, 1):
                step_output = [
                    f"Step {i}:",
                    f"  Time: {contribution.timestamp.strftime('%H:%M:%S')}",
                    f"  Agent: {contribution.agent_name}",
                    f"  Task: {contribution.task_id}",
                    f"  Type: {contribution.contribution_type}",
                    f"  Confidence: {contribution.confidence_score:.2f}",
                    ""
                ]
                output.extend(step_output)
        else:
            output.append("Timeline view:")
            output.append("")
            
            for contribution in sorted_contributions:
                output.append(f"[{contribution.timestamp.strftime('%H:%M:%S')}] "
                            f"{contribution.agent_name} → {contribution.task_id} "
                            f"({contribution.contribution_type}) "
                            f"[{contribution.confidence_score:.2f}]")
                            
        return "\n".join(output)
        
    def generate_attribution_graph(self) -> str:
        """Generate attribution graph showing agent relationships."""
        output = []
        output.append("🔗 Agent Attribution Graph")
        output.append("=" * 30)
        output.append("")
        
        # Build agent collaboration matrix
        collaboration_matrix = defaultdict(lambda: defaultdict(int))
        
        for lineage in self.task_lineages.values():
            agents = [c.agent_id for c in lineage.agent_contributions]
            for i, agent1 in enumerate(agents):
                for agent2 in agents[i+1:]:
                    collaboration_matrix[agent1][agent2] += 1
                    collaboration_matrix[agent2][agent1] += 1
                    
        # Display collaboration matrix
        agent_ids = list(self.agent_performance.keys())
        
        output.append("Collaboration Matrix (number of shared tasks):")
        output.append("")
        
        # Header
        header = "Agent".ljust(15)
        for agent_id in agent_ids:
            header += f"{self._get_agent_name(agent_id):>10}"
        output.append(header)
        output.append("-" * (15 + 10 * len(agent_ids)))
        
        # Matrix rows
        for agent1 in agent_ids:
            row = f"{self._get_agent_name(agent1):<15}"
            for agent2 in agent_ids:
                if agent1 == agent2:
                    row += f"{'--':>10}"
                else:
                    count = collaboration_matrix[agent1][agent2]
                    row += f"{count:>10}"
            output.append(row)
            
        return "\n".join(output)
        
    def export_audit_report(self, output_path: str = "audit_report.md") -> None:
        """Export comprehensive audit report."""
        report = []
        report.append("# GitBridge Agent Collaboration Audit Report")
        report.append("")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Total Tasks:** {len(self.task_lineages)}")
        report.append(f"**Total Agents:** {len(self.agent_performance)}")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        
        total_contributions = sum(len(l.agent_contributions) for l in self.task_lineages.values())
        avg_confidence = sum(l.final_confidence for l in self.task_lineages.values()) / len(self.task_lineages) if self.task_lineages else 0
        
        report.append(f"- **Total Agent Contributions:** {total_contributions}")
        report.append(f"- **Average Task Confidence:** {avg_confidence:.2f}")
        report.append(f"- **Collaboration Efficiency:** {total_contributions / len(self.task_lineages):.1f} contributions per task")
        report.append("")
        
        # Agent Performance Analysis
        report.append("## Agent Performance Analysis")
        report.append("")
        
        for agent_id, perf in self.agent_performance.items():
            agent_name = self._get_agent_name(agent_id)
            report.append(f"### {agent_name}")
            report.append("")
            report.append(f"- **Total Contributions:** {perf['total_contributions']}")
            report.append(f"- **Average Confidence:** {perf['avg_confidence']:.2f}")
            report.append(f"- **Average Completion Time:** {perf['avg_completion_time']:.1f}s")
            report.append(f"- **Total Token Usage:** {perf['total_tokens']}")
            report.append(f"- **Task Types:** {', '.join(perf['task_types'])}")
            report.append("")
            
        # Task Lineage Analysis
        report.append("## Task Lineage Analysis")
        report.append("")
        
        for task_id, lineage in self.task_lineages.items():
            report.append(f"### Task: {task_id}")
            report.append("")
            report.append(f"- **Final Confidence:** {lineage.final_confidence:.2f}")
            report.append(f"- **Agent Count:** {len(lineage.agent_contributions)}")
            report.append(f"- **Contribution Types:** {', '.join(set(c.contribution_type for c in lineage.agent_contributions))}")
            report.append("")
            
            for contribution in lineage.agent_contributions:
                report.append(f"  - **{contribution.agent_name}** ({contribution.contribution_type}): "
                            f"Confidence {contribution.confidence_score:.2f}, "
                            f"Time {contribution.completion_time:.1f}s")
            report.append("")
            
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        
        # Find best performing agents
        best_agents = sorted(self.agent_performance.items(), 
                           key=lambda x: x[1]['avg_confidence'], reverse=True)
        
        if best_agents:
            best_agent_id, best_perf = best_agents[0]
            best_agent_name = self._get_agent_name(best_agent_id)
            report.append(f"- **Top Performer:** {best_agent_name} (avg confidence: {best_perf['avg_confidence']:.2f})")
            
        # Find most active agents
        most_active = sorted(self.agent_performance.items(), 
                           key=lambda x: x[1]['total_contributions'], reverse=True)
        
        if most_active:
            active_agent_id, active_perf = most_active[0]
            active_agent_name = self._get_agent_name(active_agent_id)
            report.append(f"- **Most Active:** {active_agent_name} ({active_perf['total_contributions']} contributions)")
            
        report.append("")
        
        try:
            with open(output_path, 'w') as f:
                f.write('\n'.join(report))
            logger.info(f"[P21P6S1T1] Audit report exported to {output_path}")
        except Exception as e:
            logger.error(f"[P21P6S1T1] Failed to export audit report: {e}")

def main():
    """Main function for CLI interface."""
    parser = argparse.ArgumentParser(description='GitBridge Agent Visualizer')
    parser.add_argument('--memory-export', default='integration_memory_export.json',
                       help='Path to memory export JSON file')
    parser.add_argument('--task-id', help='Specific task ID to visualize')
    parser.add_argument('--timeline', action='store_true', help='Show timeline replay')
    parser.add_argument('--step-by-step', action='store_true', help='Step-by-step timeline replay')
    parser.add_argument('--attribution', action='store_true', help='Show attribution graph')
    parser.add_argument('--export-report', help='Export audit report to specified file')
    
    # Filter options
    parser.add_argument('--filter', action='append', 
                       help='Filter criteria (e.g., agent=OpenAI, confidence=>0.9, date-range=2025-06-19:2025-06-20)')
    parser.add_argument('--agent', help='Filter by agent name(s) (comma-separated)')
    parser.add_argument('--confidence-min', type=float, help='Minimum confidence score')
    parser.add_argument('--confidence-max', type=float, help='Maximum confidence score')
    parser.add_argument('--date-start', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--date-end', help='End date (YYYY-MM-DD)')
    parser.add_argument('--task-type', help='Filter by task type(s) (comma-separated)')
    
    args = parser.parse_args()
    
    # Initialize visualizer
    visualizer = AgentVisualizer(args.memory_export)
    
    # Build filter criteria
    filter_criteria = None
    if args.filter or args.agent or args.confidence_min or args.confidence_max or args.date_start or args.date_end or args.task_type:
        filter_criteria = FilterCriteria()
        
        # Parse --filter arguments
        if args.filter:
            for filter_arg in args.filter:
                if '=' in filter_arg:
                    key, value = filter_arg.split('=', 1)
                    if key == 'agent':
                        filter_criteria.agent_names = [v.strip() for v in value.split(',')]
                    elif key == 'confidence':
                        if '>' in value:
                            filter_criteria.confidence_min = float(value.replace('>', ''))
                        elif '<' in value:
                            filter_criteria.confidence_max = float(value.replace('<', ''))
                        elif '-' in value:
                            min_val, max_val = value.split('-')
                            filter_criteria.confidence_min = float(min_val)
                            filter_criteria.confidence_max = float(max_val)
                        else:
                            filter_criteria.confidence_min = float(value)
                            filter_criteria.confidence_max = float(value)
                    elif key == 'date-range':
                        if ':' in value:
                            start_str, end_str = value.split(':')
                            filter_criteria.date_start = datetime.fromisoformat(start_str)
                            filter_criteria.date_end = datetime.fromisoformat(end_str)
                    elif key == 'task-type':
                        filter_criteria.task_types = [v.strip() for v in value.split(',')]
        
        # Parse individual filter arguments
        if args.agent:
            filter_criteria.agent_names = [a.strip() for a in args.agent.split(',')]
        if args.confidence_min is not None:
            filter_criteria.confidence_min = args.confidence_min
        if args.confidence_max is not None:
            filter_criteria.confidence_max = args.confidence_max
        if args.date_start:
            filter_criteria.date_start = datetime.fromisoformat(args.date_start)
        if args.date_end:
            filter_criteria.date_end = datetime.fromisoformat(args.date_end)
        if args.task_type:
            filter_criteria.task_types = [t.strip() for t in args.task_type.split(',')]
    
    # Generate visualizations
    if args.timeline:
        print(visualizer.timeline_replay(args.task_id, args.step_by_step, filter_criteria))
    elif args.attribution:
        print(visualizer.generate_attribution_graph())
    elif args.export_report:
        visualizer.export_audit_report(args.export_report)
        print(f"Audit report exported to {args.export_report}")
    else:
        print(visualizer.visualize_agent_contributions(args.task_id, filter_criteria))
        
    # Always export audit report by default
    if not args.export_report:
        visualizer.export_audit_report()

if __name__ == "__main__":
    main() 