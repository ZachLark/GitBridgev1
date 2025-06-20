#!/usr/bin/env python3
"""
GitBridge Agent Behavior Model
Phase: GBP23
Part: P23P2
Step: P23P2S1
Task: P23P2S1T1 - Agent Traits and Behavior Modeling

Behavior model for storing agent traits, personality dimensions,
and behavioral patterns for trust analysis.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P23P2 Schema]
"""

import json
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
import math
import threading

logger = logging.getLogger(__name__)

@dataclass
class PersonalityTrait:
    """Represents a personality trait dimension."""
    name: str
    value: float  # Range: -1.0 to 1.0
    confidence: float = 0.0  # Range: 0.0 to 1.0
    evidence_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_value(self, new_value: float, confidence: float = 1.0, evidence: Optional[Dict[str, Any]] = None) -> None:
        """Update trait value with new evidence."""
        # Weighted average based on evidence count
        weight = 1.0 / (self.evidence_count + 1)
        self.value = (self.value * (1 - weight)) + (new_value * weight)
        self.confidence = (self.confidence * (1 - weight)) + (confidence * weight)
        self.evidence_count += 1
        self.last_updated = datetime.now(timezone.utc)
        
        if evidence:
            self.metadata.update(evidence)

@dataclass
class BehavioralPattern:
    """Represents a behavioral pattern or tendency."""
    pattern_type: str  # "consistency", "adaptability", "collaboration", "competition", etc.
    frequency: float = 0.0  # How often this pattern occurs (0.0 to 1.0)
    strength: float = 0.0   # How strongly this pattern is expressed (-1.0 to 1.0)
    context: str = "general"  # Context where this pattern applies
    confidence: float = 0.0
    observation_count: int = 0
    first_observed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_observed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_pattern(self, frequency: float, strength: float, context: str = "general", confidence: float = 1.0) -> None:
        """Update behavioral pattern with new observation."""
        weight = 1.0 / (self.observation_count + 1)
        self.frequency = (self.frequency * (1 - weight)) + (frequency * weight)
        self.strength = (self.strength * (1 - weight)) + (strength * weight)
        self.confidence = (self.confidence * (1 - weight)) + (confidence * weight)
        self.observation_count += 1
        self.last_observed = datetime.now(timezone.utc)
        
        if context != "general":
            self.context = context

@dataclass
class AgentBehavior:
    """Comprehensive behavior model for an agent."""
    agent_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Personality traits (Big Five + additional dimensions)
    personality_traits: Dict[str, PersonalityTrait] = field(default_factory=dict)
    
    # Behavioral patterns
    behavioral_patterns: Dict[str, BehavioralPattern] = field(default_factory=dict)
    
    # Interaction history
    total_interactions: int = 0
    successful_interactions: int = 0
    failed_interactions: int = 0
    
    # Specialization areas
    specializations: Set[str] = field(default_factory=set)
    
    # Behavioral metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_interactions == 0:
            return 0.0
        return self.successful_interactions / self.total_interactions
        
    @property
    def reliability_score(self) -> float:
        """Calculate reliability score based on consistency and success rate."""
        if self.total_interactions == 0:
            return 0.0
            
        # Base reliability on success rate
        base_reliability = self.success_rate
        
        # Adjust based on consistency (if we have consistency pattern)
        consistency_pattern = self.behavioral_patterns.get("consistency")
        if consistency_pattern:
            consistency_factor = (consistency_pattern.strength + 1.0) / 2.0  # Normalize to 0-1
            base_reliability = (base_reliability + consistency_factor) / 2.0
            
        return base_reliability
        
    @property
    def collaboration_score(self) -> float:
        """Calculate collaboration tendency score."""
        collaboration_pattern = self.behavioral_patterns.get("collaboration")
        if collaboration_pattern:
            return (collaboration_pattern.strength + 1.0) / 2.0  # Normalize to 0-1
        return 0.5  # Neutral default
        
    @property
    def adaptability_score(self) -> float:
        """Calculate adaptability score."""
        adaptability_pattern = self.behavioral_patterns.get("adaptability")
        if adaptability_pattern:
            return (adaptability_pattern.strength + 1.0) / 2.0  # Normalize to 0-1
        return 0.5  # Neutral default

