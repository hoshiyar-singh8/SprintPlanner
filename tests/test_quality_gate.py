#!/usr/bin/env python3
"""Tests for quality_gate.py hook."""
import json
import os
import sys
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))

import quality_gate


class TestQualityGate(unittest.TestCase):
    def setUp(self):
        self.feature_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.feature_dir)

    def _write_file(self, name, content):
        path = os.path.join(self.feature_dir, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def _create_minimal_artifacts(self):
        """Create a minimal set of valid pipeline artifacts."""
        self._write_file("feature_input.yaml", """
feature_name: test
detected_platform: ios
repo_source: local
repo_path: /tmp
rfc_path: /tmp/rfc.md
""")
        self._write_file("clarifications.md", "# Clarifications\n## Questions\n1. Q?\n")
        self._write_file("context_pack.yaml", """
architecture:
  pattern: VIPER
  di_framework: Swinject
  networking: URLSession
  ui_framework: UIKit
relevant_modules:
  - name: Test
    path: Test/
key_files:
  - path: Test.swift
    role: Test
""")
        self._write_file("high_level_plan.md", """# Plan
## Overview
Some overview. Total: 3 SP estimate.
## Architecture Decisions
Decision 1.
## Implementation Phases
| Phase | SP |
| 1 | 3 SP |
""")
        self._write_file("task_specs.yaml", """
tasks:
  - id: TASK-001
    title: Test task
    layer: config
    sp: 1
    depends_on: []
    acceptance_criteria:
      - Done
    execution_mode:
      type: herogen
      rationale: Simple
      confidence: high
      risks: []
""")
        self._write_file("jira_tickets.md", """# Tickets
## TASK-001: Test task
Description here.
""")

    def test_all_artifacts_present(self):
        self._create_minimal_artifacts()
        result = quality_gate.quality_gate(self.feature_dir)
        self.assertEqual(result, 0)

    def test_missing_artifact_fails(self):
        self._create_minimal_artifacts()
        os.unlink(os.path.join(self.feature_dir, "task_specs.yaml"))
        result = quality_gate.quality_gate(self.feature_dir)
        self.assertEqual(result, 1)

    def test_empty_artifact_fails(self):
        self._create_minimal_artifacts()
        with open(os.path.join(self.feature_dir, "clarifications.md"), "w") as f:
            f.write("")
        result = quality_gate.quality_gate(self.feature_dir)
        self.assertEqual(result, 1)

    def test_ticket_count_mismatch_warns(self):
        self._create_minimal_artifacts()
        # Add extra ticket that doesn't match task_specs
        self._write_file("jira_tickets.md", """# Tickets
## TASK-001: Test task
Description.
## TASK-002: Extra task
Extra description.
""")
        # Should still pass (mismatch is a warning, not failure)
        result = quality_gate.quality_gate(self.feature_dir)
        self.assertEqual(result, 0)

    def test_dangling_dependency_fails(self):
        self._create_minimal_artifacts()
        self._write_file("task_specs.yaml", """
tasks:
  - id: TASK-001
    title: Test task
    layer: config
    sp: 1
    depends_on: [TASK-999]
    acceptance_criteria:
      - Done
    execution_mode:
      type: herogen
      rationale: Simple
      confidence: high
      risks: []
""")
        result = quality_gate.quality_gate(self.feature_dir)
        self.assertEqual(result, 1)

    def test_jira_payload_consistency(self):
        self._create_minimal_artifacts()
        self._write_file("jira_payload.json", json.dumps({
            "tickets": [{"task_id": "TASK-001", "fields": {}}],
            "count": 1
        }))
        result = quality_gate.quality_gate(self.feature_dir)
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
