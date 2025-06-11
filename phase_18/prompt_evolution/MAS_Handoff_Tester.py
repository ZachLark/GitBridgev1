# P18P6S2 – MAS_Handoff_Tester.py

"""
GitBridge Phase 18P6 - MAS Handoff Tester

This module provides tools for testing and simulating prompt handoff behavior
across Multi-Agent Systems (MAS). It includes UID threading simulation, 
lineage visualization, and fallback chain validation.

Author: GitBridge MAS Integration Team
Phase: 18P6 - Prompt Evolution + Logging UI
MAS Lite Protocol: v2.1 Compliance
"""

import json
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set
from enum import Enum


class PromptPhase(Enum):
    """Prompt lifecycle phases as defined in Prompt_Evolution_Policy.md"""
    INIT = "PROMPT_INIT"
    MUTATION = "PROMPT_MUTATION" 
    FALLBACK = "PROMPT_FALLBACK"
    ARCHIVE = "PROMPT_ARCHIVE"


class FallbackReason(Enum):
    """Standardized fallback trigger reasons"""
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    QUALITY_FAILURE = "QUALITY_FAILURE"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    CONTEXT_OVERFLOW = "CONTEXT_OVERFLOW"
    COMPLIANCE_VIOLATION = "COMPLIANCE_VIOLATION"


@dataclass
class PromptUID:
    """
    Core dataclass representing a prompt UID with lineage tracking.
    
    Attributes:
        uid (str): Unique identifier in format {timestamp}_{entropy}_{agent_id}_{sequence}
        parent_uid (Optional[str]): Parent UID for lineage tracking
        root_uid (str): Root UID of the entire chain
        phase (PromptPhase): Current lifecycle phase
        agent_id (str): AI agent handling this prompt
        confidence_score (float): Current confidence level (0.0-1.0)
        fallback_flag (bool): Whether this prompt is result of fallback
        fallback_reason (Optional[FallbackReason]): Reason for fallback if applicable
        children_uids (List[str]): List of child UIDs spawned from this prompt
        metadata (Dict[str, Any]): Additional context and performance data
        timestamp (str): ISO timestamp of prompt creation
        lineage_depth (int): Depth in the lineage tree (root = 0)
        success (bool): Whether this prompt completed successfully
    """
    uid: str
    parent_uid: Optional[str] = None
    root_uid: str = ""
    phase: PromptPhase = PromptPhase.INIT
    agent_id: str = "unknown"
    confidence_score: float = 0.0
    fallback_flag: bool = False
    fallback_reason: Optional[FallbackReason] = None
    children_uids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    lineage_depth: int = 0
    success: bool = False
    
    def __post_init__(self):
        """Initialize computed fields after dataclass creation"""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.root_uid:
            self.root_uid = self.parent_uid if self.parent_uid else self.uid


