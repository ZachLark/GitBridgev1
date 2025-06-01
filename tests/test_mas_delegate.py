import unittest
import json
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import mas_delegate
import requests


class TestLoadAndValidateTask(unittest.TestCase):
    def setUp(self):
        # Create a valid base template
        self.valid = {
            "task_id": "a" * 64,
            "description": "Do something important",
            "assignee": "alice",
            "max_cycles": 5,
            "token_budget": 1000,
        }
        self.tmpdir = tempfile.TemporaryDirectory()
        self.dirpath = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def write_json(self, data):
        path = self.dirpath / "task.json"
        path.write_text(json.dumps(data))
        return path

    def test_valid_template(self):
        path = self.write_json(self.valid)
        out = mas_delegate.load_and_validate_task(path)
        self.assertEqual(out, self.valid)

    def test_missing_fields(self):
        for field in ["task_id", "description", "assignee", "max_cycles", "token_budget"]:
            data = dict(self.valid)
            del data[field]
            path = self.write_json(data)
            with self.assertRaises(ValueError) as cm:
                mas_delegate.load_and_validate_task(path)
            self.assertIn(f"Missing required field: {field}", str(cm.exception))

    def test_invalid_task_id(self):
        # wrong length
        data = dict(self.valid)
        data["task_id"] = "abc123"
        path = self.write_json(data)
        with self.assertRaises(ValueError):
            mas_delegate.load_and_validate_task(path)
        # non-hex characters
        data["task_id"] = "g" * 64
        path = self.write_json(data)
        with self.assertRaises(ValueError):
            mas_delegate.load_and_validate_task(path)

    def test_empty_description_or_assignee(self):
        for field in ["description", "assignee"]:
            data = dict(self.valid)
            data[field] = "   "
            path = self.write_json(data)
            with self.assertRaises(ValueError):
                mas_delegate.load_and_validate_task(path)

    def test_nonpositive_integers(self):
        for field in ["max_cycles", "token_budget"]:
            data = dict(self.valid)
            data[field] = 0
            path = self.write_json(data)
            with self.assertRaises(ValueError):
                mas_delegate.load_and_validate_task(path)
            data[field] = -1
            path = self.write_json(data)
            with self.assertRaises(ValueError):
                mas_delegate.load_and_validate_task(path)


class TestDelegateTask(unittest.TestCase):
    def setUp(self):
        self.task = {"foo": "bar"}

    @patch("mas_delegate.requests.post")
    def test_successful_delegate(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        result = mas_delegate.delegate_task(self.task, "http://api.example.com/")
        self.assertEqual(result, {"ok": True})
        mock_post.assert_called_once()

    @patch("mas_delegate.requests.post")
    def test_http_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("Bad request")
        mock_post.return_value = mock_resp

        with self.assertRaises(RuntimeError) as cm:
            mas_delegate.delegate_task(self.task, "http://api.example.com")
        self.assertIn("HTTP error occurred", str(cm.exception))

    @patch("mas_delegate.requests.post")
    def test_timeout(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout("timed out")
        with self.assertRaises(RuntimeError) as cm:
            mas_delegate.delegate_task(self.task, "http://api.example.com")
        self.assertIn("Request timed out", str(cm.exception))


class TestLogTask(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmpdir.name) / "task_log.json"

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_append_and_atomic(self):
        # First entry
        entry1 = {
            "task_id": "f" * 64,
            "assignee": "bob",
            "max_cycles": 3,
            "token_budget": 500,
            "cycle_count": 1,
        }
        mas_delegate.log_task(entry1, self.log_path)

        # Second entry
        entry2 = dict(entry1)
        entry2["cycle_count"] = 2
        mas_delegate.log_task(entry2, self.log_path)

        # Read back lines
        lines = self.log_path.read_text().strip().splitlines()
        self.assertEqual(len(lines), 2)

        rec1 = json.loads(lines[0])
        rec2 = json.loads(lines[1])

        # Check fields
        self.assertEqual(rec1["task_id"], entry1["task_id"])
        self.assertEqual(rec1["assignee"], entry1["assignee"])
        self.assertEqual(rec1["max_cycles"], entry1["max_cycles"])
        self.assertEqual(rec1["token_budget"], entry1["token_budget"])
        self.assertEqual(rec1["cycle_count"], entry1["cycle_count"])
        # timestamp present and parseable
        datetime.fromisoformat(rec1["timestamp"])

        self.assertEqual(rec2["cycle_count"], entry2["cycle_count"])
        datetime.fromisoformat(rec2["timestamp"])

class TestMainWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.dirpath = Path(self.tmpdir.name)
        # sample task template
        self.template = {
            "task_id": "b" * 64,
            "description": "Draft Developer Guide Section 3",
            "assignee": "charlie",
            "max_cycles": 2,
            "token_budget": 200,
        }
        self.task_file = self.dirpath / "task_template.json"
        self.task_file.write_text(json.dumps(self.template))
        self.log_file = self.dirpath / "task_log.json"

    def tearDown(self):
        self.tmpdir.cleanup()

    @patch("mas_delegate.requests.post")
    def test_end_to_end_main(self, mock_post):
        # Mock API response: echo back fields plus cycle_count
        api_resp = dict(self.template, **{"cycle_count": 1})
        mock_resp = MagicMock()
        mock_resp.json.return_value = api_resp
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        # Patch argv and run main
        test_argv = [
            "mas_delegate.py",
            "--task-file", str(self.task_file),
            "--api-url", "http://api.test",
            "--log-file", str(self.log_file),
        ]
        with patch.object(sys, "argv", test_argv):
            with self.assertRaises(SystemExit) as cm:
                mas_delegate.main()
            # Expect exit code 0
            self.assertEqual(cm.exception.code, 0)

        # Check log file content
        lines = self.log_file.read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["task_id"], self.template["task_id"])
        self.assertEqual(rec["assignee"], self.template["assignee"])
        self.assertEqual(rec["max_cycles"], self.template["max_cycles"])
        self.assertEqual(rec["token_budget"], self.template["token_budget"])
        self.assertEqual(rec["cycle_count"], api_resp["cycle_count"])
        # timestamp parseable
        datetime.fromisoformat(rec["timestamp"])


if __name__ == "__main__":
    unittest.main()