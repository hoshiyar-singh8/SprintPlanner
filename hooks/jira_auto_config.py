#!/usr/bin/env python3
"""Auto-generates jira_config.yaml from a Jira project URL or key.

Uses the Jira REST API to discover:
  - Project key, ID, name
  - Components (mapped by platform name)
  - Custom fields (story points, sprint, repository)
  - Priorities
  - Current user as default assignee

Requires:
  - JIRA_BASE_URL env var or --url flag (e.g., https://your-org.atlassian.net)
  - JIRA_EMAIL env var or --email flag
  - JIRA_API_TOKEN env var or --token flag

Usage:
  python3 jira_auto_config.py --project PROJ [--epic PROJ-100] [--output ./jira_config.yaml]
  python3 jira_auto_config.py --url https://your-org.atlassian.net/projects/PROJ [--epic PROJ-100]
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error

try:
    import yaml
except ImportError:
    print("FAIL: PyYAML required — run: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)


def parse_jira_url(url):
    """Extract base_url and project_key from a Jira URL."""
    # Patterns:
    #   https://org.atlassian.net/projects/PROJ
    #   https://org.atlassian.net/jira/software/projects/PROJ/board
    #   https://org.atlassian.net/browse/PROJ-123  (epic link)
    patterns = [
        r"(https?://[^/]+)/.*?projects?/([A-Z][A-Z0-9_]+)",
        r"(https?://[^/]+)/browse/([A-Z][A-Z0-9_]+)-\d+",
        r"(https?://[^/]+)/browse/([A-Z][A-Z0-9_]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
    return None, None


def parse_epic_key(epic_input):
    """Extract epic key from a URL or direct key."""
    if not epic_input:
        return None
    # Direct key like PROJ-123
    if re.match(r"^[A-Z][A-Z0-9_]+-\d+$", epic_input):
        return epic_input
    # URL like https://org.atlassian.net/browse/PROJ-123
    match = re.search(r"/browse/([A-Z][A-Z0-9_]+-\d+)", epic_input)
    if match:
        return match.group(1)
    return epic_input


class JiraClient:
    def __init__(self, base_url, email, api_token):
        self.base_url = base_url.rstrip("/")
        self.auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()

    def _get(self, path):
        url = f"{self.base_url}/rest/api/3/{path}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Basic {self.auth}")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            print(f"FAIL: Jira API error {e.code} on {path}: {body[:200]}",
                  file=sys.stderr)
            return None
        except urllib.error.URLError as e:
            print(f"FAIL: Cannot reach Jira at {self.base_url}: {e.reason}",
                  file=sys.stderr)
            return None

    def get_project(self, project_key):
        return self._get(f"project/{project_key}")

    def get_components(self, project_key):
        return self._get(f"project/{project_key}/components")

    def get_priorities(self):
        return self._get("priority")

    def get_fields(self):
        return self._get("field")

    def get_myself(self):
        return self._get("myself")

    def get_boards(self, project_key):
        """Get boards for a project (uses Agile API)."""
        url = (f"{self.base_url}/rest/agile/1.0/board"
               f"?projectKeyOrId={project_key}&type=scrum")
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Basic {self.auth}")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.HTTPError, urllib.error.URLError):
            return None

    def get_sprints(self, board_id, state="active,future"):
        """Get sprints for a board (uses Agile API)."""
        url = (f"{self.base_url}/rest/agile/1.0/board/{board_id}"
               f"/sprint?state={state}")
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Basic {self.auth}")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.HTTPError, urllib.error.URLError):
            return None


def detect_platform_from_component(name):
    """Map a Jira component name to a platform key."""
    name_lower = name.lower()
    mappings = {
        "ios": ["ios", "iphone", "ipad", "swift", "apple"],
        "android": ["android", "kotlin", "java"],
        "web": ["web", "frontend", "react", "vue", "angular", "next"],
        "backend": ["backend", "server", "api", "service", "be"],
        "flutter": ["flutter", "dart"],
    }
    for platform, keywords in mappings.items():
        if any(kw in name_lower for kw in keywords):
            return platform
    return None


def find_custom_field(fields, *search_terms):
    """Find a custom field ID by searching name/description."""
    if not fields:
        return None
    for field in fields:
        if not field.get("id", "").startswith("customfield_"):
            continue
        name = (field.get("name") or "").lower()
        for term in search_terms:
            if term.lower() in name:
                return field["id"]
    return None


def generate_config(client, project_key, epic_key=None):
    """Query Jira API and build config dict."""
    config = {}

    # 1. Project info
    print(f"  Fetching project {project_key}...")
    project = client.get_project(project_key)
    if not project:
        print(f"FAIL: Could not fetch project {project_key}", file=sys.stderr)
        return None
    config["project_key"] = project["key"]

    # 2. Components → platform mapping
    print("  Fetching components...")
    components = client.get_components(project_key)
    if components:
        component_ids = {}
        for comp in components:
            platform = detect_platform_from_component(comp["name"])
            if platform:
                component_ids[platform] = str(comp["id"])
            # Also store the raw name → id for reference
        if component_ids:
            config["component_ids"] = component_ids
            print(f"    Found {len(component_ids)} platform components: "
                  f"{', '.join(f'{k}={v}' for k, v in component_ids.items())}")

    # 3. Custom fields (story points, sprint, repo)
    print("  Fetching custom fields...")
    fields = client.get_fields()
    if fields:
        sp_field = find_custom_field(fields, "story point", "story_point",
                                     "storypoint")
        if sp_field:
            config["story_points_field"] = sp_field
            print(f"    Story points: {sp_field}")

        sprint_field = find_custom_field(fields, "sprint")
        if sprint_field:
            config["sprint_field"] = sprint_field
            print(f"    Sprint: {sprint_field}")

        repo_field = find_custom_field(fields, "repository", "repo",
                                       "source repo")
        if repo_field:
            config["repository_field"] = repo_field
            print(f"    Repository: {repo_field}")

    # 4. Priorities
    print("  Fetching priorities...")
    priorities = client.get_priorities()
    if priorities:
        priority_ids = {}
        for p in priorities:
            name = p.get("name", "").lower()
            if name in ("highest", "high", "medium", "low", "lowest"):
                priority_ids[name] = str(p["id"])
        if priority_ids:
            config["priority_ids"] = priority_ids

    # 5. Current user as default assignee
    print("  Fetching current user...")
    myself = client.get_myself()
    if myself:
        config["default_assignee"] = myself.get("accountId", "")
        display = myself.get("displayName", "unknown")
        print(f"    Default assignee: {display} ({config['default_assignee']})")

    # 6. Epic key
    if epic_key:
        config["epic_key"] = epic_key
        print(f"    Epic: {epic_key}")

    # 7. Sprint discovery
    print("  Discovering sprints...")
    boards = client.get_boards(project_key)
    if boards and boards.get("values"):
        board = boards["values"][0]  # Use the first scrum board
        board_id = board["id"]
        config["board_id"] = board_id
        config["board_name"] = board.get("name", "")
        print(f"    Board: {board.get('name', '')} (id: {board_id})")

        sprints = client.get_sprints(board_id)
        if sprints and sprints.get("values"):
            sprint_list = []
            for s in sprints["values"]:
                sprint_info = {
                    "id": s["id"],
                    "name": s.get("name", ""),
                    "state": s.get("state", ""),
                }
                if s.get("startDate"):
                    sprint_info["start_date"] = s["startDate"]
                if s.get("endDate"):
                    sprint_info["end_date"] = s["endDate"]
                sprint_list.append(sprint_info)
            config["available_sprints"] = sprint_list

            # Identify current active sprint
            active = [s for s in sprint_list if s["state"] == "active"]
            if active:
                config["active_sprint_id"] = active[0]["id"]
                config["active_sprint_name"] = active[0]["name"]
                print(f"    Active sprint: {active[0]['name']} "
                      f"(id: {active[0]['id']})")

            # List future sprints
            future = [s for s in sprint_list if s["state"] == "future"]
            if future:
                print(f"    Future sprints: "
                      f"{', '.join(s['name'] for s in future)}")
    else:
        print("    No scrum boards found (Kanban or no board)")

    return config


def get_credentials(args):
    """Get Jira credentials from args or env vars."""
    base_url = args.url or os.environ.get("JIRA_BASE_URL", "")
    email = args.email or os.environ.get("JIRA_EMAIL", "")
    token = args.token or os.environ.get("JIRA_API_TOKEN", "")

    # If --url is a full project URL, extract base_url and project from it
    if base_url and "/" in base_url and "atlassian" in base_url:
        parsed_base, parsed_key = parse_jira_url(base_url)
        if parsed_base:
            base_url = parsed_base
            if not args.project:
                args.project = parsed_key

    return base_url, email, token


def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate jira_config.yaml from Jira API")
    parser.add_argument("--project", "-p",
                        help="Jira project key (e.g., PROJ)")
    parser.add_argument("--epic", "-e",
                        help="Epic key or URL (e.g., PROJ-100)")
    parser.add_argument("--url", "-u",
                        help="Jira base URL or project URL")
    parser.add_argument("--email",
                        help="Jira email (or set JIRA_EMAIL env var)")
    parser.add_argument("--token",
                        help="Jira API token (or set JIRA_API_TOKEN env var)")
    parser.add_argument("--output", "-o",
                        help="Output path (default: ~/.claude/jira_config.yaml)")
    args = parser.parse_args()

    base_url, email, token = get_credentials(args)

    if not base_url:
        print("FAIL: Jira URL required. Set JIRA_BASE_URL env var or use --url",
              file=sys.stderr)
        sys.exit(1)
    if not email:
        print("FAIL: Jira email required. Set JIRA_EMAIL env var or use --email",
              file=sys.stderr)
        sys.exit(1)
    if not token:
        print("FAIL: Jira API token required. Set JIRA_API_TOKEN env var or "
              "use --token\n"
              "  Create one at: https://id.atlassian.net/manage-profile/security/api-tokens",
              file=sys.stderr)
        sys.exit(1)
    if not args.project:
        print("FAIL: Project key required. Use --project PROJ or pass a full "
              "Jira project URL", file=sys.stderr)
        sys.exit(1)

    epic_key = parse_epic_key(args.epic) if args.epic else None

    print(f"INFO: Connecting to {base_url}...")
    client = JiraClient(base_url, email, token)
    config = generate_config(client, args.project, epic_key)

    if not config:
        sys.exit(1)

    # Write output
    output_path = args.output or os.path.expanduser("~/.claude/jira_config.yaml")
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\nPASS: Generated jira_config.yaml → {output_path}")
    print(f"  Project: {config.get('project_key')}")
    if config.get('component_ids'):
        print(f"  Components: {config['component_ids']}")
    if config.get('default_assignee'):
        print(f"  Assignee: {config['default_assignee']}")
    if epic_key:
        print(f"  Epic: {epic_key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
