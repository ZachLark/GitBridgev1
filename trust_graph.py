#!/usr/bin/env python3
"""
GitBridge Trust Graph Core Engine
Phase: GBP23
Part: P23P1
Step: P23P1S1
Task: P23P1S1T1 - Core Directed Graph Engine

Core directed graph engine for tracking trust relationships between agents.
Supports trust score tracking, TTL decay, and comprehensive metadata.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P23P1 Schema]
"""

import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
import math
import threading
import os

logger = logging.getLogger(__name__)

@dataclass
class TrustEdge:
    """Represents a trust relationship between two agents."""
    from_agent: str
    to_agent: str
    trust_score: float = 0.0  # Range: -1.0 to 1.0
    confidence: float = 0.0   # Range: 0.0 to 1.0
    interaction_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_hours: int = 8760  # 1 year default
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if this trust edge has expired based on TTL."""
        age_hours = (datetime.now(timezone.utc) - self.updated_at).total_seconds() / 3600
        return age_hours > self.ttl_hours
        
    def decay_score(self, decay_rate: float = 0.1) -> None:
        """Apply time-based decay to trust score."""
        age_hours = (datetime.now(timezone.utc) - self.updated_at).total_seconds() / 3600
        if age_hours > 0:
            decay_factor = math.exp(-decay_rate * age_hours / 24)  # Daily decay
            self.trust_score *= decay_factor
            self.confidence *= decay_factor
            self.updated_at = datetime.now(timezone.utc)
            
    def update_score(self, new_score: float, confidence: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update trust score with new interaction data."""
        # Weighted average based on interaction count
        weight = 1.0 / (self.interaction_count + 1)
        self.trust_score = (self.trust_score * (1 - weight)) + (new_score * weight)
        self.confidence = (self.confidence * (1 - weight)) + (confidence * weight)
        
        # Clamp values to valid ranges
        self.trust_score = max(-1.0, min(1.0, self.trust_score))
        self.confidence = max(0.0, min(1.0, self.confidence))
        
        self.interaction_count += 1
        self.updated_at = datetime.now(timezone.utc)
        
        if metadata:
            self.metadata.update(metadata)

@dataclass
class TrustNode:
    """Represents an agent node in the trust graph."""
    agent_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_interactions: int = 0
    successful_interactions: int = 0
    failed_interactions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate for this agent."""
        if self.total_interactions == 0:
            return 0.0
        return self.successful_interactions / self.total_interactions
        
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate for this agent."""
        if self.total_interactions == 0:
            return 0.0
        return self.failed_interactions / self.total_interactions

