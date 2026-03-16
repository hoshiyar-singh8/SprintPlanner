---
name: herogen-task-safety
user-invocable: false
description: Agent-safe vs human-only classification rules
---

# Hero Gen Task Safety Classification

Background knowledge for agents that classify tasks as Hero Gen (bot-safe) or Human-only.

## Classification Decision Tree

```
Is the task single-layer? ──NO──→ HUMAN
  │ YES
  ▼
Is the task well-defined with clear inputs/outputs? ──NO──→ HUMAN
  │ YES
  ▼
Does it follow an existing codebase pattern? ──NO──→ HUMAN
  │ YES
  ▼
Does it require architectural judgment? ──YES──→ HUMAN
  │ NO
  ▼
Is it ≤2 SP? ──NO──→ HUMAN (or split first)
  │ YES
  ▼
→ HERO GEN CANDIDATE
```

## Hero Gen Safe Categories

These task types are safe for Hero Gen (bot execution):

| Category | Why Safe | Requirements |
|----------|----------|-------------|
| **UI Components** (View layer ONLY) | Mechanical, pattern-following | ASCII layout, Bento tokens, code blocks |
| **Config Flags** | S3 config, feature flag setup | Flag name, config key, default value |
| **API Models** | Codable structs, DTOs | Exact field names and types |
| **Domain Models** | Enums, structs, value objects | Clear field definitions |
| **Mappers** (single direction) | Pure data transformation | Input/output types, mapping rules |
| **Deep Link Params** | URL parsing additions | Parameter name, type, extraction rules |
| **Navigation Routes** | Router method additions | Source, destination, data passing |
| **Presenter Properties** | Simple computed properties | Data source, transformation logic |

## Human-Only Categories

These task types MUST be assigned to human developers:

| Category | Why Human | Characteristics |
|----------|-----------|----------------|
| **Complex Business Logic** | Judgment required | State machines, multi-step flows, conditional orchestration |
| **Cross-Layer Wiring** | Can't cleanly split | View + Presenter + Router coordination |
| **Integration/DI Setup** | Architectural decisions | Builder/container updates, module assembly |
| **Payment Flow Changes** | Critical path, high risk | Payment logic, flow bifurcation |
| **Error Handling Strategy** | Design decisions | Error mapping, retry logic, fallback design |
| **Unit Tests** (complex) | Thoughtful test case design | Edge case identification, mock strategy |
| **Architecture Decisions** | Senior judgment | New patterns, protocol design, module boundaries |
| **3 SP Tasks** | Too complex for bot | Multiple files, architectural understanding |

### Exception: Simple Tests → Hero Gen
- Model/mapper tests with obvious input/output → Hero Gen OK
- Tests following existing test file pattern exactly → Hero Gen OK

## Hero Gen Task Requirements

For a task to be Hero Gen safe, it MUST include:

1. **Exact file paths** to create/modify (no "find the right file")
2. **Code blocks** showing the expected implementation structure
3. **Reference implementation** with deviation table
4. **Anti-patterns** list (what NOT to do)
5. **Acceptance criteria** that are machine-verifiable
6. **No ambiguous instructions** ("use your judgment", "decide the best approach")

### UI Tasks Must Additionally Include
- ASCII layout diagram with exact spacing
- Bento token mapping for all colors/fonts/spacing
- `setup()` code block with UIStackView configuration
- `update(with:)` method body with numbered steps
- "Out of Scope" section listing excluded work

## Classification Output Format

Each task gets an `execution_mode` field:

```yaml
execution_mode:
  type: herogen | human
  rationale: "Single-layer UI component following existing pattern with clear specs"
  confidence: high | medium
  risks: []  # List any risks even for herogen tasks
```

### Confidence Levels
- **high**: Clear pattern match, well-specified, no ambiguity
- **medium**: Mostly clear but has minor ambiguity that could cause issues

If confidence is low, classify as **human** (not medium confidence hero gen).

## Override Rules

- User can override any classification (e.g., assign all tasks to themselves)
- If user says "all Hero Gen" → respect, but flag any 3 SP or cross-layer tasks
- If user says "all Human" → respect without question
- Always present classification for user review before finalizing
