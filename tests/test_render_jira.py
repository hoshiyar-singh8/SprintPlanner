#!/usr/bin/env python3
"""Tests for render_jira_payload.py hook."""
import json
import os
import sys
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))

import render_jira_payload


class TestRenderJiraPayload(unittest.TestCase):
    def setUp(self):
        self.feature_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.feature_dir)

    def _write_file(self, name, content):
        path = os.path.join(self.feature_dir, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_basic_render(self):
        self._write_file("task_specs.yaml", """
tasks:
  - id: TASK-001
    title: Add config flag
    layer: config
    sp: 1
    depends_on: []
    acceptance_criteria:
      - Flag defined
    execution_mode:
      type: herogen
      rationale: Simple
""")
        self._write_file("feature_input.yaml", """
feature_name: test-feature
detected_platform: ios
labels:
  - test-feature
  - ios
epic_key: PROJ-100
""")

        result = render_jira_payload.render(self.feature_dir)
        self.assertEqual(result, 0)

        payload_path = os.path.join(self.feature_dir, "jira_payload.json")
        self.assertTrue(os.path.exists(payload_path))

        with open(payload_path, "r") as f:
            data = json.load(f)

        self.assertEqual(data["count"], 1)
        ticket = data["tickets"][0]
        self.assertEqual(ticket["task_id"], "TASK-001")
        self.assertIn("[iOS]", ticket["fields"]["summary"])
        self.assertEqual(ticket["fields"]["parent"]["key"], "PROJ-100")

    def test_multiple_tasks(self):
        self._write_file("task_specs.yaml", """
tasks:
  - id: TASK-001
    title: Task A
    layer: config
    sp: 1
    depends_on: []
    acceptance_criteria:
      - Done
    execution_mode:
      type: herogen
      rationale: Simple
  - id: TASK-002
    title: Task B
    layer: api
    sp: 2
    depends_on: [TASK-001]
    acceptance_criteria:
      - Done
    execution_mode:
      type: human
      rationale: Complex
""")
        self._write_file("feature_input.yaml", """
feature_name: test
detected_platform: android
""")

        result = render_jira_payload.render(self.feature_dir)
        self.assertEqual(result, 0)

        with open(os.path.join(self.feature_dir, "jira_payload.json"), "r") as f:
            data = json.load(f)

        self.assertEqual(data["count"], 2)
        self.assertIn("[Android]", data["tickets"][0]["fields"]["summary"])
        self.assertIn("[Android]", data["tickets"][1]["fields"]["summary"])

    def test_missing_task_specs(self):
        result = render_jira_payload.render(self.feature_dir)
        self.assertEqual(result, 1)

    def test_ticket_descriptions_from_md(self):
        self._write_file("task_specs.yaml", """
tasks:
  - id: TASK-001
    title: Add flag
    layer: config
    sp: 1
    depends_on: []
    acceptance_criteria:
      - Done
    execution_mode:
      type: human
      rationale: Test
""")
        self._write_file("feature_input.yaml", """
feature_name: test
detected_platform: web
""")
        self._write_file("jira_tickets.md", """# Test Tickets

## TASK-001: Add flag
- **Component**: Web
- **Description**: Custom description from tickets md.
""")

        result = render_jira_payload.render(self.feature_dir)
        self.assertEqual(result, 0)

        with open(os.path.join(self.feature_dir, "jira_payload.json"), "r") as f:
            data = json.load(f)

        self.assertIn("Custom description", data["tickets"][0]["fields"]["description"])


class TestJiraConfigLoading(unittest.TestCase):
    def test_default_config_returned(self):
        config = render_jira_payload.load_jira_config("/nonexistent/path")
        self.assertEqual(config["project_key"], "PROJ")
        self.assertIn("ios", config["component_ids"])


if __name__ == "__main__":
    unittest.main()
