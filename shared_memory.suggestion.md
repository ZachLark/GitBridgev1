# Shared Memory Layer - Refactoring Suggestions
**Phase:** GBP21  
**Part:** P21P7  
**Step:** P21P7S1  
**Task:** P21P7S1T3 - Shared Memory Refactoring

## Current State Analysis
The `shared_memory.py` module provides basic memory functionality but needs async support, enhanced indexing, and optimization for Phase 22 arbitration logic.

## Recommended Refactoring

### 1. Async Memory Operations
```python
class AsyncSharedMemoryGraph:
    def __init__(self):
        self.nodes: Dict[str, MemoryNode] = {}
        self.agent_index: Dict[str, List[str]] = {}
        self.context_index: Dict[str, List[str]] = {}
        self.timestamp_index: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()

    async def add_node_async(
        self,
        agent_id: str,
        task_context: str,
        result: Any,
        metadata: Optional[Dict[str, Any]] = None,
        links: Optional[List[str]] = None
    ) -> str:
        async with self._lock:
            return self.add_node(agent_id, task_context, result, metadata, links)

    async def recall_context_async(self, agent_id: str, task_context: str) -> List[MemoryNode]:
        async with self._lock:
            return self.recall_context(agent_id, task_context)

    async def link_nodes_async(self, from_node_id: str, to_node_id: str) -> None:
        async with self._lock:
            self.link_nodes(from_node_id, to_node_id)
```

### 2. Enhanced Indexing System
```python
class MemoryIndexManager:
    def __init__(self):
        self.agent_index: Dict[str, List[str]] = defaultdict(list)
        self.context_index: Dict[str, List[str]] = defaultdict(list)
        self.timestamp_index: Dict[str, List[str]] = defaultdict(list)
        self.confidence_index: Dict[str, List[str]] = defaultdict(list)
        self.type_index: Dict[str, List[str]] = defaultdict(list)

    def add_to_indexes(self, node_id: str, node: MemoryNode):
        # Add to all relevant indexes
        self.agent_index[node.agent_id].append(node_id)
        self.context_index[node.task_context].append(node_id)
        self.timestamp_index[node.timestamp.strftime('%Y-%m-%d')].append(node_id)
        self.confidence_index[f"{node.result.get('confidence_score', 0):.1f}"].append(node_id)
        self.type_index[node.result.get('type', 'unknown')].append(node_id)

    def query_by_multiple_criteria(
        self,
        agent_ids: Optional[List[str]] = None,
        contexts: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        confidence_threshold: Optional[float] = None
    ) -> List[str]:
        # Complex query across multiple indexes
        pass
```

### 3. Memory Optimization and Caching
```python
class MemoryCache:
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, MemoryNode] = {}
        self.max_size = max_size
        self.access_count: Dict[str, int] = defaultdict(int)

    def get(self, node_id: str) -> Optional[MemoryNode]:
        if node_id in self.cache:
            self.access_count[node_id] += 1
            return self.cache[node_id]
        return None

    def put(self, node_id: str, node: MemoryNode):
        if len(self.cache) >= self.max_size:
            # LRU eviction
            least_used = min(self.access_count.items(), key=lambda x: x[1])[0]
            del self.cache[least_used]
            del self.access_count[least_used]
        
        self.cache[node_id] = node
        self.access_count[node_id] = 1

class OptimizedSharedMemoryGraph:
    def __init__(self):
        self.nodes: Dict[str, MemoryNode] = {}
        self.index_manager = MemoryIndexManager()
        self.cache = MemoryCache()
        self.persistent_storage = MemoryPersistentStorage()

    async def add_node_optimized(
        self,
        agent_id: str,
        task_context: str,
        result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        node_id = await self.add_node_async(agent_id, task_context, result, metadata)
        
        # Update indexes
        node = self.nodes[node_id]
        self.index_manager.add_to_indexes(node_id, node)
        
        # Cache frequently accessed nodes
        if self._should_cache(node):
            self.cache.put(node_id, node)
            
        return node_id

    def _should_cache(self, node: MemoryNode) -> bool:
        # Determine if node should be cached based on access patterns
        return node.result.get('confidence_score', 0) > 0.8
```

