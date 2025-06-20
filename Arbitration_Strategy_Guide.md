# GitBridge Arbitration Strategy Development Guide
**Version:** 1.0.0  
**Date:** 2025-06-19  
**Phase:** P22P7 - Documentation and Contributor Onboarding

---

## 📖 OVERVIEW

This guide provides comprehensive instructions for developing custom arbitration strategies for the GitBridge multi-agent system. Arbitration strategies determine how conflicting agent outputs are resolved and which agent's response is selected as the final result.

---

## 🏗️ ARCHITECTURE OVERVIEW

### **Core Components**
- **ArbitrationEngine**: Central controller that manages conflicts
- **ArbitrationPluginBase**: Base class for all strategy plugins
- **AgentOutput**: Represents an agent's response with metadata
- **ArbitrationConflict**: Represents a conflict between multiple outputs
- **ArbitrationResult**: Represents the final arbitration decision

### **Plugin System**
```
plugins/arbitration/
├── strategy_majority_vote.py
├── strategy_confidence_weight.py
├── strategy_recency_bias.py
├── strategy_cost_aware.py
├── strategy_latency_aware.py
└── strategy_hybrid_score.py
```

---

## 🎯 STRATEGY DEVELOPMENT

### **Step 1: Create Strategy Class**

All arbitration strategies must inherit from `ArbitrationPluginBase`:

```python
#!/usr/bin/env python3
"""
Custom Arbitration Strategy
Author: Your Name
Date: YYYY-MM-DD
"""

import logging
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from arbitration_engine import ArbitrationPluginBase, ArbitrationConflict, ArbitrationResult, AgentOutput

logger = logging.getLogger(__name__)

class CustomStrategy(ArbitrationPluginBase):
    """
    Custom arbitration strategy implementation.
    
    Features:
    - Describe your strategy's key features
    - Explain when to use this strategy
    - List any special considerations
    """
    
    @property
    def strategy_name(self) -> str:
        """Return the name of this arbitration strategy."""
        return "custom_strategy"
        
    def arbitrate(
        self, 
        conflict: ArbitrationConflict, 
        config: Optional[Dict[str, Any]] = None
    ) -> ArbitrationResult:
        """
        Implement your arbitration logic here.
        
        Args:
            conflict: The conflict to resolve
            config: Optional configuration for the strategy
            
        Returns:
            ArbitrationResult: The arbitration decision
        """
        # Your implementation here
        pass
```

### **Step 2: Implement Core Logic**

#### **Basic Strategy Template**
```python
def arbitrate(self, conflict: ArbitrationConflict, config: Optional[Dict[str, Any]] = None) -> ArbitrationResult:
    """Arbitrate using custom strategy."""
    logger.info(f"Using custom strategy for conflict {conflict.conflict_id}")
    
    if not conflict.agent_outputs:
        raise ValueError("No agent outputs to arbitrate")
        
    config = config or {}
    
    # 1. Analyze agent outputs
    # 2. Apply your strategy logic
    # 3. Select winning agent
    # 4. Calculate final confidence
    # 5. Return result
    
    best_agent = self._select_best_agent(conflict.agent_outputs, config)
    
    result = ArbitrationResult(
        winner_agent_id=best_agent.agent_id,
        winning_output=best_agent.output,
        confidence=best_agent.confidence,
        strategy_used=self.strategy_name,
        metadata={
            # Add strategy-specific metadata
            "custom_metric": "value",
            "total_agents": len(conflict.agent_outputs)
        }
    )
    
    logger.info(f"Custom strategy result: {best_agent.agent_id} wins")
    return result
```

### **Step 3: Configuration Support**

#### **Configuration Validation**
```python
def validate_config(self, config: Dict[str, Any]) -> bool:
    """Validate configuration for this strategy."""
    if not isinstance(config, dict):
        return False
        
    # Validate required fields
    required_fields = ["param1", "param2"]
    for field in required_fields:
        if field not in config:
            return False
            
    # Validate data types and ranges
    if not isinstance(config.get("param1"), (int, float)) or config["param1"] < 0:
        return False
        
    return True
```

#### **Default Configuration**
```python
def _get_default_config(self) -> Dict[str, Any]:
    """Get default configuration for this strategy."""
    return {
        "param1": 0.5,
        "param2": 100,
        "enable_feature": True
    }
```

