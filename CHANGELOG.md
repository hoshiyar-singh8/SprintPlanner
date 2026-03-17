# Changelog

## v1.2.0 (2026-03-17)

### Improved (based on analysis of 60+ real HeroGen PRs — diffs, reviews, closed vs merged)

**Ticket Quality (from real merged vs closed patterns):**
- `jira-ticket-standard` — rewritten with evidence-based templates, common review rework section (iOS style rules IOS-0002/0009, Android optional defaults, mapper completeness)
- `herogen-task-safety` — Android MVVM classification, file-count heuristic, granularity check, common rework patterns, PR success metrics table, platform-specific test conventions
- `pipeline-jira-writer` — three concrete ticket templates, platform-specific anti-patterns (iOS no UI tests, Android CODEOWNERS/TUIT/diff coverage), mapper field enumeration rule
- `pipeline-classifier` — granularity warnings before classification, Android layer support, file-count validation

**Task Decomposition (from closed batch #35661-35668 vs merged replacements #35660/35708/35778):**
- `task-decomposition-rules` — vertical-slice decomposition rule (the #1 finding), wrong-vs-right comparison table, feature flag cleanup pattern, independently-shippable task requirement
- `pipeline-breakdown` — vertical-slice enforcement, Android API/Impl module pattern, TODO stubs behind flags, mapper completeness rule, file count guidance
- `pipeline-planner` — mandatory Task Granularity Guidance section

**Validation:**
- `validate_classification.py` — warns when herogen task modifies 4+ existing files
- `validate_task_specs.py` — vague acceptance criteria detection, dependency chain depth warning (5+ = horizontal slicing), `cleanup` layer added
- `validate_plan.py` — warns when Task Granularity Guidance section is missing
- `pipeline-validator` — 7 new quality checks (mapper completeness, iOS no-UI-tests, file count, chain depth, independent shippability, cleanup completeness, no YAGNI params)

## v1.1.0 (2026-03-17)

### Added
- `create_jira_tickets.py` — push tickets directly to Jira API with `--dry-run` support
- `pipeline_summary.py` — quick summary utility for any feature directory
- Test suite (39 tests) covering validators, Jira renderer, and quality gate
- GitHub Actions CI with Python 3.9-3.12 matrix
- `.gitignore` for Python artifacts and user config
- Requirements traceability: R1/R2 IDs from RFC through tasks to tickets
- Fit-check table pattern in planner for multi-approach comparison
- Screen states section in context_pack.yaml for UI features
- `--version` flag for install.sh
- CI badge in README

### Fixed
- `quality_gate.py` — now uses `detected_platform` instead of `platform` field
- `render_jira_payload.py` — regex correctly strips colon from `TASK-001:` headers
- `validate_context.py` — added 10 more valid architecture patterns (bloc, hexagonal, layered, etc.)
- `install.sh` — cross-platform sed (works on both macOS and Linux)

### Improved
- `pipeline-skill-generator` — enhanced Android detection (Anvil/Whetstone DI, MockK, Turbine, VariationKey)
- `pipeline-breakdown` — platform-specific layer documentation (iOS/Android/Web/Backend)
- `pipeline-orchestrator` — Jira push option after quality gate
- `pipeline-discovery` — explicit numbered requirements extraction for traceability
- `pipeline-planner` — fit-check table for architecture approach comparison
- `pipeline-validator` — requirements coverage cross-check

## v1.0.0 (2026-03-16)

### Added
- Initial release with 8-stage pipeline
- 14 skills, 8 agents, 11 hooks
- Platform auto-detection (iOS, Android, Web, Backend, Flutter)
- Skill auto-generation for unfamiliar platforms
- Jira auto-config from API
- PostToolUse validation hook
- Resume support via pipeline_state.yaml
- Figma MCP integration
