#!/usr/bin/env python3
"""GitBridge Project Code Snapshot Generator.

This script recursively scans the project directory and generates a snapshot
of all Python, Markdown, and text files, including their structure and
documentation. Follows MAS Lite Protocol v2.1 specifications for code auditing.
"""

import os
import re
import json
import hashlib
import argparse
import sys
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime

__version__ = "2.1.0"

class CodeSnapshotGenerator:
    """Generates a snapshot of the project's code structure."""

    def __init__(self, root_dir: str = "."):
        """Initialize the snapshot generator.
        
        Args:
            root_dir: Root directory to start scanning from
        """
        self.root_dir = os.path.abspath(root_dir)
        self.snapshot_data = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "root_directory": self.root_dir,
                "version": "2.1.0"
            },
            "files": [],
            "phase_transitions": [],
            "unlinked_tests": [],
            "warnings": []
        }
        
        # Regex patterns for code analysis
        self.patterns = {
            "function": re.compile(r"^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*:"),
            "class": re.compile(r"^class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?\s*:"),
            "comment": re.compile(r"^\s*#\s*(.*)$"),
            "docstring": re.compile(r'"""(.*?)"""', re.DOTALL),
            "phase_marker": re.compile(r"#\s*(?:GBP|GitBridge Phase)\s*(\d+)(?:\s*→\s*(\d+))?"),
            "gbp_function": re.compile(r"^def\s+gbp\d+_"),
            "function_docstring": re.compile(r'^\s+"""(.*?)"""', re.DOTALL),
            "malformed_phase": re.compile(r"#\s*(?:GBX|GitBridge X)\s*\d+")
        }
        
        # File extensions to process
        self.target_extensions = {".py", ".md", ".txt"}
        
        # Directories to skip
        self.skip_dirs = {
            "__pycache__",
            ".git",
            "venv",
            "env",
            "node_modules",
            ".pytest_cache",
            ".DS_Store",
            "__MACOSX",
            ".idea",
            ".vscode"
        }
        
        # Track all GBP functions and components for test linking
        self.gbp_components: Set[str] = set()
        self.test_files: List[Dict[str, Any]] = []

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash of the file content
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def detect_phase_markers(self, content: str, file_path: str) -> Tuple[List[int], List[Tuple[int, int]]]:
        """Detect GitBridge phase markers and transitions in content.
        
        Args:
            content: File content to analyze
            file_path: Path to the file being analyzed
            
        Returns:
            Tuple of (phase numbers, phase transitions)
        """
        phases = set()
        transitions = []
        
        # Check for phase markers and transitions in comments
        for line_num, line in enumerate(content.split("\n"), 1):
            # Check for malformed phase markers
            if self.patterns["malformed_phase"].search(line):
                self.snapshot_data["warnings"].append({
                    "file": file_path,
                    "line": line_num,
                    "type": "malformed_phase",
                    "message": f"Malformed phase marker found: {line.strip()}"
                })
                continue
                
            match = self.patterns["phase_marker"].search(line)
            if match:
                try:
                    phase = int(match.group(1))
                    phases.add(phase)
                    
                    # Check for phase transition (→ arrow notation)
                    if match.group(2):
                        next_phase = int(match.group(2))
                        transitions.append((phase, next_phase))
                        self.snapshot_data["phase_transitions"].append({
                            "file": file_path,
                            "line": line_num,
                            "from_phase": phase,
                            "to_phase": next_phase
                        })
                except ValueError:
                    continue
        
        # Check for gbpXX_ function names
        for line_num, line in enumerate(content.split("\n"), 1):
            if self.patterns["gbp_function"].search(line):
                try:
                    phase_num = int(re.search(r"gbp(\d+)_", line).group(1))
                    phases.add(phase_num)
                    # Track GBP component name for test linking
                    func_name = re.search(r"def\s+(gbp\d+_\w+)", line).group(1)
                    self.gbp_components.add(func_name)
                except (ValueError, AttributeError):
                    continue
        
        return sorted(list(phases)), transitions

    def extract_function_definitions(self, content: str) -> List[Dict[str, Any]]:
        """Extract detailed function definitions including docstrings and comments.
        
        Args:
            content: File content to analyze
            
        Returns:
            List of function definition dictionaries
        """
        function_defs = []
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            func_match = self.patterns["function"].match(line)
            if func_match:
                func_name = func_match.group(1)
                func_info = {
                    "name": func_name,
                    "start_line": i + 1,
                    "docstring": "",
                    "comments": []
                }
                
                # Look for comments above the function
                j = i - 1
                while j >= 0 and (lines[j].strip().startswith("#") or not lines[j].strip()):
                    if lines[j].strip().startswith("#"):
                        func_info["comments"].insert(0, lines[j].strip()[1:].strip())
                    j -= 1
                
                # Look for docstring
                if i + 1 < len(lines):
                    docstring_match = self.patterns["function_docstring"].match(
                        "\n".join(lines[i+1:i+4])
                    )
                    if docstring_match:
                        func_info["docstring"] = docstring_match.group(1).strip()
                
                function_defs.append(func_info)
        
        return function_defs

    def is_test_file(self, file_path: str) -> bool:
        """Determine if a file is a test file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is a test file
        """
        rel_path = os.path.relpath(file_path, self.root_dir)
        return (
            rel_path.startswith("tests/") or
            os.path.basename(file_path).startswith("test_") or
            os.path.basename(file_path).endswith("_test.py")
        )

    def extract_top_comments(self, content: str, max_lines: int = 5) -> List[str]:
        """Extract the first N commented lines from the content.
        
        Args:
            content: File content to analyze
            max_lines: Maximum number of comment lines to extract
            
        Returns:
            List of extracted comment lines
        """
        comments = []
        lines = content.split("\n")
        
        # First check for module docstring
        docstring_match = self.patterns["docstring"].search(content)
        if docstring_match:
            docstring = docstring_match.group(1).strip()
            comments.extend(docstring.split("\n")[:max_lines])
            return comments
        
        # If no docstring, look for # comments
        for line in lines[:10]:  # Check first 10 lines for comments
            if len(comments) >= max_lines:
                break
                
            comment_match = self.patterns["comment"].match(line)
            if comment_match:
                comment = comment_match.group(1).strip()
                if comment:  # Only add non-empty comments
                    comments.append(comment)
        
        return comments

    def extract_definitions(self, content: str) -> Tuple[List[str], List[str]]:
        """Extract top-level function and class definitions.
        
        Args:
            content: File content to analyze
            
        Returns:
            Tuple of (function names, class names)
        """
        functions = []
        classes = []
        
        lines = content.split("\n")
        current_indent = 0
        
        for line in lines:
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith("#"):
                continue
            
            # Calculate current line's indentation
            indent = len(line) - len(line.lstrip())
            
            # Only process top-level definitions (no indentation)
            if indent == 0:
                func_match = self.patterns["function"].match(line)
                if func_match:
                    functions.append(func_match.group(1))
                    
                class_match = self.patterns["class"].match(line)
                if class_match:
                    classes.append(class_match.group(1))
        
        return functions, classes

    def process_file(self, file_path: str) -> Dict:
        """Process a single file and extract its information.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Dictionary containing file information
        """
        file_info = {
            "file_path": file_path,
            "sha256": self.calculate_file_hash(file_path)
        }
        
        # Skip processing binary or very large files
        if os.path.getsize(file_path) > 5 * 1024 * 1024:  # 5MB limit
            file_info["warning"] = "File exceeds size limit"
            return file_info
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            file_info["error"] = "Binary or non-UTF8 file"
            return file_info
        except Exception as e:
            file_info["error"] = str(e)
            return file_info
        
        # Extract top-level comments
        file_info["top_comments"] = self.extract_top_comments(content)
        
        # Extract function and class definitions
        functions, classes = self.extract_definitions(content)
        if functions:
            file_info["functions"] = functions
        if classes:
            file_info["classes"] = classes
        
        # Detect phase markers and transitions
        phases, transitions = self.detect_phase_markers(content, file_path)
        if phases:
            file_info["phases_detected"] = phases
            
        # Track test files for later analysis
        if self.is_test_file(file_path):
            file_info["is_test_file"] = True
            self.test_files.append(file_info)
            
        # Check for markdown structure if requested
        if file_path.endswith('.md'):
            try:
                file_info["markdown_structure"] = self.analyze_markdown_structure(content)
            except Exception as e:
                self.snapshot_data["warnings"].append({
                    "file": file_path,
                    "type": "markdown_parse_error",
                    "message": str(e)
                })
        
        return file_info
        
    def analyze_markdown_structure(self, content: str) -> Dict[str, Any]:
        """Analyze the structure of a markdown file.
        
        Args:
            content: Markdown content to analyze
            
        Returns:
            Dictionary containing markdown structure information
        """
        structure = {
            "headings": [],
            "roadmap_references": []
        }
        
        for line in content.split("\n"):
            # Extract headings
            if line.strip().startswith("#"):
                level = len(line.split()[0])  # Count # symbols
                heading = line.strip("#").strip()
                structure["headings"].append({
                    "level": level,
                    "text": heading
                })
            
            # Look for roadmap references
            roadmap_match = re.search(r"(?i)roadmap.*?(?:gbp|gitbridge)\s*(\d+)", line)
            if roadmap_match:
                structure["roadmap_references"].append({
                    "phase": int(roadmap_match.group(1)),
                    "context": line.strip()
                })
        
        return structure
        
    def generate_snapshot(self) -> None:
        """Generate a snapshot of the entire codebase."""
        print(f"Generating code snapshot from: {self.root_dir}\n")
        
        for root, dirs, files in os.walk(self.root_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file in files:
                if not any(file.endswith(ext) for ext in self.target_extensions):
                    continue
                    
                file_path = os.path.join(root, file)
                print(f"Processing: {os.path.relpath(file_path, self.root_dir)}")
                
                file_info = self.process_file(file_path)
                self.snapshot_data["files"].append(file_info)
        
        # Post-processing steps
        self.detect_unlinked_tests()
        self.analyze_phase_transitions()
        
    def analyze_phase_transitions(self) -> None:
        """Analyze phase transitions for consistency."""
        transitions = self.snapshot_data["phase_transitions"]
        
        # Check for missing intermediate phases
        for trans in transitions:
            if trans["to_phase"] - trans["from_phase"] > 1:
                self.snapshot_data["warnings"].append({
                    "file": trans["file"],
                    "type": "phase_gap",
                    "message": f"Phase transition {trans['from_phase']} → {trans['to_phase']} skips intermediate phases"
                })

    def save_snapshot(self, output_file: str = "gitbridge_code_snapshot.json") -> None:
        """Save the snapshot data to a JSON file.
        
        Args:
            output_file: Path to the output JSON file
        """
        output_path = os.path.join(self.root_dir, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(
                self.snapshot_data,
                f,
                indent=2,
                sort_keys=True
            )
        print(f"\nSnapshot saved to: {output_path}")

    def detect_unlinked_tests(self) -> None:
        """Identify test files that don't reference any known GBP components."""
        for test_file in self.test_files:
            file_path = test_file["file_path"]
            has_gbp_reference = False
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check if test file references any known GBP components
                    for component in self.gbp_components:
                        if component in content:
                            has_gbp_reference = True
                            break
                    
                    if not has_gbp_reference:
                        self.snapshot_data["unlinked_tests"].append({
                            "file": file_path,
                            "message": "Test file doesn't reference any known GBP components"
                        })
            except Exception as e:
                self.snapshot_data["warnings"].append({
                    "file": file_path,
                    "type": "read_error",
                    "message": f"Error reading test file: {str(e)}"
                })


def main():
    """Main entry point for the snapshot generator."""
    parser = argparse.ArgumentParser(
        description="GitBridge Code Snapshot Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                            # Generate snapshot to gitbridge_code_snapshot.json
  %(prog)s -o custom_snapshot.json    # Save to custom file
  %(prog)s -d /path/to/project        # Analyze specific directory
  %(prog)s --no-color                 # Disable colored output
  %(prog)s --verbose                  # Show detailed progress
  
Phase Marker Formats:
  # GBP13: Implementation description
  # GitBridge Phase 13: Implementation description
  # GBP13 → GBP14: Phase transition description
  def gbp13_function_name():  # Function-based marker
"""
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: gitbridge_code_snapshot.json)",
        default="gitbridge_code_snapshot.json"
    )
    parser.add_argument(
        "-d", "--directory",
        help="Root directory to analyze (default: current directory)",
        default="."
    )
    parser.add_argument(
        "--no-color",
        help="Disable colored output",
        action="store_true"
    )
    parser.add_argument(
        "-v", "--verbose",
        help="Show detailed progress",
        action="store_true"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    args = parser.parse_args()
    
    try:
        generator = CodeSnapshotGenerator(args.directory)
        generator.generate_snapshot()
        generator.save_snapshot(args.output)
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 