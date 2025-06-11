#!/usr/bin/env python3
"""
GitBridge Phase 18P7 - Quality Recovery Handler

This module provides automated recovery mechanisms for AI model quality failures,
including threshold adjustment, context enhancement, and escalation management.

Author: GitBridge MAS Integration Team
Phase: 18P7 - Quality Recovery
MAS Lite Protocol: v2.1 Compliance
"""

import json
import time
import hashlib
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
from queue import Queue, Empty

# Import Redis mock for demonstration (in production, use real Redis)
import sys


@dataclass
class QualityFailureEvent:
    """Represents a quality failure event from Redis stream"""
    event_id: str
    timestamp: str
    prompt_uid: str
    confidence_score: float
    fallback_reason: str
    agent_id: str
    thread_id: str
    audit_id: str
    escalation_level: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAction:
    """Represents a recovery action taken"""
    action_id: str
    timestamp: str
    action_type: str
    target_policy: str
    parameters: Dict[str, Any]
    success: bool
    details: str


class QualityRecoveryHandler:
    """
    Automated quality recovery system for AI model failures.
    
    Monitors Redis streams for quality failures and implements real-time
    recovery strategies including threshold adjustment and context enhancement.
    """
    
    def __init__(self, config_path: str = "ai_routing_config.json"):
        """Initialize quality recovery handler"""
        self.config_path = Path(config_path)
        self.event_queue = Queue()
        self.recovery_history: List[RecoveryAction] = []
        self.active_monitoring = False
        self.recovery_thread = None
        
        # Recovery thresholds (MAS Lite Protocol v2.1)
        self.critical_confidence_threshold = 0.25
        self.recovery_window_minutes = 15
        self.max_threshold_adjustments_per_hour = 3
        self.threshold_adjustment_step = 0.05
        
        # Load current configuration
        self.current_config = self._load_config()
        
        # Recovery strategies
        self.recovery_strategies = {
            "threshold_adjustment": self._adjust_thresholds,
            "context_enhancement": self._enhance_context,
            "model_rotation": self._rotate_models,
            "escalation_acceleration": self._accelerate_escalation
        }
        
        print("🔧 Quality Recovery Handler initialized")
        print(f"   Config loaded: {'✅' if self.current_config else '❌'}")
        print(f"   Recovery strategies: {len(self.recovery_strategies)}")
    
    def _load_config(self) -> Optional[Dict[str, Any]]:
        """Load routing configuration"""
        try:
            if not self.config_path.exists():
                print(f"❌ Configuration file not found: {self.config_path}")
                return None
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            print(f"✅ Configuration loaded: {self.config_path}")
            return config
            
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            return None
    
    def start_monitoring(self) -> None:
        """Start monitoring Redis streams for quality failures"""
        if self.active_monitoring:
            print("⚠️  Monitoring already active")
            return
        
        self.active_monitoring = True
        self.recovery_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.recovery_thread.start()
        
        print("🔍 Quality failure monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring and recovery processes"""
        self.active_monitoring = False
        
        if self.recovery_thread and self.recovery_thread.is_alive():
            self.recovery_thread.join(timeout=5)
        
        print("🛑 Quality failure monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop for quality failures"""
        print("🔄 Monitoring loop started")
        
        while self.active_monitoring:
            try:
                # Simulate Redis stream polling (in production, use real Redis client)
                events = self._poll_redis_stream()
                
                for event in events:
                    self._process_quality_failure_event(event)
                
                # Process recovery queue
                self._process_recovery_queue()
                
                time.sleep(1)  # Poll interval
                
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(5)  # Error recovery delay
    
    def _poll_redis_stream(self) -> List[QualityFailureEvent]:
        """
        Poll Redis stream for quality failure events.
        
        In production, this would connect to actual Redis streams.
        For demonstration, this generates mock events.
        """
        events = []
        
        # Simulate receiving events based on current time
        current_time = datetime.now(timezone.utc)
        
        # Generate mock quality failure event occasionally
        if hash(str(current_time.second)) % 30 == 0:  # Every ~30 seconds
            event = QualityFailureEvent(
                event_id=f"event_{hashlib.md5(str(current_time).encode()).hexdigest()[:8]}",
                timestamp=current_time.isoformat(),
                prompt_uid=f"20250610_{hashlib.md5(str(current_time).encode()).hexdigest()[:6]}_gpt4_001",
                confidence_score=0.25,  # Low confidence triggering failure
                fallback_reason="QUALITY_FAILURE",
                agent_id="gpt4",
                thread_id=f"thread_{hash(str(current_time)) % 1000:03d}",
                audit_id=f"audit_{hashlib.md5(str(current_time).encode()).hexdigest()[:9]}",
                escalation_level=1,
                metadata={
                    "task_type": "code_generation",
                    "original_threshold": 0.75,
                    "attempt_count": 1
                }
            )
            events.append(event)
        
        return events
    
    def _process_quality_failure_event(self, event: QualityFailureEvent) -> None:
        """Process individual quality failure event"""
        print(f"🚨 Quality failure detected: {event.prompt_uid} (confidence: {event.confidence_score:.2f})")
        
        # Add to processing queue
        self.event_queue.put(event)
        
        # Log the event
        self._log_quality_failure(event)
    
    def _process_recovery_queue(self) -> None:
        """Process queued recovery events"""
        try:
            while True:
                event = self.event_queue.get_nowait()
                self._execute_recovery_strategy(event)
                self.event_queue.task_done()
                
        except Empty:
            pass  # Queue is empty, continue monitoring
    
    def _execute_recovery_strategy(self, event: QualityFailureEvent) -> None:
        """Execute appropriate recovery strategy for quality failure"""
        print(f"🔧 Executing recovery for {event.prompt_uid}")
        
        # Determine recovery strategy based on failure characteristics
        strategy = self._select_recovery_strategy(event)
        
        if strategy in self.recovery_strategies:
            recovery_function = self.recovery_strategies[strategy]
            
            try:
                success = recovery_function(event)
                
                # Record recovery action
                action = RecoveryAction(
                    action_id=f"recovery_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    action_type=strategy,
                    target_policy=self._identify_policy_for_event(event),
                    parameters={
                        "confidence_score": event.confidence_score,
                        "escalation_level": event.escalation_level,
                        "agent_id": event.agent_id
                    },
                    success=success,
                    details=f"Recovery {'successful' if success else 'failed'} for {event.prompt_uid}"
                )
                
                self.recovery_history.append(action)
                print(f"✅ Recovery action completed: {strategy} ({'success' if success else 'failed'})")
                
            except Exception as e:
                print(f"❌ Recovery strategy failed: {e}")
    
    def _select_recovery_strategy(self, event: QualityFailureEvent) -> str:
        """Select appropriate recovery strategy based on event characteristics"""
        confidence = event.confidence_score
        escalation_level = event.escalation_level
        
        # Strategy selection logic
        if confidence < 0.20:
            return "escalation_acceleration"
        elif confidence < 0.30:
            return "threshold_adjustment" 
        elif confidence < 0.40:
            return "context_enhancement"
        else:
            return "model_rotation"
    
    def _identify_policy_for_event(self, event: QualityFailureEvent) -> str:
        """Identify which routing policy applies to the event"""
        task_type = event.metadata.get("task_type", "unknown")
        
        # Map task types to policies
        policy_mapping = {
            "code_generation": "edit",
            "code_editing": "edit", 
            "code_review": "review",
            "merge_conflict": "merge"
        }
        
        return policy_mapping.get(task_type, "edit")  # Default to edit policy
    
    def _adjust_thresholds(self, event: QualityFailureEvent) -> bool:
        """Adjust confidence thresholds to reduce quality failures"""
        try:
            if not self.current_config:
                return False
            
            policy_name = self._identify_policy_for_event(event)
            routing_policies = self.current_config.get("routing_policies", {})
            
            if policy_name not in routing_policies:
                return False
            
            policy = routing_policies[policy_name]
            
            # Adjust primary model threshold
            primary_model = policy.get("primary_model", {})
            current_threshold = primary_model.get("confidence_threshold", 0.5)
            
            # Lower threshold by adjustment step
            new_threshold = max(0.35, current_threshold - self.threshold_adjustment_step)
            
            if new_threshold != current_threshold:
                primary_model["confidence_threshold"] = new_threshold
                
                # Save updated configuration
                self._save_config_update()
                
                print(f"🎯 Adjusted threshold for {policy_name}: {current_threshold:.2f} → {new_threshold:.2f}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Threshold adjustment failed: {e}")
            return False
    
    def _enhance_context(self, event: QualityFailureEvent) -> bool:
        """Enhance context provided to models for better output quality"""
        try:
            # Context enhancement strategies
            enhancements = [
                "Add examples of high-quality outputs",
                "Provide more specific instructions",
                "Include relevant domain knowledge",
                "Add quality criteria checklist"
            ]
            
            # In production, this would modify the actual prompt context
            print(f"📝 Context enhanced with: {enhancements[0]}")
            
            # Simulate context enhancement success
            return True
            
        except Exception as e:
            print(f"❌ Context enhancement failed: {e}")
            return False
    
    def _rotate_models(self, event: QualityFailureEvent) -> bool:
        """Rotate to alternative models for better performance"""
        try:
            current_agent = event.agent_id
            
            # Model rotation priority
            rotation_map = {
                "gpt4": "claude3_5_sonnet",
                "claude3_5_sonnet": "gemini_pro", 
                "gemini_pro": "gpt4",
                "gpt3_5_turbo": "gpt4"
            }
            
            alternative_model = rotation_map.get(current_agent, "claude3_5_sonnet")
            
            print(f"🔄 Model rotation: {current_agent} → {alternative_model}")
            
            # In production, this would update the routing preference
            return True
            
        except Exception as e:
            print(f"❌ Model rotation failed: {e}")
            return False
    
    def _accelerate_escalation(self, event: QualityFailureEvent) -> bool:
        """Accelerate human escalation for critical quality failures"""
        try:
            # Immediate escalation for very low confidence
            if event.confidence_score < self.critical_confidence_threshold:
                print(f"🚨 CRITICAL: Immediate human escalation for {event.prompt_uid}")
                
                # In production, this would trigger immediate human notification
                escalation_data = {
                    "event_id": event.event_id,
                    "confidence": event.confidence_score,
                    "agent": event.agent_id,
                    "escalation_reason": "Critical quality failure",
                    "priority": "immediate"
                }
                
                print(f"📞 Human escalation triggered: {escalation_data}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Escalation acceleration failed: {e}")
            return False
    
    def _save_config_update(self) -> bool:
        """Save updated configuration to file"""
        try:
            if not self.current_config:
                return False
            
            # Create backup
            backup_path = self.config_path.with_suffix('.bak')
            if self.config_path.exists():
                self.config_path.rename(backup_path)
            
            # Save updated config
            with open(self.config_path, 'w') as f:
                json.dump(self.current_config, f, indent=2)
            
            print(f"💾 Configuration updated: {self.config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return False
    
    def _log_quality_failure(self, event: QualityFailureEvent) -> None:
        """Log quality failure event for audit purposes"""
        log_entry = {
            "timestamp": event.timestamp,
            "event_type": "QUALITY_FAILURE",
            "event_id": event.event_id,
            "prompt_uid": event.prompt_uid,
            "confidence_score": event.confidence_score,
            "fallback_reason": event.fallback_reason,
            "agent_id": event.agent_id,
            "thread_id": event.thread_id,
            "audit_id": event.audit_id,
            "escalation_level": event.escalation_level,
            "metadata": event.metadata,
            "mas_lite_protocol": "v2.1"
        }
        
        # In production, this would write to structured log files or database
        print(f"📝 Quality failure logged: {event.event_id}")
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get statistics about recovery actions"""
        if not self.recovery_history:
            return {"total_actions": 0, "message": "No recovery actions recorded"}
        
        total_actions = len(self.recovery_history)
        successful_actions = sum(1 for action in self.recovery_history if action.success)
        
        # Group by action type
        action_types = {}
        for action in self.recovery_history:
            action_types[action.action_type] = action_types.get(action.action_type, 0) + 1
        
        return {
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "success_rate": (successful_actions / total_actions) * 100,
            "action_type_distribution": action_types,
            "recent_actions": [
                {
                    "timestamp": action.timestamp,
                    "type": action.action_type,
                    "target": action.target_policy,
                    "success": action.success
                }
                for action in self.recovery_history[-5:]  # Last 5 actions
            ]
        }
    
    def export_recovery_report(self) -> Dict[str, Any]:
        """Export comprehensive recovery report"""
        stats = self.get_recovery_statistics()
        
        report = {
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "monitoring_active": self.active_monitoring,
            "recovery_statistics": stats,
            "configuration_status": {
                "config_loaded": self.current_config is not None,
                "config_path": str(self.config_path),
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "recovery_thresholds": {
                "critical_confidence_threshold": self.critical_confidence_threshold,
                "recovery_window_minutes": self.recovery_window_minutes,
                "max_threshold_adjustments_per_hour": self.max_threshold_adjustments_per_hour,
                "threshold_adjustment_step": self.threshold_adjustment_step
            },
            "available_strategies": list(self.recovery_strategies.keys()),
            "mas_lite_protocol": "v2.1"
        }
        
        return report


def run_quality_recovery_monitor():
    """
    Run quality recovery monitoring system.
    
    Provides real-time monitoring and automated recovery for quality failures.
    """
    print("🚀 GitBridge Quality Recovery Monitor")
    print("=" * 50)
    
    try:
        # Initialize recovery handler
        recovery_handler = QualityRecoveryHandler()
        
        # Start monitoring
        recovery_handler.start_monitoring()
        
        print("\n🔍 Monitoring for quality failures...")
        print("   Press Ctrl+C to stop monitoring")
        
        # Monitor for a demonstration period
        monitor_duration = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < monitor_duration:
            time.sleep(1)
            
            # Show periodic status
            if int(time.time() - start_time) % 10 == 0:
                stats = recovery_handler.get_recovery_statistics()
                print(f"   Status: {stats.get('total_actions', 0)} recovery actions executed")
        
        # Stop monitoring
        recovery_handler.stop_monitoring()
        
        print("\n📊 Recovery Session Summary")
        final_stats = recovery_handler.get_recovery_statistics()
        
        print(f"   Total recovery actions: {final_stats.get('total_actions', 0)}")
        print(f"   Success rate: {final_stats.get('success_rate', 0):.1f}%")
        
        # Export detailed report
        report = recovery_handler.export_recovery_report()
        report_file = Path("quality_recovery_report.json")
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"   📋 Detailed report saved: {report_file}")
        
        return {
            "success": True,
            "actions_executed": final_stats.get('total_actions', 0),
            "success_rate": final_stats.get('success_rate', 0),
            "report_file": str(report_file)
        }
        
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        return {"success": True, "message": "Stopped by user"}
        
    except Exception as e:
        print(f"❌ Quality recovery monitoring failed: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    """
    Main CLI entry point for quality recovery monitoring.
    
    Provides automated recovery mechanisms for AI model quality failures.
    """
    result = run_quality_recovery_monitor()
    
    if result["success"]:
        print(f"\n✅ Quality recovery monitoring completed")
        sys.exit(0)
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1) 