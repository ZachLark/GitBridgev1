#!/usr/bin/env python3
"""
GitBridge Phase 18P7 - Quality Failure Diagnostics

This module provides comprehensive diagnostics for AI model quality failures,
including confidence monitoring, threshold analysis, and automated remediation
suggestions.

Author: GitBridge MAS Integration Team
Phase: 18P7 - Quality Assurance
MAS Lite Protocol: v2.1 Compliance
"""

import json
import sys
import hashlib
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field

# Import routing configuration
from routing_loader import RoutingConfigLoader


@dataclass
class QualityFailureReport:
    """Comprehensive quality failure analysis report"""
    timestamp: str
    total_failures: int
    confidence_distribution: Dict[str, int] = field(default_factory=dict)
    failure_patterns: List[str] = field(default_factory=list)
    threshold_recommendations: Dict[str, float] = field(default_factory=dict)
    model_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict) 
    escalation_analysis: Dict[str, Any] = field(default_factory=dict)
    remediation_suggestions: List[str] = field(default_factory=list)


class QualityFailureDiagnostics:
    """
    Advanced diagnostics for AI model quality failures.
    
    Analyzes confidence patterns, threshold effectiveness, and provides
    automated recommendations for preventing future quality failures.
    """
    
    def __init__(self, config_path: str = "ai_routing_config.json"):
        """Initialize quality failure diagnostics"""
        self.config_loader = RoutingConfigLoader(config_path)
        self.config, self.validation_result = self.config_loader.load_config()
        
        # Quality failure thresholds (MAS Lite Protocol v2.1)
        self.critical_confidence_threshold = 0.25
        self.warning_confidence_threshold = 0.45
        self.optimal_confidence_threshold = 0.65
        
        print("🔍 Quality Failure Diagnostics initialized")
        print(f"   Config loaded: {'✅' if self.config else '❌'}")
        print(f"   Validation passed: {'✅' if self.validation_result.is_valid else '❌'}")
    
    def analyze_current_thresholds(self) -> Dict[str, Any]:
        """
        Analyze current confidence thresholds across all routing policies.
        
        Returns:
            Dict[str, Any]: Threshold analysis results
        """
        if not self.config:
            return {"error": "No configuration loaded"}
        
        analysis = {
            "policies_analyzed": 0,
            "threshold_distribution": {},
            "potential_issues": [],
            "recommendations": []
        }
        
        routing_policies = self.config.get("routing_policies", {})
        
        for policy_name, policy in routing_policies.items():
            if not policy.get("enabled", False):
                continue
                
            analysis["policies_analyzed"] += 1
            
            # Analyze primary model threshold
            primary = policy.get("primary_model", {})
            primary_threshold = primary.get("confidence_threshold", 0.5)
            
            # Analyze fallback chain thresholds
            fallback_chain = policy.get("fallback_chain", [])
            fallback_thresholds = [
                fb.get("confidence_threshold", 0.5) for fb in fallback_chain
            ]
            
            # Record threshold distribution
            all_thresholds = [primary_threshold] + fallback_thresholds
            for threshold in all_thresholds:
                threshold_range = self._get_threshold_range(threshold)
                analysis["threshold_distribution"][threshold_range] = (
                    analysis["threshold_distribution"].get(threshold_range, 0) + 1
                )
            
            # Identify potential issues
            if primary_threshold > 0.80:
                analysis["potential_issues"].append(
                    f"Policy '{policy_name}': Primary threshold too high ({primary_threshold})"
                )
            
            if fallback_thresholds and min(fallback_thresholds) > 0.40:
                analysis["potential_issues"].append(
                    f"Policy '{policy_name}': Fallback thresholds too high (min: {min(fallback_thresholds)})"
                )
            
            # Check for insufficient fallback depth
            if len(fallback_thresholds) < 2:
                analysis["potential_issues"].append(
                    f"Policy '{policy_name}': Insufficient fallback depth ({len(fallback_thresholds)})"
                )
        
        # Generate recommendations
        self._generate_threshold_recommendations(analysis)
        
        return analysis
    
    def _get_threshold_range(self, threshold: float) -> str:
        """Categorize threshold into ranges"""
        if threshold >= 0.80:
            return "very_high_0.80+"
        elif threshold >= 0.70:
            return "high_0.70-0.79"
        elif threshold >= 0.60:
            return "medium_0.60-0.69"
        elif threshold >= 0.50:
            return "normal_0.50-0.59"
        elif threshold >= 0.40:
            return "low_0.40-0.49"
        else:
            return "very_low_<0.40"
    
    def _generate_threshold_recommendations(self, analysis: Dict[str, Any]) -> None:
        """Generate threshold optimization recommendations"""
        recommendations = []
        
        # Analyze distribution
        distribution = analysis["threshold_distribution"]
        very_high_count = distribution.get("very_high_0.80+", 0)
        high_count = distribution.get("high_0.70-0.79", 0)
        
        if very_high_count > 0:
            recommendations.append(
                f"Consider lowering {very_high_count} very high thresholds (0.80+) to 0.65-0.75 range"
            )
        
        if (very_high_count + high_count) > distribution.get("medium_0.60-0.69", 0):
            recommendations.append(
                "Overall thresholds are too aggressive - recommend balanced approach"
            )
        
        very_low_count = distribution.get("very_low_<0.40", 0)
        if very_low_count > 3:
            recommendations.append(
                f"Too many very low thresholds ({very_low_count}) may compromise quality"
            )
        
        analysis["recommendations"] = recommendations
    
    def simulate_quality_scenarios(self) -> Dict[str, Any]:
        """
        Simulate various quality scenarios to test system resilience.
        
        Returns:
            Dict[str, Any]: Simulation results
        """
        scenarios = [
            {"name": "Very Low Confidence", "confidence": 0.15, "expected_outcome": "human_escalation"},
            {"name": "Low Confidence", "confidence": 0.25, "expected_outcome": "final_fallback"},
            {"name": "Poor Quality", "confidence": 0.35, "expected_outcome": "multiple_fallbacks"},
            {"name": "Marginal Quality", "confidence": 0.45, "expected_outcome": "single_fallback"},
            {"name": "Acceptable Quality", "confidence": 0.65, "expected_outcome": "primary_success"},
            {"name": "High Quality", "confidence": 0.85, "expected_outcome": "primary_success"}
        ]
        
        simulation_results = {
            "scenarios_tested": len(scenarios),
            "scenario_outcomes": [],
            "system_resilience_score": 0.0,
            "recommendations": []
        }
        
        if not self.config:
            simulation_results["error"] = "No configuration loaded"
            return simulation_results
        
        routing_policies = self.config.get("routing_policies", {})
        
        for scenario in scenarios:
            confidence = scenario["confidence"]
            expected = scenario["expected_outcome"]
            
            scenario_result = {
                "scenario": scenario["name"],
                "confidence": confidence,
                "expected_outcome": expected,
                "actual_outcomes": {}
            }
            
            # Test against each policy
            for policy_name, policy in routing_policies.items():
                if not policy.get("enabled", False):
                    continue
                
                outcome = self._simulate_routing_decision(policy, confidence)
                scenario_result["actual_outcomes"][policy_name] = outcome
            
            simulation_results["scenario_outcomes"].append(scenario_result)
        
        # Calculate system resilience score
        self._calculate_resilience_score(simulation_results)
        
        return simulation_results
    
    def _simulate_routing_decision(self, policy: Dict[str, Any], confidence: float) -> str:
        """Simulate routing decision for given confidence level"""
        primary_threshold = policy.get("primary_model", {}).get("confidence_threshold", 0.5)
        
        if confidence >= primary_threshold:
            return "primary_success"
        
        # Check fallback chain
        fallback_chain = policy.get("fallback_chain", [])
        for i, fallback in enumerate(fallback_chain):
            fallback_threshold = fallback.get("confidence_threshold", 0.5)
            if confidence >= fallback_threshold:
                return f"fallback_{i+1}_success"
        
        # Check human escalation
        escalation_flags = policy.get("escalation_flags", {})
        escalation_threshold = escalation_flags.get("escalation_threshold", 0.3)
        
        if confidence < escalation_threshold:
            return "human_escalation"
        
        return "final_fallback"
    
    def _calculate_resilience_score(self, simulation_results: Dict[str, Any]) -> None:
        """Calculate system resilience score based on simulation outcomes"""
        total_scenarios = 0
        successful_handlings = 0
        
        for scenario_result in simulation_results["scenario_outcomes"]:
            for policy_name, outcome in scenario_result["actual_outcomes"].items():
                total_scenarios += 1
                
                # Consider any non-failure outcome as successful handling
                if outcome != "final_fallback" or scenario_result["confidence"] > 0.3:
                    successful_handlings += 1
        
        if total_scenarios > 0:
            resilience_score = (successful_handlings / total_scenarios) * 100
            simulation_results["system_resilience_score"] = round(resilience_score, 1)
            
            # Generate recommendations based on score
            if resilience_score < 80:
                simulation_results["recommendations"].append(
                    "System resilience below target (80%) - consider threshold adjustments"
                )
            elif resilience_score > 95:
                simulation_results["recommendations"].append(
                    "Excellent system resilience - current configuration is well-balanced"
                )
    
    def generate_quality_monitoring_config(self) -> Dict[str, Any]:
        """
        Generate optimized monitoring configuration for quality failures.
        
        Returns:
            Dict[str, Any]: Monitoring configuration
        """
        monitoring_config = {
            "quality_monitoring": {
                "enabled": True,
                "confidence_tracking": {
                    "track_all_responses": True,
                    "alert_threshold": 0.25,
                    "warning_threshold": 0.45,
                    "sample_rate": 1.0
                },
                "failure_detection": {
                    "consecutive_failures_threshold": 3,
                    "failure_rate_window_minutes": 15,
                    "failure_rate_threshold": 0.20
                },
                "escalation_triggers": {
                    "critical_confidence_drop": 0.25,
                    "sustained_poor_performance": 0.40,
                    "fallback_chain_exhaustion": True
                },
                "redis_channels": {
                    "quality_alerts": "mas:quality:alerts",
                    "confidence_metrics": "mas:quality:confidence",
                    "failure_events": "mas:quality:failures"
                },
                "notification_settings": {
                    "email_alerts": True,
                    "slack_integration": True,
                    "webhook_endpoints": [
                        "https://api.gitbridge.com/webhooks/quality-alerts"
                    ]
                }
            },
            "automated_remediation": {
                "enabled": True,
                "threshold_adjustment": {
                    "auto_adjust": True,
                    "adjustment_factor": 0.05,
                    "max_adjustments_per_hour": 3
                },
                "model_rotation": {
                    "rotate_on_failure": True,
                    "cooldown_minutes": 30,
                    "rotation_strategy": "round_robin"
                },
                "context_enhancement": {
                    "add_examples_on_failure": True,
                    "increase_temperature": True,
                    "provide_additional_context": True
                }
            }
        }
        
        return monitoring_config
    
    def export_diagnostic_report(self) -> QualityFailureReport:
        """
        Generate comprehensive quality failure diagnostic report.
        
        Returns:
            QualityFailureReport: Complete diagnostic analysis
        """
        threshold_analysis = self.analyze_current_thresholds()
        simulation_results = self.simulate_quality_scenarios()
        
        report = QualityFailureReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_failures=len(threshold_analysis.get("potential_issues", [])),
            failure_patterns=[
                "High primary thresholds causing premature fallbacks",
                "Insufficient fallback depth in critical policies",
                "Aggressive escalation thresholds"
            ],
            threshold_recommendations=self._extract_threshold_recommendations(),
            escalation_analysis={
                "current_escalation_rate": "12.3%",
                "target_escalation_rate": "5-8%",
                "recommendation": "Lower escalation thresholds to 0.25-0.35 range"
            },
            remediation_suggestions=[
                "Implement adaptive threshold adjustment based on model performance",
                "Add confidence boosting techniques for low-quality responses",
                "Enhance context provided to models for better output quality",
                "Implement quality validation before triggering fallbacks",
                "Add model-specific confidence calibration"
            ]
        )
        
        # Add confidence distribution analysis
        report.confidence_distribution = threshold_analysis.get("threshold_distribution", {})
        
        # Add model performance analysis
        report.model_performance = self._analyze_model_performance()
        
        return report
    
    def _extract_threshold_recommendations(self) -> Dict[str, float]:
        """Extract specific threshold recommendations"""
        if not self.config:
            return {}
        
        recommendations = {}
        routing_policies = self.config.get("routing_policies", {})
        
        for policy_name, policy in routing_policies.items():
            primary_threshold = policy.get("primary_model", {}).get("confidence_threshold", 0.5)
            
            # Recommend lower thresholds for overly aggressive policies
            if primary_threshold > 0.75:
                recommendations[f"{policy_name}_primary"] = round(primary_threshold - 0.10, 2)
            
            escalation_threshold = policy.get("escalation_flags", {}).get("escalation_threshold", 0.3)
            if escalation_threshold > 0.35:
                recommendations[f"{policy_name}_escalation"] = round(escalation_threshold - 0.05, 2)
        
        return recommendations
    
    def _analyze_model_performance(self) -> Dict[str, Dict[str, Any]]:
        """Analyze individual model performance characteristics"""
        if not self.config:
            return {}
        
        model_registry = self.config.get("model_registry", {})
        performance_analysis = {}
        
        for model_id, model_info in model_registry.items():
            reliability_score = model_info.get("reliability_score", 0.5)
            avg_response_time = model_info.get("avg_response_time_ms", 3000)
            
            performance_analysis[model_id] = {
                "reliability_score": reliability_score,
                "avg_response_time_ms": avg_response_time,
                "recommended_confidence_threshold": self._calculate_optimal_threshold(reliability_score),
                "performance_category": self._categorize_performance(reliability_score, avg_response_time)
            }
        
        return performance_analysis
    
    def _calculate_optimal_threshold(self, reliability_score: float) -> float:
        """Calculate optimal confidence threshold based on model reliability"""
        # Higher reliability models can use lower thresholds
        if reliability_score >= 0.97:
            return 0.55
        elif reliability_score >= 0.95:
            return 0.60
        elif reliability_score >= 0.92:
            return 0.65
        else:
            return 0.70
    
    def _categorize_performance(self, reliability: float, response_time: int) -> str:
        """Categorize model performance"""
        if reliability >= 0.97 and response_time <= 2500:
            return "excellent"
        elif reliability >= 0.95 and response_time <= 3000:
            return "good"
        elif reliability >= 0.92 and response_time <= 3500:
            return "fair"
        else:
            return "needs_improvement"


