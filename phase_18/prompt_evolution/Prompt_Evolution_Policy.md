<!-- P18P6S1 – Prompt_Evolution_Policy.md -->
# Prompt Evolution Policy v0.1

**Phase**: 18P6 - Prompt Evolution + Logging UI  
**Document ID**: P18P6S1  
**Version**: 0.1  
**Created**: June 10, 2025 15:54 PDT  
**Author**: GitBridge MAS Integration Team  
**MAS Lite Protocol**: v2.1 Compliance  

---

## 🎯 **Executive Summary**

This document defines the **Prompt Evolution Policy** for the GitBridge SmartRepo MAS (Multi-Agent Systems) middleware. It establishes standardized prompt lifecycle phases, UID threading behavior, fallback conditions, and routing intelligence across multi-model AI systems.

The policy enables full-loop AI-assisted development with resilient error handling, confidence metadata logging, and adaptive routing for multi-model fallbacks.

---

## 📋 **Task Checklist Status**

- [x] Define prompt lifecycle phases: Init → Mutation → Fallback → Archive
- [x] Describe UID threading behavior and parent-child lineage mapping
- [x] Specify conditions for fallback triggering + MAS routing
- [x] Add flow diagram placeholder (for image or ASCII later)
- [x] Create section for "Future MAS 30 Extensions"

---

## 🔄 **Prompt Lifecycle Phases**

### **Phase 1: Initialization (INIT)**
```
Status: PROMPT_INIT
Duration: 0-5 seconds
Triggers: New task assignment, webhook payload, manual prompt
```

**Characteristics:**
- **UID Assignment**: Generate unique `prompt_uid` with timestamp and entropy
- **Context Loading**: Parse input parameters, load relevant system context
- **Agent Selection**: Determine primary AI agent based on task classification
- **Confidence Baseline**: Establish initial confidence threshold (default: 0.75)
- **Redis Logging**: Log initialization event with metadata

**Success Criteria:**
- Valid UID generated and registered
- Primary agent selected and available
- Context successfully parsed
- Initial confidence score calculated

### **Phase 2: Mutation (MUTATION)**
```
Status: PROMPT_MUTATION
Duration: 5-300 seconds
Triggers: Context evolution, refinement requests, partial failures
```

**Characteristics:**
- **Iterative Refinement**: Enhance prompt based on intermediate results
- **Context Expansion**: Add discovered dependencies and related information
- **Confidence Tracking**: Monitor confidence degradation/improvement
- **Lineage Preservation**: Maintain parent-child UID relationships
- **Performance Monitoring**: Track token usage, response time, quality metrics

**Mutation Triggers:**
1. **Low Confidence Response** (< 0.60): Trigger refinement cycle
2. **Partial Task Completion** (< 80%): Enhance context and retry
3. **Dependency Discovery**: Expand scope to include new requirements
4. **Quality Improvement**: Iterative enhancement for better results

### **Phase 3: Fallback (FALLBACK)**
```
Status: PROMPT_FALLBACK
Duration: 10-60 seconds
Triggers: Confidence threshold breach, agent failure, timeout
```

**Characteristics:**
- **Fallback Agent Selection**: Route to secondary/tertiary AI models
- **Context Preservation**: Transfer full context to fallback agent
- **Escalation Chains**: Multi-level fallback with different model capabilities
- **Confidence Recalibration**: Adjust thresholds based on fallback performance
- **Failure Analysis**: Log root cause and remediation attempts

**Fallback Conditions:**
1. **Confidence Breach**: Primary response confidence < 0.45
2. **Agent Timeout**: No response within 120 seconds
3. **Error Response**: Model returns error or malformed output
4. **Quality Failure**: Output fails validation checks
5. **Resource Exhaustion**: Token limits or rate limiting encountered

### **Phase 4: Archive (ARCHIVE)**
```
Status: PROMPT_ARCHIVE
Duration: Permanent storage
Triggers: Task completion, fallback exhaustion, manual termination
```

**Characteristics:**
- **Result Finalization**: Store final output and metadata
- **Lineage Documentation**: Complete parent-child chain records
- **Performance Analytics**: Aggregate metrics for model improvement
- **Knowledge Extraction**: Identify patterns for future optimization
- **Audit Trail**: Complete transaction log for compliance

