#!/usr/bin/env python3
"""Advanced security validation testing suite for GitBridge."""

import pytest
import json
import jwt
import secrets
import re
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

from generate_task_chain import TaskParams, generate_single_task
from mas_delegate import load_and_validate_task

def test_jwt_token_validation():
    """Test JWT token validation and expiration."""
    secret_key = secrets.token_hex(32)
    
    # Valid token
    valid_token = jwt.encode(
        {
            'task_id': 'valid_task',
            'exp': datetime.utcnow() + timedelta(hours=1)
        },
        secret_key,
        algorithm='HS256'
    )
    
    # Expired token
    expired_token = jwt.encode(
        {
            'task_id': 'expired_task',
            'exp': datetime.utcnow() - timedelta(hours=1)
        },
        secret_key,
        algorithm='HS256'
    )
    
    # Test token validation
    params = TaskParams(
        phase_id="P8SEC",
        task_counter=1,
        description="Token test"
    )
    task = generate_single_task(params)
    
    # Test with valid token
    task['auth_token'] = valid_token
    test_log = Path("test_token.json")
    with test_log.open('w') as f:
        json.dump([task], f)
    load_and_validate_task(test_log)
    
    # Test with expired token
    task['auth_token'] = expired_token
    with pytest.raises(ValueError):
        with test_log.open('w') as f:
            json.dump([task], f)
        load_and_validate_task(test_log)
    
    test_log.unlink()

def test_rate_limiting():
    """Test rate limiting protection."""
    requests = []
    start_time = datetime.now()
    
    # Generate rapid requests
    for i in range(100):
        params = TaskParams(
            phase_id="P8SEC",
            task_counter=i,
            description=f"Rate limit test {i}"
        )
        task = generate_single_task(params)
        requests.append({
            'task': task,
            'timestamp': start_time + timedelta(milliseconds=i*10)
        })
    
    # Test rate limiting
    allowed_requests = 0
    window_start = start_time
    window_size = timedelta(seconds=1)
    rate_limit = 50  # requests per second
    
    for req in requests:
        window_end = req['timestamp']
        if window_end - window_start > window_size:
            allowed_requests = 0
            window_start = window_end
        
        if allowed_requests < rate_limit:
            allowed_requests += 1
        else:
            with pytest.raises(ValueError):
                test_log = Path("test_ratelimit.json")
                with test_log.open('w') as f:
                    json.dump([req['task']], f)
                load_and_validate_task(test_log)
                test_log.unlink()

def test_regex_validation():
    """Test regex pattern validation and protection."""
    malicious_patterns = [
        r"(a+){10,}",  # ReDoS pattern
        r"([a-zA-Z]+)*",  # Catastrophic backtracking
        r"^(([a-z])+.)+[A-Z]([a-z])+$",  # Complex pattern
        r"(a|a|a|a|a|a|a|a|a|a)*",  # Multiple alternations
        r"(.*a){10}"  # Repeated wildcards
    ]
    
    for pattern in malicious_patterns:
        params = TaskParams(
            phase_id="P8SEC",
            task_counter=1,
            description="Regex test"
        )
        task = generate_single_task(params)
        task['pattern'] = pattern
        
        with pytest.raises(ValueError):
            test_log = Path("test_regex.json")
            with test_log.open('w') as f:
                json.dump([task], f)
            load_and_validate_task(test_log)
            test_log.unlink()

def test_unicode_security():
    """Test Unicode security and normalization."""
    unicode_attacks = [
        "admin\u202Eresume.exe",  # Bidirectional override
        "data\uFE00\uFE01",  # Variation selectors
        "user\u200Bname",  # Zero-width space
        "pass\uFEFFword",  # Byte order mark
        "script\u2028alert(1)"  # Line separator
    ]
    
    for attack in unicode_attacks:
        params = TaskParams(
            phase_id="P8SEC",
            task_counter=1,
            description=attack
        )
        
        with pytest.raises(ValueError):
            task = generate_single_task(params)
            test_log = Path("test_unicode.json")
            with test_log.open('w') as f:
                json.dump([task], f)
            load_and_validate_task(test_log)
            test_log.unlink()

def test_template_injection():
    """Test template injection prevention."""
    injection_attempts = [
        "{{7*7}}",
        "${7*7}",
        "#{7*7}",
        "{%print(7*7)%}",
        "<% Response.Write(7*7) %>",
        "${{7*7}}",
        "@(7*7)",
        "#{session.eval('7*7')}",
        "${session.getClass().forName('java.lang.Runtime')}"
    ]
    
    for injection in injection_attempts:
        params = TaskParams(
            phase_id="P8SEC",
            task_counter=1,
            description=injection
        )
        
        with pytest.raises(ValueError):
            task = generate_single_task(params)
            test_log = Path("test_template.json")
            with test_log.open('w') as f:
                json.dump([task], f)
            load_and_validate_task(test_log)
            test_log.unlink()

def test_serialization_security():
    """Test serialization security and validation."""
    malicious_serialized = [
        b'\x80\x04\x95\x1a\x00\x00\x00\x00\x00\x00\x00\x8c\x08builtins\x8c\x07__import__\x93\x94\x8c\x02os\x94\x85\x94R\x94.',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\xf0\x00\x00',
        '{"__class__": "subprocess.Popen", "args": ["rm", "-rf", "/"]}',
        '{"$type": "System.Diagnostics.Process"}',
        '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
    ]
    
    for data in malicious_serialized:
        params = TaskParams(
            phase_id="P8SEC",
            task_counter=1,
            description="Serialization test"
        )
        task = generate_single_task(params)
        task['serialized_data'] = data
        
        with pytest.raises(ValueError):
            test_log = Path("test_serialization.json")
            with test_log.open('w') as f:
                json.dump([task], f)
            load_and_validate_task(test_log)
            test_log.unlink()

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 