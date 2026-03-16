---
name: dependency-mapping
user-invocable: false
description: DAG rules, dependency types, cycle detection
---

# Dependency Mapping

Background knowledge for agents that need to establish and validate task dependencies.

## DAG Rules

Task dependencies MUST form a Directed Acyclic Graph (DAG):
1. **No cycles** — if A depends on B, B cannot depend on A (directly or transitively)
2. **No self-dependencies** — a task cannot depend on itself
3. **All referenced tasks must exist** — no dangling dependency references
4. **Topological ordering** — tasks should be listed in a valid topological order

## Dependency Types

| Type | Meaning | Example |
|------|---------|---------|
| **blocks** | This task must complete before dependent tasks can start | Model creation blocks mapper creation |
| **depends_on** | This task cannot start until prerequisite is complete | Mapper depends on model being created |
| **parallel** | Tasks with no dependency between them can run simultaneously | UI component (scope 1) and API model creation |

## Standard Dependency Chains (VIPER iOS)

```
Config/Feature Flag
  └→ Domain Models / Enums
       └→ API Models
            └→ API Client Methods
                 └→ Mappers (API → Domain)
                      └→ Mappers (Domain → ViewModel)
                           └→ Presenter Logic
                                └→ Router Methods
                                     └→ Builder / DI Wiring
                                          └→ Integration Tests

UI Components (Scope 1) ──── (parallel, no dependency on above chain)
  └→ UI + Layout Wiring (Scope 2+)
       └→ Presenter↔View Connection
```

## Dependency Rules

1. **Model tasks have no dependencies** (or only depend on config flags)
2. **API tasks depend on API models** (request/response structs)
3. **Mapper tasks depend on both source and target models**
4. **Presenter tasks depend on mappers and interactor** (data flow must exist)
5. **Router tasks depend on presenter** (navigation triggered by presenter)
6. **Builder/DI depends on all components it assembles**
7. **UI (scope 1) tasks are independent** — can run in parallel with everything
8. **UI (scope 2+) tasks depend on** the parent view they integrate into
9. **Test tasks depend on** the implementation they test

## Cycle Detection Algorithm

For validation scripts, use topological sort:
```
1. Build adjacency list from dependency declarations
2. Compute in-degree for each node
3. BFS from nodes with in-degree 0
4. If visited count != total nodes → cycle exists
5. Report the cycle path for debugging
```

## Dependency Validation Checks

- [ ] All `depends_on` IDs reference existing tasks
- [ ] No circular dependency chains (direct or transitive)
- [ ] Tasks are listed in topological order (or clearly marked otherwise)
- [ ] No task depends on a task with a higher SP estimate without justification
- [ ] Integration/wiring tasks appear after all components they connect
- [ ] Test tasks appear after the code they test

## Dependency Visualization

Output dependencies as a text-based graph:
```
TASK-001 (Config flag)
  └→ TASK-002 (Domain model)
       ├→ TASK-003 (API model)
       │    └→ TASK-005 (API client)
       │         └→ TASK-007 (Mapper: API→Domain)
       └→ TASK-004 (ViewModel struct)
            └→ TASK-008 (Mapper: Domain→ViewModel)

TASK-006 (UI component) ── parallel ── TASK-003..005

TASK-009 (Presenter) ← depends on TASK-007, TASK-008
  └→ TASK-010 (Router)
       └→ TASK-011 (Builder/DI)
```
