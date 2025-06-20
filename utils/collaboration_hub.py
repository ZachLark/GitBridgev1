#!/usr/bin/env python3
"""
GitBridge Collaboration Hub
Task: P20P6B - Enhanced AI Agent Collaboration

A central hub for managing communication and collaboration between different AI agents
(Cursor, ChatGPT, Grok) in the GitBridge ecosystem. Implements advanced features for
agent interaction, decision tracking, and collaborative problem-solving.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from threading import Lock
from enum import Enum
import hashlib
from pathlib import Path

# Configure logging with UTC timestamps
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [P20P6b] [collaboration] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/collaboration.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Types of AI agents in the GitBridge ecosystem."""
    CURSOR = "cursor"
    CHATGPT = "chatgpt"
    GROK = "grok"
    HUMAN = "human"
    
    def __str__(self):
        return self.value
        
    def to_json(self):
        return self.value

def _serialize_agent_type(obj):
    """Serialize AgentType enum to JSON."""
    if isinstance(obj, AgentType):
        return obj.value
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

@dataclass
class Decision:
    """Record of a decision made during collaboration."""
    timestamp: str
    agent: AgentType
    context: str
    decision: str
    reasoning: str
    confidence: float
    supporting_agents: List[AgentType]
    dissenting_agents: List[AgentType]
    metadata: Dict[str, Any]

@dataclass
class Interaction:
    """Record of an interaction between agents."""
    timestamp: str
    initiator: AgentType
    responder: AgentType
    message_type: str
    content: str
    context: str
    thread_id: str
    parent_id: Optional[str]
    metadata: Dict[str, Any]

