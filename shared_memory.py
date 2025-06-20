#!/usr/bin/env python3
"""
GitBridge Shared Memory Layer
Phase: GBP21
Part: P21P5
Step: P21P5S1
Task: P21P5S1T1 - Shared Memory Graph Implementation

Develop shared memory graph for agents.
Scoped memory context recall based on task bundling.
Record metadata: agent ID, task context, results, timestamp.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P21P5 Schema]
"""

import json
import logging
import argparse
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
import sys

logger = logging.getLogger(__name__)

@dataclass
class MemoryNode:
    """Represents a node in the shared memory graph."""
    node_id: str
    agent_id: str
    task_context: str
    result: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    links: List[str] = field(default_factory=list)  # Linked node_ids

class SharedMemoryGraph:
    """
    Shared memory graph for agent collaboration.
    
    Phase: GBP21
    Part: P21P5
    Step: P21P5S1
    Task: P21P5S1T1 - Core Implementation
    
    Features:
    - Add and link memory nodes
    - Scoped memory context recall
    - Metadata and provenance tracking
    """
    def __init__(self):
        self.nodes: Dict[str, MemoryNode] = {}
        self.agent_index: Dict[str, List[str]] = {}
        self.context_index: Dict[str, List[str]] = {}
        logger.info("[P21P5S1T1] SharedMemoryGraph initialized")

    def add_node(self, agent_id: str, task_context: str, result: Any, metadata: Optional[Dict[str, Any]] = None, links: Optional[List[str]] = None) -> str:
        node_id = f"node_{len(self.nodes) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        node = MemoryNode(
            node_id=node_id,
            agent_id=agent_id,
            task_context=task_context,
            result=result,
            metadata=metadata or {},
            links=links or []
        )
        self.nodes[node_id] = node
        self.agent_index.setdefault(agent_id, []).append(node_id)
        self.context_index.setdefault(task_context, []).append(node_id)
        logger.info(f"[P21P5S1T1] Added node {node_id} for agent {agent_id}")
        return node_id

    def link_nodes(self, from_node_id: str, to_node_id: str) -> None:
        if from_node_id in self.nodes and to_node_id in self.nodes:
            self.nodes[from_node_id].links.append(to_node_id)
            logger.info(f"[P21P5S1T1] Linked node {from_node_id} -> {to_node_id}")

    def get_nodes_by_agent(self, agent_id: str) -> List[MemoryNode]:
        return [self.nodes[nid] for nid in self.agent_index.get(agent_id, [])]

    def get_nodes_by_context(self, task_context: str) -> List[MemoryNode]:
        return [self.nodes[nid] for nid in self.context_index.get(task_context, [])]

    def recall_context(self, agent_id: str, task_context: str) -> List[MemoryNode]:
        # Scoped recall: intersection of agent and context
        agent_nodes = set(self.agent_index.get(agent_id, []))
        context_nodes = set(self.context_index.get(task_context, []))
        node_ids = agent_nodes & context_nodes
        logger.info(f"[P21P5S1T1] Recalled {len(node_ids)} nodes for agent {agent_id} and context {task_context}")
        return [self.nodes[nid] for nid in node_ids]

    def export_memory(self, output_path: str = "shared_memory_export.json") -> None:
        export_data = [
            {
                'node_id': node.node_id,
                'agent_id': node.agent_id,
                'task_context': node.task_context,
                'result': node.result,
                'timestamp': node.timestamp.isoformat(),
                'metadata': node.metadata,
                'links': node.links
            }
            for node in self.nodes.values()
        ]
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        logger.info(f"[P21P5S1T1] Exported shared memory to {output_path}")

    def preview_operations(self) -> str:
        """Preview memory operations without executing them."""
        preview = []
        preview.append("🔍 MEMORY OPERATIONS PREVIEW")
        preview.append("=" * 40)
        preview.append(f"Total nodes: {len(self.nodes)}")
        preview.append(f"Total agents: {len(self.agent_index)}")
        preview.append(f"Total contexts: {len(self.context_index)}")
        preview.append("")
        
        # Preview agent nodes
        preview.append("Agent Index Preview:")
        for agent_id, node_ids in self.agent_index.items():
            preview.append(f"  {agent_id}: {len(node_ids)} nodes")
        preview.append("")
        
        # Preview context nodes
        preview.append("Context Index Preview:")
        for context, node_ids in self.context_index.items():
            preview.append(f"  {context}: {len(node_ids)} nodes")
        preview.append("")
        
        # Preview recent nodes
        preview.append("Recent Nodes Preview:")
        recent_nodes = sorted(self.nodes.values(), key=lambda x: x.timestamp, reverse=True)[:5]
        for node in recent_nodes:
            preview.append(f"  {node.node_id}: {node.agent_id} -> {node.task_context}")
        
        return "\n".join(preview)

def main():
    parser = argparse.ArgumentParser(description='GitBridge Shared Memory Graph')
    parser.add_argument('--dry-run', action='store_true', help='Preview memory operations without storing or exporting')
    args = parser.parse_args()
    
    logger.info("[P21P5S1T1] Testing Shared Memory Graph")
    memory = SharedMemoryGraph()
    
    if args.dry_run:
        print("🔍 DRY-RUN MODE: Previewing memory operations")
        # Simulate operations without storing
        print("Simulating node additions...")
        print("Simulating node linking...")
        print("Simulating context recall...")
        print("\n" + memory.preview_operations())
        return
    
    # Add nodes
    n1 = memory.add_node("openai_gpt4o", "code_review", {"summary": "No issues found."})
    n2 = memory.add_node("cursor_assistant", "code_review", {"summary": "Refactor suggested."}, links=[n1])
    n3 = memory.add_node("grok_3", "analysis", {"insight": "Potential optimization."})
    # Link nodes
    memory.link_nodes(n1, n2)
    # Recall
    recalled = memory.recall_context("cursor_assistant", "code_review")
    print(f"Recalled {len(recalled)} nodes for cursor_assistant/code_review")
    # Export
    memory.export_memory()

if __name__ == "__main__":
    main() 