#!/usr/bin/env python3
"""
GitBridge Collaborative Composition Pipeline
Phase: GBP21
Part: P21P3
Step: P21P3S1
Task: P21P3S1T1 - Composition Pipeline Implementation

Assemble subtask results into unified output.
Integrate confidence scoring + attribution for each subagent.
Logic collision checker to pre-screen for conflicting logic or factual divergence.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P21P3 Schema]
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
import sys
from difflib import SequenceMatcher
import hashlib
import argparse

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

@dataclass
class SubtaskResult:
    """Represents the result of a completed subtask."""
    subtask_id: str
    agent_id: str
    agent_name: str
    content: str
    confidence_score: float
    completion_time: float
    token_usage: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class CompositionResult:
    """Represents the final composed output."""
    master_task_id: str
    composed_content: str
    confidence_score: float
    attribution_map: Dict[str, List[str]]  # content_hash -> [agent_ids]
    conflict_resolution_log: List[Dict[str, Any]]
    composition_strategy: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConflictInfo:
    """Represents a detected conflict between subtask results."""
    conflict_id: str
    subtask_ids: List[str]
    agent_ids: List[str]
    conflict_type: str  # factual, logical, contradictory, quality
    severity: float  # 0.0 to 1.0
    description: str
    resolution_strategy: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class CollaborativeComposer:
    """
    Collaborative composition pipeline for assembling subtask results.
    
    Phase: GBP21
    Part: P21P3
    Step: P21P3S1
    Task: P21P3S1T1 - Core Implementation
    
    Features:
    - Assemble subtask results into unified output
    - Confidence scoring and attribution tracking
    - Logic collision detection and resolution
    - Quality assurance and validation
    """
    
    def __init__(self, roles_config_path: str = "roles_config.json"):
        """
        Initialize the collaborative composer.
        
        Args:
            roles_config_path: Path to roles configuration file
        """
        self.roles_config = self._load_roles_config(roles_config_path)
        self.composition_history = []
        self.conflict_resolution_strategies = {
            'factual': self._resolve_factual_conflict,
            'logical': self._resolve_logical_conflict,
            'contradictory': self._resolve_contradictory_conflict,
            'quality': self._resolve_quality_conflict
        }
        
        logger.info("[P21P3S1T1] CollaborativeComposer initialized")
        
    def _load_roles_config(self, config_path: str) -> Dict[str, Any]:
        """Load roles configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"[P21P3S1T1] Loaded roles config with {len(config.get('agents', []))} agents")
            return config
        except Exception as e:
            logger.error(f"[P21P3S1T1] Failed to load roles config: {e}")
            return {}
            
    def compose_results(
        self,
        master_task_id: str,
        subtask_results: List[SubtaskResult],
        composition_strategy: str = "hierarchical"
    ) -> CompositionResult:
        """
        Compose subtask results into unified output.
        
        Args:
            master_task_id: ID of the master task
            subtask_results: List of completed subtask results
            composition_strategy: Strategy for composing results
            
        Returns:
            CompositionResult: Composed output with attribution and conflict resolution
        """
        logger.info(f"[P21P3S1T1] Composing results for task {master_task_id} with {len(subtask_results)} subtasks")
        
        # Detect conflicts
        conflicts = self._detect_conflicts(subtask_results)
        logger.info(f"[P21P3S1T1] Detected {len(conflicts)} conflicts")
        
        # Resolve conflicts
        resolved_results = self._resolve_conflicts(subtask_results, conflicts)
        
        # Compose final output
        composed_content = self._compose_content(resolved_results, composition_strategy)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(resolved_results)
        
        # Generate attribution map
        attribution_map = self._generate_attribution_map(resolved_results)
        
        # Create composition result
        composition_result = CompositionResult(
            master_task_id=master_task_id,
            composed_content=composed_content,
            confidence_score=confidence_score,
            attribution_map=attribution_map,
            conflict_resolution_log=[conflict.__dict__ for conflict in conflicts],
            composition_strategy=composition_strategy
        )
        
        # Store in history
        self.composition_history.append(composition_result)
        
        logger.info(f"[P21P3S1T1] Composition completed with confidence {confidence_score:.2f}")
        return composition_result
        
    def _detect_conflicts(self, subtask_results: List[SubtaskResult]) -> List[ConflictInfo]:
        """Detect conflicts between subtask results."""
        conflicts = []
        conflict_counter = 0
        
        # Compare each pair of results
        for i, result1 in enumerate(subtask_results):
            for j, result2 in enumerate(subtask_results[i+1:], i+1):
                conflict = self._compare_results(result1, result2)
                if conflict:
                    conflict_counter += 1
                    conflict.conflict_id = f"conflict_{conflict_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    conflicts.append(conflict)
                    
        return conflicts
        
    def _compare_results(self, result1: SubtaskResult, result2: SubtaskResult) -> Optional[ConflictInfo]:
        """Compare two subtask results for conflicts."""
        # Calculate similarity
        similarity = self._calculate_similarity(result1.content, result2.content)
        
        # Detect different types of conflicts
        conflicts = []
        
        # Factual conflicts (contradictory facts)
        if similarity < 0.3 and self._has_factual_conflict(result1.content, result2.content):
            conflicts.append(('factual', 0.8))
            
        # Logical conflicts (contradictory logic)
        if similarity < 0.4 and self._has_logical_conflict(result1.content, result2.content):
            conflicts.append(('logical', 0.7))
            
        # Quality conflicts (significant quality differences)
        quality_diff = abs(result1.confidence_score - result2.confidence_score)
        if quality_diff > 0.3:
            conflicts.append(('quality', quality_diff))
            
        # Contradictory conflicts (direct contradictions)
        if self._has_contradiction(result1.content, result2.content):
            conflicts.append(('contradictory', 0.9))
            
        if conflicts:
            # Return the highest severity conflict
            conflict_type, severity = max(conflicts, key=lambda x: x[1])
            return ConflictInfo(
                conflict_id="",
                subtask_ids=[result1.subtask_id, result2.subtask_id],
                agent_ids=[result1.agent_id, result2.agent_id],
                conflict_type=conflict_type,
                severity=severity,
                description=f"Conflict between {result1.agent_name} and {result2.agent_name}",
                resolution_strategy=self._get_resolution_strategy(conflict_type)
            )
            
        return None
        
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings."""
        return SequenceMatcher(None, content1.lower(), content2.lower()).ratio()
        
    def _has_factual_conflict(self, content1: str, content2: str) -> bool:
        """Check for factual conflicts between content."""
        # Extract facts (numbers, dates, names, etc.)
        facts1 = self._extract_facts(content1)
        facts2 = self._extract_facts(content2)
        
        # Check for contradictory facts
        for fact1 in facts1:
            for fact2 in facts2:
                if self._facts_contradict(fact1, fact2):
                    return True
                    
        return False
        
    def _extract_facts(self, content: str) -> List[str]:
        """Extract factual information from content."""
        facts = []
        
        # Extract numbers
        numbers = re.findall(r'\d+(?:\.\d+)?', content)
        facts.extend(numbers)
        
        # Extract dates
        dates = re.findall(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}', content)
        facts.extend(dates)
        
        # Extract names (capitalized words)
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        facts.extend(names)
        
        return facts
        
    def _facts_contradict(self, fact1: str, fact2: str) -> bool:
        """Check if two facts contradict each other."""
        # Simple contradiction detection
        if fact1.isdigit() and fact2.isdigit():
            return fact1 != fact2
        elif fact1 in fact2 or fact2 in fact1:
            return False  # One is subset of other
        else:
            return False
            
    def _has_logical_conflict(self, content1: str, content2: str) -> bool:
        """Check for logical conflicts between content."""
        # Extract logical statements
        logical1 = self._extract_logical_statements(content1)
        logical2 = self._extract_logical_statements(content2)
        
        # Check for contradictory logic
        for logic1 in logical1:
            for logic2 in logical2:
                if self._logic_contradicts(logic1, logic2):
                    return True
                    
        return False
        
    def _extract_logical_statements(self, content: str) -> List[str]:
        """Extract logical statements from content."""
        # Look for conditional statements, conclusions, etc.
        logical_patterns = [
            r'if\s+.+?\s+then\s+.+',
            r'because\s+.+',
            r'therefore\s+.+',
            r'consequently\s+.+',
            r'as\s+a\s+result\s+.+'
        ]
        
        statements = []
        for pattern in logical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            statements.extend(matches)
            
        return statements
        
    def _logic_contradicts(self, logic1: str, logic2: str) -> bool:
        """Check if two logical statements contradict each other."""
        # Simple contradiction detection based on keywords
        negative_words = ['not', 'never', 'no', 'false', 'incorrect', 'wrong']
        positive_words = ['yes', 'true', 'correct', 'right', 'valid']
        
        logic1_lower = logic1.lower()
        logic2_lower = logic2.lower()
        
        # Check for direct contradictions
        for neg_word in negative_words:
            for pos_word in positive_words:
                if neg_word in logic1_lower and pos_word in logic2_lower:
                    return True
                if pos_word in logic1_lower and neg_word in logic2_lower:
                    return True
                    
        return False
        
    def _has_contradiction(self, content1: str, content2: str) -> bool:
        """Check for direct contradictions between content."""
        # Look for direct contradictions
        contradiction_patterns = [
            (r'(\w+)\s+is\s+(\w+)', r'\1\s+is\s+not\s+\2'),
            (r'(\w+)\s+are\s+(\w+)', r'\1\s+are\s+not\s+\2'),
            (r'(\w+)\s+should\s+(\w+)', r'\1\s+should\s+not\s+\2')
        ]
        
        for pattern, negation_pattern in contradiction_patterns:
            matches1 = re.findall(pattern, content1, re.IGNORECASE)
            # Fix the negation pattern by properly handling group references
            negation_pattern_fixed = negation_pattern.replace(r'\1', r'\\1').replace(r'\2', r'\\2')
            matches2 = re.findall(negation_pattern_fixed, content2, re.IGNORECASE)
            
            if matches1 and matches2:
                return True
                
        return False
        
    def _get_resolution_strategy(self, conflict_type: str) -> str:
        """Get resolution strategy for conflict type."""
        strategies = {
            'factual': 'meta_evaluator',
            'logical': 'synthesis',
            'contradictory': 'arbitration',
            'quality': 'selection'
        }
        return strategies.get(conflict_type, 'synthesis')
        
    def _resolve_conflicts(
        self,
        subtask_results: List[SubtaskResult],
        conflicts: List[ConflictInfo]
    ) -> List[SubtaskResult]:
        """Resolve conflicts and return resolved results."""
        resolved_results = subtask_results.copy()
        
        for conflict in conflicts:
            if conflict.conflict_type in self.conflict_resolution_strategies:
                resolver = self.conflict_resolution_strategies[conflict.conflict_type]
                resolved_results = resolver(resolved_results, conflict)
                
        return resolved_results
        
    def _resolve_factual_conflict(
        self,
        results: List[SubtaskResult],
        conflict: ConflictInfo
    ) -> List[SubtaskResult]:
        """Resolve factual conflicts using meta-evaluator approach."""
        # For factual conflicts, prefer higher confidence results
        conflicting_results = [r for r in results if r.subtask_id in conflict.subtask_ids]
        
        if conflicting_results:
            # Select the result with highest confidence
            best_result = max(conflicting_results, key=lambda r: r.confidence_score)
            
            # Mark other results as resolved
            for result in conflicting_results:
                if result.subtask_id != best_result.subtask_id:
                    result.metadata['conflict_resolved'] = True
                    result.metadata['resolution_reason'] = 'lower_confidence'
                    
        return results
        
    def _resolve_logical_conflict(
        self,
        results: List[SubtaskResult],
        conflict: ConflictInfo
    ) -> List[SubtaskResult]:
        """Resolve logical conflicts using synthesis approach."""
        # For logical conflicts, try to synthesize the approaches
        conflicting_results = [r for r in results if r.subtask_id in conflict.subtask_ids]
        
        if len(conflicting_results) >= 2:
            # Create a synthesis result
            synthesis_content = self._synthesize_logical_approaches(conflicting_results)
            
            # Create a new synthesis result
            synthesis_result = SubtaskResult(
                subtask_id=f"synthesis_{conflict.conflict_id}",
                agent_id="synthesizer_specialist",
                agent_name="Synthesizer",
                content=synthesis_content,
                confidence_score=sum(r.confidence_score for r in conflicting_results) / len(conflicting_results),
                completion_time=0.0,
                token_usage={"total": 0, "prompt": 0, "completion": 0},
                metadata={"synthesis_of": [r.subtask_id for r in conflicting_results]}
            )
            
            # Mark original results as resolved
            for result in conflicting_results:
                result.metadata['conflict_resolved'] = True
                result.metadata['resolution_reason'] = 'synthesized'
                
            # Add synthesis result
            results.append(synthesis_result)
            
        return results
        
    def _synthesize_logical_approaches(self, results: List[SubtaskResult]) -> str:
        """Synthesize logical approaches from multiple results."""
        # Simple synthesis: combine approaches with clear attribution
        synthesis_parts = []
        
        for i, result in enumerate(results, 1):
            synthesis_parts.append(f"Approach {i} ({result.agent_name}): {result.content}")
            
        synthesis_parts.append("\nSynthesized Approach:")
        synthesis_parts.append("Combining the above approaches, the recommended solution is:")
        
        # Extract key points from each approach
        key_points = []
        for result in results:
            # Simple key point extraction
            sentences = result.content.split('.')
            key_points.extend(sentences[:2])  # Take first two sentences as key points
            
        synthesis_parts.extend(key_points)
        
        return "\n".join(synthesis_parts)
        
    def _resolve_contradictory_conflict(
        self,
        results: List[SubtaskResult],
        conflict: ConflictInfo
    ) -> List[SubtaskResult]:
        """Resolve contradictory conflicts using arbitration."""
        # For contradictory conflicts, use arbitration based on agent reliability
        conflicting_results = [r for r in results if r.subtask_id in conflict.subtask_ids]
        
        if conflicting_results:
            # Get agent reliability scores
            agent_scores = {}
            for result in conflicting_results:
                agent = self._get_agent_info(result.agent_id)
                if agent:
                    reliability = agent.get('priority_weight', 0.5)
                    agent_scores[result.subtask_id] = reliability * result.confidence_score
                    
            # Select the result with highest weighted score
            if agent_scores:
                best_subtask_id = max(agent_scores, key=agent_scores.get)
                
                # Mark other results as resolved
                for result in conflicting_results:
                    if result.subtask_id != best_subtask_id:
                        result.metadata['conflict_resolved'] = True
                        result.metadata['resolution_reason'] = 'arbitration'
                        
        return results
        
    def _resolve_quality_conflict(
        self,
        results: List[SubtaskResult],
        conflict: ConflictInfo
    ) -> List[SubtaskResult]:
        """Resolve quality conflicts by selecting higher quality content."""
        # For quality conflicts, prefer higher quality results
        conflicting_results = [r for r in results if r.subtask_id in conflict.subtask_ids]
        
        if conflicting_results:
            # Select the result with highest quality (confidence + agent reliability)
            best_result = max(conflicting_results, key=lambda r: self._calculate_quality_score(r))
            
            # Mark other results as resolved
            for result in conflicting_results:
                if result.subtask_id != best_result.subtask_id:
                    result.metadata['conflict_resolved'] = True
                    result.metadata['resolution_reason'] = 'lower_quality'
                    
        return results
        
    def _calculate_quality_score(self, result: SubtaskResult) -> float:
        """Calculate quality score for a result."""
        agent = self._get_agent_info(result.agent_id)
        agent_weight = agent.get('priority_weight', 0.5) if agent else 0.5
        
        # Combine confidence and agent reliability
        return result.confidence_score * 0.7 + agent_weight * 0.3
        
    def _get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information from roles config."""
        agents = self.roles_config.get('agents', [])
        for agent in agents:
            if agent.get('agent_id') == agent_id:
                return agent
        return None
        
    def _compose_content(
        self,
        results: List[SubtaskResult],
        strategy: str
    ) -> str:
        """Compose final content from resolved results."""
        if strategy == "hierarchical":
            return self._hierarchical_composition(results)
        elif strategy == "sequential":
            return self._sequential_composition(results)
        elif strategy == "synthetic":
            return self._synthetic_composition(results)
        else:
            return self._hierarchical_composition(results)
            
    def _hierarchical_composition(self, results: List[SubtaskResult]) -> str:
        """Compose content using hierarchical approach."""
        # Sort by confidence and agent priority
        sorted_results = sorted(results, key=lambda r: self._calculate_quality_score(r), reverse=True)
        
        composition_parts = []
        
        # Add main content from highest quality result
        if sorted_results:
            main_result = sorted_results[0]
            composition_parts.append(f"# Main Analysis\n\n{main_result.content}")
            
        # Add supplementary content from other results
        if len(sorted_results) > 1:
            composition_parts.append("\n# Supplementary Insights\n")
            for result in sorted_results[1:]:
                if not result.metadata.get('conflict_resolved'):
                    composition_parts.append(f"## {result.agent_name}\n\n{result.content}\n")
                    
        return "\n".join(composition_parts)
        
    def _sequential_composition(self, results: List[SubtaskResult]) -> str:
        """Compose content using sequential approach."""
        composition_parts = []
        
        for i, result in enumerate(results, 1):
            if not result.metadata.get('conflict_resolved'):
                composition_parts.append(f"## Step {i}: {result.agent_name}\n\n{result.content}\n")
                
        return "\n".join(composition_parts)
        
    def _synthetic_composition(self, results: List[SubtaskResult]) -> str:
        """Compose content using synthetic approach."""
        # Extract key insights from each result
        insights = []
        
        for result in results:
            if not result.metadata.get('conflict_resolved'):
                # Extract key sentences (simple approach)
                sentences = result.content.split('.')
                key_sentences = sentences[:3]  # Take first 3 sentences
                insights.extend([f"- {s.strip()}" for s in key_sentences if s.strip()])
                
        composition_parts = [
            "# Synthesized Analysis\n",
            "## Key Insights\n",
            "\n".join(insights),
            "\n## Comprehensive Analysis\n"
        ]
        
        # Add full content from highest quality result
        if results:
            best_result = max(results, key=lambda r: self._calculate_quality_score(r))
            composition_parts.append(best_result.content)
            
        return "\n".join(composition_parts)
        
    def _calculate_confidence_score(self, results: List[SubtaskResult]) -> float:
        """Calculate overall confidence score for composed result."""
        if not results:
            return 0.0
            
        # Calculate weighted average confidence
        total_weight = 0
        weighted_sum = 0
        
        for result in results:
            if not result.metadata.get('conflict_resolved'):
                weight = self._calculate_quality_score(result)
                weighted_sum += result.confidence_score * weight
                total_weight += weight
                
        return weighted_sum / total_weight if total_weight > 0 else 0.0
        
    def _generate_attribution_map(self, results: List[SubtaskResult]) -> Dict[str, List[str]]:
        """Generate attribution map for composed content."""
        attribution_map = {}
        
        for result in results:
            if not result.metadata.get('conflict_resolved'):
                # Create content hash
                content_hash = hashlib.md5(result.content.encode()).hexdigest()
                
                if content_hash not in attribution_map:
                    attribution_map[content_hash] = []
                    
                attribution_map[content_hash].append(result.agent_id)
                
        return attribution_map
        
    def export_attribution_log(self, output_path: str = "attribution_log.json") -> None:
        """Export attribution logs to JSON file."""
        logs = []
        for composition in self.composition_history:
            log_entry = {
                'master_task_id': composition.master_task_id,
                'confidence_score': composition.confidence_score,
                'composition_strategy': composition.composition_strategy,
                'created_at': composition.created_at.isoformat(),
                'attribution_map': composition.attribution_map,
                'conflict_resolution_log': composition.conflict_resolution_log
            }
            logs.append(log_entry)
            
        try:
            with open(output_path, 'w') as f:
                json.dump(logs, f, indent=2)
            logger.info(f"[P21P3S1T1] Attribution logs exported to {output_path}")
        except Exception as e:
            logger.error(f"[P21P3S1T1] Failed to export attribution logs: {e}")

