#!/usr/bin/env python3
"""
GitBridge Latency-Aware Arbitration Strategy
Phase: GBP22
Part: P22P3
Step: P22P3S2
Task: P22P3S2T1 - Latency-Aware Strategy Implementation

Latency-aware strategy for arbitration.
Considers response times, latency optimization, and real-time requirements.

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

class LatencyAwareStrategy(ArbitrationPluginBase):
    """
    Latency-aware arbitration strategy.
    
    Phase: GBP22
    Part: P22P3
    Step: P22P3S2
    Task: P22P3S2T1 - Core Implementation
    
    Features:
    - Considers response times and latency
    - Optimizes for real-time requirements
    - Balances speed vs quality
    - Supports latency thresholds and timeouts
    """
    
    @property
    def strategy_name(self) -> str:
        """Return the name of this arbitration strategy."""
        return "latency_aware"
        
    def arbitrate(
        self, 
        conflict: ArbitrationConflict, 
        config: Optional[Dict[str, Any]] = None
    ) -> ArbitrationResult:
        """
        Arbitrate using latency-aware strategy.
        
        Args:
            conflict: The conflict to resolve
            config: Optional configuration
            
        Returns:
            ArbitrationResult: The arbitration decision
        """
        logger.info(f"[P22P3S2T1] Using latency-aware strategy for conflict {conflict.conflict_id}")
        
        if not conflict.agent_outputs:
            raise ValueError("No agent outputs to arbitrate")
            
        config = config or {}
        max_latency_ms = config.get("max_latency_ms", 30000)  # 30 second default
        latency_weight = config.get("latency_weight", 0.5)  # 50% weight for latency
        quality_weight = 1.0 - latency_weight  # 50% weight for quality
        optimization_mode = config.get("optimization_mode", "balanced")  # "speed", "quality", "balanced"
        latency_penalty_factor = config.get("latency_penalty_factor", 0.1)
        
        # Filter agents by latency threshold
        valid_outputs = []
        for output in conflict.agent_outputs:
            execution_time = output.execution_time_ms or 0
            if execution_time <= max_latency_ms:
                valid_outputs.append(output)
            else:
                logger.warning(f"[P22P3S2T1] Agent {output.agent_id} exceeded latency threshold: {execution_time}ms")
                
        if not valid_outputs:
            logger.warning(f"[P22P3S2T1] No agents within latency threshold, using all agents")
            valid_outputs = conflict.agent_outputs
            
        # Find fastest and slowest execution times for normalization
        execution_times = [output.execution_time_ms or 0 for output in valid_outputs]
        min_time = min(execution_times) if execution_times else 0
        max_time = max(execution_times) if execution_times else 1
        
        # Calculate scores for each agent
        best_agent = None
        best_score = -1
        
        for agent_output in valid_outputs:
            execution_time = agent_output.execution_time_ms or 0
            
            # Calculate latency score (normalized, lower is better)
            if max_time > min_time:
                latency_score = 1.0 - ((execution_time - min_time) / (max_time - min_time))
            else:
                latency_score = 1.0  # All agents have same execution time
                
            # Calculate quality score (confidence adjusted for errors)
            quality_score = agent_output.confidence
            if agent_output.error_count > 0:
                error_penalty = min(0.2 * agent_output.error_count, 0.5)
                quality_score *= (1 - error_penalty)
                
            # Apply latency penalty for slow responses
            if execution_time > 10000:  # 10 second threshold
                latency_penalty = min(0.3, (execution_time - 10000) * latency_penalty_factor / 1000)
                quality_score *= (1 - latency_penalty)
                
            # Calculate combined score based on optimization mode
            if optimization_mode == "speed":
                # Prioritize speed
                combined_score = latency_score
            elif optimization_mode == "quality":
                # Prioritize quality
                combined_score = quality_score
            else:  # "balanced"
                # Balance latency and quality
                combined_score = (latency_score * latency_weight) + (quality_score * quality_weight)
                
            # Update best agent if this score is higher
            if combined_score > best_score:
                best_score = combined_score
                best_agent = agent_output
                
        if best_agent is None:
            raise ValueError("No valid agent found")
            
        # Calculate final confidence
        final_confidence = best_agent.confidence
        
        # Boost confidence for fast responses
        execution_time = best_agent.execution_time_ms or 0
        if execution_time < 5000:  # Under 5 seconds
            final_confidence = min(1.0, final_confidence + 0.05)
        elif execution_time < 10000:  # Under 10 seconds
            final_confidence = min(1.0, final_confidence + 0.02)
            
        result = ArbitrationResult(
            winner_agent_id=best_agent.agent_id,
            winning_output=best_agent.output,
            confidence=final_confidence,
            strategy_used=self.strategy_name,
            metadata={
                "original_confidence": best_agent.confidence,
                "execution_time_ms": best_agent.execution_time_ms,
                "latency_score": 1.0 - ((execution_time - min_time) / (max_time - min_time)) if max_time > min_time else 1.0,
                "optimization_mode": optimization_mode,
                "max_latency_ms": max_latency_ms,
                "total_agents": len(conflict.agent_outputs),
                "agents_within_latency": len(valid_outputs),
                "fastest_time_ms": min_time,
                "slowest_time_ms": max_time,
                "agent_scores": self._get_agent_scores(valid_outputs, config)
            }
        )
        
        logger.info(f"[P22P3S2T1] Latency-aware result: {best_agent.agent_id} wins with score {best_score:.3f}")
        return result
        
    def _get_agent_scores(
        self, 
        agent_outputs: List[AgentOutput], 
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get detailed scores for all agents."""
        latency_weight = config.get("latency_weight", 0.5)
        quality_weight = 1.0 - latency_weight
        optimization_mode = config.get("optimization_mode", "balanced")
        latency_penalty_factor = config.get("latency_penalty_factor", 0.1)
        
        # Calculate time range for normalization
        execution_times = [output.execution_time_ms or 0 for output in agent_outputs]
        min_time = min(execution_times) if execution_times else 0
        max_time = max(execution_times) if execution_times else 1
        
        scores = []
        
        for agent_output in agent_outputs:
            execution_time = agent_output.execution_time_ms or 0
            
            # Calculate latency score
            if max_time > min_time:
                latency_score = 1.0 - ((execution_time - min_time) / (max_time - min_time))
            else:
                latency_score = 1.0
                
            # Calculate quality score
            quality_score = agent_output.confidence
            if agent_output.error_count > 0:
                error_penalty = min(0.2 * agent_output.error_count, 0.5)
                quality_score *= (1 - error_penalty)
                
            # Apply latency penalty
            if execution_time > 10000:
                latency_penalty = min(0.3, (execution_time - 10000) * latency_penalty_factor / 1000)
                quality_score *= (1 - latency_penalty)
                
            # Calculate combined score
            if optimization_mode == "speed":
                combined_score = latency_score
            elif optimization_mode == "quality":
                combined_score = quality_score
            else:  # "balanced"
                combined_score = (latency_score * latency_weight) + (quality_score * quality_weight)
                
            scores.append({
                "agent_id": agent_output.agent_id,
                "latency_score": latency_score,
                "quality_score": quality_score,
                "execution_time_ms": execution_time,
                "combined_score": combined_score,
                "optimization_mode": optimization_mode,
                "error_count": agent_output.error_count
            })
            
        # Sort by combined score (descending)
        scores.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Add rank
        for i, score in enumerate(scores):
            score["rank"] = i + 1
            
        return scores 