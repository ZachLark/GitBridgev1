#!/usr/bin/env python3
"""
Debug script to understand trust score calculation behavior.
"""

from trust_graph import TrustGraph, TrustEdge
from datetime import datetime, timezone

def debug_trust_calculation():
    """Debug the trust score calculation step by step."""
    
    # Create a fresh trust graph
    graph = TrustGraph(storage_path="debug_temp", auto_save=False)
    
    # Add agents
    graph.add_agent("agent1")
    graph.add_agent("agent2")
    
    print("=== Trust Score Calculation Debug ===")
    
    # Step 1: Initial trust update
    print("\n1. Initial trust update: 0.8")
    success = graph.update_trust("agent1", "agent2", 0.8, 0.9)
    print(f"Success: {success}")
    
    edge = graph.get_edge("agent1", "agent2")
    print(f"Trust score: {edge.trust_score}")
    print(f"Confidence: {edge.confidence}")
    print(f"Interaction count: {edge.interaction_count}")
    
    # Step 2: Negative trust update
    print("\n2. Negative trust update: -0.3")
    success = graph.update_trust("agent1", "agent2", -0.3, 0.7)
    print(f"Success: {success}")
    
    edge = graph.get_edge("agent1", "agent2")
    print(f"Trust score: {edge.trust_score}")
    print(f"Confidence: {edge.confidence}")
    print(f"Interaction count: {edge.interaction_count}")
    
    # Step 3: High trust update (2.0)
    print("\n3. High trust update: 2.0")
    success = graph.update_trust("agent1", "agent2", 2.0, 1.0)
    print(f"Success: {success}")
    
    edge = graph.get_edge("agent1", "agent2")
    print(f"Trust score: {edge.trust_score}")
    print(f"Confidence: {edge.confidence}")
    print(f"Interaction count: {edge.interaction_count}")
    
    # Manual calculation verification
    print("\n=== Manual Calculation Verification ===")
    print("Previous trust score: 0.5")
    print("New trust score: 2.0")
    print("Interaction count before: 2")
    print("Weight = 1.0 / (2 + 1) = 0.333")
    print("New trust = (0.5 * 0.667) + (2.0 * 0.333) = 0.3335 + 0.666 = 0.9995")
    print("After clamping to 1.0: 1.0")
    
    # Let's check what the actual calculation is doing
    print("\n=== Actual Edge State ===")
    edge = graph.get_edge("agent1", "agent2")
    print(f"Final trust score: {edge.trust_score}")
    print(f"Final confidence: {edge.confidence}")
    print(f"Final interaction count: {edge.interaction_count}")

if __name__ == "__main__":
    debug_trust_calculation() 