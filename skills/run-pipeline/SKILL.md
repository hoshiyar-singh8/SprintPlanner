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

### MCP Health Check
Before starting Stage 0, check which MCP servers are available:

- **GitHub MCP** — needed for scanning remote repos. If user gives a GitHub URL and MCP is missing, guide them:
  `claude mcp add github -s user -e GITHUB_PERSONAL_ACCESS_TOKEN=... -- npx -y @modelcontextprotocol/server-github`
  Or suggest switching to a local clone.
- **Figma MCP** — needed for design analysis. If user provides Figma URLs and MCP is missing, guide them:
  `claude mcp add figma -s user -- npx -y figma-developer-mcp --figma-api-key=YOUR_KEY --stdio`
  Or proceed without Figma and note UI tasks will be approximate.
- **Atlassian MCP** — enhances Jira integration. If missing, pipeline falls back to REST API hooks (fully functional). To install:
  `claude mcp add atlassian -s user -e ATLASSIAN_SITE_URL=... -e ATLASSIAN_USER_EMAIL=... -e ATLASSIAN_API_TOKEN=... -- npx -y atlassian-mcp --stdio`

### Stage 0: Intake (Interactive Q&A)

**CRITICAL: Stage 0 is a conversation, not a batch job.** Ask ONE question at a time. Wait for the user's answer before asking the next question. Never pre-fill answers or skip questions. The flow should feel like a natural dialogue:

```
You: "Where's your codebase?"
User: → answers
You: "I detected iOS. Correct?"
User: → confirms
You: "What's the RFC?"
User: → gives path
...and so on
```

**Step 0a — Codebase Source (FIRST QUESTION — ask and STOP)**

Ask the user:
> "Where should I read the codebase from?
> 1. **GitHub repo** — give me the repo URL (e.g., `github.com/org/repo`)
> 2. **Local path** — give me the local directory path
> 3. **Both** — GitHub URL + local path"

**STOP and wait for the user's response.** Do NOT ask the next question in the same message.

Based on answer:
- If GitHub URL → validate with `gh repo view <url>` or GitHub MCP. Store as `repo_source: github`, `repo_url: <url>`, `repo_path: null`
- If local path → verify directory exists. Store as `repo_source: local`, `repo_url: null`, `repo_path: <path>`
- If both → store both. `repo_source: both`

**Step 0b — Platform & Stack Detection (after user answers 0a)**

Automatically detect the platform by scanning the repo:
- Look for: `build.gradle`, `AndroidManifest.xml`, `*.kt`, `*.java` → **Android**
- Look for: `*.xcodeproj`, `*.xcworkspace`, `Podfile`, `Cartfile`, `*.swift` → **iOS**
- Look for: `package.json`, `tsconfig.json`, `*.tsx`, `*.jsx` → **Web/React**
- Look for: `go.mod`, `Cargo.toml`, `pom.xml`, `build.sbt`, `requirements.txt`, `Gemfile` → **Backend**
- Look for: `flutter.yaml`, `pubspec.yaml` → **Flutter**
- Look for: `*.csproj`, `*.sln` → **.NET**

Present to user: "I detected **[platform]** ([evidence]). Is that correct?"

**STOP and wait for confirmation.**

**Step 0c — Skill Check (after user confirms platform)**

Check if platform-specific skills exist in `~/.claude/skills/`:

| Platform | Required Skills | Shipped with FeaturePlanner? |
|----------|----------------|---------------------------|
| iOS | `mobile-architecture-rules`, `bento-token-mapping`, `repo-context-gathering` | Yes |
| Android | `android-architecture-rules`, `material-token-mapping`, `android-context-gathering` | No |
| Web | `web-architecture-rules`, `web-token-mapping`, `web-context-gathering` | No |
| Backend | `backend-architecture-rules`, `backend-context-gathering` | No |
| Flutter | `flutter-architecture-rules`, `flutter-context-gathering` | No |

If required skills **exist** → tell user "Skills found for [platform]" and proceed to next question.

If required skills **DON'T exist** → present options and **STOP**:
> "I don't have architecture skills for **[platform]** yet. Two options:
>
> **(A) Supply your own skills** — give me skill files describing your architecture, design tokens, and conventions
>
> **(B) Let me explore** — I'll analyze your codebase and create the skills myself. Takes a few minutes but they're saved for future runs.
>
> Which do you prefer?"

If user picks (A) → accept skill files, validate structure, save to `~/.claude/skills/`
If user picks (B) → launch `pipeline-skill-generator` agent. Wait for it to complete before asking the next question.

**Step 0d — RFC/PRD (after skills are ready)**

Ask: "What's the RFC or PRD for this feature? (file path, URL, or paste the content)"

**STOP and wait for the user's response.**

**Step 0e — Figma Designs (after user provides RFC)**

Ask: "Do you have Figma designs for this feature? (Figma URL, 'no', or 'not yet')"

**STOP and wait for the user's response.**

- If yes → collect URLs, validate format
- If no → record `figma_urls: []`, note "no designs provided"
- If "not yet" → record `figma_status: pending`, warn that UI tasks will be approximate

**Step 0f — Jira Setup (after Figma answer)**

Ask: "Do you want to connect to Jira? Options:
1. **Yes — give me the project URL** (e.g., `https://your-org.atlassian.net/projects/PROJ`) and I'll auto-detect everything
2. **Epic link too** — project URL + epic key (e.g., `PROJ-100`)
3. **Skip** — I'll use placeholder values, you can edit later"

**STOP and wait for the user's response.**