---

## 📊 STRATEGY EXAMPLES

### **Example 1: Quality-First Strategy**
```python
class QualityFirstStrategy(ArbitrationPluginBase):
    """Prioritizes output quality over other factors."""
    
    @property
    def strategy_name(self) -> str:
        return "quality_first"
        
    def arbitrate(self, conflict: ArbitrationConflict, config: Optional[Dict[str, Any]] = None) -> ArbitrationResult:
        config = config or {}
        quality_threshold = config.get("quality_threshold", 0.8)
        
        # Filter agents by quality threshold
        high_quality_agents = [
            output for output in conflict.agent_outputs
            if output.confidence >= quality_threshold
        ]
        
        if not high_quality_agents:
            # If no high-quality agents, use best available
            best_agent = max(conflict.agent_outputs, key=lambda x: x.confidence)
        else:
            # Among high-quality agents, prefer faster ones
            best_agent = min(high_quality_agents, key=lambda x: x.execution_time_ms or float('inf'))
            
        return ArbitrationResult(
            winner_agent_id=best_agent.agent_id,
            winning_output=best_agent.output,
            confidence=best_agent.confidence,
            strategy_used=self.strategy_name,
            metadata={
                "quality_threshold": quality_threshold,
                "high_quality_agents": len(high_quality_agents)
            }
        )
```

### **Example 2: Consensus Strategy**
```python
class ConsensusStrategy(ArbitrationPluginBase):
    """Requires consensus among multiple agents."""
    
    @property
    def strategy_name(self) -> str:
        return "consensus"
        
    def arbitrate(self, conflict: ArbitrationConflict, config: Optional[Dict[str, Any]] = None) -> ArbitrationResult:
        config = config or {}
        consensus_threshold = config.get("consensus_threshold", 0.7)
        min_agents = config.get("min_agents", 2)
        
        if len(conflict.agent_outputs) < min_agents:
            raise ValueError(f"Consensus requires at least {min_agents} agents")
            
        # Group outputs by similarity
        output_groups = self._group_similar_outputs(conflict.agent_outputs)
        
        # Find group with highest consensus
        best_group = max(output_groups, key=lambda g: len(g))
        consensus_ratio = len(best_group) / len(conflict.agent_outputs)
        
        if consensus_ratio < consensus_threshold:
            raise ValueError(f"Consensus threshold {consensus_threshold} not met (got {consensus_ratio})")
            
        # Select best agent from consensus group
        best_agent = max(best_group, key=lambda x: x.confidence)
        
        return ArbitrationResult(
            winner_agent_id=best_agent.agent_id,
            winning_output=best_agent.output,
            confidence=best_agent.confidence,
            strategy_used=self.strategy_name,
            metadata={
                "consensus_ratio": consensus_ratio,
                "consensus_group_size": len(best_group)
            }
        )
        
    def _group_similar_outputs(self, outputs: List[AgentOutput]) -> List[List[AgentOutput]]:
        """Group outputs by similarity."""
        # Implementation depends on output type
        # This is a simplified example
        groups = []
        for output in outputs:
            # Find similar outputs (implement your similarity logic)
            similar_outputs = [o for o in outputs if self._are_similar(o, output)]
            if similar_outputs not in groups:
                groups.append(similar_outputs)
        return groups
        
    def _are_similar(self, output1: AgentOutput, output2: AgentOutput) -> bool:
        """Check if two outputs are similar."""
        # Implement your similarity logic
        return str(output1.output) == str(output2.output)
```

---

## 🔧 BEST PRACTICES

### **1. Error Handling**
```python
def arbitrate(self, conflict: ArbitrationConflict, config: Optional[Dict[str, Any]] = None) -> ArbitrationResult:
    """Arbitrate with comprehensive error handling."""
    try:
        # Validate inputs
        if not conflict.agent_outputs:
            raise ValueError("No agent outputs to arbitrate")
            
        if config and not self.validate_config(config):
            raise ValueError("Invalid configuration")
            
        # Perform arbitration
        result = self._perform_arbitration(conflict, config)
        
        # Validate output
        if not self._validate_result(result):
            raise ValueError("Invalid arbitration result")
            
        return result
        
    except Exception as e:
        logger.error(f"Arbitration failed in {self.strategy_name}: {e}")
        # Return safe fallback or re-raise
        raise
```

