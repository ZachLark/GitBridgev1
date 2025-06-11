"""
Task generator implementation for GitBridge.
Handles task creation, thread context management, and vote sequence routing.

MAS Lite Protocol v2.1 References:
- Section 5.1: Task Generation
- Section 5.2: Vote Sequence
- Section 5.3: Agent Routing
"""

import asyncio
import json
import logging.handlers
from typing import Set, Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging
import orjson  # Faster JSON processing
from cachetools import TTLCache  # Cache for vote sequences

@dataclass
class Task:
    """Task data structure."""
    id: str
    type: str
    payload: Dict[str, Any]
    retry_count: int = 0
    agent_target: Optional[str] = None
    votes: Dict[str, int] = None
    created_at: float = 0.0
    updated_at: float = 0.0

class TaskGenerator:
    def __init__(self):
        self.processing: Set[str] = set()
        self.lock = asyncio.Lock()
        
        # Vote sequence storage with TTL cache
        self.vote_sequences = TTLCache(
            maxsize=1000,  # Maximum number of tasks
            ttl=3600  # 1 hour TTL
        )
        
        # Setup trace logging
        self.logger = logging.getLogger("task_generator")
        self.logger.setLevel(logging.INFO)
        
        # JSON file handler with compression
        json_handler = logging.handlers.RotatingFileHandler(
            "logs/task_log.json",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        json_formatter = logging.Formatter(
            '{"task_id": "%(task_id)s", "agent_target": "%(agent_target)s", '
            '"status": "%(status)s", "timestamp": "%(asctime)s", '
            '"latency_ms": "%(latency_ms)s"}'
        )
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)
        
        # Performance metrics
        self.metrics = {
            "vote_processing_ms": [],
            "task_creation_ms": [],
            "edge_case_ms": []
        }
    
    @asynccontextmanager
    async def task_context(self, task_id: str):
        """Context manager for task processing."""
        start_time = datetime.now().timestamp()
        try:
            async with self.lock:
                if task_id in self.processing:
                    self.logger.warning(
                        "Task already processing",
                        extra={
                            "task_id": task_id,
                            "agent_target": "none",
                            "status": "duplicate",
                            "latency_ms": 0
                        }
                    )
                    return
                self.processing.add(task_id)
                self.logger.info(
                    "Task processing started",
                    extra={
                        "task_id": task_id,
                        "agent_target": "none",
                        "status": "started",
                        "latency_ms": 0
                    }
                )
            
            yield
            
        finally:
            end_time = datetime.now().timestamp()
            latency = int((end_time - start_time) * 1000)
            async with self.lock:
                self.processing.remove(task_id)
                self.logger.info(
                    "Task processing completed",
                    extra={
                        "task_id": task_id,
                        "agent_target": "none",
                        "status": "completed",
                        "latency_ms": latency
                    }
                )
    
    async def process_event(self, event_id: str, event_type: str, payload: Dict[str, Any]) -> Task:
        """Process an event into a task with thread safety."""
        start_time = datetime.now().timestamp()
        async with self.task_context(event_id):
            task = Task(
                id=event_id,
                type=event_type,
                payload=payload,
                votes={},
                created_at=start_time,
                updated_at=start_time
            )
            
            try:
                await self._validate_task(task)
                end_time = datetime.now().timestamp()
                latency = int((end_time - start_time) * 1000)
                self.metrics["task_creation_ms"].append(latency)
                
                self.logger.info(
                    "Task created",
                    extra={
                        "task_id": task.id,
                        "agent_target": "none",
                        "status": "created",
                        "latency_ms": latency
                    }
                )
                return task
            except Exception as e:
                end_time = datetime.now().timestamp()
                latency = int((end_time - start_time) * 1000)
                self.metrics["edge_case_ms"].append(latency)
                
                self.logger.error(
                    f"Task validation failed: {str(e)}",
                    extra={
                        "task_id": event_id,
                        "agent_target": "none",
                        "status": "validation_failed",
                        "latency_ms": latency
                    }
                )
                raise
    
    async def _validate_task(self, task: Task):
        """Validate task data."""
        if not task.id:
            raise ValueError("Task ID is required")
        if not task.type:
            raise ValueError("Task type is required")
        if not isinstance(task.payload, dict):
            raise ValueError("Task payload must be a dictionary")
    
    async def submit_vote(self, task_id: str, agent_id: str, vote_value: int) -> Dict[str, Any]:
        """Submit a vote for task routing with optimized processing."""
        start_time = datetime.now().timestamp()
        
        if not 0 <= vote_value <= 10:
            raise ValueError("Vote value must be between 0 and 10")
            
        async with self.lock:
            # Use TTL cache for vote sequences
            if task_id not in self.vote_sequences:
                self.vote_sequences[task_id] = {}
            
            self.vote_sequences[task_id][agent_id] = vote_value
            
            # Calculate consensus early
            votes = self.vote_sequences[task_id]
            consensus_info = self._calculate_consensus(votes)
            
            end_time = datetime.now().timestamp()
            latency = int((end_time - start_time) * 1000)
            self.metrics["vote_processing_ms"].append(latency)
            
            self.logger.info(
                "Vote submitted",
                extra={
                    "task_id": task_id,
                    "agent_target": agent_id,
                    "status": "vote_submitted",
                    "latency_ms": latency
                }
            )
            
            return {
                "task_id": task_id,
                "status": "accepted",
                "current_votes": votes.copy(),
                "consensus": consensus_info
            }
    
    def _calculate_consensus(self, votes: Dict[str, int]) -> Dict[str, Any]:
        """Calculate vote consensus with optimized algorithm."""
        if not votes:
            return {"achieved": False, "reason": "no_votes"}
            
        # Calculate weighted scores
        total_votes = sum(votes.values())
        if total_votes == 0:
            return {"achieved": False, "reason": "zero_weight"}
            
        # Use list comprehension for better performance
        scores = [(agent, vote / total_votes) for agent, vote in votes.items()]
        
        # Sort once and reuse
        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
        top_score = sorted_scores[0][1]
        
        # Quick consensus check
        if top_score > 0.6:  # 60% majority
            return {
                "achieved": True,
                "leader": sorted_scores[0][0],
                "score": top_score
            }
            
        # Check for tie
        tied_agents = [
            agent for agent, score in sorted_scores
            if abs(score - top_score) < 0.001  # Float comparison threshold
        ]
        
        if len(tied_agents) > 1:
            return {
                "achieved": False,
                "reason": "tie",
                "tied_agents": tied_agents
            }
            
        return {
            "achieved": True,
            "leader": sorted_scores[0][0],
            "score": top_score
        }
    
    async def route_task(self, task_id: str, agent_target: str) -> Dict[str, Any]:
        """Route a task with optimized vote sequence resolution."""
        start_time = datetime.now().timestamp()
        
        async with self.lock:
            if task_id not in self.processing:
                end_time = datetime.now().timestamp()
                latency = int((end_time - start_time) * 1000)
                self.metrics["edge_case_ms"].append(latency)
                
                self.logger.error(
                    "Task not found in processing set",
                    extra={
                        "task_id": task_id,
                        "agent_target": agent_target,
                        "status": "error",
                        "latency_ms": latency
                    }
                )
                return {
                    "task_id": task_id,
                    "agent_target": agent_target,
                    "status": "error",
                    "error": "Task not found"
                }
            
            try:
                # Get vote sequence from cache
                votes = self.vote_sequences.get(task_id, {})
                consensus = self._calculate_consensus(votes)
                
                # Determine routing status
                if consensus["achieved"]:
                    selected_agent = consensus["leader"]
                    status = "routed"
                else:
                    selected_agent = agent_target
                    status = "pending"
                
                end_time = datetime.now().timestamp()
                latency = int((end_time - start_time) * 1000)
                
                self.logger.info(
                    f"Task routed to {selected_agent}",
                    extra={
                        "task_id": task_id,
                        "agent_target": selected_agent,
                        "status": status,
                        "latency_ms": latency
                    }
                )
                
                return {
                    "task_id": task_id,
                    "agent_target": selected_agent,
                    "status": status,
                    "vote_sequence": votes,
                    "consensus": consensus,
                    "latency_ms": latency
                }
                
            except Exception as e:
                end_time = datetime.now().timestamp()
                latency = int((end_time - start_time) * 1000)
                self.metrics["edge_case_ms"].append(latency)
                
                self.logger.error(
                    f"Failed to route task: {str(e)}",
                    extra={
                        "task_id": task_id,
                        "agent_target": agent_target,
                        "status": "error",
                        "latency_ms": latency
                    }
                )
                return {
                    "task_id": task_id,
                    "agent_target": agent_target,
                    "status": "error",
                    "error": str(e),
                    "latency_ms": latency
                }
    
    def get_metrics(self) -> Dict[str, float]:
        """Get performance metrics."""
        return {
            "vote_processing_avg_ms": sum(self.metrics["vote_processing_ms"]) / len(self.metrics["vote_processing_ms"]) if self.metrics["vote_processing_ms"] else 0,
            "task_creation_avg_ms": sum(self.metrics["task_creation_ms"]) / len(self.metrics["task_creation_ms"]) if self.metrics["task_creation_ms"] else 0,
            "edge_case_avg_ms": sum(self.metrics["edge_case_ms"]) / len(self.metrics["edge_case_ms"]) if self.metrics["edge_case_ms"] else 0
        }
    
    def is_processing(self, task_id: str) -> bool:
        """Check if a task is currently being processed."""
        return task_id in self.processing
    
    async def cleanup_task(self, task_id: str):
        """Clean up task resources."""
        async with self.lock:
            if task_id in self.processing:
                self.processing.remove(task_id)
                if task_id in self.vote_sequences:
                    del self.vote_sequences[task_id]
                self.logger.info(
                    "Task cleaned up",
                    extra={
                        "task_id": task_id,
                        "agent_target": "none",
                        "status": "cleaned_up",
                        "latency_ms": 0
                    }
                )
    
    async def get_processing_tasks(self) -> Set[str]:
        """Get set of currently processing task IDs."""
        async with self.lock:
            return self.processing.copy() 