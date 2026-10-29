# OScope — Architecture Decision Records

This file indexes the architectural decisions. Individual ADRs may later be split into separate files if the project grows.

---

## ADR-001 — Use C++ for the Core

**Status:** Accepted

**Decision:** Implement the OScope core and simulation engine in modern C++.

**Rationale:**
- suitable for OS-level programming;
- direct access to POSIX APIs;
- strong type system;
- RAII supports resource ownership;
- appropriate for performance-sensitive simulations.

**Consequences:**
- team must manage C++ memory/resource semantics carefully;
- Linux/POSIX remains the primary target.

---

## ADR-002 — Linux as Primary Runtime

**Status:** Accepted

**Decision:** Target Linux as the primary execution environment.

**Rationale:** The syllabus includes Linux kernel concepts and POSIX/Linux practical work.

**Consequences:** Some experiments are not portable to Windows without modification.

---

## ADR-003 — Separate Simulation from Linux Experiments

**Status:** Accepted

**Decision:** Simulation algorithms and real Linux mechanisms shall be separate architectural areas.

**Rationale:** Prevents simulated behavior from being confused with kernel behavior.

**Consequences:** Some concepts will have two representations: educational model and real experiment.

---

## ADR-004 — CLI First

**Status:** Accepted

**Decision:** Build the first usable interface as a command-line/educational shell.

**Rationale:** Lower complexity, fast feedback, strong alignment with OS practical work.

**Consequences:** Rich GUI/web interfaces are not initial priorities.

---

## ADR-005 — Python for Visualization and Analysis

**Status:** Accepted

**Decision:** Use Python as a consumer of structured experiment results.

**Rationale:** Strong ecosystem for plotting and analysis.

**Consequences:** Visualization becomes a separate layer rather than part of the C++ core.

---

## ADR-006 — CMake Build System

**Status:** Accepted

**Decision:** Use CMake for project configuration and builds.

**Rationale:** Standard C++ build tooling and good test/IDE integration.

---

## ADR-007 — Structured Experiment Results

**Status:** Accepted

**Decision:** Store experiment outputs in a documented machine-readable format, initially JSON.

**Rationale:** Enables reproducibility, visualization, comparison, and future AI analysis.

---

## ADR-008 — AI Is Optional and Downstream

**Status:** Accepted

**Decision:** AI consumes structured experiment results and does not implement or control core OS algorithms.

**Rationale:** Preserves educational correctness and keeps the project useful without external AI services.

---

## ADR-009 — Explicit Resource Ownership

**Status:** Accepted

**Decision:** Use RAII where possible and explicit cleanup wrappers for POSIX resources.

**Rationale:** Low-level experiments involve file descriptors, processes, threads, shared memory, and synchronization objects.

---

## ADR-010 — Requirement Traceability

**Status:** Accepted

**Decision:** Maintain stable requirement IDs and map requirements to implementation and tests.

**Rationale:** Prevents syllabus and product requirements from being lost during implementation.

---

## ADR-011 — Metrics Derived from Traces

**Status:** Accepted

**Decision:** Where possible, calculate algorithm metrics from a common execution trace.

**Rationale:** Keeps metric definitions consistent across algorithms.

---

## ADR-012 — Educational Models Must Be Labeled

**Status:** Accepted

**Decision:** Educational simulations of kernel mechanisms, including Buddy and Slab, must explicitly state that they are simplified models.

**Rationale:** Avoids overstating implementation fidelity.
