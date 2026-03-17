---
name: mobile-architecture-rules
user-invocable: false
description: B2C iOS architecture archetypes, DI, networking, testing, and UI pattern checks grounded in live repo conventions.
---

# Mobile Architecture Rules

Use this skill when reasoning about B2C iOS architecture. Do not assume the whole repo follows one module shape.

## Start with archetype detection

Before giving guidance, classify the feature by files and folders:

| Archetype | Signals | Common examples |
|-----------|---------|-----------------|
| `classic_viper_feature` | `*Builder.swift`, `*Presenter.swift`, `*Interactor.swift`, `*Router.swift`, `*ViewController.swift` | many screen-level B2C features |
| `graphql_feed_feature` | feature folder contains `GraphQL/`, `FeedsBuilder/`, `ViewModels/`, `Views/`, and often a feature DI container | NewHome and similar feed modules |
| `modular_sdk_package` | lives under `Modules/pd-mob-*/.../Sources` with sibling `*Tests/Sources` | location, loyalty, reordering, pickup, verticals |
| `provider_or_bridge_component` | heavy use of `*Component`, `*Bridge`, `*Provider`, `*Factory`, with limited screen-level VIPER files | shared components and cross-feature bridges |

Use the nearest archetype, not repo-wide assumptions.

## Dependency Injection

- B2C commonly uses Swinject via `DependencyContainer`.
- Features may expose `DependencyContainer+Feature.swift`, or define a dedicated feature DI protocol/container such as `NewHomeScreenDIContainer`.
- Registration often happens in `register*Dependencies()` methods, not only in builders.

## Data layer conventions

- Rest/Kami style clients still exist in many areas.
- Apollo GraphQL is first-class in Search and NewHome style features. Expect `GraphQL/Core`, `GraphQL/Builders`, `GraphQL/Mappers`, `.graphql` files, repository/service layers, and request param builders.
- Async/await and RxSwift both exist. Match the surrounding feature instead of forcing one concurrency model.

## NewHome and feed-style modules

For feed-style features, the runtime flow often looks like:
1. Builder creates the screen and wires the router/view/presenter.
2. DI container registers GraphQL repositories, request builders, mappers, services, and feed builders.
3. Presenter coordinates screen state.
4. Interactor or service fetches data.
5. GraphQL mappers convert Apollo models to domain components.
6. Section/data-source builders turn domain components into rows/sections.
7. Cells/views render view models.

Do not force `*Dependencies.swift` or a strict `Views/{ModuleName}/` folder when the feature clearly follows this pattern.

## Testing conventions

- Many B2C tests live under `Volo Tests/` and override `sourceFilePath: String { #filePath }`.
- Some module packages define their own `UnitTest` base class under the module test target.
- AutoMockable via Sourcery is common, but mock generation workflow can differ between root app targets and module packages.
- Always inspect the nearest existing tests before prescribing base classes, overrides, or mock locations.

### What gets tested vs what does NOT

| Layer | Write tests? | Notes |
|-------|-------------|-------|
| Presenter | YES | Primary test target — state machine, event handling |
| Interactor | YES | Business logic, async data fetching |
| Mapper | YES | Pure transformation, clear input/output |
| Domain / model layer | YES | Value types, enums |
| ViewModel (UI-layer struct) | **NO** | Team convention: do not write ViewModel unit tests |
| UIView / UIViewController | **NO** | Team convention: do not write View or UI tests at unit level |

**Rationale (confirmed via code review):** ViewModels and Views are display-only; their correctness is verified through Presenter tests and QA. Writing ViewModel or View unit tests adds maintenance cost with no verified benefit in this team.

If HeroGen generates a `*ViewModelTests.swift` or `*ViewTests.swift` file, it is wrong — remove it.

### UIKit dynamic height pattern

When a view's intrinsic height changes at runtime (e.g. an error label appears, expanding a text field):

```swift
// CORRECT — propagates layout pass to parent so the sheet/container resizes
superview?.layoutIfNeeded()

// WRONG — only re-lays out the view itself; parent frame does not update
self.layoutIfNeeded()
```

This matters for bottom sheets and any container that sizes itself to content. Always call `superview?.layoutIfNeeded()` when the content height change must be reflected in the parent frame.

