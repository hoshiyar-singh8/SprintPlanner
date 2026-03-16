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
/run-pipeline [rfc-path] [figma-url]
```

All arguments are optional — if not provided, you'll ask for them.

## Pipeline Stages

```
0. Intake → feature_input.yaml (includes codebase + skill check + Figma ask)
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
1. Read `~/.claude/personal-project-config.md` for Jira config (if it exists)
2. Check if a `pipeline_state.yaml` exists for this feature (resume support)
3. If resuming, skip completed stages and pick up where we left off

### Stage 0: Intake

**Step 0a — Codebase Source (MANDATORY FIRST QUESTION)**

Ask the user:
> "Where should I read the codebase from?
> 1. **GitHub repo** — give me the repo URL (e.g., `github.com/org/repo`) and I'll use GitHub MCP to read it
> 2. **Local path** — give me the local directory path
> 3. **Both** — GitHub URL for browsing + local path for file reads"

Based on answer:
- If GitHub URL → validate with `gh repo view <url>` or GitHub MCP. Store as `repo_source: github`, `repo_url: <url>`, `repo_path: null`
- If local path → verify directory exists. Store as `repo_source: local`, `repo_url: null`, `repo_path: <path>`
- If both → store both. `repo_source: both`

**Step 0b — Platform & Stack Detection**

Automatically detect the platform by scanning the repo:
- Look for: `build.gradle`, `AndroidManifest.xml`, `*.kt`, `*.java` → **Android**
- Look for: `*.xcodeproj`, `*.xcworkspace`, `Podfile`, `Cartfile`, `*.swift` → **iOS**
- Look for: `package.json`, `tsconfig.json`, `*.tsx`, `*.jsx` → **Web/React**
- Look for: `go.mod`, `Cargo.toml`, `pom.xml`, `build.sbt`, `requirements.txt`, `Gemfile` → **Backend**
- Look for: `flutter.yaml`, `pubspec.yaml` → **Flutter**
- Look for: `*.csproj`, `*.sln` → **.NET**

Present to user: "I detected **[platform]** — is that correct?"

**Step 0c — Skill Check**

Check if platform-specific skills exist in `~/.claude/skills/`:

| Platform | Required Skills | Shipped with SprintPlanner? |
|----------|----------------|---------------------------|
| iOS | `mobile-architecture-rules`, `bento-token-mapping`, `repo-context-gathering` | Yes |
| Android | `android-architecture-rules`, `material-token-mapping`, `android-context-gathering` | No |
| Web | `web-architecture-rules`, `web-token-mapping`, `web-context-gathering` | No |
| Backend | `backend-architecture-rules`, `backend-context-gathering` | No |
| Flutter | `flutter-architecture-rules`, `flutter-context-gathering` | No |

If required skills **exist** → proceed normally.

If required skills **DON'T exist** → present options:
> "I don't have architecture skills for **[platform]** yet. Two options:
>
> **(A) Supply your own skills** — provide me with skill files that describe your architecture patterns, design system tokens, and context gathering strategy. I'll install them.
>
> **(B) Let me explore** — I'll analyze your codebase, learn the architecture patterns, DI framework, design system, testing conventions, and create the skills myself. This will take a few minutes but the skills will be saved for future runs.
>
> Which do you prefer?"

If user picks (A) → accept skill files, validate structure, save to `~/.claude/skills/`
If user picks (B) → launch `pipeline-skill-generator` agent with the repo. Agent will:
1. Explore the repo structure
2. Identify architecture pattern (MVVM, MVI, Clean, etc.)
3. Identify DI framework, networking, UI framework, design system, testing
4. Create platform-specific skill files
5. Save to `~/.claude/skills/`
6. Report what was created

**Step 0d — RFC/PRD**

Ask: "What's the RFC or PRD for this feature? (file path, URL, or paste the content)"

**Step 0e — Figma Designs**

