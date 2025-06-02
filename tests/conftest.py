"""GitBridgev1 Test Configuration."""

import os
import pytest
import logging
from pathlib import Path
from typing import Generator

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(tmp_path_factory) -> Generator:
    """Set up test environment."""
    # Create test directories
    test_root = tmp_path_factory.mktemp("gitbridge_test")
    (test_root / "logs").mkdir()
    (test_root / "messages").mkdir()
    (test_root / "tasks").mkdir()
    
    # Configure test logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(test_root / "logs/test.log"),
            logging.StreamHandler()
        ]
    )
    
    # Set environment variables for testing
    os.environ["GITBRIDGE_TEST"] = "1"
    os.environ["GITBRIDGE_TEST_ROOT"] = str(test_root)
    
    yield test_root
    
    # Cleanup (if needed)
    # Note: tmp_path_factory handles cleanup automatically

@pytest.fixture
def test_logger():
    """Create a test logger."""
    return logging.getLogger("gitbridge.test") 