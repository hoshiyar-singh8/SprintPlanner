---
name: clarifying-question-rules
user-invocable: false
description: 6 question categories, high-value question rules
---

# Clarifying Question Rules

Background knowledge for agents that need to ask structured clarifying questions before planning.

## Mandatory Question Groups

Present one group at a time, wait for answers, then move to the next. Number every question so the user can answer by number.

### Group 1 — Feature Scope & Business Rules
Always ask:
1. What is the exact trigger for this feature? (user action, deeplink, app launch, background event?)
2. Are there conditions under which this feature should NOT show? (user tier, country, feature flag, subscription state)
3. What happens if required data is missing or API fails? Degrade gracefully or block?
4. Edge cases in the RFC that aren't fully defined? List and clarify each.
5. Is this feature gated behind a feature flag? Name and config location?
6. Minimum version requirements (OS version, app version)?

### Group 2 — API & Data
Always ask:
1. Is the API ready, or are backend changes pending? Backend RFC or Slack thread?
2. Unexplained fields in the API response? Ask about each.
3. Timeout expectations for API calls?
4. Does data need local caching? Duration and invalidation rules?
5. Retry strategy on API failure? Count and backoff?
6. Local storage reads/writes? (UserDefaults, CoreData, Realm, etc.)

### Group 3 — UI & User Experience (only if UI is in scope)
First, confirm scope:
> "What scope for UI tasks?
> (1) Pure UI — ViewModel + View only. No existing files touched. (Default)
> (2) UI + layout integration — adds view to parent ViewController
> (3) UI + ViewModel wiring — connects through Presenter/Mapper
> (4) Full end-to-end — includes API, Presenter, Interactor, Router"

Then ask per screen:
1. Loading state? (skeleton, spinner, nothing)
2. Empty state? (no data, not eligible, error — are these different?)
3. Error state? Retry action?
4. Animations or transitions?
5. Accessibility requirements? (VoiceOver labels, dynamic text, min touch targets)
6. Text from localisation file or hardcoded?
7. Existing design system components to reuse?

### Group 4 — Analytics & Tracking
Always ask:
1. Analytics events required? List each tracked user action.
2. Existing analytics framework? Which one if multiple?
3. Impression events? (screen viewed, component shown)
4. A/B testing requirements?

### Group 5 — Testing
Always ask:
1. Most critical scenarios that MUST have unit test coverage?
2. UI/snapshot tests required, or unit testing sufficient?
3. Mocking patterns specific to this module?
4. Minimum test coverage expectation?

### Group 6 — Rollout & Risk
Always ask:
1. Gradual rollout (% of users) or all at once?
2. Rollback plan?
3. Dependencies on other teams (backend, design, platform, QA)?
4. Deadline or sprint target?

## High-Value Question Rules

1. **Never skip a question because you think you know the answer** — confirm everything
2. **If an answer opens new questions**, ask them before moving to the next group
3. **Mark unanswered questions as Open Questions** — never skip silently
4. **Do NOT proceed to planning** until all 6 groups are covered
5. **After all groups**, present a Planning Decisions Log summarizing every decision

## Output Format

Produce `clarifications.md` with:
```markdown
## Questions
[All questions asked, grouped by category]

## User Answers
[All answers received, keyed to question numbers]

## Planning Decisions
[Summary of every decision made during clarification]

## Open Questions
[Any questions the user couldn't answer — with the assumed approach noted]
```