class MASHandoffTester:
    """
    Test framework for MAS prompt handoff and lineage behavior.
    
    Provides simulation capabilities for UID threading, fallback chains,
    and lineage validation across multi-agent systems.
    """
    
    def __init__(self):
        """Initialize the MAS Handoff Tester with mock data"""
        self.prompt_registry: Dict[str, PromptUID] = {}
        self.lineage_chains: Dict[str, List[str]] = {}
        self._setup_mock_fallback_chains()
    
    def _setup_mock_fallback_chains(self):
        """
        Create 3-5 mock UID fallback chains for testing.
        
        Chains represent realistic scenarios:
        1. Simple fallback (confidence drop)
        2. Multi-level escalation 
        3. Resource exhaustion cascade
        4. Quality failure recovery
        5. Complex mutation chain
        """
        
        # Chain 1: Simple Confidence Fallback
        chain1_root = self._create_prompt_uid(
            base="20250610_a7f2c9_gpt4_001",
            phase=PromptPhase.INIT,
            agent="gpt4",
            confidence=0.85,
            metadata={"task_type": "code_generation", "complexity": "medium"}
        )
        
        chain1_fallback = self._create_prompt_uid(
            base="20250610_a7f2c9_claude_002", 
            parent=chain1_root.uid,
            root=chain1_root.uid,
            phase=PromptPhase.FALLBACK,
            agent="claude3.5",
            confidence=0.72,
            fallback_flag=True,
            fallback_reason=FallbackReason.LOW_CONFIDENCE,
            metadata={"original_confidence": 0.42, "fallback_triggered": True}
        )
        
        chain1_archive = self._create_prompt_uid(
            base="20250610_a7f2c9_claude_003",
            parent=chain1_fallback.uid,
            root=chain1_root.uid,
            phase=PromptPhase.ARCHIVE,
            agent="claude3.5",
            confidence=0.72,
            success=True,
            metadata={"final_result": "success", "total_duration": 45}
        )
        
        # Chain 2: Multi-Level Escalation 
        chain2_root = self._create_prompt_uid(
            base="20250610_b8e3d1_gpt4_001",
            phase=PromptPhase.INIT,
            agent="gpt4",
            confidence=0.78,
            metadata={"task_type": "architecture_design", "complexity": "high"}
        )
        
        chain2_mutation = self._create_prompt_uid(
            base="20250610_b8e3d1_gpt4_002",
            parent=chain2_root.uid,
            root=chain2_root.uid,
            phase=PromptPhase.MUTATION,
            agent="gpt4",
            confidence=0.65,
            metadata={"mutation_reason": "context_expansion", "added_requirements": 3}
        )
        
        chain2_fallback1 = self._create_prompt_uid(
            base="20250610_b8e3d1_claude_003",
            parent=chain2_mutation.uid,
            root=chain2_root.uid,
            phase=PromptPhase.FALLBACK,
            agent="claude3.5",
            confidence=0.58,
            fallback_flag=True,
            fallback_reason=FallbackReason.QUALITY_FAILURE,
            metadata={"escalation_level": 1, "quality_score": 0.55}
        )
        
        chain2_fallback2 = self._create_prompt_uid(
            base="20250610_b8e3d1_gemini_004",
            parent=chain2_fallback1.uid,
            root=chain2_root.uid,
            phase=PromptPhase.FALLBACK,
            agent="gemini_pro",
            confidence=0.82,
            fallback_flag=True,
            fallback_reason=FallbackReason.LOW_CONFIDENCE,
            metadata={"escalation_level": 2, "previous_attempts": 2}
        )
        
        chain2_archive = self._create_prompt_uid(
            base="20250610_b8e3d1_gemini_005",
            parent=chain2_fallback2.uid,
            root=chain2_root.uid,
            phase=PromptPhase.ARCHIVE,
            agent="gemini_pro",
            confidence=0.82,
            success=True,
            metadata={"final_result": "success", "total_duration": 180, "escalation_levels": 2}
        )
        
        # Chain 3: Resource Exhaustion Cascade
        chain3_root = self._create_prompt_uid(
            base="20250610_c9f4e2_gpt4_001",
            phase=PromptPhase.INIT,
            agent="gpt4_turbo",
            confidence=0.90,
            metadata={"task_type": "large_codebase_analysis", "complexity": "very_high", "estimated_tokens": 50000}
        )
        
        chain3_fallback = self._create_prompt_uid(
            base="20250610_c9f4e2_claude_002",
            parent=chain3_root.uid,
            root=chain3_root.uid,
            phase=PromptPhase.FALLBACK,
            agent="claude3.5",
            confidence=0.75,
            fallback_flag=True,
            fallback_reason=FallbackReason.RESOURCE_EXHAUSTION,
            metadata={"token_limit_exceeded": True, "split_strategy": "file_based"}
        )
        
        chain3_archive = self._create_prompt_uid(
            base="20250610_c9f4e2_claude_003",
            parent=chain3_fallback.uid,
            root=chain3_root.uid,
            phase=PromptPhase.ARCHIVE,
            agent="claude3.5",
            confidence=0.75,
            success=True,
            metadata={"final_result": "success", "split_tasks": 5, "total_duration": 320}
        )
        
        # Chain 4: Quality Failure Recovery
        chain4_root = self._create_prompt_uid(
            base="20250610_d1a5f3_claude_001",
            phase=PromptPhase.INIT,
            agent="claude3.5",
            confidence=0.88,
            metadata={"task_type": "code_review", "complexity": "medium", "files_count": 12}
        )
        
        chain4_mutation = self._create_prompt_uid(
            base="20250610_d1a5f3_claude_002",
            parent=chain4_root.uid,
            root=chain4_root.uid,
            phase=PromptPhase.MUTATION,
            agent="claude3.5",
            confidence=0.45,
            metadata={"mutation_reason": "incomplete_analysis", "coverage": 0.60}
        )
        
        chain4_fallback = self._create_prompt_uid(
            base="20250610_d1a5f3_gpt4_003",
            parent=chain4_mutation.uid,
            root=chain4_root.uid,
            phase=PromptPhase.FALLBACK,
            agent="gpt4",
            confidence=0.87,
            fallback_flag=True,
            fallback_reason=FallbackReason.QUALITY_FAILURE,
            metadata={"quality_improvement": 0.42, "enhanced_context": True}
        )
        
        chain4_archive = self._create_prompt_uid(
            base="20250610_d1a5f3_gpt4_004",
            parent=chain4_fallback.uid,
            root=chain4_root.uid,
            phase=PromptPhase.ARCHIVE,
            agent="gpt4",
            confidence=0.87,
            success=True,
            metadata={"final_result": "success", "coverage": 0.95, "total_duration": 95}
        )
        
        # Chain 5: Complex Mutation Chain (No Fallback)
        chain5_root = self._create_prompt_uid(
            base="20250610_e2b6g4_gpt4_001",
            phase=PromptPhase.INIT,
            agent="gpt4",
            confidence=0.82,
            metadata={"task_type": "documentation", "complexity": "low", "sections": 8}
        )
        
        chain5_mutation1 = self._create_prompt_uid(
            base="20250610_e2b6g4_gpt4_002",
            parent=chain5_root.uid,
            root=chain5_root.uid,
            phase=PromptPhase.MUTATION,
            agent="gpt4",
            confidence=0.86,
            metadata={"mutation_reason": "style_consistency", "improvements": ["formatting", "clarity"]}
        )
        
        chain5_mutation2 = self._create_prompt_uid(
            base="20250610_e2b6g4_gpt4_003",
            parent=chain5_mutation1.uid,
            root=chain5_root.uid,
            phase=PromptPhase.MUTATION,
            agent="gpt4",
            confidence=0.91,
            metadata={"mutation_reason": "content_expansion", "added_sections": 2}
        )
        
        chain5_archive = self._create_prompt_uid(
            base="20250610_e2b6g4_gpt4_004",
            parent=chain5_mutation2.uid,
            root=chain5_root.uid,
            phase=PromptPhase.ARCHIVE,
            agent="gpt4",
            confidence=0.91,
            success=True,
            metadata={"final_result": "success", "mutations": 2, "total_duration": 75}
        )
        
        # Build parent-child relationships
        self._link_chain_relationships([chain1_root, chain1_fallback, chain1_archive])
        self._link_chain_relationships([chain2_root, chain2_mutation, chain2_fallback1, chain2_fallback2, chain2_archive])
        self._link_chain_relationships([chain3_root, chain3_fallback, chain3_archive])
        self._link_chain_relationships([chain4_root, chain4_mutation, chain4_fallback, chain4_archive])
        self._link_chain_relationships([chain5_root, chain5_mutation1, chain5_mutation2, chain5_archive])
        
        print("✅ Mock fallback chains initialized:")
        print(f"   - Chain 1: Simple confidence fallback (3 nodes)")
        print(f"   - Chain 2: Multi-level escalation (5 nodes)")
        print(f"   - Chain 3: Resource exhaustion (3 nodes)")
        print(f"   - Chain 4: Quality failure recovery (4 nodes)")
        print(f"   - Chain 5: Complex mutation chain (4 nodes)")
        print(f"   - Total UIDs: {len(self.prompt_registry)}")
    
    def _create_prompt_uid(self, base: str, phase: PromptPhase = PromptPhase.INIT, 
                          parent: Optional[str] = None, root: Optional[str] = None,
                          agent: str = "unknown", confidence: float = 0.0,
                          fallback_flag: bool = False, fallback_reason: Optional[FallbackReason] = None,
                          success: bool = False, metadata: Dict[str, Any] = None) -> PromptUID:
        """Create and register a PromptUID with specified parameters"""
        if metadata is None:
            metadata = {}
            
        # Calculate lineage depth
        depth = 0
        if parent and parent in self.prompt_registry:
            depth = self.prompt_registry[parent].lineage_depth + 1
            
        prompt_uid = PromptUID(
            uid=base,
            parent_uid=parent,
            root_uid=root or base,
            phase=phase,
            agent_id=agent,
            confidence_score=confidence,
            fallback_flag=fallback_flag,
            fallback_reason=fallback_reason,
            metadata=metadata,
            lineage_depth=depth,
            success=success
        )
        
        self.prompt_registry[base] = prompt_uid
        return prompt_uid
    
    def _link_chain_relationships(self, chain: List[PromptUID]):
        """Establish parent-child relationships in a chain"""
        for i in range(len(chain) - 1):
            parent = chain[i]
            child = chain[i + 1]
            parent.children_uids.append(child.uid)
            
        # Build lineage chain mapping
        root_uid = chain[0].uid
        self.lineage_chains[root_uid] = [node.uid for node in chain]
    
    def simulate_prompt_handoff(self, uid: str) -> Dict[str, Any]:
        """
        Simulate prompt handoff for given UID and walk the lineage tree.
        
        Args:
            uid (str): Starting UID for simulation
            
        Returns:
            Dict[str, Any]: Complete simulation results with lineage walk
        """
        if uid not in self.prompt_registry:
            return {
                "error": f"UID {uid} not found in registry",
                "available_uids": list(self.prompt_registry.keys())
            }
        
        start_prompt = self.prompt_registry[uid]
        root_uid = start_prompt.root_uid
        
        print(f"\n🔍 Simulating MAS Handoff for UID: {uid}")
        print(f"📍 Root UID: {root_uid}")
        print("=" * 60)
        
        # Get complete lineage chain
        lineage_chain = self._get_complete_lineage(root_uid)
        
        # Walk through each node in the lineage
        simulation_results = {
            "simulation_uid": uid,
            "root_uid": root_uid,
            "total_nodes": len(lineage_chain),
            "lineage_path": [],
            "fallback_points": [],
            "confidence_trajectory": [],
            "agent_transitions": [],
            "performance_metrics": {},
            "success": False,
            "simulation_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print("📋 Lineage Walk:")
        
        for i, node_uid in enumerate(lineage_chain):
            node = self.prompt_registry[node_uid]
            
            # Determine display symbols
            phase_symbol = {
                PromptPhase.INIT: "🚀",
                PromptPhase.MUTATION: "🔄", 
                PromptPhase.FALLBACK: "⚠️",
                PromptPhase.ARCHIVE: "📁"
            }.get(node.phase, "❓")
            
            fallback_indicator = " [FALLBACK]" if node.fallback_flag else ""
            success_indicator = " ✅" if node.success else " 🔄" if node.phase != PromptPhase.ARCHIVE else " ❌"
            
            # Print node details
            indent = "  " * node.lineage_depth
            print(f"{indent}{phase_symbol} {node.uid}")
            print(f"{indent}   Phase: {node.phase.value}{fallback_indicator}")
            print(f"{indent}   Agent: {node.agent_id}")
            print(f"{indent}   Confidence: {node.confidence_score:.2f}")
            
            if node.fallback_flag and node.fallback_reason:
                print(f"{indent}   Fallback Reason: {node.fallback_reason.value}")
                simulation_results["fallback_points"].append({
                    "uid": node.uid,
                    "reason": node.fallback_reason.value,
                    "confidence": node.confidence_score,
                    "depth": node.lineage_depth
                })
            
            if node.metadata:
                key_metadata = {k: v for k, v in node.metadata.items() if k in ["task_type", "complexity", "escalation_level", "total_duration"]}
                if key_metadata:
                    print(f"{indent}   Metadata: {key_metadata}")
            
            print(f"{indent}   Status: {node.phase.value}{success_indicator}")
            
            if i < len(lineage_chain) - 1:
                print(f"{indent}   │")
                print(f"{indent}   ▼")
            
            # Collect simulation data
            simulation_results["lineage_path"].append({
                "uid": node.uid,
                "phase": node.phase.value,
                "agent": node.agent_id,
                "confidence": node.confidence_score,
                "depth": node.lineage_depth,
                "fallback": node.fallback_flag,
                "success": node.success
            })
            
            simulation_results["confidence_trajectory"].append(node.confidence_score)
            
            if i > 0:
                prev_agent = lineage_chain[i-1]
                if self.prompt_registry[prev_agent].agent_id != node.agent_id:
                    simulation_results["agent_transitions"].append({
                        "from": self.prompt_registry[prev_agent].agent_id,
                        "to": node.agent_id,
                        "reason": node.fallback_reason.value if node.fallback_reason else "mutation"
                    })
        
        # Calculate performance metrics
        final_node = self.prompt_registry[lineage_chain[-1]]
        simulation_results["success"] = final_node.success
        simulation_results["performance_metrics"] = {
            "total_fallbacks": len(simulation_results["fallback_points"]),
            "agent_switches": len(simulation_results["agent_transitions"]),
            "confidence_range": {
                "min": min(simulation_results["confidence_trajectory"]),
                "max": max(simulation_results["confidence_trajectory"]),
                "final": simulation_results["confidence_trajectory"][-1]
            },
            "lineage_depth": max(node.lineage_depth for node in [self.prompt_registry[uid] for uid in lineage_chain]),
            "total_duration": final_node.metadata.get("total_duration", 0)
        }
        
        print("\n📊 Simulation Summary:")
        print(f"   Total Nodes: {simulation_results['total_nodes']}")
        print(f"   Fallback Points: {simulation_results['performance_metrics']['total_fallbacks']}")
        print(f"   Agent Transitions: {simulation_results['performance_metrics']['agent_switches']}")
        print(f"   Final Confidence: {simulation_results['performance_metrics']['confidence_range']['final']:.2f}")
        print(f"   Success: {'✅ Yes' if simulation_results['success'] else '❌ No'}")
        
        return simulation_results
    
    def _get_complete_lineage(self, root_uid: str) -> List[str]:
        """Get complete lineage chain from root to final archive"""
        if root_uid in self.lineage_chains:
            return self.lineage_chains[root_uid]
        
        # Fallback: reconstruct lineage by walking tree
        lineage = []
        current_uid = root_uid
        visited = set()
        
        while current_uid and current_uid not in visited:
            visited.add(current_uid)
            lineage.append(current_uid)
            
            current_prompt = self.prompt_registry.get(current_uid)
            if current_prompt and current_prompt.children_uids:
                # Take first child (assuming linear chain for now)
                current_uid = current_prompt.children_uids[0]
            else:
                break
        
        return lineage
    
    def validate_lineage_integrity(self) -> Dict[str, Any]:
        """
        Validate UID threading and lineage integrity across all chains.
        
        Returns:
            Dict[str, Any]: Validation results with any issues found
        """
        print("\n🔍 Validating Lineage Integrity...")
        
        validation_results = {
            "total_uids": len(self.prompt_registry),
            "root_uids": [],
            "orphaned_uids": [],
            "circular_references": [],
            "broken_chains": [],
            "depth_violations": [],
            "validation_passed": True,
            "validation_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Check for root UIDs (no parent)
        for uid, prompt in self.prompt_registry.items():
            if prompt.parent_uid is None:
                validation_results["root_uids"].append(uid)
        
        # Check for orphaned UIDs (parent doesn't exist)
        for uid, prompt in self.prompt_registry.items():
            if prompt.parent_uid and prompt.parent_uid not in self.prompt_registry:
                validation_results["orphaned_uids"].append({
                    "uid": uid,
                    "missing_parent": prompt.parent_uid
                })
                validation_results["validation_passed"] = False
        
        # Check for circular references
        for uid in self.prompt_registry.keys():
            if self._has_circular_reference(uid):
                validation_results["circular_references"].append(uid)
                validation_results["validation_passed"] = False
        
        # Check depth violations (depth > 10)
        for uid, prompt in self.prompt_registry.items():
            if prompt.lineage_depth > 10:
                validation_results["depth_violations"].append({
                    "uid": uid,
                    "depth": prompt.lineage_depth
                })
                validation_results["validation_passed"] = False
        
        # Check for broken parent-child relationships
        for uid, prompt in self.prompt_registry.items():
            for child_uid in prompt.children_uids:
                if child_uid not in self.prompt_registry:
                    validation_results["broken_chains"].append({
                        "parent": uid,
                        "missing_child": child_uid
                    })
                    validation_results["validation_passed"] = False
                else:
                    child_prompt = self.prompt_registry[child_uid]
                    if child_prompt.parent_uid != uid:
                        validation_results["broken_chains"].append({
                            "parent": uid,
                            "child": child_uid,
                            "issue": "child_parent_mismatch"
                        })
                        validation_results["validation_passed"] = False
        
        # Print validation results
        print(f"📊 Validation Results:")
        print(f"   Total UIDs: {validation_results['total_uids']}")
        print(f"   Root UIDs: {len(validation_results['root_uids'])}")
        print(f"   Orphaned UIDs: {len(validation_results['orphaned_uids'])}")
        print(f"   Circular References: {len(validation_results['circular_references'])}")
        print(f"   Broken Chains: {len(validation_results['broken_chains'])}")
        print(f"   Depth Violations: {len(validation_results['depth_violations'])}")
        
        if validation_results["validation_passed"]:
            print("✅ Lineage integrity validation PASSED")
        else:
            print("❌ Lineage integrity validation FAILED")
            if validation_results["orphaned_uids"]:
                print("   Orphaned UIDs found:")
                for orphan in validation_results["orphaned_uids"]:
                    print(f"     - {orphan['uid']} (parent: {orphan['missing_parent']})")
        
        return validation_results
    
    def _has_circular_reference(self, start_uid: str, visited: Set[str] = None) -> bool:
        """Check if UID has circular reference in lineage"""
        if visited is None:
            visited = set()
        
        if start_uid in visited:
            return True
        
        visited.add(start_uid)
        prompt = self.prompt_registry.get(start_uid)
        
        if prompt and prompt.children_uids:
            for child_uid in prompt.children_uids:
                if self._has_circular_reference(child_uid, visited.copy()):
                    return True
        
        return False
    
    def get_chain_summary(self) -> Dict[str, Any]:
        """Get summary of all fallback chains"""
        summary = {
            "total_chains": len(self.lineage_chains),
            "total_uids": len(self.prompt_registry),
            "chains": {}
        }
        
        for root_uid, chain in self.lineage_chains.items():
            chain_info = {
                "root_uid": root_uid,
                "length": len(chain),
                "agents_used": list(set(self.prompt_registry[uid].agent_id for uid in chain)),
                "fallback_count": sum(1 for uid in chain if self.prompt_registry[uid].fallback_flag),
                "success": self.prompt_registry[chain[-1]].success,
                "final_confidence": self.prompt_registry[chain[-1]].confidence_score
            }
            summary["chains"][root_uid] = chain_info
        
        return summary
    
    def export_chains_json(self, filename: str = "mas_handoff_chains.json"):
        """Export all chains to JSON for analysis"""
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_uids": len(self.prompt_registry),
                "total_chains": len(self.lineage_chains)
            },
            "prompt_registry": {uid: asdict(prompt) for uid, prompt in self.prompt_registry.items()},
            "lineage_chains": self.lineage_chains,
            "chain_summary": self.get_chain_summary()
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"📁 Chains exported to {filename}")
        return filename


