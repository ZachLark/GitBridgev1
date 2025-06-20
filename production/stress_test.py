#!/usr/bin/env python3
"""
GitBridge SmartRouter Stress Testing
Task: P20P7S5C - Production Hardening

Stress testing framework for SmartRouter with concurrent request simulation.
Tests system performance under high load and failure scenarios.

Author: GitBridge Development Team
Date: 2025-06-19
"""

import os
import sys
import time
import json
import asyncio
import threading
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_router.smart_router import SmartRouter, RoutingStrategy, ProviderType
from production.circuit_breaker import CircuitBreakerConfig, get_circuit_breaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] [STRESS_TEST] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class StressTestConfig:
    """Configuration for stress testing."""
    concurrent_users: int = 10
    duration_seconds: int = 60
    requests_per_second: float = 5.0
    timeout_seconds: float = 30.0
    failure_rate_threshold: float = 0.1  # 10% failure rate threshold
    latency_threshold: float = 5.0  # 5 seconds latency threshold
    circuit_breaker_enabled: bool = True
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None


@dataclass
class RequestResult:
    """Result of a single request."""
    timestamp: str
    provider: str
    success: bool
    response_time: float
    error_message: Optional[str]
    routing_decision: Dict[str, Any]
    task_type: str


@dataclass
class StressTestResult:
    """Results of a stress test."""
    config: StressTestConfig
    start_time: str
    end_time: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    failure_rate: float
    provider_distribution: Dict[str, int]
    strategy_distribution: Dict[str, int]
    error_summary: Dict[str, int]
    recommendations: List[str]


