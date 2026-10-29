# OScope — Technical Design Document

## 1. Purpose

This document defines the technical design of OScope sufficiently for implementation to begin without repeatedly redesigning the core architecture.

## 2. Design Goals

- modularity;
- testability;
- deterministic simulation;
- explicit Linux/POSIX experiments;
- reusable experiment infrastructure;
- measurable behavior;
- clear ownership of resources;
- minimal unnecessary coupling.

## 3. Architecture

```text
┌─────────────────────────────────────────────────────┐
│                    OScope CLI                       │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│                Application Services                 │
│ command routing / experiment orchestration          │
└──────────────┬──────────────────────┬───────────────┘
               │                      │
       ┌───────▼───────┐      ┌───────▼────────┐
       │ Simulation    │      │ Linux          │
       │ Modules       │      │ Experiments    │
       └───────┬───────┘      └───────┬────────┘
               │                      │
               └──────────┬───────────┘
                          ▼
                 ┌────────────────┐
                 │ Experiment     │
                 │ Engine         │
                 └───────┬────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Workloads        Events        Metrics
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Result Repository
                         │
               ┌─────────┴─────────┐
               ▼                   ▼
        Visualization          Analytics
                                   │
                                   ▼
                                   AI
```

## 4. Repository Structure

```text
oscope/
├── CMakeLists.txt
├── README.md
├── docs/
├── include/
│   └── oscope/
│       ├── core/
│       ├── scheduling/
│       ├── memory/
│       ├── paging/
│       ├── deadlock/
│       ├── disk/
│       ├── process/
│       ├── threads/
│       ├── ipc/
│       ├── sync/
│       ├── filesystem/
│       ├── monitoring/
│       ├── experiment/
│       └── shell/
├── src/
│   └── ...
├── tests/
│   ├── unit/
│   ├── integration/
│   └── system/
├── experiments/
├── scripts/
├── configs/
├── examples/
└── results/
```

## 5. Core Domain Model

### Process

```text
Process
- id
- arrival_time
- burst_time
- remaining_time
- priority
- state
```

### Memory Block

```text
MemoryBlock
- start
- size
- allocated
- owner
```

### Page

```text
Page
- page_number
- resident
- frame_number
```

### Resource

```text
Resource
- id
- total
- available
```

### Experiment

```text
Experiment
- id
- module
- algorithm
- configuration
- workload
- execution
```

### Experiment Result

```text
ExperimentResult
- metadata
- events
- metrics
- status
- errors
```

## 6. Interfaces

Conceptual interfaces:

```text
IScheduler
  schedule(Workload, SchedulerConfig) -> SchedulingResult

IPageReplacement
  simulate(ReferenceString, FrameCount) -> PagingResult

IMemoryAllocator
  allocate(size) -> AllocationResult
  deallocate(id) -> Result

IDeadlockAnalyzer
  analyze(ResourceState) -> DeadlockResult

IDiskScheduler
  schedule(RequestQueue, DiskConfig) -> DiskResult
```

The concrete C++ signatures will be finalized during implementation according to ownership and type-safety decisions.

## 7. Scheduling Design

Each scheduling policy receives the same workload representation.

The scheduler emits:

```text
ExecutionSegment {
    process_id
    start
    end
}
```

Metrics are derived from the execution trace rather than independently recomputed by every scheduler.

This keeps metric calculations consistent.

## 8. Paging Design

Address translation:

```text
virtual_address
 ├── page_number
 └── offset

page_number
      ↓
page_table
      ↓
frame_number

physical_address =
    frame_number + offset
```

Page replacement policies operate on a common frame-state representation.

## 9. Memory Allocation Design

All allocation strategies operate on a common block representation.

Algorithms differ only in block-selection policy.

This allows:

- common workload;
- common event model;
- common fragmentation calculations;
- direct comparison.

## 10. Deadlock Design

The deadlock subsystem separates:

1. state representation;
2. safety analysis;
3. detection;
4. visualization.

Banker's algorithm should not directly own presentation logic.

## 11. Linux Experiment Design

Linux experiments should be isolated from simulation code.

Example:

```text
linux/
  process/
    fork_demo
    zombie_demo
    orphan_demo
    exec_demo
  threads/
    pthread_demo
  ipc/
    pipe_demo
    fifo_demo
    message_queue_demo
    shared_memory_demo
```

The experiment engine may launch or coordinate these experiments, but the demonstrations should remain understandable as Linux/POSIX programs.

## 12. Experiment Engine

The Experiment Engine provides:

- experiment identity;
- configuration;
- workload;
- execution;
- event collection;
- metrics;
- result serialization;
- environment metadata.

The engine should not contain algorithm-specific logic.

## 13. Result Schema

A first version may use JSON:

```json
{
  "experiment_id": "example-001",
  "module": "scheduling",
  "algorithm": "round_robin",
  "mode": "simulation",
  "configuration": {},
  "workload": {},
  "events": [],
  "metrics": {},
  "status": "success",
  "errors": [],
  "environment": {}
}
```

The schema should evolve only through documented changes.

## 14. Resource Ownership

C++ resource ownership should prefer RAII.

Examples:

- file descriptors → RAII wrapper;
- memory → standard containers/smart pointers where suitable;
- threads → managed thread object with explicit join/stop semantics;
- IPC handles → dedicated cleanup wrappers;
- mutex/semaphore ownership → explicit lifecycle.

## 15. Visualization Boundary

C++ should focus on:

- algorithms;
- experiments;
- results.

Python should consume structured result files for:

- charts;
- comparisons;
- reports.

This avoids coupling the simulation core to a visualization framework.

## 16. Build Design

CMake should define:

- core library;
- CLI executable;
- Linux experiment targets;
- tests.

The project should support separate Debug and Release builds.

## 17. Testing Design

The architecture shall support dependency-light unit testing for algorithmic modules and environment-aware tests for Linux-specific modules.

Deterministic simulations should have fixed expected-result tests.

## 18. Performance Strategy

Do not optimize prematurely.

Initial priorities:

1. correctness;
2. testability;
3. clarity;
4. observability;
5. performance optimization after measurement.

## 19. Design Constraints

- Linux is the primary runtime.
- Some modules intentionally model simplified OS behavior.
- Linux-specific APIs must not leak into pure simulation algorithms.
- Simulation modules should remain deterministic for fixed input/configuration.
