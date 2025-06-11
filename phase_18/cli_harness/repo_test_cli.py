#!/usr/bin/env python3
# P18P8S1 – CLI Test Harness for SmartRepo Fallback Simulation

"""
GitBridge Phase 18P8 - CLI Test Harness + Fallback Simulation

This module provides a comprehensive CLI interface for testing SmartRepo's
fallback ecosystem, including error simulation, UID replay, and stress testing.

Author: GitBridge MAS Integration Team
Phase: 18P8 - CLI Test Harness
MAS Lite Protocol: v2.1 Compliance
"""

import argparse
import json
import time
import sys
import os
import hashlib
import asyncio
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import logging

# Import fallback simulator, UID replay engine, and stress test engine
from fallback_simulator import FallbackSimulator
from uid_replay_engine import UIDReplayEngine
from stress_test_engine import StressTestEngine

# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Text colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


@dataclass
class TestSession:
    """Test session tracking and metadata"""
    session_id: str
    start_time: str
    command: str
    parameters: Dict[str, Any]
    results: Dict[str, Any] = field(default_factory=dict)
    log_file: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.session_id:
            self.session_id = self.generate_session_id()
        if not self.start_time:
            self.start_time = datetime.now(timezone.utc).isoformat()
    
    def generate_session_id(self) -> str:
        """Generate unique session identifier"""
        timestamp = datetime.now(timezone.utc).isoformat()
        unique_string = f"test_session_{timestamp}_{hash(time.time())}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]


class Logger:
    """Enhanced logging with color support and file output"""
    
    def __init__(self, session: TestSession, verbose: bool = False):
        self.session = session
        self.verbose = verbose
        self.log_entries = []
        
        # Setup file logging if specified
        if session.log_file:
            logging.basicConfig(
                filename=session.log_file,
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            self.file_logger = logging.getLogger(__name__)
        else:
            self.file_logger = None
    
    def log(self, level: str, message: str, color: str = Colors.RESET):
        """Log message with color and file output"""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Console output with color
        if level == "ERROR":
            color = Colors.RED
            self.session.errors.append(message)
        elif level == "WARNING":
            color = Colors.YELLOW
            self.session.warnings.append(message)
        elif level == "SUCCESS":
            color = Colors.GREEN
        elif level == "INFO":
            color = Colors.CYAN
        
        console_msg = f"{color}{level}{Colors.RESET}: {message}"
        print(console_msg)
        
        # File output (no color codes)
        if self.file_logger:
            self.file_logger.info(f"{level}: {message}")
        
        # Store in session
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "session_id": self.session.session_id
        }
        self.log_entries.append(log_entry)
    
    def info(self, message: str):
        """Log info message"""
        self.log("INFO", message, Colors.CYAN)
    
    def success(self, message: str):
        """Log success message"""
        self.log("SUCCESS", message, Colors.GREEN)
    
    def warning(self, message: str):
        """Log warning message"""
        self.log("WARNING", message, Colors.YELLOW)
    
    def error(self, message: str):
        """Log error message"""
        self.log("ERROR", message, Colors.RED)
    
    def banner(self, title: str, color: str = Colors.BLUE):
        """Print colored banner"""
        border = "=" * 60
        print(f"{color}{border}")
        print(f"{title:^60}")
        print(f"{border}{Colors.RESET}")
        if self.file_logger:
            self.file_logger.info(f"BANNER: {title}")


class CLITestHarness:
    """Main CLI test harness for SmartRepo fallback simulation"""
    
    def __init__(self):
        self.version = "v1.0.0 – Phase 18 Final"
        self.mas_protocol = "v2.1"
        self.session = None
        self.logger = None
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser"""
        parser = argparse.ArgumentParser(
            prog='repo_test_cli',
            description='GitBridge SmartRepo CLI Test Harness - Fallback Simulation & Validation',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"""
{Colors.BOLD}Examples:{Colors.RESET}
  {Colors.GREEN}# Simulate fallback scenarios{Colors.RESET}
  python repo_test_cli.py --fallback --count 5 --log fallback_test.log
  
  {Colors.GREEN}# Replay UID handoff chain{Colors.RESET}
  python repo_test_cli.py --replay --input uid_chain.json --output replay_report.json
  
  {Colors.GREEN}# Run stress test with 100 parallel fallbacks{Colors.RESET}
  python repo_test_cli.py --stress --threads 100 --duration 60 --log stress_test.log
  
  {Colors.GREEN}# Verbose mode with detailed output{Colors.RESET}
  python repo_test_cli.py --fallback --verbose --log detailed_test.log

{Colors.BOLD}Test Modes:{Colors.RESET}
  --fallback    Simulate fallback scenarios (timeout, model failure, escalation)
  --replay      Replay UID handoff chain from JSON input
  --stress      Run parallel stress test with configurable load

