# Implementation Plan — Partnership MSP v2

## Overview

This feature addresses the post-enrolment lifecycle for partnership plan users (e.g. Klarna x foodora PRO) on the Manage Subscription Page (MSP) and Manage Plan & Payment (MPP) page. Five user cases are covered: non-renewing plans, cancel/re-subscribe, no payment method states, upcoming plan removal, and dedicated UpdatePM flow.

The RFC confirms that most changes are purely backend-driven — the existing client infrastructure already handles the rendering. Only two confirmed client code changes are needed: (1) updating `PaymentMethodViewModelMapper` to handle the `paymentToken == nil + message != nil` state (R1), and (2) adding a new `isSubscriptionV3MspEnabled` config flag with OR logic in `SubscriptionClient.fetchDetails()` (R2). Four additional verification tasks confirm existing routing works correctly (R3-R6), and one test task covers the new flag logic (R7).

The implementation follows existing VIPER patterns in `pd-mob-subscription-ios`, specifically the `PaymentMethodViewModelMapper` pattern for R1 and the `isPartnershipsPlanEnabled` flag pattern for R2. Reference files: `PaymentMethodViewModelMapper.swift` (mapper gap), `SubscriptionClient.swift` (routing logic), `Configuration.swift` (flag definition).

## Architecture Decisions

- **Decision 1**: Extend `PaymentMethodViewModelMapper` with new `else if` branch — Rationale: follows existing mapper pattern, the `AddPaymentView` component already exists (confirmed in `Subscription/Source/Shared/Views/AddPaymentView/AddPaymentView.swift`), and renewal-failed state in `SubscriptionV6RenewalFailed.json` uses the same `payment_method.message` structure
- **Decision 2**: New S3 config key `isSubscriptionV3MspEnabled` — Rationale: follows `isPartnershipsPlanEnabled` pattern in `Configuration` protocol (`pd-mob-config-ios`), decouples MSP v3 migration from partnership feature activation per RFC section 5.4.4
- **Decision 3**: Defer price strikethrough — Rationale: `DynamicStringRawObject` (confirmed in `Subscription/Source/Component/DynamicFormatter/Models/DynamicStringRawObject.swift`) has only `text` + `placeholders` fields, no `original_text` or `style`. Needs BE alignment before implementation (RFC 5.3.9)
- **Decision 4**: Verification tasks as 1 SP investigation tickets — Rationale: R3-R6 require codebase investigation to confirm routing, deeplinks, and UpdatePM page availability. Low effort but must be tracked.

## Scope

### In Scope
- R1: PaymentMethodViewModelMapper change for add-payment warning state (Cases 3/4/5)
- R2: New `isSubscriptionV3MspEnabled` flag across `pd-mob-config-ios` and `pd-mob-subscription-ios`
- R3: Verify `UPDATE_RESUB` action routing
- R4: Investigate price strikethrough mechanism
- R5: Verify UpdatePM page exists
- R6: Verify `action=addPayment` deeplink registration
- R7: Unit tests for flag + OR routing logic

### Out of Scope
- Partnership enrolment (Part 1, already implemented)
- Price strikethrough implementation (deferred until BE alignment)
- New UI components (existing `AddPaymentView` suffices)
- Reqs 1-2 from RFC are purely BE-driven (no client code)

## Implementation Phases

| Phase | Description | Estimated Tasks | SP Estimate |
|-------|-------------|-----------------|-------------|
| 1 | Foundation: config flag + S3 mapping | ~2 tasks | ~2 SP |
| 2 | Core: mapper change + routing update | ~2 tasks | ~3 SP |
| 3 | Verification: routing, deeplink, UpdatePM, strikethrough | ~4 tasks | ~4 SP |
| 4 | Testing: unit tests for flag routing | ~1 task | ~1 SP |

**Total Estimate**: ~9 tasks, ~10 SP

### Phase Details

#### Phase 1: Foundation
- Add `isSubscriptionV3MspEnabled` to `Configuration` protocol in `pd-mob-config-ios` (following `isPartnershipsPlanEnabled` pattern in same file)
- Add S3 config mapping for the new flag
- Update `SubscriptionClient.fetchDetails()` with OR logic for `.manageSubscriptionPage` source (file: `Subscription/Source/Api/Subscription/SubscriptionClient.swift`)
- **Why ~2 SP**: 1 SP for new flag definition + S3 mapping (simple key addition), 1 SP for OR logic in SubscriptionClient (single condition change + compilation verification)

