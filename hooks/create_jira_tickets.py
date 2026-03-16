#!/usr/bin/env python3
"""Creates Jira tickets from jira_payload.json via the Jira REST API.

Reads jira_payload.json and pushes each ticket to Jira.
Supports --dry-run to preview without creating.
Updates jira_payload.json with created ticket keys.

Requires:
  - JIRA_BASE_URL env var (e.g., https://your-org.atlassian.net)
  - JIRA_EMAIL env var
  - JIRA_API_TOKEN env var

Usage:
  python3 create_jira_tickets.py <feature-dir> [--dry-run]
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


def main():
    if len(sys.argv) < 2:
        print("Usage: create_jira_tickets.py <feature-dir> [--dry-run]",
              file=sys.stderr)
        sys.exit(1)

    feature_dir = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

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

    if dry_run:
        print(f"DRY RUN: Would create {len(tickets)} Jira tickets:")
        for i, ticket in enumerate(tickets, 1):
            task_id = ticket.get("task_id", f"ticket-{i}")
            summary = ticket.get("fields", {}).get("summary", "No title")
            project = ticket.get("fields", {}).get("project", {}).get("key", "?")
            sp = None
            for key, val in ticket.get("fields", {}).items():
                if key.startswith("customfield_") and isinstance(val, (int, float)):
                    sp = val
                    break
            sp_str = f" ({sp} SP)" if sp else ""
            print(f"  {i}. [{project}] {task_id}: {summary}{sp_str}")
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

    print(f"Creating {len(tickets)} Jira tickets...")
    created = []
    failed = []

    for i, ticket in enumerate(tickets, 1):
        task_id = ticket.get("task_id", f"ticket-{i}")
        summary = ticket.get("fields", {}).get("summary", "No title")

        key, error = create_issue(base_url, auth_header, ticket)
        if key:
            print(f"  [{i}/{len(tickets)}] {task_id} -> {key}: {summary}")
            ticket["jira_key"] = key
            created.append({"task_id": task_id, "jira_key": key})
        else:
            print(f"  [{i}/{len(tickets)}] {task_id} FAILED: {error}")
            ticket["jira_error"] = error
            failed.append({"task_id": task_id, "error": error})

    # Update jira_payload.json with created keys
    data["created"] = created
    data["failed"] = failed
    data["creation_status"] = "complete" if not failed else "partial"

    with open(payload_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nResults: {len(created)} created, {len(failed)} failed")

    if created:
        print(f"\nCreated tickets:")
        for c in created:
            print(f"  {c['task_id']} -> {c['jira_key']}")

    if failed:
        print(f"\nFailed tickets:", file=sys.stderr)
        for f_item in failed:
            print(f"  {f_item['task_id']}: {f_item['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"\nPASS: All {len(created)} tickets created successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
