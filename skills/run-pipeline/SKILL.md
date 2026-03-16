---
name: run-pipeline
user-invocable: true
disable-model-invocation: true
description: "Run the feature planning pipeline — converts RFC/PRD/Figma inputs into implementation plans and Jira tickets through 8 sequential stages with validation gates and human checkpoints."
---

# /run-pipeline — Feature Planning Pipeline

You are the **pipeline orchestrator**. Your job is to drive a feature through 8 sequential stages, delegating work to specialized agents, running validation between stages, and presenting 4 human checkpoints for review.

## Usage

```
/run-pipeline [rfc-path] [repo-path] [figma-url]
```

All arguments are optional — if not provided, you'll ask for them.

## Pipeline Stages

```
0. Intake → feature_input.yaml
1. Discovery → clarifications.md + ★ CHECKPOINT 1 (user answers questions)
2. Context → context_pack.yaml
3. Planning → high_level_plan.md + ★ CHECKPOINT 2 (user approves plan)
4. Breakdown → task_specs.yaml
5. Classification → task_specs.yaml (+ execution_mode) + ★ CHECKPOINT 3 (user reviews)
6. Jira Writing → jira_tickets.md + jira_payload.json
7. Quality Gate → validation_report.md + ★ CHECKPOINT 4 (final review)
```

## Orchestration Instructions

### Before Starting
1. Read `~/.claude/personal-project-config.md` for Jira config
2. Check if a `pipeline_state.yaml` exists for this feature (resume support)
3. If resuming, skip completed stages and pick up where we left off

### Stage 0: Intake
1. Collect inputs from user (or from command arguments):
   - RFC/PRD path (required)
   - Repository path (required)
   - Figma URLs (optional, can be multiple)
   - Feature name (derive from RFC title if not provided)
   - Platform: ios (default) | android | both
   - UI scope level: 1-4 (default: 1)
   - Max SP per task: 1-3 (default: 3)
   - Epic key (optional)
   - Labels (optional)
2. Create directory: `<repo>/.ai/features/<feature-name>/`
3. Write `feature_input.yaml`
4. Run validation: `python3 ~/.claude/hooks/validate_input.py <path>`
5. Write `pipeline_state.yaml` with stage 0 completed

### Stage 1: Discovery
1. Launch `pipeline-discovery` agent with `feature_input.yaml` path
2. Agent reads RFC, produces `clarifications.md` with structured questions
3. Run validation: `python3 ~/.claude/hooks/validate_clarifications.py <path>`
4. **★ CHECKPOINT 1**: Present questions to user, collect answers
5. Update `clarifications.md` with user answers
6. Update `pipeline_state.yaml`

### Stage 2: Context
1. Launch `pipeline-context` agent with `feature_input.yaml` and `clarifications.md`
2. Agent scans repo and Figma, produces `context_pack.yaml`
3. Run: `python3 ~/.claude/hooks/compress_context.py <path>` (trim if oversized)
4. Run: `python3 ~/.claude/hooks/validate_context.py <path>`
5. Update `pipeline_state.yaml`

### Stage 3: Planning
1. Launch `pipeline-planner` agent with all artifacts so far
2. Agent produces `high_level_plan.md`
3. Run validation: `python3 ~/.claude/hooks/validate_plan.py <path>`
4. **★ CHECKPOINT 2**: Present plan to user for approval
5. If user requests changes, retry (max 2 retries, then escalate)
6. Update `pipeline_state.yaml`

### Stage 4: Breakdown
1. Launch `pipeline-breakdown` agent with `high_level_plan.md` + `context_pack.yaml`
2. Agent produces `task_specs.yaml`
3. Run validation: `python3 ~/.claude/hooks/validate_task_specs.py <path>`
4. Update `pipeline_state.yaml`

### Stage 5: Classification
1. Launch `pipeline-classifier` agent with `task_specs.yaml`
2. Agent adds `execution_mode` to each task
3. Run validation: `python3 ~/.claude/hooks/validate_classification.py <path>`
4. **★ CHECKPOINT 3**: Present task list with classifications for user review
5. If user overrides any classifications, update `task_specs.yaml`
6. Update `pipeline_state.yaml`

### Stage 6: Jira Writing
1. Launch `pipeline-jira-writer` agent with `task_specs.yaml` + `context_pack.yaml`
2. Agent produces `jira_tickets.md`
3. Run: `python3 ~/.claude/hooks/render_jira_payload.py <feature-dir>`
4. Produces `jira_payload.json`
5. Update `pipeline_state.yaml`

### Stage 7: Quality Gate
1. Launch `pipeline-validator` agent to cross-check all artifacts
2. Agent produces `validation_report.md`
3. Run: `python3 ~/.claude/hooks/quality_gate.py <feature-dir>`
4. **★ CHECKPOINT 4**: Present final outputs to user
5. If all checks pass, mark pipeline as complete
6. If checks fail, identify which stage to retry

### Completion
Present summary:
```
Pipeline Complete — [Feature Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Artifacts: <repo>/.ai/features/<feature-name>/
  ✅ feature_input.yaml
  ✅ clarifications.md
  ✅ context_pack.yaml
  ✅ high_level_plan.md
  ✅ task_specs.yaml (N tasks, X total SP)
  ✅ jira_tickets.md
  ✅ jira_payload.json
  ✅ validation_report.md

Next steps:
  - Review jira_tickets.md for final content
  - Use jira_payload.json to create Jira tickets (or run herogen-sprint-planner)
  - Start implementation from task_specs.yaml
```

## Retry Logic

- Max 2 retries per stage before escalating to user
- On retry, add entry to `retry_memory.yaml` with failure reason
- Pass `retry_memory.yaml` to the agent on retry so it doesn't repeat the same mistake
- If stage fails 3 times, present the error and ask user how to proceed

## Error Handling

- If an agent fails to produce its artifact → log error, retry once, then ask user
- If validation fails → show specific failure, retry stage with guidance
- If user cancels at a checkpoint → save state, can resume later with `/run-pipeline`
- If a file path doesn't exist → ask user to correct, don't proceed with invalid paths

## Agent Delegation

Use the Agent tool to launch each pipeline agent:
```
Agent(subagent_type="pipeline-discovery", prompt="...")
Agent(subagent_type="pipeline-context", prompt="...")
Agent(subagent_type="pipeline-planner", prompt="...", model="opus")
Agent(subagent_type="pipeline-breakdown", prompt="...")
Agent(subagent_type="pipeline-classifier", prompt="...")
Agent(subagent_type="pipeline-jira-writer", prompt="...")
Agent(subagent_type="pipeline-validator", prompt="...")
```

Always pass the full artifact directory path so agents can read all relevant files.
