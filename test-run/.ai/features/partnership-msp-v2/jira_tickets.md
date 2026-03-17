# Jira Tickets — Partnership MSP v2

## TASK-001: Add isSubscriptionV3MspEnabled config flag to Configuration protocol

**Type:** Story | **SP:** 1 | **Layer:** config | **Mode:** HeroGen

### Description

Add a new feature flag `isSubscriptionV3MspEnabled` to the `Configuration` protocol in `pd-mob-config-ios`. This flag decouples the MSP v3 endpoint migration from partnership feature activation, allowing all markets to migrate MSP to v3 independently.

### Acceptance Criteria

- [ ] `isSubscriptionV3MspEnabled` property added to `Configuration` protocol
- [ ] Default value is `false`
- [ ] S3 config key `subscription-v3-msp-enabled` mapped in `ConfigurationProvider`
- [ ] Flag follows `isPartnershipsPlanEnabled` pattern

### Implementation Guide

**Files to modify:**
- `pd-mob-config-ios/Sources/Configuration/Configuration.swift` — add property to protocol
- `pd-mob-config-ios/Sources/Configuration/ConfigurationProvider.swift` — add S3 mapping

**Reference:** Follow `isPartnershipsPlanEnabled` pattern in same files.

### Anti-Patterns (Do NOT)
- Do NOT add the flag to any file outside `pd-mob-config-ios`
- Do NOT consume the flag in this task — consumption is TASK-002

### Out of Scope
- SubscriptionClient routing changes (TASK-002)
- Unit tests for routing (TASK-008)

---

## TASK-002: Update SubscriptionClient.fetchDetails() with isSubscriptionV3MspEnabled OR logic for MSP source

**Type:** Story | **SP:** 1 | **Layer:** api | **Mode:** HeroGen

### Description

Update `SubscriptionClient.fetchDetails()` to use the new `isSubscriptionV3MspEnabled` flag alongside the existing `isPartnershipsPlanEnabled` for routing MSP requests to v3. Only the `.manageSubscriptionPage` source is affected.

### Acceptance Criteria

- [ ] `fetchDetails()` checks `isSubscriptionV3MspEnabled || isPartnershipsPlanEnabled` for `.manageSubscriptionPage` source
- [ ] `.general` source routing unchanged (only `isPartnershipsPlanEnabled`)
- [ ] `.cashbackBanner` source routing unchanged (only `isPartnershipsPlanEnabled`)
- [ ] Compiles without errors
- [ ] Existing routing tests still pass

### Implementation Guide

**Files to modify:**
- `Subscription/Source/Api/Subscription/SubscriptionClient.swift` — add OR condition

**Code change:**
```swift
case .manageSubscriptionPage:
    let useV3 = configuration.isSubscriptionV3MspEnabled
              || configuration.isPartnershipsPlanEnabled
```

### Anti-Patterns (Do NOT)
- Do NOT change `.general` or `.cashbackBanner` routing
- Do NOT add any UI or mapper changes

---

## TASK-003: Update PaymentMethodViewModelMapper to handle paymentToken nil + message present state

**Type:** Story | **SP:** 2 | **Layer:** mapper | **Mode:** Human

### Description

Update `PaymentMethodViewModelMapper` to handle the new partnership state where `payment_method` has no `payment_token` but includes a `message` with an add-payment warning. This routes to the existing `AddPaymentView` component.

### Acceptance Criteria

- [ ] New else-if branch: `paymentToken == nil AND message != nil` returns `.addPayment` state
- [ ] Maps `message.title` to addPaymentView title
- [ ] Maps `message.description` to addPaymentView description
- [ ] Maps `message.status` to addPaymentView warning style
- [ ] Maps `message.action.title` to addPaymentView CTA button title
- [ ] Maps `message.action.type` (`UPDATE_SUBSCRIPTION_PAYMENT_METHOD`) to CTA action
- [ ] Existing `paymentToken != nil` path unchanged
- [ ] Existing `paymentToken == nil + message == nil` path returns nil (unchanged)

### Implementation Guide

**Files to modify:**
- `Subscription/Source/Mapper/SubscriptionV6/PaymentMethodViewModelMapper.swift`

**Pattern:** Follow renewal-failed state mapping from `SubscriptionV6RenewalFailed.json`.

**Field mapping (ALL fields):**
| API Field | ViewModel Field |
|-----------|----------------|
| `payment_method.amount` | `addPaymentViewModel.amount` |
| `payment_method.amount_format` | `addPaymentViewModel.amountFormat` |
| `payment_method.message.title` | `addPaymentViewModel.warningTitle` |
| `payment_method.message.description` | `addPaymentViewModel.warningDescription` |
| `payment_method.message.status` | `addPaymentViewModel.warningStyle` |
| `payment_method.message.action.title` | `addPaymentViewModel.ctaTitle` |
| `payment_method.message.action.type` | `addPaymentViewModel.ctaActionType` |

### Risks
- AddPaymentView may not accept all mapped fields — verify component API
- Renewal-failed pattern may differ from add-payment pattern

---

## TASK-004: Verify UPDATE_RESUB action routing triggers updateMVT flow

