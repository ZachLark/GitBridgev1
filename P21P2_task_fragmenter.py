#!/usr/bin/env python3
"""
GitBridge Task Fragmentation Engine
Phase: GBP21
Part: P21P2
Step: P21P2S1
Task: P21P2S1T1 - Task Fragmentation Implementation

Create a parsing tool to break master tasks into subtasks and match subtasks to agents by role and domain.
Integrate webhook or function-based task dispatch system.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P21P2 Schema]
"""

import json
import logging
import re
import argparse
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

@dataclass
class Subtask:
    """Represents a fragmented subtask."""
    task_id: str
    parent_task_id: str
    description: str
    task_type: str
    domain: str
    priority: float
    estimated_complexity: str  # low, medium, high
    required_roles: List[str]
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskFragment:
    """Represents a fragmented master task."""
    master_task_id: str
    original_prompt: str
    task_type: str
    domain: str
    subtasks: List[Subtask]
    coordination_strategy: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "fragmented"  # fragmented, in_progress, completed, failed

@dataclass
class ValidationWarning:
    """Represents a validation warning for subtasks."""
    subtask_id: str
    warning_type: str  # malformed_description, missing_roles, circular_dependency, etc.
    message: str
    severity: str  # low, medium, high
    suggested_fix: Optional[str] = None

