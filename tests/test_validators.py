#!/usr/bin/env python3
"""Tests for pipeline validation hooks."""
import json
import os
import sys
import tempfile
import unittest

# Add hooks directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))

import validate_input
import validate_clarifications
import validate_context
import validate_plan
import validate_task_specs
import validate_classification


class TestValidateInput(unittest.TestCase):
    def _write_yaml(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_valid_input(self):
        path = self._write_yaml("""
feature_name: test-feature
detected_platform: ios
repo_source: local
repo_path: /tmp
rfc_path: /tmp/SprintPlanner/README.md
sp_max: 3
ui_scope: 1
""")
        self.assertEqual(validate_input.validate(path), 0)

    def test_missing_feature_name(self):
        path = self._write_yaml("""
detected_platform: ios
repo_source: local
repo_path: /tmp
rfc_path: /tmp/SprintPlanner/README.md
""")
        self.assertEqual(validate_input.validate(path), 1)

    def test_invalid_platform(self):
        path = self._write_yaml("""
feature_name: test
detected_platform: cobol
repo_source: local
repo_path: /tmp
rfc_path: /tmp/SprintPlanner/README.md
""")
        self.assertEqual(validate_input.validate(path), 1)

    def test_invalid_repo_source(self):
        path = self._write_yaml("""
feature_name: test
detected_platform: ios
repo_source: ftp
repo_path: /tmp
rfc_path: /tmp/SprintPlanner/README.md
""")
        self.assertEqual(validate_input.validate(path), 1)

    def test_sp_max_out_of_range(self):
        path = self._write_yaml("""
feature_name: test
detected_platform: ios
repo_source: local
repo_path: /tmp
rfc_path: /tmp/SprintPlanner/README.md
sp_max: 5
""")
        self.assertEqual(validate_input.validate(path), 1)

    def test_github_source_requires_url(self):
        path = self._write_yaml("""
feature_name: test
detected_platform: android
repo_source: github
rfc_path: /tmp/SprintPlanner/README.md
""")
        self.assertEqual(validate_input.validate(path), 1)

    def test_nonexistent_file(self):
        self.assertEqual(validate_input.validate("/tmp/does_not_exist.yaml"), 1)

    def test_invalid_yaml(self):
        path = self._write_yaml("not: valid: yaml: [")
        self.assertEqual(validate_input.validate(path), 1)


class TestValidateClarifications(unittest.TestCase):
    def _write_md(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_valid_clarifications(self):
        path = self._write_md("""# Clarifications

## Questions

### Group 1 — Scope
1. What is the scope?
2. What are the requirements?
3. Any edge cases?

### Group 2 — API
1. What endpoints?

## User Answers

## Planning Decisions

## Open Questions
""")
        self.assertEqual(validate_clarifications.validate(path), 0)

    def test_missing_questions_section(self):
        path = self._write_md("""# Clarifications

## User Answers

## Planning Decisions

## Open Questions
""")
        self.assertEqual(validate_clarifications.validate(path), 1)

    def test_empty_file(self):
        path = self._write_md("")
        self.assertEqual(validate_clarifications.validate(path), 1)


class TestValidateContext(unittest.TestCase):
    def _write_yaml(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_valid_context(self):
        path = self._write_yaml("""
architecture:
  pattern: VIPER
  di_framework: Swinject
  networking: URLSession
  ui_framework: UIKit

relevant_modules:
  - name: Subscription
    path: Subscription/Source/
    similarity: high

key_files:
  - path: Subscription/Source/Api/Client.swift
    role: API client
""")
        self.assertEqual(validate_context.validate(path), 0)

    def test_missing_architecture(self):
        path = self._write_yaml("""
relevant_modules:
  - name: Subscription
    path: Subscription/Source/

key_files:
  - path: Client.swift
    role: API client
""")
        self.assertEqual(validate_context.validate(path), 1)

    def test_unknown_architecture_pattern(self):
        """Unrecognized patterns should fail."""
        path = self._write_yaml("""
architecture:
  pattern: waterfall
  di_framework: Swinject
  networking: URLSession
  ui_framework: UIKit

relevant_modules:
  - name: Test
    path: Test/

key_files:
  - path: Test.swift
    role: Test file
""")
        self.assertEqual(validate_context.validate(path), 1)

    def test_bloc_pattern_accepted(self):
        """Flutter BLoC pattern should be valid."""
        path = self._write_yaml("""
architecture:
  pattern: bloc
  di_framework: GetIt
  networking: Dio
  ui_framework: Flutter

relevant_modules:
  - name: Feature
    path: lib/features/

key_files:
  - path: lib/features/bloc.dart
    role: BLoC
""")
        self.assertEqual(validate_context.validate(path), 0)


class TestValidateTaskSpecs(unittest.TestCase):
    def _write_yaml(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_valid_task_specs(self):
        path = self._write_yaml("""
tasks:
  - id: TASK-001
    title: Add config flag
    layer: config
    sp: 1
    depends_on: []
    acceptance_criteria:
      - Flag defined
      - Default is false
  - id: TASK-002
    title: Create API model
    layer: api
    sp: 1
    depends_on: [TASK-001]
    acceptance_criteria:
      - Codable struct created
""")
        self.assertEqual(validate_task_specs.validate(path), 0)

    def test_sp_out_of_range(self):
        path = self._write_yaml("""
tasks:
  - id: TASK-001
    title: Big task
    layer: config
    sp: 5
    depends_on: []
    acceptance_criteria:
      - Done
""")
        self.assertEqual(validate_task_specs.validate(path), 1)

    def test_duplicate_task_id(self):
        path = self._write_yaml("""
tasks:
  - id: TASK-001
    title: Task A
    layer: config
    sp: 1
    depends_on: []
    acceptance_criteria:
      - Done
  - id: TASK-001
    title: Task B
    layer: api
    sp: 1
    depends_on: []
    acceptance_criteria:
      - Done
""")
        self.assertEqual(validate_task_specs.validate(path), 1)

    def test_dangling_dependency(self):
        path = self._write_yaml("""
tasks:
  - id: TASK-001
    title: Task A
    layer: config
    sp: 1
    depends_on: [TASK-999]
    acceptance_criteria:
      - Done
""")
        self.assertEqual(validate_task_specs.validate(path), 1)

    def test_cycle_detection(self):
        path = self._write_yaml("""
tasks:
  - id: TASK-001
    title: Task A
    layer: config
    sp: 1
    depends_on: [TASK-002]
    acceptance_criteria:
      - Done
  - id: TASK-002
    title: Task B
    layer: api
    sp: 1
    depends_on: [TASK-001]
    acceptance_criteria:
      - Done
""")
        self.assertEqual(validate_task_specs.validate(path), 1)

    def test_empty_tasks(self):
        path = self._write_yaml("tasks: []")
        self.assertEqual(validate_task_specs.validate(path), 1)


class TestValidateClassification(unittest.TestCase):
    def _write_yaml(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_valid_classification(self):
        path = self._write_yaml("""
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
      rationale: Simple config flag following existing pattern
      confidence: high
      risks: []
  - id: TASK-002
    title: Complex integration
    layer: integration
    sp: 3
    depends_on: [TASK-001]
    acceptance_criteria:
      - Wired up
    execution_mode:
      type: human
      rationale: Cross-layer wiring requires judgment
      confidence: high
      risks:
        - May affect existing flows
""")
        self.assertEqual(validate_classification.validate(path), 0)

    def test_missing_execution_mode(self):
        path = self._write_yaml("""
tasks:
  - id: TASK-001
    title: Task without classification
    layer: config
    sp: 1
    depends_on: []
    acceptance_criteria:
      - Done
""")
        self.assertEqual(validate_classification.validate(path), 1)

    def test_empty_rationale(self):
        path = self._write_yaml("""
tasks:
  - id: TASK-001
    title: Task
    layer: config
    sp: 1
    depends_on: []
    acceptance_criteria:
      - Done
    execution_mode:
      type: herogen
      rationale: ""
      confidence: high
      risks: []
""")
        self.assertEqual(validate_classification.validate(path), 1)


class TestValidatePlan(unittest.TestCase):
    def _write_md(self, content):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_valid_plan(self):
        path = self._write_md("""# Implementation Plan — Test Feature

## Overview
This feature adds a new config flag and API integration for the test module.
It follows existing VIPER patterns in the codebase. The partnership voucher
feature requires changes to the Subscription SDK and B2C bridge layer.
We will implement it in phases starting with the data model foundation.

## Architecture Decisions
- Use existing SubscriptionClient pattern for API calls
- Follow VIPER with async/await for the new module
- Reuse PaymentMethodViewModelMapper for payment display

## Implementation Phases

| Phase | Description | Tasks | SP |
|-------|-------------|-------|----|
| 1 | Foundation (models, config flags) | 3 | 3 SP |
| 2 | API Layer (endpoints, mappers) | 4 | 6 SP |
| 3 | UI Components (views, viewmodels) | 3 | 4 SP |

**Total**: 10 tasks, 13 SP

## Risks
- Backend API deployment timeline is unknown
- Figma designs may change after implementation starts
""")
        self.assertEqual(validate_plan.validate(path), 0)

    def test_missing_overview(self):
        path = self._write_md("""# Plan

## Architecture Decisions
- Decision 1

## Implementation Phases
Total: 5 SP
""")
        self.assertEqual(validate_plan.validate(path), 1)

    def test_no_sp_estimates(self):
        path = self._write_md("""# Implementation Plan

## Overview
Some overview text that is long enough to pass the minimum length check.

## Architecture Decisions
- Decision 1

## Implementation Phases
Just some tasks without any point estimates mentioned anywhere in the document.
""")
        self.assertEqual(validate_plan.validate(path), 1)

    def test_too_short(self):
        path = self._write_md("""## Overview
Short.
## Architecture
A.
## Phases
1 SP
""")
        self.assertEqual(validate_plan.validate(path), 1)


if __name__ == "__main__":
    unittest.main()
