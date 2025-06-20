#!/usr/bin/env python3
"""
GitBridge Trust Analyzer
Phase: GBP23
Part: P23P3
Step: P23P3S1
Task: P23P3S1T1 - Trust Path Analysis and Propagation

Trust analyzer for analyzing trust paths, calculating trust propagation,
and assessing trustworthiness between agents.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P23P3 Schema]
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import math
import heapq
from collections import defaultdict, deque
import threading

from trust_graph import TrustGraph, TrustEdge

logger = logging.getLogger(__name__)

@dataclass
class TrustPath:
    """Represents a trust path between two agents."""
    source: str
    target: str
    path: List[str]  # List of agent IDs in the path
    total_trust: float  # Overall trust score for the path
    path_length: int  # Number of hops in the path
    confidence: float  # Confidence in the path assessment
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def trust_per_hop(self) -> float:
        """Calculate average trust per hop."""
        if self.path_length == 0:
            return 0.0
        return self.total_trust / self.path_length

@dataclass
class TrustAnalysis:
    """Comprehensive trust analysis results."""
    source: str
    target: str
    direct_trust: Optional[float] = None
    indirect_trust: Optional[float] = None
    best_path: Optional[TrustPath] = None
    all_paths: List[TrustPath] = field(default_factory=list)
    trust_network: Dict[str, float] = field(default_factory=dict)  # Trust scores to intermediate agents
    confidence: float = 0.0
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

class TrustAnalyzer:
    """
    Trust analyzer for path analysis and trust propagation.
    
    Phase: GBP23
    Part: P23P3
    Step: P23P3S1
    Task: P23P3S1T1 - Core Implementation
    
    Features:
    - Trust path finding and analysis
    - Trust propagation algorithms
    - Trustworthiness assessment
    - Path confidence calculation
    - Trust network analysis
    """
    
    def __init__(self, trust_graph: TrustGraph, max_path_length: int = 5, decay_factor: float = 0.8):
        """
        Initialize trust analyzer.
        
        Args:
            trust_graph: Trust graph to analyze
            max_path_length: Maximum path length to consider
            decay_factor: Trust decay factor per hop (0.0 to 1.0)
        """
        self.trust_graph = trust_graph
        self.max_path_length = max_path_length
        self.decay_factor = decay_factor
        
        # Analysis cache
        self._analysis_cache: Dict[str, TrustAnalysis] = {}
        self._cache_lock = threading.RLock()
        
        # Configuration
        self.min_confidence_threshold = 0.1
        self.max_paths_per_analysis = 10
        
        logger.info(f"[P23P3S1T1] TrustAnalyzer initialized with max_path_length={max_path_length}, decay_factor={decay_factor}")
        
    def analyze_trust_paths(
        self, 
        source: str, 
        target: str, 
        max_paths: Optional[int] = None,
        min_confidence: Optional[float] = None
    ) -> TrustAnalysis:
        """
        Analyze trust paths between source and target agents.
        
        Args:
            source: Source agent ID
            target: Target agent ID
            max_paths: Maximum number of paths to find
            min_confidence: Minimum confidence threshold
            
        Returns:
            TrustAnalysis: Comprehensive trust analysis results
        """
        if max_paths is None:
            max_paths = self.max_paths_per_analysis
        if min_confidence is None:
            min_confidence = self.min_confidence_threshold
            
        # Check cache first
        cache_key = f"{source}:{target}"
        with self._cache_lock:
            if cache_key in self._analysis_cache:
                cached = self._analysis_cache[cache_key]
                # Check if cache is still valid (within 1 hour)
                if (datetime.now(timezone.utc) - cached.analysis_timestamp).total_seconds() < 3600:
                    logger.debug(f"[P23P3S1T1] Using cached analysis for {source} -> {target}")
                    return cached
                    
        # Perform analysis
        analysis = TrustAnalysis(source=source, target=target)
        
        # Check for direct trust
        direct_edge = self.trust_graph.get_edge(source, target)
        if direct_edge:
            analysis.direct_trust = direct_edge.trust_score
            analysis.confidence = direct_edge.confidence
            
        # Find indirect trust paths
        paths = self._find_trust_paths(source, target, max_paths, min_confidence)
        analysis.all_paths = paths
        
        if paths:
            # Best path is the one with highest total trust
            analysis.best_path = max(paths, key=lambda p: p.total_trust)
            analysis.indirect_trust = analysis.best_path.total_trust
            
            # Calculate overall confidence
            if analysis.direct_trust is not None:
                # Combine direct and indirect trust
                analysis.confidence = max(analysis.confidence, analysis.best_path.confidence)
            else:
                analysis.confidence = analysis.best_path.confidence
                
            # Build trust network
            analysis.trust_network = self._build_trust_network(paths)
            
        # Cache results
        with self._cache_lock:
            self._analysis_cache[cache_key] = analysis
            
        logger.info(f"[P23P3S1T1] Analyzed trust paths {source} -> {target}: {len(paths)} paths found")
        return analysis
        
    def _find_trust_paths(
        self, 
        source: str, 
        target: str, 
        max_paths: int, 
        min_confidence: float
    ) -> List[TrustPath]:
        """
        Find trust paths between source and target using modified Dijkstra's algorithm.
        
        Args:
            source: Source agent ID
            target: Target agent ID
            max_paths: Maximum number of paths to find
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of trust paths
        """
        if source == target:
            return []
            
        # Priority queue for path exploration
        # (negative_trust_score, path_length, current_node, path, total_confidence)
        pq = [(0, 0, source, [source], 1.0)]
        visited = set()
        paths = []
        
        while pq and len(paths) < max_paths:
            neg_trust, path_length, current, path, confidence = heapq.heappop(pq)
            
            # Skip if path is too long or confidence is too low
            if path_length >= self.max_path_length or confidence < min_confidence:
                continue
                
            # Skip if we've already found a better path to this node
            path_key = (current, tuple(path))
            if path_key in visited:
                continue
            visited.add(path_key)
            
            # Check if we've reached the target
            if current == target and len(path) > 1:  # Must have at least one hop
                total_trust = self._calculate_path_trust(path)
                trust_path = TrustPath(
                    source=source,
                    target=target,
                    path=path.copy(),
                    total_trust=total_trust,
                    path_length=len(path) - 1,
                    confidence=confidence
                )
                paths.append(trust_path)
                continue
                
            # Explore neighbors
            neighbors = self.trust_graph.get_neighbors(current)
            for neighbor in neighbors:
                if neighbor not in path:  # Avoid cycles
                    edge = self.trust_graph.get_edge(current, neighbor)
                    if edge and edge.trust_score > 0:
                        new_path = path + [neighbor]
                        new_confidence = confidence * edge.confidence
                        
                        # Apply decay factor
                        decayed_trust = edge.trust_score * (self.decay_factor ** path_length)
                        
                        heapq.heappush(pq, (
                            -decayed_trust,  # Negative for max-heap behavior
                            path_length + 1,
                            neighbor,
                            new_path,
                            new_confidence
                        ))
                        
        # Sort paths by total trust (descending)
        paths.sort(key=lambda p: p.total_trust, reverse=True)
        return paths[:max_paths]
        
    def _calculate_path_trust(self, path: List[str]) -> float:
        """
        Calculate total trust score for a path.
        
        Args:
            path: List of agent IDs representing the path
            
        Returns:
            float: Total trust score
        """
        if len(path) < 2:
            return 0.0
            
        total_trust = 1.0
        
        for i in range(len(path) - 1):
            edge = self.trust_graph.get_edge(path[i], path[i + 1])
            if edge:
                # Apply decay factor for each hop
                hop_trust = edge.trust_score * (self.decay_factor ** i)
                total_trust *= hop_trust
            else:
                return 0.0
                
        return total_trust
        
    def _build_trust_network(self, paths: List[TrustPath]) -> Dict[str, float]:
        """
        Build trust network from multiple paths.
        
        Args:
            paths: List of trust paths
            
        Returns:
            Dict mapping agent IDs to trust scores
        """
        network = defaultdict(list)
        
        for path in paths:
            for i, agent in enumerate(path.path[1:-1]):  # Exclude source and target
                # Trust score decreases with distance from source
                trust_score = path.total_trust * (self.decay_factor ** i)
                network[agent].append(trust_score)
                
        # Average trust scores for each agent
        return {agent: sum(scores) / len(scores) for agent, scores in network.items()}
        
    def assess_trustworthiness(
        self, 
        source: str, 
        target: str, 
        context: str = "general"
    ) -> Dict[str, Any]:
        """
        Assess trustworthiness between agents.
        
        Args:
            source: Source agent ID
            target: Target agent ID
            context: Context for assessment
            
        Returns:
            Dict containing trustworthiness assessment
        """
        analysis = self.analyze_trust_paths(source, target)
        
        # Base assessment
        assessment = {
            "source": source,
            "target": target,
            "context": context,
            "direct_trust": analysis.direct_trust,
            "indirect_trust": analysis.indirect_trust,
            "overall_confidence": analysis.confidence,
            "trust_level": "unknown",
            "recommendation": "insufficient_data",
            "path_count": len(analysis.all_paths),
            "best_path_length": analysis.best_path.path_length if analysis.best_path else None,
            "trust_network_size": len(analysis.trust_network)
        }
        
        # Determine overall trust score
        if analysis.direct_trust is not None and analysis.indirect_trust is not None:
            # Combine direct and indirect trust
            overall_trust = (analysis.direct_trust + analysis.indirect_trust) / 2
        elif analysis.direct_trust is not None:
            overall_trust = analysis.direct_trust
        elif analysis.indirect_trust is not None:
            overall_trust = analysis.indirect_trust
        else:
            overall_trust = 0.0
            
        assessment["overall_trust"] = overall_trust
        
        # Determine trust level
        if overall_trust >= 0.8:
            assessment["trust_level"] = "high"
            assessment["recommendation"] = "trust"
        elif overall_trust >= 0.6:
            assessment["trust_level"] = "medium"
            assessment["recommendation"] = "trust_with_caution"
        elif overall_trust >= 0.4:
            assessment["trust_level"] = "low"
            assessment["recommendation"] = "verify"
        else:
            assessment["trust_level"] = "very_low"
            assessment["recommendation"] = "distrust"
            
        # Context-specific adjustments
        if context != "general":
            # Adjust based on context-specific trust patterns
            context_trust = self._get_context_trust(source, target, context)
            if context_trust > 0:
                assessment["context_trust"] = context_trust
                assessment["overall_trust"] = (assessment["overall_trust"] + context_trust) / 2
                
        return assessment
        
    def _get_context_trust(self, source: str, target: str, context: str) -> float:
        """
        Get context-specific trust score.
        
        Args:
            source: Source agent ID
            target: Target agent ID
            context: Context for trust assessment
            
        Returns:
            float: Context-specific trust score
        """
        # This would typically query context-specific trust data
        # For now, return a neutral score
        return 0.0
        
    def find_trust_clusters(self, min_trust: float = 0.6) -> List[Set[str]]:
        """
        Find clusters of agents with high mutual trust.
        
        Args:
            min_trust: Minimum trust score for cluster membership
            
        Returns:
            List of agent clusters
        """
        clusters = []
        visited = set()
        
        for agent in self.trust_graph.get_all_agents():
            if agent in visited:
                continue
                
            # Start BFS from this agent
            cluster = set()
            queue = deque([agent])
            
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                    
                visited.add(current)
                cluster.add(current)
                
                # Add neighbors with sufficient trust
                neighbors = self.trust_graph.get_neighbors(current)
                for neighbor in neighbors:
                    edge = self.trust_graph.get_edge(current, neighbor)
                    if edge and edge.trust_score >= min_trust:
                        queue.append(neighbor)
                        
            if len(cluster) > 1:  # Only include clusters with multiple agents
                clusters.append(cluster)
                
        return clusters
        
    def get_trust_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive trust statistics.
        
        Returns:
            Dict containing trust statistics
        """
        agents = self.trust_graph.get_all_agents()
        total_agents = len(agents)
        
        if total_agents == 0:
            return {"total_agents": 0}
            
        # Calculate trust metrics
        total_edges = 0
        total_trust = 0.0
        high_trust_edges = 0
        low_trust_edges = 0
        
        for agent in agents:
            neighbors = self.trust_graph.get_neighbors(agent)
            for neighbor in neighbors:
                edge = self.trust_graph.get_edge(agent, neighbor)
                if edge:
                    total_edges += 1
                    total_trust += edge.trust_score
                    
                    if edge.trust_score >= 0.7:
                        high_trust_edges += 1
                    elif edge.trust_score <= 0.3:
                        low_trust_edges += 1
                        
        avg_trust = total_trust / total_edges if total_edges > 0 else 0.0
        
        # Find trust clusters
        clusters = self.find_trust_clusters()
        
        return {
            "total_agents": total_agents,
            "total_trust_edges": total_edges,
            "average_trust_score": avg_trust,
            "high_trust_edges": high_trust_edges,
            "low_trust_edges": low_trust_edges,
            "trust_clusters": len(clusters),
            "largest_cluster_size": max(len(cluster) for cluster in clusters) if clusters else 0,
            "average_cluster_size": sum(len(cluster) for cluster in clusters) / len(clusters) if clusters else 0,
            "trust_density": total_edges / (total_agents * (total_agents - 1)) if total_agents > 1 else 0.0
        }
        
    def export_analysis(self, analysis: TrustAnalysis, format: str = "json") -> str:
        """
        Export trust analysis to various formats.
        
        Args:
            analysis: Trust analysis to export
            format: Export format ("json", "csv")
            
        Returns:
            str: Exported analysis data
        """
        if format == "json":
            data = {
                "source": analysis.source,
                "target": analysis.target,
                "direct_trust": analysis.direct_trust,
                "indirect_trust": analysis.indirect_trust,
                "confidence": analysis.confidence,
                "analysis_timestamp": analysis.analysis_timestamp.isoformat(),
                "paths": [
                    {
                        "path": path.path,
                        "total_trust": path.total_trust,
                        "path_length": path.path_length,
                        "confidence": path.confidence,
                        "trust_per_hop": path.trust_per_hop
                    }
                    for path in analysis.all_paths
                ],
                "trust_network": analysis.trust_network,
                "metadata": analysis.metadata
            }
            return json.dumps(data, indent=2)
        elif format == "csv":
            lines = ["path_index,path,total_trust,path_length,confidence,trust_per_hop"]
            for i, path in enumerate(analysis.all_paths):
                path_str = "->".join(path.path)
                lines.append(f"{i},{path_str},{path.total_trust},{path.path_length},{path.confidence},{path.trust_per_hop}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        with self._cache_lock:
            self._analysis_cache.clear()
            logger.info("[P23P3S1T1] Cleared trust analysis cache")

def main():
    """CLI interface for trust analyzer operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitBridge Trust Analyzer CLI")
    parser.add_argument("--graph-file", required=True, help="Trust graph file")
    parser.add_argument("--command", required=True, choices=["analyze", "assess", "clusters", "stats"])
    parser.add_argument("--source", help="Source agent ID")
    parser.add_argument("--target", help="Target agent ID")
    parser.add_argument("--context", default="general", help="Trust context")
    parser.add_argument("--max-paths", type=int, default=10, help="Maximum paths to find")
    parser.add_argument("--min-trust", type=float, default=0.6, help="Minimum trust for clusters")
    parser.add_argument("--format", default="json", choices=["json", "csv"], help="Export format")
    
    args = parser.parse_args()
    
    # Load trust graph
    graph = TrustGraph()
    graph.load_from_file(args.graph_file)
    
    analyzer = TrustAnalyzer(graph)
    
    if args.command == "analyze":
        if not all([args.source, args.target]):
            print("Error: --source and --target required for analyze command")
            return
        analysis = analyzer.analyze_trust_paths(args.source, args.target, args.max_paths)
        data = analyzer.export_analysis(analysis, args.format)
        print(data)
        
    elif args.command == "assess":
        if not all([args.source, args.target]):
            print("Error: --source and --target required for assess command")
            return
        assessment = analyzer.assess_trustworthiness(args.source, args.target, args.context)
        print(json.dumps(assessment, indent=2))
        
    elif args.command == "clusters":
        clusters = analyzer.find_trust_clusters(args.min_trust)
        result = {
            "clusters": [list(cluster) for cluster in clusters],
            "cluster_count": len(clusters),
            "min_trust_threshold": args.min_trust
        }
        print(json.dumps(result, indent=2))
        
    elif args.command == "stats":
        stats = analyzer.get_trust_statistics()
        print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