class StressTestRunner:
    """
    Stress testing runner for SmartRouter.
    
    Features:
    - Concurrent request simulation
    - Performance metrics collection
    - Failure scenario testing
    - Circuit breaker integration
    - Comprehensive reporting
    """
    
    def __init__(self, router: SmartRouter, config: StressTestConfig):
        """
        Initialize stress test runner.
        
        Args:
            router: SmartRouter instance to test
            config: Stress test configuration
        """
        self.router = router
        self.config = config
        self.results: List[RequestResult] = []
        self.running = False
        self.start_time = None
        self.end_time = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Circuit breaker setup
        if config.circuit_breaker_enabled:
            if config.circuit_breaker_config is None:
                config.circuit_breaker_config = CircuitBreakerConfig(
                    failure_threshold=5,
                    recovery_timeout=30.0,
                    success_threshold=2,
                    timeout=config.timeout_seconds
                )
            
            self.circuit_breaker = get_circuit_breaker(
                "stress_test", 
                config.circuit_breaker_config
            )
        else:
            self.circuit_breaker = None
            
        logger.info(f"Stress test runner initialized with config: {config}")
        
    def run(self) -> StressTestResult:
        """
        Run the stress test.
        
        Returns:
            StressTestResult: Test results
        """
        logger.info(f"Starting stress test with {self.config.concurrent_users} concurrent users")
        logger.info(f"Duration: {self.config.duration_seconds} seconds")
        logger.info(f"Target RPS: {self.config.requests_per_second}")
        
        self.running = True
        self.start_time = datetime.now(timezone.utc)
        
        # Calculate request intervals
        request_interval = 1.0 / self.config.requests_per_second
        
        # Start concurrent users
        with ThreadPoolExecutor(max_workers=self.config.concurrent_users) as executor:
            futures = []
            
            for user_id in range(self.config.concurrent_users):
                future = executor.submit(
                    self._user_worker, 
                    user_id, 
                    request_interval
                )
                futures.append(future)
            
            # Wait for all users to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"User worker failed: {str(e)}")
        
        self.running = False
        self.end_time = datetime.now(timezone.utc)
        
        # Generate results
        result = self._generate_results()
        
        logger.info("Stress test completed")
        logger.info(f"Total requests: {result.total_requests}")
        logger.info(f"Success rate: {(1 - result.failure_rate) * 100:.1f}%")
        logger.info(f"Average response time: {result.avg_response_time:.2f}s")
        logger.info(f"Requests per second: {result.requests_per_second:.1f}")
        
        return result
        
    def _user_worker(self, user_id: int, request_interval: float):
        """Worker function for a single user."""
        start_time = time.time()
        end_time = start_time + self.config.duration_seconds
        
        while self.running and time.time() < end_time:
            try:
                # Generate test request
                request_data = self._generate_test_request(user_id)
                
                # Execute request
                if self.circuit_breaker:
                    result = self.circuit_breaker.call(
                        self._execute_request,
                        request_data
                    )
                else:
                    result = self._execute_request(request_data)
                
                # Record result
                with self._lock:
                    self.results.append(result)
                    
            except Exception as e:
                # Record failure
                with self._lock:
                    self.results.append(RequestResult(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        provider="unknown",
                        success=False,
                        response_time=0.0,
                        error_message=str(e),
                        routing_decision={},
                        task_type="stress_test"
                    ))
                    
            # Wait for next request
            time.sleep(request_interval)
            
    def _generate_test_request(self, user_id: int) -> Dict[str, Any]:
        """Generate a test request."""
        # Different types of requests for variety
        request_types = [
            ("code_review", "Review this Python function for best practices"),
            ("analysis", "Analyze the performance implications of this algorithm"),
            ("explanation", "Explain how machine learning works in simple terms"),
            ("debugging", "Help debug this error in my code"),
            ("optimization", "Suggest ways to optimize this database query")
        ]
        
        task_type, prompt = request_types[user_id % len(request_types)]
        
        # Add some variation to prompts
        variations = [
            "Please provide a detailed response.",
            "Keep it concise and practical.",
            "Include examples if possible.",
            "Focus on the most important aspects.",
            "Consider edge cases and limitations."
        ]
        
        prompt += " " + variations[user_id % len(variations)]
        
        return {
            'prompt': prompt,
            'task_type': task_type,
            'max_tokens': 200 + (user_id % 100),  # Vary token count
            'temperature': 0.7 + (user_id % 3) * 0.1  # Vary temperature
        }
        
    def _execute_request(self, request_data: Dict[str, Any]) -> RequestResult:
        """Execute a single request."""
        start_time = time.time()
        
        try:
            response = self.router.route_request(
                prompt=request_data['prompt'],
                task_type=request_data['task_type'],
                max_tokens=request_data.get('max_tokens', 200),
                temperature=request_data.get('temperature', 0.7)
            )
            
            response_time = time.time() - start_time
            
            return RequestResult(
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider=response.provider.value,
                success=True,
                response_time=response_time,
                error_message=None,
                routing_decision=asdict(response.routing_decision),
                task_type=request_data['task_type']
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            
            return RequestResult(
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider="unknown",
                success=False,
                response_time=response_time,
                error_message=str(e),
                routing_decision={},
                task_type=request_data['task_type']
            )
            
    def _generate_results(self) -> StressTestResult:
        """Generate comprehensive test results."""
        with self._lock:
            total_requests = len(self.results)
            successful_requests = sum(1 for r in self.results if r.success)
            failed_requests = total_requests - successful_requests
            
            # Response time statistics
            response_times = [r.response_time for r in self.results if r.success]
            if response_times:
                avg_response_time = statistics.mean(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
            else:
                avg_response_time = min_response_time = max_response_time = 0.0
                p95_response_time = p99_response_time = 0.0
            
            # Calculate actual RPS
            if self.start_time and self.end_time:
                duration = (self.end_time - self.start_time).total_seconds()
                requests_per_second = total_requests / duration if duration > 0 else 0.0
            else:
                requests_per_second = 0.0
            
            # Failure rate
            failure_rate = failed_requests / total_requests if total_requests > 0 else 0.0
            
            # Provider distribution
            provider_distribution = {}
            for result in self.results:
                provider = result.provider
                provider_distribution[provider] = provider_distribution.get(provider, 0) + 1
            
            # Strategy distribution
            strategy_distribution = {}
            for result in self.results:
                if result.routing_decision:
                    strategy = result.routing_decision.get('strategy', 'unknown')
                    strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
            
            # Error summary
            error_summary = {}
            for result in self.results:
                if not result.success and result.error_message:
                    error_type = type(result.error_message).__name__
                    error_summary[error_type] = error_summary.get(error_type, 0) + 1
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                failure_rate, avg_response_time, requests_per_second
            )
            
            return StressTestResult(
                config=self.config,
                start_time=self.start_time.isoformat() if self.start_time else "",
                end_time=self.end_time.isoformat() if self.end_time else "",
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time=avg_response_time,
                min_response_time=min_response_time,
                max_response_time=max_response_time,
                p95_response_time=p95_response_time,
                p99_response_time=p99_response_time,
                requests_per_second=requests_per_second,
                failure_rate=failure_rate,
                provider_distribution=provider_distribution,
                strategy_distribution=strategy_distribution,
                error_summary=error_summary,
                recommendations=recommendations
            )
            
    def _generate_recommendations(self, failure_rate: float, avg_response_time: float, rps: float) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check failure rate
        if failure_rate > self.config.failure_rate_threshold:
            recommendations.append(
                f"High failure rate ({failure_rate:.1%}) detected. "
                "Consider investigating provider health and circuit breaker settings."
            )
        
        # Check response time
        if avg_response_time > self.config.latency_threshold:
            recommendations.append(
                f"High average response time ({avg_response_time:.2f}s) detected. "
                "Consider performance optimization or provider failover."
            )
        
        # Check throughput
        if rps < self.config.requests_per_second * 0.8:
            recommendations.append(
                f"Low throughput ({rps:.1f} RPS vs target {self.config.requests_per_second:.1f} RPS). "
                "Consider scaling up or optimizing request processing."
            )
        
        # Circuit breaker recommendations
        if self.circuit_breaker:
            cb_metrics = self.circuit_breaker.get_metrics()
            if cb_metrics['state'] == 'open':
                recommendations.append(
                    "Circuit breaker is open. Consider adjusting failure thresholds "
                    "or investigating underlying issues."
                )
        
        if not recommendations:
            recommendations.append("All performance metrics are within acceptable ranges.")
        
        return recommendations


class StressTestSuite:
    """
    Suite of stress tests for comprehensive testing.
    
    Features:
    - Multiple test scenarios
    - Progressive load testing
    - Failure injection testing
    - Performance regression testing
    """
    
    def __init__(self, router: SmartRouter):
        """Initialize stress test suite."""
        self.router = router
        self.results: List[StressTestResult] = []
        
    def run_basic_load_test(self, duration: int = 60) -> StressTestResult:
        """Run basic load test."""
        config = StressTestConfig(
            concurrent_users=10,
            duration_seconds=duration,
            requests_per_second=5.0,
            circuit_breaker_enabled=True
        )
        
        runner = StressTestRunner(self.router, config)
        result = runner.run()
        self.results.append(result)
        return result
        
    def run_high_load_test(self, duration: int = 120) -> StressTestResult:
        """Run high load test."""
        config = StressTestConfig(
            concurrent_users=50,
            duration_seconds=duration,
            requests_per_second=20.0,
            circuit_breaker_enabled=True
        )
        
        runner = StressTestRunner(self.router, config)
        result = runner.run()
        self.results.append(result)
        return result
        
    def run_stress_test(self, duration: int = 180) -> StressTestResult:
        """Run stress test with maximum load."""
        config = StressTestConfig(
            concurrent_users=100,
            duration_seconds=duration,
            requests_per_second=50.0,
            circuit_breaker_enabled=True
        )
        
        runner = StressTestRunner(self.router, config)
        result = runner.run()
        self.results.append(result)
        return result
        
    def run_failure_scenario_test(self, duration: int = 60) -> StressTestResult:
        """Run test with simulated failures."""
        # This would require mocking provider failures
        # For now, we'll run a normal test
        config = StressTestConfig(
            concurrent_users=20,
            duration_seconds=duration,
            requests_per_second=10.0,
            circuit_breaker_enabled=True
        )
        
        runner = StressTestRunner(self.router, config)
        result = runner.run()
        self.results.append(result)
        return result
        
    def run_full_suite(self) -> List[StressTestResult]:
        """Run the complete test suite."""
        logger.info("Starting full stress test suite")
        
        tests = [
            ("Basic Load Test", self.run_basic_load_test),
            ("High Load Test", self.run_high_load_test),
            ("Stress Test", self.run_stress_test),
            ("Failure Scenario Test", self.run_failure_scenario_test)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"Running {test_name}...")
            try:
                test_func()
                logger.info(f"{test_name} completed successfully")
            except Exception as e:
                logger.error(f"{test_name} failed: {str(e)}")
                
        logger.info("Full stress test suite completed")
        return self.results
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        if not self.results:
            return {"error": "No test results available"}
            
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_tests': len(self.results),
            'tests': [],
            'summary': {
                'total_requests': 0,
                'total_successful_requests': 0,
                'total_failed_requests': 0,
                'avg_failure_rate': 0.0,
                'avg_response_time': 0.0,
                'avg_requests_per_second': 0.0
            }
        }
        
        total_requests = 0
        total_successful = 0
        total_failed = 0
        failure_rates = []
        response_times = []
        rps_values = []
        
        for i, result in enumerate(self.results):
            test_data = {
                'test_number': i + 1,
                'config': asdict(result.config),
                'total_requests': result.total_requests,
                'successful_requests': result.successful_requests,
                'failed_requests': result.failed_requests,
                'failure_rate': result.failure_rate,
                'avg_response_time': result.avg_response_time,
                'requests_per_second': result.requests_per_second,
                'recommendations': result.recommendations
            }
            report['tests'].append(test_data)
            
            # Update summary
            total_requests += result.total_requests
            total_successful += result.successful_requests
            total_failed += result.failed_requests
            failure_rates.append(result.failure_rate)
            response_times.append(result.avg_response_time)
            rps_values.append(result.requests_per_second)
        
        # Calculate summary statistics
        summary = report['summary']
        summary['total_requests'] = total_requests
        summary['total_successful_requests'] = total_successful
        summary['total_failed_requests'] = total_failed
        summary['avg_failure_rate'] = statistics.mean(failure_rates) if failure_rates else 0.0
        summary['avg_response_time'] = statistics.mean(response_times) if response_times else 0.0
        summary['avg_requests_per_second'] = statistics.mean(rps_values) if rps_values else 0.0
        
        return report