### **2. Logging and Debugging**
```python
def arbitrate(self, conflict: ArbitrationConflict, config: Optional[Dict[str, Any]] = None) -> ArbitrationResult:
    """Arbitrate with detailed logging."""
    logger.info(f"[{self.strategy_name}] Starting arbitration for conflict {conflict.conflict_id}")
    logger.debug(f"[{self.strategy_name}] Config: {config}")
    logger.debug(f"[{self.strategy_name}] {len(conflict.agent_outputs)} agents involved")
    
    # Your arbitration logic here
    
    logger.info(f"[{self.strategy_name}] Arbitration completed: {result.winner_agent_id} wins")
    logger.debug(f"[{self.strategy_name}] Result metadata: {result.metadata}")
    
    return result
```

### **3. Performance Optimization**
```python
def arbitrate(self, conflict: ArbitrationConflict, config: Optional[Dict[str, Any]] = None) -> ArbitrationResult:
    """Optimized arbitration implementation."""
    start_time = time.time()
    
    # Cache frequently accessed values
    agent_count = len(conflict.agent_outputs)
    confidences = [output.confidence for output in conflict.agent_outputs]
    
    # Use efficient algorithms
    best_agent = max(conflict.agent_outputs, key=lambda x: x.confidence)
    
    execution_time = time.time() - start_time
    logger.debug(f"[{self.strategy_name}] Execution time: {execution_time:.3f}s")
    
    return ArbitrationResult(
        winner_agent_id=best_agent.agent_id,
        winning_output=best_agent.output,
        confidence=best_agent.confidence,
        strategy_used=self.strategy_name,
        metadata={"execution_time_ms": execution_time * 1000}
    )
```

### **4. Configuration Management**
```python
class ConfigurableStrategy(ArbitrationPluginBase):
    """Strategy with comprehensive configuration support."""
    
    def __init__(self):
        self.default_config = {
            "param1": 0.5,
            "param2": 100,
            "enable_feature": True
        }
        
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration with detailed error messages."""
        if not isinstance(config, dict):
            logger.error("Config must be a dictionary")
            return False
            
        # Validate each parameter
        for param, value in config.items():
            if not self._validate_parameter(param, value):
                return False
                
        return True
        
    def _validate_parameter(self, param: str, value: Any) -> bool:
        """Validate individual parameter."""
        if param == "param1":
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                logger.error(f"param1 must be a number between 0 and 1, got {value}")
                return False
        elif param == "param2":
            if not isinstance(value, int) or value < 0:
                logger.error(f"param2 must be a non-negative integer, got {value}")
                return False
        elif param == "enable_feature":
            if not isinstance(value, bool):
                logger.error(f"enable_feature must be a boolean, got {value}")
                return False
        else:
            logger.warning(f"Unknown parameter: {param}")
            
        return True
```

---

## 🧪 TESTING

### **Unit Tests**
```python
import unittest
from unittest.mock import Mock, patch

class TestCustomStrategy(unittest.TestCase):
    """Test cases for custom strategy."""
    
    def setUp(self):
        """Set up test environment."""
        self.strategy = CustomStrategy()
        
    def test_strategy_name(self):
        """Test strategy name property."""
        self.assertEqual(self.strategy.strategy_name, "custom_strategy")
        
    def test_arbitration_basic(self):
        """Test basic arbitration functionality."""
        # Create test conflict
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8),
            AgentOutput("agent2", "task1", "subtask1", "answer2", 0.9)
        ]
        
        conflict = ArbitrationConflict(
            conflict_id="test_conflict",
            task_id="task1",
            subtask_id="subtask1",
            agent_outputs=outputs,
            conflict_type="contradiction"
        )
        
        result = self.strategy.arbitrate(conflict)
        
        self.assertIsInstance(result, ArbitrationResult)
        self.assertIn(result.winner_agent_id, ["agent1", "agent2"])
        
    def test_config_validation(self):
        """Test configuration validation."""
        valid_config = {"param1": 0.5, "param2": 100}
        invalid_config = {"param1": -1, "param2": "invalid"}
        
        self.assertTrue(self.strategy.validate_config(valid_config))
        self.assertFalse(self.strategy.validate_config(invalid_config))
        
    def test_error_handling(self):
        """Test error handling."""
        # Test with empty outputs
        conflict = ArbitrationConflict(
            conflict_id="test_conflict",
            task_id="task1",
            subtask_id="subtask1",
            agent_outputs=[],
            conflict_type="contradiction"
        )
        
        with self.assertRaises(ValueError):
            self.strategy.arbitrate(conflict)
```

