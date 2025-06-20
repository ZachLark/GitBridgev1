#!/usr/bin/env python3
"""
Phase: GBP20
Part: P20P8
Step: P20P8S6
Task: P20P8S6T1 - Evaluation Tools & Testing

CLI tool to evaluate agent performance, visualize comparison, and test edge cases.
"""
import argparse
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluation.meta_evaluator import MetaEvaluator
import matplotlib.pyplot as plt

def plot_comparison_graph(comparisons):
    providers = ['openai', 'grok']
    scores = {p: [] for p in providers}
    latencies = {p: [] for p in providers}
    for c in comparisons:
        for p in providers:
            eval = c[f'{p}_evaluation']
            scores[p].append(eval['overall_score'])
            latencies[p].append(eval['response_time'])
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.title('Agent Score Comparison')
    plt.plot(scores['openai'], label='OpenAI', marker='o')
    plt.plot(scores['grok'], label='Grok', marker='o')
    plt.xlabel('Test #')
    plt.ylabel('Overall Score')
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.title('Agent Latency Comparison')
    plt.plot(latencies['openai'], label='OpenAI', marker='o')
    plt.plot(latencies['grok'], label='Grok', marker='o')
    plt.xlabel('Test #')
    plt.ylabel('Latency (s)')
    plt.legend()
    plt.tight_layout()
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Evaluate and compare AI agents.')
    parser.add_argument('--summary', action='store_true', help='Show evaluation summary')
    parser.add_argument('--plot', action='store_true', help='Show comparison graph')
    parser.add_argument('--edge', action='store_true', help='Test edge cases')
    args = parser.parse_args()
    evaluator = MetaEvaluator()
    summary = evaluator.get_evaluation_summary(limit=20)
    if args.summary:
        print(json.dumps(summary, indent=2))
    if args.plot:
        plot_comparison_graph(summary['recent_comparisons'])
    if args.edge:
        # Edge case: high token count
        prompt = ' '.join(['token'] * 2000)
        print('Testing high token count...')
        try:
            comparison = evaluator.compare_responses(prompt, 'general', max_tokens=2048)
            print('High token count test:', comparison.winner, comparison.confidence)
        except Exception as e:
            print('High token count test failed:', e)
        # Edge case: retries/partial failures
        prompt = 'Trigger a failure scenario.'
        print('Testing partial failure...')
        try:
            comparison = evaluator.compare_responses(prompt, 'general')
            print('Partial failure test:', comparison.winner, comparison.confidence)
        except Exception as e:
            print('Partial failure test failed:', e)
if __name__ == '__main__':
    main() 