"""
GitBridge Phase 18 Part 5 - SmartRepo Failure Heatmap Generator.

This module implements a comprehensive failure visualization system that analyzes
task-level error frequency, failure clustering, fallback severity patterns over
time and across system components for visual heatmap generation.

Task ID: P18P5S3
Title: Failure Heatmap Generator
Author: GitBridge Team
MAS Lite Protocol v2.1 Compliance: Yes
"""

import os
import json
import glob
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import hashlib

# Import SmartRepo components for integration
from smartrepo_audit_logger import (
    get_audit_logger, log_event, log_operation_start, log_operation_end,
    OperationType, ResultStatus
)

class SmartRepoFailureHeatmapGenerator:
    """
    SmartRepo Comprehensive Failure Heatmap Generator for GitBridge Phase 18P5.
    
    Provides failure visualization including clustering analysis, severity mapping,
    temporal distribution, and module-level failure correlation.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize the SmartRepo Failure Heatmap Generator.
        
        Args:
            repo_path (str): Path to the Git repository (default: current directory)
        """
        self.repo_path = Path(repo_path).resolve()
        self.logs_dir = self.repo_path / "logs"
        self.daily_logs_dir = self.logs_dir / "daily"
        self.docs_dir = self.repo_path / "docs"
        self.completion_logs_dir = self.docs_dir / "completion_logs"
        
        # Log file paths
        self.failures_jsonl_file = self.logs_dir / "test_failures.jsonl"
        self.main_log_file = self.logs_dir / "smartrepo.log"
        self.dashboard_file = self.docs_dir / "dashboard.md"
        
        # Output file paths
        self.heatmap_report_file = self.completion_logs_dir / "P18P5S3_FAILURE_HEATMAP.md"
        self.recursive_log_file = self.completion_logs_dir / "P18P5S3_RECURSIVE_LOG.md"
        self.completion_summary_file = self.completion_logs_dir / "P18P5S3_COMPLETION_SUMMARY.md"
        
        # Initialize audit logger
        self.audit_logger = get_audit_logger()
        
        # Failure data storage
        self.failure_data = {
            "failures": [],
            "task_failures": defaultdict(list),
            "module_failures": defaultdict(list),
            "severity_distribution": defaultdict(int),
            "failure_type_counts": defaultdict(int),
            "hourly_failures": defaultdict(int),
            "daily_failures": defaultdict(int),
            "phase_failures": defaultdict(int),
            "severity_scores": [],
            "parsing_stats": {
                "total_entries": 0,
                "parsed_entries": 0,
                "failed_entries": 0,
                "corrupted_entries": 0
            },
            "warnings": [],
            "error_log": []
        }
        
        # Severity mapping for visualization
        self.severity_map = {
            "CRITICAL": {"score": 5, "symbol": "🔴", "color": "red"},
            "HIGH": {"score": 4, "symbol": "🟠", "color": "orange"},  
            "MEDIUM": {"score": 3, "symbol": "🟡", "color": "yellow"},
            "LOW": {"score": 2, "symbol": "🟢", "color": "green"},
            "INFO": {"score": 1, "symbol": "🔵", "color": "blue"}
        }

    def generate_failure_heatmap(self, output_format: str = "markdown") -> str:
        """
        Generate comprehensive failure heatmap visualization.
        
        Args:
            output_format (str): Output format ("markdown" or "text")
            
        Returns:
            str: Generated heatmap content
        """
        operation_id = log_operation_start(OperationType.SYSTEM.value, "failure_heatmap_generation",
                                         f"Starting failure heatmap generation in {output_format} format")
        
        try:
            # Load failure data
            self._load_failure_data()
            
            # Process and analyze failures
            self._analyze_failure_patterns()
            
            # Generate heatmap content
            if output_format.lower() == "text":
                content = self._generate_text_heatmap()
            else:
                content = self._generate_markdown_heatmap()
            
            # Write heatmap report
            self._write_heatmap_report(content)
            
            # Log recursive issues if any
            if self.failure_data["warnings"] or self.failure_data["error_log"]:
                self._write_recursive_log()
            
            log_operation_end(OperationType.SYSTEM.value, "failure_heatmap_generation", operation_id,
                            ResultStatus.SUCCESS.value, f"Failure heatmap generated: {len(content)} characters")
            
            return content
            
        except Exception as e:
            error_msg = f"Failure heatmap generation failed: {e}"
            self._log_heatmap_failure("HEATMAP_FAILURE", error_msg)
            
            log_operation_end(OperationType.SYSTEM.value, "failure_heatmap_generation", operation_id,
                            ResultStatus.FAIL.value, error_msg)
            
            return self._generate_fallback_heatmap(str(e))

    def _load_failure_data(self) -> None:
        """
        Load failure data from all available sources.
        """
        # Load JSONL failure logs
        self._load_jsonl_failures()
        
        # Load daily logs for additional failures
        self._load_daily_failure_logs()

    def _load_jsonl_failures(self) -> None:
        """
        Load structured JSONL failure logs.
        """
        try:
            if not self.failures_jsonl_file.exists():
                self._add_warning(f"JSONL failure log not found: {self.failures_jsonl_file}")
                return
            
            with open(self.failures_jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    self.failure_data["parsing_stats"]["total_entries"] += 1
                    
                    try:
                        if line.strip():
                            failure = json.loads(line.strip())
                            
                            # Validate required fields
                            required_fields = ["task_id", "failure_type", "severity", "timestamp"]
                            if all(field in failure for field in required_fields):
                                self.failure_data["failures"].append(failure)
                                self.failure_data["parsing_stats"]["parsed_entries"] += 1
                            else:
                                self.failure_data["parsing_stats"]["failed_entries"] += 1
                                self._add_error(f"Missing required fields in line {line_num}")
                                
                    except json.JSONDecodeError as e:
                        self.failure_data["parsing_stats"]["failed_entries"] += 1
                        self._add_error(f"JSON parse error line {line_num}: {e}")
                    except Exception as e:
                        self.failure_data["parsing_stats"]["corrupted_entries"] += 1
                        self._add_error(f"Corrupted entry line {line_num}: {e}")
                        
        except Exception as e:
            self._add_warning(f"Failed to load JSONL failure log: {e}")

    def _load_daily_failure_logs(self) -> None:
        """
        Load daily logs and extract failure information.
        """
        try:
            if not self.daily_logs_dir.exists():
                self._add_warning(f"Daily logs directory not found: {self.daily_logs_dir}")
                return
            
            daily_log_files = list(self.daily_logs_dir.glob("*.log"))
            
            for log_file in daily_log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            # Look for failure indicators in daily logs
                            if any(keyword in line.lower() for keyword in ["error", "fail", "exception", "critical"]):
                                # Extract timestamp from log line
                                timestamp = self._extract_timestamp_from_log_line(line)
                                if timestamp:
                                    synthetic_failure = {
                                        "task_id": f"daily_log_{log_file.stem}_{line_num}",
                                        "failure_type": "DAILY_LOG_ERROR",
                                        "severity": self._determine_severity_from_line(line),
                                        "timestamp": timestamp,
                                        "message": line.strip(),
                                        "source_module": "daily_log",
                                        "source_file": str(log_file),
                                        "line_number": line_num
                                    }
                                    self.failure_data["failures"].append(synthetic_failure)
                                    
                except Exception as e:
                    self._add_warning(f"Failed to process daily log {log_file}: {e}")
                    
        except Exception as e:
            self._add_warning(f"Failed to load daily failure logs: {e}")

    def _analyze_failure_patterns(self) -> None:
        """
        Analyze failure patterns and generate statistics.
        """
        for failure in self.failure_data["failures"]:
            # Task-level clustering
            task_id = failure.get("task_id", "unknown")
            self.failure_data["task_failures"][task_id].append(failure)
            
            # Module-level clustering
            module = failure.get("source_module", "unknown")
            self.failure_data["module_failures"][module].append(failure)
            
            # Severity distribution
            severity = failure.get("severity", "UNKNOWN")
            self.failure_data["severity_distribution"][severity] += 1
            
            # Failure type counts
            failure_type = failure.get("failure_type", "UNKNOWN")
            self.failure_data["failure_type_counts"][failure_type] += 1
            
            # Phase distribution
            phase = failure.get("phase", "UNKNOWN")
            self.failure_data["phase_failures"][phase] += 1
            
            # Temporal clustering
            timestamp_str = failure.get("timestamp", "")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Hourly clustering
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    self.failure_data["hourly_failures"][hour_key] += 1
                    
                    # Daily clustering
                    day_key = timestamp.strftime("%Y-%m-%d")
                    self.failure_data["daily_failures"][day_key] += 1
                    
                except Exception as e:
                    self._add_warning(f"Failed to parse timestamp {timestamp_str}: {e}")
            
            # Severity scores for analysis
            severity_score = failure.get("severity_score", self.severity_map.get(severity, {}).get("score", 0))
            self.failure_data["severity_scores"].append(severity_score)

    def _generate_markdown_heatmap(self) -> str:
        """
        Generate markdown-formatted failure heatmap.
        """
        total_failures = len(self.failure_data["failures"])
        avg_severity = sum(self.failure_data["severity_scores"]) / len(self.failure_data["severity_scores"]) if self.failure_data["severity_scores"] else 0
        
        content = f"""# SmartRepo Failure Heatmap Analysis

**Generated**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Report Type**: Failure Pattern Analysis & Heatmap  
**MAS Lite Protocol**: v2.1 Compliant  
**Analysis Period**: System-wide failure analysis

---

## 🔥 **Failure Heatmap Overview**

### **Critical Metrics**
- **Total Failures**: {total_failures}
- **Average Severity Score**: {avg_severity:.2f}/5.0
- **Unique Tasks Affected**: {len(self.failure_data["task_failures"])}
- **Modules with Failures**: {len(self.failure_data["module_failures"])}
- **Failure Types**: {len(self.failure_data["failure_type_counts"])}

### **Data Quality**
- **Parsed Entries**: {self.failure_data["parsing_stats"]["parsed_entries"]} / {self.failure_data["parsing_stats"]["total_entries"]}
- **Parse Success Rate**: {(self.failure_data["parsing_stats"]["parsed_entries"] / max(1, self.failure_data["parsing_stats"]["total_entries"])) * 100:.1f}%
- **Data Completeness**: {"🟢 High" if self.failure_data["parsing_stats"]["parsed_entries"] > 10 else "🟡 Medium" if self.failure_data["parsing_stats"]["parsed_entries"] > 5 else "🔴 Low"}

---

## 📊 **Failure Severity Heatmap**

### **Severity Distribution**
| Severity | Count | Percentage | Heat Level | Impact |
|----------|-------|------------|------------|---------|
"""
        
        # Severity distribution table
        total_for_pct = max(1, sum(self.failure_data["severity_distribution"].values()))
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            count = self.failure_data["severity_distribution"].get(severity, 0)
            percentage = (count / total_for_pct) * 100
            symbol = self.severity_map.get(severity, {}).get("symbol", "⚪")
            heat_level = "🔴🔴🔴" if percentage > 40 else "🔴🔴" if percentage > 20 else "🔴" if percentage > 10 else "🟡" if percentage > 5 else "🟢"
            impact = "Severe" if severity == "CRITICAL" else "High" if severity == "HIGH" else "Moderate" if severity == "MEDIUM" else "Low" if severity == "LOW" else "Minimal"
            content += f"| {symbol} {severity} | {count} | {percentage:.1f}% | {heat_level} | {impact} |\n"

        # Task-level heatmap
        content += f"""

---

## 🎯 **Task-Level Failure Heatmap**

### **Top 10 Most Affected Tasks**
| Task ID | Failures | Severity | Latest Failure | Heat Index |
|---------|----------|----------|----------------|------------|
"""
        
        # Sort tasks by failure count
        sorted_tasks = sorted(self.failure_data["task_failures"].items(), 
                             key=lambda x: len(x[1]), reverse=True)[:10]
        
        for task_id, task_failures in sorted_tasks:
            failure_count = len(task_failures)
            # Calculate average severity for this task
            task_severities = [f.get("severity_score", 0) for f in task_failures]
            avg_severity = sum(task_severities) / len(task_severities) if task_severities else 0
            
            # Get latest failure
            latest_failure = max(task_failures, key=lambda x: x.get("timestamp", ""), default={})
            latest_time = latest_failure.get("timestamp", "Unknown")[:16] if latest_failure.get("timestamp") else "Unknown"
            
            # Calculate heat index
            heat_index = "🔴🔴🔴" if failure_count >= 5 else "🔴🔴" if failure_count >= 3 else "🔴" if failure_count >= 2 else "🟡"
            
            content += f"| {task_id} | {failure_count} | {avg_severity:.1f}/5.0 | {latest_time} | {heat_index} |\n"

        # Module-level heatmap
        content += f"""

---

## 🔧 **Module-Level Failure Heatmap**

### **Module Failure Distribution**
| Module | Failures | Failure Rate | Primary Issues | Heat Level |
|--------|----------|--------------|----------------|-------------|
"""
        
        # Sort modules by failure count
        sorted_modules = sorted(self.failure_data["module_failures"].items(),
                               key=lambda x: len(x[1]), reverse=True)
        
        for module, module_failures in sorted_modules:
            failure_count = len(module_failures)
            
            # Get most common failure types for this module
            module_failure_types = Counter(f.get("failure_type", "UNKNOWN") for f in module_failures)
            primary_issue = module_failure_types.most_common(1)[0][0] if module_failure_types else "N/A"
            
            # Calculate failure rate (failures per unique task)
            unique_tasks = len(set(f.get("task_id", "") for f in module_failures))
            failure_rate = f"{failure_count}/{unique_tasks}" if unique_tasks > 0 else f"{failure_count}/1"
            
            # Heat level
            heat_level = "🔴🔴🔴" if failure_count >= 8 else "🔴🔴" if failure_count >= 5 else "🔴" if failure_count >= 3 else "🟡" if failure_count >= 2 else "🟢"
            
            content += f"| {module} | {failure_count} | {failure_rate} | {primary_issue} | {heat_level} |\n"

        # Temporal heatmap
        content += f"""

---

## ⏰ **Temporal Failure Heatmap**

### **Hourly Failure Distribution**
| Hour | Failures | Activity Level | Heat Pattern |
|------|----------|----------------|--------------|
"""
        
        # Sort hourly failures
        sorted_hourly = sorted(self.failure_data["hourly_failures"].items())[-24:]  # Last 24 hours
        
        for hour, count in sorted_hourly:
            activity_level = "🔴 Critical" if count >= 10 else "🟠 High" if count >= 5 else "🟡 Medium" if count >= 2 else "🟢 Low"
            heat_pattern = "█" * min(count, 10) + "░" * max(0, 10 - count)
            content += f"| {hour} | {count} | {activity_level} | {heat_pattern} |\n"

        # Failure type analysis
        content += f"""

---

## 🔍 **Failure Type Analysis**

### **Failure Type Heatmap**
| Failure Type | Count | Percentage | Severity Impact | Trend |
|--------------|-------|------------|-----------------|-------|
"""
        
        # Sort failure types by count
        sorted_failure_types = sorted(self.failure_data["failure_type_counts"].items(),
                                     key=lambda x: x[1], reverse=True)
        
        total_failures_for_pct = max(1, sum(self.failure_data["failure_type_counts"].values()))
        
        for failure_type, count in sorted_failure_types:
            percentage = (count / total_failures_for_pct) * 100
            
            # Calculate average severity impact for this failure type
            type_failures = [f for f in self.failure_data["failures"] if f.get("failure_type") == failure_type]
            avg_impact = sum(f.get("severity_score", 0) for f in type_failures) / len(type_failures) if type_failures else 0
            
            severity_impact = f"{avg_impact:.1f}/5.0"
            trend = "📈 Rising" if count >= 5 else "➡️ Stable" if count >= 3 else "📉 Declining"
            
            content += f"| {failure_type} | {count} | {percentage:.1f}% | {severity_impact} | {trend} |\n"

        # System health assessment
        content += f"""

---

## 🏥 **System Health Assessment**

### **Failure Clustering Analysis**
- **High-Risk Tasks**: {len([t for t, f in self.failure_data["task_failures"].items() if len(f) >= 3])} tasks with ≥3 failures
- **Critical Modules**: {len([m for m, f in self.failure_data["module_failures"].items() if len(f) >= 5])} modules with ≥5 failures
- **Peak Failure Hour**: {max(self.failure_data["hourly_failures"].items(), key=lambda x: x[1])[0] if self.failure_data["hourly_failures"] else "N/A"}
- **Failure Concentration**: {(len(self.failure_data["task_failures"]) / max(1, total_failures)) * 100:.1f}% task coverage

### **Risk Assessment**
- **System Stability**: {"🔴 Critical" if total_failures >= 15 else "🟠 At Risk" if total_failures >= 10 else "🟡 Moderate" if total_failures >= 5 else "🟢 Stable"}
- **Failure Diversity**: {"🔴 High" if len(self.failure_data["failure_type_counts"]) >= 5 else "🟡 Medium" if len(self.failure_data["failure_type_counts"]) >= 3 else "🟢 Low"}
- **Module Impact**: {"🔴 Widespread" if len(self.failure_data["module_failures"]) >= 5 else "🟡 Localized" if len(self.failure_data["module_failures"]) >= 3 else "🟢 Minimal"}

### **Recommendations**
- 🔧 Focus on high-failure modules: {", ".join([m for m, f in sorted(self.failure_data["module_failures"].items(), key=lambda x: len(x[1]), reverse=True)[:3]])}
- 🎯 Address critical tasks: {len([t for t, f in self.failure_data["task_failures"].items() if any(fail.get("severity") == "CRITICAL" for fail in f)])} tasks with CRITICAL failures
- ⏰ Monitor peak hours: {", ".join([h for h, c in sorted(self.failure_data["hourly_failures"].items(), key=lambda x: x[1], reverse=True)[:3]])}

"""

        # Add warnings section if any
        if self.failure_data["warnings"]:
            content += f"""
---

## ⚠️ **Data Quality Warnings**

"""
            for warning in self.failure_data["warnings"]:
                content += f"- ⚠️ {warning}\n"

        content += f"""

---

*Generated by GitBridge SmartRepo Failure Heatmap Generator*  
*Task ID: P18P5S3 | Component: Failure Heatmap Generator*  
*MAS Lite Protocol v2.1 | Phase 18P5 - RepoReady Front-End Display*  
*Heatmap Generation: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}*

"""
        
        return content

    def _generate_text_heatmap(self) -> str:
        """
        Generate plain text failure heatmap.
        """
        total_failures = len(self.failure_data["failures"])
        
        content = f"""SmartRepo Failure Heatmap Analysis - Text Format
Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

=== FAILURE OVERVIEW ===
Total Failures: {total_failures}
Unique Tasks: {len(self.failure_data["task_failures"])}
Affected Modules: {len(self.failure_data["module_failures"])}

=== SEVERITY DISTRIBUTION ===
"""
        
        for severity, count in self.failure_data["severity_distribution"].items():
            content += f"{severity}: {count} failures\n"
        
        content += f"""
=== TOP FAILING TASKS ===
"""
        
        sorted_tasks = sorted(self.failure_data["task_failures"].items(), 
                             key=lambda x: len(x[1]), reverse=True)[:5]
        
        for task_id, failures in sorted_tasks:
            content += f"{task_id}: {len(failures)} failures\n"
        
        content += f"""
=== MODULE ANALYSIS ===
"""
        
        sorted_modules = sorted(self.failure_data["module_failures"].items(),
                               key=lambda x: len(x[1]), reverse=True)[:5]
        
        for module, failures in sorted_modules:
            content += f"{module}: {len(failures)} failures\n"
        
        return content

    def _generate_fallback_heatmap(self, error: str) -> str:
        """
        Generate fallback heatmap when primary generation fails.
        """
        return f"""# SmartRepo Failure Heatmap - Fallback Mode

**Generated**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Status**: ⚠️ Fallback Mode - Primary generation failed  
**Error**: {error}

## 📊 **Partial Analysis Available**

- **Data Sources**: Limited to available logs
- **Analysis Status**: Degraded mode
- **Recommendations**: Review log file formats and accessibility

### **System Status**
- Failure heatmap generation encountered issues
- Attempting to provide basic failure summary
- Manual review recommended for complete analysis

*Fallback report generated by GitBridge SmartRepo Failure Heatmap Generator*
"""

    def _write_heatmap_report(self, content: str) -> None:
        """
        Write heatmap report to file.
        """
        try:
            self.completion_logs_dir.mkdir(parents=True, exist_ok=True)
            with open(self.heatmap_report_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self._add_error(f"Failed to write heatmap report: {e}")

    def _write_recursive_log(self) -> None:
        """
        Write recursive resolution log if issues occurred.
        """
        try:
            recursive_content = f"""# P18P5S3 Recursive Resolution Log

**Generated**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Task**: Failure Heatmap Generator  
**Status**: Partial Success with Warnings

## ⚠️ **Warnings Encountered**

"""
            for warning in self.failure_data["warnings"]:
                recursive_content += f"- {warning}\n"
                
            recursive_content += """

## 🔍 **Error Log**

"""
            for error in self.failure_data["error_log"]:
                recursive_content += f"- {error}\n"
                
            recursive_content += f"""

## 🔄 **Resolution Actions Taken**

- Continued processing with available data
- Generated heatmap with partial coverage
- Logged issues for future resolution
- Provided degraded but functional output

## 📊 **Coverage Assessment**

- Parsed Entries: {self.failure_data["parsing_stats"]["parsed_entries"]}
- Failed Entries: {self.failure_data["parsing_stats"]["failed_entries"]}
- Coverage Gap: {(self.failure_data["parsing_stats"]["failed_entries"] / max(1, self.failure_data["parsing_stats"]["total_entries"])) * 100:.1f}%

*Recursive log generated by GitBridge SmartRepo Failure Heatmap Generator*
"""
            
            with open(self.recursive_log_file, 'w', encoding='utf-8') as f:
                f.write(recursive_content)
                
        except Exception as e:
            self._add_error(f"Failed to write recursive log: {e}")

    def _extract_timestamp_from_log_line(self, line: str) -> Optional[str]:
        """
        Extract timestamp from a log line.
        """
        # Simple timestamp extraction - look for ISO format
        import re
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})'
        match = re.search(timestamp_pattern, line)
        if match:
            return match.group(1) + "+00:00"  # Add timezone if missing
        return None

    def _determine_severity_from_line(self, line: str) -> str:
        """
        Determine severity level from log line content.
        """
        line_lower = line.lower()
        if any(word in line_lower for word in ["critical", "fatal", "emergency"]):
            return "CRITICAL"
        elif any(word in line_lower for word in ["error", "fail", "exception"]):
            return "HIGH"
        elif any(word in line_lower for word in ["warn", "warning"]):
            return "MEDIUM"
        else:
            return "LOW"

    def _add_warning(self, message: str) -> None:
        """
        Add warning message to tracking.
        """
        self.failure_data["warnings"].append(message)

    def _add_error(self, message: str) -> None:
        """
        Add error message to tracking.
        """
        self.failure_data["error_log"].append(message)

    def _log_heatmap_failure(self, category: str, message: str) -> None:
        """
        Log heatmap generation failure to smartrepo.log.
        """
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            failure_entry = f"{timestamp} - ERROR - {category}: {message}\n"
            
            with open(self.main_log_file, 'a', encoding='utf-8') as f:
                f.write(failure_entry)
                
        except Exception as e:
            # Silent failure - avoid infinite recursion
            pass

    def recursive_validate_heatmap_generator(self) -> dict:
        """
        Recursive validation of heatmap generator functionality.
        
        Returns:
            dict: Validation results with detailed metrics
        """
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "total_failures": len(self.failure_data["failures"]),
                "unique_tasks": len(self.failure_data["task_failures"]),
                "affected_modules": len(self.failure_data["module_failures"]),
                "severity_distribution": dict(self.failure_data["severity_distribution"]),
                "data_completeness": 0.0,
                "parse_success_rate": 0.0
            }
            
            # Calculate data completeness
            if self.failure_data["parsing_stats"]["total_entries"] > 0:
                validation_result["parse_success_rate"] = (
                    self.failure_data["parsing_stats"]["parsed_entries"] / 
                    self.failure_data["parsing_stats"]["total_entries"]
                ) * 100
                
                validation_result["data_completeness"] = min(100.0, validation_result["parse_success_rate"])
            
            # Check for validation errors
            if validation_result["parse_success_rate"] < 90:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Parse success rate {validation_result['parse_success_rate']:.1f}% below 90% threshold")
            
            if validation_result["total_failures"] < 5:
                validation_result["warnings"].append(f"Low failure count ({validation_result['total_failures']}) may indicate missing data")
            
            # Add warnings from processing
            validation_result["warnings"].extend(self.failure_data["warnings"])
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation failed: {e}"],
                "warnings": [],
                "total_failures": 0,
                "unique_tasks": 0,
                "affected_modules": 0,
                "severity_distribution": {},
                "data_completeness": 0.0,
                "parse_success_rate": 0.0
            }