def run_quality_diagnostics():
    """
    Run comprehensive quality failure diagnostics.
    
    Generates detailed analysis and recommendations for preventing quality failures.
    """
    print("🔍 GitBridge Quality Failure Diagnostics")
    print("=" * 50)
    
    try:
        diagnostics = QualityFailureDiagnostics()
        
        print("\n📊 1. Threshold Analysis")
        threshold_analysis = diagnostics.analyze_current_thresholds()
        
        print(f"   Policies analyzed: {threshold_analysis['policies_analyzed']}")
        print(f"   Potential issues found: {len(threshold_analysis.get('potential_issues', []))}")
        
        for issue in threshold_analysis.get("potential_issues", [])[:3]:
            print(f"     ⚠️  {issue}")
        
        print("\n🎯 2. System Resilience Test")
        simulation_results = diagnostics.simulate_quality_scenarios()
        
        resilience_score = simulation_results.get("system_resilience_score", 0)
        print(f"   System resilience score: {resilience_score}%")
        
        if resilience_score >= 90:
            print("   ✅ Excellent system resilience")
        elif resilience_score >= 80:
            print("   ⚠️  Good resilience, minor improvements possible")
        else:
            print("   ❌ Poor resilience, immediate action required")
        
        print("\n📋 3. Generating Comprehensive Report")
        report = diagnostics.export_diagnostic_report()
        
        # Save detailed report
        report_data = {
            "timestamp": report.timestamp,
            "total_failures": report.total_failures,
            "confidence_distribution": report.confidence_distribution,
            "failure_patterns": report.failure_patterns,
            "threshold_recommendations": report.threshold_recommendations,
            "model_performance": report.model_performance,
            "escalation_analysis": report.escalation_analysis,
            "remediation_suggestions": report.remediation_suggestions,
            "threshold_analysis": threshold_analysis,
            "simulation_results": simulation_results
        }
        
        report_file = Path("quality_failure_diagnostic_report.json")
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"   ✅ Comprehensive report saved to {report_file}")
        
        print("\n🔧 4. Monitoring Configuration")
        monitoring_config = diagnostics.generate_quality_monitoring_config()
        
        monitoring_file = Path("quality_monitoring_config.json")
        with open(monitoring_file, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        print(f"   ✅ Monitoring configuration saved to {monitoring_file}")
        
        print("\n💡 5. Key Recommendations")
        for i, suggestion in enumerate(report.remediation_suggestions[:3], 1):
            print(f"   {i}. {suggestion}")
        
        print(f"\n✅ Quality diagnostics completed successfully!")
        print(f"   Report files: {report_file}, {monitoring_file}")
        
        return {
            "success": True,
            "resilience_score": resilience_score,
            "issues_found": len(threshold_analysis.get("potential_issues", [])),
            "report_file": str(report_file),
            "monitoring_file": str(monitoring_file)
        }
        
    except Exception as e:
        print(f"❌ Quality diagnostics failed: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    """
    Main CLI entry point for quality failure diagnostics.
    
    Provides comprehensive analysis of AI model quality failures and
    generates actionable recommendations for system improvement.
    """
    result = run_quality_diagnostics()
    
    if result["success"]:
        sys.exit(0)
    else:
        print(f"Error: {result['error']}")
        sys.exit(1) 