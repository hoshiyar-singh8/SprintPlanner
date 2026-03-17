#!/usr/bin/env python3
"""Creates Jira tickets from jira_payload.json via the Jira REST API.

Reads jira_payload.json and pushes each ticket to Jira.
Supports filtering, sprint assignment, and board targeting.

Requires:
  - JIRA_BASE_URL env var (e.g., https://your-org.atlassian.net)
  - JIRA_EMAIL env var
  - JIRA_API_TOKEN env var

Usage:
  python3 create_jira_tickets.py <feature-dir> [--dry-run]
  python3 create_jira_tickets.py <feature-dir> --filter herogen
  python3 create_jira_tickets.py <feature-dir> --filter human
  python3 create_jira_tickets.py <feature-dir> --filter TASK-001,TASK-003
  python3 create_jira_tickets.py <feature-dir> --sprint 42
  python3 create_jira_tickets.py <feature-dir> --push-plan push_plan.yaml
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request


def get_credentials():
    """Get Jira credentials from env vars."""
    base_url = os.environ.get("JIRA_BASE_URL", "")
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    return base_url, email, token


def create_issue(base_url, auth_header, payload):
    """Create a single Jira issue. Returns (key, error)."""
    url = f"{base_url}/rest/api/3/issue"
    data = json.dumps({"fields": payload["fields"]}).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Basic {auth_header}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return result.get("key"), None
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return None, f"HTTP {e.code}: {body[:300]}"
    except urllib.error.URLError as e:
        return None, f"Connection error: {e.reason}"


def load_push_plan(feature_dir, push_plan_file=None):
    """Load push_plan.yaml to get the filtered task list."""
    path = push_plan_file or os.path.join(feature_dir, "push_plan.yaml")
    if not os.path.exists(path):
        return None
    try:
        import yaml
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        if data and "tasks_to_push" in data:
            return {t["id"] for t in data["tasks_to_push"]}
    except Exception:
        pass
    return None


def filter_tickets(tickets, filter_value):
    """Filter tickets by execution mode or task IDs.

    filter_value can be:
      - "herogen" — only herogen tasks
      - "human" — only human tasks
      - "TASK-001,TASK-003" — specific task IDs
    """
    if filter_value in ("herogen", "human"):
        return [
            t for t in tickets
            if t.get("execution_mode") == filter_value
        ]
    else:
        # Comma-separated task IDs
        ids = {tid.strip() for tid in filter_value.split(",") if tid.strip()}
        return [t for t in tickets if t.get("task_id") in ids]


def assign_sprint(ticket, sprint_id, sprint_field):
    """Add sprint field to a ticket's fields."""
    if sprint_id and sprint_field:
        ticket["fields"][sprint_field] = sprint_id