class TaskFragmenter:
    """
    Task fragmentation engine for breaking down complex tasks.
    
    Phase: GBP21
    Part: P21P2
    Step: P21P2S1
    Task: P21P2S1T1 - Core Implementation
    
    Features:
    - Parse master tasks into subtasks
    - Match subtasks to agents by role and domain
    - Task dispatch system integration
    - Dependency management
    - Dry-run mode for preview and validation
    """
    
    def __init__(self, roles_config_path: str = "roles_config.json"):
        """
        Initialize the task fragmenter.
        
        Args:
            roles_config_path: Path to roles configuration file
        """
        self.roles_config = self._load_roles_config(roles_config_path)
        self.fragmentation_history = []
        self.task_counter = 0
        
        logger.info("[P21P2S1T1] TaskFragmenter initialized")
        
    def _load_roles_config(self, config_path: str) -> Dict[str, Any]:
        """Load roles configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"[P21P2S1T1] Loaded roles config with {len(config.get('agents', []))} agents")
            return config
        except Exception as e:
            logger.error(f"[P21P2S1T1] Failed to load roles config: {e}")
            return {}
            
    def fragment_task(
        self,
        prompt: str,
        task_type: str = "general",
        domain: str = "general",
        coordination_strategy: str = "hierarchical",
        dry_run: bool = False
    ) -> TaskFragment:
        """
        Fragment a master task into subtasks.
        
        Args:
            prompt: Original task prompt
            task_type: Type of task
            domain: Domain of the task
            coordination_strategy: Strategy for coordinating subtasks
            dry_run: If True, only preview without storing in history
            
        Returns:
            TaskFragment: Fragmented task with subtasks
        """
        logger.info(f"[P21P2S1T1] Fragmenting task: {task_type} in domain {domain} (dry_run: {dry_run})")
        
        # Generate unique task ID
        self.task_counter += 1
        master_task_id = f"task_{self.task_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Analyze task complexity and determine fragmentation strategy
        complexity = self._analyze_task_complexity(prompt, task_type)
        fragmentation_strategy = self._determine_fragmentation_strategy(complexity, task_type)
        
        # Generate subtasks based on strategy
        subtasks = self._generate_subtasks(prompt, task_type, domain, master_task_id, fragmentation_strategy)
        
        # Validate subtasks if in dry-run mode
        validation_warnings = []
        if dry_run:
            validation_warnings = self._validate_subtasks(subtasks)
        
        # Create task fragment
        task_fragment = TaskFragment(
            master_task_id=master_task_id,
            original_prompt=prompt,
            task_type=task_type,
            domain=domain,
            subtasks=subtasks,
            coordination_strategy=coordination_strategy
        )
        
        # Store in history only if not dry-run
        if not dry_run:
            self.fragmentation_history.append(task_fragment)
        
        # Log validation warnings
        if validation_warnings:
            logger.warning(f"[P21P2S1T1] Found {len(validation_warnings)} validation warnings")
            for warning in validation_warnings:
                logger.warning(f"[P21P2S1T1] {warning.warning_type}: {warning.message}")
        
        logger.info(f"[P21P2S1T1] Task fragmented into {len(subtasks)} subtasks")
        return task_fragment
        
    def preview_fragmentation(
        self,
        prompt: str,
        task_type: str = "general",
        domain: str = "general",
        coordination_strategy: str = "hierarchical"
    ) -> Tuple[TaskFragment, List[ValidationWarning]]:
        """
        Preview task fragmentation without storing in history.
        
        Args:
            prompt: Original task prompt
            task_type: Type of task
            domain: Domain of the task
            coordination_strategy: Strategy for coordinating subtasks
            
        Returns:
            Tuple[TaskFragment, List[ValidationWarning]]: Preview fragment and validation warnings
        """
        # Perform dry-run fragmentation
        task_fragment = self.fragment_task(
            prompt, task_type, domain, coordination_strategy, dry_run=True
        )
        
        # Validate subtasks
        validation_warnings = self._validate_subtasks(task_fragment.subtasks)
        
        return task_fragment, validation_warnings
        
    def _validate_subtasks(self, subtasks: List[Subtask]) -> List[ValidationWarning]:
        """Validate subtasks and return warnings."""
        warnings = []
        
        for subtask in subtasks:
            # Check for malformed descriptions
            if len(subtask.description.strip()) < 10:
                warnings.append(ValidationWarning(
                    subtask_id=subtask.task_id,
                    warning_type="malformed_description",
                    message=f"Description too short: '{subtask.description}'",
                    severity="medium",
                    suggested_fix="Provide more detailed description"
                ))
            
            # Check for missing required roles
            if not subtask.required_roles:
                warnings.append(ValidationWarning(
                    subtask_id=subtask.task_id,
                    warning_type="missing_roles",
                    message="No required roles specified",
                    severity="high",
                    suggested_fix="Specify at least one required role"
                ))
            
            # Check for circular dependencies
            if subtask.task_id in subtask.dependencies:
                warnings.append(ValidationWarning(
                    subtask_id=subtask.task_id,
                    warning_type="circular_dependency",
                    message=f"Subtask depends on itself: {subtask.task_id}",
                    severity="high",
                    suggested_fix="Remove self-dependency"
                ))
            
            # Check for invalid complexity levels
            valid_complexities = ['low', 'medium', 'high']
            if subtask.estimated_complexity not in valid_complexities:
                warnings.append(ValidationWarning(
                    subtask_id=subtask.task_id,
                    warning_type="invalid_complexity",
                    message=f"Invalid complexity level: {subtask.estimated_complexity}",
                    severity="medium",
                    suggested_fix=f"Use one of: {', '.join(valid_complexities)}"
                ))
        
        # Check for dependency cycles across subtasks
        dependency_warnings = self._check_dependency_cycles(subtasks)
        warnings.extend(dependency_warnings)
        
        return warnings
        
    def _check_dependency_cycles(self, subtasks: List[Subtask]) -> List[ValidationWarning]:
        """Check for circular dependencies across subtasks."""
        warnings = []
        
        # Build dependency graph
        dependency_graph = {}
        for subtask in subtasks:
            dependency_graph[subtask.task_id] = subtask.dependencies
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            if node in rec_stack:
                return True
            if node in visited:
                return False
                
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                if has_cycle(neighbor):
                    return True
                    
            rec_stack.remove(node)
            return False
        
        # Check each subtask for cycles
        for subtask in subtasks:
            if has_cycle(subtask.task_id):
                warnings.append(ValidationWarning(
                    subtask_id=subtask.task_id,
                    warning_type="dependency_cycle",
                    message=f"Circular dependency detected involving {subtask.task_id}",
                    severity="high",
                    suggested_fix="Review and remove circular dependencies"
                ))
        
        return warnings
        
    def _analyze_task_complexity(self, prompt: str, task_type: str) -> str:
        """Analyze the complexity of a task."""
        word_count = len(prompt.split())
        
        # Complexity indicators
        complexity_indicators = {
            'low': ['simple', 'basic', 'quick', 'easy'],
            'medium': ['analyze', 'review', 'explain', 'compare'],
            'high': ['complex', 'comprehensive', 'detailed', 'thorough', 'multiple', 'various']
        }
        
        prompt_lower = prompt.lower()
        
        # Count complexity indicators
        complexity_scores = {}
        for level, indicators in complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in prompt_lower)
            complexity_scores[level] = score
            
        # Determine complexity based on indicators and word count
        if word_count > 100 or complexity_scores.get('high', 0) > 2:
            return 'high'
        elif word_count > 50 or complexity_scores.get('medium', 0) > 1:
            return 'medium'
        else:
            return 'low'
            
    def _determine_fragmentation_strategy(self, complexity: str, task_type: str) -> str:
        """Determine the fragmentation strategy based on complexity and task type."""
        if complexity == 'high':
            return 'comprehensive'
        elif task_type in ['code_review', 'analysis', 'documentation']:
            return 'structured'
        else:
            return 'simple'
            
    def _generate_subtasks(
        self,
        prompt: str,
        task_type: str,
        domain: str,
        master_task_id: str,
        strategy: str
    ) -> List[Subtask]:
        """Generate subtasks based on the fragmentation strategy."""
        subtasks = []
        
        if strategy == 'comprehensive':
            subtasks = self._comprehensive_fragmentation(prompt, task_type, domain, master_task_id)
        elif strategy == 'structured':
            subtasks = self._structured_fragmentation(prompt, task_type, domain, master_task_id)
        else:
            subtasks = self._simple_fragmentation(prompt, task_type, domain, master_task_id)
            
        return subtasks
        
    def _comprehensive_fragmentation(
        self,
        prompt: str,
        task_type: str,
        domain: str,
        master_task_id: str
    ) -> List[Subtask]:
        """Comprehensive fragmentation for complex tasks."""
        subtasks = []
        
        # Analysis phase
        subtasks.append(Subtask(
            task_id=f"{master_task_id}_analysis",
            parent_task_id=master_task_id,
            description=f"Analyze and understand the requirements: {prompt[:100]}...",
            task_type="analysis",
            domain=domain,
            priority=0.9,
            estimated_complexity="medium",
            required_roles=["Synthesizer", "Analyst"],
            dependencies=[]
        ))
        
        # Research phase
        subtasks.append(Subtask(
            task_id=f"{master_task_id}_research",
            parent_task_id=master_task_id,
            description=f"Research relevant information and context for: {prompt[:100]}...",
            task_type="research",
            domain=domain,
            priority=0.8,
            estimated_complexity="medium",
            required_roles=["Synthesizer", "Explainer"],
            dependencies=[f"{master_task_id}_analysis"]
        ))
        
        # Creation phase
        subtasks.append(Subtask(
            task_id=f"{master_task_id}_creation",
            parent_task_id=master_task_id,
            description=f"Create the main output for: {prompt[:100]}...",
            task_type=task_type,
            domain=domain,
            priority=0.95,
            estimated_complexity="high",
            required_roles=self._get_required_roles(task_type, domain),
            dependencies=[f"{master_task_id}_analysis", f"{master_task_id}_research"]
        ))
        
        # Review phase
        subtasks.append(Subtask(
            task_id=f"{master_task_id}_review",
            parent_task_id=master_task_id,
            description=f"Review and validate the output for: {prompt[:100]}...",
            task_type="review",
            domain=domain,
            priority=0.85,
            estimated_complexity="medium",
            required_roles=["Editor", "Challenger"],
            dependencies=[f"{master_task_id}_creation"]
        ))
        
        # Optimization phase
        subtasks.append(Subtask(
            task_id=f"{master_task_id}_optimization",
            parent_task_id=master_task_id,
            description=f"Optimize and improve the final output for: {prompt[:100]}...",
            task_type="optimization",
            domain=domain,
            priority=0.8,
            estimated_complexity="medium",
            required_roles=["Optimizer", "Editor"],
            dependencies=[f"{master_task_id}_review"]
        ))
        
        return subtasks
        
    def _structured_fragmentation(
        self,
        prompt: str,
        task_type: str,
        domain: str,
        master_task_id: str
    ) -> List[Subtask]:
        """Structured fragmentation for specific task types."""
        subtasks = []
        
        if task_type == "code_review":
            # Code review specific fragmentation
            subtasks.extend([
                Subtask(
                    task_id=f"{master_task_id}_security_review",
                    parent_task_id=master_task_id,
                    description="Review code for security vulnerabilities and best practices",
                    task_type="security_review",
                    domain="code_review",
                    priority=0.9,
                    estimated_complexity="medium",
                    required_roles=["Code_Specialist", "Challenger"],
                    dependencies=[]
                ),
                Subtask(
                    task_id=f"{master_task_id}_performance_review",
                    parent_task_id=master_task_id,
                    description="Review code for performance optimizations",
                    task_type="performance_review",
                    domain="code_review",
                    priority=0.8,
                    estimated_complexity="medium",
                    required_roles=["Code_Specialist", "Optimizer"],
                    dependencies=[]
                ),
                Subtask(
                    task_id=f"{master_task_id}_readability_review",
                    parent_task_id=master_task_id,
                    description="Review code for readability and maintainability",
                    task_type="readability_review",
                    domain="code_review",
                    priority=0.7,
                    estimated_complexity="low",
                    required_roles=["Editor", "Code_Specialist"],
                    dependencies=[]
                )
            ])
        elif task_type == "analysis":
            # Analysis specific fragmentation
            subtasks.extend([
                Subtask(
                    task_id=f"{master_task_id}_data_analysis",
                    parent_task_id=master_task_id,
                    description="Analyze data and extract insights",
                    task_type="data_analysis",
                    domain="analysis",
                    priority=0.9,
                    estimated_complexity="high",
                    required_roles=["Synthesizer", "Analyst"],
                    dependencies=[]
                ),
                Subtask(
                    task_id=f"{master_task_id}_interpretation",
                    parent_task_id=master_task_id,
                    description="Interpret analysis results and provide conclusions",
                    task_type="interpretation",
                    domain="analysis",
                    priority=0.8,
                    estimated_complexity="medium",
                    required_roles=["Explainer", "Synthesizer"],
                    dependencies=[f"{master_task_id}_data_analysis"]
                )
            ])
        else:
            # Generic structured fragmentation
            subtasks.extend([
                Subtask(
                    task_id=f"{master_task_id}_planning",
                    parent_task_id=master_task_id,
                    description=f"Plan the approach for: {prompt[:100]}...",
                    task_type="planning",
                    domain=domain,
                    priority=0.8,
                    estimated_complexity="medium",
                    required_roles=["Synthesizer", "Coordinator"],
                    dependencies=[]
                ),
                Subtask(
                    task_id=f"{master_task_id}_execution",
                    parent_task_id=master_task_id,
                    description=f"Execute the main task: {prompt[:100]}...",
                    task_type=task_type,
                    domain=domain,
                    priority=0.9,
                    estimated_complexity="high",
                    required_roles=self._get_required_roles(task_type, domain),
                    dependencies=[f"{master_task_id}_planning"]
                ),
                Subtask(
                    task_id=f"{master_task_id}_validation",
                    parent_task_id=master_task_id,
                    description=f"Validate the results for: {prompt[:100]}...",
                    task_type="validation",
                    domain=domain,
                    priority=0.7,
                    estimated_complexity="medium",
                    required_roles=["Editor", "Challenger"],
                    dependencies=[f"{master_task_id}_execution"]
                )
            ])
            
        return subtasks
        
    def _simple_fragmentation(
        self,
        prompt: str,
        task_type: str,
        domain: str,
        master_task_id: str
    ) -> List[Subtask]:
        """Simple fragmentation for straightforward tasks."""
        return [
            Subtask(
                task_id=f"{master_task_id}_main",
                parent_task_id=master_task_id,
                description=f"Execute the main task: {prompt}",
                task_type=task_type,
                domain=domain,
                priority=0.9,
                estimated_complexity="medium",
                required_roles=self._get_required_roles(task_type, domain),
                dependencies=[]
            )
        ]
        
    def _get_required_roles(self, task_type: str, domain: str) -> List[str]:
        """Get required roles for a task type and domain."""
        # Get preferred roles from task domains
        task_domains = self.roles_config.get('task_domains', {})
        domain_config = task_domains.get(domain, {})
        preferred_roles = domain_config.get('preferred_roles', ['Generalist'])
        
        # Return top 2 preferred roles
        return preferred_roles[:2]
        
    def assign_agents_to_subtasks(self, task_fragment: TaskFragment) -> Dict[str, str]:
        """
        Assign agents to subtasks based on roles and availability.
        
        Args:
            task_fragment: The task fragment to assign agents to
            
        Returns:
            Dict[str, str]: Mapping of subtask_id to assigned agent
        """
        assignments = {}
        agents = self.roles_config.get('agents', [])
        
        for subtask in task_fragment.subtasks:
            # Find best matching agent
            best_agent = self._find_best_agent(subtask, agents)
            if best_agent:
                subtask.assigned_agent = best_agent['agent_id']
                assignments[subtask.task_id] = best_agent['agent_id']
                logger.info(f"[P21P2S1T1] Assigned {best_agent['agent_name']} to {subtask.task_id}")
            else:
                logger.warning(f"[P21P2S1T1] No suitable agent found for {subtask.task_id}")
                
        return assignments
        
    def _find_best_agent(self, subtask: Subtask, agents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the best agent for a subtask based on roles and capabilities."""
        best_agent = None
        best_score = 0
        
        for agent in agents:
            score = self._calculate_agent_score(subtask, agent)
            if score > best_score:
                best_score = score
                best_agent = agent
                
        return best_agent
        
    def _calculate_agent_score(self, subtask: Subtask, agent: Dict[str, Any]) -> float:
        """Calculate how well an agent matches a subtask."""
        score = 0
        
        # Role matching
        agent_roles = agent.get('roles', [])
        required_roles = subtask.required_roles
        
        for role in required_roles:
            if role in agent_roles:
                score += 0.4  # High weight for role matching
                
        # Domain matching
        agent_domains = agent.get('domains', [])
        if subtask.domain in agent_domains:
            score += 0.3  # Medium weight for domain matching
            
        # Priority weight
        priority_weight = agent.get('priority_weight', 0.5)
        score += priority_weight * 0.2  # Lower weight for priority
        
        # Complexity matching
        complexity = subtask.estimated_complexity
        if complexity == 'high' and 'Synthesizer' in agent_roles:
            score += 0.1
        elif complexity == 'low' and 'Generalist' in agent_roles:
            score += 0.1
            
        return score
        
    def dispatch_subtasks(self, task_fragment: TaskFragment) -> Dict[str, Any]:
        """
        Dispatch subtasks to assigned agents.
        
        Args:
            task_fragment: The task fragment to dispatch
            
        Returns:
            Dict[str, Any]: Dispatch results and metadata
        """
        dispatch_results = {
            'master_task_id': task_fragment.master_task_id,
            'dispatched_subtasks': [],
            'failed_subtasks': [],
            'dispatch_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        for subtask in task_fragment.subtasks:
            if subtask.assigned_agent:
                try:
                    # Simulate task dispatch (in real implementation, this would call agent APIs)
                    dispatch_result = self._dispatch_to_agent(subtask)
                    dispatch_results['dispatched_subtasks'].append({
                        'subtask_id': subtask.task_id,
                        'assigned_agent': subtask.assigned_agent,
                        'status': 'dispatched',
                        'dispatch_result': dispatch_result
                    })
                    subtask.status = 'in_progress'
                except Exception as e:
                    logger.error(f"[P21P2S1T1] Failed to dispatch {subtask.task_id}: {e}")
                    dispatch_results['failed_subtasks'].append({
                        'subtask_id': subtask.task_id,
                        'error': str(e)
                    })
                    subtask.status = 'failed'
            else:
                dispatch_results['failed_subtasks'].append({
                    'subtask_id': subtask.task_id,
                    'error': 'No agent assigned'
                })
                subtask.status = 'failed'
                
        return dispatch_results
        
    def _dispatch_to_agent(self, subtask: Subtask) -> Dict[str, Any]:
        """Dispatch a subtask to a specific agent."""
        # This is a simulation - in real implementation, this would make API calls
        return {
            'agent_id': subtask.assigned_agent,
            'subtask_id': subtask.task_id,
            'dispatch_method': 'api_call',
            'estimated_completion_time': self._estimate_completion_time(subtask),
            'priority': subtask.priority
        }
        
    def _estimate_completion_time(self, subtask: Subtask) -> int:
        """Estimate completion time in seconds based on complexity."""
        complexity_times = {
            'low': 30,
            'medium': 120,
            'high': 300
        }
        return complexity_times.get(subtask.estimated_complexity, 60)
        
    def get_fragmentation_history(self) -> List[TaskFragment]:
        """Get history of fragmented tasks."""
        return self.fragmentation_history
        
    def export_routing_logs(self, output_path: str = "routing_logs.json") -> None:
        """Export routing logs to JSON file."""
        logs = []
        for fragment in self.fragmentation_history:
            log_entry = {
                'master_task_id': fragment.master_task_id,
                'original_prompt': fragment.original_prompt,
                'task_type': fragment.task_type,
                'domain': fragment.domain,
                'coordination_strategy': fragment.coordination_strategy,
                'created_at': fragment.created_at.isoformat(),
                'status': fragment.status,
                'subtasks': [
                    {
                        'task_id': subtask.task_id,
                        'description': subtask.description,
                        'task_type': subtask.task_type,
                        'domain': subtask.domain,
                        'priority': subtask.priority,
                        'estimated_complexity': subtask.estimated_complexity,
                        'required_roles': subtask.required_roles,
                        'dependencies': subtask.dependencies,
                        'assigned_agent': subtask.assigned_agent,
                        'status': subtask.status,
                        'created_at': subtask.created_at.isoformat()
                    }
                    for subtask in fragment.subtasks
                ]
            }
            logs.append(log_entry)
            
        try:
            with open(output_path, 'w') as f:
                json.dump(logs, f, indent=2)
            logger.info(f"[P21P2S1T1] Routing logs exported to {output_path}")
        except Exception as e:
            logger.error(f"[P21P2S1T1] Failed to export routing logs: {e}")

def main():
    """Main function for CLI interface with hot-reload support."""
    parser = argparse.ArgumentParser(description='GitBridge Task Fragmentation Engine')
    parser.add_argument('--prompt', '-p', help='Task prompt to fragment')
    parser.add_argument('--task-type', '-t', default='general', help='Type of task')
    parser.add_argument('--domain', '-d', default='general', help='Domain of task')
    parser.add_argument('--strategy', '-s', default='hierarchical', help='Coordination strategy')
    parser.add_argument('--dry-run', action='store_true', help='Preview fragmentation without execution')
    parser.add_argument('--export-logs', '-e', help='Export routing logs to specified file')
    parser.add_argument('--reload-roles', action='store_true', help='Reload roles_config.json at runtime')
    args = parser.parse_args()
    
    logger.info("[P21P2S1T1] Testing Task Fragmentation Engine")
    fragmenter = TaskFragmenter()
    
    if args.reload_roles:
        fragmenter.roles_config = fragmenter._load_roles_config('roles_config.json')
        print("✅ roles_config.json reloaded at runtime.")
        return
    
    if args.prompt:
        # Use provided prompt
        if args.dry_run:
            print(f"🔍 DRY-RUN MODE: Previewing fragmentation for '{args.prompt}'")
            print("=" * 60)
            
            task_fragment, warnings = fragmenter.preview_fragmentation(
                args.prompt, args.task_type, args.domain, args.strategy
            )
            
            # Display preview
            print(f"📋 Task Fragment Preview:")
            print(f"   Master Task ID: {task_fragment.master_task_id}")
            print(f"   Task Type: {task_fragment.task_type}")
            print(f"   Domain: {task_fragment.domain}")
            print(f"   Strategy: {task_fragment.coordination_strategy}")
            print(f"   Subtasks: {len(task_fragment.subtasks)}")
            print()
            
            # Display subtasks
            for i, subtask in enumerate(task_fragment.subtasks, 1):
                print(f"   {i}. {subtask.task_id}")
                print(f"      Description: {subtask.description}")
                print(f"      Type: {subtask.task_type}")
                print(f"      Domain: {subtask.domain}")
                print(f"      Complexity: {subtask.estimated_complexity}")
                print(f"      Required Roles: {', '.join(subtask.required_roles)}")
                print(f"      Dependencies: {', '.join(subtask.dependencies) if subtask.dependencies else 'None'}")
                print()
            
            # Display validation warnings
            if warnings:
                print("⚠️  VALIDATION WARNINGS:")
                print("-" * 30)
                for warning in warnings:
                    print(f"   [{warning.severity.upper()}] {warning.subtask_id}: {warning.message}")
                    if warning.suggested_fix:
                        print(f"      💡 Suggestion: {warning.suggested_fix}")
                    print()
            else:
                print("✅ No validation warnings found")
                
        else:
            # Normal execution
            print(f"🚀 EXECUTING: Fragmenting task '{args.prompt}'")
            print("=" * 60)
            
            fragment = fragmenter.fragment_task(
                args.prompt, args.task_type, args.domain, args.strategy
            )
            assignments = fragmenter.assign_agents_to_subtasks(fragment)
            dispatch = fragmenter.dispatch_subtasks(fragment)
            
            print(f"✅ Task fragmented into {len(fragment.subtasks)} subtasks")
            print(f"📋 Assignments: {assignments}")
            print(f"📤 Dispatch results: {len(dispatch['dispatched_subtasks'])} successful, {len(dispatch['failed_subtasks'])} failed")
    else:
        # Default test cases
        print("🧪 Running default test cases")
        print("=" * 60)
        
        # Test case 1: Simple task
        simple_task = "Explain how to use Python decorators"
        print(f"📝 Test 1: Simple task - '{simple_task}'")
        
        if args.dry_run:
            fragment1, warnings1 = fragmenter.preview_fragmentation(simple_task, "explanation", "education")
            print(f"   Preview: {len(fragment1.subtasks)} subtasks, {len(warnings1)} warnings")
        else:
            fragment1 = fragmenter.fragment_task(simple_task, "explanation", "education")
            assignments1 = fragmenter.assign_agents_to_subtasks(fragment1)
            print(f"   Result: {len(fragment1.subtasks)} subtasks, {len(assignments1)} assignments")
        print()
        
        # Test case 2: Complex task
        complex_task = "Create a comprehensive code review system that analyzes security vulnerabilities, performance issues, and code quality, with detailed reporting and recommendations for improvement"
        print(f"📝 Test 2: Complex task - '{complex_task[:50]}...'")
        
        if args.dry_run:
            fragment2, warnings2 = fragmenter.preview_fragmentation(complex_task, "code_review", "technical", "comprehensive")
            print(f"   Preview: {len(fragment2.subtasks)} subtasks, {len(warnings2)} warnings")
        else:
            fragment2 = fragmenter.fragment_task(complex_task, "code_review", "technical", "comprehensive")
            assignments2 = fragmenter.assign_agents_to_subtasks(fragment2)
            dispatch2 = fragmenter.dispatch_subtasks(fragment2)
            print(f"   Result: {len(fragment2.subtasks)} subtasks, {len(assignments2)} assignments, {len(dispatch2['dispatched_subtasks'])} dispatched")
        print()
    
    # Export routing logs if requested
    if args.export_logs:
        fragmenter.export_routing_logs(args.export_logs)
        print(f"📊 Routing logs exported to {args.export_logs}")
    elif not args.dry_run:
        # Export default logs for non-dry-run mode
        fragmenter.export_routing_logs()

if __name__ == "__main__":
    main() 