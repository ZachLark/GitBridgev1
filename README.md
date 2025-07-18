# GitBridge Trust Graph Engine (GBP23)

## Description

This repository contains the implementation for **GitBridge Trust Graph Engine (GBP23)**, a high-performance trust relationship management system developed as part of the GitBridge SmartRepo ecosystem. This project follows GitBridge development standards and integrates with the broader GitBridge ecosystem for automated repository management and intelligent development workflows.

## 🚀 **Key Features**

### **Trust Graph Engine (GBP23)**
- **High-Performance Trust Management**: Track and analyze trust relationships between agents
- **Multiple Performance Modes**: Standard, High-Performance, and Batch operations
- **MAS Lite Protocol v2.1 Compliance**: Full protocol compliance with authentication, error handling, logging, and task delegation
- **Real-time Trust Analysis**: Dynamic trust scoring with confidence metrics
- **Behavioral Modeling**: Advanced agent behavior analysis and prediction
- **Trust Visualization**: Interactive trust network visualization and analytics
- **Comprehensive Metrics**: Detailed trust metrics and performance monitoring

### **Performance Highlights**
- **Standard Mode**: ~51 trust updates/second (full validation/logging)
- **High-Performance Mode**: >200,000 trust updates/second (minimal validation)
- **Batch Operations**: >290,000 trust updates/second (bulk processing)
- **Memory Efficient**: Optimized data structures and garbage collection
- **Thread Safe**: Concurrent operations with minimal lock contention

### **Core Components**
- **Trust Graph Engine** (`trust_graph.py`): Core directed graph with weighted edges
- **Behavior Model** (`behavior_model.py`): Agent behavior analysis and prediction
- **Trust Analyzer** (`trust_analyzer.py`): Trust relationship analysis and insights
- **Trust Visualizer** (`trust_visualizer.py`): Interactive network visualization
- **Trust Metrics** (`trust_metrics.py`): Comprehensive metrics and monitoring

## Project Metadata

| Field | Value |
|-------|-------|
| **Phase** | `GBP23` |
| **Component** | `Trust Graph Engine` |
| **Branch Name** | `feature/trust-graph-gbp23` |
| **Branch Type** | `feature` |
| **Creator** | GitBridge SmartRepo System |
| **Created** | June 19, 2025 |
| **Status** | `active` |
| **MAS Lite Protocol** | `v2.1` |
| **Performance** | `>290,000 updates/sec` |

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd <repository-name>

# Install dependencies
pip install -r requirements.txt

# Run setup or initialization scripts
python setup.py install
```

## Quick Start

```python
# Basic trust graph usage
from trust_graph import TrustGraph

# Initialize trust graph
trust_graph = TrustGraph()

# Add agents
trust_graph.add_agent("agent_001")
trust_graph.add_agent("agent_002")

# Update trust relationship
trust_graph.update_trust("agent_001", "agent_002", 0.8, 0.9)

# Get trust score
score = trust_graph.get_trust_score("agent_001", "agent_002")
print(f"Trust score: {score}")

# High-performance mode for bulk operations
trust_graph.set_high_performance_mode(True)
trust_graph.set_auto_save(False)

# Batch updates for maximum performance
updates = [
    ("agent_001", "agent_002", 0.8, 0.9, {}),
    ("agent_002", "agent_003", 0.7, 0.8, {}),
    # ... more updates
]
trust_graph.update_trust_batch(updates, high_performance=True)
```

## Performance Modes

### **Standard Mode** (Default)
```python
trust_graph = TrustGraph(auto_save=True, high_performance=False)
# Full validation, logging, and auto-save
# Throughput: ~51 updates/sec
```

### **High-Performance Mode**
```python
trust_graph = TrustGraph(auto_save=False, high_performance=True)
# Minimal validation and logging
# Throughput: >200,000 updates/sec
```

### **Batch Operations**
```python
# Process multiple updates in a single operation
updates = [(from_agent, to_agent, score, confidence, metadata), ...]
trust_graph.update_trust_batch(updates, high_performance=True)
# Throughput: >290,000 updates/sec
```

## Development

### Prerequisites

- Python 3.13.3+
- Git
- GitBridge SmartRepo system
- MAS Lite Protocol v2.1 compatible environment

### Testing

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run performance tests
python -m pytest tests/integration/test_phase23_load_performance.py

# Generate coverage report
pytest --cov=trust_graph tests/
```

