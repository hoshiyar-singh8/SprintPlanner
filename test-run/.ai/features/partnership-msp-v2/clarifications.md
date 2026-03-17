# Clarifications

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | PaymentMethodViewModelMapper must handle `paymentToken == nil + message != nil` state to route to `addPaymentView` | RFC 5.2.7.5, 5.3.11 #1 |
| R2 | New `isSubscriptionV3MspEnabled` config flag + OR logic in `SubscriptionClient.fetchDetails()` for MSP source | RFC 5.4.4, 5.3.11 #2 |
| R3 | Verify `UPDATE_RESUB` action routing correctly triggers updateMVT / re-subscription flow | RFC 5.3.11 #3 |
| R4 | Verify price strikethrough mechanism works with current `DynamicStringRawObject` + `InfoDetailRowViewV2.oldPrice` | RFC 5.3.9, 5.3.11 #4 |
| R5 | Verify UpdatePM page exists in `pd-mob-subscription-ios` or build new route for Case 5 | RFC 5.2.7.8, 5.3.11 #5 |
| R6 | Verify `action=addPayment` deeplink is registered in deeplink handler | RFC 5.2.7.6 |
| R7 | Unit tests for new flag + OR routing logic in SubscriptionClient | RFC 5.4.6 |

## Questions

### Group 1 — Scope & Requirements
1. The RFC identifies Reqs 1-2 as definite client code changes and Reqs 3-6 as verifications. Should the pipeline plan only the confirmed changes (R1, R2), or also include verification tasks for R3-R6?
2. Price strikethrough (R4) needs BE alignment on mechanism (WTI-resolved vs new placeholder type vs `original_text` field). Should we defer this to a follow-up ticket or include a placeholder task?
3. The RFC mentions `pd-mob-config-ios` as a third repo for the new flag. Should we scope tasks across all repos or focus on `pd-mob-subscription-ios` only?

### Group 2 — Architecture & Approach
1. For R1 (PaymentMethodViewModelMapper): The mapper change routes `paymentToken == nil + message != nil` to `addPaymentView`. Is this a new state alongside existing states, or does it replace the current nil-returns-nil behavior?
2. For R2 (v3 MSP flag): The existing `isPartnershipsPlanEnabled` already gates v3 routing. Should the new flag be a separate S3 key or an FWF experiment?

### Group 3 — Integration & Data Flow
1. The RFC mentions `payment_method.message` pattern already exists for renewal-failed state (from `SubscriptionV6RenewalFailed.json`). Should R1 reuse that exact mapping pattern or create a new one?
2. For Case 5 UpdatePM: Does the existing `PUT subscription-api/v3/subscription/{code}/payment-method` endpoint in `SubscriptionCheckoutResource` already handle the add-PM-only flow, or does it need a new code path?

### Group 4 — Testing
1. What test fixtures exist for partnership plan states? Any JSON fixture files in the test bundle we should reference?
2. Should R7 (unit tests) include tests for all 5 user cases, or just the flag + routing logic?

### Group 5 — Figma & UI
1. The Figma URL references UpdateMVT / Select Renewal Plan. Are there specific Figma frames for the add-payment warning state in the payment section?
2. Does the `AddPaymentView` component already match the Figma design, or does it need visual updates?

### Group 6 — Rollout & Dependencies
1. Is the v3 migration (R2) a prerequisite for R1 (mapper change), or can they ship independently?
2. What's the BE team's timeline for sending `plan.action.type = "UPDATE_MVT"` for partnership plans?

## User Answers

1.1: Plan both confirmed changes AND verification tasks. Verifications become 1 SP investigation tickets.
1.2: Defer strikethrough to follow-up. Include a 1 SP investigation ticket only.
1.3: Scope across all repos — the flag needs to live in `pd-mob-config-ios` and be consumed in `pd-mob-subscription-ios`.

2.1: New state alongside existing. The existing `paymentToken != nil` path is unchanged. This adds a new `else if` branch.
2.2: S3 config key, same pattern as `isPartnershipsPlanEnabled`. Mapped in `Configuration` protocol.

3.1: Reuse the renewal-failed pattern. The `payment_method.message` structure is identical.
3.2: The existing endpoint handles it. `SubscriptionCheckoutResource.updatePaymentMethod()` already sends the PUT request.

4.1: Check `pd-mob-subscription-ios/Tests/` for `SubscriptionV6*.json` fixture files. `SubscriptionV6RenewalFailed.json` is a good reference.
4.2: Test flag + routing logic only. User case testing is BE-driven (different API responses), not client-testable in isolation.

5.1: No specific Figma frames for add-payment warning. Use existing `AddPaymentView` design.
5.2: `AddPaymentView` already matches. No visual updates needed.

6.1: They can ship independently. R1 works with v6 responses too (if BE sends the data). R2 is a routing-only change.
6.2: BE is targeting same sprint. We can use feature flag to gate the client side.

## Planning Decisions

- **R1 (Mapper):** New `else if` branch in `PaymentMethodViewModelMapper` for `paymentToken == nil + message != nil`. Follow renewal-failed pattern. ~2 SP.
- **R2 (v3 flag):** New `isSubscriptionV3MspEnabled` S3 config key in `pd-mob-config-ios`, consumed in `SubscriptionClient.fetchDetails()` with OR logic. ~2 SP across 2 repos.
- **R3-R6 (Verifications):** 4 investigation tickets at 1 SP each to verify routing, strikethrough, UpdatePM page, and deeplink registration.
- **R7 (Tests):** Unit tests for flag routing logic. ~1 SP.
- **Strikethrough:** Deferred to follow-up ticket. Only investigation included.
- **Repos in scope:** `pd-mob-subscription-ios` (mapper, client, tests), `pd-mob-config-ios` (new flag), `pd-mob-b2c-ios` (bridge if needed).

## Open Questions

- Price strikethrough mechanism needs BE alignment before implementation (deferred)
- `action=addPayment` deeplink registration needs codebase verification
- UpdatePM page existence needs codebase verification