# TODO: Define PromptUID dataclass ✅
# TODO: Mock 3–5 UID fallback chains ✅
# TODO: simulate_prompt_handoff(uid) to print lineage ✅
# TODO: Highlight fallback points in output ✅
# TODO: Test CLI run with sample UID input ✅


def run_handoff_tests():
    """
    CLI-style test function to run lineage prints and simulations.
    
    Tests all mock chains and validates system behavior.
    """
    print("🚀 MAS Handoff Tester - CLI Test Run")
    print("=" * 50)
    
    # Initialize tester
    tester = MASHandoffTester()
    
    # Test each root chain
    test_uids = [
        "20250610_a7f2c9_gpt4_001",    # Simple fallback
        "20250610_b8e3d1_gpt4_001",    # Multi-level escalation  
        "20250610_c9f4e2_gpt4_001",    # Resource exhaustion
        "20250610_d1a5f3_claude_001",  # Quality failure
        "20250610_e2b6g4_gpt4_001"     # Complex mutation
    ]
    
    simulation_results = []
    
    for uid in test_uids:
        result = tester.simulate_prompt_handoff(uid)
        simulation_results.append(result)
        print("\n" + "─" * 60)
    
    # Validate lineage integrity
    validation_result = tester.validate_lineage_integrity()
    
    # Export results
    export_file = tester.export_chains_json()
    
    # Summary report
    print(f"\n📋 Test Summary:")
    print(f"   Chains Tested: {len(simulation_results)}")
    print(f"   Successful Simulations: {sum(1 for r in simulation_results if r.get('success'))}")
    print(f"   Validation Status: {'✅ PASSED' if validation_result['validation_passed'] else '❌ FAILED'}")
    print(f"   Export File: {export_file}")
    
    return {
        "simulation_results": simulation_results,
        "validation_result": validation_result,
        "export_file": export_file
    }


if __name__ == "__main__":
    """
    Main CLI entry point for MAS Handoff Tester.
    
    Run comprehensive tests of UID threading and fallback simulation.
    """
    import sys
    
    if len(sys.argv) > 1:
        # Test specific UID if provided
        test_uid = sys.argv[1]
        tester = MASHandoffTester()
        result = tester.simulate_prompt_handoff(test_uid)
        print(f"\n📊 Result: {result}")
    else:
        # Run full test suite
        run_handoff_tests() 