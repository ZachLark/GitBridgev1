"""
AI routing functionality for GitBridge MAS Lite.

This module provides AI-based routing functionality for GitBridge's event processing
system, following MAS Lite Protocol v2.1 routing requirements.
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

from mas_core.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from mas_core.utils.logging import MASLogger

logger = MASLogger(__name__)

@dataclass
class AgentInfo:
    """Agent information."""
    agent_id: str
    name: str
    capabilities: List[str]
    status: str
    load: float
    last_heartbeat: str

class AIRouter:
    """AI-based task router."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize router.
        
        Args:
            config: Configuration dictionary containing router settings
                   Required keys:
                   - router.load_threshold: Maximum agent load
                   - router.heartbeat_timeout: Agent heartbeat timeout in seconds
        """
        self.load_threshold = config["router"]["load_threshold"]
        self.heartbeat_timeout = config["router"]["heartbeat_timeout"]
        self.agents: Dict[str, AgentInfo] = {}
        self.error_handler = ErrorHandler()
        
    def register_agent(self, agent_info: AgentInfo) -> bool:
        """Register an agent.
        
        Args:
            agent_info: Agent information
            
        Returns:
            bool: True if registration successful
        """
        try:
            # Validate agent info
            if not agent_info.agent_id:
                raise ValueError("Agent ID is required")
                
            if not agent_info.name:
                raise ValueError("Agent name is required")
                
            if not agent_info.capabilities:
                raise ValueError("Agent capabilities are required")
                
            if not agent_info.status:
                raise ValueError("Agent status is required")
                
            if agent_info.load < 0 or agent_info.load > 1:
                raise ValueError("Agent load must be between 0 and 1")
                
            # Register agent
            self.agents[agent_info.agent_id] = agent_info
            
            logger.info(
                f"Registered agent {agent_info.name}",
                extra={
                    "agent_id": agent_info.agent_id,
                    "capabilities": agent_info.capabilities
                }
            )
            return True
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to register agent: {str(e)}",
                details={
                    "agent_info": agent_info.__dict__,
                    "error": str(e)
                }
            )
            return False
            
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            bool: True if unregistration successful
        """
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
                
            agent = self.agents.pop(agent_id)
            
            logger.info(
                f"Unregistered agent {agent.name}",
                extra={"agent_id": agent_id}
            )
            return True
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to unregister agent: {str(e)}",
                details={
                    "agent_id": agent_id,
                    "error": str(e)
                }
            )
            return False
            
    def update_agent_status(self, agent_id: str, status: str, load: float) -> bool:
        """Update agent status.
        
        Args:
            agent_id: Agent identifier
            status: New status
            load: New load value
            
        Returns:
            bool: True if update successful
        """
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
                
            if load < 0 or load > 1:
                raise ValueError("Load must be between 0 and 1")
                
            agent = self.agents[agent_id]
            agent.status = status
            agent.load = load
            agent.last_heartbeat = datetime.now(timezone.utc).isoformat()
            
            logger.info(
                f"Updated agent {agent.name} status",
                extra={
                    "agent_id": agent_id,
                    "status": status,
                    "load": load
                }
            )
            return True
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to update agent status: {str(e)}",
                details={
                    "agent_id": agent_id,
                    "status": status,
                    "load": load,
                    "error": str(e)
                }
            )
            return False
            
    def route_task(self, task: Dict[str, Any]) -> Optional[str]:
        """Route task to best suited agent.
        
        Args:
            task: Task to route
            
        Returns:
            Optional[str]: Agent ID if routing successful, None otherwise
        """
        try:
            # Get required capabilities
            if "required_capabilities" not in task:
                raise ValueError("Task missing required capabilities")
                
            required_capabilities = task["required_capabilities"]
            
            # Find eligible agents
            eligible_agents = [
                agent for agent in self.agents.values()
                if all(cap in agent.capabilities for cap in required_capabilities)
                and agent.status == "available"
                and agent.load < self.load_threshold
            ]
            
            if not eligible_agents:
                logger.warning(
                    "No eligible agents found",
                    extra={
                        "required_capabilities": required_capabilities,
                        "task": task
                    }
                )
                return None
                
            # Sort by load
            eligible_agents.sort(key=lambda a: a.load)
            
            # Return agent with lowest load
            selected_agent = eligible_agents[0]
            
            logger.info(
                f"Routed task to agent {selected_agent.name}",
                extra={
                    "agent_id": selected_agent.agent_id,
                    "task": task
                }
            )
            return selected_agent.agent_id
            
        except Exception as e:
            error_id = str(uuid.uuid4())
            self.error_handler.handle_error(
                error_id=error_id,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.ERROR,
                message=f"Failed to route task: {str(e)}",
                details={
                    "task": task,
                    "error": str(e)
                }
            )
            return None
            
    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent information.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Optional[AgentInfo]: Agent information if found
        """
        return self.agents.get(agent_id)
        
    def list_agents(self) -> List[AgentInfo]:
        """List all registered agents.
        
        Returns:
            List[AgentInfo]: List of agent information
        """
        return list(self.agents.values()) 