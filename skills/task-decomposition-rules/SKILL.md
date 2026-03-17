---
name: task-decomposition-rules
user-invocable: false
description: Split work into single-layer tasks across VIPER/MVVM, API, DI, and UI flows.
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
4. **ALWAYS keep all states of one UI component in a single ticket** — splitting states across tickets causes HeroGen failures (each ticket is too small to be meaningful alone).
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
| Multi-state banner | ALL states in ONE task (ViewModel enum + View with update method handling all states) |
| Config flag work | flag definition + version gating in ONE task, then feature usage as separate task |
| Feature flag cleanup | ONE task: remove enum case + FeatureFlag extension(s) + protocol property + implementation + mock + all call sites that become dead |
| Sourcery/mock generation work | protocol annotation, generation wiring, test adoption |
| Multi-surface entry-action flow (any feature where Surface A triggers Surface B) | One HeroGen UI ticket per visual surface with stub action closures → one Human wiring ticket that connects CTAs, presents/dismisses, threads callbacks, and registers into parent module — see Multi-Surface Flow Pattern |
| SDUI feature with multiple layout components from same API | ONE model ticket (all structs + wiring + tests), ONE factory ticket (all component factories), ONE mapper ticket, ONE presenter+interactor ticket (Human), ONE router ticket — see Layer Flow Grouping |
| Same-API Decodable structs + parent wiring | ONE ticket: define new structs + add optional properties to parent + CodingKeys + backward compat tests |
| Interactor + Presenter for same user action | ONE Human ticket: protocol method + interactor implementation + presenter state machine + loading states |

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

## Decomposition Axis: Vertical Slices, Not Horizontal

**This is the #1 lesson from real HeroGen PR data.** A batch of 8 horizontal-slice PRs (iOS #35661-35668) was entirely closed and replaced by 3 vertical-slice PRs (#35660, #35708, #35778) that all merged.

| Wrong: Horizontal Slices | Right: Vertical Slices |
|--------------------------|----------------------|
| PR 1: Deeplink extraction | PR 1: API param threading (all layers for one param) |
| PR 2: API models | PR 2: Pure new UI component A (View + ViewModel, 0 existing files) |
| PR 3: Mapper | PR 3: Pure new UI component B (View + ViewModel, 0 existing files) |
| PR 4: ViewModel | PR 4: Wiring (human, last) |
| PR 5-7: UI states (split) | |
| PR 8: Integration | |
| **Result: 8 interdependent PRs, all closed** | **Result: 3 independent PRs, all merged** |

### Rules
1. **Each task must be independently shippable** — it compiles and passes tests without other tasks in the batch
2. **Use default parameter values** (`= nil`, `= null`) so existing call sites need no change
3. **New UI components = new files only** — zero modifications to existing files (Scope 1)
4. **Spread creation over time** — don't create 8 PRs in 14 minutes; merge one before creating the next
5. **Minimize inter-task dependencies** — if task B requires a type from task A, consider: can A define the type AND use it?

## Layer Flow Grouping — Don't Over-Split

**This is the #2 lesson from real ticket restructuring.** A batch of 14 fine-grained single-layer tickets was restructured into 6 layer-flow-grouped tickets that match how developers actually work.

The single-layer principle prevents mixing UI + presenter in one ticket. But it does NOT mean every struct, every factory method, and every enum case gets its own ticket. **Group by architectural layer flow**, not by individual component.

### The Principle

> If two pieces of work are in the same architectural layer, serve the same API response, and would never be reviewed or shipped separately — they belong in ONE ticket.

### What to Combine

| Combine these... | Into one ticket | Why |
|-------------------|----------------|-----|
| All Decodable structs from same API response | Model ticket | Struct definitions + parent wiring + enum cases + decoding tests are one unit. A struct with no parent property is useless. |
| All layout factory methods for same API | Factory ticket | Enum registration + all factory methods for VOUCHER_STICKY_BANNER, VOUCHER_BOTTOM_SHEET, modified MOBILE_STICKY_FOOTER = one ticket. Splitting per component creates interdependent stubs. |
| Interactor method + Presenter wiring for same user flow | Presenter+Interactor ticket (Human) | Protocol + interactor + presenter state machine + loading states for one user action are inseparable. |
| All payment changes for same checkout flow | Payment ticket (Human) | Payment factory + confirm presenter + request params + renewal banner for one payment flow. |
| Mapper extraction + ViewModel fields for same data flow | Mapper ticket | Moving logic from presenter to mapper + adding ViewModel fields it populates = one unit. |

