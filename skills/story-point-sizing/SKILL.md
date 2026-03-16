---
name: story-point-sizing
user-invocable: false
description: 1/2/3 scale, when to split, complexity criteria
---

# Story Point Sizing

Background knowledge for agents that need to estimate and validate story points.

## Scale: 1 / 2 / 3

| SP | Effort | Criteria | Examples |
|----|--------|----------|----------|
| **1** | ~half day (≤4 hrs) | Straightforward, follows existing patterns, mechanical change, single file or tightly scoped | Add a config flag, create a model struct, add a mapper method, create a single UI component |
| **2** | ~1 day (4-6 hrs) | Some complexity, minor design decisions, 2-3 files, may need to understand existing code | Wire presenter to new data, implement API client method with error handling, create view with multiple states |
| **3** | ~1.5 days (6-8 hrs) | Multiple files, requires understanding architecture, some judgment calls, testing included | Implement full VIPER layer connection, complex state machine in presenter, integration with external SDK |

## Hard Rules

1. **Maximum 3 SP per task** — no exceptions
2. **Prefer 1 SP tasks** — granular tasks are easier for both Hero Gen and human developers
3. **Auto-split any task >3 SP** — present the split for user confirmation before finalizing
4. **1 SP is the default** — only go higher if complexity genuinely warrants it

## When to Split (Auto-Split Triggers)

Split a task if ANY of these apply:
- Task touches **4+ files**
- Task spans **multiple VIPER layers** (e.g., View + Presenter)
- Task has **multiple independent acceptance criteria** that could be verified separately
- Task requires **both creation and wiring** (create component = 1 task, wire it = another)
- Task involves **multiple visual states** that can be built independently
- Task combines **data model creation + API integration** (split: model, then API)
- Estimate exceeds **6 hours of focused work**

## Complexity Signals

### 1 SP Signals
- "Add a field to an existing model"
- "Create a new enum/struct"
- "Add a config flag with default value"
- "Create a UI component following existing pattern"
- "Add a mapper method (single direction)"
- "Add a route method"

### 2 SP Signals
- "Create API client method with request/response models"
- "Build view with loading/error states"
- "Wire presenter to interactor for a new data flow"
- "Implement feature flag gating with version check"
- "Create bottom sheet builder + content view"

### 3 SP Signals
- "Implement presenter state machine for multi-step flow"
- "Create full VIPER mini-module (bottom sheet/dialog)"
- "Integrate with external SDK and handle all edge cases"
- "Implement complex mapper with conditional transformations"

## Estimation Checklist

Before assigning SP, verify:
- [ ] Task stays within single architectural layer
- [ ] File count matches SP expectation (1SP=1-2 files, 2SP=2-3, 3SP=3-4)
- [ ] Task is independently testable
- [ ] Acceptance criteria are concrete and verifiable
- [ ] No hidden dependencies that inflate scope

## SP vs Hero Gen Eligibility

| SP | Hero Gen Eligible? | Notes |
|----|-------------------|-------|
| 1 | Almost always yes | Clean, mechanical, well-scoped |
| 2 | Usually yes | If single-layer and well-specified |
| 3 | Rarely | Usually requires judgment → Human |
