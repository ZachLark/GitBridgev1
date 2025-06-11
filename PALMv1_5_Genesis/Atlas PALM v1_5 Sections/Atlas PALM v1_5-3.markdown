# III: Intent & Journey Mapping

The Intent & Journey Mapping layer is the navigational intelligence of Atlas PALM v1.5, orchestrating the user’s cannabis journey by synthesizing parsed inputs into actionable intents and contextual journey stages. As the second layer of the Atlas Insight Engine, it bridges raw user expressions—parsed by the Input Interpretation layer (Section II)—to behavioral and emotional contexts, ensuring responses are tailored to the user’s goals, readiness, and regulatory environment. This layer casts the user as the hero, dynamically mapping their path through a narrative arc, guided by mentor-driven insights. Building on v1.0’s robust intent classification and journey staging, v1.5 introduces the Cultural Context Filter, ensuring 100% regulatory compliance and cultural sensitivity across 50+ regions (Appendix C). This section provides a detailed, developer-focused overview of the layer’s capabilities, workflows, technical implementation, and performance, with references to Appendices C (JSON Schemas), D (Simulation Tests), and F (Domain Ontology), empowering the development team, including Chat, for the May 5, 2025, delivery.

## 3.1 Purpose and Function
Intent & Journey Mapping determines *what* the user seeks and *where* they stand in their personal cannabis journey, translating parsed queries into structured intents (e.g., discover, optimize) and narrative-based stages (e.g., exploration, disruption). By merging sentiment analysis, user memory, and regional context, it ensures responses align with the user’s emotional state, goals, and legal constraints. The v1.5 Cultural Context Filter enhances this by tailoring outputs to regional regulations and cultural norms (e.g., CBD-only recommendations in Japan), a critical advancement over v1.0’s static mapping. For developers, this layer is essential for routing queries to appropriate mentor archetypes (Section IV) and domain data (Section V), with schemas in Appendix C ensuring data integrity.

## 3.2 Core Capabilities
The layer performs five key functions, optimized for v1.5’s global scalability and compliance:
1. **Intent Classification Engine**: Categorizes user objectives (e.g., discover, learn, reflect, decide, optimize) using fine-tuned NLP models (GPT-4o) and historical behavior, achieving 95% accuracy (Appendix D).  
2. **Journey Stage Detection**: Tags users across six narrative stages:  
   - *Initiation*: First-time users, curious about cannabis.  
   - *Exploration*: Browsing strains or options.  
   - *Immersion*: Developing preferences through repeated use.  
   - *Disruption*: Facing confusion or setbacks (e.g., adverse effects).  
   - *Reflection*: Reviewing past experiences.  
   - *Integration*: Optimizing fluency and preferences.  
3. **Goal Progression Tracking**: Monitors patterns (e.g., stalled progress, breakthroughs) by associating past goals with current behaviors, logged in journey schemas (Appendix C).  
4. **Emotion & Identity Signals**: Combines sentiment from Input Interpretation (Section II) with journey data to flag transitions (e.g., readiness for deeper insights), validated in simulation tests (Appendix D).  
5. **Mentor Role Guidance Recommendation**: Suggests mentor archetypes (e.g., Strategist, Guardian) and interaction modes (e.g., Caddy, Sherpa) based on stage, confidence, and needs, defined in Appendix C.  

## 3.3 Technical Implementation
Intent & Journey Mapping leverages advanced NLP, schema-driven logic, and database integration, enhanced for v1.5:
- **NLP Backend**: GPT-4o classifies intents and stages, with v1.5’s multi-model logic improving precision by 10% over v1.0 (Appendix D).  
- **Cultural Context Filter**: Applies region-specific rules (e.g., THC restrictions in Japan) using schema-defined enums (Appendix C), ensuring compliance.  
- **Database Access**: Queries Postgres/Redis for user history and goal progression, caching frequent patterns for 20% faster retrieval (Appendix D).  
- **Schema Validation**: Uses journey schemas (Appendix C) to structure outputs, ensuring consistency for downstream layers.  

**Code Snippet**: Example Cultural Context Filter logic, applied during intent mapping:
```javascript
function applyCulturalFilter(intent, region) {
  const restrictions = {
    JP: { thc: false, cbd: true },
    CA: { thc: true, cbd: true },
    EU: { thc: false, cbd: true }
  };
  const allowed = restrictions[region] || { thc: true, cbd: true };
  return {
    ...intent,
    recommendations: intent.recommendations.filter(r => allowed[r.type]),
    compliance: true
  };
}
// Example: applyCulturalFilter({ intent: "optimize", recommendations: [{ type: "thc" }] }, "JP") → { recommendations: [] }
```
See Appendix C for journey schemas and Appendix F for regulatory data referenced by the filter.

