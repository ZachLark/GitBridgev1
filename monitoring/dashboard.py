#!/usr/bin/env python3
"""
GitBridge SmartRouter Monitoring Dashboard
Task: P20P7S5B - Monitoring Dashboard

Flask-based web dashboard for real-time SmartRouter monitoring with Prometheus metrics.
Features routing decisions visualization, provider health monitoring, and budget tracking.

Author: GitBridge Development Team
Date: 2025-06-19
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import prometheus_client
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_router.smart_router import SmartRouter, RoutingStrategy, ProviderType


# Prometheus metrics
REQUEST_COUNT = Counter('smartrouter_requests_total', 'Total requests processed', ['provider', 'status'])
REQUEST_LATENCY = Histogram('smartrouter_request_duration_seconds', 'Request latency', ['provider'])
PROVIDER_HEALTH = Gauge('smartrouter_provider_health', 'Provider health status', ['provider'])
ROUTING_DECISIONS = Counter('smartrouter_routing_decisions_total', 'Routing decisions made', ['strategy', 'provider'])
COST_TOTAL = Counter('smartrouter_cost_total', 'Total cost incurred', ['provider'])
TOKEN_USAGE = Counter('smartrouter_tokens_total', 'Total tokens used', ['provider'])


class SmartRouterDashboard:
    """
    Flask-based monitoring dashboard for SmartRouter.
    
    Features:
    - Real-time routing decisions visualization
    - Provider health monitoring
    - Budget consumption tracking
    - Token usage analytics
    - Prometheus metrics export
    - Performance trend analysis
    """
    
    def __init__(self, router: SmartRouter, host: str = '0.0.0.0', port: int = 5000):
        """
        Initialize the monitoring dashboard.
        
        Args:
            router: SmartRouter instance to monitor
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.router = router
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Setup routes
        self._setup_routes()
        
        # Data storage for real-time updates
        self.latest_metrics = {}
        self.latest_decisions = []
        self.performance_history = []
        
        # Start background data collection
        self._start_background_collection()
        
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page."""
            return render_template('dashboard.html')
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get current metrics."""
            try:
                metrics = self.router.get_enhanced_metrics()
                return jsonify(metrics)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/decisions')
        def get_decisions():
            """Get recent routing decisions."""
            try:
                decisions = self.router.get_routing_history(limit=50)
                return jsonify(decisions)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics')
        def get_analytics():
            """Get routing analytics."""
            try:
                analytics = self.router.get_routing_analytics()
                return jsonify(analytics)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/status')
        def get_status():
            """Get provider status."""
            try:
                status = self.router.get_provider_status()
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance-history')
        def get_performance_history():
            """Get performance history."""
            try:
                return jsonify(self.performance_history)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/strategy', methods=['GET', 'POST'])
        def manage_strategy():
            """Get or set routing strategy."""
            if request.method == 'POST':
                try:
                    data = request.get_json()
                    strategy_name = data.get('strategy')
                    if strategy_name:
                        strategy = RoutingStrategy(strategy_name)
                        self.router.set_strategy(strategy)
                        return jsonify({'message': f'Strategy changed to {strategy_name}'})
                    else:
                        return jsonify({'error': 'Strategy not specified'}), 400
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            else:
                return jsonify({'strategy': self.router.strategy.value})
        
        @self.app.route('/api/weights', methods=['GET', 'POST'])
        def manage_weights():
            """Get or set routing weights."""
            if request.method == 'POST':
                try:
                    data = request.get_json()
                    cost_weight = data.get('cost_weight', 0.4)
                    performance_weight = data.get('performance_weight', 0.3)
                    availability_weight = data.get('availability_weight', 0.3)
                    
                    self.router.set_weights(cost_weight, performance_weight, availability_weight)
                    return jsonify({'message': 'Weights updated successfully'})
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            else:
                return jsonify({
                    'cost_weight': self.router.cost_weight,
                    'performance_weight': self.router.performance_weight,
                    'availability_weight': self.router.availability_weight
                })
        
        @self.app.route('/api/reset-metrics', methods=['POST'])
        def reset_metrics():
            """Reset all metrics."""
            try:
                self.router.reset_metrics()
                return jsonify({'message': 'Metrics reset successfully'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/test-request', methods=['POST'])
        def test_request():
            """Test a routing request."""
            try:
                data = request.get_json()
                prompt = data.get('prompt', 'Test request')
                task_type = data.get('task_type', 'test')
                max_tokens = data.get('max_tokens', 100)
                
                response = self.router.route_request(
                    prompt=prompt,
                    task_type=task_type,
                    max_tokens=max_tokens
                )
                
                # Update Prometheus metrics
                REQUEST_COUNT.labels(
                    provider=response.provider.value,
                    status='success'
                ).inc()
                
                REQUEST_LATENCY.labels(
                    provider=response.provider.value
                ).observe(response.response_time)
                
                ROUTING_DECISIONS.labels(
                    strategy=response.routing_decision.strategy.value,
                    provider=response.provider.value
                ).inc()
                
                return jsonify({
                    'success': True,
                    'provider': response.provider.value,
                    'response_time': response.response_time,
                    'content': response.content[:200] + '...' if len(response.content) > 200 else response.content,
                    'routing_decision': {
                        'strategy': response.routing_decision.strategy.value,
                        'confidence': response.routing_decision.confidence,
                        'reasoning': response.routing_decision.reasoning
                    }
                })
            except Exception as e:
                # Update Prometheus metrics for failure
                REQUEST_COUNT.labels(
                    provider='unknown',
                    status='failure'
                ).inc()
                
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/metrics')
        def metrics():
            """Prometheus metrics endpoint."""
            return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
        
        @self.app.route('/health')
        def health():
            """Health check endpoint."""
            try:
                status = self.router.get_provider_status()
                healthy_providers = sum(
                    1 for provider_data in status['providers'].values()
                    if provider_data['available']
                )
                
                if healthy_providers > 0:
                    return jsonify({
                        'status': 'healthy',
                        'healthy_providers': healthy_providers,
                        'total_providers': len(status['providers'])
                    })
                else:
                    return jsonify({
                        'status': 'unhealthy',
                        'message': 'No healthy providers available'
                    }), 503
            except Exception as e:
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e)
                }), 503
        
        @self.app.route('/api/budget-analysis')
        def budget_analysis():
            """Get budget analysis."""
            try:
                metrics = self.router.get_enhanced_metrics()
                analytics = self.router.get_routing_analytics()
                
                # Calculate budget analysis
                total_cost = 0.0
                provider_costs = {}
                
                for provider_name, provider_data in metrics['providers'].items():
                    # Estimate cost based on requests and average cost per 1K tokens
                    estimated_cost = (
                        provider_data['total_requests'] * 
                        provider_data['avg_cost_per_1k_tokens'] * 
                        0.5  # Assume average 500 tokens per request
                    )
                    provider_costs[provider_name] = estimated_cost
                    total_cost += estimated_cost
                
                # Calculate daily trends
                today = datetime.now(timezone.utc).date()
                daily_decisions = [
                    d for d in analytics.get('recent_decisions', [])
                    if datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')).date() == today
                ]
                
                analysis = {
                    'total_cost': total_cost,
                    'provider_costs': provider_costs,
                    'daily_requests': len(daily_decisions),
                    'cost_per_request': total_cost / max(1, metrics['overall_performance']['total_requests']),
                    'budget_efficiency': self._calculate_budget_efficiency(metrics, analytics),
                    'recommendations': self._generate_budget_recommendations(metrics, analytics)
                }
                
                return jsonify(analysis)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
    def _start_background_collection(self):
        """Start background data collection thread."""
        def collect_data():
            while True:
                try:
                    # Update latest metrics
                    self.latest_metrics = self.router.get_enhanced_metrics()
                    
                    # Update latest decisions
                    self.latest_decisions = self.router.get_routing_history(limit=20)
                    
                    # Update performance history
                    timestamp = datetime.now(timezone.utc)
                    performance_point = {
                        'timestamp': timestamp.isoformat(),
                        'total_requests': self.latest_metrics['overall_performance']['total_requests'],
                        'avg_latency': self.latest_metrics['overall_performance']['avg_latency'],
                        'avg_success_rate': self.latest_metrics['overall_performance']['avg_success_rate']
                    }
                    
                    self.performance_history.append(performance_point)
                    
                    # Keep only last 1000 data points
                    if len(self.performance_history) > 1000:
                        self.performance_history = self.performance_history[-1000:]
                    
                    # Update Prometheus metrics
                    self._update_prometheus_metrics()
                    
                    time.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    print(f"Error in background data collection: {str(e)}")
                    time.sleep(5)
        
        # Start background thread
        self.data_thread = threading.Thread(target=collect_data, daemon=True)
        self.data_thread.start()
        
    def _update_prometheus_metrics(self):
        """Update Prometheus metrics."""
        try:
            # Update provider health metrics
            for provider_name, provider_data in self.latest_metrics['providers'].items():
                health_value = 1.0 if provider_data['availability_score'] > 0.5 else 0.0
                PROVIDER_HEALTH.labels(provider=provider_name).set(health_value)
                
                # Update cost metrics
                estimated_cost = (
                    provider_data['total_requests'] * 
                    provider_data['avg_cost_per_1k_tokens'] * 
                    0.5
                )
                COST_TOTAL.labels(provider=provider_name).inc(estimated_cost)
                
                # Update token usage metrics
                estimated_tokens = provider_data['total_requests'] * 500  # Assume 500 tokens per request
                TOKEN_USAGE.labels(provider=provider_name).inc(estimated_tokens)
                
        except Exception as e:
            print(f"Error updating Prometheus metrics: {str(e)}")
        
    def _calculate_budget_efficiency(self, metrics: Dict, analytics: Dict) -> float:
        """Calculate budget efficiency score."""
        try:
            # Calculate cost per successful request
            total_requests = metrics['overall_performance']['total_requests']
            total_failures = metrics['overall_performance']['total_failures']
            successful_requests = total_requests - total_failures
            
            if successful_requests == 0:
                return 0.0
            
            # Estimate total cost
            total_cost = 0.0
            for provider_data in metrics['providers'].values():
                estimated_cost = (
                    provider_data['total_requests'] * 
                    provider_data['avg_cost_per_1k_tokens'] * 
                    0.5
                )
                total_cost += estimated_cost
            
            # Efficiency = successful requests / cost
            efficiency = successful_requests / max(total_cost, 0.01)
            
            # Normalize to 0-1 range
            return min(1.0, efficiency / 1000)  # Scale factor
            
        except Exception:
            return 0.0
        
    def _generate_budget_recommendations(self, metrics: Dict, analytics: Dict) -> List[str]:
        """Generate budget optimization recommendations."""
        recommendations = []
        
        # Check for high-cost providers
        provider_costs = {}
        for provider_name, provider_data in metrics['providers'].items():
            estimated_cost = (
                provider_data['total_requests'] * 
                provider_data['avg_cost_per_1k_tokens'] * 
                0.5
            )
            provider_costs[provider_name] = estimated_cost
        
        # Find most expensive provider
        if provider_costs:
            most_expensive = max(provider_costs.items(), key=lambda x: x[1])
            if most_expensive[1] > 1.0:  # More than $1
                recommendations.append(f"Consider cost optimization for {most_expensive[0].upper()} - highest cost provider")
        
        # Check success rates
        for provider_name, provider_data in metrics['providers'].items():
            if provider_data['success_rate'] < 0.9:
                recommendations.append(f"Low success rate for {provider_name.upper()} - consider failover to reduce retry costs")
        
        # Check routing strategy
        strategy_dist = analytics.get('strategy_distribution', {})
        if strategy_dist.get('cost_optimized', 0) == 0:
            recommendations.append("Consider using cost-optimized routing strategy to reduce expenses")
        
        if not recommendations:
            recommendations.append("Budget efficiency is good - no immediate optimization needed")
        
        return recommendations
        
    def start(self):
        """Start the dashboard server."""
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] "
              f"Starting SmartRouter Dashboard on http://{self.host}:{self.port}")
        print(f"Prometheus metrics available at http://{self.host}:{self.port}/metrics")
        print(f"Health check available at http://{self.host}:{self.port}/health")
        
        self.app.run(host=self.host, port=self.port, debug=False, threaded=True)


