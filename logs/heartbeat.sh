#!/bin/bash

# Heartbeat Monitor for Cursor's Test Coverage Loop
while true; do
  # Set defaults if environment variables are not set
  TASK_NAME=${CURRENT_TASK_NAME:-"initializing"}
  TASK_COVERAGE=${CURRENT_TASK_COVERAGE:-"0"}
  
  # Try to read from status file if it exists
  if [ -f "logs/current_status.env" ]; then
    source logs/current_status.env
    TASK_NAME=${CURRENT_TASK_NAME:-$TASK_NAME}
    TASK_COVERAGE=${CURRENT_TASK_COVERAGE:-$TASK_COVERAGE}
  fi
  
  echo "[`date`] Running: $TASK_NAME – Coverage: $TASK_COVERAGE%" > logs/cursor_live_status.log
  sleep 60
done 