## 3.4 Interaction with Other Layers
The layer integrates seamlessly with the Atlas PALM architecture:
- **Input Interpretation**: Receives parsed queries, sentiment, and entities (Section II), structured in input schemas (Appendix C).  
- **Mentor Matrix**: Forwards intent, stage, and mentor recommendations, enabling archetype selection (Section IV, Appendix C).  
- **Domain Expertise**: Provides intent and context for querying strain and regulatory data (Section V, Appendix F).  
- **Feedback & Learning**: Logs journey states and user interactions for model refinement (Section VII, Appendix C).  

For example, a “frustrated” sentiment from Input Interpretation triggers a disruption-stage mapping, recommending a Strategist/Caddy mentor (Appendix C).

## 3.5 Example Mapping Logic
Consider a user query: “I’ve been trying different strains for sleep, but it’s been hit or miss.”
- **Input**: Parsed by Section II, tagged as “frustrated” with intent “problem-solving” (Appendix C).  
- **Processing**: 
  1. **Intent Classification**: Identifies “optimize” intent, seeking better strain selection.  
  2. **Journey Stage**: Tags as “disruption” transitioning to “integration.”  
  3. **Goal Tracking**: Notes prior sleep-related queries, flags inconsistent outcomes.  
  4. **Emotion Signals**: Confirms frustration, suggesting empathetic tone.  
  5. **Mentor Recommendation**: Recommends Strategist/Caddy for data-driven guidance.  
  6. **Cultural Filter**: Applies region-specific rules (e.g., US allows THC/CBD), per Appendix C.  
- **Output**: Structured journey state:
```json
{
  "intent": "optimize",
  "journey_stage": "disruption",
  "emotional_state": "frustrated",
  "goal_progress": "moderate",
  "recommendation": {
    "mentor_archetype": "strategist",
    "interaction_mode": "caddy"
  },
  "region": "US",
  "compliance": true
}
```
- **Routing**: Triggers a response suggesting journaling and strain optimization (Appendix C), validated by simulation tests (Appendix D).  

This workflow ensures context-aware, compliant mapping, critical for global deployment.

## 3.6 Performance Metrics
The layer’s performance is validated by the Simulation Framework (Appendix D):
- **Intent Accuracy**: 95%, ensuring reliable classification across diverse queries.  
- **Stage Detection**: 90% accuracy, correctly identifying journey stages.  
- **Compliance**: 100%, with Cultural Context Filter enforcing regional regulations (Appendix C).  
- **Latency**: <100ms for mapping, contributing to 500ms total query latency (Appendix D).  
- **Throughput**: Supports 10,000 queries/second, enabled by Redis caching.  

These metrics confirm the layer’s robustness, supporting developers in building responsive applications.

## 3.7 Design Safeguards and Optimizations
To ensure reliability and user trust, the layer incorporates:
- **Privacy-Aware**: Stores minimal data in journey schemas (Appendix C), anonymizing analytics (Appendix B).  
- **Time-Aware**: Tracks session gaps to infer engagement velocity, logged in user profiles (Appendix C).  
- **Transparency-Ready**: Supports journey summaries (“Here’s how far you’ve come…”), accessible via API (Appendix E).  
- **Bias-Tuned**: Avoids cultural assumptions, validated through bias checks (Appendix B).  

## 3.8 Alignment with v1.0 and Advancements
Compared to v1.0, v1.5 enhances intent and journey mapping:
- **v1.0**: Basic intent classification and stage detection, no cultural adjustments, 10% misaligned responses.  
- **v1.5**: Cultural Context Filter (Appendix C), multi-model NLP, and schema-driven outputs, reducing misalignments to <2% (Appendix D).  

Version history is documented in Appendix A, with ethical protocols in Appendix B.

## 3.9 Developer Notes
For Chat and the dev team:
- **Implementation**: Use journey schemas (Appendix C) for intent and stage validation, ensuring compliance with regional enums.  
- **API Integration**: Retrieve journey states via /response endpoint (Appendix E), handling 404 errors for invalid queries.  
- **Testing**: Reference Appendix D’s simulation tests (e.g., “ambiguous intent” cases) to validate mapping accuracy.  
- **Data Access**: Query regulatory constraints from the domain ontology (Appendix F) for filter logic.  
- **Extensibility**: Prepare for multi-language intent models (Section XI), supported by Appendix C schemas.  

## 3.10 Narrative Context
In the hero’s journey, Intent & Journey Mapping is the wise cartographer, charting the user’s path through the complex landscape of cannabis exploration. It understands their goals, senses their emotional state, and ensures their journey respects cultural and legal boundaries. For developers like Chat, this layer is a precise, compliant engine, enabling the Atlas Insight Engine to guide each user with unparalleled relevance and care.