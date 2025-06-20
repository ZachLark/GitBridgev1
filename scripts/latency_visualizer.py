#!/usr/bin/env python3
"""
GitBridge Real-Time Latency Visualizer
Task: P20P7S5A - Performance Optimization

Real-time latency visualization tool for SmartRouter performance monitoring.
Displays live latency trends, provider performance, and routing decisions.

Author: GitBridge Development Team
Date: 2025-06-19
"""

import os
import sys
import time
import json
import argparse
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_router.smart_router import SmartRouter, RoutingStrategy, ProviderType


class LatencyVisualizer:
    """
    Real-time latency visualizer for SmartRouter performance monitoring.
    
    Features:
    - Live latency trend graphs
    - Provider performance comparison
    - Routing decision visualization
    - Performance window analysis
    - Adaptive score tracking
    """
    
    def __init__(self, router: SmartRouter, update_interval: float = 2.0):
        """
        Initialize the latency visualizer.
        
        Args:
            router: SmartRouter instance to monitor
            update_interval: Update interval in seconds
        """
        self.router = router
        self.update_interval = update_interval
        self.running = False
        
        # Data storage
        self.latency_data = {provider.value: [] for provider in router.providers.keys()}
        self.timestamps = []
        self.routing_decisions = []
        self.adaptive_scores = {provider.value: [] for provider in router.providers.keys()}
        
        # Performance windows data
        self.performance_windows = {provider.value: [] for provider in router.providers.keys()}
        
        # Setup matplotlib
        plt.style.use('dark_background')
        self.fig, self.axes = plt.subplots(2, 2, figsize=(15, 10))
        self.fig.suptitle('GitBridge SmartRouter - Real-Time Performance Monitor', 
                         fontsize=16, fontweight='bold')
        
        # Initialize plots
        self._setup_plots()
        
    def _setup_plots(self):
        """Setup the visualization plots."""
        # Latency trends
        self.ax1 = self.axes[0, 0]
        self.ax1.set_title('Real-Time Latency Trends', fontweight='bold')
        self.ax1.set_xlabel('Time')
        self.ax1.set_ylabel('Latency (seconds)')
        self.ax1.grid(True, alpha=0.3)
        
        # Provider performance comparison
        self.ax2 = self.axes[0, 1]
        self.ax2.set_title('Provider Performance Comparison', fontweight='bold')
        self.ax2.set_ylabel('Score')
        self.ax2.grid(True, alpha=0.3)
        
        # Adaptive scores
        self.ax3 = self.axes[1, 0]
        self.ax3.set_title('Adaptive Scores Over Time', fontweight='bold')
        self.ax3.set_xlabel('Time')
        self.ax3.set_ylabel('Adaptive Score')
        self.ax3.grid(True, alpha=0.3)
        
        # Routing decisions
        self.ax4 = self.axes[1, 1]
        self.ax4.set_title('Recent Routing Decisions', fontweight='bold')
        self.ax4.set_xlabel('Time')
        self.ax4.set_ylabel('Provider')
        self.ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
    def start_monitoring(self):
        """Start real-time monitoring."""
        self.running = True
        
        # Start data collection thread
        self.data_thread = threading.Thread(target=self._collect_data)
        self.data_thread.daemon = True
        self.data_thread.start()
        
        # Start animation
        self.ani = animation.FuncAnimation(
            self.fig, self._update_plots, interval=self.update_interval * 1000,
            blit=False, cache_frame_data=False
        )
        
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] "
              f"Starting real-time latency monitoring...")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            plt.show()
        except KeyboardInterrupt:
            self.stop_monitoring()
            
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.running = False
        print(f"\n[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] "
              f"Stopping latency monitoring...")
        
    def _collect_data(self):
        """Collect data in background thread."""
        while self.running:
            try:
                # Get current metrics
                metrics = self.router.get_enhanced_metrics()
                current_time = datetime.now(timezone.utc)
                
                # Update latency data
                for provider_name, provider_data in metrics['providers'].items():
                    if provider_name in self.latency_data:
                        self.latency_data[provider_name].append(provider_data['avg_latency'])
                        self.adaptive_scores[provider_name].append(provider_data['adaptive_score'])
                        
                        # Keep only last 100 data points
                        if len(self.latency_data[provider_name]) > 100:
                            self.latency_data[provider_name] = self.latency_data[provider_name][-100:]
                        if len(self.adaptive_scores[provider_name]) > 100:
                            self.adaptive_scores[provider_name] = self.adaptive_scores[provider_name][-100:]
                
                # Update timestamps
                self.timestamps.append(current_time)
                if len(self.timestamps) > 100:
                    self.timestamps = self.timestamps[-100:]
                
                # Get recent routing decisions
                recent_decisions = self.router.get_routing_history(limit=20)
                self.routing_decisions = recent_decisions
                
                # Get performance windows data
                for provider_type, provider_metrics in self.router.get_provider_metrics().items():
                    provider_name = provider_type.value
                    if provider_name in self.performance_windows:
                        windows_data = []
                        for window in provider_metrics.performance_windows:
                            windows_data.append({
                                'avg_latency': window.avg_latency,
                                'success_rate': window.success_rate,
                                'retry_effectiveness': window.retry_effectiveness,
                                'timestamp': window.end_time
                            })
                        self.performance_windows[provider_name] = windows_data
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Error collecting data: {str(e)}")
                time.sleep(self.update_interval)
                
    def _update_plots(self, frame):
        """Update all plots with current data."""
        try:
            # Clear all axes
            for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
                ax.clear()
            
            # Update latency trends
            self._plot_latency_trends()
            
            # Update provider performance comparison
            self._plot_performance_comparison()
            
            # Update adaptive scores
            self._plot_adaptive_scores()
            
            # Update routing decisions
            self._plot_routing_decisions()
            
            # Redraw
            self.fig.canvas.draw()
            
        except Exception as e:
            print(f"Error updating plots: {str(e)}")
            
    def _plot_latency_trends(self):
        """Plot real-time latency trends."""
        self.ax1.set_title('Real-Time Latency Trends', fontweight='bold')
        self.ax1.set_xlabel('Time')
        self.ax1.set_ylabel('Latency (seconds)')
        self.ax1.grid(True, alpha=0.3)
        
        if not self.timestamps:
            return
            
        # Plot latency for each provider
        colors = ['#00ff00', '#ff6b6b', '#4ecdc4', '#45b7d1']
        for i, (provider_name, latencies) in enumerate(self.latency_data.items()):
            if latencies and len(latencies) == len(self.timestamps):
                color = colors[i % len(colors)]
                self.ax1.plot(self.timestamps, latencies, 
                            label=provider_name.upper(), 
                            color=color, linewidth=2, marker='o', markersize=4)
        
        self.ax1.legend()
        self.ax1.set_ylim(bottom=0)
        
        # Format x-axis
        if len(self.timestamps) > 1:
            time_diff = (self.timestamps[-1] - self.timestamps[0]).total_seconds()
            if time_diff > 300:  # More than 5 minutes
                self.ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
            else:
                self.ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%M:%S'))
        
    def _plot_performance_comparison(self):
        """Plot provider performance comparison."""
        self.ax2.set_title('Provider Performance Comparison', fontweight='bold')
        self.ax2.set_ylabel('Score')
        self.ax2.grid(True, alpha=0.3)
        
        # Get current metrics
        metrics = self.router.get_enhanced_metrics()
        
        providers = []
        success_rates = []
        availability_scores = []
        adaptive_scores = []
        
        for provider_name, provider_data in metrics['providers'].items():
            providers.append(provider_name.upper())
            success_rates.append(provider_data['success_rate'])
            availability_scores.append(provider_data['availability_score'])
            adaptive_scores.append(provider_data['adaptive_score'])
        
        if providers:
            x = np.arange(len(providers))
            width = 0.25
            
            self.ax2.bar(x - width, success_rates, width, label='Success Rate', 
                        color='#00ff00', alpha=0.8)
            self.ax2.bar(x, availability_scores, width, label='Availability', 
                        color='#ff6b6b', alpha=0.8)
            self.ax2.bar(x + width, adaptive_scores, width, label='Adaptive Score', 
                        color='#4ecdc4', alpha=0.8)
            
            self.ax2.set_xticks(x)
            self.ax2.set_xticklabels(providers)
            self.ax2.legend()
            self.ax2.set_ylim(0, 1.1)
            
    def _plot_adaptive_scores(self):
        """Plot adaptive scores over time."""
        self.ax3.set_title('Adaptive Scores Over Time', fontweight='bold')
        self.ax3.set_xlabel('Time')
        self.ax3.set_ylabel('Adaptive Score')
        self.ax3.grid(True, alpha=0.3)
        
        if not self.timestamps:
            return
            
        colors = ['#00ff00', '#ff6b6b', '#4ecdc4', '#45b7d1']
        for i, (provider_name, scores) in enumerate(self.adaptive_scores.items()):
            if scores and len(scores) == len(self.timestamps):
                color = colors[i % len(colors)]
                self.ax3.plot(self.timestamps, scores, 
                            label=provider_name.upper(), 
                            color=color, linewidth=2, marker='s', markersize=4)
        
        self.ax3.legend()
        self.ax3.set_ylim(0, 1.1)
        
        # Format x-axis
        if len(self.timestamps) > 1:
            time_diff = (self.timestamps[-1] - self.timestamps[0]).total_seconds()
            if time_diff > 300:  # More than 5 minutes
                self.ax3.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
            else:
                self.ax3.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%M:%S'))
        
    def _plot_routing_decisions(self):
        """Plot recent routing decisions."""
        self.ax4.set_title('Recent Routing Decisions', fontweight='bold')
        self.ax4.set_xlabel('Time')
        self.ax4.set_ylabel('Provider')
        self.ax4.grid(True, alpha=0.3)
        
        if not self.routing_decisions:
            return
            
        # Extract decision data
        decision_times = []
        decision_providers = []
        decision_confidences = []
        
        for decision in self.routing_decisions[-20:]:  # Last 20 decisions
            try:
                timestamp = datetime.fromisoformat(decision['timestamp'].replace('Z', '+00:00'))
                provider = decision['selected_provider']
                confidence = decision.get('confidence', 0.5)
                
                decision_times.append(timestamp)
                decision_providers.append(provider)
                decision_confidences.append(confidence)
            except Exception as e:
                continue
        
        if decision_times:
            # Create scatter plot
            colors = {'openai': '#00ff00', 'grok': '#ff6b6b'}
            sizes = [conf * 200 + 50 for conf in decision_confidences]  # Size based on confidence
            
            for provider in set(decision_providers):
                mask = [p == provider for p in decision_providers]
                provider_times = [decision_times[i] for i in range(len(decision_times)) if mask[i]]
                provider_sizes = [sizes[i] for i in range(len(sizes)) if mask[i]]
                
                color = colors.get(provider, '#4ecdc4')
                self.ax4.scatter(provider_times, [provider.upper()] * len(provider_times),
                               s=provider_sizes, c=color, alpha=0.7, label=provider.upper())
            
            self.ax4.legend()
            
            # Format x-axis
            if len(decision_times) > 1:
                time_diff = (decision_times[-1] - decision_times[0]).total_seconds()
                if time_diff > 300:  # More than 5 minutes
                    self.ax4.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
                else:
                    self.ax4.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%M:%S'))
        
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        metrics = self.router.get_enhanced_metrics()
        analytics = self.router.get_routing_analytics()
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'monitoring_duration': self._get_monitoring_duration(),
            'overall_performance': metrics['overall_performance'],
            'provider_performance': {},
            'routing_analytics': analytics,
            'performance_windows': self.performance_windows,
            'recommendations': self._generate_recommendations(metrics, analytics)
        }
        
        # Add provider-specific performance
        for provider_name, provider_data in metrics['providers'].items():
            report['provider_performance'][provider_name] = {
                'avg_latency': provider_data['avg_latency'],
                'success_rate': provider_data['success_rate'],
                'availability_score': provider_data['availability_score'],
                'adaptive_score': provider_data['adaptive_score'],
                'retry_effectiveness': provider_data['retry_effectiveness'],
                'total_requests': provider_data['total_requests'],
                'performance_windows_count': provider_data['performance_windows_count']
            }
        
        return report
        
    def _get_monitoring_duration(self) -> str:
        """Get the duration of monitoring."""
        if not self.timestamps:
            return "0 seconds"
        
        duration = self.timestamps[-1] - self.timestamps[0]
        total_seconds = duration.total_seconds()
        
        if total_seconds < 60:
            return f"{total_seconds:.1f} seconds"
        elif total_seconds < 3600:
            minutes = total_seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = total_seconds / 3600
            return f"{hours:.1f} hours"
        
    def _generate_recommendations(self, metrics: Dict, analytics: Dict) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Check overall performance
        overall = metrics['overall_performance']
        if overall['avg_success_rate'] < 0.95:
            recommendations.append("Consider investigating provider failures - success rate below 95%")
        
        if overall['avg_latency'] > 5.0:
            recommendations.append("High average latency detected - consider performance optimization")
        
        # Check individual providers
        for provider_name, provider_data in metrics['providers'].items():
            if provider_data['success_rate'] < 0.9:
                recommendations.append(f"{provider_name.upper()} has low success rate - check health status")
            
            if provider_data['avg_latency'] > 10.0:
                recommendations.append(f"{provider_name.upper()} has high latency - consider failover")
        
        # Check routing strategy
        if analytics.get('strategy_distribution', {}).get('adaptive', 0) == 0:
            recommendations.append("Consider using adaptive routing strategy for better performance")
        
        if not recommendations:
            recommendations.append("All systems performing well - no immediate action required")
        
        return recommendations


