#!/usr/bin/env python3
"""
GitBridge Trust Visualizer
Phase: GBP23
Part: P23P4
Step: P23P4S1
Task: P23P4S1T1 - Trust Graph Visualization

Trust visualizer for interactive graph visualization, trust path display,
and trust network exploration.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P23P4 Schema]
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import math
import colorsys
import threading

from trust_graph import TrustGraph, TrustEdge
from trust_analyzer import TrustAnalyzer, TrustPath, TrustAnalysis

logger = logging.getLogger(__name__)

@dataclass
class VisualNode:
    """Represents a node in the trust visualization."""
    id: str
    x: float = 0.0
    y: float = 0.0
    size: float = 10.0
    color: str = "#3498db"
    label: str = ""
    trust_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class VisualEdge:
    """Represents an edge in the trust visualization."""
    source: str
    target: str
    width: float = 2.0
    color: str = "#95a5a6"
    trust_score: float = 0.0
    confidence: float = 0.0
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class VisualPath:
    """Represents a trust path in the visualization."""
    path: List[str]
    trust_score: float
    confidence: float
    color: str = "#e74c3c"
    width: float = 3.0
    highlight: bool = False

class TrustVisualizer:
    """
    Trust visualizer for interactive graph visualization.
    
    Phase: GBP23
    Part: P23P4
    Step: P23P4S1
    Task: P23P4S1T1 - Core Implementation
    
    Features:
    - Interactive graph visualization
    - Trust path highlighting
    - Node and edge styling
    - Export to various formats
    - Real-time updates
    """
    
    def __init__(self, trust_graph: TrustGraph, analyzer: Optional[TrustAnalyzer] = None):
        """
        Initialize trust visualizer.
        
        Args:
            trust_graph: Trust graph to visualize
            analyzer: Optional trust analyzer for path analysis
        """
        self.trust_graph = trust_graph
        self.analyzer = analyzer or TrustAnalyzer(trust_graph)
        
        # Visualization state
        self.nodes: Dict[str, VisualNode] = {}
        self.edges: Dict[Tuple[str, str], VisualEdge] = {}
        self.paths: List[VisualPath] = []
        
        # Layout configuration
        self.layout_type = "force_directed"  # "force_directed", "circular", "hierarchical"
        self.node_spacing = 100.0
        self.edge_length = 150.0
        
        # Color schemes
        self.color_schemes = {
            "trust": {
                "high": "#27ae60",      # Green
                "medium": "#f39c12",    # Orange
                "low": "#e74c3c",       # Red
                "neutral": "#95a5a6"    # Gray
            },
            "confidence": {
                "high": "#3498db",      # Blue
                "medium": "#9b59b6",    # Purple
                "low": "#e67e22"        # Orange
            }
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize visualization
        self._build_visualization()
        
        logger.info(f"[P23P4S1T1] TrustVisualizer initialized with {len(self.nodes)} nodes and {len(self.edges)} edges")
        
    def _build_visualization(self) -> None:
        """Build the initial visualization from the trust graph."""
        with self._lock:
            # Clear existing visualization
            self.nodes.clear()
            self.edges.clear()
            self.paths.clear()
            
            # Add nodes
            agents = self.trust_graph.get_all_agents()
            for agent in agents:
                node = VisualNode(
                    id=agent,
                    label=agent,
                    trust_score=0.0  # Will be calculated based on incoming edges
                )
                self.nodes[agent] = node
                
            # Add edges
            for agent in agents:
                neighbors = self.trust_graph.get_neighbors(agent)
                for neighbor in neighbors:
                    edge = self.trust_graph.get_edge(agent, neighbor)
                    if edge:
                        visual_edge = VisualEdge(
                            source=agent,
                            target=neighbor,
                            trust_score=edge.trust_score,
                            confidence=edge.confidence,
                            label=f"{edge.trust_score:.2f}"
                        )
                        
                        # Style edge based on trust score
                        visual_edge.color = self._get_trust_color(edge.trust_score)
                        visual_edge.width = self._get_trust_width(edge.trust_score)
                        
                        self.edges[(agent, neighbor)] = visual_edge
                        
            # Calculate node trust scores (average of incoming edges)
            self._calculate_node_trust_scores()
            
            # Apply layout
            self._apply_layout()
            
    def _calculate_node_trust_scores(self) -> None:
        """Calculate trust scores for nodes based on incoming edges."""
        for node_id, node in self.nodes.items():
            incoming_trust = []
            for edge in self.edges.values():
                if edge.target == node_id:
                    incoming_trust.append(edge.trust_score)
                    
            if incoming_trust:
                node.trust_score = sum(incoming_trust) / len(incoming_trust)
                node.color = self._get_trust_color(node.trust_score)
                node.size = self._get_trust_size(node.trust_score)
                
    def _get_trust_color(self, trust_score: float) -> str:
        """Get color based on trust score."""
        if trust_score >= 0.7:
            return self.color_schemes["trust"]["high"]
        elif trust_score >= 0.4:
            return self.color_schemes["trust"]["medium"]
        elif trust_score >= 0.1:
            return self.color_schemes["trust"]["low"]
        else:
            return self.color_schemes["trust"]["neutral"]
            
    def _get_trust_width(self, trust_score: float) -> float:
        """Get edge width based on trust score."""
        return 1.0 + (trust_score * 4.0)  # Range: 1.0 to 5.0
        
    def _get_trust_size(self, trust_score: float) -> float:
        """Get node size based on trust score."""
        return 8.0 + (trust_score * 12.0)  # Range: 8.0 to 20.0
        
    def _apply_layout(self) -> None:
        """Apply layout algorithm to position nodes."""
        if self.layout_type == "circular":
            self._apply_circular_layout()
        elif self.layout_type == "force_directed":
            self._apply_force_directed_layout()
        elif self.layout_type == "hierarchical":
            self._apply_hierarchical_layout()
            
    def _apply_circular_layout(self) -> None:
        """Apply circular layout."""
        nodes_list = list(self.nodes.values())
        center_x, center_y = 400.0, 300.0
        radius = min(300.0, len(nodes_list) * 20.0)
        
        for i, node in enumerate(nodes_list):
            angle = (2 * math.pi * i) / len(nodes_list)
            node.x = center_x + radius * math.cos(angle)
            node.y = center_y + radius * math.sin(angle)
            
    def _apply_force_directed_layout(self) -> None:
        """Apply force-directed layout (simplified)."""
        # Simple force-directed layout with repulsion and attraction
        nodes_list = list(self.nodes.values())
        
        # Initialize random positions
        for node in nodes_list:
            node.x = 400.0 + (hash(node.id) % 200 - 100)
            node.y = 300.0 + (hash(node.id) % 200 - 100)
            
        # Apply forces for a few iterations
        for _ in range(50):
            # Repulsion between all nodes
            for i, node1 in enumerate(nodes_list):
                for j, node2 in enumerate(nodes_list[i+1:], i+1):
                    dx = node2.x - node1.x
                    dy = node2.y - node1.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance > 0:
                        # Repulsion force
                        force = 1000.0 / (distance * distance)
                        node1.x -= (dx / distance) * force * 0.01
                        node1.y -= (dy / distance) * force * 0.01
                        node2.x += (dx / distance) * force * 0.01
                        node2.y += (dy / distance) * force * 0.01
                        
            # Attraction along edges
            for edge in self.edges.values():
                source_node = self.nodes[edge.source]
                target_node = self.nodes[edge.target]
                
                dx = target_node.x - source_node.x
                dy = target_node.y - source_node.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > 0:
                    # Attraction force based on trust score
                    force = (distance - self.edge_length) * edge.trust_score * 0.1
                    source_node.x += (dx / distance) * force
                    source_node.y += (dy / distance) * force
                    target_node.x -= (dx / distance) * force
                    target_node.y -= (dy / distance) * force
                    
    def _apply_hierarchical_layout(self) -> None:
        """Apply hierarchical layout."""
        # Simple hierarchical layout based on trust scores
        nodes_list = list(self.nodes.values())
        nodes_list.sort(key=lambda n: n.trust_score, reverse=True)
        
        # Position nodes in layers
        layer_height = 100.0
        nodes_per_layer = 5
        
        for i, node in enumerate(nodes_list):
            layer = i // nodes_per_layer
            pos_in_layer = i % nodes_per_layer
            
            node.x = 100.0 + pos_in_layer * 150.0
            node.y = 50.0 + layer * layer_height
            
    def highlight_trust_path(self, source: str, target: str, max_paths: int = 3) -> List[VisualPath]:
        """
        Highlight trust paths between source and target.
        
        Args:
            source: Source agent ID
            target: Target agent ID
            max_paths: Maximum number of paths to highlight
            
        Returns:
            List of visual paths
        """
        with self._lock:
            # Clear existing paths
            self.paths.clear()
            
            # Get trust analysis
            analysis = self.analyzer.analyze_trust_paths(source, target, max_paths)
            
            # Create visual paths
            for i, path in enumerate(analysis.all_paths):
                # Generate different colors for different paths
                hue = (i * 137.5) % 360  # Golden angle for good distribution
                color = f"hsl({hue}, 70%, 50%)"
                
                visual_path = VisualPath(
                    path=path.path,
                    trust_score=path.total_trust,
                    confidence=path.confidence,
                    color=color,
                    width=3.0 + (path.total_trust * 2.0),
                    highlight=(i == 0)  # Highlight best path
                )
                self.paths.append(visual_path)
                
            logger.info(f"[P23P4S1T1] Highlighted {len(self.paths)} trust paths from {source} to {target}")
            return self.paths
            
    def highlight_trust_clusters(self, min_trust: float = 0.6) -> List[Set[str]]:
        """
        Highlight trust clusters in the visualization.
        
        Args:
            min_trust: Minimum trust score for cluster membership
            
        Returns:
            List of agent clusters
        """
        with self._lock:
            clusters = self.analyzer.find_trust_clusters(min_trust)
            
            # Assign cluster colors to nodes
            for i, cluster in enumerate(clusters):
                hue = (i * 137.5) % 360
                color = f"hsl({hue}, 70%, 50%)"
                
                for agent_id in cluster:
                    if agent_id in self.nodes:
                        self.nodes[agent_id].color = color
                        
            logger.info(f"[P23P4S1T1] Highlighted {len(clusters)} trust clusters")
            return clusters
            
    def filter_by_trust_threshold(self, min_trust: float = 0.3) -> None:
        """
        Filter visualization to show only edges above trust threshold.
        
        Args:
            min_trust: Minimum trust score to display
        """
        with self._lock:
            # Hide edges below threshold
            for edge_key, edge in self.edges.items():
                if edge.trust_score < min_trust:
                    edge.color = "#ecf0f1"  # Very light gray (effectively hidden)
                    edge.width = 0.5
                    
            logger.info(f"[P23P4S1T1] Filtered edges by trust threshold {min_trust}")
            
    def get_visualization_data(self) -> Dict[str, Any]:
        """
        Get visualization data for export or rendering.
        
        Returns:
            Dict containing visualization data
        """
        with self._lock:
            return {
                "nodes": [
                    {
                        "id": node.id,
                        "x": node.x,
                        "y": node.y,
                        "size": node.size,
                        "color": node.color,
                        "label": node.label,
                        "trust_score": node.trust_score,
                        "metadata": node.metadata
                    }
                    for node in self.nodes.values()
                ],
                "edges": [
                    {
                        "source": edge.source,
                        "target": edge.target,
                        "width": edge.width,
                        "color": edge.color,
                        "trust_score": edge.trust_score,
                        "confidence": edge.confidence,
                        "label": edge.label,
                        "metadata": edge.metadata
                    }
                    for edge in self.edges.values()
                ],
                "paths": [
                    {
                        "path": path.path,
                        "trust_score": path.trust_score,
                        "confidence": path.confidence,
                        "color": path.color,
                        "width": path.width,
                        "highlight": path.highlight
                    }
                    for path in self.paths
                ],
                "metadata": {
                    "total_nodes": len(self.nodes),
                    "total_edges": len(self.edges),
                    "total_paths": len(self.paths),
                    "layout_type": self.layout_type,
                    "exported_at": datetime.now(timezone.utc).isoformat()
                }
            }
            
    def export_visualization(self, format: str = "json", output_file: Optional[str] = None) -> str:
        """
        Export visualization to various formats.
        
        Args:
            format: Export format ("json", "svg", "dot")
            output_file: Optional output file path
            
        Returns:
            str: Exported visualization data or file path
        """
        if format == "json":
            data = self.get_visualization_data()
            json_data = json.dumps(data, indent=2)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(json_data)
                return output_file
            else:
                return json_data
                
        elif format == "svg":
            return self._export_svg(output_file)
            
        elif format == "dot":
            return self._export_dot(output_file)
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def _export_svg(self, output_file: Optional[str] = None) -> str:
        """Export visualization as SVG."""
        data = self.get_visualization_data()
        
        # Calculate viewport
        min_x = min(node["x"] for node in data["nodes"]) - 50
        max_x = max(node["x"] for node in data["nodes"]) + 50
        min_y = min(node["y"] for node in data["nodes"]) - 50
        max_y = max(node["y"] for node in data["nodes"]) + 50
        width = max_x - min_x
        height = max_y - min_y
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" 
            refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#95a5a6"/>
    </marker>
  </defs>
  
  <!-- Edges -->
'''
        
        # Add edges
        for edge in data["edges"]:
            source_node = next(n for n in data["nodes"] if n["id"] == edge["source"])
            target_node = next(n for n in data["nodes"] if n["id"] == edge["target"])
            
            svg_content += f'''  <line x1="{source_node['x']}" y1="{source_node['y']}" 
        x2="{target_node['x']}" y2="{target_node['y']}" 
        stroke="{edge['color']}" stroke-width="{edge['width']}" 
        marker-end="url(#arrowhead)"/>
'''
            
        # Add nodes
        for node in data["nodes"]:
            svg_content += f'''  <circle cx="{node['x']}" cy="{node['y']}" r="{node['size']}" 
        fill="{node['color']}" stroke="#2c3e50" stroke-width="2"/>
  <text x="{node['x']}" y="{node['y'] + node['size'] + 15}" 
        text-anchor="middle" font-family="Arial" font-size="12" fill="#2c3e50">
    {node['label']}
  </text>
'''
            
        svg_content += "</svg>"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(svg_content)
            return output_file
        else:
            return svg_content
            
    def _export_dot(self, output_file: Optional[str] = None) -> str:
        """Export visualization as DOT format for Graphviz."""
        data = self.get_visualization_data()
        
        dot_content = "digraph trust_graph {\n"
        dot_content += "  rankdir=LR;\n"
        dot_content += "  node [shape=circle, style=filled];\n"
        dot_content += "  edge [arrowsize=0.5];\n\n"
        
        # Add nodes
        for node in data["nodes"]:
            dot_content += f'  "{node["id"]}" [label="{node["label"]}", fillcolor="{node["color"]}", width={node["size"]/10:.1f}];\n'
            
        # Add edges
        for edge in data["edges"]:
            dot_content += f'  "{edge["source"]}" -> "{edge["target"]}" [label="{edge["label"]}", color="{edge["color"]}", penwidth={edge["width"]}];\n'
            
        dot_content += "}\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(dot_content)
            return output_file
        else:
            return dot_content
            
    def update_node_position(self, node_id: str, x: float, y: float) -> bool:
        """
        Update node position in the visualization.
        
        Args:
            node_id: ID of the node to update
            x: New x coordinate
            y: New y coordinate
            
        Returns:
            bool: True if node was updated successfully
        """
        with self._lock:
            if node_id in self.nodes:
                self.nodes[node_id].x = x
                self.nodes[node_id].y = y
                return True
            return False
            
    def set_layout_type(self, layout_type: str) -> bool:
        """
        Set the layout type and reapply layout.
        
        Args:
            layout_type: Layout type ("force_directed", "circular", "hierarchical")
            
        Returns:
            bool: True if layout was applied successfully
        """
        if layout_type not in ["force_directed", "circular", "hierarchical"]:
            return False
            
        with self._lock:
            self.layout_type = layout_type
            self._apply_layout()
            return True
            
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get visualization statistics.
        
        Returns:
            Dict containing visualization statistics
        """
        with self._lock:
            total_nodes = len(self.nodes)
            total_edges = len(self.edges)
            
            # Calculate trust score distribution
            trust_scores = [edge.trust_score for edge in self.edges.values()]
            avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
            
            high_trust_edges = sum(1 for score in trust_scores if score >= 0.7)
            medium_trust_edges = sum(1 for score in trust_scores if 0.4 <= score < 0.7)
            low_trust_edges = sum(1 for score in trust_scores if score < 0.4)
            
            return {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "average_trust_score": avg_trust,
                "high_trust_edges": high_trust_edges,
                "medium_trust_edges": medium_trust_edges,
                "low_trust_edges": low_trust_edges,
                "highlighted_paths": len(self.paths),
                "layout_type": self.layout_type
            }

