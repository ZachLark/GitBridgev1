#!/usr/bin/env python3
"""Agent framework implementation for GitBridge."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod

class AgentState:
    """Represents the current state of an agent."""
    
    def __init__(self):
        self.task_queue: List[Dict[str, Any]] = []
        self.current_task: Optional[Dict[str, Any]] = None
        self.completed_tasks: List[Dict[str, Any]] = []
        self.failed_tasks: List[Dict[str, Any]] = []
        self.start_time: datetime = datetime.now()
        self.last_heartbeat: datetime = datetime.now()
        self.status: str = "idle"
        self.metrics: Dict[str, Any] = {
            "tasks_processed": 0,
            "success_rate": 0.0,
            "avg_processing_time": 0.0
        }

class AgentCapability:
    """Defines a specific capability of an agent."""
    
    def __init__(
        self,
        name: str,
        handler: Callable,
        requirements: List[str],
        description: str
    ):
        self.name = name
        self.handler = handler
        self.requirements = requirements
        self.description = description
        self.enabled = True

class BaseAgent(ABC):
    """Base class for all GitBridge agents."""
    
    def __init__(self, agent_id: str, capabilities: List[AgentCapability]):
        self.agent_id = agent_id
        self.capabilities = {cap.name: cap for cap in capabilities}
        self.state = AgentState()
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
        # Configure logging
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f"logs/agent_{agent_id}.log")
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent and its resources."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Clean up resources and prepare for shutdown."""
        pass
    
    async def process_task(self, task: Dict[str, Any]) -> bool:
        """Process a single task using appropriate capabilities."""
        try:
            self.state.current_task = task
            self.state.status = "processing"
            self.logger.info(f"Processing task {task['task_id']}")
            
            # Validate task requirements
            if not self._validate_task(task):
                raise ValueError("Task validation failed")
            
            # Find matching capability
            capability = self._find_capability(task)
            if not capability:
                raise ValueError("No matching capability found")
            
            # Execute task
            start_time = datetime.now()
            result = await capability.handler(task)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update metrics
            self._update_metrics(True, processing_time)
            
            # Log success
            self.logger.info(f"Task {task['task_id']} completed successfully")
            self.state.completed_tasks.append(task)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process task {task['task_id']}: {str(e)}")
            self._update_metrics(False, 0)
            self.state.failed_tasks.append(task)
            return False
        
        finally:
            self.state.current_task = None
            self.state.status = "idle"
    
    def _validate_task(self, task: Dict[str, Any]) -> bool:
        """Validate task structure and requirements."""
        required_fields = ["task_id", "type", "requirements"]
        return all(field in task for field in required_fields)
    
    def _find_capability(self, task: Dict[str, Any]) -> Optional[AgentCapability]:
        """Find a matching capability for the task."""
        task_type = task.get("type")
        task_requirements = set(task.get("requirements", []))
        
        for capability in self.capabilities.values():
            if (capability.enabled and
                capability.name == task_type and
                set(capability.requirements).issubset(task_requirements)):
                return capability
        return None
    
    def _update_metrics(self, success: bool, processing_time: float):
        """Update agent performance metrics."""
        metrics = self.state.metrics
        metrics["tasks_processed"] += 1
        
        if success:
            current_success = metrics["success_rate"] * (metrics["tasks_processed"] - 1)
            metrics["success_rate"] = (current_success + 1) / metrics["tasks_processed"]
        else:
            current_success = metrics["success_rate"] * (metrics["tasks_processed"] - 1)
            metrics["success_rate"] = current_success / metrics["tasks_processed"]
        
        if processing_time > 0:
            current_avg = metrics["avg_processing_time"]
            metrics["avg_processing_time"] = (
                (current_avg * (metrics["tasks_processed"] - 1) + processing_time) /
                metrics["tasks_processed"]
            )
    
    async def heartbeat(self):
        """Update agent heartbeat and status."""
        while True:
            self.state.last_heartbeat = datetime.now()
            self.logger.debug(f"Agent {self.agent_id} heartbeat")
            await asyncio.sleep(60)  # Heartbeat every minute
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics."""
        return {
            "agent_id": self.agent_id,
            "status": self.state.status,
            "current_task": self.state.current_task,
            "metrics": self.state.metrics,
            "last_heartbeat": self.state.last_heartbeat.isoformat(),
            "uptime": (datetime.now() - self.state.start_time).total_seconds()
        }
    
    def enable_capability(self, capability_name: str):
        """Enable a specific capability."""
        if capability_name in self.capabilities:
            self.capabilities[capability_name].enabled = True
            self.logger.info(f"Enabled capability: {capability_name}")
    
    def disable_capability(self, capability_name: str):
        """Disable a specific capability."""
        if capability_name in self.capabilities:
            self.capabilities[capability_name].enabled = False
            self.logger.info(f"Disabled capability: {capability_name}")

class TaskProcessingAgent(BaseAgent):
    """Concrete implementation of a task processing agent."""
    
    async def initialize(self) -> bool:
        """Initialize the task processing agent."""
        try:
            # Create required directories
            Path("logs").mkdir(exist_ok=True)
            Path("outputs").mkdir(exist_ok=True)
            
            # Start heartbeat
            asyncio.create_task(self.heartbeat())
            
            self.logger.info(f"Agent {self.agent_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the task processing agent."""
        try:
            # Complete current task if any
            if self.state.current_task:
                await self.process_task(self.state.current_task)
            
            # Save final metrics
            with open(f"logs/agent_{self.agent_id}_metrics.json", "w") as f:
                json.dump(self.state.metrics, f)
            
            self.logger.info(f"Agent {self.agent_id} shutdown successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to shutdown agent: {str(e)}")
            return False 