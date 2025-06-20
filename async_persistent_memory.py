#!/usr/bin/env python3
"""
GitBridge Async Persistent Memory Layer
Phase: GBP21
Part: P21P8
Step: P21P8S1
Task: P21P8S1T1 - Async Persistent Memory Implementation

Enable concurrent memory operations with persistence support for Phase 22 arbitration logic.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P21P8 Schema]
"""

import json
import logging
import asyncio
import aiofiles
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import hashlib
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TimeRange:
    """Represents a time range for temporal queries."""
    start: datetime
    end: datetime
    
    def __post_init__(self):
        if self.start.tzinfo is None:
            self.start = self.start.replace(tzinfo=timezone.utc)
        if self.end.tzinfo is None:
            self.end = self.end.replace(tzinfo=timezone.utc)

@dataclass
class MemoryNode:
    """Represents a memory node with async persistence support."""
    node_id: str
    agent_id: str
    task_context: str
    result: Any
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    persistence_hash: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        if self.persistence_hash is None:
            self.persistence_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate hash for persistence validation."""
        content = f"{self.node_id}{self.agent_id}{self.task_context}{self.timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

class AsyncPersistentMemory:
    """
    Async persistent memory layer with concurrent operations.
    
    Phase: GBP21
    Part: P21P8
    Step: P21P8S1
    Task: P21P8S1T1 - Core Implementation
    
    Features:
    - Async memory operations with thread safety
    - Persistent storage with file-based backend
    - Temporal querying with time range support
    - Memory indexing and caching
    - Concurrent access support
    """
    
    def __init__(self, storage_path: str = "memory_storage", cache_size: int = 1000):
        """
        Initialize async persistent memory.
        
        Args:
            storage_path: Directory for persistent storage
            cache_size: Maximum number of nodes in memory cache
        """
        self.storage_path = Path(storage_path)
        self.cache_size = cache_size
        self.cache: Dict[str, MemoryNode] = {}
        self.index: Dict[str, List[str]] = defaultdict(list)
        self.temporal_index: Dict[str, List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._ensure_storage_directory()
        
        logger.info(f"[P21P8S1T1] AsyncPersistentMemory initialized with storage: {storage_path}")
        
    def _ensure_storage_directory(self):
        """Ensure storage directory exists."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (self.storage_path / "nodes").mkdir(exist_ok=True)
        (self.storage_path / "indexes").mkdir(exist_ok=True)
        (self.storage_path / "metadata").mkdir(exist_ok=True)
        
    async def add_node_async(self, node: MemoryNode) -> str:
        """
        Add a memory node asynchronously with immediate persistence.
        
        Args:
            node: Memory node to add
            
        Returns:
            str: Node ID of the added node
        """
        async with self._lock:
            try:
                # Add to cache
                self.cache[node.node_id] = node
                
                # Update indexes
                await self._update_indexes_async(node)
                
                # Persist to storage
                await self._persist_node_async(node)
                
                # Manage cache size
                await self._manage_cache_size_async()
                
                logger.info(f"[P21P8S1T1] Added node {node.node_id} with persistence")
                return node.node_id
                
            except Exception as e:
                logger.error(f"[P21P8S1T1] Failed to add node {node.node_id}: {e}")
                raise
                
    async def _update_indexes_async(self, node: MemoryNode):
        """Update memory indexes asynchronously."""
        # Agent index
        self.index[f"agent:{node.agent_id}"].append(node.node_id)
        
        # Context index
        self.index[f"context:{node.task_context}"].append(node.node_id)
        
        # Temporal index (by date)
        date_key = node.timestamp.strftime('%Y-%m-%d')
        self.temporal_index[date_key].append(node.node_id)
        
        # Type index
        node_type = node.metadata.get('type', 'general')
        self.index[f"type:{node_type}"].append(node.node_id)
        
    async def _persist_node_async(self, node: MemoryNode):
        """Persist node to storage asynchronously."""
        node_file = self.storage_path / "nodes" / f"{node.node_id}.json"
        
        # Convert node to dict for JSON serialization
        node_data = asdict(node)
        node_data['timestamp'] = node.timestamp.isoformat()
        
        async with aiofiles.open(node_file, 'w') as f:
            await f.write(json.dumps(node_data, indent=2, default=str))
            
    async def _manage_cache_size_async(self):
        """Manage cache size using LRU eviction."""
        if len(self.cache) <= self.cache_size:
            return
            
        # Simple LRU: remove oldest nodes
        sorted_nodes = sorted(self.cache.items(), key=lambda x: x[1].timestamp)
        nodes_to_remove = len(self.cache) - self.cache_size
        
        for i in range(nodes_to_remove):
            node_id, node = sorted_nodes[i]
            del self.cache[node_id]
            
        logger.info(f"[P21P8S1T1] Evicted {nodes_to_remove} nodes from cache")
        
    async def query_temporal_async(self, context: str, time_range: TimeRange) -> List[MemoryNode]:
        """
        Query memory nodes within a time range asynchronously.
        
        Args:
            context: Context to search for
            time_range: Time range for query
            
        Returns:
            List[MemoryNode]: Nodes matching the criteria
        """
        async with self._lock:
            try:
                # Get all nodes for the context
                context_nodes = self.index.get(f"context:{context}", [])
                
                # Filter by time range
                matching_nodes = []
                for node_id in context_nodes:
                    node = await self._get_node_async(node_id)
                    if node and time_range.start <= node.timestamp <= time_range.end:
                        matching_nodes.append(node)
                        
                # Sort by timestamp
                matching_nodes.sort(key=lambda x: x.timestamp)
                
                logger.info(f"[P21P8S1T1] Temporal query returned {len(matching_nodes)} nodes")
                return matching_nodes
                
            except Exception as e:
                logger.error(f"[P21P8S1T1] Failed temporal query: {e}")
                return []
                
    async def _get_node_async(self, node_id: str) -> Optional[MemoryNode]:
        """Get a node from cache or storage asynchronously."""
        # Check cache first
        if node_id in self.cache:
            return self.cache[node_id]
            
        # Load from storage
        node_file = self.storage_path / "nodes" / f"{node_id}.json"
        if not node_file.exists():
            return None
            
        try:
            async with aiofiles.open(node_file, 'r') as f:
                data = json.loads(await f.read())
                
            # Reconstruct node
            node = MemoryNode(
                node_id=data['node_id'],
                agent_id=data['agent_id'],
                task_context=data['task_context'],
                result=data['result'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                metadata=data['metadata'],
                links=data['links'],
                persistence_hash=data.get('persistence_hash')
            )
            
            # Add to cache
            self.cache[node_id] = node
            
            return node
            
        except Exception as e:
            logger.error(f"[P21P8S1T1] Failed to load node {node_id}: {e}")
            return None
            
    async def query_by_agent_async(self, agent_id: str) -> List[MemoryNode]:
        """Query all nodes by a specific agent."""
        async with self._lock:
            agent_nodes = self.index.get(f"agent:{agent_id}", [])
            nodes = []
            
            for node_id in agent_nodes:
                node = await self._get_node_async(node_id)
                if node:
                    nodes.append(node)
                    
            return sorted(nodes, key=lambda x: x.timestamp)
            
    async def query_by_type_async(self, node_type: str) -> List[MemoryNode]:
        """Query all nodes by type."""
        async with self._lock:
            type_nodes = self.index.get(f"type:{node_type}", [])
            nodes = []
            
            for node_id in type_nodes:
                node = await self._get_node_async(node_id)
                if node:
                    nodes.append(node)
                    
            return sorted(nodes, key=lambda x: x.timestamp)
            
    async def get_memory_stats_async(self) -> Dict[str, Any]:
        """Get memory statistics asynchronously."""
        async with self._lock:
            total_nodes = len(self.cache)
            total_agents = len([k for k in self.index.keys() if k.startswith('agent:')])
            total_contexts = len([k for k in self.index.keys() if k.startswith('context:')])
            
            # Calculate storage size
            storage_size = 0
            for node_file in (self.storage_path / "nodes").glob("*.json"):
                storage_size += node_file.stat().st_size
                
            return {
                "total_nodes": total_nodes,
                "total_agents": total_agents,
                "total_contexts": total_contexts,
                "cache_size": len(self.cache),
                "cache_max_size": self.cache_size,
                "storage_size_bytes": storage_size,
                "storage_path": str(self.storage_path)
            }
            
    async def cleanup_old_nodes_async(self, days_old: int = 30) -> int:
        """Clean up nodes older than specified days."""
        async with self._lock:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            removed_count = 0
            
            # Find old nodes
            old_nodes = []
            for node_id, node in self.cache.items():
                if node.timestamp < cutoff_date:
                    old_nodes.append(node_id)
                    
            # Remove from cache and storage
            for node_id in old_nodes:
                del self.cache[node_id]
                
                # Remove from storage
                node_file = self.storage_path / "nodes" / f"{node_id}.json"
                if node_file.exists():
                    node_file.unlink()
                    
                removed_count += 1
                
            # Clean up indexes
            await self._rebuild_indexes_async()
            
            logger.info(f"[P21P8S1T1] Cleaned up {removed_count} old nodes")
            return removed_count
            
    async def _rebuild_indexes_async(self):
        """Rebuild indexes from cache."""
        # Clear existing indexes
        self.index.clear()
        self.temporal_index.clear()
        
        # Rebuild from cache
        for node in self.cache.values():
            await self._update_indexes_async(node)
            
    async def export_memory_async(self, export_path: str) -> bool:
        """Export memory to file asynchronously."""
        try:
            async with self._lock:
                export_data = {
                    "export_timestamp": datetime.now(timezone.utc).isoformat(),
                    "total_nodes": len(self.cache),
                    "nodes": [asdict(node) for node in self.cache.values()]
                }
                
                async with aiofiles.open(export_path, 'w') as f:
                    await f.write(json.dumps(export_data, indent=2, default=str))
                    
                logger.info(f"[P21P8S1T1] Memory exported to {export_path}")
                return True
                
        except Exception as e:
            logger.error(f"[P21P8S1T1] Failed to export memory: {e}")
            return False
            
    async def import_memory_async(self, import_path: str) -> int:
        """Import memory from file asynchronously."""
        try:
            async with aiofiles.open(import_path, 'r') as f:
                import_data = json.loads(await f.read())
                
            imported_count = 0
            for node_data in import_data.get('nodes', []):
                try:
                    # Reconstruct node
                    node = MemoryNode(
                        node_id=node_data['node_id'],
                        agent_id=node_data['agent_id'],
                        task_context=node_data['task_context'],
                        result=node_data['result'],
                        timestamp=datetime.fromisoformat(node_data['timestamp']),
                        metadata=node_data['metadata'],
                        links=node_data['links']
                    )
                    
                    # Add node
                    await self.add_node_async(node)
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"[P21P8S1T1] Failed to import node: {e}")
                    continue
                    
            logger.info(f"[P21P8S1T1] Imported {imported_count} nodes from {import_path}")
            return imported_count
            
        except Exception as e:
            logger.error(f"[P21P8S1T1] Failed to import memory: {e}")
            return 0

async def main():
    """Main function for testing async persistent memory."""
    # Initialize memory
    memory = AsyncPersistentMemory()
    
    # Create test nodes
    test_nodes = [
        MemoryNode(
            node_id="test_1",
            agent_id="openai_gpt4o",
            task_context="analysis",
            result={"confidence": 0.9, "content": "Test analysis"},
            timestamp=datetime.now(timezone.utc),
            metadata={"type": "analysis", "priority": "high"}
        ),
        MemoryNode(
            node_id="test_2",
            agent_id="grok_3",
            task_context="review",
            result={"confidence": 0.8, "content": "Test review"},
            timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
            metadata={"type": "review", "priority": "medium"}
        )
    ]
    
    # Add nodes
    for node in test_nodes:
        await memory.add_node_async(node)
        
    # Query temporal
    time_range = TimeRange(
        start=datetime.now(timezone.utc) - timedelta(hours=2),
        end=datetime.now(timezone.utc)
    )
    
    results = await memory.query_temporal_async("analysis", time_range)
    print(f"Temporal query returned {len(results)} nodes")
    
    # Get stats
    stats = await memory.get_memory_stats_async()
    print(f"Memory stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main()) 