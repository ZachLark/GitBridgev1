#!/usr/bin/env python3
"""
GitBridge Meta-Evaluator System
Phase: GBP20
Part: P20P8
Step: P20P8S1
Task: P20P8S1T1 - Meta-Evaluator System Setup

Intelligent evaluation system for comparing AI agent responses across multiple criteria:
- Latency performance
- Cost efficiency
- Response relevance
- Reliability metrics
- Side-by-side comparison

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [Corrected P20P8 Schema]
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import statistics
import re

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_router.smart_router import SmartRouter, ProviderType, SmartRouterResponse
from clients.openai_client import OpenAIClient
from clients.grok_client import GrokClient

# Configure logging with P20P8 schema
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [P20P8S1] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/meta_evaluator.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class EvaluationCriteria(Enum):
    """Evaluation criteria for AI agent responses."""
    LATENCY = "latency"
    COST = "cost"
    RELEVANCE = "relevance"
    RELIABILITY = "reliability"
    COMPREHENSIVENESS = "comprehensiveness"
    ACCURACY = "accuracy"

@dataclass
class ResponseEvaluation:
    """Evaluation results for a single response."""
    provider: str
    response_time: float
    token_count: int
    cost: float
    content: str
    relevance_score: float
    comprehensiveness_score: float
    accuracy_score: float
    reliability_score: float
    overall_score: float
    evaluation_notes: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class ComparisonResult:
    """Results of comparing two AI agent responses."""
    prompt: str
    task_type: str
    openai_evaluation: ResponseEvaluation
    grok_evaluation: ResponseEvaluation
    winner: str
    confidence: float
    comparison_notes: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class MetaEvaluator:
    """
    Meta-evaluator system for intelligent AI agent comparison.
    
    Phase: GBP20
    Part: P20P8
    Step: P20P8S1
    Task: P20P8S1T1 - Core Implementation
    
    Features:
    - Multi-criteria evaluation (latency, cost, relevance, reliability)
    - Side-by-side comparison with scoring logic
    - Response quality assessment
    - Cost-benefit analysis
    - Performance trend tracking
    """
    
    def __init__(self, evaluation_weights: Optional[Dict[str, float]] = None):
        """
        Initialize the meta-evaluator system.
        
        Args:
            evaluation_weights: Custom weights for evaluation criteria
        """
        # Default evaluation weights
        self.evaluation_weights = evaluation_weights or {
            'latency': 0.2,
            'cost': 0.15,
            'relevance': 0.25,
            'reliability': 0.2,
            'comprehensiveness': 0.1,
            'accuracy': 0.1
        }
        
        # Initialize clients for direct evaluation
        self.openai_client = OpenAIClient()
        self.grok_client = GrokClient()
        
        # Ensure evaluation directory exists
        os.makedirs('evaluation', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        logger.info(f"[P20P8S1T1] MetaEvaluator initialized with weights: {self.evaluation_weights}")
        
    def evaluate_response(
        self,
        provider: str,
        response: SmartRouterResponse,
        prompt: str,
        task_type: str = "general"
    ) -> ResponseEvaluation:
        """
        Evaluate a single AI response across multiple criteria.
        
        Args:
            provider: Provider name (openai/grok)
            response: SmartRouter response object
            prompt: Original prompt
            task_type: Type of task performed
            
        Returns:
            ResponseEvaluation: Comprehensive evaluation results
        """
        logger.info(f"[P20P8S1T1] Evaluating {provider} response for {task_type} task")
        
        # Calculate cost
        cost = self._calculate_cost(provider, response.usage)
        
        # Evaluate content quality
        relevance_score = self._evaluate_relevance(response.content, prompt, task_type)
        comprehensiveness_score = self._evaluate_comprehensiveness(response.content, task_type)
        accuracy_score = self._evaluate_accuracy(response.content, task_type)
        reliability_score = self._evaluate_reliability(response, provider)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            response.response_time,
            cost,
            relevance_score,
            reliability_score,
            comprehensiveness_score,
            accuracy_score
        )
        
        # Generate evaluation notes
        evaluation_notes = self._generate_evaluation_notes(
            response, relevance_score, comprehensiveness_score, accuracy_score, reliability_score
        )
        
        evaluation = ResponseEvaluation(
            provider=provider,
            response_time=response.response_time,
            token_count=response.usage.get('total_tokens', 0),
            cost=cost,
            content=response.content,
            relevance_score=relevance_score,
            comprehensiveness_score=comprehensiveness_score,
            accuracy_score=accuracy_score,
            reliability_score=reliability_score,
            overall_score=overall_score,
            evaluation_notes=evaluation_notes
        )
        
        logger.info(f"[P20P8S1T1] {provider} evaluation complete - Score: {overall_score:.3f}")
        return evaluation
        
    def compare_responses(
        self,
        prompt: str,
        task_type: str = "general",
        max_tokens: Optional[int] = None
    ) -> ComparisonResult:
        """
        Compare responses from both OpenAI and Grok for the same prompt.
        
        Args:
            prompt: Input prompt
            task_type: Type of task
            max_tokens: Maximum tokens for responses
            
        Returns:
            ComparisonResult: Side-by-side comparison results
        """
        logger.info(f"[P20P8S1T1] Starting side-by-side comparison for {task_type} task")
        
        # Get responses from both providers
        openai_response = self._get_direct_response('openai', prompt, task_type, max_tokens)
        grok_response = self._get_direct_response('grok', prompt, task_type, max_tokens)
        
        # Evaluate both responses
        openai_evaluation = self.evaluate_response('openai', openai_response, prompt, task_type)
        grok_evaluation = self.evaluate_response('grok', grok_response, prompt, task_type)
        
        # Determine winner
        winner, confidence = self._determine_winner(openai_evaluation, grok_evaluation)
        
        # Generate comparison notes
        comparison_notes = self._generate_comparison_notes(
            openai_evaluation, grok_evaluation, winner, confidence
        )
        
        comparison = ComparisonResult(
            prompt=prompt,
            task_type=task_type,
            openai_evaluation=openai_evaluation,
            grok_evaluation=grok_evaluation,
            winner=winner,
            confidence=confidence,
            comparison_notes=comparison_notes
        )
        
        # Store comparison result
        self._store_comparison_result(comparison)
        
        logger.info(f"[P20P8S1T1] Comparison complete - Winner: {winner} (confidence: {confidence:.2f})")
        return comparison
        
    def _get_direct_response(
        self,
        provider: str,
        prompt: str,
        task_type: str,
        max_tokens: Optional[int]
    ) -> SmartRouterResponse:
        """Get direct response from specified provider."""
        try:
            if provider == 'openai':
                response = self.openai_client.generate_response(
                    prompt=prompt,
                    max_tokens=max_tokens
                )
                # Convert to SmartRouterResponse format
                smart_response = SmartRouterResponse(
                    content=response.content,
                    provider=ProviderType.OPENAI,
                    response_time=response.response_time,
                    usage=response.usage,
                    routing_decision=None,  # Not needed for evaluation
                    metadata={'task_type': task_type}
                )
            else:
                response = self.grok_client.generate_response(
                    prompt=prompt,
                    max_tokens=max_tokens
                )
                # Convert to SmartRouterResponse format
                smart_response = SmartRouterResponse(
                    content=response.content,
                    provider=ProviderType.GROK,
                    response_time=response.response_time,
                    usage=response.usage,
                    routing_decision=None,  # Not needed for evaluation
                    metadata={'task_type': task_type}
                )
                
            return smart_response
            
        except Exception as e:
            logger.error(f"[P20P8S1T1] Failed to get {provider} response: {e}")
            raise
            
    def _calculate_cost(self, provider: str, usage: Dict[str, Any]) -> float:
        """Calculate cost for the response."""
        total_tokens = usage.get('total_tokens', 0)
        
        if provider == 'openai':
            # GPT-4o pricing
            return (total_tokens / 1000) * 0.01
        else:
            # Grok-3 pricing
            return (total_tokens / 1000) * 0.005
            
    def _evaluate_relevance(self, content: str, prompt: str, task_type: str) -> float:
        """
        Evaluate how relevant the response is to the prompt.
        
        Returns:
            float: Relevance score (0.0-1.0)
        """
        # Simple keyword matching for now
        # In a production system, this could use embeddings or semantic similarity
        
        prompt_lower = prompt.lower()
        content_lower = content.lower()
        
        # Extract key terms from prompt
        prompt_words = set(re.findall(r'\b\w+\b', prompt_lower))
        content_words = set(re.findall(r'\b\w+\b', content_lower))
        
        # Calculate overlap
        if not prompt_words:
            return 0.5  # Neutral score if no words to match
            
        overlap = len(prompt_words.intersection(content_words))
        relevance_score = min(1.0, overlap / len(prompt_words))
        
        # Task-specific adjustments
        if task_type == "code_review":
            # Code review should mention code elements
            code_indicators = ['function', 'class', 'method', 'variable', 'loop', 'condition']
            code_mentions = sum(1 for indicator in code_indicators if indicator in content_lower)
            relevance_score = min(1.0, relevance_score + (code_mentions * 0.1))
            
        elif task_type == "analysis":
            # Analysis should be comprehensive
            analysis_indicators = ['because', 'therefore', 'however', 'furthermore', 'conclusion']
            analysis_mentions = sum(1 for indicator in analysis_indicators if indicator in content_lower)
            relevance_score = min(1.0, relevance_score + (analysis_mentions * 0.05))
            
        return max(0.0, min(1.0, relevance_score))
        
    def _evaluate_comprehensiveness(self, content: str, task_type: str) -> float:
        """
        Evaluate how comprehensive the response is.
        
        Returns:
            float: Comprehensiveness score (0.0-1.0)
        """
        # Base score on content length and structure
        word_count = len(content.split())
        
        # Minimum expected lengths for different task types
        min_lengths = {
            'general': 20,
            'code_review': 50,
            'analysis': 100,
            'explanation': 80
        }
        
        min_length = min_lengths.get(task_type, 30)
        
        if word_count < min_length:
            comprehensiveness = word_count / min_length
        else:
            comprehensiveness = min(1.0, word_count / (min_length * 2))
            
        # Bonus for structured responses
        if any(marker in content for marker in ['1.', '2.', '3.', '- ', '* ', '•']):
            comprehensiveness = min(1.0, comprehensiveness + 0.1)
            
        return max(0.0, min(1.0, comprehensiveness))
        
    def _evaluate_accuracy(self, content: str, task_type: str) -> float:
        """
        Evaluate the accuracy of the response.
        
        Returns:
            float: Accuracy score (0.0-1.0)
        """
        # This is a simplified accuracy evaluation
        # In production, this could use fact-checking APIs or domain-specific validation
        
        # Check for common accuracy indicators
        accuracy_indicators = [
            'according to', 'research shows', 'studies indicate',
            'best practice', 'recommended', 'standard'
        ]
        
        accuracy_penalties = [
            'i think', 'maybe', 'possibly', 'uncertain', 'not sure'
        ]
        
        content_lower = content.lower()
        
        # Count positive indicators
        positive_count = sum(1 for indicator in accuracy_indicators if indicator in content_lower)
        
        # Count negative indicators
        negative_count = sum(1 for penalty in accuracy_penalties if penalty in content_lower)
        
        # Calculate base accuracy
        base_accuracy = 0.7  # Assume reasonable accuracy
        
        # Adjust based on indicators
        accuracy = base_accuracy + (positive_count * 0.05) - (negative_count * 0.1)
        
        return max(0.0, min(1.0, accuracy))
        
    def _evaluate_reliability(self, response: SmartRouterResponse, provider: str) -> float:
        """
        Evaluate the reliability of the response.
        
        Returns:
            float: Reliability score (0.0-1.0)
        """
        # Base reliability on response characteristics
        reliability = 0.8  # Base reliability
        
        # Check for error indicators in content
        error_indicators = ['error', 'failed', 'unable', 'cannot', 'sorry']
        content_lower = response.content.lower()
        
        if any(indicator in content_lower for indicator in error_indicators):
            reliability -= 0.3
            
        # Check response time (very fast responses might be cached/less reliable)
        if response.response_time < 0.5:
            reliability -= 0.1
        elif response.response_time > 10.0:
            reliability -= 0.2
            
        # Provider-specific reliability adjustments
        if provider == 'openai':
            # OpenAI generally has high reliability
            reliability += 0.1
        elif provider == 'grok':
            # Grok is newer but generally reliable
            reliability += 0.05
            
        return max(0.0, min(1.0, reliability))
        
    def _calculate_overall_score(
        self,
        response_time: float,
        cost: float,
        relevance: float,
        reliability: float,
        comprehensiveness: float,
        accuracy: float
    ) -> float:
        """Calculate overall evaluation score."""
        # Normalize response time (lower is better)
        latency_score = max(0.0, 1.0 - (response_time / 10.0))  # 10s = 0 score
        
        # Normalize cost (lower is better)
        cost_score = max(0.0, 1.0 - (cost / 0.01))  # $0.01 = 0 score
        
        # Calculate weighted score
        overall_score = (
            self.evaluation_weights['latency'] * latency_score +
            self.evaluation_weights['cost'] * cost_score +
            self.evaluation_weights['relevance'] * relevance +
            self.evaluation_weights['reliability'] * reliability +
            self.evaluation_weights['comprehensiveness'] * comprehensiveness +
            self.evaluation_weights['accuracy'] * accuracy
        )
        
        return max(0.0, min(1.0, overall_score))
        
    def _determine_winner(
        self,
        openai_eval: ResponseEvaluation,
        grok_eval: ResponseEvaluation
    ) -> Tuple[str, float]:
        """Determine the winner and confidence level."""
        openai_score = openai_eval.overall_score
        grok_score = grok_eval.overall_score
        
        if openai_score > grok_score:
            winner = 'openai'
            confidence = (openai_score - grok_score) / max(openai_score, 0.1)
        elif grok_score > openai_score:
            winner = 'grok'
            confidence = (grok_score - openai_score) / max(grok_score, 0.1)
        else:
            winner = 'tie'
            confidence = 0.0
            
        return winner, min(1.0, confidence)
        
    def _generate_evaluation_notes(
        self,
        response: SmartRouterResponse,
        relevance: float,
        comprehensiveness: float,
        accuracy: float,
        reliability: float
    ) -> str:
        """Generate evaluation notes for the response."""
        notes = []
        
        if relevance < 0.5:
            notes.append("Low relevance to prompt")
        elif relevance > 0.8:
            notes.append("High relevance to prompt")
            
        if comprehensiveness < 0.5:
            notes.append("Response lacks comprehensiveness")
        elif comprehensiveness > 0.8:
            notes.append("Comprehensive response")
            
        if accuracy < 0.6:
            notes.append("Accuracy concerns detected")
        elif accuracy > 0.8:
            notes.append("High accuracy indicators")
            
        if reliability < 0.7:
            notes.append("Reliability concerns")
        elif reliability > 0.9:
            notes.append("High reliability")
            
        if response.response_time > 5.0:
            notes.append("Slow response time")
        elif response.response_time < 1.0:
            notes.append("Fast response time")
            
        return "; ".join(notes) if notes else "Good overall performance"
        
    def _generate_comparison_notes(
        self,
        openai_eval: ResponseEvaluation,
        grok_eval: ResponseEvaluation,
        winner: str,
        confidence: float
    ) -> str:
        """Generate comparison notes."""
        notes = []
        
        # Performance differences
        time_diff = abs(openai_eval.response_time - grok_eval.response_time)
        if time_diff > 2.0:
            faster = 'openai' if openai_eval.response_time < grok_eval.response_time else 'grok'
            notes.append(f"{faster} was {time_diff:.1f}s faster")
            
        cost_diff = abs(openai_eval.cost - grok_eval.cost)
        if cost_diff > 0.001:
            cheaper = 'openai' if openai_eval.cost < grok_eval.cost else 'grok'
            notes.append(f"{cheaper} was ${cost_diff:.4f} cheaper")
            
        # Quality differences
        quality_diff = abs(openai_eval.overall_score - grok_eval.overall_score)
        if quality_diff > 0.1:
            better = 'openai' if openai_eval.overall_score > grok_eval.overall_score else 'grok'
            notes.append(f"{better} had higher quality score")
            
        # Winner analysis
        if winner == 'tie':
            notes.append("Both providers performed similarly")
        elif confidence > 0.3:
            notes.append(f"{winner} clearly outperformed the other")
        else:
            notes.append(f"{winner} slightly outperformed the other")
            
        return "; ".join(notes)
        
    def _store_comparison_result(self, comparison: ComparisonResult) -> None:
        """Store comparison result in JSONL format."""
        try:
            # Convert to JSON-serializable format
            comparison_data = {
                'timestamp': comparison.timestamp.isoformat(),
                'prompt': comparison.prompt,
                'task_type': comparison.task_type,
                'winner': comparison.winner,
                'confidence': comparison.confidence,
                'comparison_notes': comparison.comparison_notes,
                'openai_evaluation': {
                    'provider': comparison.openai_evaluation.provider,
                    'response_time': comparison.openai_evaluation.response_time,
                    'token_count': comparison.openai_evaluation.token_count,
                    'cost': comparison.openai_evaluation.cost,
                    'relevance_score': comparison.openai_evaluation.relevance_score,
                    'comprehensiveness_score': comparison.openai_evaluation.comprehensiveness_score,
                    'accuracy_score': comparison.openai_evaluation.accuracy_score,
                    'reliability_score': comparison.openai_evaluation.reliability_score,
                    'overall_score': comparison.openai_evaluation.overall_score,
                    'evaluation_notes': comparison.openai_evaluation.evaluation_notes
                },
                'grok_evaluation': {
                    'provider': comparison.grok_evaluation.provider,
                    'response_time': comparison.grok_evaluation.response_time,
                    'token_count': comparison.grok_evaluation.token_count,
                    'cost': comparison.grok_evaluation.cost,
                    'relevance_score': comparison.grok_evaluation.relevance_score,
                    'comprehensiveness_score': comparison.grok_evaluation.comprehensiveness_score,
                    'accuracy_score': comparison.grok_evaluation.accuracy_score,
                    'reliability_score': comparison.grok_evaluation.reliability_score,
                    'overall_score': comparison.grok_evaluation.overall_score,
                    'evaluation_notes': comparison.grok_evaluation.evaluation_notes
                }
            }
            
            # Write to JSONL file
            with open('evaluation/agent_comparison.jsonl', 'a') as f:
                json.dump(comparison_data, f)
                f.write('\n')
                
            logger.info(f"[P20P8S1T1] Comparison result stored")
            
        except Exception as e:
            logger.error(f"[P20P8S1T1] Failed to store comparison result: {e}")
            
    def get_evaluation_summary(self, limit: int = 10) -> Dict[str, Any]:
        """Get summary of recent evaluations."""
        try:
            comparisons = []
            
            if os.path.exists('evaluation/agent_comparison.jsonl'):
                with open('evaluation/agent_comparison.jsonl', 'r') as f:
                    for line in f:
                        if line.strip():
                            comparisons.append(json.loads(line))
                            
            # Get recent comparisons
            recent_comparisons = comparisons[-limit:] if comparisons else []
            
            # Calculate statistics
            if recent_comparisons:
                openai_wins = sum(1 for c in recent_comparisons if c['winner'] == 'openai')
                grok_wins = sum(1 for c in recent_comparisons if c['winner'] == 'grok')
                ties = sum(1 for c in recent_comparisons if c['winner'] == 'tie')
                
                avg_confidence = statistics.mean([c['confidence'] for c in recent_comparisons])
                
                summary = {
                    'total_comparisons': len(recent_comparisons),
                    'openai_wins': openai_wins,
                    'grok_wins': grok_wins,
                    'ties': ties,
                    'avg_confidence': avg_confidence,
                    'recent_comparisons': recent_comparisons
                }
            else:
                summary = {
                    'total_comparisons': 0,
                    'openai_wins': 0,
                    'grok_wins': 0,
                    'ties': 0,
                    'avg_confidence': 0.0,
                    'recent_comparisons': []
                }
                
            return summary
            
        except Exception as e:
            logger.error(f"[P20P8S1T1] Failed to get evaluation summary: {e}")
            return {}

def main():
    """Test the meta-evaluator system."""
    logger.info("[P20P8S1T1] Testing Meta-Evaluator System")
    
    evaluator = MetaEvaluator()
    
    # Test prompts
    test_cases = [
        ("Explain the benefits of using multiple AI providers", "explanation"),
        ("Review this code: def hello(): print('world')", "code_review"),
        ("Analyze the performance implications of this algorithm", "analysis")
    ]
    
    for prompt, task_type in test_cases:
        logger.info(f"[P20P8S1T1] Testing: {task_type}")
        try:
            comparison = evaluator.compare_responses(prompt, task_type)
            logger.info(f"[P20P8S1T1] Winner: {comparison.winner} (confidence: {comparison.confidence:.2f})")
        except Exception as e:
            logger.error(f"[P20P8S1T1] Test failed: {e}")
            
    # Get summary
    summary = evaluator.get_evaluation_summary()
    logger.info(f"[P20P8S1T1] Evaluation summary: {summary}")

if __name__ == "__main__":
    main() 