# P21P2 Task Fragmenter - Refactoring Suggestions
**Phase:** GBP21  
**Part:** P21P7  
**Step:** P21P7S1  
**Task:** P21P7S1T1 - Task Fragmenter Refactoring

## Current State Analysis
The `P21P2_task_fragmenter.py` module is well-structured but could benefit from enhanced modularity and async support for Phase 22 arbitration logic.

## Recommended Refactoring

### 1. Plugin Architecture
```python
# Proposed structure:
class FragmentationStrategy(ABC):
    @abstractmethod
    def fragment_task(self, prompt: str, task_type: str, domain: str, master_task_id: str) -> List[Subtask]:
        pass

class SimpleFragmentationStrategy(FragmentationStrategy):
    def fragment_task(self, prompt: str, task_type: str, domain: str, master_task_id: str) -> List[Subtask]:
        # Current simple fragmentation logic
        pass

class StructuredFragmentationStrategy(FragmentationStrategy):
    def fragment_task(self, prompt: str, task_type: str, domain: str, master_task_id: str) -> List[Subtask]:
        # Current structured fragmentation logic
        pass

class ComprehensiveFragmentationStrategy(FragmentationStrategy):
    def fragment_task(self, prompt: str, task_type: str, domain: str, master_task_id: str) -> List[Subtask]:
        # Current comprehensive fragmentation logic
        pass
```

### 2. Async Support
```python
class AsyncTaskFragmenter:
    async def fragment_task_async(
        self,
        prompt: str,
        task_type: str = "general",
        domain: str = "general",
        coordination_strategy: str = "hierarchical"
    ) -> TaskFragment:
        # Async implementation with event loop integration
        pass

    async def assign_agents_to_subtasks_async(self, task_fragment: TaskFragment) -> Dict[str, str]:
        # Async agent assignment with concurrent processing
        pass

    async def dispatch_subtasks_async(self, task_fragment: TaskFragment) -> Dict[str, Any]:
        # Async dispatch with webhook integration
        pass
```

### 3. Enhanced Logging with Metadata
```python
def _log_task_fragmentation(self, task_fragment: TaskFragment, metadata: Dict[str, Any]):
    logger.info(
        "[P21P2S1T1] Task fragmented",
        extra={
            "agent_id": "task_fragmenter",
            "task_id": task_fragment.master_task_id,
            "subtask_count": len(task_fragment.subtasks),
            "strategy": task_fragment.coordination_strategy,
            "confidence": self._calculate_fragmentation_confidence(task_fragment),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata
        }
    )
```

### 4. Hook System for Custom Logic
```python
class TaskFragmenterHooks:
    def __init__(self):
        self.pre_fragmentation_hooks: List[Callable] = []
        self.post_fragmentation_hooks: List[Callable] = []
        self.agent_assignment_hooks: List[Callable] = []

    def add_pre_fragmentation_hook(self, hook: Callable):
        self.pre_fragmentation_hooks.append(hook)

    def add_post_fragmentation_hook(self, hook: Callable):
        self.post_fragmentation_hooks.append(hook)

    def add_agent_assignment_hook(self, hook: Callable):
        self.agent_assignment_hooks.append(hook)
```

### 5. Configuration Management
```python
@dataclass
class FragmenterConfig:
    max_subtasks_per_task: int = 10
    min_confidence_threshold: float = 0.7
    enable_async_processing: bool = True
    max_concurrent_assignments: int = 5
    fragmentation_strategies: Dict[str, Type[FragmentationStrategy]] = field(default_factory=dict)
    hooks: TaskFragmenterHooks = field(default_factory=TaskFragmenterHooks)
```

## Implementation Priority
1. **High Priority:** Plugin architecture and async support
2. **Medium Priority:** Enhanced logging and metadata
3. **Low Priority:** Hook system and configuration management

## Benefits for Phase 22
- **Arbitration Logic:** Async support enables concurrent agent evaluation
- **Dynamic Strategy:** Plugin architecture allows runtime strategy selection
- **Monitoring:** Enhanced logging supports real-time performance tracking
- **Extensibility:** Hook system enables custom business logic integration

## Migration Strategy
1. Create new async methods alongside existing sync methods
2. Gradually migrate to plugin architecture
3. Add hooks incrementally
4. Update configuration management last

## Testing Recommendations
- Unit tests for each fragmentation strategy
- Integration tests for async workflows
- Performance tests for concurrent processing
- Hook system validation tests 