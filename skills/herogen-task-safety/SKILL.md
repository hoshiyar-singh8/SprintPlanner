---
name: herogen-task-safety
user-invocable: false
description: Agent-safe vs human-only classification rules
---

# Hero Gen Task Safety Classification

Background knowledge for agents that classify tasks as Hero Gen (bot-safe) or Human-only.
Based on analysis of real HeroGen PRs — what gets MERGED vs CLOSED.

## Evidence From Real PRs

### What HeroGen Succeeds At (Merged PRs)
- **Single API endpoint additions** — adding a query param, new GET/POST route (iOS #35660, Android #43745)
- **Single UI component with all states** — one View + ViewModel, both states in same PR (iOS #35708, #35778)
- **Config flags** — S3 feature flag with version gating (Android #43620)
- **Single mapper** — one-direction data transformation (iOS #35820)
- **Cleanup/deletion** — removing dead code behind removed flag (iOS #35685)
- **Module creation** — new module with clear public API and no integration wiring (Android #43636)

### What HeroGen Fails At (Closed/Rejected PRs)
- **Over-split UI states** — 3 separate tickets for one component's empty/loading/error states (combine them)
- **Cross-layer tasks** — model + mapper + view in one ticket (split by layer instead)
- **Integration wiring** — connecting a new component to an existing parent VC/Fragment
- **Tasks requiring runtime context** — understanding navigation flow, lifecycle, DI graph
- **Vague acceptance criteria** — "works correctly" instead of "returns nil when input is empty"
- **Many-file modifications** — touching 5+ existing files with interrelated changes
- **Incomplete field coverage** — mapper/comparator covers subset of fields, reviewer requests "compare ALL values" (Android #43691)
- **Wrong base branch** — branching off `development` when a feature branch exists (Android #43611)
- **Design QA mismatch** — UI implementation doesn't match design QA feedback, gets closed (Android #43695, #43704)
- **Compilation errors on first push** — PRs that fail CI on first push often get closed or stale (iOS #35138, Android #43585)

### Common Rework Patterns (What Reviewers Ask HeroGen to Fix)
- **iOS style violations**: Parameterless builders should be computed properties (IOS-0002); no `== true`/`== false` (IOS-0009); no redundant `return` in single-expression properties
- **iOS test precision**: Replace `XCTAssertGreaterThan(x, 0)` with `XCTAssertEqual(x, 32.0)` — exact values, not range checks
- **iOS incomplete cleanup**: Removing a flag but leaving empty wrapper functions and their call sites
- **Android unnecessary optional defaults**: Adding `= null` on parameters that every call site always provides
- **Android unrelated diffs**: Cleanup PRs must not touch unrelated files (import reordering, empty lines)
- **Android module dependencies**: Use `api(projects.shadowComparisonApi)` not `implementation(projects.shadowComparison)` — depend on abstractions

## Classification Decision Tree

```
Is the task single-layer? ──NO──→ HUMAN
  │ YES
  ▼
Is it well-defined with clear inputs/outputs? ──NO──→ HUMAN
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
Does it modify >3 existing files? ──YES──→ HUMAN
  │ NO
  ▼
→ HERO GEN CANDIDATE
```

## Hero Gen Safe Categories

### iOS (VIPER)

| Category | Why Safe | Requirements |
|----------|----------|-------------|
| **UI Components** (View layer ONLY) | Mechanical, pattern-following | Layout spec, Bento tokens, reference file, all states in one task |
| **Config Flags** | S3 config + version gating | Flag name, config key, default value, version gate |
| **API Models** | Codable structs, DTOs | Exact field names, types, CodingKeys |
| **Domain Models** | Enums, structs, value objects | Clear field definitions |
| **Mappers** (single direction) | Pure data transformation | Input/output types, mapping rules |
| **API Endpoint Changes** | URL/param additions | Exact param name, type, URL construction rules |
| **Cleanup/Deletion** | Removing dead code | List of files/code to remove, what flag gated it |

### Android (MVVM)

| Category | Why Safe | Requirements |
|----------|----------|-------------|
| **Composable UI** (View layer ONLY) | Declarative, pattern-following | Layout spec, design tokens, reference composable, all states |
| **Config Flags** (VariationKey/S3) | Feature flag setup | Key name, default, variation mapping |
| **Data Models** | data class / sealed class | Exact field names, types, serialization |
| **Mappers** (single direction) | Pure transformation | Input/output types, mapping rules |
| **Repository additions** | New data source method | Endpoint, return type, error handling pattern |
| **UseCase creation** | Single-purpose business logic | Input, output, repository dependency |
| **Shadow/comparison modules** | A/B testing infra | Old/new source, comparison logic |

## Human-Only Categories

| Category | Why Human | Applies To |
|----------|-----------|-----------|
| **Cross-Layer Wiring** | View + Presenter + Router coordination | Both |
| **Integration/DI Setup** | Builder/container/Dagger updates, module assembly | Both |
| **Payment Flow Changes** | Critical path, high risk | Both |
| **Complex Business Logic** | State machines, multi-step flows | Both |
| **Error Handling Strategy** | Design decisions, fallback design | Both |
| **Fragment/VC Lifecycle** | Lifecycle-aware coordination | Both |
| **Navigation Graph Changes** | Route registration, deep link wiring | Both |
| **3 SP Tasks** | Too complex for bot | Both |
| **Tasks modifying 4+ existing files** | Too many integration points | Both |

### Exceptions: Simple Tests → Hero Gen
- Model/mapper tests with obvious input/output → Hero Gen OK
- Tests following existing test file pattern exactly → Hero Gen OK
- Snapshot/preview tests for UI components → Hero Gen OK (if reference pattern exists)

## Granularity Check (Prevent Over-Splitting)

Before classifying, check for these anti-patterns that should be COMBINED:

| Anti-Pattern | Fix |
|-------------|-----|
| 3 separate tickets for one component's states (empty/loading/error) | Combine into 1 UI task with all states |
| Separate tickets for ViewModel + View of same component | Combine into 1 task |
| Separate ticket for "add protocol" + "implement protocol" | Combine into 1 task |
| Model creation + its mapper as separate tasks | Keep separate (different layers) — this IS correct |

Rule: If removing one ticket makes the other meaningless, they should be one ticket.

## Hero Gen Task Requirements

For a task to be Hero Gen safe, it MUST include:

1. **Exact file paths** to create/modify (no "find the right file")
2. **Reference implementation** — "follow pattern in `ExistingFile.swift`"
3. **Deviation table** — what differs from reference
4. **Anti-patterns** list (what NOT to do)
5. **Acceptance criteria** that are machine-verifiable (not "works correctly")
6. **Scope boundary** — what's explicitly NOT included

### UI Tasks Must Additionally Include
- Layout spec (ASCII diagram or structured description)
- Design token mapping for ALL visual properties (colors, fonts, spacing, radius)
- ViewModel definition (enum/struct with all states)
- View structure (class signature, key methods)
- All states handled in one task (not split across tickets)
- "Out of Scope" section listing excluded work (tap handling, parent wiring, etc.)

### Android-Specific Requirements
- Composable function signature with all parameters
- Preview function for each state
- Theme token references (not raw hex/dp values)
- Hilt/Anvil module binding if new injectable class

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