def generate_failure_heatmap(output_format: str = "markdown") -> str:
    """
    Generate failure heatmap using SmartRepoFailureHeatmapGenerator.
    
    Args:
        output_format (str): Output format ("markdown" or "text")
        
    Returns:
        str: Generated heatmap content
    """
    generator = SmartRepoFailureHeatmapGenerator()
    return generator.generate_failure_heatmap(output_format)


def recursive_validate_heatmap_generator() -> dict:
    """
    Perform recursive validation of heatmap generator.
    
    Returns:
        dict: Validation results
    """
    generator = SmartRepoFailureHeatmapGenerator()
    generator._load_failure_data()
    generator._analyze_failure_patterns()
    return generator.recursive_validate_heatmap_generator()


if __name__ == "__main__":
    """
    Command-line interface for failure heatmap generation.
    """
    import sys
    
    output_format = sys.argv[1] if len(sys.argv) > 1 else "markdown"
    
    print(f"Generating failure heatmap in {output_format} format...")
    result = generate_failure_heatmap(output_format)
    
    print(f"Heatmap generated: {len(result)} characters")
    print("\nValidating heatmap generator...")
    
    validation = recursive_validate_heatmap_generator()
    print(f"Validation result: {'PASS' if validation['valid'] else 'FAIL'}")
    print(f"Total failures analyzed: {validation['total_failures']}")
    print(f"Unique tasks affected: {validation['unique_tasks']}") 