---

## 🔗 **UID Threading Behavior**

### **UID Structure**
```
Format: {timestamp}_{entropy}_{agent_id}_{sequence}
Example: 20250610_a7f2c9_gpt4_001
```

**Components:**
- **Timestamp**: YYYYMMDD format for temporal organization
- **Entropy**: 6-character random hex for uniqueness
- **Agent ID**: Primary AI model identifier
- **Sequence**: 3-digit incremental counter for same-session prompts

### **Parent-Child Lineage Mapping**

#### **Inheritance Rules**
1. **INIT → MUTATION**: Child inherits parent context + mutations
2. **MUTATION → FALLBACK**: Child inherits full lineage + failure context
3. **FALLBACK → FALLBACK**: Chain preserves original root + all intermediate attempts
4. **Any → ARCHIVE**: Final node contains complete lineage tree

#### **Lineage Data Structure**
```json
{
  "prompt_uid": "20250610_a7f2c9_gpt4_001",
  "parent_uid": "20250610_a7f2c9_gpt4_000",
  "root_uid": "20250610_a7f2c9_gpt4_000",
  "children_uids": ["20250610_a7f2c9_claude_002"],
  "phase": "FALLBACK",
  "depth": 2,
  "lineage_path": ["root_000", "mutation_001", "fallback_002"],
  "metadata": {
    "confidence_scores": [0.85, 0.42, 0.67],
    "agents_used": ["gpt4", "gpt4", "claude"],
    "total_duration": 245,
    "success": true
  }
}
```

### **Threading Policies**

#### **Orphan Prevention**
- Every UID MUST have valid parent (except root UIDs)
- Orphaned UIDs trigger automatic lineage reconstruction
- Redis maintains parent-child index for fast lookups

#### **Cycle Detection**
- Prevent circular references in lineage chains
- Maximum depth limit: 10 levels
- Automatic termination for infinite loops

#### **Garbage Collection**
- Archive UIDs older than 30 days
- Preserve lineage metadata for analytics
- Compress and store in long-term audit logs

---

## ⚠️ **Fallback Triggering Conditions**

### **Primary Triggers**

#### **1. Confidence Threshold Breach**
```python
if response_confidence < FALLBACK_THRESHOLD:
    trigger_fallback(reason="LOW_CONFIDENCE", score=response_confidence)
```
- **Threshold**: 0.45 (configurable per task type)
- **Measurement**: Model's self-assessed confidence score
- **Action**: Route to higher-capability model

#### **2. Agent Availability Failure**
```python
if agent_timeout > MAX_RESPONSE_TIME:
    trigger_fallback(reason="AGENT_TIMEOUT", duration=agent_timeout)
```
- **Timeout**: 120 seconds for complex tasks, 30 seconds for simple
- **Retry Policy**: 2 attempts before fallback
- **Action**: Switch to alternative model

#### **3. Output Quality Validation**
```python
if validation_score < QUALITY_THRESHOLD:
    trigger_fallback(reason="QUALITY_FAILURE", validation=validation_score)
```
- **Quality Metrics**: Syntax validation, logical consistency, completeness
- **Threshold**: 0.60 minimum quality score
- **Action**: Re-prompt with enhanced context

#### **4. Resource Constraints**
```python
if token_usage > MODEL_TOKEN_LIMIT:
    trigger_fallback(reason="RESOURCE_EXHAUSTION", tokens=token_usage)
```
- **Token Limits**: Model-specific constraints
- **Rate Limiting**: API throttling protection
- **Action**: Split task or use higher-capacity model

### **Secondary Triggers**

#### **5. Context Complexity Overflow**
- Task scope exceeds single-model capabilities
- Multi-domain expertise required
- Action: Distribute to specialized agents

#### **6. Regulatory Compliance Requirements**
- Content filtering violations
- Data privacy constraints
- Action: Route to compliant model

#### **7. Performance Optimization**
- Cost optimization triggers
- Speed requirements exceed model capabilities
- Action: Route to faster/cheaper alternative

---

## 🔀 **MAS Routing Intelligence**

### **Agent Selection Matrix**

