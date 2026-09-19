# OScope — Coding and Engineering Standards

## 1. Language

Use modern C++ appropriate to the selected compiler/toolchain.

## 2. Naming

- Types: `PascalCase`
- Functions/methods: `camelCase`
- Constants: project-consistent `UPPER_SNAKE_CASE` or documented convention
- Files: consistent `snake_case` or module convention

The repository shall use one convention consistently.

## 3. Ownership

Prefer:

- values;
- standard containers;
- RAII;
- smart pointers where ownership is dynamic.

Avoid raw owning pointers.

## 4. Error Handling

Do not silently ignore failures.

System-call return values must be checked.

Errors should carry enough context to identify:

- operation;
- resource;
- cause.

## 5. Headers

- minimize unnecessary includes;
- use include guards or `#pragma once` consistently;
- keep implementation details out of public interfaces where possible.

## 6. Concurrency

- document shared state;
- define synchronization ownership;
- avoid detached threads unless justified;
- join/stop threads deterministically.

## 7. Logging

Use structured logging rather than scattered `std::cout` debugging statements for persistent diagnostics.

## 8. Comments

Comment the reasoning and OS concept where useful, not obvious syntax.

## 9. Testing

Every algorithmic module should include unit tests before being considered complete.

## 10. Git

Use small, focused commits.

Suggested commit style:

```text
feat(scheduling): add round robin simulator
test(paging): add LRU edge cases
docs(architecture): record result schema decision
fix(ipc): clean up shared memory segment
```

## 11. Code Review Checklist

Review for:

- correctness;
- edge cases;
- ownership;
- race conditions;
- resource cleanup;
- complexity;
- readability;
- test coverage;
- requirement traceability.
