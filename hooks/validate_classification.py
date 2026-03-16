#!/usr/bin/env python3
"""Validates execution_mode fields in task_specs.yaml."""
import os
import sys
import yaml


VALID_TYPES = {"herogen", "human"}


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

    tasks = data.get("tasks", [])
    if not tasks or not isinstance(tasks, list):
        print("FAIL: Missing or empty 'tasks' list", file=sys.stderr)
        return 1

    herogen_count = 0
    human_count = 0

    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            continue

        task_id = task.get("id", f"tasks[{i}]")

        # Check execution_mode exists
        exec_mode = task.get("execution_mode")
        if not exec_mode or not isinstance(exec_mode, dict):
            errors.append(f"{task_id}: missing or invalid 'execution_mode'")
            continue

        # Check type
        mode_type = exec_mode.get("type", "")
        if mode_type not in VALID_TYPES:
            errors.append(
                f"{task_id}: execution_mode.type '{mode_type}' "
                f"not valid (must be: {', '.join(VALID_TYPES)})"
            )
        elif mode_type == "herogen":
            herogen_count += 1
        else:
            human_count += 1

        # Check rationale
        rationale = exec_mode.get("rationale", "")
        if not rationale or not str(rationale).strip():
            errors.append(f"{task_id}: execution_mode.rationale is empty")

        # Semantic checks
        sp = task.get("sp", 0)
        if mode_type == "herogen" and isinstance(sp, (int, float)) and sp > 2:
            warnings.append(
                f"{task_id}: {sp} SP task classified as herogen "
                f"(tasks >2 SP are usually human-only)"
            )

        # Check for cross-layer in herogen
        layer = str(task.get("layer", "")).lower()
        if mode_type == "herogen" and layer in ("integration", "cross-layer"):
            warnings.append(
                f"{task_id}: integration/cross-layer task classified as herogen "
                f"(usually requires human judgment)"
            )

    # Print results
    for w in warnings:
        print(f"WARN: {w}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print(
        f"PASS: Classification valid "
        f"({herogen_count} herogen, {human_count} human, {len(tasks)} total)"
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_classification.py <path>", file=sys.stderr)
        sys.exit(1)
    sys.exit(validate(sys.argv[1]))
