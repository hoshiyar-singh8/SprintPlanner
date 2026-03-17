#!/usr/bin/env python3
"""Converts task_specs.yaml + jira_tickets.md → jira_payload.json.

Reads task_specs.yaml for structured data (SP, dependencies, layer, execution_mode).
Reads jira_tickets.md for ticket descriptions.
Reads feature_input.yaml for project config (epic, labels, platform).
Reads jira_config.yaml (optional) for Jira project-specific field IDs.
Outputs jira_payload.json with Jira API-compatible payloads.
"""
import json
import os
import re
import sys
import yaml


# Default Jira config — used when no jira_config.yaml is provided.
# Users should create jira_config.yaml in the feature dir or ~/.claude/ to override.
DEFAULT_JIRA_CONFIG = {
    "project_key": "PROJ",
    "story_points_field": "customfield_10053",
    "repository_field": "customfield_11585",
    "sprint_field": "customfield_10020",
    "component_ids": {
        "ios": "0",
        "android": "0",
        "web": "0",
        "backend": "0",
    },
    "priority_ids": {
        "highest": "1",
        "high": "2",
        "medium": "3",
        "low": "4",
        "lowest": "5",
    },
    "default_assignee": "",
    "herogen_agent": "",
    "default_repo": "",
}


def load_jira_config(feature_dir):
    """Load Jira config from feature dir, ~/.claude/, or fall back to defaults."""
    # Priority: feature_dir/jira_config.yaml > ~/.claude/jira_config.yaml > defaults
    search_paths = [
        os.path.join(feature_dir, "jira_config.yaml"),
        os.path.expanduser("~/.claude/jira_config.yaml"),
    ]

    for path in search_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                try:
                    user_config = yaml.safe_load(f) or {}
                    # Merge with defaults (user values override)
                    config = dict(DEFAULT_JIRA_CONFIG)
                    config.update(user_config)
                    # Deep merge component_ids and priority_ids
                    if "component_ids" in user_config:
                        config["component_ids"] = dict(
                            DEFAULT_JIRA_CONFIG["component_ids"]
                        )
                        config["component_ids"].update(user_config["component_ids"])
                    if "priority_ids" in user_config:
                        config["priority_ids"] = dict(
                            DEFAULT_JIRA_CONFIG["priority_ids"]
                        )
                        config["priority_ids"].update(user_config["priority_ids"])
                    print(f"INFO: Loaded Jira config from {path}")
                    return config
                except yaml.YAMLError:
                    pass

    print("WARN: No jira_config.yaml found — using placeholder defaults. "
          "Edit jira_payload.json manually or create jira_config.yaml.")
    return dict(DEFAULT_JIRA_CONFIG)


def extract_ticket_descriptions(tickets_md_path):
    """Extract ticket descriptions from jira_tickets.md keyed by ticket ID."""
    descriptions = {}
    if not os.path.exists(tickets_md_path):
        return descriptions

    with open(tickets_md_path, "r") as f:
        content = f.read()

    # Split by ticket headers (## TASK-XXX: or ## [TASK-XXX])
    sections = re.split(r"\n(?=## )", content)
    for section in sections:
        # Find task ID in header — strip trailing colon/punctuation
        match = re.match(r"## \[?(TASK-\d+)\]?", section)
        if match:
            task_id = match.group(1)
            # Remove the header line, keep the rest as description
            lines = section.split("\n", 1)
            desc = lines[1].strip() if len(lines) > 1 else ""
            descriptions[task_id] = desc

    return descriptions


def render(feature_dir):
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

    # Load Jira config
    jira_config = load_jira_config(feature_dir)

    # Load ticket descriptions
    tickets_md_path = os.path.join(feature_dir, "jira_tickets.md")
    descriptions = extract_ticket_descriptions(tickets_md_path)

    # Determine platform — support both old "platform" and new "detected_platform"
    platform = str(
        feature_input.get("detected_platform",
                          feature_input.get("platform", "ios"))
    ).lower()
    component_id = jira_config["component_ids"].get(
        platform, jira_config["component_ids"].get("ios", "0")
    )

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
        mode_type = (
            exec_mode.get("type", "human")
            if isinstance(exec_mode, dict)
            else "human"
        )

        # Determine assignee
        if mode_type == "herogen" and jira_config.get("herogen_agent"):
            assignee_id = jira_config["herogen_agent"]
        elif jira_config.get("default_assignee"):
            assignee_id = jira_config["default_assignee"]
        else:
            assignee_id = None

        # Get description from tickets.md or generate from task spec
        description = descriptions.get(task_id, "")
        if not description:
            ac = task.get("acceptance_criteria", [])
            ac_text = "\n".join(f"- [ ] {c}" for c in ac) if ac else ""
            description = (
                f"**Task**: {title}\n\n**Acceptance Criteria**:\n{ac_text}"
            )

        # Platform prefix for summary
        platform_prefix = {
            "ios": "[iOS]",
            "android": "[Android]",
            "web": "[Web]",
            "backend": "[BE]",
            "flutter": "[Flutter]",
        }
        prefix = platform_prefix.get(platform, "")
        summary = f"{prefix} {title}".strip() if prefix else title

        # Build payload
        payload = {
            "task_id": task_id,
            "fields": {
                "project": {"key": jira_config["project_key"]},
                "issuetype": {"name": "Task"},
                "summary": summary,
                "description": description,
                "priority": {"id": jira_config["priority_ids"]["high"]},
                "labels": labels,
                jira_config["story_points_field"]: sp,
            },
        }

        # Only add fields that have real values
        if component_id and component_id != "0":
            payload["fields"]["components"] = [{"id": component_id}]

        if assignee_id:
            payload["fields"]["assignee"] = {"accountId": assignee_id}

        if jira_config.get("default_repo"):
            payload["fields"][jira_config["repository_field"]] = (
                jira_config["default_repo"]
            )

        if epic_key:
            payload["fields"]["parent"] = {"key": epic_key}

        # Add execution_mode for downstream filtering
        if isinstance(exec_mode, dict) and exec_mode.get("type"):
            payload["execution_mode"] = exec_mode["type"]

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
