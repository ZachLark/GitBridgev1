#!/usr/bin/env python3
"""
GitBridge Collaboration Manager
Task: P20P6B - Enhanced AI Agent Collaboration

CLI tool for managing and visualizing AI agent collaboration in GitBridge.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.collaboration_hub import collaboration_hub, AgentType
from utils.collaboration_visualizer import (
    generate_collaboration_diagram,
    generate_consensus_diagram,
    generate_collaboration_network,
    generate_daily_summary,
    create_summary_report
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [P20P6b] [manager] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/collaboration_manager.log'),
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def save_diagram(name: str, content: str, output_dir: str = "collaboration_diagrams"):
    """Save a Mermaid diagram to a file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.mmd"
    path = os.path.join(output_dir, filename)
    
    with open(path, 'w') as f:
        f.write(content)
    logger.info(f"Saved diagram to {path}")
    return path

def export_metrics(output_file: str = "collaboration_metrics.json"):
    """Export collaboration metrics to a JSON file."""
    metrics = collaboration_hub.get_consensus_metrics()
    
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Exported metrics to {output_file}")
    return output_file

def main():
    """CLI entrypoint for collaboration management."""
    parser = argparse.ArgumentParser(
        description="GitBridge Collaboration Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Show interaction diagram:
    %(prog)s visualize interaction
    
  Show consensus metrics:
    %(prog)s metrics
    
  Record an interaction:
    %(prog)s record-interaction cursor grok "code_review" "Reviewing PR #123"
    
  Record a decision:
    %(prog)s record-decision cursor "Approve PR #123" --confidence 0.9
    
  Export all diagrams:
    %(prog)s export-all
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Visualize command
    viz_parser = subparsers.add_parser('visualize', help='Generate visualization diagrams')
    viz_parser.add_argument('type', choices=['interaction', 'consensus', 'network', 'daily'],
                         help='Type of diagram to generate')
    viz_parser.add_argument('--thread', help='Thread ID for interaction diagram')
    viz_parser.add_argument('--days', type=int, default=7,
                         help='Number of days for daily summary')
    viz_parser.add_argument('--save', action='store_true',
                         help='Save diagram to file')
    
    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Show collaboration metrics')
    metrics_parser.add_argument('--export', action='store_true',
                            help='Export metrics to JSON')
    
    # Record interaction command
    interact_parser = subparsers.add_parser('record-interaction',
                                        help='Record an agent interaction')
    interact_parser.add_argument('initiator', help='Initiating agent')
    interact_parser.add_argument('responder', help='Responding agent')
    interact_parser.add_argument('type', help='Type of interaction')
    interact_parser.add_argument('content', help='Interaction content')
    interact_parser.add_argument('--context', help='Interaction context')
    interact_parser.add_argument('--thread', help='Thread ID')
    
    # Record decision command
    decision_parser = subparsers.add_parser('record-decision',
                                        help='Record an agent decision')
    decision_parser.add_argument('agent', help='Agent making the decision')
    decision_parser.add_argument('decision', help='The decision made')
    decision_parser.add_argument('--context', help='Decision context')
    decision_parser.add_argument('--reasoning', help='Decision reasoning')
    decision_parser.add_argument('--confidence', type=float, default=0.8,
                             help='Confidence level (0-1)')
    decision_parser.add_argument('--supporting', nargs='+',
                             help='Supporting agents')
    decision_parser.add_argument('--dissenting', nargs='+',
                             help='Dissenting agents')
    
    # Export all command
    subparsers.add_parser('export-all',
                       help='Export all diagrams and metrics')
    
    args = parser.parse_args()
    
    if args.command == 'visualize':
        # Generate requested diagram
        if args.type == 'interaction':
            diagram = generate_collaboration_diagram(args.thread)
        elif args.type == 'consensus':
            diagram = generate_consensus_diagram()
        elif args.type == 'network':
            diagram = generate_collaboration_network()
        else:  # daily
            diagram = generate_daily_summary(args.days)
            
        if args.save:
            save_diagram(args.type, diagram)
        else:
            print(diagram)
            
    elif args.command == 'metrics':
        metrics = collaboration_hub.get_consensus_metrics()
        if args.export:
            export_metrics()
        else:
            print(json.dumps(metrics, indent=2))
            
    elif args.command == 'record-interaction':
        thread_id = collaboration_hub.record_interaction(
            initiator=args.initiator,
            responder=args.responder,
            message_type=args.type,
            content=args.content,
            context=args.context or "",
            thread_id=args.thread
        )
        print(f"Recorded interaction in thread: {thread_id}")
        
    elif args.command == 'record-decision':
        collaboration_hub.record_decision(
            agent=args.agent,
            context=args.context or "",
            decision=args.decision,
            reasoning=args.reasoning or "",
            confidence=args.confidence,
            supporting_agents=args.supporting,
            dissenting_agents=args.dissenting
        )
        print("Recorded decision")
        
    elif args.command == 'export-all':
        # Create output directory
        output_dir = "collaboration_export"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # Export diagrams
        diagrams = create_summary_report()
        for name, content in diagrams.items():
            save_diagram(name, content, output_dir)
            
        # Export metrics
        metrics_file = os.path.join(output_dir, f"metrics_{timestamp}.json")
        export_metrics(metrics_file)
        
        print(f"Exported all artifacts to {output_dir}")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 