---
name: repo-context-gathering
user-invocable: false
description: Detect B2C/Bento module archetypes and gather only the local architecture, DI, GraphQL, and testing context needed for the task.
---

# Repository Context Gathering

Use this skill to build a small, reliable context pack before editing B2C or Bento code.

## Parallel Discovery Strategy

**Efficiency rule**: Run all independent reads in a single parallel message. Never read files sequentially when they don't depend on each other.

### Wave 1 - Repo Type and Archetype Detection (all parallel)
```
├─ Identify repo root (`pd-mob-b2c-ios` vs `pd-mob-ui-kit-ios`)
├─ Find the nearest feature folder from the user request
├─ Glob for `*Builder*`, `*Presenter*`, `*Interactor*`, `GraphQL/`, `FeedsBuilder/`, `ViewModels/`, `Views/`
├─ Grep for `DependencyContainer`, `register*Dependencies`, `autoregister`, `Swinject`
└─ Collect 2-4 files that prove the local archetype
```

Classify the feature as one of:
- `bento_tokens_or_component`
- `classic_viper_feature`
- `graphql_feed_feature`
- `modular_sdk_package`
- `provider_or_bridge_component`

### Wave 2 - Archetype-Specific Reads (after Wave 1, all parallel)
```
├─ Bento: token file, component implementation, snapshot test if relevant
├─ Classic VIPER: builder, presenter, interactor or router, one test
├─ GraphQL feed: builder, DI container, query or repository, mapper, sections builder, one test
└─ Modular SDK: public interface, composition root, one source file, one test or mocks file
```

### Wave 3 - Similar Examples and Edge Conventions (after Wave 2, all parallel)
```
├─ Find the closest similar feature in the same archetype
├─ Read local test base class or mock generation doc
└─ Read the exact UI or navigation API used by neighboring files
```

## What to Discover

| Aspect | What to find | Where to look |
|--------|--------------|---------------|
| Repo type | B2C app repo vs Bento UI kit | repo root and top-level folders |
| Archetype | VIPER, GraphQL feed, module package, Bento component | feature folder contents |
| Entry points | builder, DI container, public interface, composition root | `*Builder.swift`, `DependencyContainer+*`, `*DIContainer.swift` |
| Data flow | query/client/repository/service/mapper chain | `GraphQL/`, `*Client.swift`, `*Repository.swift`, `*Service.swift`, `*Mapper.swift` |
| Rendering path | sections builder, data source, cell or view model factory | `FeedsBuilder/`, `DataSource`, `Views/`, `ViewModels/` |
| Navigation | router, coordinator, provider, builder | `*Router.swift`, coordinator files, builder/provider files |
| Testing | base class, mock strategy, source path overrides | nearest test files, mock docs, Sourcery config |
| Feature flags or config | config provider, GraphQL flags, static config | configuration providers, request builders, config modules |
| Similar feature | closest existing pattern in same archetype | sibling feature folders |

## Context Pack Output Format

```yaml
architecture:
  pattern: VIPER
  di_framework: DependencyContainer + Swinject
  networking: Apollo GraphQL
  ui_framework: UIKit + Bento
  concurrency: async/await + local legacy patterns
  archetype: graphql_feed_feature

relevant_modules:
  - name: NewHomeScreen
    path: FoodPanda/VendorDiscovery/NewHomeScreen/
    similarity: high
    description: "GraphQL feed screen with DI container, mappers, feed builders, and Bento views"
    files:
      - NewHomeScreenBuilder.swift
      - NewHomeScreenDIContainer.swift
      - GraphQL/Core/HomeApolloRepository.swift
      - FeedsBuilder/HomeSectionsBuilder.swift

key_files:
  - path: FoodPanda/VendorDiscovery/NewHomeScreen/NewHomeScreenBuilder.swift
    role: screen entry point and presenter/view wiring
  - path: FoodPanda/VendorDiscovery/NewHomeScreen/NewHomeScreenDIContainer.swift
    role: composition root and dependency registrations
  - path: FoodPanda/VendorDiscovery/NewHomeScreen/GraphQL/Core/HomeApolloRepository.swift
    role: GraphQL fetch layer
  - path: FoodPanda/VendorDiscovery/NewHomeScreen/GraphQL/Mappers/Apollo/HomeApolloGraphQLMapper.swift
    role: Apollo to domain mapping
  - path: FoodPanda/VendorDiscovery/NewHomeScreen/FeedsBuilder/HomeSectionsBuilder.swift
    role: domain component to section and row assembly

entry_points:
  builder: FoodPanda/VendorDiscovery/NewHomeScreen/NewHomeScreenBuilder.swift
  di: FoodPanda/VendorDiscovery/NewHomeScreen/NewHomeScreenDIContainer.swift

data_flow:
  fetch: FoodPanda/VendorDiscovery/NewHomeScreen/GraphQL/Core/HomeApolloRepository.swift
  request_builder: FoodPanda/VendorDiscovery/NewHomeScreen/GraphQL/Builders/HomeRequestApolloParamsBuilder.swift
  mapper: FoodPanda/VendorDiscovery/NewHomeScreen/GraphQL/Mappers/Apollo/HomeApolloGraphQLMapper.swift
  render_builder: FoodPanda/VendorDiscovery/NewHomeScreen/FeedsBuilder/HomeSectionsBuilder.swift

testing:
  base_class: nearest local UnitTest or app test base
  conventions:
    - inspect nearest tests for `sourceFilePath`
    - inspect local target for Sourcery or custom mocks
```

## Archetype Notes

### Bento repo
- Focus on token source, component implementation, generated accessors, and snapshot tests.
- Do not waste context on app-level DI or routing.

### Classic VIPER feature
- Capture builder, presenter, interactor, router, and one representative test.
- Verify whether the feature really uses `*Dependencies.swift` before mentioning it.

### GraphQL feed feature
- Capture builder, DI registration, request/query layer, repository/service, mapper chain, section builder/data source, and view models or views.
- NewHome is the canonical example for this pattern in the repo.

### Modular SDK package
- Capture `Sources/` entry points, public interfaces, composition root, target-specific tests, and local mock generation workflow.

## Context hygiene

- Never bulk-load a whole repo tree when one feature folder proves the pattern.
- Prefer one archetype and one similar example over five shallow reads.
- If the feature mixes patterns, call out the seam explicitly instead of flattening it into a generic template.
