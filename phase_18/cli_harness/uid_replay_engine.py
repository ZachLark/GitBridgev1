# P18P8S3 – UID Replay Chain Support Module

"""
GitBridge Phase 18P8 - UID Replay Engine

This module implements comprehensive UID handoff chain replay functionality
with detailed transcript generation and lineage analysis.

Author: GitBridge MAS Integration Team
Phase: 18P8 - CLI Test Harness
MAS Lite Protocol: v2.1 Compliance
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ReplayNode:
    """Individual node in UID handoff chain"""
    node_id: str
    uid: str
    agent: str
    timestamp: str
    confidence_score: float
    fallback_flag: bool
    model_id: Optional[str] = None
    error_code: Optional[str] = None
    escalation_reason: Optional[str] = None
    processing_time_ms: Optional[int] = None
    parent_uid: Optional[str] = None
    children_uids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "node_id": self.node_id,
            "uid": self.uid,
            "agent": self.agent,
            "timestamp": self.timestamp,
            "confidence_score": self.confidence_score,
            "fallback_flag": self.fallback_flag,
            "model_id": self.model_id,
            "error_code": self.error_code,
            "escalation_reason": self.escalation_reason,
            "processing_time_ms": self.processing_time_ms,
            "parent_uid": self.parent_uid,
            "children_uids": self.children_uids,
            "mas_lite_protocol": "v2.1"
        }


@dataclass
class ReplayTranscript:
    """Complete replay session transcript"""
    replay_session_id: str
    input_file: str
    total_nodes: int
    successful_replays: int
    failed_replays: int
    start_time: str
    end_time: str
    execution_time_ms: int
    nodes: List[ReplayNode] = field(default_factory=list)
    lineage_analysis: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "replay_session_id": self.replay_session_id,
            "input_file": self.input_file,
            "total_nodes": self.total_nodes,
            "successful_replays": self.successful_replays,
            "failed_replays": self.failed_replays,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time_ms": self.execution_time_ms,
            "nodes": [node.to_dict() for node in self.nodes],
            "lineage_analysis": self.lineage_analysis,
            "errors": self.errors,
            "mas_lite_protocol": "v2.1"
        }


class UIDReplayEngine:
    """Advanced UID handoff chain replay engine"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.transcript = None
        
        print(f"🎬 UIDReplayEngine initialized for session: {session_id}")
    
    def load_uid_chain(self, input_file: str, logger: Any) -> Optional[List[Dict[str, Any]]]:
        """Load UID handoff chain from JSON file"""
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                logger.error(f"Input file not found: {input_file}")
                return None
            
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            # Handle different input formats
            if isinstance(data, list):
                # Direct list of UID nodes
                uid_chain = data
            elif isinstance(data, dict):
                # Check for common data structures
                if 'detailed_scenarios' in data:
                    # Fallback simulation audit format
                    uid_chain = data['detailed_scenarios']
                elif 'scenarios' in data:
                    # Simple scenarios format  
                    uid_chain = data['scenarios']
                elif 'uid_chain' in data:
                    # Dedicated UID chain format
                    uid_chain = data['uid_chain']
                else:
                    # Assume the dict itself is a single node
                    uid_chain = [data]
            else:
                logger.error(f"Unsupported input format in {input_file}")
                return None
            
            logger.success(f"Loaded {len(uid_chain)} nodes from {input_file}")
            return uid_chain
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {input_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load {input_file}: {e}")
            return None
    
    def convert_to_replay_nodes(self, raw_data: List[Dict[str, Any]], 
                               logger: Any) -> List[ReplayNode]:
        """Convert raw data to ReplayNode objects"""
        nodes = []
        
        for i, raw_node in enumerate(raw_data):
            try:
                # Extract required fields with fallbacks
                node_id = raw_node.get('scenario_id', raw_node.get('node_id', f"node_{i+1}"))
                uid = raw_node.get('uid', raw_node.get('id', f"uid_{i+1}"))
                
                # Determine agent from various fields
                agent = (raw_node.get('agent') or 
                        raw_node.get('model_id') or 
                        raw_node.get('model') or 
                        "unknown_agent")
                
                timestamp = raw_node.get('timestamp', datetime.now(timezone.utc).isoformat())
                confidence_score = float(raw_node.get('confidence_score', 0.0))
                
                # Determine fallback flag
                fallback_flag = (
                    raw_node.get('fallback_flag', False) or
                    raw_node.get('fallback_type') is not None or
                    raw_node.get('error_code') is not None
                )
                
                # Optional fields
                model_id = raw_node.get('model_id')
                error_code = raw_node.get('error_code')
                escalation_reason = raw_node.get('escalation_trigger') or raw_node.get('reason')
                processing_time_ms = raw_node.get('duration_ms') or raw_node.get('processing_time_ms')
                parent_uid = raw_node.get('parent_uid')
                children_uids = raw_node.get('children_uids', [])
                
                node = ReplayNode(
                    node_id=node_id,
                    uid=uid,
                    agent=agent,
                    timestamp=timestamp,
                    confidence_score=confidence_score,
                    fallback_flag=fallback_flag,
                    model_id=model_id,
                    error_code=error_code,
                    escalation_reason=escalation_reason,
                    processing_time_ms=processing_time_ms,
                    parent_uid=parent_uid,
                    children_uids=children_uids
                )
                
                nodes.append(node)
                
            except Exception as e:
                logger.error(f"Failed to convert node {i+1}: {e}")
                continue
        
        logger.info(f"Converted {len(nodes)} nodes for replay")
        return nodes
    
    def analyze_lineage(self, nodes: List[ReplayNode]) -> Dict[str, Any]:
        """Analyze UID handoff lineage patterns"""
        analysis = {
            "total_nodes": len(nodes),
            "unique_agents": len(set(node.agent for node in nodes)),
            "fallback_count": sum(1 for node in nodes if node.fallback_flag),
            "confidence_statistics": {},
            "temporal_analysis": {},
            "agent_distribution": {},
            "error_patterns": {},
            "escalation_triggers": {}
        }
        
        if not nodes:
            return analysis
        
        # Confidence statistics
        confidence_scores = [node.confidence_score for node in nodes]
        analysis["confidence_statistics"] = {
            "average": sum(confidence_scores) / len(confidence_scores),
            "minimum": min(confidence_scores),
            "maximum": max(confidence_scores),
            "below_threshold_count": sum(1 for score in confidence_scores if score < 0.5)
        }
        
        # Temporal analysis
        timestamps = [datetime.fromisoformat(node.timestamp.replace('Z', '+00:00')) for node in nodes]
        if timestamps:
            analysis["temporal_analysis"] = {
                "first_event": min(timestamps).isoformat(),
                "last_event": max(timestamps).isoformat(),
                "time_span_seconds": (max(timestamps) - min(timestamps)).total_seconds()
            }
        
        # Agent distribution
        agent_counts = {}
        for node in nodes:
            agent_counts[node.agent] = agent_counts.get(node.agent, 0) + 1
        analysis["agent_distribution"] = agent_counts
        
        # Error patterns
        error_counts = {}
        for node in nodes:
            if node.error_code:
                error_counts[node.error_code] = error_counts.get(node.error_code, 0) + 1
        analysis["error_patterns"] = error_counts
        
        # Escalation triggers
        escalation_counts = {}
        for node in nodes:
            if node.escalation_reason:
                escalation_counts[node.escalation_reason] = escalation_counts.get(node.escalation_reason, 0) + 1
        analysis["escalation_triggers"] = escalation_counts
        
        # Processing time statistics
        processing_times = [node.processing_time_ms for node in nodes if node.processing_time_ms]
        if processing_times:
            analysis["processing_time_statistics"] = {
                "average_ms": sum(processing_times) / len(processing_times),
                "minimum_ms": min(processing_times),
                "maximum_ms": max(processing_times),
                "total_ms": sum(processing_times)
            }
        
        return analysis
    
    def replay_uid_chain(self, input_file: str, logger: Any) -> Optional[ReplayTranscript]:
        """Replay complete UID handoff chain"""
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting UID chain replay from: {input_file}")
        
        # Load UID chain data
        raw_data = self.load_uid_chain(input_file, logger)
        if not raw_data:
            return None
        
        # Convert to replay nodes
        nodes = self.convert_to_replay_nodes(raw_data, logger)
        if not nodes:
            logger.error("No valid nodes found for replay")
            return None
        
        successful_replays = 0
        failed_replays = 0
        errors = []
        
        # Replay each node
        for i, node in enumerate(nodes):
            try:
                logger.info(f"Replaying node {i+1}/{len(nodes)}: {node.uid}")
                
                # Simulate replay processing
                time.sleep(0.1)  # Brief delay to simulate processing
                
                # Log node details
                logger.success(f"✅ Node replayed successfully")
                logger.info(f"   Timestamp: {node.timestamp}")
                logger.info(f"   Agent: {node.agent}")
                logger.info(f"   Confidence: {node.confidence_score:.3f}")
                logger.info(f"   Fallback: {'Yes' if node.fallback_flag else 'No'}")
                
                if node.model_id:
                    logger.info(f"   Model: {node.model_id}")
                if node.error_code:
                    logger.warning(f"   Error Code: {node.error_code}")
                if node.escalation_reason:
                    logger.warning(f"   Escalation: {node.escalation_reason}")
                if node.processing_time_ms:
                    logger.info(f"   Processing Time: {node.processing_time_ms}ms")
                
                successful_replays += 1
                
            except Exception as e:
                failed_replays += 1
                error_msg = f"Failed to replay node {node.uid}: {e}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # Generate lineage analysis
        lineage_analysis = self.analyze_lineage(nodes)
        
        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Create transcript
        transcript = ReplayTranscript(
            replay_session_id=self.session_id,
            input_file=input_file,
            total_nodes=len(nodes),
            successful_replays=successful_replays,
            failed_replays=failed_replays,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            execution_time_ms=execution_time_ms,
            nodes=nodes,
            lineage_analysis=lineage_analysis,
            errors=errors
        )
        
        self.transcript = transcript
        
        # Log summary
        logger.success(f"Replay completed in {execution_time_ms}ms")
        logger.info(f"Successful replays: {successful_replays}")
        logger.info(f"Failed replays: {failed_replays}")
        logger.info(f"Success rate: {(successful_replays/len(nodes))*100:.1f}%")
        
        return transcript
    
    def save_replay_transcript(self, output_file: str, logger: Any) -> bool:
        """Save replay transcript to JSON file"""
        if not self.transcript:
            logger.error("No replay transcript to save")
            return False
        
        try:
            transcript_data = {
                "transcript_metadata": {
                    "report_type": "uid_replay_transcript",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "session_id": self.session_id,
                    "mas_lite_protocol": "v2.1"
                },
                "replay_summary": {
                    "input_file": self.transcript.input_file,
                    "total_nodes": self.transcript.total_nodes,
                    "successful_replays": self.transcript.successful_replays,
                    "failed_replays": self.transcript.failed_replays,
                    "success_rate": (self.transcript.successful_replays / self.transcript.total_nodes) * 100 if self.transcript.total_nodes > 0 else 0,
                    "execution_time_ms": self.transcript.execution_time_ms,
                    "start_time": self.transcript.start_time,
                    "end_time": self.transcript.end_time
                },
                "lineage_analysis": self.transcript.lineage_analysis,
                "detailed_nodes": [node.to_dict() for node in self.transcript.nodes],
                "errors": self.transcript.errors
            }
            
            with open(output_file, 'w') as f:
                json.dump(transcript_data, f, indent=2, default=str)
            
            logger.success(f"Replay transcript saved to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save replay transcript: {e}")
            return False


def create_sample_uid_chain(count: int = 5) -> List[Dict[str, Any]]:
    """Create sample UID chain data for testing"""
    import random
    import hashlib
    
    sample_chain = []
    parent_uid = None
    
    agents = ["gpt4_turbo", "claude3_5_sonnet", "gemini_pro", "human_escalation"]
    error_codes = ["TIMEOUT", "MODEL_FAILURE", "ESCALATION_TRIGGER", None, None]  # More successes
    
    for i in range(count):
        timestamp = datetime.now(timezone.utc).isoformat()
        uid = hashlib.sha256(f"uid_{i}_{timestamp}".encode()).hexdigest()[:16]
        
        node = {
            "node_id": f"node_{i+1}",
            "uid": uid,
            "agent": random.choice(agents),
            "timestamp": timestamp,
            "confidence_score": random.uniform(0.1, 0.9),
            "fallback_flag": random.choice([True, False]),
            "model_id": random.choice(agents[:-1]),  # Exclude human_escalation
            "error_code": random.choice(error_codes),
            "escalation_reason": random.choice([None, "low_confidence", "complex_request", "user_request"]),
            "processing_time_ms": random.randint(500, 5000),
            "parent_uid": parent_uid,
            "children_uids": []
        }
        
        # Link to parent
        if parent_uid and sample_chain:
            # Add this UID as child of previous node
            sample_chain[-1]["children_uids"].append(uid)
        
        sample_chain.append(node)
        parent_uid = uid
    
    return sample_chain


if __name__ == "__main__":
    """Test the UID replay engine"""
    print("🧪 Testing UID Replay Engine")
    
    # Create sample UID chain
    sample_chain = create_sample_uid_chain(5)
    
    print(f"Created sample UID chain with {len(sample_chain)} nodes:")
    for i, node in enumerate(sample_chain, 1):
        print(f"  {i}. {node['agent']} - {node['uid']} - Confidence: {node['confidence_score']:.3f}")
    
    # Save sample data
    with open("sample_uid_chain.json", "w") as f:
        json.dump({"uid_chain": sample_chain}, f, indent=2)
    
    print("✅ Sample UID chain saved to sample_uid_chain.json") 