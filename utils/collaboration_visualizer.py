#!/usr/bin/env python3
"""
GitBridge Collaboration Visualizer
Task: P20P6B - Enhanced AI Agent Collaboration

Visualization tools for understanding collaboration patterns between AI agents.
Generates insightful diagrams and metrics for the GitBridge collaboration system.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

from utils.collaboration_hub import collaboration_hub, AgentType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [P20P6b] [visualizer] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/visualizer.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def _load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load records from a JSONL file."""
    records = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    records.append(json.loads(line.strip()))
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
    return records

def generate_collaboration_diagram(thread_id: Optional[str] = None) -> str:
    """
    Generate a Mermaid sequence diagram of agent interactions.
    
    Args:
        thread_id: Optional thread ID to visualize
        
    Returns:
        str: Mermaid diagram definition
    """
    # Get interaction history
    history = _load_jsonl(collaboration_hub.interactions_file)
    
    # Filter by thread if specified
    if thread_id:
        history = [i for i in history if i['thread_id'] == thread_id]
        
    if not history:
        return "sequenceDiagram\n    Note over System: No interactions to display"
        
    # Sort by timestamp
    history.sort(key=lambda x: x['timestamp'])
    
    # Build diagram
    diagram = ["sequenceDiagram"]
    
    # Add participants
    participants = set()
    for interaction in history:
        participants.add(interaction['initiator'])
        participants.add(interaction['responder'])
    
    for participant in sorted(participants):
        diagram.append(f"    participant {participant}")
        
    # Add interactions
    for interaction in history:
        initiator = interaction['initiator']
        responder = interaction['responder']
        msg_type = interaction['message_type']
        
        # Format message content (truncate if too long)
        content = interaction['content']
        if len(content) > 50:
            content = content[:47] + "..."
        content = content.replace('"', "'")  # Escape quotes
        
        # Add interaction line
        diagram.append(f'    {initiator}->>+{responder}: "{msg_type}: {content}"')
        
        # Add notes for context if present
        if interaction.get('context'):
            context = interaction['context']
            if len(context) > 50:
                context = context[:47] + "..."
            context = context.replace('"', "'")
            diagram.append(f'    Note over {initiator},{responder}: {context}')
            
    return "\n".join(diagram)

def generate_consensus_diagram() -> str:
    """
    Generate a Mermaid pie chart of consensus metrics.
    
    Returns:
        str: Mermaid diagram definition
    """
    metrics = collaboration_hub.get_consensus_metrics()
    
    if metrics["total_decisions"] == 0:
        return 'pie\n    title No decisions recorded\n    "No Data" : 1'
        
    diagram = ['pie']
    diagram.append('    title Consensus Distribution')
    diagram.append(f'    "Unanimous" : {metrics["unanimous_decisions"]}')
    diagram.append(f'    "Contested" : {metrics["contested_decisions"]}')
    
    return "\n".join(diagram)

def generate_collaboration_network() -> str:
    """
    Generate a Mermaid flowchart of agent collaboration network.
    
    Returns:
        str: Mermaid diagram definition
    """
    interactions = _load_jsonl(collaboration_hub.interactions_file)
    
    if not interactions:
        return "graph TD\n    A[No interactions recorded]"
        
    # Build network
    edges = {}  # (from, to) -> count
    for interaction in interactions:
        edge = (interaction['initiator'], interaction['responder'])
        edges[edge] = edges.get(edge, 0) + 1
        
    # Generate diagram
    diagram = ['graph TD']
    
    # Add nodes
    nodes = set()
    for (src, dst) in edges:
        nodes.add(src)
        nodes.add(dst)
        
    for node in sorted(nodes):
        diagram.append(f'    {node}["{node}"]')
        
    # Add edges with weights
    for (src, dst), weight in edges.items():
        # Line thickness based on interaction count
        style = "normal"
        if weight > 10:
            style = "thick"
        elif weight > 5:
            style = "normal"
        else:
            style = "thin"
            
        diagram.append(f'    {src} -->|"{weight}"| {dst}')
        
    return "\n".join(diagram)

def generate_daily_summary(days: int = 7) -> str:
    """
    Generate a Mermaid gantt chart of daily collaboration activity.
    
    Args:
        days: Number of days to include
        
    Returns:
        str: Mermaid diagram definition
    """
    interactions = _load_jsonl(collaboration_hub.interactions_file)
    
    if not interactions:
        return "gantt\n    title No interactions recorded\n    dateFormat YYYY-MM-DD"
        
    # Group by date
    daily_counts = {}
    cutoff = datetime.now() - timedelta(days=days)
    
    for interaction in interactions:
        date = datetime.fromisoformat(interaction['timestamp']).date()
        if date >= cutoff.date():
            if date not in daily_counts:
                daily_counts[date] = {
                    'total': 0,
                    'by_type': {}
                }
            daily_counts[date]['total'] += 1
            msg_type = interaction['message_type']
            daily_counts[date]['by_type'][msg_type] = daily_counts[date]['by_type'].get(msg_type, 0) + 1
            
    # Generate diagram
    diagram = ['gantt']
    diagram.append('    title Daily Collaboration Activity')
    diagram.append('    dateFormat YYYY-MM-DD')
    diagram.append('    axisFormat %m-%d')
    
    # Add sections by message type
    message_types = set()
    for day_data in daily_counts.values():
        message_types.update(day_data['by_type'].keys())
        
    for msg_type in sorted(message_types):
        diagram.append(f'    section {msg_type}')
        for date, data in sorted(daily_counts.items()):
            count = data['by_type'].get(msg_type, 0)
            if count > 0:
                diagram.append(f'    {msg_type} {count}x: 1d')
                
    return "\n".join(diagram)

def create_summary_report() -> Dict[str, str]:
    """
    Create a complete set of collaboration visualization diagrams.
    
    Returns:
        Dict[str, str]: Dictionary of diagram names and their Mermaid definitions
    """
    return {
        "interaction_sequence": generate_collaboration_diagram(),
        "consensus_distribution": generate_consensus_diagram(),
        "collaboration_network": generate_collaboration_network(),
        "daily_activity": generate_daily_summary()
    } 