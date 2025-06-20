# P21P3 Collaborative Composer - Refactoring Suggestions
**Phase:** GBP21  
**Part:** P21P7  
**Step:** P21P7S1  
**Task:** P21P7S1T2 - Composer Refactoring

## Current State Analysis
The `P21P3_composer.py` module provides solid conflict resolution and composition capabilities but needs async support and enhanced modularity for Phase 22 arbitration logic.

## Recommended Refactoring

### 1. Conflict Resolution Plugin System
```python
class ConflictResolver(ABC):
    @abstractmethod
    def resolve_conflicts(self, subtask_results: List[SubtaskResult], conflicts: List[ConflictInfo]) -> List[SubtaskResult]:
        pass

class MetaEvaluatorResolver(ConflictResolver):
    def resolve_conflicts(self, subtask_results: List[SubtaskResult], conflicts: List[ConflictInfo]) -> List[SubtaskResult]:
        # Use meta-evaluator for conflict resolution
        pass

class ArbitrationResolver(ConflictResolver):
    def resolve_conflicts(self, subtask_results: List[SubtaskResult], conflicts: List[ConflictInfo]) -> List[SubtaskResult]:
        # Use arbitration logic for conflict resolution
        pass

class SynthesisResolver(ConflictResolver):
    def resolve_conflicts(self, subtask_results: List[SubtaskResult], conflicts: List[ConflictInfo]) -> List[SubtaskResult]:
        # Use synthesis approach for conflict resolution
        pass
```

### 2. Async Composition Pipeline
```python
class AsyncCollaborativeComposer:
    async def compose_results_async(
        self,
        master_task_id: str,
        subtask_results: List[SubtaskResult],
        composition_strategy: str = "hierarchical"
    ) -> CompositionResult:
        # Async composition with concurrent conflict resolution
        pass

    async def detect_conflicts_async(self, subtask_results: List[SubtaskResult]) -> List[ConflictInfo]:
        # Async conflict detection with parallel processing
        pass

    async def resolve_conflicts_async(
        self,
        subtask_results: List[SubtaskResult],
        conflicts: List[ConflictInfo]
    ) -> List[SubtaskResult]:
        # Async conflict resolution
        pass
```

### 3. Enhanced Attribution Tracking
```python
@dataclass
class AttributionMetadata:
    agent_id: str
    agent_name: str
    contribution_percentage: float
    confidence_weight: float
    quality_score: float
    timestamp: datetime
    task_context: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class AttributionTracker:
    def __init__(self):
        self.attribution_history: List[AttributionMetadata] = []
        self.agent_performance_tracker: Dict[str, List[float]] = defaultdict(list)

    def track_contribution(self, contribution: AgentContribution, final_composition: str):
        # Track detailed attribution information
        pass

    def calculate_contribution_percentage(self, agent_id: str, final_composition: str) -> float:
        # Calculate percentage of final composition attributed to agent
        pass
```

### 4. Composition Strategy Plugins
```python
class CompositionStrategy(ABC):
    @abstractmethod
    def compose_content(self, results: List[SubtaskResult]) -> str:
        pass

class HierarchicalCompositionStrategy(CompositionStrategy):
    def compose_content(self, results: List[SubtaskResult]) -> str:
        # Current hierarchical composition logic
        pass

class SequentialCompositionStrategy(CompositionStrategy):
    def compose_content(self, results: List[SubtaskResult]) -> str:
        # Current sequential composition logic
        pass

class SyntheticCompositionStrategy(CompositionStrategy):
    def compose_content(self, results: List[SubtaskResult]) -> str:
        # Current synthetic composition logic
        pass

class AdaptiveCompositionStrategy(CompositionStrategy):
    def compose_content(self, results: List[SubtaskResult]) -> str:
        # Adaptive strategy based on result characteristics
        pass
```

### 5. Enhanced Logging with AI Origin Tags
```python
def _log_composition_result(self, composition: CompositionResult, metadata: Dict[str, Any]):
    logger.info(
        "[P21P3S1T1] Composition completed",
        extra={
            "agent_id": "collaborative_composer",
            "master_task_id": composition.master_task_id,
            "subtask_count": len(composition.attribution_map),
            "confidence_score": composition.confidence_score,
            "conflicts_resolved": len(composition.conflict_resolution_log),
            "composition_strategy": composition.composition_strategy,
            "ai_origin_tags": self._extract_ai_origin_tags(composition),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata
        }
    )

def _extract_ai_origin_tags(self, composition: CompositionResult) -> List[str]:
    # Extract AI origin tags from attribution map
    tags = []
    for agent_ids in composition.attribution_map.values():
        tags.extend(agent_ids)
    return list(set(tags))
```

### 6. Quality Assurance Pipeline
```python
class QualityAssurancePipeline:
    def __init__(self):
        self.quality_checks: List[Callable] = []
        self.quality_thresholds: Dict[str, float] = {}

    def add_quality_check(self, check: Callable):
        self.quality_checks.append(check)

    def run_quality_checks(self, composition: CompositionResult) -> Dict[str, Any]:
        results = {}
        for check in self.quality_checks:
            check_name = check.__name__
            result = check(composition)
            results[check_name] = result
        return results

    def check_confidence_threshold(self, composition: CompositionResult) -> bool:
        return composition.confidence_score >= self.quality_thresholds.get('confidence', 0.7)

    def check_attribution_completeness(self, composition: CompositionResult) -> bool:
        return len(composition.attribution_map) > 0
```

### 7. Configuration Management
```python
@dataclass
class ComposerConfig:
    default_composition_strategy: str = "hierarchical"
    conflict_resolution_method: str = "meta_evaluator"
    enable_async_processing: bool = True
    quality_assurance_enabled: bool = True
    attribution_tracking_enabled: bool = True
    max_concurrent_conflict_resolution: int = 3
    composition_strategies: Dict[str, Type[CompositionStrategy]] = field(default_factory=dict)
    conflict_resolvers: Dict[str, Type[ConflictResolver]] = field(default_factory=dict)
    quality_pipeline: QualityAssurancePipeline = field(default_factory=QualityAssurancePipeline)
```

## Implementation Priority
1. **High Priority:** Async composition pipeline and conflict resolution plugins
2. **Medium Priority:** Enhanced attribution tracking and quality assurance
3. **Low Priority:** Configuration management and advanced composition strategies

## Benefits for Phase 22
- **Arbitration Logic:** Async support enables real-time conflict resolution
- **Dynamic Resolution:** Plugin system allows adaptive conflict resolution strategies
- **Quality Control:** Quality assurance pipeline ensures output standards
- **Attribution:** Enhanced tracking supports detailed performance analysis

## Migration Strategy
1. Implement async methods alongside existing sync methods
2. Add conflict resolution plugins incrementally
3. Integrate quality assurance pipeline
4. Enhance attribution tracking
5. Update configuration management

## Testing Recommendations
- Unit tests for each composition strategy
- Integration tests for async conflict resolution
- Quality assurance validation tests
- Attribution tracking accuracy tests
- Performance tests for concurrent processing 