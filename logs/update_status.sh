#!/bin/bash

# Helper script to update heartbeat status
# Usage: ./logs/update_status.sh "task_name" "coverage_percentage"

if [ $# -ne 2 ]; then
    echo "Usage: $0 <task_name> <coverage_percentage>"
    echo "Example: $0 'testing_auth_module' '45'"
    exit 1
fi

TASK_NAME="$1"
COVERAGE="$2"

echo "CURRENT_TASK_NAME=\"$TASK_NAME\"" > logs/current_status.env
echo "CURRENT_TASK_COVERAGE=\"$COVERAGE\"" >> logs/current_status.env

echo "Status updated: $TASK_NAME - $COVERAGE%" 