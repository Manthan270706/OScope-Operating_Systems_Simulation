# OScope — Software Architecture

## 1. Architecture Style

OScope uses a modular layered architecture with a clear separation between educational simulations and real Linux experiments.

## 2. Layers

```text
Presentation
    │
    ▼
Application
    │
    ▼
Domain / Simulation
    │
    ├──────────────► Linux Experiment Adapters
    │
    ▼
Experiment Infrastructure
    │
    ▼
Persistence / Result Files
    │
    ▼
Analysis / Visualization
```

## 3. Module Boundaries

### Core
Shared types, validation, result/status types, utilities.

### Simulation
Pure educational models.

### Linux Experiments
Actual POSIX/Linux mechanisms.

### Experiment
Workload, execution, events, metrics, serialization.

### Shell
Command parsing and dispatch.

### Monitoring
Host observation.

### Visualization
External analysis layer.

### AI
Optional consumer of structured results.

## 4. Dependency Rule

Preferred dependency direction:

```text
Shell → Application → Domain
                       ↑
Linux Experiments → Experiment
                       ↑
Visualization ← Result Schema
```

Pure simulation algorithms should not depend on the shell.

## 5. Separation of Concerns

A scheduler should not:

- parse CLI input;
- draw a chart;
- write arbitrary files;
- call AI services.

A Linux experiment should not:

- implement unrelated scheduling algorithms;
- own visualization;
- contain product-level command parsing.

## 6. Data Flow

```text
User Command
    ↓
Command Parser
    ↓
Application Service
    ↓
Module
    ↓
Execution Trace
    ↓
Metrics
    ↓
Experiment Result
    ↓
JSON
    ↓
Python Visualization / Analysis
```

## 7. Simulation vs Real-System Boundary

The boundary is mandatory:

```text
Simulation Domain
   ├── scheduler
   ├── paging
   ├── memory allocation
   ├── deadlock
   └── disk scheduling

Linux Domain
   ├── fork/exec/wait
   ├── pthread
   ├── IPC
   ├── synchronization
   └── /proc monitoring
```

## 8. Architecture Quality Attributes

- testability;
- maintainability;
- observability;
- reproducibility;
- portability within Linux environments;
- low coupling;
- clear resource ownership.

## 9. Architecture Evolution

Architecture changes shall be recorded in ADRs when they materially affect interfaces, dependencies, persistence, or runtime behavior.
