# Changelog

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