### What NOT to Combine (still separate)

| Keep separate | Why |
|--------------|-----|
| Model layer vs Factory layer | Different layers, different risk profiles, different reviewers |
| Factory layer vs Presenter layer | Factory is data parsing, presenter is orchestration |
| Router/navigation vs Presenter | Navigation is pure routing, presenter is state machine |
| UI components vs Wiring | Per Multi-Surface Flow Pattern |

### Anti-Pattern: 14 Tickets → 6

| Wrong: Per-Component Tickets (14) | Right: Layer-Flow Tickets (6) |
|-----------------------------------|-------------------------------|
| T1: VoucherDataModel struct | T1: All data models + parent wiring + enum cases + tests (model) |
| T2: PlanPolicyDataModel struct | T2: Mapper extraction + ViewModel fields (mapper) |
| T3: RenewalDataModel struct | T3: All factory methods for all layout components (factory) |
| T4: Wire voucher to PartnershipsData | T4: Presenter + Interactor + Dependencies (Human) |
| T5: Wire planPolicy to PartnershipsData | T5: Router navigation (router) |
| T6: VOUCHER_STICKY_BANNER factory | T6: Payment flow changes (Human) |
| T7: VOUCHER_BOTTOM_SHEET factory | |
| T8: MOBILE_STICKY_FOOTER factory | |
| T9: Exception types (hallucinated!) | |
| T10: Mapper changes | |
| T11: Presenter changes | |
| T12: Interactor changes | |
| T13: Router changes | |
| T14: Payment changes | |
| **Result: 8 dismissed, massive rework** | **Result: 6 clean tickets, correct grouping** |

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

## Ticket Description Quality Rules

**This is the #3 lesson from real ticket creation.** Tickets that just list "files to modify" and "acceptance criteria" get misunderstood. Tickets that show the actual code flow, existing method signatures, and before/after diffs get implemented correctly first time.

### Every ticket MUST include

1. **Current code flow** — show the actual method signatures and call chain from the codebase, with file paths and line numbers. Don't describe abstractly what happens; paste the real code.
2. **Target code flow** — show the exact change: what the code looks like after. Include before/after snippets when modifying existing methods.
3. **Codebase references** — every claim about "X already exists" must cite the file path, line number, and method signature. Don't say "the message view already handles this" without showing where.
4. **RFC JSON examples** — paste the relevant JSON from the RFC for the specific flow this ticket covers. Don't make the implementer go find it.
5. **Out of Scope** section — explicitly name what this ticket does NOT do, especially when splitting related work across tickets.

### Routing tickets MUST include

1. **User action trigger** — what does the user tap? Show the delegate/action method in the ViewController.
2. **Presenter data gathering** — what does the presenter collect before routing? Show the current method and the target method with new params.
3. **Router implementation** — show the router method and what it delegates to (UIFactory, Builder, etc.).
4. **Data model at destination** — what struct/protocol receives the data? Show its fields.
5. **Default parameter values** — show how existing call sites remain unaffected.

### Rendering/mapping tickets MUST include

1. **Full rendering chain** — trace data from presenter → factory → viewModel → view. Show each step with file path and line number.
2. **Existing infrastructure** — if a view/component already exists that can render the data, show it. Don't propose creating new views when existing ones work.
3. **Mapping logic** — show how source data (e.g., `DynamicStringRawObject`) maps to the target viewModel (e.g., `SubscriptionMessageViewModel`). Include the style/type mapping.
4. **Verify-first approach** — if the chain might already work end-to-end, say "verify this works" rather than "implement this". Existing infrastructure often just needs data to flow through it.

### Anti-patterns in ticket descriptions

- **Abstract descriptions** — "update the presenter to handle voucher data" tells the implementer nothing. Show the actual method change.
- **Missing codebase references** — "the payment input factory needs updating" without showing its current signature and file path.
- **Inventing new components** — proposing a new `RenewalBannerView` when `MessageView` already exists and renders the same thing.
- **Splitting routing from CTA handling** — "route to payment page" is meaningless without "user taps Proceed CTA → presenter gathers X, Y, Z → router calls factory".
- **Leaving the RFC lookup to the implementer** — paste the JSON. Don't say "see RFC section 4.2".

## Acceptance Criteria Rules

Each task must have:
- 2-4 specific, testable acceptance criteria
- Each criterion is independently verifiable
- No ambiguous language ("should work", "looks good")
- Use concrete assertions ("builds without errors", "renders X when Y")
