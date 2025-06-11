# 🔍 GitBridge Code Snapshot Generator

A powerful code analysis tool that generates a comprehensive JSON snapshot of the GitBridge codebase, focusing on GitBridge Phase (GBP) tracking, test coverage, and structural analysis.

## Features

- **Phase Detection & Tracking**
  - Identifies GBP markers in comments and function names
  - Tracks phase transitions (e.g., `GBP13 → GBP14`)
  - Detects malformed phase markers
  - Reports skipped phase transitions

- **Test Coverage Analysis**
  - Identifies unlinked test files
  - Maps tests to GBP components
  - Tracks test file distribution
  - Reports test coverage gaps

- **Code Structure Analysis**
  - Extracts function and class definitions
  - Analyzes markdown documentation structure
  - Identifies roadmap references
  - Generates SHA-256 file hashes

- **Warning System**
  - Reports malformed phase markers
  - Flags large files (>5MB)
  - Identifies encoding issues
  - Detects skipped phase transitions

## Usage

### Basic Usage

From your GitBridge project root:

```bash
python3 scripts/gitbridge_audit_snapshot.py
```

This will generate `gitbridge_code_snapshot.json` in your current directory.

### Output to File

To save the output to a specific file:

```bash
python3 scripts/gitbridge_audit_snapshot.py > custom_snapshot.json
```

## Output Format

The snapshot is generated in JSON format with the following structure:

```json
{
  "metadata": {
    "generated_at": "ISO-8601 timestamp",
    "root_directory": "absolute path",
    "version": "2.1.0"
  },
  "files": [
    {
      "file_path": "path/to/file",
      "sha256": "file hash",
      "top_comments": ["comment1", "comment2"],
      "functions": ["function1", "function2"],
      "classes": ["class1", "class2"],
      "phases_detected": [13, 14, 15],
      "is_test_file": true/false
    }
  ],
  "phase_transitions": [
    {
      "file": "path/to/file",
      "line": 42,
      "from_phase": 13,
      "to_phase": 14
    }
  ],
  "unlinked_tests": [
    {
      "file": "path/to/test",
      "message": "Test file doesn't reference any known GBP components"
    }
  ],
  "warnings": [
    {
      "file": "path/to/file",
      "type": "warning_type",
      "message": "Warning description",
      "line": 42
    }
  ]
}
```

## Phase Marker Format

The tool recognizes the following phase marker formats:

```python
# GBP13: Implementation description
# GitBridge Phase 13: Implementation description
# GBP13 → GBP14: Phase transition description
def gbp13_function_name():  # Function-based marker
```

## Markdown Analysis

For `.md` files, the tool analyzes:

- Heading structure and hierarchy
- Roadmap references to GBP phases
- Phase transition documentation
- Implementation status markers

## Warning Types

- `malformed_phase`: Invalid phase marker format
- `phase_gap`: Skipped phase in transition
- `markdown_parse_error`: Error parsing markdown structure
- `file_size`: File exceeds size limit (5MB)
- `encoding`: Non-UTF8 or binary file
- `read_error`: File read/access error

## Requirements

- Python 3.13.3 or higher
- UTF-8 file encoding support
- Read access to GitBridge codebase

## Contributing

When adding new features to the snapshot generator:

1. Follow the existing code structure
2. Add appropriate test cases
3. Update this documentation
4. Include docstrings and type hints
5. Follow MAS Lite Protocol v2.1 specifications 