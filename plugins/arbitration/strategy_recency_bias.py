#!/usr/bin/env python3
"""
GitBridge Recency Bias Arbitration Strategy
Phase: GBP22
Part: P22P4
Step: P22P4S3
Task: P22P4S3T1 - Recency Bias Strategy Implementation

Recency bias strategy for arbitration.
Favors more recent outputs based on timestamps.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P22P4 Schema]
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path to import arbitration_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from arbitration_engine import ArbitrationPluginBase, ArbitrationConflict, ArbitrationResult, AgentOutput

logger = logging.getLogger(__name__)

class RecencyBiasStrategy(ArbitrationPluginBase):
    """
    Recency bias arbitration strategy.
    
    Phase: GBP22
    Part: P22P4
    Step: P22P4S3
    Task: P22P4S3T1 - Core Implementation
    
    Features:
    - Favors more recent outputs
    - Combines recency with confidence
    - Configurable recency weight
    """
    
    @property
    def strategy_name(self) -> str:
        """Return the name of this arbitration strategy."""
        return "recency_bias"
        
    def arbitrate(
        self, 
        conflict: ArbitrationConflict, 
        config: Optional[Dict[str, Any]] = None
    ) -> ArbitrationResult:
        """
        Arbitrate using recency bias strategy.
        
        Args:
            conflict: The conflict to resolve
            config: Optional configuration
            
        Returns:
            ArbitrationResult: The arbitration decision
        """
        logger.info(f"[P22P4S3T1] Using recency bias strategy for conflict {conflict.conflict_id}")
        
        if not conflict.agent_outputs:
            raise ValueError("No agent outputs to arbitrate")
            
        config = config or {}
        recency_weight = config.get("recency_weight", 0.3)  # 30% weight for recency
        confidence_weight = 1.0 - recency_weight  # 70% weight for confidence
        
        # Find the most recent timestamp
        timestamps = [output.timestamp for output in conflict.agent_outputs]
        most_recent = max(timestamps)
        
        # Calculate scores for each agent
        best_agent = None
        best_score = -1
        
        for agent_output in conflict.agent_outputs:
            # Calculate recency score (0-1, where 1 is most recent)
            time_diff = (most_recent - agent_output.timestamp).total_seconds()
            max_time_diff = max((most_recent - ts).total_seconds() for ts in timestamps)
            
            if max_time_diff > 0:
                recency_score = 1.0 - (time_diff / max_time_diff)
            else:
                recency_score = 1.0  # All timestamps are the same
                
            # Calculate confidence score
            confidence_score = agent_output.confidence
            
            # Apply error penalty to confidence
            if agent_output.error_count > 0:
                error_penalty = min(0.2 * agent_output.error_count, 0.5)
                confidence_score *= (1 - error_penalty)
                
            # Calculate combined score
            combined_score = (recency_score * recency_weight) + (confidence_score * confidence_weight)
            
            # Update best agent if this score is higher
            if combined_score > best_score:
                best_score = combined_score
                best_agent = agent_output
                
        if best_agent is None:
            raise ValueError("No valid agent found")
            
        # Calculate final confidence
        final_confidence = best_agent.confidence
        
        # Boost confidence based on recency if configured
        if config.get("recency_confidence_boost", False):
            time_diff = (most_recent - best_agent.timestamp).total_seconds()
            if time_diff < 60:  # Within 1 minute
                final_confidence = min(1.0, final_confidence + 0.1)
                
        result = ArbitrationResult(
            winner_agent_id=best_agent.agent_id,
            winning_output=best_agent.output,
            confidence=final_confidence,
            strategy_used=self.strategy_name,
            metadata={
                "original_confidence": best_agent.confidence,
                "recency_weight": recency_weight,
                "confidence_weight": confidence_weight,
                "combined_score": best_score,
                "timestamp": best_agent.timestamp.isoformat(),
                "most_recent_timestamp": most_recent.isoformat(),
                "time_diff_seconds": (most_recent - best_agent.timestamp).total_seconds(),
                "total_agents": len(conflict.agent_outputs),
                "agent_scores": self._get_agent_scores(conflict.agent_outputs, recency_weight, confidence_weight)
            }
        )
        
        logger.info(f"[P22P4S3T1] Recency bias result: {best_agent.agent_id} wins with score {best_score:.3f}")
        return result
        
    def _get_agent_scores(
        self, 
        agent_outputs: List[AgentOutput], 
        recency_weight: float, 
        confidence_weight: float
    ) -> List[Dict[str, Any]]:
        """Get scores for all agents."""
        timestamps = [output.timestamp for output in agent_outputs]
        most_recent = max(timestamps)
        
        scores = []
        
        for agent_output in agent_outputs:
            # Calculate recency score
            time_diff = (most_recent - agent_output.timestamp).total_seconds()
            max_time_diff = max((most_recent - ts).total_seconds() for ts in timestamps)
            
            if max_time_diff > 0:
                recency_score = 1.0 - (time_diff / max_time_diff)
            else:
                recency_score = 1.0
                
            # Calculate confidence score
            confidence_score = agent_output.confidence
            if agent_output.error_count > 0:
                error_penalty = min(0.2 * agent_output.error_count, 0.5)
                confidence_score *= (1 - error_penalty)
                
            # Calculate combined score
            combined_score = (recency_score * recency_weight) + (confidence_score * confidence_weight)
            
            scores.append({
                "agent_id": agent_output.agent_id,
                "recency_score": recency_score,
                "confidence_score": confidence_score,
                "combined_score": combined_score,
                "timestamp": agent_output.timestamp.isoformat(),
                "time_diff_seconds": time_diff
            })
            
        # Sort by combined score (descending)
        scores.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Add rank
        for i, score in enumerate(scores):
            score["rank"] = i + 1
            
        return scores 