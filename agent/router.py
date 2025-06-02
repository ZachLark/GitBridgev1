#!/usr/bin/env python3
"""Agent delegation routing system for GitBridge."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import asyncio
from dataclasses import dataclass

@dataclass
class RoutePolicy:
    """Defines a routing policy for task delegation."""
    capability_name: str
    priority: int
    requirements: Set[str]
    max_concurrent: int
    timeout_seconds: int

class DelegationRouter:
    """Handles task delegation and routing between agents."""
    
    def __init__(self):
        self.logger = logging.getLogger("delegation.router")
        self.policies: Dict[str, RoutePolicy] = {}
        self.active_routes: Dict[str, List[str]] = {}  # capability -> agent_ids
        self.agent_loads: Dict[str, int] = {}  # agent_id -> current task count
        
        # Configure logging
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("logs/router.log")
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
    
    def register_policy(self, policy: RoutePolicy):
        """Register a new routing policy."""
        self.policies[policy.capability_name] = policy
        self.active_routes[policy.capability_name] = []
        self.logger.info(f"Registered policy for capability: {policy.capability_name}")
    
    def register_agent(self, agent_id: str, capabilities: List[str]):
        """Register an agent with its capabilities."""
        for capability in capabilities:
            if capability in self.active_routes:
                self.active_routes[capability].append(agent_id)
        self.agent_loads[agent_id] = 0
        self.logger.info(f"Registered agent {agent_id} with capabilities: {capabilities}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the routing system."""
        for routes in self.active_routes.values():
            if agent_id in routes:
                routes.remove(agent_id)
        if agent_id in self.agent_loads:
            del self.agent_loads[agent_id]
        self.logger.info(f"Unregistered agent: {agent_id}")
    
    async def delegate_task(self, task: Dict[str, Any]) -> Optional[str]:
        """Delegate a task to an appropriate agent."""
        try:
            # Validate task
            if "type" not in task or "requirements" not in task:
                raise ValueError("Invalid task format")
            
            capability = task["type"]
            if capability not in self.policies:
                raise ValueError(f"No policy found for capability: {capability}")
            
            policy = self.policies[capability]
            
            # Validate requirements
            task_requirements = set(task.get("requirements", []))
            if not task_requirements.issubset(policy.requirements):
                raise ValueError("Task requirements not met by policy")
            
            # Find eligible agents
            eligible_agents = self.active_routes.get(capability, [])
            if not eligible_agents:
                raise ValueError(f"No agents available for capability: {capability}")
            
            # Select agent based on load and policy
            selected_agent = await self._select_agent(eligible_agents, policy)
            if not selected_agent:
                raise ValueError("No suitable agent found")
            
            # Update load
            self.agent_loads[selected_agent] += 1
            
            # Log delegation
            self.logger.info(
                f"Delegated task {task['task_id']} to agent {selected_agent}"
            )
            
            return selected_agent
            
        except Exception as e:
            self.logger.error(f"Task delegation failed: {str(e)}")
            return None
    
    async def _select_agent(
        self,
        eligible_agents: List[str],
        policy: RoutePolicy
    ) -> Optional[str]:
        """Select the most suitable agent based on policy."""
        min_load = float('inf')
        selected_agent = None
        
        for agent_id in eligible_agents:
            current_load = self.agent_loads.get(agent_id, 0)
            if (current_load < min_load and 
                current_load < policy.max_concurrent):
                min_load = current_load
                selected_agent = agent_id
        
        return selected_agent
    
    def task_completed(self, agent_id: str):
        """Update agent load when task is completed."""
        if agent_id in self.agent_loads:
            self.agent_loads[agent_id] = max(0, self.agent_loads[agent_id] - 1)
    
    def get_routing_status(self) -> Dict[str, Any]:
        """Get current routing system status."""
        return {
            "active_policies": len(self.policies),
            "registered_agents": len(self.agent_loads),
            "active_routes": {
                cap: len(agents) for cap, agents in self.active_routes.items()
            },
            "current_loads": self.agent_loads.copy()
        }

class CLIDelegator:
    """CLI interface for task delegation."""
    
    def __init__(self, router: DelegationRouter):
        self.router = router
        self.logger = logging.getLogger("delegation.cli")
        
        # Configure logging
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("logs/cli_delegator.log")
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
    
    async def delegate_from_file(self, task_file: Path) -> bool:
        """Delegate tasks from a file."""
        try:
            with task_file.open('r') as f:
                tasks = json.load(f)
            
            if not isinstance(tasks, list):
                tasks = [tasks]
            
            results = []
            for task in tasks:
                agent_id = await self.router.delegate_task(task)
                results.append({
                    'task_id': task['task_id'],
                    'delegated_to': agent_id,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Write delegation results
            output_file = task_file.parent / f"delegation_{task_file.stem}.json"
            with output_file.open('w') as f:
                json.dump(results, f, indent=2)
            
            self.logger.info(f"Delegated {len(results)} tasks from {task_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delegate tasks from {task_file}: {str(e)}")
            return False
    
    def get_delegation_status(self) -> Dict[str, Any]:
        """Get delegation system status."""
        return {
            "router_status": self.router.get_routing_status(),
            "cli_status": {
                "last_delegation": datetime.now().isoformat()
            }
        } 