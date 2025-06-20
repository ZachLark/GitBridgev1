#!/usr/bin/env python3
"""
GitBridge Cost-Aware Arbitration Strategy
Phase: GBP22
Part: P22P3
Step: P22P3S1
Task: P22P3S1T1 - Cost-Aware Strategy Implementation

Cost-aware strategy for arbitration.
Considers agent costs, cost-effectiveness, and budget constraints.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P22P3 Schema]
"""

import logging
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path to import arbitration_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from arbitration_engine import ArbitrationPluginBase, ArbitrationConflict, ArbitrationResult, AgentOutput

logger = logging.getLogger(__name__)

class CostAwareStrategy(ArbitrationPluginBase):
    """
    Cost-aware arbitration strategy.
    
    Phase: GBP22
    Part: P22P3
    Step: P22P3S1
    Task: P22P3S1T1 - Core Implementation
    
    Features:
    - Considers agent costs and cost-effectiveness
    - Balances quality vs cost
    - Respects budget constraints
    - Supports cost optimization modes
    """
    
    @property
    def strategy_name(self) -> str:
        """Return the name of this arbitration strategy."""
        return "cost_aware"
        
    def arbitrate(
        self, 
        conflict: ArbitrationConflict, 
        config: Optional[Dict[str, Any]] = None
    ) -> ArbitrationResult:
        """
        Arbitrate using cost-aware strategy.
        
        Args:
            conflict: The conflict to resolve
            config: Optional configuration
            
        Returns:
            ArbitrationResult: The arbitration decision
        """
        logger.info(f"[P22P3S1T1] Using cost-aware strategy for conflict {conflict.conflict_id}")
        
        if not conflict.agent_outputs:
            raise ValueError("No agent outputs to arbitrate")
            
        config = config or {}
        budget_limit = config.get("budget_limit", float('inf'))
        cost_weight = config.get("cost_weight", 0.4)  # 40% weight for cost
        quality_weight = 1.0 - cost_weight  # 60% weight for quality
        optimization_mode = config.get("optimization_mode", "balanced")  # "cost", "quality", "balanced"
        
        # Get agent cost data
        agent_costs = self._get_agent_costs(config)
        
        # Calculate scores for each agent
        best_agent = None
        best_score = -1
        
        for agent_output in conflict.agent_outputs:
            agent_id = agent_output.agent_id
            
            # Get agent cost
            agent_cost = agent_costs.get(agent_id, 0.0)
            
            # Check budget constraint
            if agent_cost > budget_limit:
                logger.warning(f"[P22P3S1T1] Agent {agent_id} exceeds budget limit {budget_limit}")
                continue
                
            # Calculate quality score (confidence adjusted for errors)
            quality_score = agent_output.confidence
            if agent_output.error_count > 0:
                error_penalty = min(0.2 * agent_output.error_count, 0.5)
                quality_score *= (1 - error_penalty)
                
            # Calculate cost-effectiveness score
            if agent_cost > 0:
                cost_effectiveness = quality_score / agent_cost
            else:
                cost_effectiveness = quality_score  # Free agents get full quality score
                
            # Calculate combined score based on optimization mode
            if optimization_mode == "cost":
                # Prioritize cost-effectiveness
                combined_score = cost_effectiveness
            elif optimization_mode == "quality":
                # Prioritize quality
                combined_score = quality_score
            else:  # "balanced"
                # Balance quality and cost
                cost_score = 1.0 / (1.0 + agent_cost)  # Normalize cost (lower is better)
                combined_score = (quality_score * quality_weight) + (cost_score * cost_weight)
                
            # Update best agent if this score is higher
            if combined_score > best_score:
                best_score = combined_score
                best_agent = agent_output
                
        if best_agent is None:
            raise ValueError("No valid agent found within budget constraints")
            
        # Calculate final confidence
        final_confidence = best_agent.confidence
        
        # Adjust confidence based on cost-effectiveness
        agent_cost = agent_costs.get(best_agent.agent_id, 0.0)
        if agent_cost > 0:
            cost_effectiveness = final_confidence / agent_cost
            # Boost confidence for highly cost-effective agents
            if cost_effectiveness > 2.0:  # High cost-effectiveness threshold
                final_confidence = min(1.0, final_confidence + 0.1)
                
        result = ArbitrationResult(
            winner_agent_id=best_agent.agent_id,
            winning_output=best_agent.output,
            confidence=final_confidence,
            strategy_used=self.strategy_name,
            metadata={
                "original_confidence": best_agent.confidence,
                "agent_cost": agent_costs.get(best_agent.agent_id, 0.0),
                "cost_effectiveness": final_confidence / agent_costs.get(best_agent.agent_id, 1.0),
                "optimization_mode": optimization_mode,
                "budget_limit": budget_limit,
                "total_agents": len(conflict.agent_outputs),
                "agents_within_budget": len([a for a in conflict.agent_outputs 
                                           if agent_costs.get(a.agent_id, 0.0) <= budget_limit]),
                "agent_scores": self._get_agent_scores(conflict.agent_outputs, agent_costs, config)
            }
        )
        
        logger.info(f"[P22P3S1T1] Cost-aware result: {best_agent.agent_id} wins with score {best_score:.3f}")
        return result
        
    def _get_agent_costs(self, config: Dict[str, Any]) -> Dict[str, float]:
        """Get agent costs from configuration or defaults."""
        # Use provided costs or defaults
        agent_costs = config.get("agent_costs", {})
        
        # Default costs if not provided
        if not agent_costs:
            agent_costs = {
                "openai_gpt4o": 0.03,      # $0.03 per 1K tokens
                "grok_3": 0.01,            # $0.01 per 1K tokens
                "cursor_assistant": 0.005,  # $0.005 per 1K tokens
                "claude_3_5_sonnet": 0.015, # $0.015 per 1K tokens
                "gemini_pro": 0.008,       # $0.008 per 1K tokens
            }
            
        return agent_costs
        
    def _get_agent_scores(
        self, 
        agent_outputs: List[AgentOutput], 
        agent_costs: Dict[str, float],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get detailed scores for all agents."""
        budget_limit = config.get("budget_limit", float('inf'))
        cost_weight = config.get("cost_weight", 0.4)
        quality_weight = 1.0 - cost_weight
        optimization_mode = config.get("optimization_mode", "balanced")
        
        scores = []
        
        for agent_output in agent_outputs:
            agent_id = agent_output.agent_id
            agent_cost = agent_costs.get(agent_id, 0.0)
            
            # Calculate quality score
            quality_score = agent_output.confidence
            if agent_output.error_count > 0:
                error_penalty = min(0.2 * agent_output.error_count, 0.5)
                quality_score *= (1 - error_penalty)
                
            # Calculate cost-effectiveness
            if agent_cost > 0:
                cost_effectiveness = quality_score / agent_cost
            else:
                cost_effectiveness = quality_score
                
            # Calculate combined score
            if optimization_mode == "cost":
                combined_score = cost_effectiveness
            elif optimization_mode == "quality":
                combined_score = quality_score
            else:  # "balanced"
                cost_score = 1.0 / (1.0 + agent_cost)
                combined_score = (quality_score * quality_weight) + (cost_score * cost_weight)
                
            scores.append({
                "agent_id": agent_id,
                "quality_score": quality_score,
                "agent_cost": agent_cost,
                "cost_effectiveness": cost_effectiveness,
                "combined_score": combined_score,
                "within_budget": agent_cost <= budget_limit,
                "optimization_mode": optimization_mode
            })
            
        # Sort by combined score (descending)
        scores.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Add rank
        for i, score in enumerate(scores):
            score["rank"] = i + 1
            
        return scores 