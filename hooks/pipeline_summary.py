#!/usr/bin/env python3
"""Prints a quick summary of pipeline artifacts in a feature directory.

Usage: python3 pipeline_summary.py <feature-dir>
"""
import json
import os
import re
import sys

import yaml


def summarize(feature_dir):
    if not os.path.isdir(feature_dir):
        print(f"Error: {feature_dir} is not a directory", file=sys.stderr)
        return 1

    print(f"Pipeline Summary — {os.path.basename(feature_dir)}")
    print("=" * 50)

    # Feature input
    input_path = os.path.join(feature_dir, "feature_input.yaml")
    if os.path.exists(input_path):
        with open(input_path) as f:
            fi = yaml.safe_load(f) or {}
        print(f"Feature:  {fi.get('feature_name', '?')}")
        print(f"Platform: {fi.get('detected_platform', fi.get('platform', '?'))}")
        print(f"Repo:     {fi.get('repo_url', fi.get('repo_path', '?'))}")
        print(f"UI Scope: {fi.get('ui_scope', '?')}")

    # Task specs
    specs_path = os.path.join(feature_dir, "task_specs.yaml")
    if os.path.exists(specs_path):
        with open(specs_path) as f:
            specs = yaml.safe_load(f) or {}
        tasks = specs.get("tasks", [])
        total_sp = sum(t.get("sp", 0) for t in tasks if isinstance(t, dict))
        herogen = sum(1 for t in tasks if isinstance(t, dict)
                      and isinstance(t.get("execution_mode"), dict)
                      and t["execution_mode"].get("type") == "herogen")
        human = len(tasks) - herogen

        print(f"\nTasks:    {len(tasks)} ({total_sp} SP)")
        print(f"  Hero Gen: {herogen}")
        print(f"  Human:    {human}")

        # Layer distribution
        layers = {}
        for t in tasks:
            if isinstance(t, dict):
                layer = t.get("layer", "unknown")
                layers[layer] = layers.get(layer, 0) + 1
        if layers:
            print(f"\nLayers:")
            for layer, count in sorted(layers.items(), key=lambda x: -x[1]):
                print(f"  {layer}: {count}")

    # Pipeline state
    state_path = os.path.join(feature_dir, "pipeline_state.yaml")
    if os.path.exists(state_path):
        with open(state_path) as f:
            state = yaml.safe_load(f) or {}
        stage = state.get("current_stage", "?")
        status = state.get("stage_status", "?")
        print(f"\nPipeline: Stage {stage} ({status})")

    # Artifacts
    expected = [
        "feature_input.yaml", "clarifications.md", "context_pack.yaml",
        "high_level_plan.md", "task_specs.yaml", "jira_tickets.md",
        "jira_payload.json", "validation_report.md",
    ]
    print(f"\nArtifacts:")
    for name in expected:
        path = os.path.join(feature_dir, name)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  + {name} ({size:,} bytes)")
        else:
            print(f"  - {name} (missing)")

    # Jira creation status
    payload_path = os.path.join(feature_dir, "jira_payload.json")
    if os.path.exists(payload_path):
        with open(payload_path) as f:
            try:
                payload = json.load(f)
                status = payload.get("creation_status")
                if status:
                    created = len(payload.get("created", []))
                    failed = len(payload.get("failed", []))
                    print(f"\nJira: {status} ({created} created, {failed} failed)")
                    for c in payload.get("created", []):
                        print(f"  {c['task_id']} -> {c['jira_key']}")
            except json.JSONDecodeError:
                pass

    print()
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: pipeline_summary.py <feature-dir>", file=sys.stderr)
        sys.exit(1)
    sys.exit(summarize(sys.argv[1]))
