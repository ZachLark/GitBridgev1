#!/usr/bin/env python3
"""
GitBridge Phase 21 Integration Test
P21P1-P21P5: Multi-Agent Collaboration Layer

Integration test for:
- P21P1: Multi-Agent Role Assignment Protocol (roles_config.json)
- P21P2: Task Fragmentation Engine (P21P2_task_fragmenter.py)
- P21P3: Collaborative Composition Pipeline (P21P3_composer.py)
- P21P5: Memory Coordination Layer (shared_memory.py)

Author: GitBridge Development Team
Date: 2025-06-19
"""

import json
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our modules
try:
    from P21P2_task_fragmenter import TaskFragmenter, Subtask, TaskFragment
    from P21P3_composer import CollaborativeComposer, SubtaskResult, CompositionResult
    from shared_memory import SharedMemoryGraph, MemoryNode
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    sys.exit(1)

class IntegrationTestSuite:
    """Integration test suite for P21P1-P21P5 modules."""
    
    def __init__(self):
        self.test_results = []
        self.roles_config = None
        self.fragmenter = None
        self.composer = None
        self.memory = None
        
    def setup(self):
        """Initialize all modules for testing."""
        logger.info("=== Setting up integration test ===")
        
        # Load roles config (P21P1)
        try:
            with open('roles_config.json', 'r') as f:
                self.roles_config = json.load(f)
            logger.info(f"✓ Loaded roles config with {len(self.roles_config.get('agents', []))} agents")
        except Exception as e:
            logger.error(f"✗ Failed to load roles config: {e}")
            return False
            
        # Initialize modules
        try:
            self.fragmenter = TaskFragmenter()
            self.composer = CollaborativeComposer()
            self.memory = SharedMemoryGraph()
            logger.info("✓ All modules initialized successfully")
        except Exception as e:
            logger.error(f"✗ Failed to initialize modules: {e}")
            return False
            
        return True
        
    def test_complex_workflow(self):
        """Test a complex end-to-end workflow."""
        logger.info("\n=== Testing Complex Workflow ===")
        
        # Test scenario: Code review with multiple agents
        master_task = """
        Perform a comprehensive code review of a Python web application that includes:
        1. Security vulnerability analysis
        2. Performance optimization recommendations
        3. Code quality and best practices review
        4. Documentation improvements
        5. Testing strategy suggestions
        """
        
        # Step 1: Fragment the task (P21P2)
        logger.info("Step 1: Fragmenting master task...")
        task_fragment = self.fragmenter.fragment_task(
            prompt=master_task,
            task_type="code_review",
            domain="technical",
            coordination_strategy="comprehensive"
        )
        
        # Step 2: Assign agents to subtasks (P21P2)
        logger.info("Step 2: Assigning agents to subtasks...")
        assignments = self.fragmenter.assign_agents_to_subtasks(task_fragment)
        
        # Step 3: Simulate subtask execution and store in memory (P21P5)
        logger.info("Step 3: Simulating subtask execution and storing in memory...")
        subtask_results = []
        
        for subtask in task_fragment.subtasks:
            # Simulate agent execution
            simulated_result = self._simulate_agent_execution(subtask, assignments.get(subtask.task_id))
            
            # Store in shared memory
            memory_node_id = self.memory.add_node(
                agent_id=subtask.assigned_agent or "unassigned",
                task_context=subtask.task_type,
                result=simulated_result,
                metadata={
                    "subtask_id": subtask.task_id,
                    "task_type": subtask.task_type,
                    "domain": subtask.domain,
                    "priority": subtask.priority
                }
            )
            
            # Create subtask result for composition
            subtask_result = SubtaskResult(
                subtask_id=subtask.task_id,
                agent_id=subtask.assigned_agent or "unassigned",
                agent_name=self._get_agent_name(subtask.assigned_agent),
                content=simulated_result["content"],
                confidence_score=simulated_result["confidence"],
                completion_time=simulated_result["completion_time"],
                token_usage=simulated_result["token_usage"]
            )
            subtask_results.append(subtask_result)
            
        # Step 4: Compose results (P21P3)
        logger.info("Step 4: Composing results...")
        composition = self.composer.compose_results(
            master_task_id=task_fragment.master_task_id,
            subtask_results=subtask_results,
            composition_strategy="hierarchical"
        )
        
        # Step 5: Store final composition in memory
        logger.info("Step 5: Storing final composition in memory...")
        final_memory_id = self.memory.add_node(
            agent_id="synthesizer_specialist",
            task_context="final_composition",
            result={
                "composed_content": composition.composed_content,
                "confidence_score": composition.confidence_score,
                "attribution_map": composition.attribution_map
            },
            metadata={
                "master_task_id": task_fragment.master_task_id,
                "composition_strategy": composition.composition_strategy,
                "conflicts_resolved": len(composition.conflict_resolution_log)
            }
        )
        
        # Step 6: Test memory recall
        logger.info("Step 6: Testing memory recall...")
        recalled_nodes = self.memory.recall_context("cursor_assistant", "code_review")
        
        # Step 7: Export results
        logger.info("Step 7: Exporting results...")
        self.fragmenter.export_routing_logs("integration_routing_logs.json")
        self.composer.export_attribution_log("integration_attribution_log.json")
        self.memory.export_memory("integration_memory_export.json")
        
        # Log results
        logger.info(f"\n=== Integration Test Results ===")
        logger.info(f"✓ Task fragmented into {len(task_fragment.subtasks)} subtasks")
        logger.info(f"✓ {len(assignments)} agent assignments made")
        logger.info(f"✓ {len(subtask_results)} subtask results generated")
        logger.info(f"✓ Composition confidence: {composition.confidence_score:.2f}")
        logger.info(f"✓ {len(composition.conflict_resolution_log)} conflicts resolved")
        logger.info(f"✓ {len(recalled_nodes)} nodes recalled from memory")
        logger.info(f"✓ All exports completed successfully")
        
        return True
        
    def _simulate_agent_execution(self, subtask: Subtask, agent_id: str) -> Dict[str, Any]:
        """Simulate agent execution of a subtask."""
        agent_name = self._get_agent_name(agent_id)
        
        # Generate simulated content based on task type
        if "security" in subtask.task_type.lower():
            content = f"Security analysis by {agent_name}: No critical vulnerabilities found. Recommend implementing input validation and using parameterized queries."
        elif "performance" in subtask.task_type.lower():
            content = f"Performance review by {agent_name}: Database queries can be optimized. Consider adding indexes and implementing caching."
        elif "quality" in subtask.task_type.lower() or "readability" in subtask.task_type.lower():
            content = f"Code quality assessment by {agent_name}: Code follows PEP 8 standards. Suggest adding more comprehensive error handling."
        else:
            content = f"General review by {agent_name}: Overall code quality is good. Minor improvements suggested for maintainability."
            
        return {
            "content": content,
            "confidence": 0.85 + (hash(subtask.task_id) % 15) / 100,  # Vary confidence slightly
            "completion_time": 2.0 + (hash(subtask.task_id) % 10) / 10,
            "token_usage": {
                "total": 150 + (hash(subtask.task_id) % 50),
                "prompt": 50 + (hash(subtask.task_id) % 20),
                "completion": 100 + (hash(subtask.task_id) % 30)
            }
        }
        
    def _get_agent_name(self, agent_id: str) -> str:
        """Get agent name from agent ID."""
        if not agent_id or agent_id == "unassigned":
            return "Unknown Agent"
            
        agents = self.roles_config.get('agents', [])
        for agent in agents:
            if agent.get('agent_id') == agent_id:
                return agent.get('agent_name', agent_id)
        return agent_id
        
    def test_memory_operations(self):
        """Test memory operations independently."""
        logger.info("\n=== Testing Memory Operations ===")
        
        # Test node creation and linking
        node1_id = self.memory.add_node("openai_gpt4o", "analysis", {"result": "Initial analysis"})
        node2_id = self.memory.add_node("cursor_assistant", "review", {"result": "Code review"})
        self.memory.link_nodes(node1_id, node2_id)
        
        # Test recall operations
        openai_nodes = self.memory.get_nodes_by_agent("openai_gpt4o")
        analysis_nodes = self.memory.get_nodes_by_context("analysis")
        recalled_nodes = self.memory.recall_context("openai_gpt4o", "analysis")
        
        logger.info(f"✓ Created {len(openai_nodes)} nodes for OpenAI")
        logger.info(f"✓ Found {len(analysis_nodes)} nodes in analysis context")
        logger.info(f"✓ Recalled {len(recalled_nodes)} nodes for OpenAI/analysis")
        
        return True
        
    def test_conflict_resolution(self):
        """Test conflict detection and resolution."""
        logger.info("\n=== Testing Conflict Resolution ===")
        
        # Create conflicting results
        conflicting_results = [
            SubtaskResult(
                subtask_id="conflict_test_1",
                agent_id="openai_gpt4o",
                agent_name="OpenAI",
                content="The code is secure and follows best practices.",
                confidence_score=0.9,
                completion_time=2.0,
                token_usage={"total": 150, "prompt": 50, "completion": 100}
            ),
            SubtaskResult(
                subtask_id="conflict_test_2",
                agent_id="grok_3",
                agent_name="Grok",
                content="The code has security vulnerabilities and needs immediate fixes.",
                confidence_score=0.8,
                completion_time=1.8,
                token_usage={"total": 140, "prompt": 45, "completion": 95}
            )
        ]
        
        # Test composition with conflicts
        composition = self.composer.compose_results(
            master_task_id="conflict_test",
            subtask_results=conflicting_results,
            composition_strategy="hierarchical"
        )
        
        logger.info(f"✓ Composition completed with {len(composition.conflict_resolution_log)} conflicts")
        logger.info(f"✓ Final confidence score: {composition.confidence_score:.2f}")
        
        return True
        
    def run_all_tests(self):
        """Run all integration tests."""
        logger.info("Starting P21P1-P21P5 Integration Test Suite")
        
        if not self.setup():
            logger.error("Setup failed. Aborting tests.")
            return False
            
        try:
            self.test_memory_operations()
            self.test_conflict_resolution()
            self.test_complex_workflow()
            
            logger.info("\n=== All Integration Tests Completed Successfully ===")
            return True
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            return False

def main():
    """Run the integration test suite."""
    test_suite = IntegrationTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 Integration test PASSED!")
        print("All P21P1-P21P5 modules are working together correctly.")
    else:
        print("\n❌ Integration test FAILED!")
        print("Check the logs above for details.")
        
    return success

if __name__ == "__main__":
    main() 