### 4. Memory Bundling and Context Management
```python
@dataclass
class MemoryBundle:
    bundle_id: str
    task_id: str
    agent_ids: List[str]
    contexts: List[str]
    nodes: List[str]
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

class MemoryBundleManager:
    def __init__(self):
        self.bundles: Dict[str, MemoryBundle] = {}
        self.task_to_bundle: Dict[str, str] = {}

    def create_bundle(
        self,
        task_id: str,
        agent_ids: List[str],
        contexts: List[str],
        nodes: List[str]
    ) -> str:
        bundle_id = f"bundle_{len(self.bundles) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        bundle = MemoryBundle(
            bundle_id=bundle_id,
            task_id=task_id,
            agent_ids=agent_ids,
            contexts=contexts,
            nodes=nodes,
            created_at=datetime.now(timezone.utc)
        )
        
        self.bundles[bundle_id] = bundle
        self.task_to_bundle[task_id] = bundle_id
        return bundle_id

    def get_bundle_by_task(self, task_id: str) -> Optional[MemoryBundle]:
        bundle_id = self.task_to_bundle.get(task_id)
        return self.bundles.get(bundle_id) if bundle_id else None

    def get_bundle_by_context(self, context: str) -> List[MemoryBundle]:
        return [bundle for bundle in self.bundles.values() if context in bundle.contexts]
```

### 5. Enhanced Logging with Memory Metrics
```python
class MemoryMetrics:
    def __init__(self):
        self.total_nodes: int = 0
        self.total_agents: int = 0
        self.total_contexts: int = 0
        self.cache_hit_rate: float = 0.0
        self.query_performance: List[float] = []
        self.memory_usage: int = 0

    def update_metrics(self, operation: str, duration: float, success: bool):
        if operation == "query":
            self.query_performance.append(duration)
        # Update other metrics as needed

    def get_performance_report(self) -> Dict[str, Any]:
        return {
            "total_nodes": self.total_nodes,
            "total_agents": self.total_agents,
            "total_contexts": self.total_contexts,
            "cache_hit_rate": self.cache_hit_rate,
            "avg_query_time": sum(self.query_performance) / len(self.query_performance) if self.query_performance else 0,
            "memory_usage_mb": self.memory_usage / (1024 * 1024)
        }

def _log_memory_operation(self, operation: str, node_id: str, metadata: Dict[str, Any]):
    logger.info(
        f"[P21P5S1T1] Memory {operation}",
        extra={
            "agent_id": "shared_memory",
            "operation": operation,
            "node_id": node_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata
        }
    )
```

### 6. Persistent Storage Integration
```python
class MemoryPersistentStorage:
    def __init__(self, storage_path: str = "memory_storage"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    async def save_node_async(self, node_id: str, node: MemoryNode):
        file_path = os.path.join(self.storage_path, f"{node_id}.json")
        node_data = {
            'node_id': node.node_id,
            'agent_id': node.agent_id,
            'task_context': node.task_context,
            'result': node.result,
            'timestamp': node.timestamp.isoformat(),
            'metadata': node.metadata,
            'links': node.links
        }
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(node_data, indent=2))

    async def load_node_async(self, node_id: str) -> Optional[MemoryNode]:
        file_path = os.path.join(self.storage_path, f"{node_id}.json")
        if not os.path.exists(file_path):
            return None
            
        async with aiofiles.open(file_path, 'r') as f:
            data = json.loads(await f.read())
            
        return MemoryNode(
            node_id=data['node_id'],
            agent_id=data['agent_id'],
            task_context=data['task_context'],
            result=data['result'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data['metadata'],
            links=data['links']
        )
```

### 7. Configuration Management
```python
@dataclass
class MemoryConfig:
    enable_async_operations: bool = True
    enable_caching: bool = True
    cache_max_size: int = 1000
    enable_persistent_storage: bool = True
    storage_path: str = "memory_storage"
    enable_metrics: bool = True
    enable_bundling: bool = True
    max_nodes_per_bundle: int = 50
    index_update_strategy: str = "immediate"  # immediate, batch, lazy
```

## Implementation Priority
1. **High Priority:** Async operations and enhanced indexing
2. **Medium Priority:** Memory optimization and bundling
3. **Low Priority:** Persistent storage and advanced metrics

## Benefits for Phase 22
- **Arbitration Logic:** Async support enables concurrent memory operations
- **Performance:** Enhanced indexing and caching improve query performance
- **Scalability:** Memory bundling supports large-scale collaboration
- **Reliability:** Persistent storage ensures data durability

## Migration Strategy
1. Implement async methods alongside existing sync methods
2. Add enhanced indexing incrementally
3. Integrate caching and optimization
4. Add memory bundling capabilities
5. Implement persistent storage

## Testing Recommendations
- Unit tests for async memory operations
- Performance tests for indexing and caching
- Integration tests for memory bundling
- Persistence tests for storage operations
- Load testing for concurrent access 