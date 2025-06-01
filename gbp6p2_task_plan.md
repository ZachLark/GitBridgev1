# Task Plan: Develop mas_delegate.py for GitBridge (GBP6P2)

## Observations
- No existing HTTP client patterns or utilities in the project.
- Current logging is to stdout with no structured format.
- No testing framework in use; tests need to be implemented from scratch.
- Input task JSON files need validation per MAS Lite Protocol v2.1 Section III.1.
- API responses need to be logged atomically to avoid corruption.

## Approach
1. **Create `mas_delegate.py`**:
   - Implement `load_and_validate_task(path)` to load and validate task JSON:
     - Validate required fields: `task_id`, `description`, `assignee`, `max_cycles`, `token_budget`.
     - Ensure `task_id` follows SHA256 format (`SHA256:<64-char-hex>`).
     - Validate types: `description` and `assignee` as non-empty strings, `max_cycles` and `token_budget` as positive integers.
   - Implement `delegate_task(task, api_url)` to send the task to the API:
     - Use `requests.post()` with a 60-second timeout.
     - Raise `RuntimeError` on failure.
   - Implement `log_task(record, log_path)` to log tasks atomically:
     - Add ISO8601 timestamp (`datetime.utcnow().isoformat()`).
     - Use `tempfile` for atomic writes to `log_path`.
   - Implement `main()` as the entry point:
     - Use `argparse` for `--task-file`, `--api-url`, `--log-file` (default: `task_log.json`).
     - Call the above functions in sequence.
2. **Set Up Testing**:
   - Create `tests/__init__.py` to make `tests` a Python package.
   - Create `tests/test_mas_delegate.py` with unit tests using `unittest`.

## Files to Create
- `mas_delegate.py`: Main script with the four functions above.
- `tests/__init__.py`: Empty file to make `tests` a package.
- `tests/test_mas_delegate.py`: Unit tests for the script.

## Unit Tests
- **Validation Tests**:
  - Test `load_and_validate_task` with valid and invalid JSON (e.g., missing fields, invalid `task_id`).
- **API Tests**:
  - Mock `requests.post` to test `delegate_task` for success and failure cases.
- **Logging Tests**:
  - Test `log_task` to ensure atomic writes and correct timestamp format.
- **End-to-End Test**:
  - Simulate the full workflow from loading to logging.