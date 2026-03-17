---
name: jira-ticket-standard
user-invocable: false
description: Ticket format, Hero Gen requirements, Jira API payload structure
---

# Jira Ticket Standard

Background knowledge for agents that produce Jira ticket content.
Based on analysis of real HeroGen PRs — what gets MERGED vs CLOSED.

## What Makes a HeroGen Ticket Succeed

From studying merged HeroGen PRs across iOS and Android:

1. **Single responsibility** — one clear deliverable per ticket (not "add model + mapper + view")
2. **Explicit file change table** — every file listed with what changes
3. **Concrete test plan** — checkbox items with exact conditions, not "test it works"
4. **Scope boundary** — explicitly says what's NOT included (critical for scope-1 UI)
5. **Design tokens by name** — `.proDealHighlight1`, `.cornerRadiusContainerEdge`, never hex
6. **Figma node references** — `Figma node 698-45462` for UI tasks
7. **Reference file** — "follow pattern in `ExistingView.swift`" with deviation table
8. **Unit tests in same PR** — test requirements must be concrete enough for HeroGen to write them

What causes HeroGen to FAIL:
- Tickets that cross layers (model + mapper + view in one ticket)
- Tickets that require understanding integration context the bot doesn't have
- Overly split tickets (3 separate tickets for one component's states — combine them)
- Vague acceptance criteria ("works correctly" instead of "returns nil when input is empty")
- Missing mock/test infrastructure context
- Incomplete field coverage in mappers/comparators (reviewer: "compare ALL values, add missing ones")
- Wrong target branch — ticket must specify if a feature branch exists

## Common Review Rework (Encode in Tickets to Prevent)

From studying reviewer feedback on HeroGen PRs:

### iOS Style Rules (Prevent Gemini/Reviewer Rework)
- Parameterless builder functions MUST be computed properties, not functions (IOS-0002)
- Never use `== true` or `== false` in comparisons or assertions (IOS-0009)
- No redundant `return` in single-expression computed properties
- Test factories should be nouns: `sut(...)` not `makeSUT(...)`
- Use exact assertion values: `XCTAssertEqual(x, 32.0)` not `XCTAssertGreaterThan(x, 0)`

### Android Rules (Prevent Reviewer Rework)
- Do NOT add optional defaults (`= null`) on parameters that every call site always provides
- Depend on API/abstraction modules, not implementation modules (`api(projects.fooApi)` not `implementation(projects.foo)`)
- Cleanup PRs must not include unrelated diffs (import reordering, empty lines in unrelated files)

### Both Platforms
- Mapper/comparator tickets MUST list ALL fields to map — enumerate them explicitly in the ticket
- Cleanup tickets MUST also remove empty wrapper functions and their call sites (don't leave dead code)
- Do NOT add parameters "for future use" — add them when actually needed (YAGNI)
- If a feature branch exists for the ticket prefix, specify it as the target branch

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
- **Component**: iOS | Android | Backend | Web
- **Story Points**: [1 | 2 | 3]

### Context
[Why this task exists — 1-2 sentences linking to the feature goal]

### Requirements
1. [Specific requirement with file path]
2. [Another requirement]

### Acceptance Criteria
- [ ] [Testable criterion]
- [ ] [Another testable criterion]
- [ ] Unit tests passing

### Files to Modify
| File | Change |
|------|--------|
| `path/to/file.swift` | Add X method |
| `path/to/other.swift` | Update Y protocol |

### Technical Notes
- Follow pattern in `path/to/reference.swift`
- [Key architectural decision or constraint]

### Dependencies
- [TICKET-ID]: [What it provides]
```

## Hero Gen Ticket Format

HeroGen tickets must be self-contained — the bot reads ONLY the ticket description.
Every piece of information the bot needs must be in the ticket.

### API / Data Layer Tasks

```markdown
## [TICKET-ID] Add voucher_code query param to partnership endpoint

- **Component**: iOS
- **Type**: Hero Gen Task
- **Story Points**: 1

### Context
The partnership enrollment flow needs to forward an optional voucher code
to the backend API when fetching partnership details.

### Files to Modify
| File | Change |
|------|--------|
| `SubscriptionResource.swift` | Add `voucherCode: String?` param to `fetchPartnershipDetails` |
| `PartnershipsClient.swift` | Update protocol + impl to accept and forward `voucherCode` |
| `PartnershipsRepository.swift` | Pass through `voucherCode` |

### Exact Requirements
1. Add `voucherCode: String?` parameter (default `nil`) to `fetchPartnershipDetails`
2. When non-nil, append `?voucher_code=<code>` to the URL
3. When nil, omit the query parameter entirely (preserve existing behavior)
4. Update all call sites to pass `voucherCode: nil` for backward compatibility

### Acceptance Criteria
- [ ] `fetchPartnershipDetails(planCode: "klarna", voucherCode: "FREE-123")` → URL contains `?voucher_code=FREE-123`
- [ ] `fetchPartnershipDetails(planCode: "klarna", voucherCode: nil)` → URL has no query param
- [ ] All existing tests pass without modification
- [ ] New unit tests cover both cases

### Reference Implementation
Follow `SubscriptionResource.fetchPartnershipDetails` existing pattern.
| Aspect | Current | New |
|--------|---------|-----|
| Parameters | `planCode: String` | `planCode: String, voucherCode: String? = nil` |
| URL construction | Fixed path only | Conditional `?voucher_code=` query param |

### Anti-patterns
- Do NOT use force unwrap on voucherCode
- Do NOT modify the enrollment POST endpoint — only the GET details endpoint
- Do NOT add feature flag gating in this task (handled separately)

### Testing Requirements
- Test file: `SubscriptionResourceTests.swift` (create if needed)
- Test 1: Call with voucherCode="FREE-123" → assert URL contains query param
- Test 2: Call with voucherCode=nil → assert URL has no query param
```

### UI Component Tasks (Scope 1)

```markdown
## [TICKET-ID] Create PartnershipVoucherBannerView — Two-State Sticky Banner

- **Component**: iOS
- **Type**: Hero Gen Task
- **Story Points**: 2

### Context
Partnership plans can include a voucher. The banner shows either an "unapplied"
state (prompting the user to apply) or an "applied" state (confirming discount).

### Scope
Pure UI (Scope 1) — ViewModel struct + View only. Zero existing files modified.

### Out of Scope
- Tap action handling / delegate wiring
- Wiring into parent ViewController
- Presenter / Interactor changes
- Navigation logic

### Files to Create
| File | Path |
|------|------|
| `PartnershipVoucherBannerViewModel.swift` | `Subscription/Source/Views/Partnerships/Views/` |
| `PartnershipVoucherBannerView.swift` | `Subscription/Source/Views/Partnerships/Views/` |

### Layout Spec
```
[Icon 24×24] ——8pt—— [Title label (flex)] ——8pt—— [CTA label]
└──── 16pt padding ────────────────────────────── 16pt padding ─┘
                    8pt top / 8pt bottom
Top-left + top-right corners: 16pt radius. Bottom corners: square.
```

### Design Tokens
| Element | Unapplied State | Applied State |
|---------|----------------|---------------|
| Background | `.proDealHighlight1` | `.feedbackPositiveSurface` |
| Icon | `icVoucherFilled` | `icSuccessFilled` |
| Title font | `.bodyBase` | `.bodyBase` |
| Title color | `.neutralPrimary` | `.neutralPrimary` |
| CTA font | `.highlightBase` | `.highlightBase` |
| CTA color | `.interactionSecondary` | `.interactionSecondary` |
| Corner radius | `.cornerRadiusContainerEdge` (top only) | `.cornerRadiusContainerEdge` (top only) |
| Stack spacing | `.spacingXs` (8pt) | `.spacingXs` (8pt) |
| Horizontal padding | `.spacingSm` (16pt) | `.spacingSm` (16pt) |

### Figma References
- Unapplied: Figma node `698-45462`
- Applied: Figma node `698-45093`

### ViewModel Definition
```swift
enum PartnershipVoucherBannerState {
    case unapplied
    case applied
}

struct PartnershipVoucherBannerViewModel {
    let state: PartnershipVoucherBannerState
    let bannerText: String
    let ctaText: String
}
```

### View Structure
```swift
final class PartnershipVoucherBannerView: UIView {
    // Horizontal UIStackView: icon + titleLabel + ctaLabel
    // update(with: PartnershipVoucherBannerViewModel) switches state appearance
}
```

### Reference Implementation
Follow `EnrolmentVoucherBannerView.swift` pattern.
| Aspect | Reference (`EnrolmentVoucherBannerView`) | New (`PartnershipVoucherBannerView`) |
|--------|------------------------------------------|-------------------------------------|
| States | Single (always visible) | Two: `.unapplied` / `.applied` |
| Corner radius | `.cornerRadiusSm` (all corners) | `.cornerRadiusContainerEdge` (top only) |
| Icon rendering | `.alwaysOriginal` | `.alwaysTemplate` (tinted) |
| CTA | None | Trailing label with interactionSecondary color |

### Acceptance Criteria
- [ ] `update(with:)` with `.unapplied` → background is `.proDealHighlight1`, icon is `icVoucherFilled`
- [ ] `update(with:)` with `.applied` → background is `.feedbackPositiveSurface`, icon is `icSuccessFilled`
- [ ] Top corners rounded at 16pt, bottom corners square (`layer.maskedCorners`)
- [ ] Stack spacing is 8pt, vertical padding 8pt, horizontal padding 16pt
- [ ] Title uses `.bodyBase` font and `.neutralPrimary` color
- [ ] CTA uses `.highlightBase` font and `.interactionSecondary` color
- [ ] Icon constrained to 24×24pt with `.alwaysTemplate` rendering mode
- [ ] No existing files modified (diff is only new files)

### Anti-patterns
- Do NOT use raw hex colors — Bento tokens only
- Do NOT add delegate/protocol for tap handling (out of scope)
- Do NOT import UIKit components when Bento equivalents exist
- Do NOT hardcode strings — use ViewModel properties
```

### Config Flag Tasks

```markdown
## [TICKET-ID] Add isPartnershipVoucherEnabled config flag

- **Component**: iOS
- **Type**: Hero Gen Task
- **Story Points**: 1

### Context
Feature flag to gate the partnership voucher flow. Must be false by default.

### Files to Modify
| File | Change |
|------|--------|
| `Configuration.swift` | Add `isPartnershipVoucherEnabled: Bool` property |
| `ConfigurationProvider.swift` | Add S3 key mapping + version gating |

### Exact Requirements
1. Add `isPartnershipVoucherEnabled` property to Configuration protocol
2. Default value: `false`
3. S3 key: `is_partnership_voucher_enabled` (following existing naming pattern)
4. Apply version gating: only enabled for app version >= [specified version]

### Reference Implementation
Follow `isPartnershipsPlanEnabled` pattern in the same files.

### Acceptance Criteria
- [ ] Flag defaults to `false`
- [ ] Flag reads from S3 config correctly
- [ ] Version gating applied
- [ ] Existing tests pass

### Anti-patterns
- Do NOT use a hardcoded `true` default
- Do NOT skip version gating
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
- Action-oriented: "Add", "Create", "Implement", "Wire", "Update", "Clean up"
- Include the specific component/module name
- Example: `[iOS] Create PartnershipVoucherBannerView — Two-State Sticky Banner`

## Task Granularity Rules (from real HeroGen success/failure data)

### DO — Tasks that merge successfully:
- Single new UIView/Composable with ViewModel (all states in one task)
- Single API endpoint addition (query param, new route)
- Single config flag
- Single mapper (one direction)
- Module creation with clear public API
- Cleanup/deletion of old code behind removed flag

### DON'T — Tasks that get closed/rejected:
- Multiple UI states split across separate tickets (combine into one component ticket)
- Model + mapper + view in one ticket (split by layer)
- Tasks requiring understanding of runtime integration flow
- Tasks that modify many existing files without clear patterns
- Tasks with vague scope ("implement voucher flow")