class TrustGraph:
    """
    Core trust graph engine for tracking agent trust relationships.
    
    Phase: GBP23
    Part: P23P1
    Step: P23P1S1
    Task: P23P1S1T1 - Core Implementation
    
    Features:
    - Directed graph with weighted edges
    - Trust score tracking with TTL decay
    - Comprehensive metadata support
    - Thread-safe operations
    - Circular reference detection
    - Export/import capabilities
    """
    
    def __init__(self, storage_path: str = "trust_data", auto_save: bool = True, high_performance: bool = False):
        """
        Initialize trust graph.
        
        Args:
            storage_path: Directory for storing trust data
            auto_save: Whether to automatically save changes
            high_performance: Enable high-performance mode for bulk operations
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Graph data structures
        self.nodes: Dict[str, TrustNode] = {}
        self.edges: Dict[Tuple[str, str], TrustEdge] = {}
        self.adjacency_list: Dict[str, Set[str]] = {}
        
        # Configuration
        self.auto_save = auto_save
        self.high_performance = high_performance
        self.decay_rate = 0.1  # Daily decay rate
        self.max_trust_score = 1.0
        self.min_trust_score = -1.0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load existing data
        self._load_data()
        
        logger.info(f"[P23P1S1T1] TrustGraph initialized with {len(self.nodes)} nodes and {len(self.edges)} edges")
        
    def add_agent(self, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add an agent to the trust graph.
        
        Args:
            agent_id: Unique identifier for the agent
            metadata: Optional metadata for the agent
            
        Returns:
            bool: True if agent was added successfully
        """
        with self._lock:
            if agent_id in self.nodes:
                logger.warning(f"[P23P1S1T1] Agent {agent_id} already exists in trust graph")
                return False
                
            node = TrustNode(agent_id=agent_id, metadata=metadata or {})
            self.nodes[agent_id] = node
            self.adjacency_list[agent_id] = set()
            
            if self.auto_save:
                self._save_data()
                
            logger.info(f"[P23P1S1T1] Added agent {agent_id} to trust graph")
            return True
            
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the trust graph.
        
        Args:
            agent_id: ID of agent to remove
            
        Returns:
            bool: True if agent was removed successfully
        """
        with self._lock:
            if agent_id not in self.nodes:
                logger.warning(f"[P23P1S1T1] Agent {agent_id} not found in trust graph")
                return False
                
            # Remove all edges involving this agent
            edges_to_remove = []
            for (from_agent, to_agent) in self.edges.keys():
                if from_agent == agent_id or to_agent == agent_id:
                    edges_to_remove.append((from_agent, to_agent))
                    
            for edge_key in edges_to_remove:
                del self.edges[edge_key]
                
            # Remove from adjacency list
            if agent_id in self.adjacency_list:
                del self.adjacency_list[agent_id]
                
            # Remove from other agents' adjacency lists
            for adj_list in self.adjacency_list.values():
                adj_list.discard(agent_id)
                
            # Remove node
            del self.nodes[agent_id]
            
            if self.auto_save:
                self._save_data()
                
            logger.info(f"[P23P1S1T1] Removed agent {agent_id} from trust graph")
            return True
            
    def update_trust(
        self, 
        from_agent: str, 
        to_agent: str, 
        trust_score: float, 
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update trust score between two agents.
        
        Args:
            from_agent: Agent providing the trust assessment
            to_agent: Agent being assessed
            trust_score: Trust score (-1.0 to 1.0)
            confidence: Confidence in the assessment (0.0 to 1.0)
            metadata: Optional metadata about the interaction
            
        Returns:
            bool: True if trust was updated successfully
        """
        with self._lock:
            # Cache current time for performance
            current_time = datetime.now(timezone.utc)
            
            # Ensure both agents exist
            if from_agent not in self.nodes:
                self.add_agent(from_agent)
            if to_agent not in self.nodes:
                self.add_agent(to_agent)
                
            # Validate trust score
            trust_score = max(self.min_trust_score, min(self.max_trust_score, trust_score))
            confidence = max(0.0, min(1.0, confidence))
            
            # Create or update edge
            edge_key = (from_agent, to_agent)
            if edge_key in self.edges:
                if self.high_performance:
                    # Fast update without complex calculations
                    edge = self.edges[edge_key]
                    edge.trust_score = trust_score
                    edge.confidence = confidence
                    edge.interaction_count += 1
                    edge.updated_at = current_time
                    if metadata:
                        edge.metadata.update(metadata)
                else:
                    self.edges[edge_key].update_score(trust_score, confidence, metadata)
            else:
                edge = TrustEdge(
                    from_agent=from_agent,
                    to_agent=to_agent,
                    trust_score=trust_score,
                    confidence=confidence,
                    interaction_count=1,
                    metadata=metadata or {}
                )
                edge.updated_at = current_time  # Use cached time
                self.edges[edge_key] = edge
                self.adjacency_list[from_agent].add(to_agent)
                
            # Update node statistics
            self.nodes[to_agent].total_interactions += 1
            if not self.high_performance:
                if trust_score > 0:
                    self.nodes[to_agent].successful_interactions += 1
                elif trust_score < 0:
                    self.nodes[to_agent].failed_interactions += 1
            self.nodes[to_agent].updated_at = current_time
            
            if self.auto_save:
                self._save_data()
                
            if not self.high_performance:
                logger.debug(f"[P23P1S1T1] Updated trust: {from_agent} -> {to_agent} = {trust_score:.3f}")
            return True
            
    def get_trust_score(self, from_agent: str, to_agent: str) -> Optional[float]:
        """
        Get trust score between two agents.
        
        Args:
            from_agent: Agent providing the assessment
            to_agent: Agent being assessed
            
        Returns:
            float: Trust score if edge exists, None otherwise
        """
        with self._lock:
            edge_key = (from_agent, to_agent)
            if edge_key in self.edges:
                edge = self.edges[edge_key]
                if edge.is_expired():
                    logger.debug(f"[P23P1S1T1] Trust edge {from_agent} -> {to_agent} has expired")
                    return None
                return edge.trust_score
            return None
            
    def get_trust_confidence(self, from_agent: str, to_agent: str) -> Optional[float]:
        """
        Get confidence in trust score between two agents.
        
        Args:
            from_agent: Agent providing the assessment
            to_agent: Agent being assessed
            
        Returns:
            float: Confidence score if edge exists, None otherwise
        """
        with self._lock:
            edge_key = (from_agent, to_agent)
            if edge_key in self.edges:
                edge = self.edges[edge_key]
                if edge.is_expired():
                    return None
                return edge.confidence
            return None
            
    def get_agent_trust_summary(self, agent_id: str) -> Dict[str, Any]:
        """
        Get comprehensive trust summary for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dict containing trust summary
        """
        with self._lock:
            if agent_id not in self.nodes:
                return {}
                
            node = self.nodes[agent_id]
            
            # Calculate incoming trust scores
            incoming_trust = []
            outgoing_trust = []
            
            for (from_agent, to_agent), edge in self.edges.items():
                if edge.is_expired():
                    continue
                    
                if to_agent == agent_id:
                    incoming_trust.append({
                        'from_agent': from_agent,
                        'trust_score': edge.trust_score,
                        'confidence': edge.confidence,
                        'interaction_count': edge.interaction_count
                    })
                elif from_agent == agent_id:
                    outgoing_trust.append({
                        'to_agent': to_agent,
                        'trust_score': edge.trust_score,
                        'confidence': edge.confidence,
                        'interaction_count': edge.interaction_count
                    })
                    
            # Calculate average trust scores
            avg_incoming_trust = sum(t['trust_score'] for t in incoming_trust) / len(incoming_trust) if incoming_trust else 0.0
            avg_outgoing_trust = sum(t['trust_score'] for t in outgoing_trust) / len(outgoing_trust) if outgoing_trust else 0.0
            
            return {
                'agent_id': agent_id,
                'total_interactions': node.total_interactions,
                'successful_interactions': node.successful_interactions,
                'failed_interactions': node.failed_interactions,
                'success_rate': node.success_rate,
                'failure_rate': node.failure_rate,
                'avg_incoming_trust': avg_incoming_trust,
                'avg_outgoing_trust': avg_outgoing_trust,
                'incoming_trust_count': len(incoming_trust),
                'outgoing_trust_count': len(outgoing_trust),
                'created_at': node.created_at.isoformat(),
                'updated_at': node.updated_at.isoformat(),
                'metadata': node.metadata
            }
            
    def apply_decay(self) -> int:
        """
        Apply time-based decay to all trust edges.
        
        Returns:
            int: Number of edges that were decayed
        """
        with self._lock:
            decayed_count = 0
            for edge in self.edges.values():
                if not edge.is_expired():
                    edge.decay_score(self.decay_rate)
                    decayed_count += 1
                    
            if self.auto_save and decayed_count > 0:
                self._save_data()
                
            logger.info(f"[P23P1S1T1] Applied decay to {decayed_count} trust edges")
            return decayed_count
            
    def cleanup_expired_edges(self) -> int:
        """
        Remove expired trust edges.
        
        Returns:
            int: Number of edges removed
        """
        with self._lock:
            expired_edges = []
            for edge_key, edge in self.edges.items():
                if edge.is_expired():
                    expired_edges.append(edge_key)
                    
            for edge_key in expired_edges:
                from_agent, to_agent = edge_key
                del self.edges[edge_key]
                self.adjacency_list[from_agent].discard(to_agent)
                
            if self.auto_save and expired_edges:
                self._save_data()
                
            logger.info(f"[P23P1S1T1] Removed {len(expired_edges)} expired trust edges")
            return len(expired_edges)
            
    def detect_circular_references(self) -> List[List[str]]:
        """
        Detect circular references in the trust graph.
        
        Returns:
            List of circular reference paths
        """
        with self._lock:
            visited = set()
            rec_stack = set()
            circles = []
            
            def dfs(node: str, path: List[str]) -> None:
                if node in rec_stack:
                    # Found a circle
                    circle_start = path.index(node)
                    circles.append(path[circle_start:] + [node])
                    return
                    
                if node in visited:
                    return
                    
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                
                for neighbor in self.adjacency_list.get(node, set()):
                    dfs(neighbor, path.copy())
                    
                rec_stack.remove(node)
                
            for node in self.nodes:
                if node not in visited:
                    dfs(node, [])
                    
            return circles
            
    def get_all_agents(self) -> List[str]:
        """
        Get list of all agent IDs in the graph.
        
        Returns:
            List of agent IDs
        """
        with self._lock:
            return list(self.nodes.keys())
            
    def get_all_edges(self) -> List[TrustEdge]:
        """
        Get list of all trust edges in the graph.
        
        Returns:
            List of TrustEdge objects
        """
        with self._lock:
            return [edge for edge in self.edges.values() if not edge.is_expired()]
            
    def get_edge(self, from_agent: str, to_agent: str) -> Optional[TrustEdge]:
        """
        Get trust edge between two agents.
        
        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID
            
        Returns:
            TrustEdge if exists and not expired, None otherwise
        """
        with self._lock:
            edge_key = (from_agent, to_agent)
            if edge_key in self.edges:
                edge = self.edges[edge_key]
                if not edge.is_expired():
                    return edge
            return None
            
    def get_neighbors(self, agent_id: str) -> List[str]:
        """
        Get list of neighbors for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of neighbor agent IDs
        """
        with self._lock:
            if agent_id not in self.adjacency_list:
                return []
            return list(self.adjacency_list[agent_id])

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the trust graph.
        
        Returns:
            Dict containing graph statistics
        """
        with self._lock:
            total_edges = len(self.edges)
            active_edges = sum(1 for edge in self.edges.values() if not edge.is_expired())
            
            trust_scores = [edge.trust_score for edge in self.edges.values() if not edge.is_expired()]
            avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
            
            confidence_scores = [edge.confidence for edge in self.edges.values() if not edge.is_expired()]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            return {
                'total_agents': len(self.nodes),
                'total_edges': total_edges,
                'active_edges': active_edges,
                'expired_edges': total_edges - active_edges,
                'avg_trust_score': avg_trust,
                'avg_confidence': avg_confidence,
                'circular_references': len(self.detect_circular_references()),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
    def export_graph(self, format: str = "json") -> str:
        """
        Export the trust graph to various formats.
        
        Args:
            format: Export format ("json", "csv", "dot")
            
        Returns:
            str: Exported graph data
        """
        with self._lock:
            if format == "json":
                data = {
                    'nodes': [asdict(node) for node in self.nodes.values()],
                    'edges': [asdict(edge) for edge in self.edges.values()],
                    'metadata': {
                        'exported_at': datetime.now(timezone.utc).isoformat(),
                        'version': '1.0.0'
                    }
                }
                return json.dumps(data, indent=2, default=str)
            elif format == "csv":
                lines = ["from_agent,to_agent,trust_score,confidence,interaction_count,created_at,updated_at"]
                for edge in self.edges.values():
                    lines.append(f"{edge.from_agent},{edge.to_agent},{edge.trust_score},{edge.confidence},{edge.interaction_count},{edge.created_at},{edge.updated_at}")
                lines.append("")  # Add empty line at end
                return "\n".join(lines)
            elif format == "dot":
                lines = ["digraph TrustGraph {"]
                for edge in self.edges.values():
                    if not edge.is_expired():
                        color = "green" if edge.trust_score > 0 else "red" if edge.trust_score < 0 else "gray"
                        lines.append(f'  "{edge.from_agent}" -> "{edge.to_agent}" [label="{edge.trust_score:.2f}", color={color}];')
                lines.append("}")
                return "\n".join(lines)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
    def _save_data(self) -> None:
        """Save trust graph data to disk."""
        try:
            data = {
                'nodes': [asdict(node) for node in self.nodes.values()],
                'edges': [asdict(edge) for edge in self.edges.values()],
                'metadata': {
                    'saved_at': datetime.now(timezone.utc).isoformat(),
                    'version': '1.0.0'
                }
            }
            
            with open(self.storage_path / "trust_graph.json", 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            logger.debug(f"[P23P1S1T1] Saved trust graph data to {self.storage_path}")
            
        except Exception as e:
            logger.error(f"[P23P1S1T1] Failed to save trust graph data: {e}")
            
    def _load_data(self) -> None:
        """Load trust graph data from disk."""
        try:
            data_file = self.storage_path / "trust_graph.json"
            if not data_file.exists():
                logger.info(f"[P23P1S1T1] No existing trust graph data found at {data_file}")
                return
                
            with open(data_file, 'r') as f:
                data = json.load(f)
                
            # Load nodes
            for node_data in data.get('nodes', []):
                node = TrustNode(
                    agent_id=node_data['agent_id'],
                    created_at=datetime.fromisoformat(node_data['created_at']),
                    updated_at=datetime.fromisoformat(node_data['updated_at']),
                    total_interactions=node_data['total_interactions'],
                    successful_interactions=node_data['successful_interactions'],
                    failed_interactions=node_data['failed_interactions'],
                    metadata=node_data.get('metadata', {})
                )
                self.nodes[node.agent_id] = node
                self.adjacency_list[node.agent_id] = set()
                
            # Load edges
            for edge_data in data.get('edges', []):
                edge = TrustEdge(
                    from_agent=edge_data['from_agent'],
                    to_agent=edge_data['to_agent'],
                    trust_score=edge_data['trust_score'],
                    confidence=edge_data['confidence'],
                    interaction_count=edge_data['interaction_count'],
                    created_at=datetime.fromisoformat(edge_data['created_at']),
                    updated_at=datetime.fromisoformat(edge_data['updated_at']),
                    ttl_hours=edge_data.get('ttl_hours', 8760),
                    metadata=edge_data.get('metadata', {})
                )
                edge_key = (edge.from_agent, edge.to_agent)
                self.edges[edge_key] = edge
                self.adjacency_list[edge.from_agent].add(edge.to_agent)
                
            logger.info(f"[P23P1S1T1] Loaded trust graph data: {len(self.nodes)} nodes, {len(self.edges)} edges")
            
        except Exception as e:
            logger.error(f"[P23P1S1T1] Failed to load trust graph data: {e}")

    def save_to_file(self, file_path: str) -> bool:
        """
        Save trust graph to a specific file.
        
        Args:
            file_path: Path to save the graph data
            
        Returns:
            bool: True if save was successful
        """
        try:
            data = {
                'nodes': [asdict(node) for node in self.nodes.values()],
                'edges': [asdict(edge) for edge in self.edges.values()],
                'metadata': {
                    'saved_at': datetime.now(timezone.utc).isoformat(),
                    'version': '1.0.0'
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            logger.info(f"[P23P1S1T1] Saved trust graph to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"[P23P1S1T1] Failed to save trust graph to {file_path}: {e}")
            return False
            
    def load_from_file(self, file_path: str) -> bool:
        """
        Load trust graph from a specific file.
        
        Args:
            file_path: Path to load the graph data from
            
        Returns:
            bool: True if load was successful
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"[P23P1S1T1] Trust graph file not found: {file_path}")
                return False
                
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Clear existing data
            self.nodes.clear()
            self.edges.clear()
            self.adjacency_list.clear()
            
            # Load nodes
            for node_data in data.get('nodes', []):
                node = TrustNode(
                    agent_id=node_data['agent_id'],
                    created_at=datetime.fromisoformat(node_data['created_at']),
                    updated_at=datetime.fromisoformat(node_data['updated_at']),
                    total_interactions=node_data['total_interactions'],
                    successful_interactions=node_data['successful_interactions'],
                    failed_interactions=node_data['failed_interactions'],
                    metadata=node_data.get('metadata', {})
                )
                self.nodes[node.agent_id] = node
                self.adjacency_list[node.agent_id] = set()
                
            # Load edges
            for edge_data in data.get('edges', []):
                edge = TrustEdge(
                    from_agent=edge_data['from_agent'],
                    to_agent=edge_data['to_agent'],
                    trust_score=edge_data['trust_score'],
                    confidence=edge_data['confidence'],
                    interaction_count=edge_data['interaction_count'],
                    created_at=datetime.fromisoformat(edge_data['created_at']),
                    updated_at=datetime.fromisoformat(edge_data['updated_at']),
                    ttl_hours=edge_data.get('ttl_hours', 8760),
                    metadata=edge_data.get('metadata', {})
                )
                edge_key = (edge.from_agent, edge.to_agent)
                self.edges[edge_key] = edge
                self.adjacency_list[edge.from_agent].add(edge.to_agent)
                
            logger.info(f"[P23P1S1T1] Loaded trust graph from {file_path}: {len(self.nodes)} nodes, {len(self.edges)} edges")
            return True
            
        except Exception as e:
            logger.error(f"[P23P1S1T1] Failed to load trust graph from {file_path}: {e}")
            return False

    def update_trust_batch(
        self, 
        trust_updates: List[Tuple[str, str, float, float, Optional[Dict[str, Any]]]],
        high_performance: bool = False
    ) -> int:
        """
        Update multiple trust relationships in a single batch operation.
        
        Args:
            trust_updates: List of (from_agent, to_agent, trust_score, confidence, metadata) tuples
            high_performance: Skip validation and logging for maximum speed
            
        Returns:
            int: Number of successful updates
        """
        if not trust_updates:
            return 0
            
        with self._lock:
            successful_updates = 0
            
            # Pre-create agents if needed (batch operation)
            if not high_performance:
                agents_to_create = set()
                for from_agent, to_agent, _, _, _ in trust_updates:
                    if from_agent not in self.nodes:
                        agents_to_create.add(from_agent)
                    if to_agent not in self.nodes:
                        agents_to_create.add(to_agent)
                        
                for agent_id in agents_to_create:
                    node = TrustNode(agent_id=agent_id, metadata={})
                    self.nodes[agent_id] = node
                    self.adjacency_list[agent_id] = set()
            
            # Process all updates
            for from_agent, to_agent, trust_score, confidence, metadata in trust_updates:
                try:
                    # Create agents if needed (high-performance mode)
                    if high_performance:
                        if from_agent not in self.nodes:
                            node = TrustNode(agent_id=from_agent, metadata={})
                            self.nodes[from_agent] = node
                            self.adjacency_list[from_agent] = set()
                        if to_agent not in self.nodes:
                            node = TrustNode(agent_id=to_agent, metadata={})
                            self.nodes[to_agent] = node
                            self.adjacency_list[to_agent] = set()
                    
                    # Validate trust score (skip in high-performance mode)
                    if not high_performance:
                        trust_score = max(self.min_trust_score, min(self.max_trust_score, trust_score))
                        confidence = max(0.0, min(1.0, confidence))
                    else:
                        # Quick validation
                        trust_score = max(-1.0, min(1.0, trust_score))
                        confidence = max(0.0, min(1.0, confidence))
                    
                    # Create or update edge
                    edge_key = (from_agent, to_agent)
                    if edge_key in self.edges:
                        if high_performance:
                            # Fast update without complex calculations
                            edge = self.edges[edge_key]
                            edge.trust_score = trust_score
                            edge.confidence = confidence
                            edge.interaction_count += 1
                            edge.updated_at = datetime.now(timezone.utc)
                            if metadata:
                                edge.metadata.update(metadata)
                        else:
                            self.edges[edge_key].update_score(trust_score, confidence, metadata)
                    else:
                        edge = TrustEdge(
                            from_agent=from_agent,
                            to_agent=to_agent,
                            trust_score=trust_score,
                            confidence=confidence,
                            interaction_count=1,
                            metadata=metadata or {}
                        )
                        self.edges[edge_key] = edge
                        self.adjacency_list[from_agent].add(to_agent)
                    
                    # Update node statistics (simplified in high-performance mode)
                    if not high_performance:
                        self.nodes[to_agent].total_interactions += 1
                        if trust_score > 0:
                            self.nodes[to_agent].successful_interactions += 1
                        elif trust_score < 0:
                            self.nodes[to_agent].failed_interactions += 1
                        self.nodes[to_agent].updated_at = datetime.now(timezone.utc)
                    else:
                        # Fast node update
                        self.nodes[to_agent].total_interactions += 1
                        self.nodes[to_agent].updated_at = datetime.now(timezone.utc)
                    
                    successful_updates += 1
                    
                except Exception as e:
                    if not high_performance:
                        logger.error(f"[P23P1S1T1] Failed to update trust {from_agent} -> {to_agent}: {e}")
            
            # Batch save (only once for all updates)
            if self.auto_save and successful_updates > 0:
                self._save_data()
            
            if not high_performance:
                logger.info(f"[P23P1S1T1] Batch updated {successful_updates} trust relationships")
            
            return successful_updates

    def set_high_performance_mode(self, enabled: bool) -> None:
        """
        Enable or disable high-performance mode.
        
        Args:
            enabled: Whether to enable high-performance mode
        """
        self.high_performance = enabled
        logger.info(f"[P23P1S1T1] High-performance mode {'enabled' if enabled else 'disabled'}")
        
    def set_auto_save(self, enabled: bool) -> None:
        """
        Enable or disable auto-save functionality.
        
        Args:
            enabled: Whether to enable auto-save
        """
        self.auto_save = enabled
        logger.info(f"[P23P1S1T1] Auto-save {'enabled' if enabled else 'disabled'}")
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get current performance configuration and statistics.
        
        Returns:
            Dict containing performance information
        """
        return {
            'high_performance_mode': self.high_performance,
            'auto_save_enabled': self.auto_save,
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'decay_rate': self.decay_rate,
            'max_trust_score': self.max_trust_score,
            'min_trust_score': self.min_trust_score
        }

def main():
    """CLI interface for trust graph operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitBridge Trust Graph CLI")
    parser.add_argument("--storage", default="trust_data", help="Storage directory")
    parser.add_argument("--command", required=True, choices=["add", "update", "get", "stats", "export", "decay", "cleanup"])
    parser.add_argument("--from-agent", help="Source agent ID")
    parser.add_argument("--to-agent", help="Target agent ID")
    parser.add_argument("--trust-score", type=float, help="Trust score (-1.0 to 1.0)")
    parser.add_argument("--confidence", type=float, default=1.0, help="Confidence (0.0 to 1.0)")
    parser.add_argument("--format", default="json", choices=["json", "csv", "dot"], help="Export format")
    
    args = parser.parse_args()
    
    graph = TrustGraph(storage_path=args.storage)
    
    if args.command == "add":
        if not args.from_agent:
            print("Error: --from-agent required for add command")
            return
        success = graph.add_agent(args.from_agent)
        print(f"Agent added: {success}")
        
    elif args.command == "update":
        if not all([args.from_agent, args.to_agent, args.trust_score is not None]):
            print("Error: --from-agent, --to-agent, and --trust-score required for update command")
            return
        success = graph.update_trust(args.from_agent, args.to_agent, args.trust_score, args.confidence)
        print(f"Trust updated: {success}")
        
    elif args.command == "get":
        if not all([args.from_agent, args.to_agent]):
            print("Error: --from-agent and --to-agent required for get command")
            return
        score = graph.get_trust_score(args.from_agent, args.to_agent)
        confidence = graph.get_trust_confidence(args.from_agent, args.to_agent)
        print(f"Trust score: {score}")
        print(f"Confidence: {confidence}")
        
    elif args.command == "stats":
        stats = graph.get_statistics()
        print(json.dumps(stats, indent=2))
        
    elif args.command == "export":
        data = graph.export_graph(args.format)
        print(data)
        
    elif args.command == "decay":
        count = graph.apply_decay()
        print(f"Decayed {count} edges")
        
    elif args.command == "cleanup":
        count = graph.cleanup_expired_edges()
        print(f"Removed {count} expired edges")

if __name__ == "__main__":
    main() 