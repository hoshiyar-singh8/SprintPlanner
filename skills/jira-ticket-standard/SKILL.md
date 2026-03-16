---
name: jira-ticket-standard
user-invocable: false
description: Ticket format, Hero Gen requirements, Jira config (LOY)
---

# Jira Ticket Standard

Background knowledge for agents that produce Jira ticket content.

## Jira Configuration (LOY Project)

| Field | Value |
|-------|-------|
| Cloud ID | `89647aba-aaa1-4669-9f6d-a9ad8db6435e` |
| Base URL | `https://deliveryhero.atlassian.net` |
| Project Key | `LOY` |
| Project ID | `12188` |
| Project Name | Pd Gr Mission Loyalty Offering |
| Issue Type | Always **Task** (never Story, Bug, Epic, Sub-task) |
| Default Assignee | Hoshiyar Singh (`5eda5557a0b0350b9552af08`) |
| Hero Gen Agent | `712020:16313f8d-93e3-48d1-9d18-4058406403be` |

### Custom Field IDs

| Field | ID |
|-------|-----|
| Story Points | `customfield_10053` (number) |
| Repository | `customfield_11585` (text) |
| Sprint | `customfield_10020` |

### Component IDs

| Platform | ID |
|----------|-----|
| iOS | `18967` |
| Android | `18965` |
| Backend | `18966` |

### Priority IDs

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
- **Component**: iOS | Android | Backend
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
- **Component**: iOS | Android
- **Type**: Hero Gen Task
- **Story Points**: [1 | 2 — max 2 for Hero Gen, prefer 1]

- **Layout Spec** (UI tasks only):
  ```
  [ASCII art layout diagram]
  ```
  - Padding: top/bottom Xpt, left/right Xpt
  - Element gap: Xpt
  - Corner radius: Xpt (specify which corners)
  - Icon: {icon-name} Xpt × Xpt

- **Bento Design Tokens** (UI tasks only):
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

- **Layout Code Block** (iOS/UIKit):
  ```swift
  private lazy var stackView: UIStackView = { ... }()
  private func setup() { ... }
  ```

- **update(with:) Code Block** (iOS/UIKit):
  ```swift
  func update(with viewModel: ViewModel) {
    // 1. Background color by state
    // 2. Icon image by state
    // 3. Primary label text
  }
  ```

- **Dependencies**: [Blocking tickets]
- **Estimated Effort**: X hours (≤4h for 1pt, ≤6h for 2pt)
```

## Jira API Payload Structure

```json
{
  "fields": {
    "project": { "key": "LOY" },
    "issuetype": { "name": "Task" },
    "summary": "[iOS] Task title here",
    "description": "Full markdown description",
    "priority": { "id": "1" },
    "components": [{ "id": "18967" }],
    "labels": ["feature-name", "ios"],
    "parent": { "key": "LOY-XXX" },
    "assignee": { "accountId": "5eda5557a0b0350b9552af08" },
    "customfield_10053": 1,
    "customfield_11585": "deliveryhero/pd-mob-b2c-ios"
  }
}
```

## Ticket Title Convention
- Prefix with `[iOS]` for iOS tasks
- Action-oriented: "Add", "Create", "Implement", "Wire", "Update"
- Include the specific component/module name

## Project Conventions
- Repository field: `deliveryhero/pd-mob-b2c-ios`
- Labels: feature-specific (e.g., `partnership-voucher`) + platform (`ios`)
- Epic parent: specified per feature (e.g., `LOY-865` for partnership voucher)