def create_dashboard_templates():
    """Create HTML templates for the dashboard."""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create dashboard.html template
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitBridge SmartRouter Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-top: 0;
            color: #fff;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            padding-bottom: 10px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
        }
        .metric-value {
            font-weight: bold;
            color: #4ade80;
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .btn {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .btn:hover {
            background: rgba(255,255,255,0.3);
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-healthy { background: #4ade80; }
        .status-warning { background: #fbbf24; }
        .status-error { background: #f87171; }
        .loading {
            text-align: center;
            padding: 20px;
            color: rgba(255,255,255,0.7);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 GitBridge SmartRouter Dashboard</h1>
            <p>Real-time monitoring and analytics</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="refreshData()">🔄 Refresh</button>
            <button class="btn" onclick="resetMetrics()">🔄 Reset Metrics</button>
            <button class="btn" onclick="testRequest()">🧪 Test Request</button>
            <select id="strategySelect" class="btn" onchange="changeStrategy()">
                <option value="adaptive">Adaptive</option>
                <option value="cost_optimized">Cost Optimized</option>
                <option value="performance_optimized">Performance Optimized</option>
                <option value="availability_optimized">Availability Optimized</option>
                <option value="hybrid">Hybrid</option>
            </select>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 Overall Performance</h3>
                <div id="overallMetrics" class="loading">Loading...</div>
            </div>
            
            <div class="card">
                <h3>🏥 Provider Health</h3>
                <div id="providerHealth" class="loading">Loading...</div>
            </div>
            
            <div class="card">
                <h3>💰 Budget Analysis</h3>
                <div id="budgetAnalysis" class="loading">Loading...</div>
            </div>
            
            <div class="card">
                <h3>🎯 Routing Analytics</h3>
                <div id="routingAnalytics" class="loading">Loading...</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📈 Performance Trends</h3>
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h3>🎲 Recent Decisions</h3>
                <div id="recentDecisions" class="loading">Loading...</div>
            </div>
        </div>
    </div>
    
    <script>
        let performanceChart;
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboard();
            setInterval(loadDashboard, 5000); // Refresh every 5 seconds
        });
        
        async function loadDashboard() {
            try {
                await Promise.all([
                    loadOverallMetrics(),
                    loadProviderHealth(),
                    loadBudgetAnalysis(),
                    loadRoutingAnalytics(),
                    loadRecentDecisions(),
                    loadPerformanceChart()
                ]);
            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }
        
        async function loadOverallMetrics() {
            const response = await axios.get('/api/metrics');
            const data = response.data;
            
            const html = `
                <div class="metric">
                    <span>Total Requests:</span>
                    <span class="metric-value">${data.overall_performance.total_requests}</span>
                </div>
                <div class="metric">
                    <span>Success Rate:</span>
                    <span class="metric-value">${(data.overall_performance.avg_success_rate * 100).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>Avg Latency:</span>
                    <span class="metric-value">${data.overall_performance.avg_latency.toFixed(2)}s</span>
                </div>
                <div class="metric">
                    <span>Retry Effectiveness:</span>
                    <span class="metric-value">${(data.overall_performance.avg_retry_effectiveness * 100).toFixed(1)}%</span>
                </div>
            `;
            
            document.getElementById('overallMetrics').innerHTML = html;
        }
        
        async function loadProviderHealth() {
            const response = await axios.get('/api/status');
            const data = response.data;
            
            let html = '';
            for (const [provider, info] of Object.entries(data.providers)) {
                const statusClass = info.available ? 'status-healthy' : 'status-error';
                const statusText = info.available ? 'Healthy' : 'Unavailable';
                
                html += `
                    <div class="metric">
                        <span>
                            <span class="status-indicator ${statusClass}"></span>
                            ${provider.toUpperCase()}
                        </span>
                        <span class="metric-value">${statusText}</span>
                    </div>
                    <div class="metric">
                        <span>Success Rate:</span>
                        <span class="metric-value">${(info.metrics.success_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span>Avg Latency:</span>
                        <span class="metric-value">${info.metrics.avg_latency.toFixed(2)}s</span>
                    </div>
                `;
            }
            
            document.getElementById('providerHealth').innerHTML = html;
        }
        
        async function loadBudgetAnalysis() {
            const response = await axios.get('/api/budget-analysis');
            const data = response.data;
            
            const html = `
                <div class="metric">
                    <span>Total Cost:</span>
                    <span class="metric-value">$${data.total_cost.toFixed(4)}</span>
                </div>
                <div class="metric">
                    <span>Cost per Request:</span>
                    <span class="metric-value">$${data.cost_per_request.toFixed(6)}</span>
                </div>
                <div class="metric">
                    <span>Budget Efficiency:</span>
                    <span class="metric-value">${(data.budget_efficiency * 100).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>Daily Requests:</span>
                    <span class="metric-value">${data.daily_requests}</span>
                </div>
            `;
            
            document.getElementById('budgetAnalysis').innerHTML = html;
        }
        
        async function loadRoutingAnalytics() {
            const response = await axios.get('/api/analytics');
            const data = response.data;
            
            const html = `
                <div class="metric">
                    <span>Total Decisions:</span>
                    <span class="metric-value">${data.total_decisions}</span>
                </div>
                <div class="metric">
                    <span>Avg Confidence:</span>
                    <span class="metric-value">${(data.avg_confidence * 100).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>Avg Estimated Cost:</span>
                    <span class="metric-value">$${data.avg_estimated_cost.toFixed(6)}</span>
                </div>
                <div class="metric">
                    <span>Avg Estimated Latency:</span>
                    <span class="metric-value">${data.avg_estimated_latency.toFixed(2)}s</span>
                </div>
            `;
            
            document.getElementById('routingAnalytics').innerHTML = html;
        }
        
        async function loadRecentDecisions() {
            const response = await axios.get('/api/decisions');
            const decisions = response.data.slice(-10); // Last 10 decisions
            
            let html = '';
            for (const decision of decisions.reverse()) {
                const timestamp = new Date(decision.timestamp).toLocaleTimeString();
                html += `
                    <div class="metric">
                        <span>${timestamp}</span>
                        <span class="metric-value">${decision.selected_provider.toUpperCase()}</span>
                    </div>
                `;
            }
            
            document.getElementById('recentDecisions').innerHTML = html;
        }
        
        async function loadPerformanceChart() {
            const response = await axios.get('/api/performance-history');
            const data = response.data;
            
            const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString());
            const latencies = data.map(d => d.avg_latency);
            const requests = data.map(d => d.total_requests);
            
            if (performanceChart) {
                performanceChart.destroy();
            }
            
            const ctx = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Avg Latency (s)',
                        data: latencies,
                        borderColor: '#4ade80',
                        backgroundColor: 'rgba(74, 222, 128, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255,255,255,0.1)'
                            },
                            ticks: {
                                color: 'rgba(255,255,255,0.8)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255,255,255,0.1)'
                            },
                            ticks: {
                                color: 'rgba(255,255,255,0.8)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: 'rgba(255,255,255,0.8)'
                            }
                        }
                    }
                }
            });
        }
        
        async function refreshData() {
            await loadDashboard();
        }
        
        async function resetMetrics() {
            if (confirm('Are you sure you want to reset all metrics?')) {
                await axios.post('/api/reset-metrics');
                await loadDashboard();
            }
        }
        
        async function testRequest() {
            const prompt = prompt('Enter test prompt:');
            if (prompt) {
                try {
                    const response = await axios.post('/api/test-request', {
                        prompt: prompt,
                        task_type: 'test',
                        max_tokens: 100
                    });
                    
                    alert(`Test completed! Provider: ${response.data.provider}, Time: ${response.data.response_time.toFixed(2)}s`);
                    await loadDashboard();
                } catch (error) {
                    alert('Test failed: ' + error.response?.data?.error || error.message);
                }
            }
        }
        
        async function changeStrategy() {
            const strategy = document.getElementById('strategySelect').value;
            try {
                await axios.post('/api/strategy', { strategy: strategy });
                alert('Strategy changed successfully!');
            } catch (error) {
                alert('Failed to change strategy: ' + error.response?.data?.error || error.message);
            }
        }
    </script>
</body>
</html>'''
    
    with open(os.path.join(templates_dir, 'dashboard.html'), 'w') as f:
        f.write(dashboard_html)


def main():
    """Main function for the dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitBridge SmartRouter Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--strategy', default='adaptive', 
                       choices=['cost_optimized', 'performance_optimized', 'availability_optimized', 'hybrid', 'adaptive'],
                       help='Routing strategy to use')
    
    args = parser.parse_args()
    
    try:
        # Create templates
        create_dashboard_templates()
        
        # Initialize SmartRouter
        strategy = RoutingStrategy(args.strategy)
        router = SmartRouter(strategy=strategy)
        
        # Start dashboard
        dashboard = SmartRouterDashboard(router, args.host, args.port)
        dashboard.start()
        
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 