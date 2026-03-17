#!/usr/bin/env python3
"""Final cross-file consistency check across all pipeline artifacts."""
import json
import os
import re
import sys
import yaml


def load_yaml(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError:
            return None


def load_md(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return f.read()


def quality_gate(feature_dir):
    results = {"pass": [], "fail": [], "warn": []}

    # 1. Check all expected artifacts exist
    expected_files = [
        "feature_input.yaml",
        "clarifications.md",
        "context_pack.yaml",
        "high_level_plan.md",
        "task_specs.yaml",
        "jira_tickets.md",
    ]

    for fname in expected_files:
        fpath = os.path.join(feature_dir, fname)
        if os.path.exists(fpath):
            size = os.path.getsize(fpath)
            if size > 0:
                results["pass"].append(f"Artifact exists and non-empty: {fname}")
            else:
                results["fail"].append(f"Artifact exists but is empty: {fname}")
        else:
            results["fail"].append(f"Missing artifact: {fname}")

    # 2. Load key artifacts
    feature_input = load_yaml(os.path.join(feature_dir, "feature_input.yaml")) or {}
    context_pack = load_yaml(os.path.join(feature_dir, "context_pack.yaml")) or {}
    task_specs = load_yaml(os.path.join(feature_dir, "task_specs.yaml")) or {}
    plan_md = load_md(os.path.join(feature_dir, "high_level_plan.md")) or ""
    tickets_md = load_md(os.path.join(feature_dir, "jira_tickets.md")) or ""

    tasks = task_specs.get("tasks", [])

    # 3. Cross-file: task count consistency
    task_count = len(tasks)
    if task_count > 0:
        results["pass"].append(f"Task specs has {task_count} tasks")
    else:
        results["fail"].append("No tasks found in task_specs.yaml")

    # Count tickets in jira_tickets.md
    ticket_headers = re.findall(r"## \[?TASK-\S+\]?", tickets_md)
    ticket_count = len(ticket_headers)
    if ticket_count == task_count:
        results["pass"].append(f"Ticket count matches task count: {ticket_count}")
    elif ticket_count > 0:
        results["warn"].append(
            f"Ticket count ({ticket_count}) differs from task count ({task_count})"
        )
    else:
        results["fail"].append("No ticket sections found in jira_tickets.md")

    # 4. Cross-file: every task has execution_mode
    tasks_with_mode = sum(
        1 for t in tasks if isinstance(t, dict) and t.get("execution_mode")
    )
    if tasks_with_mode == task_count and task_count > 0:
        results["pass"].append("All tasks have execution_mode classification")
    elif task_count > 0:
        results["fail"].append(
            f"{task_count - tasks_with_mode} tasks missing execution_mode"
        )

    # 5. Cross-file: SP consistency
    total_sp = sum(t.get("sp", 0) for t in tasks if isinstance(t, dict))
    if total_sp > 0:
        results["pass"].append(f"Total story points: {total_sp}")
        # Check plan mentions similar SP total
        plan_sp_matches = re.findall(r"(\d+)\s*(?:SP|story\s*point|pts?)", plan_md, re.IGNORECASE)
        if plan_sp_matches:
            plan_sp_total = max(int(s) for s in plan_sp_matches)
            if abs(plan_sp_total - total_sp) <= total_sp * 0.3:
                results["pass"].append(
                    f"Plan SP estimate ({plan_sp_total}) within 30% of actual ({total_sp})"
                )
            else:
                results["warn"].append(
                    f"Plan SP estimate ({plan_sp_total}) differs significantly "
                    f"from actual ({total_sp})"
                )

    # 6. Cross-file: platform consistency
    input_platform = str(
        feature_input.get("detected_platform",
                          feature_input.get("platform", ""))
    ).lower()
    if input_platform:
        # Check context pack architecture
        arch = context_pack.get("architecture", {})
        if arch:
            results["pass"].append("Architecture section present in context_pack")
        else:
            results["warn"].append("No architecture section in context_pack")

    # 7. Requirement coverage — every R-ID in clarifications must be covered by a task
    clarifications_md = load_md(os.path.join(feature_dir, "clarifications.md")) or ""
    req_ids_in_clarifications = set(re.findall(r"\bR(\d+)\b", clarifications_md))
    if req_ids_in_clarifications and tasks:
        task_req_ids = set()
        for t in tasks:
            if isinstance(t, dict):
                for rid in (t.get("requirement_ids") or []):
                    # Extract number from "R1", "R2", etc.
                    m = re.match(r"R(\d+)", str(rid))
                    if m:
                        task_req_ids.add(m.group(1))
        uncovered = req_ids_in_clarifications - task_req_ids
        if not uncovered:
            results["pass"].append(
                f"All {len(req_ids_in_clarifications)} requirements (R-IDs) "
                f"covered by tasks"
            )
        else:
            uncovered_labels = sorted(f"R{r}" for r in uncovered)
            results["warn"].append(
                f"Requirements not covered by any task: "
                f"{', '.join(uncovered_labels)}"
            )

    # 8. Dependency integrity
    task_ids = {t.get("id") for t in tasks if isinstance(t, dict) and t.get("id")}
    dangling_deps = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        for dep in (t.get("depends_on") or []):
            if dep not in task_ids:
                dangling_deps.append(f"{t.get('id')} → {dep}")
    if dangling_deps:
        results["fail"].append(f"Dangling dependencies: {', '.join(dangling_deps)}")
    elif task_ids:
        results["pass"].append("All dependency references are valid")

    # 9. Check jira_payload.json if it exists
    payload_path = os.path.join(feature_dir, "jira_payload.json")
    if os.path.exists(payload_path):
        try:
            with open(payload_path, "r") as f:
                payload = json.load(f)
            payload_count = payload.get("count", 0)
            if payload_count == task_count:
                results["pass"].append(f"Jira payload has {payload_count} tickets (matches)")
            else:
                results["warn"].append(
                    f"Jira payload count ({payload_count}) differs from task count ({task_count})"
                )
        except json.JSONDecodeError:
            results["fail"].append("jira_payload.json is invalid JSON")

    # Print results
    print("=" * 60)
    print("QUALITY GATE REPORT")
    print("=" * 60)

    for category in ("pass", "warn", "fail"):
        label = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[category]
        for msg in results[category]:
            print(f"{label}: {msg}")

    total = sum(len(v) for v in results.values())
    print("-" * 60)
    print(
        f"Summary: {len(results['pass'])} passed, "
        f"{len(results['warn'])} warnings, "
        f"{len(results['fail'])} failures "
        f"(total {total} checks)"
    )

    return 1 if results["fail"] else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: quality_gate.py <feature-dir>", file=sys.stderr)
        sys.exit(1)
    sys.exit(quality_gate(sys.argv[1]))