def main():
    """Main function for stress testing."""
    parser = argparse.ArgumentParser(description='GitBridge SmartRouter Stress Testing')
    parser.add_argument('--test-type', default='basic', 
                       choices=['basic', 'high', 'stress', 'failure', 'full'],
                       help='Type of stress test to run')
    parser.add_argument('--duration', type=int, default=60,
                       help='Test duration in seconds')
    parser.add_argument('--users', type=int, default=10,
                       help='Number of concurrent users')
    parser.add_argument('--rps', type=float, default=5.0,
                       help='Requests per second')
    parser.add_argument('--strategy', default='adaptive',
                       choices=['cost_optimized', 'performance_optimized', 'availability_optimized', 'hybrid', 'adaptive'],
                       help='Routing strategy to use')
    parser.add_argument('--output', default='stress_test_results.json',
                       help='Output file for results')
    
    args = parser.parse_args()
    
    try:
        # Initialize SmartRouter
        strategy = RoutingStrategy(args.strategy)
        router = SmartRouter(strategy=strategy)
        
        if args.test_type == 'full':
            # Run full test suite
            suite = StressTestSuite(router)
            results = suite.run_full_suite()
            report = suite.generate_report()
        else:
            # Run single test
            config = StressTestConfig(
                concurrent_users=args.users,
                duration_seconds=args.duration,
                requests_per_second=args.rps,
                circuit_breaker_enabled=True
            )
            
            runner = StressTestRunner(router, config)
            result = runner.run()
            report = asdict(result)
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"Stress test completed. Results saved to {args.output}")
        print(f"Summary: {report.get('summary', 'N/A')}")
        
    except KeyboardInterrupt:
        print("\nStress test interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 