# P18P8S2 – Error/Fallback Triggers Module

"""
GitBridge Phase 18P8 - Fallback Simulation Engine

This module implements comprehensive fallback scenario simulation including
timeout, model failure, and escalation triggers with detailed audit logging.

Author: GitBridge MAS Integration Team
Phase: 18P8 - CLI Test Harness
MAS Lite Protocol: v2.1 Compliance
"""

import json
import time
import random
import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class FallbackType(Enum):
    """Types of fallback scenarios"""
    TIMEOUT = "timeout"
    MODEL_FAILURE = "model_failure"
    ESCALATION = "escalation"


@dataclass
class FallbackScenario:
    """Individual fallback scenario configuration"""
    scenario_id: str
    fallback_type: FallbackType
    thread_id: str
    uid: str
    model_id: str
    reason: str
    confidence_score: float
    timestamp: str
    duration_ms: int = 0
    error_code: Optional[str] = None
    escalation_trigger: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "scenario_id": self.scenario_id,
            "fallback_type": self.fallback_type.value,
            "thread_id": self.thread_id,
            "uid": self.uid,
            "model_id": self.model_id,
            "reason": self.reason,
            "confidence_score": self.confidence_score,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "error_code": self.error_code,
            "escalation_trigger": self.escalation_trigger,
            "mas_lite_protocol": "v2.1"
        }


@dataclass
class FallbackSimulationResults:
    """Results of fallback simulation run"""
    session_id: str
    total_scenarios: int
    successful_triggers: int
    failed_triggers: int
    scenarios: List[FallbackScenario] = field(default_factory=list)
    error_distribution: Dict[str, int] = field(default_factory=dict)
    execution_time_ms: int = 0
    start_time: str = ""
    end_time: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "total_scenarios": self.total_scenarios,
            "successful_triggers": self.successful_triggers,
            "failed_triggers": self.failed_triggers,
            "scenarios": [s.to_dict() for s in self.scenarios],
            "error_distribution": self.error_distribution,
            "execution_time_ms": self.execution_time_ms,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "mas_lite_protocol": "v2.1"
        }