def main():
    if len(sys.argv) < 2:
        print("Usage: create_jira_tickets.py <feature-dir> [options]",
              file=sys.stderr)
        print("  --dry-run         Preview without creating", file=sys.stderr)
        print("  --filter <value>  herogen|human|TASK-001,TASK-003",
              file=sys.stderr)
        print("  --sprint <id>     Jira sprint ID to assign tickets to",
              file=sys.stderr)
        print("  --push-plan <f>   Use push_plan.yaml for filtering",
              file=sys.stderr)
        sys.exit(1)

    feature_dir = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    # Parse optional flags
    filter_value = None
    sprint_id = None
    push_plan_file = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--filter" and i + 1 < len(args):
            filter_value = args[i + 1]
            i += 2
        elif args[i] == "--sprint" and i + 1 < len(args):
            sprint_id = args[i + 1]
            i += 2
        elif args[i] == "--push-plan" and i + 1 < len(args):
            push_plan_file = args[i + 1]
            i += 2
        elif args[i] == "--dry-run":
            i += 1
        else:
            i += 1

    payload_path = os.path.join(feature_dir, "jira_payload.json")
    if not os.path.exists(payload_path):
        print(f"FAIL: jira_payload.json not found in {feature_dir}",
              file=sys.stderr)
        sys.exit(1)

    with open(payload_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"FAIL: Invalid JSON in jira_payload.json: {e}",
                  file=sys.stderr)
            sys.exit(1)

    tickets = data.get("tickets", [])
    if not tickets:
        print("WARN: No tickets to create")
        sys.exit(0)

    # Apply filtering
    if push_plan_file or os.path.exists(
            os.path.join(feature_dir, "push_plan.yaml")):
        plan_ids = load_push_plan(feature_dir, push_plan_file)
        if plan_ids:
            tickets = [t for t in tickets if t.get("task_id") in plan_ids]
            print(f"INFO: Filtered to {len(tickets)} tickets from push plan")

    if filter_value:
        tickets = filter_tickets(tickets, filter_value)
        print(f"INFO: Filtered to {len(tickets)} tickets "
              f"(filter: {filter_value})")

    if not tickets:
        print("WARN: No tickets match the filter criteria")
        sys.exit(0)

    # Load sprint field from jira_config if sprint_id given
    sprint_field = None
    if sprint_id:
        config_path = os.path.join(feature_dir, "jira_config.yaml")
        if not os.path.exists(config_path):
            config_path = os.path.expanduser("~/.claude/jira_config.yaml")
        if os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                sprint_field = config.get("sprint_field")
            except Exception:
                pass
        if not sprint_field:
            print("WARN: --sprint given but no sprint_field found in "
                  "jira_config.yaml. Sprint will not be assigned.")
            sprint_id = None

    if dry_run:
        print(f"DRY RUN: Would create {len(tickets)} Jira tickets:")
        for idx, ticket in enumerate(tickets, 1):
            task_id = ticket.get("task_id", f"ticket-{idx}")
            summary = ticket.get("fields", {}).get("summary", "No title")
            project = ticket.get("fields", {}).get("project", {}).get(
                "key", "?")
            mode = ticket.get("execution_mode", "")
            mode_str = f" [{mode}]" if mode else ""
            sp = None
            for key, val in ticket.get("fields", {}).items():
                if key.startswith("customfield_") and isinstance(
                        val, (int, float)):
                    sp = val
                    break
            sp_str = f" ({sp} SP)" if sp else ""
            sprint_str = f" -> Sprint {sprint_id}" if sprint_id else ""
            print(f"  {idx}. [{project}] {task_id}: "
                  f"{summary}{sp_str}{mode_str}{sprint_str}")
        print(f"\nRun without --dry-run to create tickets.")
        sys.exit(0)

    # Real creation
    base_url, email, token = get_credentials()
    if not all([base_url, email, token]):
        missing = []
        if not base_url:
            missing.append("JIRA_BASE_URL")
        if not email:
            missing.append("JIRA_EMAIL")
        if not token:
            missing.append("JIRA_API_TOKEN")
        print(f"FAIL: Missing env vars: {', '.join(missing)}", file=sys.stderr)
        print("Set these environment variables to enable Jira ticket creation.",
              file=sys.stderr)
        sys.exit(1)

    auth_header = base64.b64encode(f"{email}:{token}".encode()).decode()

    # Assign sprint to all tickets if specified
    if sprint_id and sprint_field:
        for ticket in tickets:
            assign_sprint(ticket, int(sprint_id), sprint_field)

    print(f"Creating {len(tickets)} Jira tickets...")
    created = []
    failed = []

    for idx, ticket in enumerate(tickets, 1):
        task_id = ticket.get("task_id", f"ticket-{idx}")
        summary = ticket.get("fields", {}).get("summary", "No title")

        key, error = create_issue(base_url, auth_header, ticket)
        if key:
            print(f"  [{idx}/{len(tickets)}] {task_id} -> {key}: {summary}")
            ticket["jira_key"] = key
            created.append({"task_id": task_id, "jira_key": key})
        else:
            print(f"  [{idx}/{len(tickets)}] {task_id} FAILED: {error}")
            ticket["jira_error"] = error
            failed.append({"task_id": task_id, "error": error})

    # Update jira_payload.json with created keys
    data["created"] = data.get("created", []) + created
    data["failed"] = data.get("failed", []) + failed
    data["creation_status"] = "complete" if not failed else "partial"

    with open(payload_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nResults: {len(created)} created, {len(failed)} failed")

    if created:
        print(f"\nCreated tickets:")
        for c in created:
            url = f"{base_url}/browse/{c['jira_key']}"
            print(f"  {c['task_id']} -> {c['jira_key']}  {url}")

    if failed:
        print(f"\nFailed tickets:", file=sys.stderr)
        for f_item in failed:
            print(f"  {f_item['task_id']}: {f_item['error']}", file=sys.stderr)

    # Write push_log.md with clickable links
    if created:
        write_push_log(feature_dir, base_url, created, failed, tickets,
                       sprint_id, filter_value)

    # Update pipeline_state.yaml with push status
    update_pipeline_state(feature_dir, created, failed)

    if failed:
        sys.exit(1)

    print(f"\nPASS: All {len(created)} tickets created successfully")
    sys.exit(0)


def write_push_log(feature_dir, base_url, created, failed, tickets,
                   sprint_id, filter_value):
    """Write push_log.md with links to all created tickets."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build lookup from task_id to ticket details
    ticket_map = {}
    for t in tickets:
        tid = t.get("task_id", "")
        summary = t.get("fields", {}).get("summary", "")
        mode = t.get("execution_mode", "")
        sp = None
        for key, val in t.get("fields", {}).items():
            if key.startswith("customfield_") and isinstance(val, (int, float)):
                sp = val
                break
        project = t.get("fields", {}).get("project", {}).get("key", "?")
        ticket_map[tid] = {
            "summary": summary, "mode": mode, "sp": sp, "project": project
        }

    total_sp = sum(
        (ticket_map.get(c["task_id"], {}).get("sp") or 0) for c in created
    )
    herogen_count = sum(
        1 for c in created
        if ticket_map.get(c["task_id"], {}).get("mode") == "herogen"
    )
    human_count = len(created) - herogen_count
    project = next(
        (ticket_map[c["task_id"]]["project"]
         for c in created if c["task_id"] in ticket_map), "?"
    )

    strategy = "filtered" if filter_value else "full plan"
    sprint_str = f"Sprint {sprint_id}" if sprint_id else "Unassigned"

    lines = [
        f"# Push Log — {feature_dir.rstrip('/').split('/')[-1]}",
        f"Pushed: {now}",
        f"Project: {project}",
        f"Sprint: {sprint_str}",
        f"Strategy: {strategy}",
        "",
        f"## Created ({len(created)} tickets, {int(total_sp)} SP"
        f" — {herogen_count} HeroGen, {human_count} Human)",
        "",
        "| # | Task ID | Jira Key | Title | SP | Type | URL |",
        "|---|---------|----------|-------|----|------|-----|",
    ]

    for idx, c in enumerate(created, 1):
        tid = c["task_id"]
        jkey = c["jira_key"]
        info = ticket_map.get(tid, {})
        url = f"{base_url}/browse/{jkey}"
        sp_val = int(info.get("sp") or 0) if info.get("sp") else "—"
        mode = info.get("mode", "—")
        summary = info.get("summary", "—")
        lines.append(
            f"| {idx} | {tid} | {jkey} | {summary} | {sp_val} | {mode} | "
            f"[{jkey}]({url}) |"
        )

    if failed:
        lines.extend([
            "",
            f"## Failed ({len(failed)} tickets)",
            "",
            "| Task ID | Error |",
            "|---------|-------|",
        ])
        for f_item in failed:
            lines.append(f"| {f_item['task_id']} | {f_item['error'][:100]} |")

    lines.append("")

    log_path = os.path.join(feature_dir, "push_log.md")
    # Append if log already exists (multiple push rounds)
    mode = "a" if os.path.exists(log_path) else "w"
    with open(log_path, mode) as f:
        if mode == "a":
            f.write("\n---\n\n")
        f.write("\n".join(lines))

    print(f"\nPush log written to {log_path}")


def update_pipeline_state(feature_dir, created, failed):
    """Update pipeline_state.yaml with push status."""
    state_path = os.path.join(feature_dir, "pipeline_state.yaml")
    if not os.path.exists(state_path):
        return

    with open(state_path, "r") as f:
        content = f.read()

    status = "pushed" if not failed else "partial"

    if "push_status:" in content:
        lines = content.split("\n")
        lines = [
            f"push_status: {status}" if l.startswith("push_status:") else l
            for l in lines
        ]
        content = "\n".join(lines)
    else:
        content = content.rstrip() + f"\npush_status: {status}\n"

    with open(state_path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    main()
