#!/usr/bin/env python3
"""
GitBridge Trust Metrics
Phase: GBP23
Part: P23P5
Step: P23P5S1
Task: P23P5S1T1 - Trust Analytics and Metrics

Trust metrics for calculating trust analytics, metrics, and trustworthiness
assessment across the trust network.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P23P5 Schema]
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
import math
import statistics
from collections import defaultdict, Counter
import threading

from trust_graph import TrustGraph, TrustEdge
from trust_analyzer import TrustAnalyzer, TrustAnalysis
from behavior_model import BehaviorModel, AgentBehavior

logger = logging.getLogger(__name__)

@dataclass
class TrustMetrics:
    """Comprehensive trust metrics for an agent or network."""
    agent_id: Optional[str] = None
    total_trust_score: float = 0.0
    average_trust_score: float = 0.0
    trust_consistency: float = 0.0
    trust_volatility: float = 0.0
    trust_centrality: float = 0.0
    trust_reciprocity: float = 0.0
    trust_clustering: float = 0.0
    trust_reachability: float = 0.0
    trust_influence: float = 0.0
    trust_reliability: float = 0.0
    trust_trend: float = 0.0
    confidence_score: float = 0.0
    risk_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NetworkMetrics:
    """Network-wide trust metrics."""
    total_agents: int = 0
    total_edges: int = 0
    average_trust_score: float = 0.0
    trust_density: float = 0.0
    trust_clustering_coefficient: float = 0.0
    trust_centralization: float = 0.0
    trust_fragmentation: float = 0.0
    trust_stability: float = 0.0
    trust_efficiency: float = 0.0
    trust_resilience: float = 0.0
    high_trust_agents: int = 0
    low_trust_agents: int = 0
    trust_communities: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TrustTrend:
    """Trust trend analysis over time."""
    agent_id: str
    time_period: str  # "daily", "weekly", "monthly"
    start_date: datetime
    end_date: datetime
    trust_scores: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    trend_direction: str = "stable"  # "increasing", "decreasing", "stable"
    trend_strength: float = 0.0
    volatility: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class TrustMetricsCalculator:
    """
    Trust metrics calculator for comprehensive trust analytics.
    
    Phase: GBP23
    Part: P23P5
    Step: P23P5S1
    Task: P23P5S1T1 - Core Implementation
    
    Features:
    - Individual agent trust metrics
    - Network-wide trust analytics
    - Trust trend analysis
    - Trust risk assessment
    - Trust influence calculation
    """
    
    def __init__(
        self, 
        trust_graph: TrustGraph, 
        analyzer: Optional[TrustAnalyzer] = None,
        behavior_model: Optional[BehaviorModel] = None
    ):
        """
        Initialize trust metrics calculator.
        
        Args:
            trust_graph: Trust graph to analyze
            analyzer: Optional trust analyzer for path analysis
            behavior_model: Optional behavior model for behavioral metrics
        """
        self.trust_graph = trust_graph
        self.analyzer = analyzer or TrustAnalyzer(trust_graph)
        self.behavior_model = behavior_model
        
        # Metrics cache
        self._metrics_cache: Dict[str, TrustMetrics] = {}
        self._network_cache: Optional[NetworkMetrics] = None
        self._cache_lock = threading.RLock()
        
        # Configuration
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.min_confidence_threshold = 0.1
        
        logger.info(f"[P23P5S1T1] TrustMetricsCalculator initialized")
        
    def calculate_agent_metrics(self, agent_id: str, include_behavior: bool = True) -> TrustMetrics:
        """
        Calculate comprehensive trust metrics for an agent.
        
        Args:
            agent_id: ID of the agent to analyze
            include_behavior: Whether to include behavioral metrics
            
        Returns:
            TrustMetrics: Comprehensive trust metrics
        """
        # Check cache first
        cache_key = f"agent_{agent_id}_{include_behavior}"
        with self._cache_lock:
            if cache_key in self._metrics_cache:
                cached = self._metrics_cache[cache_key]
                # Check if cache is still valid
                if (datetime.now(timezone.utc) - cached.metadata.get("calculated_at", datetime.min.replace(tzinfo=timezone.utc))).total_seconds() < self.cache_ttl:
                    return cached
                    
        # Calculate metrics
        metrics = TrustMetrics(agent_id=agent_id)
        
        # Basic trust scores
        incoming_edges = []
        outgoing_edges = []
        
        for edge in self.trust_graph.get_all_edges():
            if edge.to_agent == agent_id:
                incoming_edges.append(edge)
            if edge.from_agent == agent_id:
                outgoing_edges.append(edge)
                
        # Total and average trust scores
        if incoming_edges:
            metrics.total_trust_score = sum(edge.trust_score for edge in incoming_edges)
            metrics.average_trust_score = metrics.total_trust_score / len(incoming_edges)
            
        # Trust consistency (standard deviation of incoming trust scores)
        if len(incoming_edges) > 1:
            trust_scores = [edge.trust_score for edge in incoming_edges]
            metrics.trust_consistency = 1.0 - min(statistics.stdev(trust_scores), 1.0)
            
        # Trust volatility (based on confidence scores)
        if incoming_edges:
            confidence_scores = [edge.confidence for edge in incoming_edges]
            metrics.trust_volatility = 1.0 - (sum(confidence_scores) / len(confidence_scores))
            
        # Trust centrality (degree centrality)
        total_agents = len(self.trust_graph.get_all_agents())
        if total_agents > 1:
            metrics.trust_centrality = (len(incoming_edges) + len(outgoing_edges)) / (total_agents - 1)
            
        # Trust reciprocity
        if incoming_edges and outgoing_edges:
            reciprocal_trust = 0
            reciprocal_count = 0
            
            for in_edge in incoming_edges:
                for out_edge in outgoing_edges:
                    if in_edge.from_agent == out_edge.to_agent:
                        reciprocal_count += 1
                        # Calculate reciprocity as similarity of trust scores
                        trust_diff = abs(in_edge.trust_score - out_edge.trust_score)
                        reciprocal_trust += 1.0 - trust_diff
                        
            if reciprocal_count > 0:
                metrics.trust_reciprocity = reciprocal_trust / reciprocal_count
                
        # Trust clustering (local clustering coefficient)
        metrics.trust_clustering = self._calculate_clustering_coefficient(agent_id)
        
        # Trust reachability (how many agents can be reached through trust paths)
        metrics.trust_reachability = self._calculate_reachability(agent_id)
        
        # Trust influence (based on outgoing trust and centrality)
        if outgoing_edges:
            avg_outgoing_trust = sum(edge.trust_score for edge in outgoing_edges) / len(outgoing_edges)
            metrics.trust_influence = metrics.trust_centrality * avg_outgoing_trust
            
        # Trust reliability (combination of consistency and confidence)
        if incoming_edges:
            avg_confidence = sum(edge.confidence for edge in incoming_edges) / len(incoming_edges)
            metrics.trust_reliability = (metrics.trust_consistency + avg_confidence) / 2
            
        # Trust trend (simplified - would need historical data for full implementation)
        metrics.trust_trend = 0.0  # Placeholder for trend calculation
        
        # Confidence score (overall confidence in metrics)
        confidence_factors = [
            metrics.trust_consistency,
            metrics.trust_reliability,
            1.0 - metrics.trust_volatility
        ]
        metrics.confidence_score = sum(confidence_factors) / len(confidence_factors)
        
        # Risk score (inverse of trust reliability)
        metrics.risk_score = 1.0 - metrics.trust_reliability
        
        # Include behavioral metrics if available
        if include_behavior and self.behavior_model:
            behavior_metrics = self._calculate_behavioral_metrics(agent_id)
            metrics.metadata.update(behavior_metrics)
            
        # Add calculation timestamp
        metrics.metadata["calculated_at"] = datetime.now(timezone.utc)
        
        # Cache results
        with self._cache_lock:
            self._metrics_cache[cache_key] = metrics
            
        logger.info(f"[P23P5S1T1] Calculated trust metrics for agent {agent_id}")
        return metrics
        
    def _calculate_clustering_coefficient(self, agent_id: str) -> float:
        """Calculate local clustering coefficient for an agent."""
        neighbors = self.trust_graph.get_neighbors(agent_id)
        if len(neighbors) < 2:
            return 0.0
            
        # Count triangles (trust relationships between neighbors)
        triangles = 0
        possible_triangles = len(neighbors) * (len(neighbors) - 1) / 2
        
        for i, neighbor1 in enumerate(neighbors):
            for neighbor2 in neighbors[i+1:]:
                # Check if there's a trust edge between neighbors
                edge1 = self.trust_graph.get_edge(neighbor1, neighbor2)
                edge2 = self.trust_graph.get_edge(neighbor2, neighbor1)
                if edge1 or edge2:
                    triangles += 1
                    
        return triangles / possible_triangles if possible_triangles > 0 else 0.0
        
    def _calculate_reachability(self, agent_id: str) -> float:
        """Calculate trust reachability for an agent."""
        all_agents = set(self.trust_graph.get_all_agents())
        reachable_agents = set()
        
        # Use BFS to find reachable agents
        queue = [agent_id]
        visited = {agent_id}
        
        while queue:
            current = queue.pop(0)
            reachable_agents.add(current)
            
            neighbors = self.trust_graph.get_neighbors(current)
            for neighbor in neighbors:
                if neighbor not in visited:
                    edge = self.trust_graph.get_edge(current, neighbor)
                    if edge and edge.trust_score >= 0.3:  # Minimum trust threshold
                        visited.add(neighbor)
                        queue.append(neighbor)
                        
        return len(reachable_agents) / len(all_agents) if all_agents else 0.0
        
    def _calculate_behavioral_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Calculate behavioral metrics for an agent."""
        if not self.behavior_model:
            return {}
            
        behavior = self.behavior_model.get_agent_behavior(agent_id)
        if not behavior:
            return {}
            
        return {
            "behavioral_reliability": behavior.reliability_score,
            "collaboration_tendency": behavior.collaboration_score,
            "adaptability_score": behavior.adaptability_score,
            "success_rate": behavior.success_rate,
            "total_interactions": behavior.total_interactions,
            "specializations": list(behavior.specializations)
        }
        
    def calculate_network_metrics(self) -> NetworkMetrics:
        """
        Calculate network-wide trust metrics.
        
        Returns:
            NetworkMetrics: Network-wide trust metrics
        """
        # Check cache
        with self._cache_lock:
            if self._network_cache:
                cached = self._network_cache
                if (datetime.now(timezone.utc) - cached.metadata.get("calculated_at", datetime.min.replace(tzinfo=timezone.utc))).total_seconds() < self.cache_ttl:
                    return cached
                    
        # Calculate network metrics
        metrics = NetworkMetrics()
        
        agents = self.trust_graph.get_all_agents()
        edges = self.trust_graph.get_all_edges()
        
        metrics.total_agents = len(agents)
        metrics.total_edges = len(edges)
        
        # Average trust score
        if edges:
            metrics.average_trust_score = sum(edge.trust_score for edge in edges) / len(edges)
            
        # Trust density
        if metrics.total_agents > 1:
            max_possible_edges = metrics.total_agents * (metrics.total_agents - 1)
            metrics.trust_density = metrics.total_edges / max_possible_edges
            
        # Trust clustering coefficient (global)
        metrics.trust_clustering_coefficient = self._calculate_global_clustering_coefficient()
        
        # Trust centralization
        metrics.trust_centralization = self._calculate_centralization()
        
        # Trust fragmentation
        metrics.trust_fragmentation = self._calculate_fragmentation()
        
        # Trust stability (based on confidence scores)
        if edges:
            avg_confidence = sum(edge.confidence for edge in edges) / len(edges)
            metrics.trust_stability = avg_confidence
            
        # Trust efficiency (average path length)
        metrics.trust_efficiency = self._calculate_efficiency()
        
        # Trust resilience (ability to maintain connectivity)
        metrics.trust_resilience = self._calculate_resilience()
        
        # High and low trust agents
        agent_metrics = {}
        for agent in agents:
            agent_metrics[agent] = self.calculate_agent_metrics(agent, include_behavior=False)
            
        high_trust_threshold = 0.7
        low_trust_threshold = 0.3
        
        metrics.high_trust_agents = sum(1 for m in agent_metrics.values() if m.average_trust_score >= high_trust_threshold)
        metrics.low_trust_agents = sum(1 for m in agent_metrics.values() if m.average_trust_score <= low_trust_threshold)
        
        # Trust communities
        clusters = self.analyzer.find_trust_clusters()
        metrics.trust_communities = len(clusters)
        
        # Add calculation timestamp
        metrics.metadata["calculated_at"] = datetime.now(timezone.utc)
        
        # Cache results
        with self._cache_lock:
            self._network_cache = metrics
            
        logger.info(f"[P23P5S1T1] Calculated network trust metrics")
        return metrics
        
    def _calculate_global_clustering_coefficient(self) -> float:
        """Calculate global clustering coefficient."""
        agents = self.trust_graph.get_all_agents()
        total_clustering = 0.0
        valid_agents = 0
        
        for agent in agents:
            clustering = self._calculate_clustering_coefficient(agent)
            if clustering > 0:
                total_clustering += clustering
                valid_agents += 1
                
        return total_clustering / valid_agents if valid_agents > 0 else 0.0
        
    def _calculate_centralization(self) -> float:
        """Calculate network centralization."""
        agents = self.trust_graph.get_all_agents()
        if len(agents) < 2:
            return 0.0
            
        # Calculate centrality for each agent
        centralities = []
        for agent in agents:
            incoming_edges = []
            outgoing_edges = []
            
            for edge in self.trust_graph.get_all_edges():
                if edge.to_agent == agent:
                    incoming_edges.append(edge)
                if edge.from_agent == agent:
                    outgoing_edges.append(edge)
                    
            centrality = (len(incoming_edges) + len(outgoing_edges)) / (len(agents) - 1)
            centralities.append(centrality)
            
        # Calculate centralization as variance of centralities
        if centralities:
            mean_centrality = sum(centralities) / len(centralities)
            variance = sum((c - mean_centrality) ** 2 for c in centralities) / len(centralities)
            return min(variance, 1.0)  # Normalize to 0-1 range
            
        return 0.0
        
    def _calculate_fragmentation(self) -> float:
        """Calculate network fragmentation."""
        clusters = self.analyzer.find_trust_clusters()
        total_agents = len(self.trust_graph.get_all_agents())
        
        if total_agents == 0:
            return 0.0
            
        # Fragmentation is higher when there are more small clusters
        if not clusters:
            return 1.0  # Completely fragmented
            
        # Calculate fragmentation based on cluster size distribution
        cluster_sizes = [len(cluster) for cluster in clusters]
        avg_cluster_size = sum(cluster_sizes) / len(cluster_sizes)
        
        # Normalize fragmentation (0 = no fragmentation, 1 = complete fragmentation)
        fragmentation = 1.0 - (avg_cluster_size / total_agents)
        return max(0.0, min(1.0, fragmentation))
        
    def _calculate_efficiency(self) -> float:
        """Calculate network efficiency (inverse of average path length)."""
        agents = list(self.trust_graph.get_all_agents())
        if len(agents) < 2:
            return 0.0
            
        total_path_length = 0
        path_count = 0
        
        # Sample a subset of agent pairs for efficiency
        sample_size = min(50, len(agents) * (len(agents) - 1) // 2)
        pairs_checked = 0
        
        for i, agent1 in enumerate(agents):
            for agent2 in agents[i+1:]:
                if pairs_checked >= sample_size:
                    break
                    
                analysis = self.analyzer.analyze_trust_paths(agent1, agent2, max_paths=1)
                if analysis.best_path:
                    total_path_length += analysis.best_path.path_length
                    path_count += 1
                    
                pairs_checked += 1
                
        if path_count > 0:
            avg_path_length = total_path_length / path_count
            # Efficiency is inverse of path length, normalized to 0-1
            return 1.0 / (1.0 + avg_path_length)
            
        return 0.0
        
    def _calculate_resilience(self) -> float:
        """Calculate network resilience."""
        # Simplified resilience calculation based on connectivity
        agents = list(self.trust_graph.get_all_agents())
        if len(agents) < 2:
            return 0.0
            
        # Calculate resilience as the fraction of agents that remain connected
        # when a random agent is removed
        resilience_scores = []
        
        for _ in range(min(10, len(agents))):  # Sample for efficiency
            # Simulate removing a random agent
            remaining_agents = agents.copy()
            removed_agent = remaining_agents.pop()
            
            # Count connected components
            components = self._find_connected_components(remaining_agents)
            largest_component = max(len(comp) for comp in components) if components else 0
            
            # Resilience is the fraction of agents in the largest component
            resilience = largest_component / len(remaining_agents) if remaining_agents else 0.0
            resilience_scores.append(resilience)
            
        return sum(resilience_scores) / len(resilience_scores) if resilience_scores else 0.0
        
    def _find_connected_components(self, agents: List[str]) -> List[Set[str]]:
        """Find connected components in the trust graph."""
        components = []
        visited = set()
        
        for agent in agents:
            if agent in visited:
                continue
                
            # Start BFS from this agent
            component = set()
            queue = [agent]
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                    
                visited.add(current)
                component.add(current)
                
                # Add neighbors
                neighbors = self.trust_graph.get_neighbors(current)
                for neighbor in neighbors:
                    if neighbor in agents and neighbor not in visited:
                        edge = self.trust_graph.get_edge(current, neighbor)
                        if edge and edge.trust_score >= 0.3:
                            queue.append(neighbor)
                            
            if component:
                components.append(component)
                
        return components
        
    def analyze_trust_trends(
        self, 
        agent_id: str, 
        time_period: str = "weekly",
        days: int = 30
    ) -> TrustTrend:
        """
        Analyze trust trends for an agent over time.
        
        Args:
            agent_id: ID of the agent to analyze
            time_period: Time period for analysis ("daily", "weekly", "monthly")
            days: Number of days to analyze
            
        Returns:
            TrustTrend: Trust trend analysis
        """
        # This is a simplified implementation
        # In a real system, you would need historical trust data
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Generate synthetic trend data for demonstration
        trust_scores = []
        timestamps = []
        
        # Simulate trust score changes over time
        base_score = 0.5  # Base trust score
        trend_factor = 0.1  # Small trend
        noise_factor = 0.05  # Random noise
        
        for i in range(days):
            # Calculate trend
            if time_period == "daily":
                days_elapsed = i
            elif time_period == "weekly":
                days_elapsed = i // 7
            else:  # monthly
                days_elapsed = i // 30
                
            # Simulate trust score with trend and noise
            trend = base_score + (trend_factor * days_elapsed) + (noise_factor * (hash(f"{agent_id}_{i}") % 100 - 50) / 100)
            trust_score = max(0.0, min(1.0, trend))
            
            trust_scores.append(trust_score)
            timestamps.append(start_date + timedelta(days=i))
            
        # Calculate trend direction and strength
        if len(trust_scores) > 1:
            trend_strength = (trust_scores[-1] - trust_scores[0]) / len(trust_scores)
            
            if trend_strength > 0.01:
                trend_direction = "increasing"
            elif trend_strength < -0.01:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
                
            # Calculate volatility (standard deviation)
            volatility = statistics.stdev(trust_scores) if len(trust_scores) > 1 else 0.0
        else:
            trend_strength = 0.0
            trend_direction = "stable"
            volatility = 0.0
            
        return TrustTrend(
            agent_id=agent_id,
            time_period=time_period,
            start_date=start_date,
            end_date=end_date,
            trust_scores=trust_scores,
            timestamps=timestamps,
            trend_direction=trend_direction,
            trend_strength=abs(trend_strength),
            volatility=volatility
        )
        
    def get_trust_ranking(self, metric: str = "average_trust_score", limit: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Get ranking of agents by trust metric.
        
        Args:
            metric: Metric to rank by
            limit: Maximum number of agents to return
            
        Returns:
            List of (agent_id, metric_value) tuples, sorted by metric
        """
        agents = self.trust_graph.get_all_agents()
        rankings = []
        
        for agent in agents:
            agent_metrics = self.calculate_agent_metrics(agent, include_behavior=False)
            
            if hasattr(agent_metrics, metric):
                value = getattr(agent_metrics, metric)
                rankings.append((agent, value))
                
        # Sort by metric value (descending)
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        if limit:
            rankings = rankings[:limit]
            
        return rankings
        
    def export_metrics(self, format: str = "json", output_file: Optional[str] = None) -> str:
        """
        Export trust metrics to various formats.
        
        Args:
            format: Export format ("json", "csv")
            output_file: Optional output file path
            
        Returns:
            str: Exported metrics data
        """
        # Calculate metrics for all agents
        agents = self.trust_graph.get_all_agents()
        agent_metrics = {}
        
        for agent in agents:
            agent_metrics[agent] = self.calculate_agent_metrics(agent)
            
        network_metrics = self.calculate_network_metrics()
        
        if format == "json":
            data = {
                "network_metrics": {
                    "total_agents": network_metrics.total_agents,
                    "total_edges": network_metrics.total_edges,
                    "average_trust_score": network_metrics.average_trust_score,
                    "trust_density": network_metrics.trust_density,
                    "trust_clustering_coefficient": network_metrics.trust_clustering_coefficient,
                    "trust_centralization": network_metrics.trust_centralization,
                    "trust_fragmentation": network_metrics.trust_fragmentation,
                    "trust_stability": network_metrics.trust_stability,
                    "trust_efficiency": network_metrics.trust_efficiency,
                    "trust_resilience": network_metrics.trust_resilience,
                    "high_trust_agents": network_metrics.high_trust_agents,
                    "low_trust_agents": network_metrics.low_trust_agents,
                    "trust_communities": network_metrics.trust_communities
                },
                "agent_metrics": {
                    agent_id: {
                        "total_trust_score": metrics.total_trust_score,
                        "average_trust_score": metrics.average_trust_score,
                        "trust_consistency": metrics.trust_consistency,
                        "trust_volatility": metrics.trust_volatility,
                        "trust_centrality": metrics.trust_centrality,
                        "trust_reciprocity": metrics.trust_reciprocity,
                        "trust_clustering": metrics.trust_clustering,
                        "trust_reachability": metrics.trust_reachability,
                        "trust_influence": metrics.trust_influence,
                        "trust_reliability": metrics.trust_reliability,
                        "trust_trend": metrics.trust_trend,
                        "confidence_score": metrics.confidence_score,
                        "risk_score": metrics.risk_score,
                        "metadata": metrics.metadata
                    }
                    for agent_id, metrics in agent_metrics.items()
                },
                "exported_at": datetime.now(timezone.utc).isoformat()
            }
            
            json_data = json.dumps(data, indent=2, default=str)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(json_data)
                return output_file
            else:
                return json_data
                
        elif format == "csv":
            lines = ["agent_id,total_trust_score,average_trust_score,trust_consistency,trust_volatility,trust_centrality,trust_reciprocity,trust_clustering,trust_reachability,trust_influence,trust_reliability,confidence_score,risk_score"]
            
            for agent_id, metrics in agent_metrics.items():
                lines.append(f"{agent_id},{metrics.total_trust_score},{metrics.average_trust_score},{metrics.trust_consistency},{metrics.trust_volatility},{metrics.trust_centrality},{metrics.trust_reciprocity},{metrics.trust_clustering},{metrics.trust_reachability},{metrics.trust_influence},{metrics.trust_reliability},{metrics.confidence_score},{metrics.risk_score}")
                
            csv_data = "\n".join(lines)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(csv_data)
                return output_file
            else:
                return csv_data
                
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def clear_cache(self) -> None:
        """Clear the metrics cache."""
        with self._cache_lock:
            self._metrics_cache.clear()
            self._network_cache = None
            logger.info("[P23P5S1T1] Cleared trust metrics cache")

def main():
    """CLI interface for trust metrics operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitBridge Trust Metrics CLI")
    parser.add_argument("--graph-file", required=True, help="Trust graph file")
    parser.add_argument("--behavior-file", help="Behavior model file")
    parser.add_argument("--command", required=True, choices=["agent", "network", "trend", "ranking", "export"])
    parser.add_argument("--agent-id", help="Agent ID for analysis")
    parser.add_argument("--metric", default="average_trust_score", help="Metric for ranking")
    parser.add_argument("--limit", type=int, help="Limit for ranking results")
    parser.add_argument("--time-period", default="weekly", choices=["daily", "weekly", "monthly"], help="Time period for trends")
    parser.add_argument("--days", type=int, default=30, help="Number of days for trend analysis")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--format", default="json", choices=["json", "csv"], help="Export format")
    
    args = parser.parse_args()
    
    # Load trust graph
    graph = TrustGraph()
    graph.load_from_file(args.graph_file)
    
    # Load behavior model if provided
    behavior_model = None
    if args.behavior_file:
        behavior_model = BehaviorModel()
        # Note: This would need to be implemented based on the behavior model's load method
        
    # Create metrics calculator
    calculator = TrustMetricsCalculator(graph, behavior_model=behavior_model)
    
    if args.command == "agent":
        if not args.agent_id:
            print("Error: --agent-id required for agent command")
            return
        metrics = calculator.calculate_agent_metrics(args.agent_id)
        print(json.dumps(metrics.__dict__, indent=2, default=str))
        
    elif args.command == "network":
        metrics = calculator.calculate_network_metrics()
        print(json.dumps(metrics.__dict__, indent=2, default=str))
        
    elif args.command == "trend":
        if not args.agent_id:
            print("Error: --agent-id required for trend command")
            return
        trend = calculator.analyze_trust_trends(args.agent_id, args.time_period, args.days)
        print(json.dumps(trend.__dict__, indent=2, default=str))
        
    elif args.command == "ranking":
        ranking = calculator.get_trust_ranking(args.metric, args.limit)
        result = {
            "metric": args.metric,
            "ranking": [{"agent_id": agent_id, "value": value} for agent_id, value in ranking]
        }
        print(json.dumps(result, indent=2))
        
    elif args.command == "export":
        result = calculator.export_metrics(args.format, args.output)
        if args.output:
            print(f"Metrics exported to: {result}")
        else:
            print(result)

if __name__ == "__main__":
    main()