class FallbackSimulator:
    """Advanced fallback scenario simulation engine"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.scenarios = []
        self.results = None
        
        # Available models for simulation
        self.models = [
            "gpt4_turbo", "claude3_5_sonnet", "gemini_pro", 
            "gpt3_5_turbo", "gpt4", "human_escalation"
        ]
        
        # Timeout ranges (in milliseconds)
        self.timeout_ranges = {
            "short": (1000, 3000),
            "medium": (3000, 10000),
            "long": (10000, 30000)
        }
        
        # Model failure error codes
        self.error_codes = [
            "API_TIMEOUT", "RATE_LIMIT_EXCEEDED", "MODEL_UNAVAILABLE",
            "INVALID_REQUEST", "AUTHENTICATION_FAILED", "QUOTA_EXCEEDED",
            "INTERNAL_ERROR", "SERVICE_DEGRADED", "CONNECTION_FAILED"
        ]
        
        # Escalation triggers
        self.escalation_triggers = [
            "confidence_too_low", "security_concern", "complex_request",
            "policy_violation", "user_request", "multiple_failures",
            "critical_error", "human_intervention_required"
        ]
        
        print(f"🔧 FallbackSimulator initialized for session: {session_id}")
    
    def generate_uid(self) -> str:
        """Generate MAS-compliant UID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        unique_string = f"fallback_{self.session_id}_{timestamp}_{random.randint(1000, 9999)}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    def generate_thread_id(self) -> str:
        """Generate thread identifier"""
        return f"thread_{random.randint(100000, 999999)}"
    
    def simulate_timeout_scenario(self) -> FallbackScenario:
        """Simulate a timeout fallback scenario"""
        scenario_id = self.generate_uid()
        thread_id = self.generate_thread_id()
        uid = self.generate_uid()
        model_id = random.choice(self.models[:-1])  # Exclude human_escalation
        
        # Choose timeout type and duration
        timeout_type = random.choice(["short", "medium", "long"])
        duration_ms = random.randint(*self.timeout_ranges[timeout_type])
        
        # Simulate the timeout delay
        time.sleep(duration_ms / 10000)  # Scale down for testing
        
        reason = f"Model {model_id} exceeded {timeout_type} timeout threshold ({duration_ms}ms)"
        confidence_score = random.uniform(0.1, 0.4)  # Low confidence due to timeout
        
        scenario = FallbackScenario(
            scenario_id=scenario_id,
            fallback_type=FallbackType.TIMEOUT,
            thread_id=thread_id,
            uid=uid,
            model_id=model_id,
            reason=reason,
            confidence_score=confidence_score,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_ms=duration_ms
        )
        
        return scenario
    
    def simulate_model_failure_scenario(self) -> FallbackScenario:
        """Simulate a model failure fallback scenario"""
        scenario_id = self.generate_uid()
        thread_id = self.generate_thread_id()
        uid = self.generate_uid()
        model_id = random.choice(self.models[:-1])  # Exclude human_escalation
        error_code = random.choice(self.error_codes)
        
        # Simulate processing time before failure
        duration_ms = random.randint(500, 2000)
        time.sleep(duration_ms / 10000)  # Scale down for testing
        
        reason = f"Model {model_id} failed with error: {error_code}"
        confidence_score = 0.0  # Zero confidence on failure
        
        scenario = FallbackScenario(
            scenario_id=scenario_id,
            fallback_type=FallbackType.MODEL_FAILURE,
            thread_id=thread_id,
            uid=uid,
            model_id=model_id,
            reason=reason,
            confidence_score=confidence_score,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_ms=duration_ms,
            error_code=error_code
        )
        
        return scenario
    
    def simulate_escalation_scenario(self) -> FallbackScenario:
        """Simulate an escalation trigger fallback scenario"""
        scenario_id = self.generate_uid()
        thread_id = self.generate_thread_id()
        uid = self.generate_uid()
        model_id = random.choice(self.models[:-1])  # Exclude human_escalation
        escalation_trigger = random.choice(self.escalation_triggers)
        
        # Simulate processing time before escalation
        duration_ms = random.randint(1000, 5000)
        time.sleep(duration_ms / 10000)  # Scale down for testing
        
        reason = f"Escalation triggered: {escalation_trigger}"
        confidence_score = random.uniform(0.2, 0.6)  # Variable confidence
        
        scenario = FallbackScenario(
            scenario_id=scenario_id,
            fallback_type=FallbackType.ESCALATION,
            thread_id=thread_id,
            uid=uid,
            model_id=model_id,
            reason=reason,
            confidence_score=confidence_score,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_ms=duration_ms,
            escalation_trigger=escalation_trigger
        )
        
        return scenario
    
    def run_fallback_simulation(self, count: int, fallback_types: List[str], 
                              logger: Any) -> FallbackSimulationResults:
        """
        Run comprehensive fallback simulation.
        
        Args:
            count (int): Number of scenarios to simulate
            fallback_types (List[str]): Types of fallbacks to include
            logger: Logger instance for output
            
        Returns:
            FallbackSimulationResults: Detailed simulation results
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting fallback simulation: {count} scenarios")
        
        # Determine which fallback types to simulate
        types_to_simulate = []
        if "all" in fallback_types:
            types_to_simulate = [FallbackType.TIMEOUT, FallbackType.MODEL_FAILURE, FallbackType.ESCALATION]
        else:
            for ft in fallback_types:
                if ft == "timeout":
                    types_to_simulate.append(FallbackType.TIMEOUT)
                elif ft == "model_failure":
                    types_to_simulate.append(FallbackType.MODEL_FAILURE)
                elif ft == "escalation":
                    types_to_simulate.append(FallbackType.ESCALATION)
        
        logger.info(f"Simulating types: {[t.value for t in types_to_simulate]}")
        
        scenarios = []
        successful_triggers = 0
        failed_triggers = 0
        
        for i in range(count):
            try:
                # Randomly select fallback type to simulate
                fallback_type = random.choice(types_to_simulate)
                
                logger.info(f"Scenario {i+1}/{count}: Simulating {fallback_type.value}")
                
                # Simulate the appropriate scenario
                if fallback_type == FallbackType.TIMEOUT:
                    scenario = self.simulate_timeout_scenario()
                elif fallback_type == FallbackType.MODEL_FAILURE:
                    scenario = self.simulate_model_failure_scenario()
                elif fallback_type == FallbackType.ESCALATION:
                    scenario = self.simulate_escalation_scenario()
                else:
                    raise ValueError(f"Unknown fallback type: {fallback_type}")
                
                scenarios.append(scenario)
                successful_triggers += 1
                
                logger.success(f"✅ {scenario.fallback_type.value} scenario completed")
                logger.info(f"   UID: {scenario.uid}")
                logger.info(f"   Thread: {scenario.thread_id}")
                logger.info(f"   Model: {scenario.model_id}")
                logger.info(f"   Confidence: {scenario.confidence_score:.3f}")
                logger.info(f"   Duration: {scenario.duration_ms}ms")
                
            except Exception as e:
                failed_triggers += 1
                logger.error(f"❌ Failed to simulate scenario {i+1}: {e}")
        
        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Generate error distribution statistics
        error_distribution = self._calculate_error_distribution(scenarios)
        
        # Create results object
        results = FallbackSimulationResults(
            session_id=self.session_id,
            total_scenarios=count,
            successful_triggers=successful_triggers,
            failed_triggers=failed_triggers,
            scenarios=scenarios,
            error_distribution=error_distribution,
            execution_time_ms=execution_time_ms,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )
        
        self.results = results
        
        # Log summary statistics
        logger.success(f"Simulation completed in {execution_time_ms}ms")
        logger.info(f"Successful triggers: {successful_triggers}")
        logger.info(f"Failed triggers: {failed_triggers}")
        logger.info(f"Success rate: {(successful_triggers/count)*100:.1f}%")
        
        return results
    
    def _calculate_error_distribution(self, scenarios: List[FallbackScenario]) -> Dict[str, int]:
        """Calculate distribution of error types"""
        distribution = {}
        
        for scenario in scenarios:
            fallback_type = scenario.fallback_type.value
            distribution[fallback_type] = distribution.get(fallback_type, 0) + 1
        
        return distribution
    
    def save_audit_report(self, output_file: str, logger: Any) -> bool:
        """Save detailed audit report to JSON file"""
        if not self.results:
            logger.error("No simulation results to save")
            return False
        
        try:
            audit_report = {
                "audit_metadata": {
                    "report_type": "fallback_simulation_audit",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "session_id": self.session_id,
                    "mas_lite_protocol": "v2.1"
                },
                "simulation_summary": {
                    "total_scenarios": self.results.total_scenarios,
                    "successful_triggers": self.results.successful_triggers,
                    "failed_triggers": self.results.failed_triggers,
                    "success_rate": (self.results.successful_triggers / self.results.total_scenarios) * 100,
                    "execution_time_ms": self.results.execution_time_ms,
                    "start_time": self.results.start_time,
                    "end_time": self.results.end_time
                },
                "error_distribution": self.results.error_distribution,
                "detailed_scenarios": [s.to_dict() for s in self.results.scenarios],
                "statistics": self._generate_statistics()
            }
            
            with open(output_file, 'w') as f:
                json.dump(audit_report, f, indent=2, default=str)
            
            logger.success(f"Audit report saved to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save audit report: {e}")
            return False
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate detailed statistics from simulation results"""
        if not self.results or not self.results.scenarios:
            return {}
        
        scenarios = self.results.scenarios
        
        # Confidence score statistics
        confidence_scores = [s.confidence_score for s in scenarios]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        min_confidence = min(confidence_scores)
        max_confidence = max(confidence_scores)
        
        # Duration statistics
        durations = [s.duration_ms for s in scenarios]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        # Model distribution
        model_distribution = {}
        for scenario in scenarios:
            model = scenario.model_id
            model_distribution[model] = model_distribution.get(model, 0) + 1
        
        # Error code distribution (for model failures)
        error_code_distribution = {}
        for scenario in scenarios:
            if scenario.error_code:
                code = scenario.error_code
                error_code_distribution[code] = error_code_distribution.get(code, 0) + 1
        
        # Escalation trigger distribution
        escalation_distribution = {}
        for scenario in scenarios:
            if scenario.escalation_trigger:
                trigger = scenario.escalation_trigger
                escalation_distribution[trigger] = escalation_distribution.get(trigger, 0) + 1
        
        return {
            "confidence_statistics": {
                "average": avg_confidence,
                "minimum": min_confidence,
                "maximum": max_confidence,
                "count": len(confidence_scores)
            },
            "duration_statistics": {
                "average_ms": avg_duration,
                "minimum_ms": min_duration,
                "maximum_ms": max_duration,
                "total_ms": sum(durations)
            },
            "model_distribution": model_distribution,
            "error_code_distribution": error_code_distribution,
            "escalation_trigger_distribution": escalation_distribution,
            "unique_threads": len(set(s.thread_id for s in scenarios)),
            "unique_uids": len(set(s.uid for s in scenarios))
        }