class BehaviorModel:
    """
    Behavior model manager for tracking agent traits and patterns.
    
    Phase: GBP23
    Part: P23P2
    Step: P23P2S1
    Task: P23P2S1T1 - Core Implementation
    
    Features:
    - Personality trait tracking (Big Five + custom dimensions)
    - Behavioral pattern analysis
    - Interaction history and success rates
    - Specialization tracking
    - Predictive behavior modeling
    """
    
    def __init__(self, storage_path: str = "behavior_data", auto_save: bool = True):
        """
        Initialize behavior model.
        
        Args:
            storage_path: Directory for storing behavior data
            auto_save: Whether to automatically save changes
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Behavior data
        self.agents: Dict[str, AgentBehavior] = {}
        
        # Configuration
        self.auto_save = auto_save
        
        # Default personality dimensions (Big Five + additional)
        self.default_traits = {
            "openness": "Openness to experience",
            "conscientiousness": "Conscientiousness and organization",
            "extraversion": "Extraversion and sociability",
            "agreeableness": "Agreeableness and cooperation",
            "neuroticism": "Neuroticism and emotional stability",
            "curiosity": "Intellectual curiosity",
            "persistence": "Persistence and determination",
            "creativity": "Creative problem solving",
            "analytical": "Analytical thinking",
            "practical": "Practical and pragmatic approach"
        }
        
        # Default behavioral patterns
        self.default_patterns = {
            "consistency": "Consistency in behavior and responses",
            "adaptability": "Ability to adapt to new situations",
            "collaboration": "Tendency to collaborate with others",
            "competition": "Competitive behavior patterns",
            "innovation": "Innovative and creative approaches",
            "caution": "Cautious and careful behavior",
            "speed": "Speed of response and decision making",
            "quality": "Focus on quality over speed",
            "communication": "Communication style and clarity",
            "learning": "Learning and improvement patterns"
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load existing data
        self._load_data()
        
        logger.info(f"[P23P2S1T1] BehaviorModel initialized with {len(self.agents)} agents")
        
    def add_agent(self, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add an agent to the behavior model.
        
        Args:
            agent_id: Unique identifier for the agent
            metadata: Optional metadata for the agent
            
        Returns:
            bool: True if agent was added successfully
        """
        with self._lock:
            if agent_id in self.agents:
                logger.warning(f"[P23P2S1T1] Agent {agent_id} already exists in behavior model")
                return False
                
            agent = AgentBehavior(agent_id=agent_id, metadata=metadata or {})
            self.agents[agent_id] = agent
            
            # Initialize default traits
            for trait_name in self.default_traits:
                agent.personality_traits[trait_name] = PersonalityTrait(
                    name=trait_name,
                    value=0.0,  # Neutral default
                    confidence=0.0
                )
                
            # Initialize default patterns
            for pattern_name in self.default_patterns:
                agent.behavioral_patterns[pattern_name] = BehavioralPattern(
                    pattern_type=pattern_name,
                    frequency=0.0,
                    strength=0.0,
                    confidence=0.0
                )
                
            if self.auto_save:
                self._save_data()
                
            logger.info(f"[P23P2S1T1] Added agent {agent_id} to behavior model")
            return True
            
    def update_personality_trait(
        self, 
        agent_id: str, 
        trait_name: str, 
        value: float, 
        confidence: float = 1.0,
        evidence: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a personality trait for an agent.
        
        Args:
            agent_id: ID of the agent
            trait_name: Name of the trait to update
            value: New trait value (-1.0 to 1.0)
            confidence: Confidence in the assessment (0.0 to 1.0)
            evidence: Optional evidence supporting the assessment
            
        Returns:
            bool: True if trait was updated successfully
        """
        with self._lock:
            if agent_id not in self.agents:
                logger.warning(f"[P23P2S1T1] Agent {agent_id} not found in behavior model")
                return False
                
            agent = self.agents[agent_id]
            
            # Validate value range
            value = max(-1.0, min(1.0, value))
            confidence = max(0.0, min(1.0, confidence))
            
            # Update or create trait
            if trait_name in agent.personality_traits:
                agent.personality_traits[trait_name].update_value(value, confidence, evidence)
            else:
                agent.personality_traits[trait_name] = PersonalityTrait(
                    name=trait_name,
                    value=value,
                    confidence=confidence,
                    evidence_count=1,
                    metadata=evidence or {}
                )
                
            agent.updated_at = datetime.now(timezone.utc)
            
            if self.auto_save:
                self._save_data()
                
            logger.debug(f"[P23P2S1T1] Updated trait {trait_name} for {agent_id}: {value:.3f}")
            return True
            
    def update_behavioral_pattern(
        self, 
        agent_id: str, 
        pattern_type: str, 
        frequency: float, 
        strength: float,
        context: str = "general",
        confidence: float = 1.0
    ) -> bool:
        """
        Update a behavioral pattern for an agent.
        
        Args:
            agent_id: ID of the agent
            pattern_type: Type of behavioral pattern
            frequency: How often this pattern occurs (0.0 to 1.0)
            strength: How strongly this pattern is expressed (-1.0 to 1.0)
            context: Context where this pattern applies
            confidence: Confidence in the assessment (0.0 to 1.0)
            
        Returns:
            bool: True if pattern was updated successfully
        """
        with self._lock:
            if agent_id not in self.agents:
                logger.warning(f"[P23P2S1T1] Agent {agent_id} not found in behavior model")
                return False
                
            agent = self.agents[agent_id]
            
            # Validate ranges
            frequency = max(0.0, min(1.0, frequency))
            strength = max(-1.0, min(1.0, strength))
            confidence = max(0.0, min(1.0, confidence))
            
            # Update or create pattern
            if pattern_type in agent.behavioral_patterns:
                agent.behavioral_patterns[pattern_type].update_pattern(frequency, strength, context, confidence)
            else:
                agent.behavioral_patterns[pattern_type] = BehavioralPattern(
                    pattern_type=pattern_type,
                    frequency=frequency,
                    strength=strength,
                    context=context,
                    confidence=confidence,
                    observation_count=1
                )
                
            agent.updated_at = datetime.now(timezone.utc)
            
            if self.auto_save:
                self._save_data()
                
            logger.debug(f"[P23P2S1T1] Updated pattern {pattern_type} for {agent_id}: freq={frequency:.3f}, strength={strength:.3f}")
            return True
            
    def record_interaction(
        self, 
        agent_id: str, 
        success: bool, 
        context: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record an interaction for an agent.
        
        Args:
            agent_id: ID of the agent
            success: Whether the interaction was successful
            context: Context of the interaction
            metadata: Optional metadata about the interaction
            
        Returns:
            bool: True if interaction was recorded successfully
        """
        with self._lock:
            if agent_id not in self.agents:
                logger.warning(f"[P23P2S1T1] Agent {agent_id} not found in behavior model")
                return False
                
            agent = self.agents[agent_id]
            
            agent.total_interactions += 1
            if success:
                agent.successful_interactions += 1
            else:
                agent.failed_interactions += 1
                
            agent.updated_at = datetime.now(timezone.utc)
            
            if metadata:
                agent.metadata.update(metadata)
                
            if self.auto_save:
                self._save_data()
                
            logger.debug(f"[P23P2S1T1] Recorded {'successful' if success else 'failed'} interaction for {agent_id}")
            return True
            
    def add_specialization(self, agent_id: str, specialization: str) -> bool:
        """
        Add a specialization for an agent.
        
        Args:
            agent_id: ID of the agent
            specialization: Specialization area
            
        Returns:
            bool: True if specialization was added successfully
        """
        with self._lock:
            if agent_id not in self.agents:
                logger.warning(f"[P23P2S1T1] Agent {agent_id} not found in behavior model")
                return False
                
            agent = self.agents[agent_id]
            agent.specializations.add(specialization)
            agent.updated_at = datetime.now(timezone.utc)
            
            if self.auto_save:
                self._save_data()
                
            logger.debug(f"[P23P2S1T1] Added specialization '{specialization}' for {agent_id}")
            return True
            
    def get_agent_behavior(self, agent_id: str) -> Optional[AgentBehavior]:
        """
        Get behavior data for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            AgentBehavior: Behavior data if agent exists, None otherwise
        """
        with self._lock:
            return self.agents.get(agent_id)
            
    def get_behavior_summary(self, agent_id: str) -> Dict[str, Any]:
        """
        Get comprehensive behavior summary for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dict containing behavior summary
        """
        with self._lock:
            if agent_id not in self.agents:
                return {}
                
            agent = self.agents[agent_id]
            
            # Calculate trait averages
            trait_summary = {}
            for trait_name, trait in agent.personality_traits.items():
                trait_summary[trait_name] = {
                    "value": trait.value,
                    "confidence": trait.confidence,
                    "evidence_count": trait.evidence_count,
                    "description": self.default_traits.get(trait_name, "Custom trait")
                }
                
            # Calculate pattern summary
            pattern_summary = {}
            for pattern_name, pattern in agent.behavioral_patterns.items():
                pattern_summary[pattern_name] = {
                    "frequency": pattern.frequency,
                    "strength": pattern.strength,
                    "confidence": pattern.confidence,
                    "context": pattern.context,
                    "observation_count": pattern.observation_count,
                    "description": self.default_patterns.get(pattern_name, "Custom pattern")
                }
                
            return {
                "agent_id": agent_id,
                "total_interactions": agent.total_interactions,
                "successful_interactions": agent.successful_interactions,
                "failed_interactions": agent.failed_interactions,
                "success_rate": agent.success_rate,
                "reliability_score": agent.reliability_score,
                "collaboration_score": agent.collaboration_score,
                "adaptability_score": agent.adaptability_score,
                "specializations": list(agent.specializations),
                "personality_traits": trait_summary,
                "behavioral_patterns": pattern_summary,
                "created_at": agent.created_at.isoformat(),
                "updated_at": agent.updated_at.isoformat(),
                "metadata": agent.metadata
            }
            
    def predict_behavior(self, agent_id: str, context: str = "general") -> Dict[str, Any]:
        """
        Predict agent behavior in a given context.
        
        Args:
            agent_id: ID of the agent
            context: Context for prediction
            
        Returns:
            Dict containing behavior predictions
        """
        with self._lock:
            if agent_id not in self.agents:
                return {}
                
            agent = self.agents[agent_id]
            
            # Base predictions on personality traits and patterns
            predictions = {
                "reliability": agent.reliability_score,
                "collaboration_tendency": agent.collaboration_score,
                "adaptability": agent.adaptability_score,
                "expected_success_rate": agent.success_rate,
                "communication_style": "neutral",
                "decision_speed": "medium",
                "risk_tolerance": "medium"
            }
            
            # Adjust predictions based on personality traits
            if "conscientiousness" in agent.personality_traits:
                trait = agent.personality_traits["conscientiousness"]
                if trait.value > 0.5:
                    predictions["reliability"] *= 1.2
                    predictions["decision_speed"] = "slow"
                elif trait.value < -0.5:
                    predictions["reliability"] *= 0.8
                    predictions["decision_speed"] = "fast"
                    
            if "extraversion" in agent.personality_traits:
                trait = agent.personality_traits["extraversion"]
                if trait.value > 0.5:
                    predictions["communication_style"] = "expressive"
                    predictions["collaboration_tendency"] *= 1.1
                elif trait.value < -0.5:
                    predictions["communication_style"] = "reserved"
                    
            if "neuroticism" in agent.personality_traits:
                trait = agent.personality_traits["neuroticism"]
                if trait.value > 0.5:
                    predictions["risk_tolerance"] = "low"
                elif trait.value < -0.5:
                    predictions["risk_tolerance"] = "high"
                    
            # Adjust based on behavioral patterns
            if "speed" in agent.behavioral_patterns:
                pattern = agent.behavioral_patterns["speed"]
                if pattern.strength > 0.5:
                    predictions["decision_speed"] = "fast"
                elif pattern.strength < -0.5:
                    predictions["decision_speed"] = "slow"
                    
            if "caution" in agent.behavioral_patterns:
                pattern = agent.behavioral_patterns["caution"]
                if pattern.strength > 0.5:
                    predictions["risk_tolerance"] = "low"
                elif pattern.strength < -0.5:
                    predictions["risk_tolerance"] = "high"
                    
            # Context-specific adjustments
            if context in agent.specializations:
                predictions["expected_success_rate"] *= 1.2
                predictions["reliability"] *= 1.1
                
            return predictions
            
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the behavior model.
        
        Returns:
            Dict containing model statistics
        """
        with self._lock:
            total_agents = len(self.agents)
            total_interactions = sum(agent.total_interactions for agent in self.agents.values())
            total_successful = sum(agent.successful_interactions for agent in self.agents.values())
            
            avg_success_rate = total_successful / total_interactions if total_interactions > 0 else 0.0
            
            # Calculate average trait values
            trait_averages = {}
            for trait_name in self.default_traits:
                values = [agent.personality_traits[trait_name].value 
                         for agent in self.agents.values() 
                         if trait_name in agent.personality_traits]
                if values:
                    trait_averages[trait_name] = sum(values) / len(values)
                    
            # Calculate average pattern strengths
            pattern_averages = {}
            for pattern_name in self.default_patterns:
                strengths = [agent.behavioral_patterns[pattern_name].strength 
                           for agent in self.agents.values() 
                           if pattern_name in agent.behavioral_patterns]
                if strengths:
                    pattern_averages[pattern_name] = sum(strengths) / len(strengths)
                    
            return {
                "total_agents": total_agents,
                "total_interactions": total_interactions,
                "total_successful_interactions": total_successful,
                "avg_success_rate": avg_success_rate,
                "trait_averages": trait_averages,
                "pattern_averages": pattern_averages,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
    def export_data(self, format: str = "json") -> str:
        """
        Export behavior data to various formats.
        
        Args:
            format: Export format ("json", "csv")
            
        Returns:
            str: Exported data
        """
        with self._lock:
            if format == "json":
                data = {
                    "agents": [asdict(agent) for agent in self.agents.values()],
                    "metadata": {
                        "exported_at": datetime.now(timezone.utc).isoformat(),
                        "version": "1.0.0",
                        "default_traits": self.default_traits,
                        "default_patterns": self.default_patterns
                    }
                }
                return json.dumps(data, indent=2, default=str)
            elif format == "csv":
                lines = ["agent_id,trait_name,trait_value,confidence,pattern_name,pattern_frequency,pattern_strength"]
                for agent in self.agents.values():
                    for trait_name, trait in agent.personality_traits.items():
                        lines.append(f"{agent.agent_id},{trait_name},{trait.value},{trait.confidence},,,,,")
                    for pattern_name, pattern in agent.behavioral_patterns.items():
                        lines.append(f"{agent.agent_id},,,,{pattern_name},{pattern.frequency},{pattern.strength}")
                return "\n".join(lines)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
    def _save_data(self) -> None:
        """Save behavior data to disk."""
        try:
            data = {
                "agents": [asdict(agent) for agent in self.agents.values()],
                "metadata": {
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0.0"
                }
            }
            
            with open(self.storage_path / "behavior_model.json", 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            logger.debug(f"[P23P2S1T1] Saved behavior data to {self.storage_path}")
            
        except Exception as e:
            logger.error(f"[P23P2S1T1] Failed to save behavior data: {e}")
            
    def _load_data(self) -> None:
        """Load behavior data from disk."""
        try:
            data_file = self.storage_path / "behavior_model.json"
            if not data_file.exists():
                logger.info(f"[P23P2S1T1] No existing behavior data found at {data_file}")
                return
                
            with open(data_file, 'r') as f:
                data = json.load(f)
                
            # Load agents
            for agent_data in data.get('agents', []):
                agent = AgentBehavior(
                    agent_id=agent_data['agent_id'],
                    created_at=datetime.fromisoformat(agent_data['created_at']),
                    updated_at=datetime.fromisoformat(agent_data['updated_at']),
                    total_interactions=agent_data['total_interactions'],
                    successful_interactions=agent_data['successful_interactions'],
                    failed_interactions=agent_data['failed_interactions'],
                    specializations=set(agent_data.get('specializations', [])),
                    metadata=agent_data.get('metadata', {})
                )
                
                # Load personality traits
                for trait_data in agent_data.get('personality_traits', {}).values():
                    trait = PersonalityTrait(
                        name=trait_data['name'],
                        value=trait_data['value'],
                        confidence=trait_data['confidence'],
                        evidence_count=trait_data['evidence_count'],
                        last_updated=datetime.fromisoformat(trait_data['last_updated']),
                        metadata=trait_data.get('metadata', {})
                    )
                    agent.personality_traits[trait.name] = trait
                    
                # Load behavioral patterns
                for pattern_data in agent_data.get('behavioral_patterns', {}).values():
                    pattern = BehavioralPattern(
                        pattern_type=pattern_data['pattern_type'],
                        frequency=pattern_data['frequency'],
                        strength=pattern_data['strength'],
                        context=pattern_data['context'],
                        confidence=pattern_data['confidence'],
                        observation_count=pattern_data['observation_count'],
                        first_observed=datetime.fromisoformat(pattern_data['first_observed']),
                        last_observed=datetime.fromisoformat(pattern_data['last_observed']),
                        metadata=pattern_data.get('metadata', {})
                    )
                    agent.behavioral_patterns[pattern.pattern_type] = pattern
                    
                self.agents[agent.agent_id] = agent
                
            logger.info(f"[P23P2S1T1] Loaded behavior data: {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"[P23P2S1T1] Failed to load behavior data: {e}")

def main():
    """CLI interface for behavior model operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitBridge Behavior Model CLI")
    parser.add_argument("--storage", default="behavior_data", help="Storage directory")
    parser.add_argument("--command", required=True, choices=["add", "trait", "pattern", "interaction", "summary", "predict", "stats", "export"])
    parser.add_argument("--agent-id", help="Agent ID")
    parser.add_argument("--trait-name", help="Trait name")
    parser.add_argument("--trait-value", type=float, help="Trait value (-1.0 to 1.0)")
    parser.add_argument("--pattern-type", help="Pattern type")
    parser.add_argument("--frequency", type=float, help="Pattern frequency (0.0 to 1.0)")
    parser.add_argument("--strength", type=float, help="Pattern strength (-1.0 to 1.0)")
    parser.add_argument("--success", action="store_true", help="Interaction was successful")
    parser.add_argument("--format", default="json", choices=["json", "csv"], help="Export format")
    
    args = parser.parse_args()
    
    model = BehaviorModel(storage_path=args.storage)
    
    if args.command == "add":
        if not args.agent_id:
            print("Error: --agent-id required for add command")
            return
        success = model.add_agent(args.agent_id)
        print(f"Agent added: {success}")
        
    elif args.command == "trait":
        if not all([args.agent_id, args.trait_name, args.trait_value is not None]):
            print("Error: --agent-id, --trait-name, and --trait-value required for trait command")
            return
        success = model.update_personality_trait(args.agent_id, args.trait_name, args.trait_value)
        print(f"Trait updated: {success}")
        
    elif args.command == "pattern":
        if not all([args.agent_id, args.pattern_type, args.frequency is not None, args.strength is not None]):
            print("Error: --agent-id, --pattern-type, --frequency, and --strength required for pattern command")
            return
        success = model.update_behavioral_pattern(args.agent_id, args.pattern_type, args.frequency, args.strength)
        print(f"Pattern updated: {success}")
        
    elif args.command == "interaction":
        if not all([args.agent_id, args.success is not None]):
            print("Error: --agent-id and --success required for interaction command")
            return
        success = model.record_interaction(args.agent_id, args.success)
        print(f"Interaction recorded: {success}")
        
    elif args.command == "summary":
        if not args.agent_id:
            print("Error: --agent-id required for summary command")
            return
        summary = model.get_behavior_summary(args.agent_id)
        print(json.dumps(summary, indent=2))
        
    elif args.command == "predict":
        if not args.agent_id:
            print("Error: --agent-id required for predict command")
            return
        predictions = model.predict_behavior(args.agent_id)
        print(json.dumps(predictions, indent=2))
        
    elif args.command == "stats":
        stats = model.get_statistics()
        print(json.dumps(stats, indent=2))
        
    elif args.command == "export":
        data = model.export_data(args.format)
        print(data)

if __name__ == "__main__":
    main()
