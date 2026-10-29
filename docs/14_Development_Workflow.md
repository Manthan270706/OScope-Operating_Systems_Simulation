# OScope — Development Workflow

## 1. Workflow

```text
Requirement
   ↓
Design
   ↓
ADR if needed
   ↓
Test cases
   ↓
Implementation
   ↓
Review
   ↓
Integration
   ↓
Documentation
```

## 2. Branching

Recommended:

```text
main
develop
feature/*
fix/*
docs/*
```

The exact strategy may be simplified for a small student team, but protected stable branches should not receive unreviewed experimental code.

## 3. Pull Request Expectations

A meaningful PR should include:

- purpose;
- requirement IDs;
- implementation summary;
- tests;
- screenshots/output where useful;
- known limitations.

## 4. Definition of Ready

Before coding:

- requirement is clear;
- interface is understood;
- test cases are identified;
- dependencies are known.

## 5. Definition of Done

See Project Charter and SRS. A feature is not complete merely because it compiles.

## 6. Documentation Updates

When implementation changes behavior:

- update relevant docs;
- update requirement traceability;
- create/update ADR if architecture changed;
- add regression tests.