### Performance Testing

```bash
# Run throughput benchmarks
python -m pytest tests/integration/test_phase23_load_performance.py::TestPhase23LoadPerformance::test_optimized_throughput_benchmark -v -s

# Run performance comparison
python -m pytest tests/integration/test_phase23_load_performance.py::TestPhase23LoadPerformance::test_performance_comparison -v -s
```

## Documentation

- **Performance Documentation**: See `/docs/performance/gbp13_metrics.md` for detailed performance benchmarks
- **MAS Lite Compliance**: See `/docs/internal/gbp1_15_maslite_compliance_report.md` for protocol compliance
- **API Documentation**: See `/docs/api/` for detailed API documentation
- **Architecture**: See `/docs/architecture/` for system design
- **Examples**: See `/docs/examples/` for usage examples

## GitBridge Integration

This project is part of the GitBridge SmartRepo ecosystem and integrates with:

- **SmartRepo Branch Manager**: Automated branch creation and management
- **Task Chain System**: Workflow automation and task orchestration
- **MAS Lite Protocol v2.1**: Data integrity and audit compliance
- **Webhook System**: Real-time event processing and integration
- **Trust Analysis**: Behavioral modeling and trust relationship analysis

## MAS Lite Protocol v2.1 Compliance

### **Full Protocol Compliance**
- **Authentication**: Token-based authentication with secure refresh
- **Error Handling**: Standardized error codes and recovery mechanisms
- **Logging**: Structured JSON format with performance metrics
- **UI Accessibility**: CLI interface compliance and status reporting
- **Task Delegation**: Vote sequence protocol and agent capacity management

### **Performance Compliance**
- **Latency**: All operations meet or exceed protocol requirements
- **Throughput**: Significantly exceeds baseline performance targets
- **Resource Usage**: Memory and CPU utilization within protocol limits
- **Security**: Encryption and rate limiting compliant with protocol standards

## License

This project is part of the GitBridge system and follows the GitBridge licensing terms.

## Support

For support and questions:

- **Documentation**: See `/docs/` directory
- **Issues**: Create an issue in the repository
- **GitBridge Support**: Contact the GitBridge development team
- **Performance**: See `/docs/performance/` for optimization guidance

---

*Generated by GitBridge SmartRepo README Generator - 2025-06-19 18:00:00 UTC*
*MAS Lite Protocol v2.1 Compliant*
*GBP23 Trust Graph Engine Release*

## Overview
GitBridge is a collaborative platform for real-time contributor attribution, task tracking, and changelog management, compliant with MAS Lite Protocol v2.1.

---

## Phase 24 Highlights
- **Modern Web UI:** Responsive dashboard and attribution overview with dark mode, keyboard navigation, and ARIA roles.
- **Real-Time Collaboration:** Live activity feed, changelog, and diff viewer with WebSocket updates.
- **Performance Benchmarks:** Run `python performance_benchmarks.py` for comprehensive load, memory, and concurrency tests. Results in `benchmark_results/`.
- **Accessibility & Internationalization:** ARIA, screen reader, keyboard support, and multi-language (see `webui/translations/`).
- **Quick Actions:** Data export, navigation, and notifications from the dashboard.

---

## Usage
1. **Start the server:**
   ```bash
   python app.py
   ```
2. **Open the dashboard:**
   - Visit `http://localhost:5000/`
3. **Run the demo:**
   ```bash
   python phase24_demo.py
   ```
4. **Run performance benchmarks:**
   ```bash
   python performance_benchmarks.py
   ```
   - Results saved in `benchmark_results/`

---

## Accessibility & i18n
- All templates use ARIA roles and keyboard navigation.
- High-contrast, reduced motion, and large text supported.
- Switch UI language by updating the language in `webui/accessibility.py` (future: UI toggle).
- Sample Spanish translation: `webui/translations/es.json`

---

## Protocol Compliance
- All APIs and features are MAS Lite Protocol v2.1 compliant.

---

## Contributing
See `CONTRIBUTING.md` for guidelines. Feedback and PRs welcome!

---

## License
MIT