class CollaborationHub:
    """
    Central hub for managing AI agent collaboration in GitBridge.
    
    Features:
    - Cross-agent communication and decision tracking
    - Consensus building and disagreement resolution
    - Context preservation across interactions
    - Thread-based discussions
    - Knowledge sharing and caching
    """
    
    def __init__(self, workspace_dir: str = "collaboration_workspace"):
        """
        Initialize the collaboration hub.
        
        Args:
            workspace_dir: Directory for collaboration artifacts
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread-safe storage
        self._interaction_lock = Lock()
        self._decision_lock = Lock()
        self._context_lock = Lock()
        
        # Initialize storage files
        self.interactions_file = self.workspace_dir / "interactions.jsonl"
        self.decisions_file = self.workspace_dir / "decisions.jsonl"
        self.context_file = self.workspace_dir / "context_cache.json"
        
        # Initialize context cache
        self._init_context_cache()
        
        logger.info(f"CollaborationHub initialized in {workspace_dir}")
        
    def _init_context_cache(self):
        """Initialize the context cache for faster lookups."""
        if not self.context_file.exists():
            with open(self.context_file, 'w') as f:
                json.dump({}, f, default=_serialize_agent_type)
                
    def record_interaction(
        self,
        initiator: Union[str, AgentType],
        responder: Union[str, AgentType],
        message_type: str,
        content: str,
        context: str,
        thread_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record an interaction between agents.
        
        Args:
            initiator: Agent initiating the interaction
            responder: Agent responding to the interaction
            message_type: Type of message (e.g., 'question', 'suggestion', 'decision')
            content: Content of the interaction
            context: Context of the interaction
            thread_id: Optional thread ID for grouped interactions
            parent_id: Optional parent interaction ID
            metadata: Additional metadata about the interaction
            
        Returns:
            str: Interaction ID
        """
        # Convert string agent types to enum
        if isinstance(initiator, str):
            initiator = AgentType(initiator.lower())
        if isinstance(responder, str):
            responder = AgentType(responder.lower())
            
        # Generate thread ID if not provided
        if not thread_id:
            thread_id = hashlib.sha256(f"{time.time()}{initiator}{responder}".encode()).hexdigest()[:12]
            
        interaction = Interaction(
            timestamp=datetime.now(timezone.utc).isoformat(),
            initiator=initiator,
            responder=responder,
            message_type=message_type,
            content=content,
            context=context,
            thread_id=thread_id,
            parent_id=parent_id,
            metadata=metadata or {}
        )
        
        # Thread-safe write
        with self._interaction_lock:
            with open(self.interactions_file, 'a') as f:
                json.dump(asdict(interaction), f, default=_serialize_agent_type)
                f.write('\n')
                
        logger.info(
            f"Interaction recorded - {initiator.value} → {responder.value} "
            f"[{message_type}] (thread: {thread_id})"
        )
        
        return thread_id
        
    def record_decision(
        self,
        agent: Union[str, AgentType],
        context: str,
        decision: str,
        reasoning: str,
        confidence: float,
        supporting_agents: List[Union[str, AgentType]] = None,
        dissenting_agents: List[Union[str, AgentType]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a decision made during collaboration.
        
        Args:
            agent: Agent making the decision
            context: Context in which the decision was made
            decision: The actual decision
            reasoning: Reasoning behind the decision
            confidence: Confidence level (0-1)
            supporting_agents: Agents supporting the decision
            dissenting_agents: Agents disagreeing with the decision
            metadata: Additional metadata about the decision
        """
        # Convert string agent types to enum
        if isinstance(agent, str):
            agent = AgentType(agent.lower())
        
        supporting = []
        for a in (supporting_agents or []):
            supporting.append(AgentType(a.lower()) if isinstance(a, str) else a)
            
        dissenting = []
        for a in (dissenting_agents or []):
            dissenting.append(AgentType(a.lower()) if isinstance(a, str) else a)
        
        decision_record = Decision(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent=agent,
            context=context,
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            supporting_agents=supporting,
            dissenting_agents=dissenting,
            metadata=metadata or {}
        )
        
        # Thread-safe write
        with self._decision_lock:
            with open(self.decisions_file, 'a') as f:
                json.dump(asdict(decision_record), f, default=_serialize_agent_type)
                f.write('\n')
                
        logger.info(
            f"Decision recorded - {agent.value} "
            f"(confidence: {confidence:.2f}, support: {len(supporting)}, dissent: {len(dissenting)})"
        )
        
    def get_thread_history(
        self,
        thread_id: str,
        include_context: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get the history of interactions in a thread.
        
        Args:
            thread_id: Thread ID to retrieve
            include_context: Whether to include context in the response
            
        Returns:
            List of interaction records
        """
        history = []
        try:
            with open(self.interactions_file, 'r') as f:
                for line in f:
                    interaction = json.loads(line)
                    if interaction['thread_id'] == thread_id:
                        if not include_context:
                            interaction.pop('context', None)
                        history.append(interaction)
        except FileNotFoundError:
            logger.warning(f"No interaction history found for thread {thread_id}")
            
        return sorted(history, key=lambda x: x['timestamp'])
        
    def get_agent_decisions(
        self,
        agent: Union[str, AgentType],
        confidence_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get decisions made by a specific agent.
        
        Args:
            agent: Agent to query
            confidence_threshold: Minimum confidence level to include
            
        Returns:
            List of decision records
        """
        if isinstance(agent, str):
            agent = AgentType(agent.lower())
            
        decisions = []
        try:
            with open(self.decisions_file, 'r') as f:
                for line in f:
                    decision = json.loads(line)
                    if (AgentType(decision['agent']) == agent and
                        (confidence_threshold is None or
                         decision['confidence'] >= confidence_threshold)):
                        decisions.append(decision)
        except FileNotFoundError:
            logger.warning(f"No decisions found for agent {agent.value}")
            
        return sorted(decisions, key=lambda x: x['timestamp'])
        
    def get_consensus_metrics(self) -> Dict[str, Any]:
        """
        Calculate consensus metrics across all decisions.
        
        Returns:
            Dict containing consensus statistics
        """
        metrics = {
            "total_decisions": 0,
            "unanimous_decisions": 0,
            "contested_decisions": 0,
            "average_confidence": 0.0,
            "by_agent": {},
            "collaboration_score": 0.0
        }
        
        try:
            with open(self.decisions_file, 'r') as f:
                decisions = [json.loads(line) for line in f]
                
            if not decisions:
                return metrics
                
            metrics["total_decisions"] = len(decisions)
            total_confidence = 0.0
            
            for decision in decisions:
                # Count unanimous vs contested
                if not decision['dissenting_agents']:
                    metrics["unanimous_decisions"] += 1
                else:
                    metrics["contested_decisions"] += 1
                    
                # Track by agent
                agent = decision['agent']
                if agent not in metrics["by_agent"]:
                    metrics["by_agent"][agent] = {
                        "decisions": 0,
                        "average_confidence": 0.0,
                        "support_rate": 0.0
                    }
                
                metrics["by_agent"][agent]["decisions"] += 1
                metrics["by_agent"][agent]["average_confidence"] += decision['confidence']
                
                # Calculate support rate
                total_agents = (len(decision['supporting_agents']) +
                              len(decision['dissenting_agents']))
                if total_agents > 0:
                    support_rate = len(decision['supporting_agents']) / total_agents
                    metrics["by_agent"][agent]["support_rate"] += support_rate
                    
                total_confidence += decision['confidence']
                
            # Calculate averages
            metrics["average_confidence"] = total_confidence / len(decisions)
            
            # Finalize agent metrics
            for agent in metrics["by_agent"]:
                agent_decisions = metrics["by_agent"][agent]["decisions"]
                if agent_decisions > 0:
                    metrics["by_agent"][agent]["average_confidence"] /= agent_decisions
                    metrics["by_agent"][agent]["support_rate"] /= agent_decisions
                    
            # Calculate collaboration score (0-1)
            unanimous_ratio = metrics["unanimous_decisions"] / metrics["total_decisions"]
            avg_support = sum(a["support_rate"] for a in metrics["by_agent"].values()) / len(metrics["by_agent"])
            metrics["collaboration_score"] = (unanimous_ratio + avg_support) / 2
            
        except FileNotFoundError:
            logger.warning("No decision history found for consensus calculation")
            
        return metrics

# Global instance
collaboration_hub = CollaborationHub()

def record_interaction(*args, **kwargs):
    """Global function to record an interaction."""
    return collaboration_hub.record_interaction(*args, **kwargs)

def record_decision(*args, **kwargs):
    """Global function to record a decision."""
    return collaboration_hub.record_decision(*args, **kwargs) 