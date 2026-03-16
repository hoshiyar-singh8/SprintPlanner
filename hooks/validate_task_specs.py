#!/usr/bin/env python3
"""Validates task_specs.yaml — valid YAML, SP 1-3, valid layers, DAG cycle detection."""
import os
import sys
from collections import defaultdict, deque

import yaml


VALID_LAYERS = {
    # Shared
    "api", "config", "di", "domain", "mapper", "model", "navigation",
    "test", "integration", "ui", "viewmodel",
    # iOS / VIPER
    "builder", "interactor", "presenter", "router", "view",
    # Android / MVVM
    "data", "repository", "usecase", "fragment", "composable",
    # Web
    "component", "hook", "service", "store", "page",
    # Backend
    "handler", "controller", "middleware", "schema",
}

MAX_SP = 3


def validate(file_path):
    errors = []
    warnings = []

    if not os.path.exists(file_path):
        print(f"FAIL: File does not exist: {file_path}", file=sys.stderr)
        return 1

    with open(file_path, "r") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"FAIL: Invalid YAML: {e}", file=sys.stderr)
            return 1

    if not isinstance(data, dict):
        print("FAIL: Root element must be a mapping", file=sys.stderr)
        return 1

    tasks = data.get("tasks", [])
    if not tasks or not isinstance(tasks, list):
        print("FAIL: Missing or empty 'tasks' list", file=sys.stderr)
        return 1

    task_ids = set()
    adj = defaultdict(list)  # dependency graph
    in_degree = defaultdict(int)

    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"tasks[{i}] is not a mapping")
            continue

        task_id = task.get("id")
        if not task_id:
            errors.append(f"tasks[{i}] missing 'id'")
            continue

        if task_id in task_ids:
            errors.append(f"Duplicate task ID: {task_id}")
        task_ids.add(task_id)

        # Required fields
        for field in ("title", "layer", "sp", "acceptance_criteria"):
            if field not in task or task[field] is None:
                errors.append(f"{task_id}: missing required field '{field}'")

        # SP validation
        sp = task.get("sp")
        if sp is not None:
            if not isinstance(sp, (int, float)):
                errors.append(f"{task_id}: sp must be a number, got {type(sp).__name__}")
            elif sp < 1 or sp > MAX_SP:
                errors.append(f"{task_id}: sp={sp} out of range 1-{MAX_SP}")

        # Layer validation
        layer = task.get("layer", "")
        if layer:
            layer_lower = str(layer).lower().strip()
            if layer_lower not in VALID_LAYERS:
                warnings.append(
                    f"{task_id}: layer '{layer}' not in standard set "
                    f"({', '.join(sorted(VALID_LAYERS))})"
                )

        # Acceptance criteria
        ac = task.get("acceptance_criteria", [])
        if isinstance(ac, list) and len(ac) < 1:
            warnings.append(f"{task_id}: acceptance_criteria is empty")

        # Requirement traceability (optional but recommended)
        req_ids = task.get("requirement_ids", [])
        if not req_ids:
            warnings.append(f"{task_id}: no requirement_ids — cannot trace to RFC")

        # Dependencies
        depends_on = task.get("depends_on", [])
        if depends_on is None:
            depends_on = []
        if not isinstance(depends_on, list):
            errors.append(f"{task_id}: depends_on must be a list")
            depends_on = []

        for dep_id in depends_on:
            adj[dep_id].append(task_id)
            in_degree[task_id] += 0  # ensure node exists
        in_degree.setdefault(task_id, 0)
        for dep_id in depends_on:
            in_degree[task_id] += 1

    # Check dangling dependency references
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            continue
        depends_on = task.get("depends_on", []) or []
        for dep_id in depends_on:
            if dep_id not in task_ids:
                errors.append(
                    f"{task.get('id', f'tasks[{i}]')}: depends_on references "
                    f"non-existent task '{dep_id}'"
                )

    # DAG cycle detection (Kahn's algorithm)
    if task_ids:
        all_nodes = task_ids.copy()
        queue = deque()
        temp_in_degree = dict(in_degree)

        # Initialize all nodes
        for tid in all_nodes:
            if tid not in temp_in_degree:
                temp_in_degree[tid] = 0

        for node, degree in temp_in_degree.items():
            if degree == 0:
                queue.append(node)

        visited_count = 0
        while queue:
            node = queue.popleft()
            visited_count += 1
            for neighbor in adj.get(node, []):
                temp_in_degree[neighbor] -= 1
                if temp_in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count < len(all_nodes):
            # Find nodes in cycle
            cycle_nodes = [
                tid for tid in all_nodes
                if temp_in_degree.get(tid, 0) > 0
            ]
            errors.append(
                f"Dependency cycle detected involving: {', '.join(cycle_nodes)}"
            )

    # Print results
    for w in warnings:
        print(f"WARN: {w}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print(f"PASS: task_specs.yaml is valid ({len(task_ids)} tasks, no cycles)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_task_specs.py <path>", file=sys.stderr)
        sys.exit(1)
    sys.exit(validate(sys.argv[1]))
