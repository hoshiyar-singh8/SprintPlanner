---
name: validation-rules
user-invocable: false
description: Per-stage structural + semantic + cross-file checks
---

# Validation Rules

Background knowledge for agents and hooks that validate pipeline artifacts.

## Validation Categories

### Structural Validation (automated, fast)
- File exists and is non-empty
- Required sections/fields present
- YAML/JSON parses without errors
- Markdown headers match expected structure
- Values are in allowed ranges (e.g., SP 1-3)

### Semantic Validation (requires understanding)
- Content makes sense in context
- No contradictions between artifacts
- All requirements traced to tasks
- Dependencies form valid DAG
- Story points align with complexity

### Cross-File Validation (final quality gate)
- Every RFC requirement has at least one task
- Every task traces back to a requirement or Figma design change
- Dependencies reference existing task IDs
- Total SP is reasonable for feature scope
- No orphaned tasks (tasks with no requirement source)

## Per-Stage Validation

### Stage 0: feature_input.yaml
**Structural:**
- Has `feature_name` (non-empty string)
- Has `platform` (one of: ios, android, both)
- Has `rfc_path` (file exists at path)
- Has `repo_path` (directory exists at path)
- Optional: `figma_urls` (list of valid URLs)
- Optional: `sp_max` (integer 1-3, default 3)

### Stage 1: clarifications.md
**Structural:**
- Has `## Questions` section
- Has `## User Answers` section
- Has `## Open Questions` section
- Has `## Planning Decisions` section
**Semantic:**
- All 6 question groups have at least one question
- Every question has an answer or is listed under Open Questions
- Planning Decisions section is non-empty

### Stage 2: context_pack.yaml
**Structural:**
- Valid YAML
- Has `architecture` section with `pattern`, `di_framework`, `networking`, `ui_framework`
- Has `relevant_modules` section (list, ≥1 entry)
- Has `key_files` section (list, ≥1 entry)
**Semantic:**
- Architecture pattern matches one of: VIPER, MVVM, MVI, Clean, MVP, MVC
- File paths in `key_files` look valid (have file extensions)
- Module similarity ratings are one of: high, medium, low
**Size check:**
- If >10K characters, compress (keep essential paths, trim descriptions)

### Stage 3: high_level_plan.md
**Structural:**
- Has `## Overview` section
- Has `## Architecture` or `## Architecture Decisions` section
- Has `## Phases` or `## Implementation Phases` section
- SP estimates exist (numbers followed by "SP" or "story point")
**Semantic:**
- Architecture approach references patterns from context_pack
- Phases are ordered logically
- Risks section exists with at least one risk identified

### Stage 4: task_specs.yaml
**Structural:**
- Valid YAML
- Each task has: `id`, `title`, `layer`, `sp`, `depends_on`, `acceptance_criteria`
- `sp` values are 1, 2, or 3
- Standard `layer` values include: `ui`, `viewmodel`, `api`, `mapper`, `presenter`, `interactor`, `router`, `navigation`, `config`, `test`, `integration`, `domain`, `model`, `builder`, `di`
- `depends_on` references existing task IDs only
**Semantic:**
- No DAG cycles (topological sort succeeds)
- Tasks are in topological order
- Single-layer principle: each task's layer is singular (not mixed)
- SP distribution is reasonable (majority should be 1-2)
**Model task checks:**
- Model/API layer tasks use `Decodable` (not `Codable`) for response-only structs
- Model struct names are not over-qualified (e.g., `RenewalApiModel` not `PlanPolicyRenewalApiModel`)
- Model tasks that create new structs do NOT also wire them into existing types (separate tasks)
- Every field listed in a model task traces to a specific JSON object in the RFC/API contract
- No "for future use" fields (e.g., `is_removable` if explicitly out of scope)

### Stage 5: task_specs.yaml (with execution_mode)
**Structural:**
- Every task has `execution_mode.type` (herogen or human)
- Every task has `execution_mode.rationale` (non-empty string)
**Semantic:**
- 3 SP tasks are not classified as herogen
- Cross-layer tasks are not classified as herogen
- Classification rationale aligns with the task's layer and complexity

### Stage 6: jira_tickets.md
**Structural:**
- Every task from task_specs has a corresponding ticket section
- Hero Gen tickets have: Layout Spec, Bento Tokens, Out of Scope, Code Blocks
- Human tickets have: Description, Acceptance Criteria, Dependencies
**Semantic:**
- Ticket content aligns with task_specs data
- No raw hex values in iOS UI tickets
- Anti-patterns section present in Hero Gen tickets

### Stage 7: validation_report.md
**Structural:**
- Has Structural Checks section
- Has Semantic Checks section
- Has Cross-File Checks section
- Has Summary (pass/fail count)
- Each check has result: PASS, FAIL, or WARN

## Validation Response Format

For hooks (PostToolUse):
```json
{
  "decision": "allow",  // or "block"
  "reason": "validation passed"  // or specific failure message
}
```

For scripts (between stages):
```
PASS: [check description]
FAIL: [check description] — [specific error]
WARN: [check description] — [advisory message]
```

Exit code: 0 = all passed, 1 = has failures (blocks pipeline)