Ask: "Do you have Figma designs for this feature? (Figma URL, or 'no' / 'not yet')"
- If yes → collect URLs, validate format
- If no → record `figma_urls: []`, note "no designs provided"
- If "not yet" → record `figma_status: pending`, warn that UI tasks will be approximate

**Step 0f — Jira Setup (Auto-Config)**

Ask: "Do you want to connect to Jira? Options:
1. **Yes — give me the project URL** (e.g., `https://your-org.atlassian.net/projects/PROJ`) and I'll auto-detect components, fields, and priorities
2. **Epic link** — also give me the epic URL/key if you have one (e.g., `PROJ-100` or the Jira URL)
3. **Skip** — I'll use placeholder values and you can edit `jira_config.yaml` later"

If user provides a Jira URL/key:
- Check for Jira credentials: env vars `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
- If credentials not set, ask user to provide email + API token (guide them to https://id.atlassian.net/manage-profile/security/api-tokens to create one)
- Run: `python3 ~/.claude/hooks/jira_auto_config.py --url <url> --project <key> --epic <epic_key> --email <email> --token <token> --output <feature_dir>/jira_config.yaml`
- This auto-discovers: project key, component IDs by platform, story points field, sprint field, repository field, priorities, and sets the current user as default assignee
- Show the user what was found: "Found project **PROJ** with components: iOS (18967), Android (18965). Story points field: customfield_10053. Assignee: Your Name."
- Store `jira_config_status: auto` in feature_input.yaml

If user skips:
- Store `jira_config_status: manual`
- Pipeline will use placeholder defaults from `jira_config.template.yaml`

**Step 0g — Output Directory**

Ask: "Where should I save pipeline artifacts? (default: `./.ai/features/<feature-name>/` in your current directory)"
- User can accept default (cwd-based) or provide a custom path
- **Never write artifacts inside a dependency checkout or vendored directory** — if repo_path looks like `Carthage/Checkouts/`, `node_modules/`, `vendor/`, `Pods/`, default to cwd instead
- Store the chosen path as `output_dir` in feature_input.yaml

**Step 0h — Remaining Config**

Collect:
- Feature name (derive from RFC title if not provided)
- UI scope level: 1-4 (default: 1)
- Max SP per task: 1-3 (default: 3)
- Epic key (if not already collected in Step 0f)
- Labels (optional)

**Step 0i — Write Artifacts**

1. Create directory: `<output_dir>` (resolved from step 0f)
2. Write `feature_input.yaml`
3. Run validation: `python3 ~/.claude/hooks/validate_input.py <path>`
4. Write `pipeline_state.yaml` with stage 0 completed

### Stage 1: Discovery
1. Launch `pipeline-discovery` agent with `feature_input.yaml` path
2. Agent reads RFC, produces `clarifications.md` with structured questions
3. Run validation: `python3 ~/.claude/hooks/validate_clarifications.py <path>`
4. **★ CHECKPOINT 1**: Present questions to user, collect answers
5. Update `clarifications.md` with user answers
6. Update `pipeline_state.yaml`

### Stage 2: Context
1. Launch `pipeline-context` agent with `feature_input.yaml` and `clarifications.md`
2. Agent scans repo (via local path or GitHub MCP) and Figma, produces `context_pack.yaml`
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
Artifacts: .ai/features/<feature-name>/
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
- If GitHub MCP is unavailable → fall back to asking for local path

## Agent Delegation

Use the Agent tool to launch each pipeline agent:
```
Agent(subagent_type="pipeline-skill-generator", prompt="...")  # only if skills missing
Agent(subagent_type="pipeline-discovery", prompt="...")
Agent(subagent_type="pipeline-context", prompt="...")
Agent(subagent_type="pipeline-planner", prompt="...", model="opus")
Agent(subagent_type="pipeline-breakdown", prompt="...")
Agent(subagent_type="pipeline-classifier", prompt="...")
Agent(subagent_type="pipeline-jira-writer", prompt="...")
Agent(subagent_type="pipeline-validator", prompt="...")
```

Always pass the full artifact directory path so agents can read all relevant files.