def main():
    """Test the collaborative composer with dry-run/preview support."""
    parser = argparse.ArgumentParser(description='GitBridge Collaborative Composer')
    parser.add_argument('--dry-run', action='store_true', help='Preview composition without storing or exporting')
    args = parser.parse_args()
    
    logger.info("[P21P3S1T1] Testing Collaborative Composition Pipeline")
    
    composer = CollaborativeComposer()
    
    # Create sample subtask results
    results = [
        SubtaskResult(
            subtask_id="task_1_analysis",
            agent_id="openai_gpt4o",
            agent_name="OpenAI",
            content="Python decorators are functions that modify other functions. They use the @ syntax and are commonly used for logging, authentication, and caching.",
            confidence_score=0.9,
            completion_time=2.5,
            token_usage={"total": 150, "prompt": 50, "completion": 100}
        ),
        SubtaskResult(
            subtask_id="task_1_explanation",
            agent_id="chatgpt_gpt4",
            agent_name="ChatGPT",
            content="Decorators in Python are a way to modify or enhance functions without changing their source code. They are denoted by the @ symbol and can be used for various purposes like timing, validation, and memoization.",
            confidence_score=0.85,
            completion_time=2.0,
            token_usage={"total": 140, "prompt": 45, "completion": 95}
        ),
        SubtaskResult(
            subtask_id="task_1_example",
            agent_id="cursor_assistant",
            agent_name="Cursor",
            content="Here's a simple decorator example: @timer def slow_function(): time.sleep(1). The @timer decorator would measure execution time.",
            confidence_score=0.95,
            completion_time=1.5,
            token_usage={"total": 120, "prompt": 40, "completion": 80}
        )
    ]
    
    if args.dry_run:
        print("🔍 DRY-RUN MODE: Previewing composition")
        composition = composer.compose_results("task_1", results, "hierarchical")
        print(f"Composed content length: {len(composition.composed_content)} characters")
        print(f"Confidence score: {composition.confidence_score:.2f}")
        print(f"Attribution map: {composition.attribution_map}")
        print(f"Conflicts resolved: {len(composition.conflict_resolution_log)}")
        print("\n--- Preview Output ---\n")
        print(composition.composed_content)
        print("\n--- End Preview ---\n")
        return
    
    # Compose results (normal mode)
    composition = composer.compose_results("task_1", results, "hierarchical")
    print(f"Composed content length: {len(composition.composed_content)} characters")
    print(f"Confidence score: {composition.confidence_score:.2f}")
    print(f"Attribution map: {composition.attribution_map}")
    print(f"Conflicts resolved: {len(composition.conflict_resolution_log)}")
    
    # Export attribution logs
    composer.export_attribution_log()

if __name__ == "__main__":
    main() 