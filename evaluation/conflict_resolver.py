#!/usr/bin/env python3
"""
GitBridge Conflict Resolution Logic
Phase: GBP20
Part: P20P8
Step: P20P8S5
Task: P20P8S5T1 - Conflict Resolution Implementation

Design fallback if agents disagree on response, use meta-evaluator for arbitration,
and combine responses using synthesis function.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P20P8 Schema]
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class ConflictType(Enum):
    """Types of conflicts between AI agents."""
    DIVERGENT_RESPONSES = "divergent_responses"
    RATING_DIVERGENCE = "rating_divergence"
    CONTRADICTORY_ANSWERS = "contradictory_answers"
    QUALITY_DISPUTE = "quality_dispute"

@dataclass
class ConflictResolution:
    """Result of conflict resolution process."""
    conflict_type: ConflictType
    original_responses: Dict[str, str]
    resolution_method: str
    final_response: str
    confidence: float
    arbitration_notes: str
    synthesis_components: List[str]

class ConflictResolver:
    """
    Conflict resolution system for AI agent disagreements.
    
    Phase: GBP20
    Part: P20P8
    Step: P20P8S5
    Task: P20P8S5T1 - Core Implementation
    
    Features:
    - Detect conflicts between agent responses
    - Use meta-evaluator for arbitration
    - Synthesize responses when appropriate
    - Provide confidence scores for resolutions
    """
    
    def __init__(self):
        """Initialize the conflict resolver."""
        self.conflict_history = []
        
        logger.info("[P20P8S5T1] ConflictResolver initialized")
        
    def detect_conflict(
        self,
        openai_response: str,
        grok_response: str,
        prompt: str,
        task_type: str = "general"
    ) -> Optional[ConflictType]:
        """
        Detect if there's a conflict between agent responses.
        
        Args:
            openai_response: OpenAI's response
            grok_response: Grok's response
            prompt: Original prompt
            task_type: Type of task
            
        Returns:
            ConflictType or None if no conflict detected
        """
        # Check for contradictory answers
        if self._has_contradictory_answers(openai_response, grok_response, task_type):
            return ConflictType.CONTRADICTORY_ANSWERS
            
        # Check for significant quality differences
        if self._has_quality_dispute(openai_response, grok_response):
            return ConflictType.QUALITY_DISPUTE
            
        # Check for divergent approaches
        if self._has_divergent_approaches(openai_response, grok_response, task_type):
            return ConflictType.DIVERGENT_RESPONSES
            
        return None
        
    def resolve_conflict(
        self,
        conflict_type: ConflictType,
        openai_response: str,
        grok_response: str,
        prompt: str,
        task_type: str = "general"
    ) -> ConflictResolution:
        """
        Resolve a detected conflict using appropriate method.
        
        Args:
            conflict_type: Type of conflict detected
            openai_response: OpenAI's response
            grok_response: Grok's response
            prompt: Original prompt
            task_type: Type of task
            
        Returns:
            ConflictResolution: Resolution result
        """
        logger.info(f"[P20P8S5T1] Resolving {conflict_type.value} conflict")
        
        if conflict_type == ConflictType.CONTRADICTORY_ANSWERS:
            return self._resolve_contradictory_answers(
                openai_response, grok_response, prompt, task_type
            )
        elif conflict_type == ConflictType.QUALITY_DISPUTE:
            return self._resolve_quality_dispute(
                openai_response, grok_response, prompt, task_type
            )
        elif conflict_type == ConflictType.DIVERGENT_RESPONSES:
            return self._resolve_divergent_responses(
                openai_response, grok_response, prompt, task_type
            )
        else:
            return self._resolve_generic_conflict(
                openai_response, grok_response, prompt, task_type
            )
            
    def _has_contradictory_answers(
        self,
        openai_response: str,
        grok_response: str,
        task_type: str
    ) -> bool:
        """Check if responses contain contradictory information."""
        # Simple keyword-based contradiction detection
        contradictions = {
            'yes': 'no',
            'true': 'false',
            'correct': 'incorrect',
            'should': 'should not',
            'recommend': 'not recommend'
        }
        
        openai_lower = openai_response.lower()
        grok_lower = grok_response.lower()
        
        for word1, word2 in contradictions.items():
            if (word1 in openai_lower and word2 in grok_lower) or \
               (word2 in openai_lower and word1 in grok_lower):
                return True
                
        return False
        
    def _has_quality_dispute(self, openai_response: str, grok_response: str) -> bool:
        """Check if there's a significant quality difference."""
        # Compare response lengths and structure
        openai_words = len(openai_response.split())
        grok_words = len(grok_response.split())
        
        # If one response is significantly longer/shorter
        if abs(openai_words - grok_words) > max(openai_words, grok_words) * 0.5:
            return True
            
        # Check for structured vs unstructured responses
        openai_structured = any(marker in openai_response for marker in ['1.', '2.', '3.', '- ', '* '])
        grok_structured = any(marker in grok_response for marker in ['1.', '2.', '3.', '- ', '* '])
        
        if openai_structured != grok_structured:
            return True
            
        return False
        
    def _has_divergent_approaches(
        self,
        openai_response: str,
        grok_response: str,
        task_type: str
    ) -> bool:
        """Check if responses use different approaches."""
        # Check for different technical approaches
        technical_indicators = {
            'code_review': ['security', 'performance', 'readability', 'maintainability'],
            'analysis': ['qualitative', 'quantitative', 'theoretical', 'practical'],
            'explanation': ['simple', 'detailed', 'technical', 'non-technical']
        }
        
        indicators = technical_indicators.get(task_type, [])
        openai_lower = openai_response.lower()
        grok_lower = grok_response.lower()
        
        openai_indicators = [ind for ind in indicators if ind in openai_lower]
        grok_indicators = [ind for ind in indicators if ind in grok_lower]
        
        # If they focus on different aspects
        if openai_indicators and grok_indicators and \
           not set(openai_indicators).intersection(set(grok_indicators)):
            return True
            
        return False
        
    def _resolve_contradictory_answers(
        self,
        openai_response: str,
        grok_response: str,
        prompt: str,
        task_type: str
    ) -> ConflictResolution:
        """Resolve contradictory answers using simple arbitration."""
        # For now, use a simple heuristic - prefer the more detailed response
        openai_words = len(openai_response.split())
        grok_words = len(grok_response.split())
        
        if openai_words > grok_words:
            final_response = openai_response
            confidence = 0.6
            winner = 'openai'
        elif grok_words > openai_words:
            final_response = grok_response
            confidence = 0.6
            winner = 'grok'
        else:
            # Tie - synthesize the responses
            final_response = self._synthesize_responses(openai_response, grok_response)
            confidence = 0.5
            winner = 'tie'
            
        return ConflictResolution(
            conflict_type=ConflictType.CONTRADICTORY_ANSWERS,
            original_responses={'openai': openai_response, 'grok': grok_response},
            resolution_method='detail_based_arbitration',
            final_response=final_response,
            confidence=confidence,
            arbitration_notes=f"Used detail-based arbitration. Winner: {winner}",
            synthesis_components=[]
        )
        
    def _resolve_quality_dispute(
        self,
        openai_response: str,
        grok_response: str,
        prompt: str,
        task_type: str
    ) -> ConflictResolution:
        """Resolve quality disputes by combining best aspects."""
        # Analyze strengths of each response
        openai_strengths = self._analyze_response_strengths(openai_response, task_type)
        grok_strengths = self._analyze_response_strengths(grok_response, task_type)
        
        # Synthesize responses based on strengths
        final_response = self._synthesize_by_strengths(
            openai_response, grok_response, openai_strengths, grok_strengths
        )
        
        return ConflictResolution(
            conflict_type=ConflictType.QUALITY_DISPUTE,
            original_responses={'openai': openai_response, 'grok': grok_response},
            resolution_method='strength_based_synthesis',
            final_response=final_response,
            confidence=0.7,
            arbitration_notes="Combined best aspects of both responses",
            synthesis_components=['structure', 'content', 'detail']
        )
        
    def _resolve_divergent_responses(
        self,
        openai_response: str,
        grok_response: str,
        prompt: str,
        task_type: str
    ) -> ConflictResolution:
        """Resolve divergent responses by providing multiple perspectives."""
        # Create a multi-perspective response
        final_response = self._create_multi_perspective_response(
            openai_response, grok_response, task_type
        )
        
        return ConflictResolution(
            conflict_type=ConflictType.DIVERGENT_RESPONSES,
            original_responses={'openai': openai_response, 'grok': grok_response},
            resolution_method='multi_perspective_synthesis',
            final_response=final_response,
            confidence=0.8,
            arbitration_notes="Provided multiple perspectives on the topic",
            synthesis_components=['perspective_1', 'perspective_2', 'synthesis']
        )
        
    def _resolve_generic_conflict(
        self,
        openai_response: str,
        grok_response: str,
        prompt: str,
        task_type: str
    ) -> ConflictResolution:
        """Generic conflict resolution using simple synthesis."""
        final_response = self._synthesize_responses(openai_response, grok_response)
        
        return ConflictResolution(
            conflict_type=ConflictType.DIVERGENT_RESPONSES,
            original_responses={'openai': openai_response, 'grok': grok_response},
            resolution_method='generic_synthesis',
            final_response=final_response,
            confidence=0.6,
            arbitration_notes="Applied generic synthesis to resolve conflict",
            synthesis_components=['combined_content']
        )
        
    def _analyze_response_strengths(self, response: str, task_type: str) -> List[str]:
        """Analyze the strengths of a response."""
        strengths = []
        
        # Check for structure
        if any(marker in response for marker in ['1.', '2.', '3.', '- ', '* ']):
            strengths.append('structure')
            
        # Check for detail
        if len(response.split()) > 100:
            strengths.append('detail')
            
        # Check for technical depth
        technical_terms = ['algorithm', 'complexity', 'optimization', 'implementation']
        if any(term in response.lower() for term in technical_terms):
            strengths.append('technical_depth')
            
        # Check for clarity
        if 'example' in response.lower() or 'for instance' in response.lower():
            strengths.append('clarity')
            
        return strengths
        
    def _synthesize_by_strengths(
        self,
        openai_response: str,
        grok_response: str,
        openai_strengths: List[str],
        grok_strengths: List[str]
    ) -> str:
        """Synthesize responses based on their strengths."""
        synthesis_parts = []
        
        # Use OpenAI's structure if it's better
        if 'structure' in openai_strengths and 'structure' not in grok_strengths:
            synthesis_parts.append("Structured approach from OpenAI:")
            synthesis_parts.append(openai_response)
        elif 'structure' in grok_strengths and 'structure' not in openai_strengths:
            synthesis_parts.append("Structured approach from Grok:")
            synthesis_parts.append(grok_response)
        else:
            # Combine both
            synthesis_parts.append("Combined insights:")
            synthesis_parts.append(f"OpenAI: {openai_response}")
            synthesis_parts.append(f"Grok: {grok_response}")
            
        return "\n\n".join(synthesis_parts)
        
    def _create_multi_perspective_response(
        self,
        openai_response: str,
        grok_response: str,
        task_type: str
    ) -> str:
        """Create a multi-perspective response."""
        return f"""Multiple Perspectives on this {task_type} task:

**OpenAI's Perspective:**
{openai_response}

**Grok's Perspective:**
{grok_response}

**Synthesis:**
Both approaches provide valuable insights. Consider the context and requirements when choosing the most appropriate solution."""
        
    def _synthesize_responses(self, openai_response: str, grok_response: str) -> str:
        """Simple synthesis of two responses."""
        return f"""Combined Response:

{openai_response}

Additional insights from alternative approach:
{grok_response}"""
        
    def get_conflict_history(self) -> List[Dict[str, Any]]:
        """Get history of resolved conflicts."""
        return self.conflict_history
        
    def store_resolution(self, resolution: ConflictResolution) -> None:
        """Store a conflict resolution for history."""
        self.conflict_history.append({
            'timestamp': resolution.conflict_type,
            'conflict_type': resolution.conflict_type.value,
            'resolution_method': resolution.resolution_method,
            'confidence': resolution.confidence,
            'arbitration_notes': resolution.arbitration_notes
        })

def main():
    """Test the conflict resolver."""
    logger.info("[P20P8S5T1] Testing Conflict Resolution System")
    
    resolver = ConflictResolver()
    
    # Test case 1: Contradictory answers
    openai_response = "Yes, this approach is recommended for production use."
    grok_response = "No, this approach should not be used in production due to security concerns."
    
    conflict = resolver.detect_conflict(openai_response, grok_response, "Should we use this approach?", "analysis")
    if conflict:
        resolution = resolver.resolve_conflict(conflict, openai_response, grok_response, "Should we use this approach?", "analysis")
        print(f"Conflict resolved: {resolution.confidence}")
        
    # Test case 2: Quality dispute
    openai_response = "This is a simple answer."
    grok_response = "This is a very detailed answer with multiple points:\n1. First point\n2. Second point\n3. Third point with examples and explanations."
    
    conflict = resolver.detect_conflict(openai_response, grok_response, "Explain this concept", "explanation")
    if conflict:
        resolution = resolver.resolve_conflict(conflict, openai_response, grok_response, "Explain this concept", "explanation")
        print(f"Quality dispute resolved: {resolution.confidence}")

if __name__ == "__main__":
    main()