**Type:** Story | **SP:** 1 | **Layer:** test | **Mode:** Human

### Description

Investigate and confirm that `UPDATE_RESUB` action type correctly routes to the updateMVT / plan selection flow. Document the full routing chain.

### Acceptance Criteria

- [ ] Confirmed: `SubscriptionActionType.updateResub` exists in `PaymentDetailView.swift`
- [ ] Confirmed: `PlanAndPaymentPresenterV2` handles `UPDATE_RESUB` and routes to plan selection
- [ ] Confirmed: No partnership guard blocks the routing
- [ ] Documented: exact code path from action type to plan selection screen

---

## TASK-005: Investigate price strikethrough mechanism for DynamicStringRawObject

**Type:** Story | **SP:** 1 | **Layer:** test | **Mode:** Human

### Description

Investigate whether the current `DynamicStringRawObject` (text + placeholders only) and `InfoDetailRowViewV2.oldPrice` can support partnership discount strikethrough display. Recommend which of the 3 approaches from RFC 5.3.9 is feasible.

### Acceptance Criteria

- [ ] Documented: `DynamicStringRawObject` struct fields
- [ ] Documented: `InfoDetailRowViewV2.oldPrice` capabilities
- [ ] Documented: Whether WTI can resolve strikethrough formatting
- [ ] Recommendation: which approach (WTI-resolved, new placeholder, new field) is feasible

---

## TASK-006: Verify UpdatePM page exists in pd-mob-subscription-ios

**Type:** Story | **SP:** 1 | **Layer:** test | **Mode:** Human

### Description

Investigate whether a dedicated "Update Payment Method" page exists in `pd-mob-subscription-ios` for Case 5 (add PM without plan change).

### Acceptance Criteria

- [ ] Confirmed or denied: dedicated UpdatePM page exists
- [ ] If exists: documented page class name, entry point, routing
- [ ] If not exists: documented what needs to be built + SP estimate
- [ ] Documented: `SubscriptionCheckoutResource.updatePaymentMethod()` handles standalone PM update

---

## TASK-007: Verify action=addPayment deeplink registration

**Type:** Story | **SP:** 1 | **Layer:** test | **Mode:** Human

### Description

Verify that `action=addPayment` (or equivalent) is registered in the deeplink handler for routing from message CTA to the payment method addition flow.

### Acceptance Criteria

- [ ] Confirmed or denied: `action=addPayment` registered in deeplink handler
- [ ] If registered: documented handler class and routing destination
- [ ] If not registered: documented registration needed + SP estimate
- [ ] Documented: `UPDATE_SUBSCRIPTION_PAYMENT_METHOD` action routes from message CTA

---

## TASK-008: Unit tests for isSubscriptionV3MspEnabled flag and OR routing logic

**Type:** Story | **SP:** 1 | **Layer:** test | **Mode:** HeroGen

### Description

Create unit tests covering all flag combinations for the new `isSubscriptionV3MspEnabled` OR routing logic in `SubscriptionClient.fetchDetails()`.

### Acceptance Criteria

- [ ] Test: MSP routes to v3 when `isSubscriptionV3MspEnabled = true`, `isPartnershipsPlanEnabled = false`
- [ ] Test: MSP routes to v3 when `isSubscriptionV3MspEnabled = false`, `isPartnershipsPlanEnabled = true`
- [ ] Test: MSP routes to v3 when both flags true
- [ ] Test: MSP routes to v6 when both flags false
- [ ] Test: `.general` source only uses `isPartnershipsPlanEnabled`
- [ ] Test: `.cashbackBanner` source only uses `isPartnershipsPlanEnabled`

### Implementation Guide

**Files to create:**
- `Subscription/Tests/Api/SubscriptionClientV3MspRoutingTests.swift`

**Pattern:** Follow existing SubscriptionClient test patterns. Mock Configuration with both flag combinations.

### Anti-Patterns (Do NOT)
- Do NOT test mapper logic (separate TASK-009)
- Do NOT test UI rendering

---

## TASK-009: Add JSON fixture and unit test for PaymentMethodViewModelMapper add-payment state

**Type:** Story | **SP:** 1 | **Layer:** test | **Mode:** HeroGen

### Description

Create a JSON fixture for the partnership no-payment-method state and unit tests for the `PaymentMethodViewModelMapper` add-payment branch.

### Acceptance Criteria

- [ ] JSON fixture `SubscriptionV6PartnershipNoPayment.json` created
- [ ] Test: mapper returns `.addPayment` state when `paymentToken nil + message present`
- [ ] Test: mapper returns `.paymentMethod` state when `paymentToken present` (regression)
- [ ] Test: mapper returns `nil` when `paymentToken nil + message nil` (regression)

### Implementation Guide

**Files to create:**
- `Subscription/Tests/Fixtures/SubscriptionV6PartnershipNoPayment.json`
- `Subscription/Tests/Mapper/PaymentMethodViewModelMapperPartnershipTests.swift`

**Pattern:** Base fixture on `SubscriptionV6RenewalFailed.json` but with no `payment_token`.

### Anti-Patterns (Do NOT)
- Do NOT write tests for UIView subclasses or ViewModel structs (iOS team convention)