{Colors.BOLD}Output Options:{Colors.RESET}
  --log FILE    Save detailed logs to file
  --output FILE Save results to JSON file  
  --verbose     Enable detailed console output

{Colors.BOLD}MAS Lite Protocol:{Colors.RESET} v2.1
{Colors.BOLD}Version:{Colors.RESET} P18P8_v1.0
            """
        )
        
        # Main command modes (mutually exclusive)
        mode_group = parser.add_mutually_exclusive_group(required=True)
        mode_group.add_argument(
            '--fallback',
            action='store_true',
            help='Simulate fallback scenarios (timeout, model failure, escalation)'
        )
        mode_group.add_argument(
            '--replay',
            action='store_true',
            help='Replay UID handoff chain from JSON input'
        )
        mode_group.add_argument(
            '--stress',
            action='store_true',
            help='Run parallel stress test with configurable load'
        )
        
        # Fallback mode options
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of fallback scenarios to simulate (default: 10)'
        )
        parser.add_argument(
            '--fallback-types',
            nargs='+',
            choices=['timeout', 'model_failure', 'escalation', 'all'],
            default=['all'],
            help='Types of fallbacks to simulate (default: all)'
        )
        
        # Replay mode options
        parser.add_argument(
            '--input',
            type=str,
            help='Input JSON file containing UID handoff chain'
        )
        
        # Stress test options
        parser.add_argument(
            '--threads',
            type=int,
            default=50,
            help='Number of parallel threads for stress test (default: 50)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=30,
            help='Duration of stress test in seconds (default: 30)'
        )
        
        # Output and logging options
        parser.add_argument(
            '--output',
            type=str,
            help='Output JSON file for test results'
        )
        parser.add_argument(
            '--log',
            type=str,
            help='Log file for detailed output'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--no-color',
            action='store_true',
            help='Disable colored output'
        )
        
        # Version and help
        parser.add_argument(
            '--version',
            action='version',
            version=f'GitBridge CLI Test Harness {self.version} (MAS Protocol {self.mas_protocol})'
        )
        
        return parser
    
    def initialize_session(self, args: argparse.Namespace) -> TestSession:
        """Initialize test session with parameters"""
        # Determine command mode
        if args.fallback:
            command = "fallback"
        elif args.replay:
            command = "replay"
        elif args.stress:
            command = "stress"
        else:
            command = "unknown"
        
        # Gather parameters
        parameters = {
            "command": command,
            "count": getattr(args, 'count', None),
            "fallback_types": getattr(args, 'fallback_types', None),
            "input_file": getattr(args, 'input', None),
            "output_file": getattr(args, 'output', None),
            "threads": getattr(args, 'threads', None),
            "duration": getattr(args, 'duration', None),
            "verbose": args.verbose,
            "no_color": getattr(args, 'no_color', False)
        }
        
        session = TestSession(
            session_id="",
            start_time="",
            command=command,
            parameters=parameters,
            log_file=getattr(args, 'log', None)
        )
        
        return session
    
    def validate_arguments(self, args: argparse.Namespace) -> List[str]:
        """Validate command line arguments"""
        errors = []
        
        # Validate replay mode requirements
        if args.replay and not args.input:
            errors.append("--replay mode requires --input file")
        
        if args.replay and args.input and not Path(args.input).exists():
            errors.append(f"Input file not found: {args.input}")
        
        # Validate stress test parameters
        if args.stress:
            if args.threads < 1 or args.threads > 1000:
                errors.append("--threads must be between 1 and 1000")
            
            if args.duration < 1 or args.duration > 3600:
                errors.append("--duration must be between 1 and 3600 seconds")
        
        # Validate fallback parameters
        if args.fallback:
            if args.count < 1 or args.count > 1000:
                errors.append("--count must be between 1 and 1000")
        
        # Validate output paths
        if args.output:
            output_dir = Path(args.output).parent
            if not output_dir.exists():
                errors.append(f"Output directory does not exist: {output_dir}")
        
        if args.log:
            log_dir = Path(args.log).parent
            if not log_dir.exists():
                errors.append(f"Log directory does not exist: {log_dir}")
        
        return errors
    
    def run_fallback_mode(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Run fallback simulation mode"""
        self.logger.banner(f"🔄 FALLBACK SIMULATION MODE", Colors.MAGENTA)
        
        self.logger.info(f"Simulating {args.count} fallback scenarios")
        self.logger.info(f"Fallback types: {', '.join(args.fallback_types)}")
        
        # Initialize fallback simulator
        simulator = FallbackSimulator(self.session.session_id)
        
        # Run simulation
        simulation_results = simulator.run_fallback_simulation(
            count=args.count,
            fallback_types=args.fallback_types,
            logger=self.logger
        )
        
        # Generate audit report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audit_file = f"fallback_audit_{timestamp}.json"
        simulator.save_audit_report(audit_file, self.logger)
        
        # Prepare results
        results = {
            "mode": "fallback",
            "count": args.count,
            "types": args.fallback_types,
            "status": "completed",
            "simulation_results": simulation_results.to_dict(),
            "audit_report_file": audit_file,
            "error_distribution": simulation_results.error_distribution,
            "success_rate": (simulation_results.successful_triggers / simulation_results.total_scenarios) * 100 if simulation_results.total_scenarios > 0 else 0,
            "execution_time_ms": simulation_results.execution_time_ms
        }
        
        # Log error distribution summary
        self.logger.banner("📊 ERROR DISTRIBUTION SUMMARY", Colors.YELLOW)
        for error_type, count in simulation_results.error_distribution.items():
            percentage = (count / simulation_results.total_scenarios) * 100
            self.logger.info(f"{error_type}: {count} scenarios ({percentage:.1f}%)")
        
        return results
    
    def run_replay_mode(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Run UID replay mode"""
        self.logger.banner(f"📼 UID REPLAY MODE", Colors.BLUE)
        
        self.logger.info(f"Loading UID chain from: {args.input}")
        if args.output:
            self.logger.info(f"Output will be saved to: {args.output}")
        
        # Initialize UID replay engine
        replay_engine = UIDReplayEngine(self.session.session_id)
        
        # Run UID chain replay
        transcript = replay_engine.replay_uid_chain(args.input, self.logger)
        
        if not transcript:
            self.logger.error("Failed to replay UID chain")
            return {
                "mode": "replay",
                "input_file": args.input,
                "output_file": args.output,
                "status": "failed",
                "error": "Failed to load or replay UID chain"
            }
        
        # Determine output file
        if args.output:
            output_file = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"uid_replay_report_{timestamp}.json"
        
        # Save replay transcript
        replay_engine.save_replay_transcript(output_file, self.logger)
        
        # Prepare results
        results = {
            "mode": "replay",
            "input_file": args.input,
            "output_file": output_file,
            "status": "completed",
            "transcript": transcript.to_dict(),
            "lineage_analysis": transcript.lineage_analysis,
            "total_nodes": transcript.total_nodes,
            "successful_replays": transcript.successful_replays,
            "failed_replays": transcript.failed_replays,
            "success_rate": (transcript.successful_replays / transcript.total_nodes) * 100 if transcript.total_nodes > 0 else 0,
            "execution_time_ms": transcript.execution_time_ms
        }
        
        # Log lineage analysis summary
        self.logger.banner("🔍 LINEAGE ANALYSIS SUMMARY", Colors.YELLOW)
        analysis = transcript.lineage_analysis
        self.logger.info(f"Total nodes: {analysis.get('total_nodes', 0)}")
        self.logger.info(f"Unique agents: {analysis.get('unique_agents', 0)}")
        self.logger.info(f"Fallback events: {analysis.get('fallback_count', 0)}")
        
        # Confidence statistics
        conf_stats = analysis.get('confidence_statistics', {})
        if conf_stats:
            self.logger.info(f"Average confidence: {conf_stats.get('average', 0):.3f}")
            self.logger.info(f"Below threshold: {conf_stats.get('below_threshold_count', 0)} nodes")
        
        # Agent distribution
        agent_dist = analysis.get('agent_distribution', {})
        if agent_dist:
            self.logger.info("Agent distribution:")
            for agent, count in agent_dist.items():
                percentage = (count / analysis.get('total_nodes', 1)) * 100
                self.logger.info(f"  {agent}: {count} ({percentage:.1f}%)")
        
        return results
    
    def run_stress_mode(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Run stress test mode"""
        self.logger.banner(f"⚡ STRESS TEST MODE", Colors.RED)
        
        self.logger.info(f"Parallel threads: {args.threads}")
        self.logger.info(f"Test duration: {args.duration} seconds")
        
        # Initialize stress test engine
        stress_engine = StressTestEngine(self.session.session_id)
        
        # Run stress test
        metrics = stress_engine.run_stress_test(
            thread_count=args.threads,
            duration_seconds=args.duration,
            logger=self.logger
        )
        
        # Determine output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"stress_test_results_{timestamp}.json"
        
        # Save stress test results
        stress_engine.save_stress_test_results(output_file, self.logger)
        
        # Prepare results
        results = {
            "mode": "stress",
            "threads": args.threads,
            "duration": args.duration,
            "status": "completed",
            "metrics": metrics.to_dict(),
            "output_file": output_file,
            "total_operations": metrics.total_operations,
            "operations_per_second": metrics.operations_per_second,
            "redis_writes": metrics.redis_writes,
            "redis_write_rate": metrics.redis_write_rate,
            "peak_memory_mb": metrics.peak_memory_mb,
            "success_rate": (metrics.successful_operations / metrics.total_operations * 100) if metrics.total_operations > 0 else 0,
            "execution_time_ms": metrics.total_duration_ms
        }
        
        # Log stress test performance summary
        self.logger.banner("🔥 STRESS TEST PERFORMANCE SUMMARY", Colors.YELLOW)
        self.logger.info(f"Total operations executed: {metrics.total_operations}")
        self.logger.info(f"Operations per second: {metrics.operations_per_second:.2f}")
        self.logger.info(f"Peak memory usage: {metrics.peak_memory_mb:.1f} MB")
        self.logger.info(f"Redis write rate: {metrics.redis_write_rate:.2f} writes/sec")
        self.logger.info(f"Redis total writes: {metrics.redis_writes}")
        self.logger.info(f"Redis errors: {metrics.redis_errors}")
        
        # Error distribution
        self.logger.info("Error distribution:")
        for error_type, count in metrics.error_distribution.items():
            percentage = (count / metrics.total_operations) * 100 if metrics.total_operations > 0 else 0
            self.logger.info(f"  {error_type}: {count} ({percentage:.1f}%)")
        
        # Performance assessment with lite test mode suppression
        if metrics.operations_per_second > 50:
            self.logger.success("🚀 High performance: >50 ops/sec")
        elif metrics.operations_per_second > 20:
            self.logger.info("✅ Good performance: >20 ops/sec")
        else:
            if args.duration < 10:
                self.logger.info("⚠️  Low performance: <20 ops/sec")
                self.logger.info("INFO: Performance warning suppressed (lite test mode < 10s)")
            else:
                self.logger.warning("⚠️  Low performance: <20 ops/sec")
        
        return results
    
    def save_results(self, results: Dict[str, Any], output_file: Optional[str] = None):
        """Save test results to JSON file"""
        # Add session metadata
        results.update({
            "session_id": self.session.session_id,
            "start_time": self.session.start_time,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "command": self.session.command,
            "parameters": self.session.parameters,
            "errors": self.session.errors,
            "warnings": self.session.warnings,
            "mas_lite_protocol": self.mas_protocol,
            "version": self.version
        })
        
        # Determine output file
        if output_file:
            output_path = Path(output_file)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"test_results_{timestamp}.json")
        
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.success(f"Results saved to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        self.logger.banner("📊 TEST SUMMARY", Colors.GREEN)
        
        # Session info
        self.logger.info(f"Session ID: {self.session.session_id}")
        self.logger.info(f"Command: {self.session.command}")
        self.logger.info(f"Start Time: {self.session.start_time}")
        
        # Results
        mode = results.get("mode", "unknown")
        status = results.get("status", "unknown")
        
        if status == "placeholder":
            self.logger.warning(f"Mode '{mode}' execution pending implementation")
        else:
            self.logger.success(f"Mode '{mode}' completed with status: {status}")
        
        # Error and warning counts
        error_count = len(self.session.errors)
        warning_count = len(self.session.warnings)
        
        if error_count > 0:
            self.logger.error(f"Errors encountered: {error_count}")
        
        if warning_count > 0:
            self.logger.warning(f"Warnings: {warning_count}")
        
        if error_count == 0 and warning_count == 0:
            self.logger.success("No errors or warnings")
    
    def run(self):
        """Main CLI execution entry point"""
        try:
            # Parse arguments
            parser = self.create_parser()
            args = parser.parse_args()
            
            # Disable colors if requested
            if getattr(args, 'no_color', False):
                for attr in dir(Colors):
                    if not attr.startswith('_'):
                        setattr(Colors, attr, '')
            
            # Initialize session
            self.session = self.initialize_session(args)
            self.logger = Logger(self.session, args.verbose)
            
            # Welcome banner
            self.logger.banner(f"🚀 GitBridge CLI Test Harness {self.version}", Colors.CYAN)
            
            # Validate arguments
            validation_errors = self.validate_arguments(args)
            if validation_errors:
                for error in validation_errors:
                    self.logger.error(error)
                return 1
            
            # Execute appropriate mode
            if args.fallback:
                results = self.run_fallback_mode(args)
            elif args.replay:
                results = self.run_replay_mode(args)
            elif args.stress:
                results = self.run_stress_mode(args)
            else:
                self.logger.error("No valid mode specified")
                return 1
            
            # Save results
            self.save_results(results, args.output)
            
            # Print summary
            self.print_summary(results)
            
            # Return appropriate exit code
            if self.session.errors:
                return 1
            else:
                return 0
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
            return 130
        except Exception as e:
            print(f"{Colors.RED}Unexpected error: {e}{Colors.RESET}")
            return 1


def main():
    """CLI entry point"""
    harness = CLITestHarness()
    exit_code = harness.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main() 