#!/usr/bin/env python3
"""
GitBridge Hybrid Score Arbitration Strategy
Phase: GBP22
Part: P22P3
Step: P22P3S3
Task: P22P3S3T1 - Hybrid Score Strategy Implementation

Hybrid score strategy for arbitration.
Combines multiple heuristics: confidence, cost, latency, recency, and quality.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P22P3 Schema]
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

class HybridScoreStrategy(ArbitrationPluginBase):
    """
    Hybrid score arbitration strategy.
    
    Phase: GBP22
    Part: P22P3
    Step: P22P3S3
    Task: P22P3S3T1 - Core Implementation
    
    Features:
    - Combines multiple heuristics for comprehensive scoring
    - Configurable weights for different factors
    - Adaptive scoring based on context
    - Multi-dimensional decision making
    """
    
    @property
    def strategy_name(self) -> str:
        """Return the name of this arbitration strategy."""
        return "hybrid_score"
        
    def arbitrate(
        self, 
        conflict: ArbitrationConflict, 
        config: Optional[Dict[str, Any]] = None
    ) -> ArbitrationResult:
        """
        Arbitrate using hybrid score strategy.
        
        Args:
            conflict: The conflict to resolve
            config: Optional configuration
            
        Returns:
            ArbitrationResult: The arbitration decision
        """
        logger.info(f"[P22P3S3T1] Using hybrid score strategy for conflict {conflict.conflict_id}")
        
        if not conflict.agent_outputs:
            raise ValueError("No agent outputs to arbitrate")
            
        config = config or {}
        
        # Get scoring weights (default to balanced weights)
        weights = config.get("weights", {
            "confidence": 0.25,
            "cost": 0.20,
            "latency": 0.20,
            "recency": 0.15,
            "quality": 0.20
        })
        
        # Get agent costs
        agent_costs = config.get("agent_costs", {
            "openai_gpt4o": 0.03,
            "grok_3": 0.01,
            "cursor_assistant": 0.005,
            "claude_3_5_sonnet": 0.015,
            "gemini_pro": 0.008,
        })
        
        # Get scoring parameters
        max_latency_ms = config.get("max_latency_ms", 30000)
        recency_weight_decay = config.get("recency_weight_decay", 0.1)  # per minute
        quality_threshold = config.get("quality_threshold", 0.7)
        
        # Calculate scores for each agent
        best_agent = None
        best_score = -1
        agent_scores = []
        
        # Find ranges for normalization
        confidences = [output.confidence for output in conflict.agent_outputs]
        execution_times = [output.execution_time_ms or 0 for output in conflict.agent_outputs]
        timestamps = [output.timestamp for output in conflict.agent_outputs]
        
        max_confidence = max(confidences) if confidences else 1.0
        min_time = min(execution_times) if execution_times else 0
        max_time = max(execution_times) if execution_times else 1
        most_recent = max(timestamps) if timestamps else datetime.now(timezone.utc)
        
        for agent_output in conflict.agent_outputs:
            agent_id = agent_output.agent_id
            
            # 1. Confidence Score (0-1)
            confidence_score = agent_output.confidence / max_confidence if max_confidence > 0 else 0
            
            # 2. Cost Score (0-1, lower cost is better)
            agent_cost = agent_costs.get(agent_id, 0.0)
            max_cost = max(agent_costs.values()) if agent_costs else 1.0
            cost_score = 1.0 - (agent_cost / max_cost) if max_cost > 0 else 1.0
            
            # 3. Latency Score (0-1, lower latency is better)
            execution_time = agent_output.execution_time_ms or 0
            if max_time > min_time:
                latency_score = 1.0 - ((execution_time - min_time) / (max_time - min_time))
            else:
                latency_score = 1.0
                
            # Apply latency penalty for slow responses
            if execution_time > max_latency_ms:
                latency_score *= 0.5  # 50% penalty for exceeding threshold
                
            # 4. Recency Score (0-1, more recent is better)
            time_diff = (most_recent - agent_output.timestamp).total_seconds()
            recency_score = max(0.0, 1.0 - (time_diff * recency_weight_decay / 60))
            
            # 5. Quality Score (0-1, based on errors and execution quality)
            quality_score = 1.0
            
            # Penalize for errors
            if agent_output.error_count > 0:
                error_penalty = min(0.3, agent_output.error_count * 0.1)
                quality_score *= (1 - error_penalty)
                
            # Boost for high confidence
            if agent_output.confidence > quality_threshold:
                quality_score *= 1.1
                
            # Penalize for very slow responses
            if execution_time > 20000:  # 20 seconds
                quality_score *= 0.8
                
            # Calculate weighted combined score
            combined_score = (
                confidence_score * weights["confidence"] +
                cost_score * weights["cost"] +
                latency_score * weights["latency"] +
                recency_score * weights["recency"] +
                quality_score * weights["quality"]
            )
            
            # Store detailed scores
            agent_scores.append({
                "agent_id": agent_id,
                "confidence_score": confidence_score,
                "cost_score": cost_score,
                "latency_score": latency_score,
                "recency_score": recency_score,
                "quality_score": quality_score,
                "combined_score": combined_score,
                "weights": weights.copy(),
                "details": {
                    "confidence": agent_output.confidence,
                    "cost": agent_cost,
                    "execution_time_ms": execution_time,
                    "time_diff_seconds": time_diff,
                    "error_count": agent_output.error_count
                }
            })
            
            # Update best agent if this score is higher
            if combined_score > best_score:
                best_score = combined_score
                best_agent = agent_output
                
        if best_agent is None:
            raise ValueError("No valid agent found")
            
        # Calculate final confidence with hybrid boost
        final_confidence = best_agent.confidence
        
        # Boost confidence based on overall score quality
        if best_score > 0.8:
            final_confidence = min(1.0, final_confidence + 0.1)
        elif best_score > 0.6:
            final_confidence = min(1.0, final_confidence + 0.05)
            
        # Sort agent scores by combined score
        agent_scores.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Add ranks
        for i, score in enumerate(agent_scores):
            score["rank"] = i + 1
            
        result = ArbitrationResult(
            winner_agent_id=best_agent.agent_id,
            winning_output=best_agent.output,
            confidence=final_confidence,
            strategy_used=self.strategy_name,
            metadata={
                "original_confidence": best_agent.confidence,
                "hybrid_score": best_score,
                "weights_used": weights,
                "total_agents": len(conflict.agent_outputs),
                "agent_scores": agent_scores,
                "scoring_parameters": {
                    "max_latency_ms": max_latency_ms,
                    "recency_weight_decay": recency_weight_decay,
                    "quality_threshold": quality_threshold
                }
            }
        )
        
        logger.info(f"[P22P3S3T1] Hybrid score result: {best_agent.agent_id} wins with score {best_score:.3f}")
        return result
        
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration for hybrid strategy."""
        if not isinstance(config, dict):
            return False
            
        # Validate weights
        weights = config.get("weights", {})
        if weights:
            weight_sum = sum(weights.values())
            if abs(weight_sum - 1.0) > 0.01:  # Allow small floating point errors
                logger.warning(f"[P22P3S3T1] Weights sum to {weight_sum}, should be 1.0")
                
        # Validate numeric parameters
        numeric_params = ["max_latency_ms", "recency_weight_decay", "quality_threshold"]
        for param in numeric_params:
            if param in config and not isinstance(config[param], (int, float)):
                return False
                
        return True 