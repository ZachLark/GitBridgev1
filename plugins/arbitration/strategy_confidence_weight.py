#!/usr/bin/env python3
"""
GitBridge Confidence Weight Arbitration Strategy
Phase: GBP22
Part: P22P4
Step: P22P4S2
Task: P22P4S2T1 - Confidence Weight Strategy Implementation

Confidence weight strategy for arbitration.
Selects the agent with the highest confidence score.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P22P4 Schema]
"""

import logging
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path to import arbitration_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from arbitration_engine import ArbitrationPluginBase, ArbitrationConflict, ArbitrationResult, AgentOutput

logger = logging.getLogger(__name__)

class ConfidenceWeightStrategy(ArbitrationPluginBase):
    """
    Confidence weight arbitration strategy.
    
    Phase: GBP22
    Part: P22P4
    Step: P22P4S2
    Task: P22P4S2T1 - Core Implementation
    
    Features:
    - Selects agent with highest confidence
    - Handles confidence ties by execution time
    - Considers error count in confidence calculation
    """
    
    @property
    def strategy_name(self) -> str:
        """Return the name of this arbitration strategy."""
        return "confidence_weight"
        
    def arbitrate(
        self, 
        conflict: ArbitrationConflict, 
        config: Optional[Dict[str, Any]] = None
    ) -> ArbitrationResult:
        """
        Arbitrate using confidence weight strategy.
        
        Args:
            conflict: The conflict to resolve
            config: Optional configuration
            
        Returns:
            ArbitrationResult: The arbitration decision
        """
        logger.info(f"[P22P4S2T1] Using confidence weight strategy for conflict {conflict.conflict_id}")
        
        if not conflict.agent_outputs:
            raise ValueError("No agent outputs to arbitrate")
            
        # Find agent with highest confidence
        best_agent = None
        best_confidence = -1
        best_execution_time = float('inf')
        
        for agent_output in conflict.agent_outputs:
            # Adjust confidence based on error count
            adjusted_confidence = agent_output.confidence
            
            if agent_output.error_count > 0:
                # Penalize for errors
                error_penalty = min(0.2 * agent_output.error_count, 0.5)  # Max 50% penalty
                adjusted_confidence *= (1 - error_penalty)
                
            # Check if this agent has higher confidence
            if adjusted_confidence > best_confidence:
                best_confidence = adjusted_confidence
                best_agent = agent_output
                best_execution_time = agent_output.execution_time_ms or float('inf')
                
            # If confidence is tied, prefer faster execution
            elif adjusted_confidence == best_confidence:
                current_execution_time = agent_output.execution_time_ms or float('inf')
                if current_execution_time < best_execution_time:
                    best_agent = agent_output
                    best_execution_time = current_execution_time
                    
        if best_agent is None:
            raise ValueError("No valid agent found")
            
        # Calculate final confidence
        final_confidence = best_agent.confidence
        
        # Apply any additional confidence adjustments from config
        if config:
            confidence_boost = config.get("confidence_boost", 0.0)
            final_confidence = min(1.0, final_confidence + confidence_boost)
            
        result = ArbitrationResult(
            winner_agent_id=best_agent.agent_id,
            winning_output=best_agent.output,
            confidence=final_confidence,
            strategy_used=self.strategy_name,
            metadata={
                "original_confidence": best_agent.confidence,
                "execution_time_ms": best_agent.execution_time_ms,
                "error_count": best_agent.error_count,
                "total_agents": len(conflict.agent_outputs),
                "confidence_ranking": self._get_confidence_ranking(conflict.agent_outputs)
            }
        )
        
        logger.info(f"[P22P4S2T1] Confidence weight result: {best_agent.agent_id} wins with confidence {final_confidence:.3f}")
        return result
        
    def _get_confidence_ranking(self, agent_outputs: List[AgentOutput]) -> List[Dict[str, Any]]:
        """Get confidence ranking of all agents."""
        rankings = []
        
        for agent_output in agent_outputs:
            # Calculate adjusted confidence
            adjusted_confidence = agent_output.confidence
            if agent_output.error_count > 0:
                error_penalty = min(0.2 * agent_output.error_count, 0.5)
                adjusted_confidence *= (1 - error_penalty)
                
            rankings.append({
                "agent_id": agent_output.agent_id,
                "original_confidence": agent_output.confidence,
                "adjusted_confidence": adjusted_confidence,
                "execution_time_ms": agent_output.execution_time_ms,
                "error_count": agent_output.error_count
            })
            
        # Sort by adjusted confidence (descending)
        rankings.sort(key=lambda x: x["adjusted_confidence"], reverse=True)
        
        # Add rank
        for i, ranking in enumerate(rankings):
            ranking["rank"] = i + 1
            
        return rankings 