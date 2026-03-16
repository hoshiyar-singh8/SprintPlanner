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