def create_sample_fallback_data(count: int = 5) -> List[Dict[str, Any]]:
    """Create sample fallback data for testing purposes"""
    simulator = FallbackSimulator("sample_session")
    
    sample_scenarios = []
    for i in range(count):
        fallback_type = random.choice([FallbackType.TIMEOUT, FallbackType.MODEL_FAILURE, FallbackType.ESCALATION])
        
        if fallback_type == FallbackType.TIMEOUT:
            scenario = simulator.simulate_timeout_scenario()
        elif fallback_type == FallbackType.MODEL_FAILURE:
            scenario = simulator.simulate_model_failure_scenario()
        else:  # ESCALATION
            scenario = simulator.simulate_escalation_scenario()
        
        sample_scenarios.append(scenario.to_dict())
    
    return sample_scenarios


if __name__ == "__main__":
    """Test the fallback simulator"""
    print("🧪 Testing Fallback Simulator")
    
    # Create sample data
    sample_data = create_sample_fallback_data(3)
    
    print(f"Generated {len(sample_data)} sample scenarios:")
    for i, scenario in enumerate(sample_data, 1):
        print(f"  {i}. {scenario['fallback_type']} - {scenario['model_id']} - {scenario['uid']}")
    
    # Save sample data
    with open("sample_fallback_scenarios.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    print("✅ Sample data saved to sample_fallback_scenarios.json") 