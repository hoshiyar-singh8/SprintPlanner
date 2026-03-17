---
name: rfc-reading
user-invocable: false
description: RFC/PRD reading, requirement extraction, gap identification
---

# RFC Reading Skill

Background knowledge for agents that need to read and analyze RFC/PRD documents.

## RFC Intake Workflow

1. **Read the full document** using file reading tools (supports PDF, Markdown, plain text)
2. **Produce a structured summary** — 3-5 bullet points of key feature requirements
3. **UI Scope Check (CRITICAL)**:
   - If RFC **explicitly describes** UI changes → flag them clearly
   - If RFC **does not mention UI** → do NOT infer UI tasks. Ask the user:
     > "(A) No UI changes — backend/config/data only. (B) Yes, I have Figma designs. (C) Yes, but no designs yet."
   - If RFC is **ambiguous** on UI → ask the same question
4. **Confirm understanding** with the user before proceeding

## Requirement Extraction

For each requirement found in the RFC, extract:
- **Requirement ID**: Sequential (REQ-001, REQ-002, ...)
- **Category**: feature | api | ui | config | data | navigation | analytics | testing
- **Description**: What the RFC says (verbatim or close paraphrase)
- **Ambiguity Level**: clear | needs-clarification | undefined
- **Dependent On**: Other REQ IDs or external systems

## API Contract Extraction

When an RFC contains API request/response changes, extract the exact contract from the **JSON examples**, not the prose.

### Step 1: Find ALL JSON examples in the RFC

Scan the entire RFC for JSON code blocks. Group them by scenario:
- Success response
- Failure/error response
- Edge case responses (e.g., manual_apply, partial data)

### Step 2: For each new JSON object, extract the field table

For every new or modified JSON object (e.g., `voucher`, `plan_policy`), build a field table:

| Field | JSON key | JSON type | Optional? | Swift type | Evidence |
|-------|----------|-----------|-----------|------------|----------|
| status | `"status"` | string | No (present in all examples) | `String` | `"applied"`, `"failed"`, `"manual_apply"` |
| code | `"code"` | string/null | Yes (null in manual_apply) | `String?` | `"FREE-123"`, `null` |
| originalPrice | `"original_price"` | number | No | `Double` | `34.50` |

### Step 3: Determine types from JSON values, NOT from prose

| JSON value | Swift type | NOT |
|------------|-----------|-----|
| `34.50` | `Double` | NOT `DynamicStringRawObject` |
| `"Free"` | `String` | NOT `DynamicStringRawObject` |
| `true` / `false` | `Bool` | |
| `null` | Field is optional (`Type?`) | |
| `{ "text": "...", "placeholders": [...] }` | `DynamicStringRawObject` | NOT `String` |
| `[{ ... }]` | `[SomeModel]` | |

### Step 4: Distinguish data objects from layout objects

RFCs with server-driven UI (SDUI) have TWO layers:
- **`data`** — domain/business data (e.g., `data.data.voucher`)
- **`layout`** — UI component configurations (e.g., `layout[].VOUCHER_STICKY_BANNER`)

These are DIFFERENT objects with DIFFERENT schemas. The `voucher` data object has fields like `status`, `code`, `original_price`. The `VOUCHER_STICKY_BANNER` layout component has fields like `state`, `title`, `action`. Do NOT merge them into one model.

### Step 5: Extract layout component contracts (SDUI)

For RFCs with server-driven UI, also extract the layout component changes:

**New components** — list each new `component` type and ALL its fields:
```
VOUCHER_STICKY_BANNER:
  - state: String ("applied" | "manual_apply")
  - title: DynamicStringRawObject
  - action.title: DynamicStringRawObject
  - action.type: String ("OPEN_VOUCHER_BOTTOM_SHEET")
```

**Modified components** — list only the NEW fields being added:
```
MOBILE_STICKY_FOOTER (existing, modified):
  - original_price: DynamicStringRawObject? (NEW, additive, optional)
```

Mark additive fields as optional — old responses without them must still work.

### Step 6: Verify backward compatibility

For every contract change, ask:
1. Will old API responses (without the new fields) still decode without crash?
2. Will the UI render correctly when new fields are absent?
3. Are all new fields on existing structs optional?

Flag any non-optional addition to an existing struct as a **BREAKING CHANGE**.

### Step 7: Output

Produce a `## API Contract` section in clarifications.md with:
- Field table for each new data object
- Field table for each new/modified layout component
- Backward compatibility notes
This becomes the authoritative reference for the breakdown and jira-writer agents.

## Gap Identification

Actively look for:
- **Missing edge cases**: What happens when data is empty, null, error?
- **Undefined user flows**: Transitions between states not described
- **API contract gaps**: Response fields mentioned without structure
- **Error handling gaps**: No mention of failure modes
- **Feature flag gaps**: No mention of rollout strategy
- **Analytics gaps**: No tracking events defined
- **Accessibility gaps**: No mention of VoiceOver, dynamic text
- **Offline gaps**: No mention of offline behavior

## RFC Quality Signals

| Signal | Action |
|--------|--------|
| RFC < 1 page | Flag as "very short" — require extensive clarification |
| No API section | Ask if backend changes are planned or ready |
| No UI section | Run UI Scope Check above |
| No rollout plan | Ask about feature flags and gradual rollout |
| Contradicts codebase | Flag contradiction, present options, ask user to decide |

## Output Format

Produce a structured summary suitable for `feature_input.yaml`:
```yaml
rfc_summary:
  title: "Feature Name"
  requirements:
    - id: REQ-001
      category: feature
      description: "..."
      ambiguity: clear
  gaps:
    - "Missing error handling for API timeout"
    - "No feature flag mentioned"
  ui_scope: in_scope | out_of_scope | needs_clarification
```
