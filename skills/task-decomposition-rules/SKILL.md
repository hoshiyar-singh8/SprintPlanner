---
name: task-decomposition-rules
user-invocable: false
description: Split B2C iOS work into single-layer tasks across VIPER, GraphQL feed, DI, and UI registration flows.
---

# Task Decomposition Rules

Use this skill when breaking down B2C iOS work into implementation tickets.

## First detect the local flow

Choose the dominant flow before splitting tasks:
- `classic_viper_feature`
- `graphql_feed_feature`
- `modular_sdk_package`
- `bento_tokens_or_component`

If the feature is NewHome or Search style, prefer feed and GraphQL layers over generic VIPER labels.

## Single-Layer Principle

**Every task MUST stay within a single architectural layer.** Never mix layers in one task.

### Common Layer Set

Use validator-friendly `layer` values in `task_specs.yaml`: `ui`, `viewmodel`, `api`, `mapper`, `presenter`, `interactor`, `router`, `navigation`, `config`, `test`, `integration`, `domain`, `model`, `builder`, `di`.

| Layer | Creates/Modifies | Never Includes |
|-------|-----------------|----------------|
| **ui** | cell/view/controller rendering and layout | query or repository logic, presenter orchestration |
| **viewmodel / domain / model** | enums, structs, local state, value objects | view layout, network code |
| **api** | `.graphql` files, request params builders, endpoints, repositories, services, clients | UI rendering, section building |
| **mapper** | one transformation direction only | unrelated transforms, business coordination |
| **builder** | section/data source registration, row assembly, composition helpers | fetch logic, screen orchestration |
| **presenter / interactor / navigation / router** | orchestration, state transitions, navigation | view layout code |
| **di** | registrations, builders, composition roots | business logic |
| **test / integration** | unit, integration, UI test coverage | production logic beyond test seams |

### Mapper Direction Rule
Each mapper task specifies ONE transformation direction:
- GraphQL or API model -> Domain model
- Domain model -> ViewModel
- Domain model -> Section or Row model

Never bundle multiple mapper directions into one ticket.

## UI Scoping Ladder

Always clarify and honor the user's intended scope. Default to SMALLEST scope:

| Scope | Includes | Trigger Words |
|-------|----------|---------------|
| **1 - Pure UI** (default) | new view model plus view or cell only | "just UI", "pure UI", "no wiring", "UI only" |
| **2 - UI + Registration** | also registers the component in a parent layout, section builder, or data source | "add it to the screen", "register the cell", "wire up the layout" |
| **3 - UI + Data Wiring** | also threads data through mapper, presenter, interactor, or feed builder | "connect to presenter", "wire the data" |
| **4 - Full Feature** | query or API, fetch, mapping, UI, analytics, navigation, wiring | "end to end", "full feature", "complete implementation" |

### Scope 1 rules
- Prefer new files only.
- If the local architecture requires a registration point to render the component, that belongs in Scope 2.
- "Out of Scope" should explicitly list wiring, fetch, and orchestration that are excluded.
- No delegate protocols, closures, or gesture recognizers for display-only components unless the existing component family already requires them.

## Hard Splitting Rules

1. **NEVER combine UI rendering with query or repository changes** in the same ticket.
2. **NEVER combine View + Presenter** in the same ticket.
3. **NEVER combine section-builder registration with fetch-layer changes** if they can be delivered independently.
4. **NEVER bundle multiple visual states** into one ticket if they can be built independently.
5. **NEVER embed feedback UI inside a Presenter ticket** - UI component creation is separate; presenter or router tickets only trigger it.
6. **If a task cannot be cleanly split into single-layer work** -> mark as Human, not Hero Gen.
7. **NEVER build two interacting UI surfaces AND wire them together in the same ticket.** Surface construction and surface connection are always separate tickets — see Multi-Surface Flow Pattern below.

## Proven Splitting Patterns

These patterns have been confirmed effective for this team:

| Scenario | Split Into |
|----------|-----------|
| GraphQL feed component (backend-driven) | query or fragment, request or repository, GraphQL mapper, domain component registration, section builder registration, view model mapper, UI component, analytics, DI or tests |
| Local-only feed component | view model, UI component, section or data source registration, tracking or tests |
| New model files vs extensions to existing models | Separate tasks (different risk profiles) |
| ViewController layout vs Presenter state machine | Always separate (different layers) |
| Builder or DI wiring | Always its own ticket; often a final verification task |
| Bottom sheet module | UI, presenter or interactor handling, router, builder or DI |
| Feedback UI (snackbar with action) | UI component, then presenter or router trigger |
| Multi-state banner | base view plus one task per independent state when feasible |
| Config flag work | flag definition, consumption or version gating, then feature usage |
| Sourcery/mock generation work | protocol annotation, generation wiring, test adoption |
| Multi-surface entry-action flow (any feature where Surface A triggers Surface B) | One HeroGen UI ticket per visual surface with stub action closures → one Human wiring ticket that connects CTAs, presents/dismisses, threads callbacks, and registers into parent module — see Multi-Surface Flow Pattern |

## Multi-Surface Flow Pattern

Use this pattern whenever a feature introduces **2 or more distinct visual surfaces that will eventually interact** — regardless of what those surfaces are.

### Detection Signals

Apply this pattern when the RFC or spec describes ANY of the following:
- A CTA, tap, or event on Surface A causes Surface B to appear, update, or submit
- One surface acts as an **entry point** (banner, card, row, button) and another as an **action endpoint** (sheet, modal, form, dialog)
- The feature has a "show" phase (display the entry surface) and an "act" phase (user takes action on a second surface)
- A result or value produced by Surface B needs to flow back into the presenter, interactor, or network call

Common shapes this takes: `banner → bottom sheet`, `card → full-screen form`, `inline row → modal`, `sticky header → action panel`, `notification → confirmation dialog`.

### Decomposition Algorithm

**Step 1 — Identify each distinct visual surface.**
Each surface becomes its own independent HeroGen UI ticket (Scope 1):
- Build with stub closures for all interactive actions: `var onActionTapped: (() -> Void)?`
- No `present(_:animated:)` or routing calls inside the surface
- No knowledge of the other surfaces — fully self-contained
- Explicitly list in "Out of Scope": presenting other surfaces, data passing, registration into parent VC

**Step 2 — Identify shared data contracts.**
If the surfaces share a ViewModel, domain model, or callback type that does not yet exist, create a separate `model` or `domain` layer ticket. Both UI tickets depend on it. If types already exist, skip this step.

**Step 3 — Create one Human wiring ticket (always last).**
This single ticket connects everything:
- Wires the action closure on Surface A to present Surface B (via router or coordinator)
- Handles dismissal and result/callback passing from Surface B back to presenter or interactor
- Registers both surfaces into the parent module (DI, builder, router registration)
- Updates existing presenter state machine or interactor if the combined flow changes behaviour

### Wiring Ticket Is Always Human

Never assign the wiring ticket to HeroGen. It is Human because:
- It coordinates across view + router + presenter layers simultaneously
- It requires judgment about navigation stack, modal dismissal, and back-stack behaviour
- It threads data across surface boundaries (result of Surface B affects presenter state)
- It may modify existing flow logic, not just add new code

### Task Ordering for Multi-Surface Flows

```
[shared domain model / callback type]  ← only if new types needed; else skip
            ↓
Surface A UI (HeroGen) ──┐
Surface B UI (HeroGen) ──┼── run in parallel; no dependency on each other
[Surface C UI (HeroGen)]─┘
            ↓
Wiring ticket (Human) ← always last; depends on ALL surface UI tickets
```

### Scope 1 Rules Specific to Multi-Surface Features

When writing each individual surface ticket:
- All action closures must be declared but left as no-ops: `var onPrimaryTapped: (() -> Void)?`
- "Out of Scope" must explicitly name: presenting the other surface, passing data to presenter, router calls, DI registration
- The surface must be renderable and reviewable in isolation — a designer or QA can verify it without the other surface existing

---

## Task Ordering Rules

1. Tasks must be ordered by dependency — no task references a dependency that comes after it
2. Model/enum tasks before fetch-layer tasks
3. Query/request tasks before repository/service tasks
4. Repository/service tasks before mapper tasks
5. Mapper tasks before section/data source registration
6. UI tasks can often run in parallel with fetch or mapper tasks when they are scope 1
7. Presenter/router tasks after the data they consume exists
8. Builder/DI wiring after all components it assembles
9. Integration/testing tasks last unless the repo clearly does test-first coverage for that layer

## Acceptance Criteria Rules

Each task must have:
- 2-4 specific, testable acceptance criteria
- Each criterion is independently verifiable
- No ambiguous language ("should work", "looks good")
- Use concrete assertions ("builds without errors", "renders X when Y")
