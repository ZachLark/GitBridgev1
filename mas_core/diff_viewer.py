#!/usr/bin/env python3
"""
GitBridge Diff Viewer Component
Phase: GBP24
Part: P24P2
Step: P24P2S2
Task: P24P2S2T1 - Diff Viewer Implementation

Build inline visual for what changed between versions.
Implements MAS Lite Protocol v2.1 diff visualization requirements.

Author: GitBridge Development Team
Date: 2025-06-20
Schema: [P24P2 Schema]
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import os
import sys
from difflib import unified_diff, SequenceMatcher, ndiff
import re

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .changelog import ChangelogManager, ChangeType
from .utils.logging import MASLogger

logger = MASLogger(__name__)

@dataclass
class DiffLine:
    """Represents a line in a diff."""
    line_number: int
    content: str
    line_type: str  # 'added', 'removed', 'unchanged', 'context'
    original_line_number: Optional[int] = None
    new_line_number: Optional[int] = None

@dataclass
class DiffBlock:
    """Represents a block of changes in a diff."""
    block_id: str
    start_line: int
    end_line: int
    lines: List[DiffLine]
    change_type: str  # 'addition', 'deletion', 'modification', 'context'
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DiffResult:
    """Complete diff result."""
    file_path: str
    old_content: Optional[str]
    new_content: Optional[str]
    blocks: List[DiffBlock]
    summary: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

class DiffViewer:
    """
    Provides inline visual representation of changes between versions.
    
    Phase: GBP24
    Part: P24P2
    Step: P24P2S2
    Task: P24P2S2T1 - Core Implementation
    
    Features:
    - Generate unified diffs
    - Highlight changes inline
    - Provide side-by-side comparison
    - Support multiple output formats
    - Calculate change statistics
    """
    
    def __init__(self, changelog_manager: Optional[ChangelogManager] = None):
        """
        Initialize the diff viewer.
        
        Args:
            changelog_manager: Optional changelog manager for revision data
        """
        self.changelog_manager = changelog_manager
        self.line_types = {
            '+': 'added',
            '-': 'removed',
            ' ': 'unchanged',
            '?': 'context'
        }
        
        logger.info("[P24P2S2T1] DiffViewer initialized")
    
    def generate_diff(
        self,
        old_content: Optional[str],
        new_content: Optional[str],
        file_path: str,
        context_lines: int = 3
    ) -> DiffResult:
        """
        Generate a diff between old and new content.
        
        Args:
            old_content: Old content (None for new files)
            new_content: New content (None for deleted files)
            file_path: File path for context
            context_lines: Number of context lines to include
            
        Returns:
            DiffResult: Complete diff result
        """
        # Handle special cases
        if old_content is None and new_content is None:
            return self._create_empty_diff(file_path)
        elif old_content is None:
            return self._create_addition_diff(new_content, file_path)
        elif new_content is None:
            return self._create_deletion_diff(old_content, file_path)
        
        # Generate unified diff
        diff_lines = list(unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
            n=context_lines
        ))
        
        # Parse diff lines into blocks
        blocks = self._parse_diff_blocks(diff_lines, context_lines)
        
        # Calculate summary statistics
        summary = self._calculate_diff_summary(blocks, old_content, new_content)
        
        return DiffResult(
            file_path=file_path,
            old_content=old_content,
            new_content=new_content,
            blocks=blocks,
            summary=summary
        )
    
    def _create_empty_diff(self, file_path: str) -> DiffResult:
        """Create diff for empty comparison."""
        return DiffResult(
            file_path=file_path,
            old_content=None,
            new_content=None,
            blocks=[],
            summary={
                "total_lines": 0,
                "added_lines": 0,
                "removed_lines": 0,
                "unchanged_lines": 0,
                "change_percentage": 0.0,
                "change_type": "none"
            }
        )
    
    def _create_addition_diff(self, new_content: str, file_path: str) -> DiffResult:
        """Create diff for file addition."""
        lines = new_content.splitlines()
        diff_lines = []
        
        # Add header
        diff_lines.append(f"--- a/{file_path}")
        diff_lines.append(f"+++ b/{file_path}")
        diff_lines.append("@@ -0,0 +1," + str(len(lines)) + " @@")
        
        # Add all lines as additions
        for i, line in enumerate(lines, 1):
            diff_lines.append(f"+{line}")
        
        blocks = self._parse_diff_blocks(diff_lines, 0)
        summary = {
            "total_lines": len(lines),
            "added_lines": len(lines),
            "removed_lines": 0,
            "unchanged_lines": 0,
            "change_percentage": 100.0,
            "change_type": "addition"
        }
        
        return DiffResult(
            file_path=file_path,
            old_content=None,
            new_content=new_content,
            blocks=blocks,
            summary=summary
        )
    
    def _create_deletion_diff(self, old_content: str, file_path: str) -> DiffResult:
        """Create diff for file deletion."""
        lines = old_content.splitlines()
        diff_lines = []
        
        # Add header
        diff_lines.append(f"--- a/{file_path}")
        diff_lines.append(f"+++ b/{file_path}")
        diff_lines.append("@@ -1," + str(len(lines)) + " +0,0 @@")
        
        # Add all lines as deletions
        for i, line in enumerate(lines, 1):
            diff_lines.append(f"-{line}")
        
        blocks = self._parse_diff_blocks(diff_lines, 0)
        summary = {
            "total_lines": len(lines),
            "added_lines": 0,
            "removed_lines": len(lines),
            "unchanged_lines": 0,
            "change_percentage": 100.0,
            "change_type": "deletion"
        }
        
        return DiffResult(
            file_path=file_path,
            old_content=old_content,
            new_content=None,
            blocks=blocks,
            summary=summary
        )
    
    def _parse_diff_blocks(self, diff_lines: List[str], context_lines: int) -> List[DiffBlock]:
        """Parse diff lines into structured blocks."""
        blocks = []
        current_block_lines = []
        current_block_type = None
        block_id = 0
        
        for line in diff_lines:
            if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
                # Save current block if it exists
                if current_block_lines:
                    blocks.append(DiffBlock(
                        block_id=f"block_{block_id}",
                        start_line=len(blocks) + 1,
                        end_line=len(blocks) + len(current_block_lines),
                        lines=current_block_lines,
                        change_type=current_block_type or 'context'
                    ))
                    block_id += 1
                    current_block_lines = []
                    current_block_type = None
                
                # Skip header lines
                continue
            
            # Parse line type
            line_type = 'unchanged'
            if line.startswith('+'):
                line_type = 'added'
                current_block_type = 'addition' if current_block_type != 'modification' else 'modification'
            elif line.startswith('-'):
                line_type = 'removed'
                current_block_type = 'deletion' if current_block_type != 'modification' else 'modification'
            elif line.startswith(' '):
                line_type = 'unchanged'
                if current_block_type in ['addition', 'deletion']:
                    current_block_type = 'modification'
            
            # Create diff line
            diff_line = DiffLine(
                line_number=len(current_block_lines) + 1,
                content=line[1:] if line.startswith(('+', '-', ' ')) else line,
                line_type=line_type
            )
            
            current_block_lines.append(diff_line)
        
        # Add final block
        if current_block_lines:
            blocks.append(DiffBlock(
                block_id=f"block_{block_id}",
                start_line=len(blocks) + 1,
                end_line=len(blocks) + len(current_block_lines),
                lines=current_block_lines,
                change_type=current_block_type or 'context'
            ))
        
        return blocks
    
    def _calculate_diff_summary(self, blocks: List[DiffBlock], old_content: Optional[str], new_content: Optional[str]) -> Dict[str, Any]:
        """Calculate summary statistics for the diff."""
        total_lines = 0
        added_lines = 0
        removed_lines = 0
        unchanged_lines = 0
        
        for block in blocks:
            for line in block.lines:
                total_lines += 1
                if line.line_type == 'added':
                    added_lines += 1
                elif line.line_type == 'removed':
                    removed_lines += 1
                elif line.line_type == 'unchanged':
                    unchanged_lines += 1
        
        # Calculate change percentage
        old_line_count = len(old_content.splitlines()) if old_content else 0
        new_line_count = len(new_content.splitlines()) if new_content else 0
        max_lines = max(old_line_count, new_line_count)
        change_percentage = (added_lines + removed_lines) / max_lines * 100 if max_lines > 0 else 0
        
        # Determine change type
        if added_lines > 0 and removed_lines == 0:
            change_type = "addition"
        elif removed_lines > 0 and added_lines == 0:
            change_type = "deletion"
        elif added_lines > 0 and removed_lines > 0:
            change_type = "modification"
        else:
            change_type = "none"
        
        return {
            "total_lines": total_lines,
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "unchanged_lines": unchanged_lines,
            "change_percentage": change_percentage,
            "change_type": change_type,
            "old_line_count": old_line_count,
            "new_line_count": new_line_count
        }
    
    def render_diff(self, diff_result: DiffResult, format_type: str = "html") -> str:
        """
        Render diff result in specified format.
        
        Args:
            diff_result: Diff result to render
            format_type: Output format ("html", "markdown", "json", "side_by_side")
            
        Returns:
            str: Rendered diff
        """
        if format_type == "html":
            return self._render_html_diff(diff_result)
        elif format_type == "markdown":
            return self._render_markdown_diff(diff_result)
        elif format_type == "json":
            return self._render_json_diff(diff_result)
        elif format_type == "side_by_side":
            return self._render_side_by_side_diff(diff_result)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def _render_html_diff(self, diff_result: DiffResult) -> str:
        """Render diff in HTML format."""
        html = f"""
        <div class="diff-container" data-file-path="{diff_result.file_path}">
            <div class="diff-header">
                <h3>📄 {diff_result.file_path}</h3>
                <div class="diff-summary">
                    <span class="summary-item added">+{diff_result.summary['added_lines']}</span>
                    <span class="summary-item removed">-{diff_result.summary['removed_lines']}</span>
                    <span class="summary-item unchanged">{diff_result.summary['unchanged_lines']}</span>
                    <span class="summary-item percentage">{diff_result.summary['change_percentage']:.1f}% changed</span>
                </div>
            </div>
            
            <div class="diff-content">
        """
        
        for block in diff_result.blocks:
            html += f"""
                <div class="diff-block {block.change_type}" data-block-id="{block.block_id}">
                    <div class="block-header">
                        <span class="block-type">{block.change_type.title()}</span>
                        <span class="block-lines">Lines {block.start_line}-{block.end_line}</span>
                    </div>
                    <div class="block-content">
            """
            
            for line in block.lines:
                line_class = f"diff-line {line.line_type}"
                line_icon = self._get_line_icon(line.line_type)
                
                html += f"""
                        <div class="{line_class}">
                            <span class="line-icon">{line_icon}</span>
                            <span class="line-number">{line.line_number:4d}</span>
                            <span class="line-content">{self._escape_html(line.content)}</span>
                        </div>
                """
            
            html += """
                    </div>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _render_markdown_diff(self, diff_result: DiffResult) -> str:
        """Render diff in Markdown format."""
        markdown = f"# Diff: {diff_result.file_path}\n\n"
        
        # Summary
        summary = diff_result.summary
        markdown += f"**Summary:** +{summary['added_lines']} -{summary['removed_lines']} ~{summary['unchanged_lines']} ({summary['change_percentage']:.1f}% changed)\n\n"
        
        # Diff blocks
        for block in diff_result.blocks:
            markdown += f"## {block.change_type.title()} (Lines {block.start_line}-{block.end_line})\n\n"
            
            for line in block.lines:
                line_icon = self._get_line_icon(line.line_type)
                markdown += f"{line_icon} {line.content}\n"
            
            markdown += "\n"
        
        return markdown
    
    def _render_json_diff(self, diff_result: DiffResult) -> str:
        """Render diff in JSON format."""
        json_data = {
            "file_path": diff_result.file_path,
            "summary": diff_result.summary,
            "blocks": []
        }
        
        for block in diff_result.blocks:
            block_data = {
                "block_id": block.block_id,
                "change_type": block.change_type,
                "start_line": block.start_line,
                "end_line": block.end_line,
                "lines": []
            }
            
            for line in block.lines:
                line_data = {
                    "line_number": line.line_number,
                    "content": line.content,
                    "line_type": line.line_type
                }
                block_data["lines"].append(line_data)
            
            json_data["blocks"].append(block_data)
        
        return json.dumps(json_data, indent=2)
    
    def _render_side_by_side_diff(self, diff_result: DiffResult) -> str:
        """Render diff in side-by-side format."""
        if not diff_result.old_content or not diff_result.new_content:
            return self._render_html_diff(diff_result)  # Fallback to regular diff
        
        old_lines = diff_result.old_content.splitlines()
        new_lines = diff_result.new_content.splitlines()
        
        html = f"""
        <div class="side-by-side-diff" data-file-path="{diff_result.file_path}">
            <div class="diff-header">
                <h3>📄 {diff_result.file_path}</h3>
                <div class="diff-summary">
                    <span class="summary-item added">+{diff_result.summary['added_lines']}</span>
                    <span class="summary-item removed">-{diff_result.summary['removed_lines']}</span>
                    <span class="summary-item unchanged">{diff_result.summary['unchanged_lines']}</span>
                </div>
            </div>
            
            <div class="diff-panels">
                <div class="diff-panel old">
                    <div class="panel-header">Original</div>
                    <div class="panel-content">
        """
        
        # Generate side-by-side comparison
        matcher = SequenceMatcher(None, old_lines, new_lines)
        old_line_num = 1
        new_line_num = 1
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Unchanged lines
                for k in range(i1, i2):
                    html += f"""
                        <div class="diff-line unchanged">
                            <span class="line-number old">{old_line_num:4d}</span>
                            <span class="line-content old">{self._escape_html(old_lines[k])}</span>
                            <span class="line-number new">{new_line_num:4d}</span>
                            <span class="line-content new">{self._escape_html(new_lines[j1 + k - i1])}</span>
                        </div>
                    """
                    old_line_num += 1
                    new_line_num += 1
            
            elif tag == 'replace':
                # Modified lines
                for k in range(i1, i2):
                    html += f"""
                        <div class="diff-line removed">
                            <span class="line-number old">{old_line_num:4d}</span>
                            <span class="line-content old">{self._escape_html(old_lines[k])}</span>
                            <span class="line-number new"></span>
                            <span class="line-content new"></span>
                        </div>
                    """
                    old_line_num += 1
                
                for k in range(j1, j2):
                    html += f"""
                        <div class="diff-line added">
                            <span class="line-number old"></span>
                            <span class="line-content old"></span>
                            <span class="line-number new">{new_line_num:4d}</span>
                            <span class="line-content new">{self._escape_html(new_lines[k])}</span>
                        </div>
                    """
                    new_line_num += 1
            
            elif tag == 'delete':
                # Deleted lines
                for k in range(i1, i2):
                    html += f"""
                        <div class="diff-line removed">
                            <span class="line-number old">{old_line_num:4d}</span>
                            <span class="line-content old">{self._escape_html(old_lines[k])}</span>
                            <span class="line-number new"></span>
                            <span class="line-content new"></span>
                        </div>
                    """
                    old_line_num += 1
            
            elif tag == 'insert':
                # Added lines
                for k in range(j1, j2):
                    html += f"""
                        <div class="diff-line added">
                            <span class="line-number old"></span>
                            <span class="line-content old"></span>
                            <span class="line-number new">{new_line_num:4d}</span>
                            <span class="line-content new">{self._escape_html(new_lines[k])}</span>
                        </div>
                    """
                    new_line_num += 1
        
        html += """
                    </div>
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _get_line_icon(self, line_type: str) -> str:
        """Get icon for line type."""
        icons = {
            'added': '➕',
            'removed': '➖',
            'unchanged': ' ',
            'context': ' '
        }
        return icons.get(line_type, ' ')
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
    
    def generate_css_styles(self) -> str:
        """Generate CSS styles for diff viewer."""
        css = """
        .diff-container {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin: 16px 0;
            background: white;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.4;
        }
        
        .diff-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
            border-radius: 8px 8px 0 0;
        }
        
        .diff-header h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: #111827;
        }
        
        .diff-summary {
            display: flex;
            gap: 8px;
            font-size: 12px;
        }
        
        .summary-item {
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 500;
        }
        
        .summary-item.added {
            background: #dcfce7;
            color: #166534;
        }
        
        .summary-item.removed {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .summary-item.unchanged {
            background: #f3f4f6;
            color: #6b7280;
        }
        
        .summary-item.percentage {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .diff-content {
            padding: 0;
        }
        
        .diff-block {
            border-bottom: 1px solid #f3f4f6;
        }
        
        .diff-block:last-child {
            border-bottom: none;
        }
        
        .block-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 16px;
            background: #f9fafb;
            font-size: 12px;
            color: #6b7280;
        }
        
        .block-type {
            font-weight: 500;
            text-transform: uppercase;
        }
        
        .block-content {
            padding: 0;
        }
        
        .diff-line {
            display: flex;
            align-items: center;
            padding: 2px 16px;
            border-bottom: 1px solid #f9fafb;
        }
        
        .diff-line:last-child {
            border-bottom: none;
        }
        
        .diff-line.added {
            background: #f0fdf4;
        }
        
        .diff-line.removed {
            background: #fef2f2;
        }
        
        .diff-line.unchanged {
            background: white;
        }
        
        .line-icon {
            width: 20px;
            text-align: center;
            font-size: 12px;
            color: #6b7280;
        }
        
        .line-number {
            width: 50px;
            text-align: right;
            padding-right: 12px;
            color: #9ca3af;
            font-size: 11px;
            user-select: none;
        }
        
        .line-content {
            flex: 1;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .diff-line.added .line-content {
            color: #166534;
        }
        
        .diff-line.removed .line-content {
            color: #991b1b;
            text-decoration: line-through;
        }
        
        .diff-line.unchanged .line-content {
            color: #374151;
        }
        
        /* Side-by-side diff styles */
        .side-by-side-diff {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin: 16px 0;
            background: white;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.4;
        }
        
        .diff-panels {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
        }
        
        .diff-panel {
            border-right: 1px solid #e5e7eb;
        }
        
        .diff-panel:last-child {
            border-right: none;
        }
        
        .panel-header {
            padding: 8px 16px;
            background: #f3f4f6;
            font-size: 12px;
            font-weight: 500;
            color: #6b7280;
            text-align: center;
        }
        
        .panel-content {
            padding: 0;
        }
        
        .side-by-side-diff .diff-line {
            display: grid;
            grid-template-columns: 50px 1fr 50px 1fr;
            gap: 0;
            padding: 2px 0;
        }
        
        .side-by-side-diff .line-number.old {
            text-align: right;
            padding-right: 8px;
            background: #f9fafb;
        }
        
        .side-by-side-diff .line-content.old {
            padding-left: 8px;
            border-right: 1px solid #e5e7eb;
        }
        
        .side-by-side-diff .line-number.new {
            text-align: right;
            padding-right: 8px;
            background: #f9fafb;
        }
        
        .side-by-side-diff .line-content.new {
            padding-left: 8px;
        }
        """
        
        return css


def main():
    """Main function for testing diff viewer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitBridge Diff Viewer')
    parser.add_argument('--old-file', help='Path to old file')
    parser.add_argument('--new-file', help='Path to new file')
    parser.add_argument('--format', choices=['html', 'markdown', 'json', 'side_by_side'], default='html',
                       help='Output format')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Read file contents
    old_content = None
    new_content = None
    
    if args.old_file and os.path.exists(args.old_file):
        with open(args.old_file, 'r') as f:
            old_content = f.read()
    
    if args.new_file and os.path.exists(args.new_file):
        with open(args.new_file, 'r') as f:
            new_content = f.read()
    
    # Create diff viewer
    diff_viewer = DiffViewer()
    
    # Generate diff
    file_path = args.new_file or args.old_file or "unknown"
    diff_result = diff_viewer.generate_diff(old_content, new_content, file_path)
    
    # Render diff
    result = diff_viewer.render_diff(diff_result, args.format)
    
    # Output result
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
        print(f"Diff rendered to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main() 