### **Integration Tests**
```python
class TestCustomStrategyIntegration(unittest.TestCase):
    """Integration tests for custom strategy."""
    
    def test_with_arbitration_engine(self):
        """Test strategy integration with arbitration engine."""
        engine = ArbitrationEngine()
        strategy = CustomStrategy()
        
        # Register strategy
        engine.register_strategy(strategy)
        
        # Test arbitration
        outputs = [
            AgentOutput("agent1", "task1", "subtask1", "answer1", 0.8),
            AgentOutput("agent2", "task1", "subtask1", "answer2", 0.9)
        ]
        
        result = engine.arbitrate_conflict(outputs, "task1", "subtask1", "custom_strategy")
        
        self.assertIsInstance(result, ArbitrationResult)
        self.assertEqual(result.strategy_used, "custom_strategy")
```

---

## 🚀 DEPLOYMENT

### **1. Plugin Installation**
```bash
# Copy your strategy to the plugins directory
cp strategy_custom.py plugins/arbitration/

# Verify the plugin loads correctly
python -c "from arbitration_engine import ArbitrationEngine; engine = ArbitrationEngine(); print('Loaded strategies:', list(engine.strategies.keys()))"
```

### **2. Configuration**
```json
{
  "strategy_configs": {
    "custom_strategy": {
      "enabled": true,
      "param1": 0.7,
      "param2": 150,
      "enable_feature": true,
      "metadata": {
        "description": "Custom strategy for specific use cases",
        "use_case": "When custom logic is required"
      }
    }
  }
}
```

### **3. Testing in Production**
```python
# Test your strategy with real data
engine = ArbitrationEngine()

# Use your strategy for specific task types
result = engine.arbitrate_conflict(
    agent_outputs, 
    "task_id", 
    "subtask_id", 
    "custom_strategy",
    config={"param1": 0.8}
)
```

---

## 🔍 TROUBLESHOOTING

### **Common Issues**

#### **1. Plugin Not Loading**
```python
# Check plugin file location
ls -la plugins/arbitration/strategy_custom.py

# Check import errors
python -c "import plugins.arbitration.strategy_custom"

# Check strategy registration
engine = ArbitrationEngine()
print("Available strategies:", list(engine.strategies.keys()))
```

#### **2. Configuration Errors**
```python
# Validate configuration
strategy = CustomStrategy()
config = {"param1": 0.5, "param2": 100}
print("Config valid:", strategy.validate_config(config))
```

#### **3. Performance Issues**
```python
# Profile your strategy
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run your strategy
result = strategy.arbitrate(conflict, config)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### **Debug Mode**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug output
engine = ArbitrationEngine()
result = engine.arbitrate_conflict(outputs, "task1", "subtask1", "custom_strategy")
```

---

## 📚 RESOURCES

### **Reference Documentation**
- [Arbitration Engine API Reference](arbitration_engine.md)
- [Plugin Development Examples](examples/)
- [Configuration Schema](arbitration_config.json)

### **Community Support**
- [GitHub Issues](https://github.com/gitbridge/arbitration/issues)
- [Discord Community](https://discord.gg/gitbridge)
- [Documentation Wiki](https://wiki.gitbridge.dev)

### **Contributing**
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Pull Request Template](.github/pull_request_template.md)

---

## 📝 CONCLUSION

This guide provides the foundation for developing custom arbitration strategies. Remember to:

1. **Follow the base class structure** for consistency
2. **Implement comprehensive error handling** for reliability
3. **Add detailed logging** for debugging
4. **Write thorough tests** for quality assurance
5. **Document your strategy** for maintainability
6. **Consider performance implications** for scalability

For additional support or questions, please refer to the resources listed above or contact the development team.

---

**Guide Version:** 1.0.0  
**Last Updated:** 2025-06-19  
**Next Review:** 2025-07-19 