If user provides a Jira URL/key:
- Check for Jira credentials: env vars `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
- If credentials not set, ask user to provide email + API token (guide them to https://id.atlassian.net/manage-profile/security/api-tokens to create one)
- Run: `python3 ~/.claude/hooks/jira_auto_config.py --url <url> --project <key> --epic <epic_key> --email <email> --token <token> --output <feature_dir>/jira_config.yaml`
- Show the user what was found: "Found project **PROJ** with components: iOS (18967), Android (18965). Story points field: customfield_10053. Assignee: Your Name."
- Store `jira_config_status: auto` in feature_input.yaml

If user skips:
- Store `jira_config_status: manual`
- Pipeline will use placeholder defaults from `jira_config.template.yaml`

**Step 0g — Output Directory (after Jira answer)**

Ask: "Where should I save pipeline artifacts? (default: `./.ai/features/<feature-name>/`)"

**STOP and wait.** User can accept default or provide a custom path.

- **Never write artifacts inside a dependency checkout or vendored directory** — if repo_path looks like `Carthage/Checkouts/`, `node_modules/`, `vendor/`, `Pods/`, default to cwd instead
- Store the chosen path as `output_dir` in feature_input.yaml

**Step 0h — Remaining Config (after output dir)**

Ask for any remaining config in a single message (these can be grouped since they have sensible defaults):
> "A few more settings (press enter to accept defaults):
> - **Feature name**: [derived from RFC title]
> - **UI scope level**: 1-4 (default: 1)
> - **Max SP per task**: 1-3 (default: 3)
> - **Epic key**: [from Step 0f, or enter one]
> - **Labels**: (optional, comma-separated)"

**STOP and wait.**

**Step 0i — Write Artifacts**

1. Create directory: `<output_dir>` (resolved from step 0g)
2. Write `feature_input.yaml`
3. Run validation: `python3 ~/.claude/hooks/validate_input.py <path>`
4. Write `pipeline_state.yaml` with stage 0 completed
5. Show confirmation: "Intake complete. Starting Discovery..."

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
4. **WAIT for validation to pass before proceeding to Stage 5**
5. Update `pipeline_state.yaml`

### Stage 5: Classification
**CRITICAL: Stage 5 MUST run AFTER Stage 4 completes. NEVER launch the classifier in parallel with the breakdown agent.** The classifier reads `task_specs.yaml` which must be fully written and validated first.

1. **Verify `task_specs.yaml` exists and passed validation** — if not, do NOT proceed
2. Launch `pipeline-classifier` agent with `task_specs.yaml`
3. Agent adds `execution_mode` to each task (reads the file, adds classification, writes it back)
4. Run validation: `python3 ~/.claude/hooks/validate_classification.py <path>`
5. **★ CHECKPOINT 3**: Present task list with classifications for user review
6. If user overrides any classifications, update `task_specs.yaml`
7. Update `pipeline_state.yaml`

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

### Stage 8: Push Strategy

After the quality gate passes at Checkpoint 4, present push options:

> "Pipeline complete! How would you like to push tickets to Jira?
>
> 1. **Full plan** — push all [N] tickets ([X] SP)
> 2. **Sprint capacity** — fit tickets into your sprint capacity (you tell me the SP budget)
> 3. **HeroGen only** — push only bot-safe tickets + their dependencies
> 4. **Human only** — push only human-required tickets + their dependencies
> 5. **Cherry-pick** — you choose specific task IDs
> 6. **Skip** — save everything for later"

For any option (1-5):
1. Run `plan_push_strategy.py` with the chosen strategy
2. Show the push plan to the user
3. Always dry-run first: `create_jira_tickets.py ... --dry-run`
4. Confirm with user, then create tickets
5. Optionally assign to a sprint (show available sprints from jira_config.yaml)

Requires `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` env vars.

### Completion
Present summary:
```
Pipeline Complete — [Feature Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Platform: [detected_platform]
Skills: [ready | generated | user_supplied]
Artifacts: .ai/features/<feature-name>/
  ✅ feature_input.yaml
  ✅ clarifications.md
  ✅ context_pack.yaml
  ✅ high_level_plan.md
  ✅ task_specs.yaml (N tasks, X total SP)
  ✅ jira_tickets.md + jira_payload.json
  ✅ validation_report.md (P pass, W warn, F fail)
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
- If GitHub MCP is unavailable → try `gh` CLI → fall back to asking for local path
- If Figma MCP is unavailable → ask for manual design specs → proceed without Figma
- If pipeline appears stuck → explain what stage is blocked, why, and offer concrete alternatives

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

## YAML Schema Contract

**All agents MUST use these exact field names.** Validators will reject non-conforming fields.

### task_specs.yaml — task entry fields
```yaml
tasks:
  - id: "TASK-001"              # NOT task_id
    title: "Short title"
    description: "What to do"
    layer: model                 # one of: model, mapper, presenter, interactor, router, view, config, test, etc.
    sp: 1                        # 1, 2, or 3
    phase: 1
    depends_on: []               # list of task IDs (e.g., ["TASK-001", "TASK-002"])
    requirement_ids: ["R1"]      # list of R-IDs from clarifications.md
    files_to_modify: []
    files_to_create: []
    acceptance_criteria: []
    reference_file: "path"
    execution_mode:
      type: herogen              # NOT mode. Must be "herogen" or "human"
      rationale: "Brief reason"
```

**Common mistakes to avoid:**
- `task_id` → use `id`
- `execution_mode.mode` → use `execution_mode.type`
- Running classifier before breakdown finishes → NEVER do this