def main():
    """Main function for the latency visualizer."""
    parser = argparse.ArgumentParser(description='GitBridge Real-Time Latency Visualizer')
    parser.add_argument('--strategy', default='adaptive', 
                       choices=['cost_optimized', 'performance_optimized', 'availability_optimized', 'hybrid', 'adaptive'],
                       help='Routing strategy to use')
    parser.add_argument('--update-interval', type=float, default=2.0,
                       help='Update interval in seconds')
    parser.add_argument('--report-only', action='store_true',
                       help='Generate performance report without visualization')
    
    args = parser.parse_args()
    
    try:
        # Initialize SmartRouter
        strategy = RoutingStrategy(args.strategy)
        router = SmartRouter(strategy=strategy)
        
        if args.report_only:
            # Generate report only
            visualizer = LatencyVisualizer(router, args.update_interval)
            
            # Collect some data
            print("Collecting performance data...")
            for _ in range(10):
                time.sleep(args.update_interval)
            
            # Generate report
            report = visualizer.generate_performance_report()
            print("\n" + "="*60)
            print("GITBRIDGE SMARTROUTER PERFORMANCE REPORT")
            print("="*60)
            print(f"Generated: {report['timestamp']}")
            print(f"Monitoring Duration: {report['monitoring_duration']}")
            print(f"Routing Strategy: {strategy.value}")
            
            print("\nOVERALL PERFORMANCE:")
            overall = report['overall_performance']
            print(f"  Total Requests: {overall['total_requests']}")
            print(f"  Total Failures: {overall['total_failures']}")
            print(f"  Average Latency: {overall['avg_latency']:.2f}s")
            print(f"  Average Success Rate: {overall['avg_success_rate']:.2%}")
            print(f"  Average Retry Effectiveness: {overall['avg_retry_effectiveness']:.2%}")
            
            print("\nPROVIDER PERFORMANCE:")
            for provider_name, provider_data in report['provider_performance'].items():
                print(f"  {provider_name.upper()}:")
                print(f"    Average Latency: {provider_data['avg_latency']:.2f}s")
                print(f"    Success Rate: {provider_data['success_rate']:.2%}")
                print(f"    Availability Score: {provider_data['availability_score']:.2f}")
                print(f"    Adaptive Score: {provider_data['adaptive_score']:.2f}")
                print(f"    Retry Effectiveness: {provider_data['retry_effectiveness']:.2%}")
                print(f"    Total Requests: {provider_data['total_requests']}")
            
            print("\nRECOMMENDATIONS:")
            for i, recommendation in enumerate(report['recommendations'], 1):
                print(f"  {i}. {recommendation}")
            
            print("\n" + "="*60)
            
        else:
            # Start real-time visualization
            visualizer = LatencyVisualizer(router, args.update_interval)
            visualizer.start_monitoring()
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 