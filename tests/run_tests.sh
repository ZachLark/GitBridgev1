#!/bin/bash

# Set PYTHONPATH to include project root
export PYTHONPATH=$(pwd)

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies if needed
pip install -r requirements.txt
pip install -r requirements-webhook.txt
pip install tox pytest pytest-cov pytest-asyncio fakeredis

# Run tests with tox
tox -e py3

# Run specific integration tests if requested
if [ "$1" == "--integration" ]; then
    pytest tests/integration/test_redis_queue_integration.py -v --cov=scripts/redis_queue --cov-report=html
fi

# Generate coverage report
coverage html 