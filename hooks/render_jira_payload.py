#!/usr/bin/env python3
"""Converts task_specs.yaml + jira_tickets.md → jira_payload.json.

Reads task_specs.yaml for structured data (SP, dependencies, layer, execution_mode).
Reads jira_tickets.md for ticket descriptions.
Reads feature_input.yaml for project config (epic, labels, platform).
Outputs jira_payload.json with Jira API-compatible payloads.
"""
import json
import os
import re
import sys
import yaml


# Jira LOY project config
JIRA_CONFIG = {
    "project_key": "LOY",
    "cloud_id": "89647aba-aaa1-4669-9f6d-a9ad8db6435e",
    "story_points_field": "customfield_10053",
    "repository_field": "customfield_11585",
    "sprint_field": "customfield_10020",
    "component_ids": {
        "ios": "18967",
        "android": "18965",
        "backend": "18966",
    },
    "priority_ids": {
        "highest": "1",
        "high": "2",
        "medium": "3",
        "low": "4",
        "lowest": "5",
    },
    "default_assignee": "5eda5557a0b0350b9552af08",
    "herogen_agent": "712020:16313f8d-93e3-48d1-9d18-4058406403be",
    "default_repo": "deliveryhero/pd-mob-b2c-ios",
}


def extract_ticket_descriptions(tickets_md_path):
    """Extract ticket descriptions from jira_tickets.md keyed by ticket ID."""
    descriptions = {}
    if not os.path.exists(tickets_md_path):
        return descriptions

    with open(tickets_md_path, "r") as f:
        content = f.read()

    # Split by ticket headers (## TASK-XXX or ## [TASK-XXX])
    sections = re.split(r"\n(?=## )", content)
    for section in sections:
        # Find task ID in header
        match = re.match(r"## \[?(TASK-\S+)\]?", section)
        if match:
            task_id = match.group(1)
            # Remove the header line, keep the rest as description
            lines = section.split("\n", 1)
            desc = lines[1].strip() if len(lines) > 1 else ""
            descriptions[task_id] = desc

    return descriptions


def render(feature_dir):
    errors = []

    # Load task_specs.yaml
    specs_path = os.path.join(feature_dir, "task_specs.yaml")
    if not os.path.exists(specs_path):
        print(f"FAIL: task_specs.yaml not found in {feature_dir}", file=sys.stderr)
        return 1

    with open(specs_path, "r") as f:
        try:
            specs = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"FAIL: Invalid task_specs.yaml: {e}", file=sys.stderr)
            return 1

    # Load feature_input.yaml
    input_path = os.path.join(feature_dir, "feature_input.yaml")
    feature_input = {}
    if os.path.exists(input_path):
        with open(input_path, "r") as f:
            try:
                feature_input = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                pass

    # Load ticket descriptions
    tickets_md_path = os.path.join(feature_dir, "jira_tickets.md")
    descriptions = extract_ticket_descriptions(tickets_md_path)

    # Determine platform component
    platform = str(feature_input.get("platform", "ios")).lower()
    component_id = JIRA_CONFIG["component_ids"].get(platform, JIRA_CONFIG["component_ids"]["ios"])

    # Get labels and epic
    labels = feature_input.get("labels", [])
    if not labels:
        feature_name = feature_input.get("feature_name", "")
        if feature_name:
            labels = [feature_name, platform]
    epic_key = feature_input.get("epic_key", "")

    tasks = specs.get("tasks", [])
    payloads = []

    for task in tasks:
        if not isinstance(task, dict):
            continue

        task_id = task.get("id", "")
        title = task.get("title", "")
        sp = task.get("sp", 1)
        exec_mode = task.get("execution_mode", {})
        mode_type = exec_mode.get("type", "human") if isinstance(exec_mode, dict) else "human"

        # Determine assignee
        if mode_type == "herogen":
            assignee_id = JIRA_CONFIG["herogen_agent"]
        else:
            assignee_id = JIRA_CONFIG["default_assignee"]

        # Get description from tickets.md or generate from task spec
        description = descriptions.get(task_id, "")
        if not description:
            ac = task.get("acceptance_criteria", [])
            ac_text = "\n".join(f"- [ ] {c}" for c in ac) if ac else ""
            description = f"**Task**: {title}\n\n**Acceptance Criteria**:\n{ac_text}"

        # Build payload
        payload = {
            "task_id": task_id,
            "fields": {
                "project": {"key": JIRA_CONFIG["project_key"]},
                "issuetype": {"name": "Task"},
                "summary": f"[iOS] {title}" if platform == "ios" else title,
                "description": description,
                "priority": {"id": JIRA_CONFIG["priority_ids"]["high"]},
                "components": [{"id": component_id}],
                "labels": labels,
                "assignee": {"accountId": assignee_id},
                JIRA_CONFIG["story_points_field"]: sp,
                JIRA_CONFIG["repository_field"]: JIRA_CONFIG["default_repo"],
            },
        }

        if epic_key:
            payload["fields"]["parent"] = {"key": epic_key}

        payloads.append(payload)

    # Write output
    output_path = os.path.join(feature_dir, "jira_payload.json")
    with open(output_path, "w") as f:
        json.dump({"tickets": payloads, "count": len(payloads)}, f, indent=2)

    print(f"PASS: Generated {len(payloads)} Jira payloads → {output_path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: render_jira_payload.py <feature-dir>", file=sys.stderr)
        sys.exit(1)
    sys.exit(render(sys.argv[1]))