| **Task Type** | **Primary Agent** | **Fallback 1** | **Fallback 2** | **Final Resort** |
|---------------|-------------------|-----------------|-----------------|------------------|
| Code Generation | GPT-4 Turbo | Claude 3.5 | Gemini Pro | GPT-3.5 |
| Code Review | Claude 3.5 | GPT-4 | Gemini Pro | GPT-3.5 |
| Documentation | GPT-4 | Claude 3.5 | Gemini Pro | GPT-3.5 |
| Testing | GPT-4 Turbo | Claude 3.5 | Gemini Pro | Specialized Test AI |
| Debugging | Claude 3.5 | GPT-4 | Gemini Pro | GPT-3.5 |
| Architecture | GPT-4 | Claude 3.5 | Gemini Pro | Human Escalation |

### **Routing Decision Factors**

#### **Model Capabilities**
```python
def select_agent(task_type, context_complexity, performance_requirements):
    capability_matrix = {
        "code_generation": {"gpt4": 0.95, "claude": 0.90, "gemini": 0.85},
        "code_review": {"claude": 0.95, "gpt4": 0.90, "gemini": 0.80},
        "documentation": {"gpt4": 0.95, "claude": 0.85, "gemini": 0.80}
    }
    return rank_by_capability(capability_matrix[task_type])
```

#### **Cost Optimization**
- Token cost per model
- Response time requirements
- Quality vs. cost trade-offs

#### **Availability Monitoring**
- Real-time model availability
- API rate limiting status
- Response time tracking

---

## 📊 **Redis Log Expectations**

### **Event Logging Structure**

#### **Initialization Events**
```json
{
  "event_type": "PROMPT_INIT",
  "prompt_uid": "20250610_a7f2c9_gpt4_001",
  "timestamp": "2025-06-10T15:54:23.456Z",
  "task_type": "code_generation",
  "primary_agent": "gpt4",
  "initial_confidence": 0.85,
  "context_size": 1247,
  "metadata": {
    "source": "github_webhook",
    "repository": "user/project",
    "branch": "feature/new-api"
  }
}
```

#### **Mutation Events**
```json
{
  "event_type": "PROMPT_MUTATION",
  "prompt_uid": "20250610_a7f2c9_gpt4_002",
  "parent_uid": "20250610_a7f2c9_gpt4_001", 
  "timestamp": "2025-06-10T15:54:45.789Z",
  "mutation_reason": "context_expansion",
  "confidence_change": {"from": 0.85, "to": 0.78},
  "context_delta": {
    "added_dependencies": ["numpy", "pandas"],
    "removed_assumptions": ["simple_data_structure"]
  }
}
```

#### **Fallback Events**
```json
{
  "event_type": "PROMPT_FALLBACK",
  "prompt_uid": "20250610_a7f2c9_claude_003",
  "parent_uid": "20250610_a7f2c9_gpt4_002",
  "root_uid": "20250610_a7f2c9_gpt4_001",
  "timestamp": "2025-06-10T15:55:12.345Z",
  "fallback_reason": "LOW_CONFIDENCE",
  "original_confidence": 0.42,
  "fallback_agent": "claude3.5",
  "escalation_level": 1,
  "lineage_depth": 3
}
```

### **Redis Channel Organization**

#### **Channel Structure**
```
mas:prompt:events:init        - Initialization events
mas:prompt:events:mutation    - Mutation events  
mas:prompt:events:fallback    - Fallback events
mas:prompt:events:archive     - Archive events
mas:prompt:lineage:{uid}      - Individual UID lineage
mas:prompt:metrics:hourly     - Aggregated metrics
```

#### **Index Keys**
```
mas:prompt:index:by_time      - Chronological ordering
mas:prompt:index:by_agent     - Agent-specific lookup
mas:prompt:index:by_status    - Status-based filtering
mas:prompt:index:by_root      - Root UID grouping
```

---

## 📈 **Flow Diagram Placeholder**