def main():
    """CLI interface for trust visualizer operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitBridge Trust Visualizer CLI")
    parser.add_argument("--graph-file", required=True, help="Trust graph file")
    parser.add_argument("--command", required=True, choices=["export", "highlight", "filter", "stats"])
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--format", default="json", choices=["json", "svg", "dot"], help="Export format")
    parser.add_argument("--source", help="Source agent ID for path highlighting")
    parser.add_argument("--target", help="Target agent ID for path highlighting")
    parser.add_argument("--min-trust", type=float, default=0.3, help="Minimum trust threshold")
    parser.add_argument("--layout", default="force_directed", choices=["force_directed", "circular", "hierarchical"], help="Layout type")
    
    args = parser.parse_args()
    
    # Load trust graph
    graph = TrustGraph()
    graph.load_from_file(args.graph_file)
    
    # Create visualizer
    visualizer = TrustVisualizer(graph)
    visualizer.set_layout_type(args.layout)
    
    if args.command == "export":
        result = visualizer.export_visualization(args.format, args.output)
        if args.output:
            print(f"Visualization exported to: {result}")
        else:
            print(result)
            
    elif args.command == "highlight":
        if args.source and args.target:
            paths = visualizer.highlight_trust_path(args.source, args.target)
            print(f"Highlighted {len(paths)} trust paths")
        else:
            clusters = visualizer.highlight_trust_clusters(args.min_trust)
            print(f"Highlighted {len(clusters)} trust clusters")
            
    elif args.command == "filter":
        visualizer.filter_by_trust_threshold(args.min_trust)
        print(f"Filtered edges by trust threshold {args.min_trust}")
        
    elif args.command == "stats":
        stats = visualizer.get_statistics()
        print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
