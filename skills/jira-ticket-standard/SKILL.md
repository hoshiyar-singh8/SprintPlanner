---
name: jira-ticket-standard
user-invocable: false
description: Ticket format, Hero Gen requirements, Jira API payload structure
---

# Jira Ticket Standard

Background knowledge for agents that produce Jira ticket content.

## Jira Configuration

Configuration is loaded from `jira_config.yaml` (feature dir or `~/.claude/`).
The `render_jira_payload.py` hook reads this config and generates API-ready payloads.

Key config fields:
- `project_key` — Jira project key (e.g., "LOY", "ANDROID", "WEB")
- `story_points_field` — Custom field ID for story points
- `repository_field` — Custom field ID for repository name
- `component_ids` — Map of platform → Jira component ID
- `default_assignee` — Account ID for human tasks
- `herogen_agent` — Account ID for bot tasks

See `jira_config.template.yaml` for all available fields.

### Issue Type

Always **Task** (never Story, Bug, Epic, Sub-task).

### Priority IDs (Standard)

| Priority | ID |
|----------|-----|
| Highest | `1` |
| High | `2` |
| Medium | `3` |
| Low | `4` |
| Lowest | `5` |

## Human Developer Ticket Format

```markdown
## [TICKET-ID] Title
- **Title**: Clear, action-oriented (e.g., "Add is_partnership_voucher_enabled config key")
- **Component**: iOS | Android | Backend | Web
- **Assignee**: [Name or TBD]
- **Story Points**: [1 | 2 | 3 — max 3, prefer 1]
- **Description**:
  - What needs to be done (specific, unambiguous)
  - Acceptance criteria (bullet points)
  - Technical notes (relevant code paths, patterns to follow)
- **Dependencies**: [List any blocking tickets]
- **Definition of Done**:
  - [ ] Code implemented
  - [ ] Unit tests passing
  - [ ] Code review approved
```

## Hero Gen (Bot) Ticket Format

Hero Gen tasks must be significantly more detailed since a bot executes them:

```markdown
## [TICKET-ID] Title
- **Title**: Precise, unambiguous title
- **Component**: iOS | Android | Web
- **Type**: Hero Gen Task
- **Story Points**: [1 | 2 — max 2 for Hero Gen, prefer 1]

- **Layout Spec** (UI tasks only):
  ```
  [ASCII art layout diagram]
  ```
  - Padding: top/bottom Xpt, left/right Xpt
  - Element gap: Xpt
  - Corner radius: Xpt (specify which corners)
  - Icon: {icon-name} Xpt x Xpt

- **Design Tokens** (UI tasks only):
  - Background: .tokenName
  - Label font: .tokenName
  - Label color: .tokenName

- **Out of Scope** (UI tasks — explicit exclusion list):
  - e.g., Tap action handling
  - e.g., Wiring into parent ViewController
  - e.g., Presenter / Interactor changes

- **Files to Create**:
  - `path/to/ViewModel.swift`
  - `path/to/View.swift`

- **Detailed Description**:
  - **Context**: Why this task exists (1-2 sentences)
  - **Exact Requirements**: Step-by-step with file paths, code patterns, naming conventions
  - **Input/Output Specification**: What the code accepts and returns
  - **Edge Cases to Handle**: Explicit list
  - **Testing Requirements**: Specific test cases, expected behaviors, mock setup
  - **Acceptance Criteria**: Numbered, each testable
  - **Anti-patterns to Avoid**: Implementation-specific "do NOT" list

- **Reference Implementation**: File path + deviation table:
  ```
  | Aspect | Reference (ExistingView) | New (NewView) |
  |--------|--------------------------|---------------|
  | Corner radius | .cornerRadiusSm | .cornerRadiusContainerEdge |
  | States | Single | Two: .stateA / .stateB |
  ```

- **Layout Code Block** (platform-specific starter code)

- **Dependencies**: [Blocking tickets]
- **Estimated Effort**: X hours (<=4h for 1pt, <=6h for 2pt)
```

## Jira API Payload Structure

The `render_jira_payload.py` hook generates this from `task_specs.yaml` + `jira_config.yaml`:

```json
{
  "fields": {
    "project": { "key": "<from jira_config>" },
    "issuetype": { "name": "Task" },
    "summary": "[Platform] Task title here",
    "description": "Full markdown description",
    "priority": { "id": "2" },
    "components": [{ "id": "<from jira_config>" }],
    "labels": ["feature-name", "platform"],
    "parent": { "key": "<epic_key from feature_input>" },
    "assignee": { "accountId": "<from jira_config>" },
    "<story_points_field>": 1,
    "<repository_field>": "<default_repo from jira_config>"
  }
}
```

## Ticket Title Convention
- Prefix with platform tag: `[iOS]`, `[Android]`, `[Web]`, `[BE]`, `[Flutter]`
- Action-oriented: "Add", "Create", "Implement", "Wire", "Update"
- Include the specific component/module name

## Project Conventions
- Labels: feature-specific (e.g., `partnership-voucher`) + platform (e.g., `ios`)
- Epic parent: specified per feature in `feature_input.yaml`
- Repository: configured in `jira_config.yaml`
