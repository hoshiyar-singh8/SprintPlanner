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