```
[ASCII Flow Diagram - To Be Enhanced with Visual Tool]

INIT Phase:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Task Input  │───▶│ UID Generate│───▶│Agent Select │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │Redis Log    │    │Confidence   │
                   │INIT Event   │    │Baseline     │
                   └─────────────┘    └─────────────┘

MUTATION Phase:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Context Expnd│───▶│Child UID    │───▶│Refinement   │
└─────────────┘    │Generation   │    │Iteration    │
       ▲           └─────────────┘    └─────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼                   
                   ┌─────────────┐    
                   │Confidence   │    
                   │Monitoring   │    
                   └─────────────┘    

FALLBACK Phase:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Trigger Check│───▶│Fallback UID │───▶│Agent Switch │
└─────────────┘    │Generation   │    └─────────────┘
       ▲           └─────────────┘            │
       │                   │                 │
   Confidence < 0.45       ▼                 ▼
       │           ┌─────────────┐    ┌─────────────┐
       │           │Lineage      │    │Context      │
       │           │Preservation │    │Transfer     │
       │           └─────────────┘    └─────────────┘
       │                   │                 │
       └───────────────────┼─────────────────┘
                           ▼
                   ┌─────────────┐
                   │Redis Log    │
                   │FALLBACK     │
                   └─────────────┘

ARCHIVE Phase:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Task Complete│───▶│Result Store │───▶│Lineage Doc  │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │Analytics    │    │Audit Trail  │
                   │Extraction   │    │Completion   │
                   └─────────────┘    └─────────────┘
```

---

## 🚀 **Future MAS 30 Extensions**

### **Advanced Capabilities Pipeline**

#### **1. Multi-Model Ensemble Routing**
```
Planned: Q3 2025
- Parallel execution across multiple models
- Consensus-based result aggregation  
- Confidence-weighted output synthesis
- Real-time model performance benchmarking
```

#### **2. Adaptive Learning System**
```
Planned: Q4 2025
- Historical performance analysis
- Dynamic threshold adjustment
- Personalized routing preferences
- Continuous model evaluation
```

#### **3. Federated MAS Coordination**
```
Planned: Q1 2026
- Cross-organization model sharing
- Distributed fallback networks
- Privacy-preserving collaboration
- Global model availability pools
```

#### **4. Autonomous Quality Assurance**
```
Planned: Q2 2026
- Self-improving validation systems
- Automated test case generation
- Predictive failure detection
- Quality metric evolution
```

### **Integration Roadmap**

#### **Phase 19: Enhanced Routing (Q3 2025)**
- Graph-based fallback networks
- Cost-performance optimization
- Regional model deployment

#### **Phase 20: Intelligent Caching (Q4 2025)**
- Semantic prompt similarity matching
- Context-aware cache invalidation
- Distributed cache synchronization

#### **Phase 21: Predictive Scaling (Q1 2026)**
- Load prediction algorithms
- Proactive resource allocation
- Demand-based model selection

---

## 📚 **References & Compliance**

### **MAS Lite Protocol v2.1**
- **Logging Standards**: Structured JSON event format
- **Error Handling**: Standardized failure categorization
- **Audit Requirements**: Complete transaction traceability
- **Performance Metrics**: Response time, confidence, success rate

### **Related Documentation**
- `P18P5S2_AUDIT_VIEW_REPORT.md` - Audit trail specifications
- `P18P5S3_FAILURE_HEATMAP_REPORT.md` - Failure pattern analysis
- `P18P5S5_FALLBACK_SUMMARY.md` - Fallback implementation details
- `P18P5S6_API_EXPORTER_COMPLETION.md` - Front-end integration

### **Configuration Management**
- Environment-specific thresholds
- Model-specific parameters
- Cost optimization settings
- Compliance requirements

---

## 🔧 **Implementation Notes**

### **Development Priorities**
1. **Core UID Threading** - Fundamental lineage tracking
2. **Redis Integration** - Event logging and retrieval
3. **Fallback Logic** - Reliable model switching
4. **UI Components** - Real-time monitoring dashboard

### **Testing Strategy**
- Unit tests for UID generation and lineage
- Integration tests for Redis logging
- End-to-end fallback scenario validation
- Performance benchmarking under load

### **Monitoring & Alerting**
- Real-time confidence tracking
- Fallback rate monitoring
- Model availability dashboards
- Cost tracking and optimization

---

*Document Version: 0.1*  
*Last Updated: June 10, 2025 15:54 PDT*  
*Next Review: June 17, 2025*  
*MAS Lite Protocol v2.1 Compliance: VERIFIED* 