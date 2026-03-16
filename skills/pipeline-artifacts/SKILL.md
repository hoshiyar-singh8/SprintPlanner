---
name: pipeline-artifacts
user-invocable: false
description: YAML/MD schemas for all pipeline artifacts
---

# Pipeline Artifacts

Background knowledge for agents that produce or consume pipeline artifacts.

## Artifact Directory

All artifacts for a feature live in the `output_dir` chosen during Stage 0 intake.
Default: `./.ai/features/<feature-name>/` in the user's current working directory.
The pipeline never writes artifacts inside dependency directories (Carthage, node_modules, Pods, vendor, .build).

## Artifact Inventory

| File | Format | Producer | Consumer |
|------|--------|----------|----------|
| `feature_input.yaml` | YAML | orchestrator | all agents |
| `clarifications.md` | Markdown | pipeline-discovery | pipeline-planner, pipeline-context |
| `context_pack.yaml` | YAML | pipeline-context | pipeline-planner, pipeline-breakdown, pipeline-jira-writer |
| `high_level_plan.md` | Markdown | pipeline-planner | pipeline-breakdown, user |
| `task_specs.yaml` | YAML | pipeline-breakdown, pipeline-classifier | pipeline-jira-writer, pipeline-validator |
| `jira_tickets.md` | Markdown | pipeline-jira-writer | user, render_jira_payload.py |
| `jira_payload.json` | JSON | render_jira_payload.py | user (for Jira import) |
| `validation_report.md` | Markdown | pipeline-validator | user |
| `pipeline_state.yaml` | YAML | orchestrator | orchestrator (resume) |
| `retry_memory.yaml` | YAML | orchestrator | orchestrator (prevent repeats) |

## Schema: feature_input.yaml

```yaml
feature_name: "partnership-voucher"         # kebab-case
detected_platform: ios                      # ios | android | web | backend | flutter | other
repo_source: local                          # local | github | both
repo_url: "github.com/org/repo"            # GitHub URL (if repo_source is github or both)
repo_path: "/path/to/repo"                 # local path (if repo_source is local or both)
rfc_path: "/path/to/RFC.md"               # absolute path, URL, or relative to feature dir
skills_status: ready                        # ready | generated | user_supplied
figma_urls:                                 # optional
  - url: "https://figma.com/design/..."
    screen: "Manage Subscription"
    type: before                            # before | after | new
  - url: "https://figma.com/design/..."
    screen: "Manage Subscription"
    type: after
figma_status: provided                      # provided | not_provided | pending
sp_max: 3                                  # max story points per task (1-3)
ui_scope: 1                                # UI scoping ladder level (1-4)
output_dir: "/path/to/.ai/features/feature-name"  # resolved absolute path for artifacts
epic_key: "PROJ-100"                        # optional, Jira epic parent
labels:                                     # optional
  - "partnership-voucher"
  - "ios"
```

## Schema: clarifications.md

```markdown
# Clarifications — [Feature Name]

## Questions

### Group 1 — Feature Scope & Business Rules
1. [Question text]
2. [Question text]
...

### Group 2 — API & Data
...

[Groups 3-6]

## User Answers

### Group 1
1. [Answer]
2. [Answer]
...

## Planning Decisions
- [Decision 1: description]
- [Decision 2: description]
...

## Open Questions
- [Question]: Assumed approach: [approach]. Risk: [risk level].
```

## Schema: context_pack.yaml

```yaml
architecture:
  pattern: VIPER
  di_framework: DependencyContainer
  networking: Kami
  concurrency: RxSwift  # or async-await
  ui_framework: UIKit
  design_system: Bento
  persistence: UserDefaults
  testing: XCTest
  feature_flags: Configurations SDK (S3)
  archetype: classic_viper_feature        # optional: classic_viper_feature | graphql_feed_feature | modular_sdk_package | bento_tokens_or_component | provider_or_bridge_component

relevant_modules:
  - name: Partnerships
    path: Subscription/Source/Views/Partnerships/
    similarity: high
    description: "Existing partnerships module — closest pattern match"
    files:
      - PartnershipsPresenter.swift
      - PartnershipsInteractor.swift
      - PartnershipsRouter.swift

key_files:
  - path: Subscription/Source/Api/Partnerships/PartnershipsClient.swift
    role: "API client for partnerships endpoints"
  - path: Subscription/Source/Mapper/PartnershipsModelMapper.swift
    role: "API model to domain model transformation"

entry_points:                              # optional
  builder: "..."
  di: "..."

data_flow:                                 # optional
  fetch: "..."
  mapper: "..."
  render_builder: "..."

figma_context:                              # present only if Figma URLs provided
  screens:
    - name: "Manage Subscription"
      changes_summary: "Added voucher banner with apply/applied states"
      new_components: ["VoucherBannerView"]
      modified_components: ["ManageSubscriptionViewController"]

dependencies:
  - type: backend
    description: "Partnership voucher API must be deployed"
    status: ready | pending
  - type: design
    description: "Figma designs finalized"
    status: ready
```

## Schema: high_level_plan.md

```markdown
# Implementation Plan — [Feature Name]

## Overview
[2-3 paragraph summary of the feature and approach]

## Architecture Decisions
- [Decision 1 with rationale]
- [Decision 2 with rationale]

## Implementation Phases

| Phase | Description | Tasks | SP Total |
|-------|-------------|-------|----------|
| 1 | Foundation (models, config) | TASK-001 to TASK-003 | 3 |
| 2 | API & Data (endpoints, mappers) | TASK-004 to TASK-007 | 6 |
| 3 | UI Components | TASK-008 to TASK-012 | 5 |
| 4 | Wiring & Integration | TASK-013 to TASK-015 | 4 |

**Total**: 15 tasks, 18 SP

## Scope
### In Scope
- [item]
### Out of Scope
- [item]

## Risks
- [Risk 1]: [Mitigation]
```

## Schema: task_specs.yaml

```yaml
tasks:
  - id: TASK-001
    title: "Add is_partnership_voucher_enabled config flag"
    layer: config
    sp: 1
    depends_on: []
    acceptance_criteria:
      - "Config flag defined in Configuration.swift"
      - "Default value is false"
      - "Version gating applied in ConfigurationProvider"
    files_to_create:
      - path: "..."
        description: "..."
    files_to_modify:
      - path: "..."
        description: "..."
    implementation_notes: "Follow isPartnershipsPlanEnabled pattern"
    execution_mode:                         # added by pipeline-classifier
      type: herogen
      rationale: "Single-layer config flag following existing pattern"
      confidence: high
      risks: []
```

## Schema: pipeline_state.yaml

```yaml
feature_name: "partnership-voucher"
created_at: "2026-03-14T10:00:00Z"
current_stage: 3                            # 0-7
stage_status: in_progress                   # pending | in_progress | completed | failed
stages:
  0: { status: completed, completed_at: "..." }
  1: { status: completed, completed_at: "..." }
  2: { status: completed, completed_at: "..." }
  3: { status: in_progress, started_at: "...", retries: 0 }
  4: { status: pending }
  5: { status: pending }
  6: { status: pending }
  7: { status: pending }
max_retries: 2
```

## Schema: retry_memory.yaml

```yaml
retries:
  - stage: 3
    attempt: 1
    timestamp: "2026-03-14T10:30:00Z"
    failure_reason: "high_level_plan.md missing Risks section"
    action_taken: "Added Risks section with 3 identified risks"
```
