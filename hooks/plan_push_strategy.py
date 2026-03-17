#!/usr/bin/env python3
"""Plans a push strategy for Jira tickets based on sprint capacity and filters.

Takes task_specs.yaml + push strategy config and outputs a push_plan.yaml
with the dependency-ordered subset of tickets to create.

Strategies:
  - full_plan: Push all tickets
  - sprint_capacity: Push tickets up to N SP, respecting dependency order
  - herogen_only: Push only herogen-classified tasks
  - human_only: Push only human-classified tasks
  - cherry_pick: Push specific task IDs

Usage:
  python3 plan_push_strategy.py <feature-dir> --strategy full_plan
  python3 plan_push_strategy.py <feature-dir> --strategy sprint_capacity --capacity 13
  python3 plan_push_strategy.py <feature-dir> --strategy herogen_only
  python3 plan_push_strategy.py <feature-dir> --strategy human_only
  python3 plan_push_strategy.py <feature-dir> --strategy cherry_pick --tasks TASK-001,TASK-003
"""
import argparse
import os
import sys
from collections import defaultdict, deque

try:
    import yaml
except ImportError:
    print("FAIL: PyYAML required -- run: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)


VALID_STRATEGIES = {
    "full_plan", "sprint_capacity", "herogen_only", "human_only", "cherry_pick",
}


def load_task_specs(feature_dir):
    """Load and parse task_specs.yaml."""
    path = os.path.join(feature_dir, "task_specs.yaml")
    if not os.path.exists(path):
        print(f"FAIL: task_specs.yaml not found in {feature_dir}", file=sys.stderr)
        return None
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if not data or not isinstance(data.get("tasks"), list):
        print("FAIL: task_specs.yaml has no tasks list", file=sys.stderr)
        return None
    return data["tasks"]


def topological_sort(tasks):
    """Return tasks in dependency order (Kahn's algorithm)."""
    task_map = {t["id"]: t for t in tasks}
    adj = defaultdict(list)
    in_degree = {t["id"]: 0 for t in tasks}

    for t in tasks:
        for dep in (t.get("depends_on") or []):
            if dep in task_map:
                adj[dep].append(t["id"])
                in_degree[t["id"]] += 1

    queue = deque(tid for tid, deg in in_degree.items() if deg == 0)
    ordered = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return [task_map[tid] for tid in ordered if tid in task_map]


def get_required_deps(task_id, tasks):
    """Recursively collect all dependency task IDs for a given task."""
    task_map = {t["id"]: t for t in tasks}
    visited = set()
    stack = [task_id]
    while stack:
        tid = stack.pop()
        if tid in visited:
            continue
        visited.add(tid)
        t = task_map.get(tid)
        if t:
            for dep in (t.get("depends_on") or []):
                stack.append(dep)
    visited.discard(task_id)
    return visited


def filter_full_plan(tasks):
    """All tasks, dependency-ordered."""
    return topological_sort(tasks)


def filter_sprint_capacity(tasks, capacity):
    """Fill up to capacity SP in dependency order."""
    ordered = topological_sort(tasks)
    selected = []
    total_sp = 0
    selected_ids = set()

    for task in ordered:
        sp = task.get("sp", 1)
        if total_sp + sp <= capacity:
            # Check all deps are included
            deps = task.get("depends_on") or []
            if all(d in selected_ids for d in deps):
                selected.append(task)
                selected_ids.add(task["id"])
                total_sp += sp

    return selected


def filter_by_execution_mode(tasks, mode):
    """Filter tasks by execution_mode type, including required deps."""
    matching_ids = set()
    for t in tasks:
        exec_mode = t.get("execution_mode", {})
        if isinstance(exec_mode, dict) and exec_mode.get("type") == mode:
            matching_ids.add(t["id"])

    # Add required dependencies even if they're the other type
    all_needed = set(matching_ids)
    for tid in matching_ids:
        all_needed |= get_required_deps(tid, tasks)

    filtered = [t for t in tasks if t["id"] in all_needed]
    return topological_sort(filtered)


def filter_cherry_pick(tasks, task_ids):
    """Select specific tasks by ID, including required deps."""
    requested = set(task_ids)
    all_needed = set(requested)
    for tid in requested:
        all_needed |= get_required_deps(tid, tasks)

    filtered = [t for t in tasks if t["id"] in all_needed]
    return topological_sort(filtered)


def plan_strategy(tasks, strategy, capacity=None, task_ids=None):
    """Apply the chosen strategy and return (selected_tasks, summary)."""
    if strategy == "full_plan":
        selected = filter_full_plan(tasks)
    elif strategy == "sprint_capacity":
        if capacity is None:
            print("FAIL: --capacity required for sprint_capacity strategy",
                  file=sys.stderr)
            return None, None
        selected = filter_sprint_capacity(tasks, capacity)
    elif strategy == "herogen_only":
        selected = filter_by_execution_mode(tasks, "herogen")
    elif strategy == "human_only":
        selected = filter_by_execution_mode(tasks, "human")
    elif strategy == "cherry_pick":
        if not task_ids:
            print("FAIL: --tasks required for cherry_pick strategy",
                  file=sys.stderr)
            return None, None
        selected = filter_cherry_pick(tasks, task_ids)
    else:
        print(f"FAIL: Unknown strategy '{strategy}'", file=sys.stderr)
        return None, None

    total_sp = sum(t.get("sp", 1) for t in selected)
    herogen_count = sum(
        1 for t in selected
        if isinstance(t.get("execution_mode"), dict)
        and t["execution_mode"].get("type") == "herogen"
    )
    human_count = len(selected) - herogen_count

    # Identify dep tasks pulled in that weren't directly requested
    dep_tasks = []
    if strategy == "herogen_only":
        dep_tasks = [
            t["id"] for t in selected
            if isinstance(t.get("execution_mode"), dict)
            and t["execution_mode"].get("type") != "herogen"
        ]
    elif strategy == "human_only":
        dep_tasks = [
            t["id"] for t in selected
            if isinstance(t.get("execution_mode"), dict)
            and t["execution_mode"].get("type") != "human"
        ]
    elif strategy == "cherry_pick" and task_ids:
        dep_tasks = [t["id"] for t in selected if t["id"] not in set(task_ids)]

    summary = {
        "strategy": strategy,
        "total_tasks": len(selected),
        "total_sp": total_sp,
        "herogen_count": herogen_count,
        "human_count": human_count,
    }
    if capacity is not None:
        summary["capacity"] = capacity
        summary["remaining_capacity"] = capacity - total_sp
    if dep_tasks:
        summary["dependency_tasks_included"] = dep_tasks

    return selected, summary


def main():
    parser = argparse.ArgumentParser(
        description="Plan a push strategy for Jira tickets")
    parser.add_argument("feature_dir", help="Feature directory path")
    parser.add_argument("--strategy", "-s", required=True,
                        choices=sorted(VALID_STRATEGIES),
                        help="Push strategy")
    parser.add_argument("--capacity", "-c", type=int,
                        help="Sprint capacity in SP (for sprint_capacity)")
    parser.add_argument("--tasks", "-t",
                        help="Comma-separated task IDs (for cherry_pick)")
    parser.add_argument("--output", "-o",
                        help="Output path (default: <feature-dir>/push_plan.yaml)")
    args = parser.parse_args()

    tasks = load_task_specs(args.feature_dir)
    if tasks is None:
        sys.exit(1)

    task_ids = None
    if args.tasks:
        task_ids = [t.strip() for t in args.tasks.split(",") if t.strip()]

    selected, summary = plan_strategy(
        tasks, args.strategy,
        capacity=args.capacity,
        task_ids=task_ids,
    )
    if selected is None:
        sys.exit(1)

    # Build push plan
    push_plan = {
        "push_strategy": summary,
        "tasks_to_push": [
            {
                "id": t["id"],
                "title": t.get("title", ""),
                "layer": t.get("layer", ""),
                "sp": t.get("sp", 1),
                "execution_mode": (
                    t.get("execution_mode", {}).get("type", "unknown")
                    if isinstance(t.get("execution_mode"), dict)
                    else "unknown"
                ),
            }
            for t in selected
        ],
    }

    output_path = args.output or os.path.join(args.feature_dir, "push_plan.yaml")
    with open(output_path, "w") as f:
        yaml.dump(push_plan, f, default_flow_style=False, sort_keys=False)

    # Print summary
    print(f"Push Strategy: {args.strategy}")
    print(f"  Tasks: {summary['total_tasks']} "
          f"({summary['herogen_count']} herogen, {summary['human_count']} human)")
    print(f"  Total SP: {summary['total_sp']}")
    if args.strategy == "sprint_capacity":
        print(f"  Capacity: {summary.get('capacity', '?')} SP "
              f"(remaining: {summary.get('remaining_capacity', '?')} SP)")
    if summary.get("dependency_tasks_included"):
        print(f"  Dependency tasks auto-included: "
              f"{', '.join(summary['dependency_tasks_included'])}")

    print(f"\nPush plan: {len(selected)} tasks in dependency order:")
    for i, t in enumerate(selected, 1):
        mode = "unknown"
        if isinstance(t.get("execution_mode"), dict):
            mode = t["execution_mode"].get("type", "unknown")
        print(f"  {i}. {t['id']}: {t.get('title', '')} "
              f"({t.get('sp', '?')} SP, {mode})")

    print(f"\nPASS: Push plan written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
