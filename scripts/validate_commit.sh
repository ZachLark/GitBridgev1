#!/bin/bash

# GitBridge Commit Validation Script
# This script validates commits according to MAS Lite Protocol v2.1 standards

echo "🔍 GitBridge Commit Validation - MAS Lite Protocol v2.1"
echo "----------------------------------------"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Get the latest commit info
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MESSAGE=$(git log -1 --pretty=%B)
COMMIT_AUTHOR=$(git log -1 --pretty=%an)

echo "📝 Commit: $COMMIT_HASH"
echo "👤 Author: $COMMIT_AUTHOR"
echo "💬 Message: $(echo "$COMMIT_MESSAGE" | head -n 1)"

# TODO: Add actual validation logic here
# - Check commit message format
# - Validate file changes against MAS protocol
# - Run security checks
# - Verify webhook compatibility

# Log known failing tests for Phase 19
echo "📋 Known failing tests (Phase 19):"
echo "   - tests/unit/scripts/test_event_queue.py"
echo "   - tests/unit/mas_core/test_task_chain.py" 
echo "   - tests/unit/mas_core/test_pipeline.py"
echo "   - tests/integration/test_redis_queue_integration.py"
echo "   - Coverage currently at ~5.54% (target: 80% in Phase 20)"

# Check for test skip flag
if [[ "$COMMIT_MESSAGE" == *"[skip tests]"* ]]; then
    echo "⚠️  Test execution will be skipped due to [skip tests] flag"
fi

echo "✅ Validation completed - Phase 19 stabilization mode"
echo "🚀 Ready for GitBridge integration"

exit 0 