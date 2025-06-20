#!/usr/bin/env python3
"""
GitBridge Majority Vote Arbitration Strategy
Phase: GBP22
Part: P22P4
Step: P22P4S1
Task: P22P4S1T1 - Majority Vote Strategy Implementation

Majority vote strategy for arbitration.
Selects the most common output among agents.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P22P4 Schema]
"""

import logging
from typing import Dict, List, Any, Optional
from collections import Counter
import sys
import os

# Add parent directory to path to import arbitration_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from arbitration_engine import ArbitrationPluginBase, ArbitrationConflict, ArbitrationResult, AgentOutput

logger = logging.getLogger(__name__)

class MajorityVoteStrategy(ArbitrationPluginBase):
    """
    Majority vote arbitration strategy.
    
    Phase: GBP22
    Part: P22P4
    Step: P22P4S1
    Task: P22P4S1T1 - Core Implementation
    
    Features:
    - Counts occurrences of each output
    - Selects the most common output
    - Handles ties by confidence
    """
    
    @property
    def strategy_name(self) -> str:
        """Return the name of this arbitration strategy."""
        return "majority_vote"
        
    def arbitrate(
        self, 
        conflict: ArbitrationConflict, 
        config: Optional[Dict[str, Any]] = None
    ) -> ArbitrationResult:
        """
        Arbitrate using majority vote strategy.
        
        Args:
            conflict: The conflict to resolve
            config: Optional configuration
            
        Returns:
            ArbitrationResult: The arbitration decision
        """
        logger.info(f"[P22P4S1T1] Using majority vote strategy for conflict {conflict.conflict_id}")
        
        # Count outputs
        output_counts = Counter()
        output_agents = {}
        
        for agent_output in conflict.agent_outputs:
            output_str = str(agent_output.output)
            output_counts[output_str] += 1
            
            if output_str not in output_agents:
                output_agents[output_str] = []
            output_agents[output_str].append(agent_output)
            
        # Find the most common output
        if not output_counts:
            raise ValueError("No outputs to arbitrate")
            
        most_common_output = output_counts.most_common(1)[0][0]
        max_count = output_counts[most_common_output]
        
        # Check for ties
        tied_outputs = [output for output, count in output_counts.items() if count == max_count]
        
        if len(tied_outputs) > 1:
            # Resolve tie by confidence
            logger.info(f"[P22P4S1T1] Tie detected, resolving by confidence")
            best_output = None
            best_confidence = -1
            
            for output_str in tied_outputs:
                for agent_output in output_agents[output_str]:
                    if agent_output.confidence > best_confidence:
                        best_confidence = agent_output.confidence
                        best_output = agent_output
                        
            winner_agent = best_output.agent_id
            winning_output = best_output.output
            confidence = best_output.confidence
            
        else:
            # No tie, select agent with highest confidence among those with the winning output
            best_agent = None
            best_confidence = -1
            
            for agent_output in output_agents[most_common_output]:
                if agent_output.confidence > best_confidence:
                    best_confidence = agent_output.confidence
                    best_agent = agent_output
                    
            winner_agent = best_agent.agent_id
            winning_output = best_agent.output
            confidence = best_agent.confidence
            
        # Calculate overall confidence based on majority percentage
        total_agents = len(conflict.agent_outputs)
        majority_percentage = max_count / total_agents
        overall_confidence = (confidence + majority_percentage) / 2
        
        result = ArbitrationResult(
            winner_agent_id=winner_agent,
            winning_output=winning_output,
            confidence=overall_confidence,
            strategy_used=self.strategy_name,
            metadata={
                "majority_count": max_count,
                "total_agents": total_agents,
                "majority_percentage": majority_percentage,
                "tie_resolved": len(tied_outputs) > 1
            }
        )
        
        logger.info(f"[P22P4S1T1] Majority vote result: {winner_agent} wins with {max_count}/{total_agents} votes")
        return result 