### Bottom Sheet
- some features create `BottomSheetViewController()` directly
- some pass `contentView:`
- some route via builders or providers

### Snackbar
- signatures vary by feature:
- `showSnackBar(with message: String, isActiveOrderCardVisible: Bool)`
- `showSnackBar(message: String)`
- `showSnackBar(viewModel: BentoSnackBarViewModel)`
- `showSnackBar(_ message: String, action: SnackBar.Action?)`

### Translation / Localization
- localisation also varies between `translator.translate(key:)`, `LocalisationProvider`, and GraphQL translation mappers

## API Model Conventions

### Decodable, NOT Codable

API response models (structs decoded from JSON) MUST conform to `Decodable`, not `Codable`. We never encode these back to JSON — `Codable` adds an unnecessary `Encodable` conformance. Only use `Codable` when the struct is both sent AND received (e.g., request bodies that are also in responses).

### Field Accuracy — Use RFC JSON Examples as Source of Truth

When creating API model structs:

1. **Use the JSON payload examples in the RFC as the source of truth** — NOT the prose descriptions. Find the highlighted/annotated JSON blocks and extract field names, types, and optionality directly from them.
2. **Cross-reference ALL JSON examples** — the RFC typically shows success, failure, and edge case payloads. Compare the same object across all examples:
   - Field present in all examples with a value → non-optional
   - Field is `null` in some examples → optional (`Type?`)
   - Field absent in some examples → optional with `decodeIfPresent`
3. **Each JSON object = one struct** — if the API returns `{ "voucher": {...}, "plan_policy": {...} }`, that's two separate structs. Do NOT merge fields from `data.voucher` with fields from `layout[].VOUCHER_STICKY_BANNER` — they are different JSON objects with different schemas.
4. **Match JSON types exactly**:
   - `34.50` (number) → `Double`, NOT `DynamicStringRawObject`
   - `"Free"` (string) → `String`, NOT `DynamicStringRawObject`
   - `{ "text": "...", "placeholders": [...] }` (object) → `DynamicStringRawObject`
   - `null` → the field is optional
5. **Verify every field against the JSON** — before finalizing, list each struct field and confirm it appears in the JSON payload for THAT specific object. Remove any field that doesn't appear in any JSON example.

### Naming Conventions for Model Structs

- **Suffix**: `ApiModel` for API response models (e.g., `VoucherApiModel`, `RenewalApiModel`)
- **Do NOT over-qualify names** — use `RenewalApiModel`, not `PlanPolicyRenewalApiModel`. The parent-child relationship is expressed via the property type, not the name.
- **Nested models get their own top-level struct** — define `RenewalApiModel` as a standalone struct, then reference it as a property in `PlanPolicyApiModel`. Do not nest struct definitions inside other structs.
- **Follow existing naming patterns** in the file — if existing models in the same file use `XxxApiModel`, follow that pattern exactly.

### Backward Compatibility — Graceful Degradation

All new fields added to existing Decodable structs MUST be optional. The API response without voucher data must continue to decode and render exactly as before.

**Rules:**
1. **New fields on existing structs are ALWAYS optional** (`Type?`) — never add a non-optional field to a struct that already decodes existing API responses. If `PartnershipsData` currently works without `voucher`, then `voucher: VoucherApiModel?` must be optional.
2. **Use `decodeIfPresent`** — if the struct has a custom `init(from:)`, new fields use `decodeIfPresent`. If it uses synthesized decoding (no custom init), optional properties auto-decode with `decodeIfPresent` semantics.
3. **New Decodable structs themselves can have non-optional fields** — `VoucherApiModel.status: String` is fine because the struct is only decoded when the `voucher` key is present. But the property ON the parent (`voucher: VoucherApiModel?`) must be optional.
4. **Layout components are safe by default** — they parse via `[String: Any]` dictionary casting with `as?`, so missing keys return nil naturally. But still guard properly.
5. **Test backward compat explicitly** — every task that adds new fields must include a test with a JSON payload that OMITS the new keys entirely, proving the old path doesn't crash.

### SDUI Layout Components vs Data Models

This codebase uses Server-Driven UI (SDUI) with two distinct JSON layers:

| Layer | Path in response | Decoded via | Pattern |
|-------|-----------------|-------------|---------|
| **Data** | `data.data.*` | `JSONDecoder` → `PartnershipsData` (Decodable struct) | Strict — unknown fields cause decode failure if not optional |
| **Layout** | `data.layout[]` | `AnyDecodable` → `[String: Any]` → factory method per component type | Loose — unknown components/fields silently ignored |

**Data models** (e.g., `VoucherApiModel`, `PlanPolicyApiModel`):
- Decoded via `JSONDecoder` from `JSONSerialization.data(withJSONObject:)`
- Strict schema — every field must match or be optional
- New fields on existing structs MUST be optional

**Layout component models** (e.g., `VOUCHER_STICKY_BANNER`, `VOUCHER_BOTTOM_SHEET`):
- Decoded via `[String: Any]` dictionary casting in factory methods
- Each component type has a factory method in `LayoutComponentViewModelFactory+Partnerships.swift`
- New component types need: enum case + switch case + factory method
- Fields parsed with `data["key"] as? Type` — missing keys return nil, no crash

### Naming Convention — Suffix Depends on File Location

Model struct naming depends on WHERE the struct lives in the module:

| Location | Suffix | Example |
|----------|--------|---------|
| `Source/Api/Models/` | `ApiModel` | `SubscriptionApiModel`, `LayoutApiModel`, `EnrolmentPlanApiModel` |
| `Source/Views/*/` (data structs) | `DataModel` | `LayoutPlanDataModel`, `VoucherDataModel`, `PlanPolicyDataModel` |
| `Source/Views/*/` (UI display) | `ViewModel` | `PartnershipsViewModel`, `SelectPlanViewModel` |

Before naming a new struct, check what suffix the TARGET FILE already uses. If `LayoutPlanDataModel` is in the same file, use `DataModel`. Do NOT use `ApiModel` for structs outside `Api/Models/`.

### CodingKeys

- Always provide explicit `CodingKeys` when JSON uses snake_case and Swift uses camelCase.
- Order: fields first, then `CodingKeys` enum (matching `LayoutPlanDataModel` convention).
- Keys that are identical in JSON and Swift (e.g., `code`, `status`) still appear in `CodingKeys` for clarity.

### Placement

- Data model structs for a feature go in the same file as related models (e.g., alongside `LayoutPlanDataModel` in `PartnershipsViewModel.swift`).
- Place new structs near related existing structs, not at the end of the file.
- Creating separate files for each model is acceptable for larger features but not required for 2-3 small structs.

## Error Handling Patterns — Inline vs Modal

B2C has TWO distinct error handling patterns. Do NOT confuse them:

### 1. Top-level error responses (modal pipeline)
- API returns non-200 `status_code` or an `exception` field in the response
- Client maps exception string via `*ExceptionType` enum (e.g., `PartnershipsExceptionType`)
- Error is displayed as a **modal** (alert, error screen, or error overlay)
- `messageKey` is derived: `"NEXTGEN_" + exceptionType.rawValue`

### 2. Layout-inline errors (SDUI component pipeline)
- API returns `status_code: 200` — it's a successful response
- Error text is carried **inside a layout component** field (e.g., `VOUCHER_BOTTOM_SHEET.input.error`)
- Error is a `DynamicStringRawObject` (localisation key), resolved via existing dynamic string pipeline
- Error is displayed **inline** in the component (e.g., beneath an input field)
- Does NOT go through `*ExceptionType` enum at all

### How to classify when reading an RFC
- If the RFC shows a non-200 response with an `exception` field → top-level error → add to `*ExceptionType` enum
- If the RFC shows a 200 response with error text inside a layout component field → inline error → parse in factory method
- Do NOT assume one pattern when the RFC shows the other
- Do NOT hallucinate exception types — only add exceptions that appear in RFC JSON examples

## What not to assume

- not every B2C feature is classic VIPER
- not every feature has `*Dependencies.swift`
- not every new task belongs in Presenter/Interactor/Router terms
- not every test target uses the same `UnitTest` base class
- not every UI API uses the same snackbar or bottom sheet signature

## Default response behavior

- Name the detected archetype explicitly.
- Cite 2-4 files that prove the archetype.
- Describe the flow using the local folder structure, not a generic template.
- If the feature mixes archetypes, say so and explain the seam.