#### Phase 2: Core
- Update `PaymentMethodViewModelMapper` (file: `Subscription/Source/Mapper/SubscriptionV6/PaymentMethodViewModelMapper.swift`) with new `else if` branch for `paymentToken == nil + message != nil` → route to `addPaymentView`
- Ensure `addPaymentView` state renders correctly with warning message and action CTA
- **Why ~3 SP**: 2 SP for mapper change (new branch + mapping all PaymentMethod fields: amount, amount_format, message.title, message.description, message.status, message.action.title, message.action.type), 1 SP for integration verification

#### Phase 3: Verification
- Verify `UPDATE_RESUB` action type routes to updateMVT flow in `PlanAndPaymentPresenterV2` (file: `Subscription/Source/Views/PlanAndPayment/PlanAndPaymentPresenterV2.swift`)
- Investigate `DynamicStringRawObject` + `InfoDetailRowViewV2.oldPrice` for strikethrough support
- Verify dedicated UpdatePM page exists in `pd-mob-subscription-ios`
- Verify `action=addPayment` deeplink registration in deeplink handler
- **Why ~4 SP**: Each verification is 1 SP (code reading + confirmation + documentation)

#### Phase 4: Testing
- Unit tests for `isSubscriptionV3MspEnabled` flag + OR routing in `SubscriptionClient` (reference: existing routing tests in `SubscriptionClientTests`)
- **Why ~1 SP**: Single test file, follows existing test pattern

## Technical Design Notes
- `PaymentMethodViewModelMapper` uses switch/if-else on payment method fields — new branch adds after existing `paymentToken != nil` check (reference: `Subscription/Source/Mapper/SubscriptionV6/PaymentMethodViewModelMapper.swift`)
- `SubscriptionClient.fetchDetails()` uses `isPartnershipsPlanEnabled` for v3 routing — new flag adds `|| isSubscriptionV3MspEnabled` for `.manageSubscriptionPage` source only (reference: `Subscription/Source/Api/Subscription/SubscriptionClient.swift`)
- `AddPaymentView` component already renders warning with CTA button (reference: `Subscription/Source/Shared/Views/AddPaymentView/AddPaymentView.swift`)
- Renewal-failed state uses same `payment_method.message` structure — mapper pattern can be directly reused

## Design Context (from Figma)
- **Figma URL**: UpdateMVT / Select Renewal Plan screens
- **No specific frames for add-payment warning state** — using existing `AddPaymentView` design
- No new UI components needed — existing Bento components suffice
- Note: "No Figma designs analyzed — UI tasks may need refinement once designs are available" (Figma MCP not called in this test run)

## Task Granularity Guidance
- **Config flag + S3 mapping = ONE task** — flag definition and S3 key always ship together
- **SubscriptionClient OR logic = ONE task** — single condition change, must compile with the flag
- **Mapper change = ONE task** — all payment method states (paymentToken present, paymentToken nil + message, paymentToken nil + no message) in a single mapper function
- **Each verification = ONE task** — separate tickets because they're independent investigations
- **Unit tests for routing = ONE task** — test file covers flag + OR logic together
- **DO NOT split**: mapper into per-case tasks (the mapper handles all cases in one function)
- **DO NOT split**: flag across repos into separate tasks (flag in config-ios and consumption in subscription-ios can ship together if they're the same PR, but are separate repos so must be separate tasks)

## Risks & Mitigations
- **Risk 1**: Price strikethrough needs BE alignment — Mitigation: Deferred to follow-up, only investigation ticket included
- **Risk 2**: UpdatePM page may not exist — Mitigation: Verification ticket will confirm; if missing, follow-up ticket for new page
- **Risk 3**: `action=addPayment` deeplink may not be registered — Mitigation: Verification ticket; if missing, simple deeplink registration addition
- **Risk 4**: BE timeline for `plan.action.type = "UPDATE_MVT"` change — Mitigation: Client-side gated by feature flag, can ship independently

## Open Questions
- Price strikethrough mechanism (deferred — needs BE alignment)
- `action=addPayment` deeplink registration status
- UpdatePM dedicated page availability
