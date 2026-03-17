#!/usr/bin/env python3
"""Tests for plan_push_strategy.py hook."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))

import plan_push_strategy


def _make_tasks():
    """Create a standard set of tasks for testing."""
    return [
        {
            "id": "TASK-001", "title": "Config flag", "layer": "config",
            "sp": 1, "depends_on": [],
            "execution_mode": {"type": "herogen", "rationale": "simple"},
        },
        {
            "id": "TASK-002", "title": "API model", "layer": "api",
            "sp": 2, "depends_on": ["TASK-001"],
            "execution_mode": {"type": "herogen", "rationale": "codable"},
        },
        {
            "id": "TASK-003", "title": "Mapper", "layer": "mapper",
            "sp": 1, "depends_on": ["TASK-002"],
            "execution_mode": {"type": "herogen", "rationale": "mapping"},
        },
        {
            "id": "TASK-004", "title": "Presenter", "layer": "presenter",
            "sp": 3, "depends_on": ["TASK-003"],
            "execution_mode": {"type": "human", "rationale": "complex"},
        },
        {
            "id": "TASK-005", "title": "UI View", "layer": "ui",
            "sp": 2, "depends_on": ["TASK-004"],
            "execution_mode": {"type": "human", "rationale": "design"},
        },
    ]


class TestTopologicalSort(unittest.TestCase):
    def test_basic_order(self):
        tasks = _make_tasks()
        ordered = plan_push_strategy.topological_sort(tasks)
        ids = [t["id"] for t in ordered]
        self.assertEqual(ids[0], "TASK-001")
        self.assertTrue(ids.index("TASK-002") > ids.index("TASK-001"))
        self.assertTrue(ids.index("TASK-004") > ids.index("TASK-003"))

    def test_no_deps(self):
        tasks = [
            {"id": "A", "sp": 1, "depends_on": []},
            {"id": "B", "sp": 1, "depends_on": []},
        ]
        ordered = plan_push_strategy.topological_sort(tasks)
        self.assertEqual(len(ordered), 2)


class TestFullPlan(unittest.TestCase):
    def test_returns_all_tasks(self):
        tasks = _make_tasks()
        selected, summary = plan_push_strategy.plan_strategy(tasks, "full_plan")
        self.assertEqual(summary["total_tasks"], 5)
        self.assertEqual(summary["total_sp"], 9)


class TestSprintCapacity(unittest.TestCase):
    def test_fits_within_capacity(self):
        tasks = _make_tasks()
        selected, summary = plan_push_strategy.plan_strategy(
            tasks, "sprint_capacity", capacity=4)
        total = sum(t["sp"] for t in selected)
        self.assertLessEqual(total, 4)
        self.assertEqual(summary["remaining_capacity"], 4 - total)

    def test_respects_dependencies(self):
        tasks = _make_tasks()
        selected, _ = plan_push_strategy.plan_strategy(
            tasks, "sprint_capacity", capacity=3)
        ids = [t["id"] for t in selected]
        # TASK-001 (1 SP) + TASK-002 (2 SP) = 3 SP
        self.assertIn("TASK-001", ids)
        self.assertIn("TASK-002", ids)
        # TASK-003 would need TASK-002, and we have 0 capacity left
        self.assertNotIn("TASK-004", ids)

    def test_zero_capacity(self):
        tasks = _make_tasks()
        selected, summary = plan_push_strategy.plan_strategy(
            tasks, "sprint_capacity", capacity=0)
        self.assertEqual(len(selected), 0)

    def test_missing_capacity_fails(self):
        tasks = _make_tasks()
        selected, summary = plan_push_strategy.plan_strategy(
            tasks, "sprint_capacity")
        self.assertIsNone(selected)


class TestHerogenOnly(unittest.TestCase):
    def test_filters_herogen(self):
        tasks = _make_tasks()
        selected, summary = plan_push_strategy.plan_strategy(
            tasks, "herogen_only")
        # TASK-001, 002, 003 are herogen
        self.assertEqual(summary["herogen_count"], 3)
        self.assertEqual(summary["total_tasks"], 3)

    def test_includes_deps(self):
        """If a herogen task depends on a human task, include the human task."""
        tasks = [
            {"id": "H1", "sp": 1, "depends_on": [],
             "execution_mode": {"type": "human", "rationale": "x"}},
            {"id": "B1", "sp": 1, "depends_on": ["H1"],
             "execution_mode": {"type": "herogen", "rationale": "y"}},
        ]
        selected, summary = plan_push_strategy.plan_strategy(
            tasks, "herogen_only")
        ids = [t["id"] for t in selected]
        self.assertIn("H1", ids)  # dep pulled in
        self.assertIn("B1", ids)
        self.assertEqual(len(summary.get("dependency_tasks_included", [])), 1)


class TestHumanOnly(unittest.TestCase):
    def test_filters_human(self):
        tasks = _make_tasks()
        selected, summary = plan_push_strategy.plan_strategy(
            tasks, "human_only")
        # TASK-004, 005 are human, but they need 001-003 as deps
        self.assertEqual(summary["human_count"], 2)
        self.assertEqual(summary["total_tasks"], 5)  # all pulled in as deps


class TestCherryPick(unittest.TestCase):
    def test_picks_specific_tasks(self):
        tasks = _make_tasks()
        selected, summary = plan_push_strategy.plan_strategy(
            tasks, "cherry_pick", task_ids=["TASK-003"])
        ids = [t["id"] for t in selected]
        # TASK-003 needs 002, which needs 001
        self.assertIn("TASK-001", ids)
        self.assertIn("TASK-002", ids)
        self.assertIn("TASK-003", ids)
        self.assertNotIn("TASK-004", ids)

    def test_missing_task_ids_fails(self):
        tasks = _make_tasks()
        selected, _ = plan_push_strategy.plan_strategy(
            tasks, "cherry_pick")
        self.assertIsNone(selected)


class TestGetRequiredDeps(unittest.TestCase):
    def test_transitive_deps(self):
        tasks = _make_tasks()
        deps = plan_push_strategy.get_required_deps("TASK-004", tasks)
        self.assertEqual(deps, {"TASK-001", "TASK-002", "TASK-003"})

    def test_no_deps(self):
        tasks = _make_tasks()
        deps = plan_push_strategy.get_required_deps("TASK-001", tasks)
        self.assertEqual(deps, set())


if __name__ == "__main__":
    unittest.main()
