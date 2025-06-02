#!/bin/bash
export PYTHONPATH=$(pwd)
source venv/bin/activate

# Run tests with:
# - Verbose output (-v)
# - Show local variables in tracebacks (-l)
# - Exit on first failure (-x)
# - Show stdout/stderr (-s)
# - Show test durations (--durations=10)
python -m pytest tests/unit/mas_core/test_redis_queue.py -v -l -x -s --durations=10 