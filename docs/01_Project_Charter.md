# OScope — Project Charter

**Project:** OScope  
**Course:** CI3202 — Operating Systems  
**Project Type:** Academic OS learning, simulation, experimentation, and Linux systems platform  
**Primary Implementation:** C++ on Linux/POSIX  
**Status:** Approved baseline for implementation planning

---

## 1. Project Purpose

OScope is an interactive Operating Systems learning and experimentation platform designed to connect OS theory with implementation, execution, measurement, visualization, and analysis.

The project follows:

> **Learn → Implement → Execute → Observe → Measure → Compare → Analyze**

OScope has two complementary sides:

1. **OS Simulation** — educational simulations of OS algorithms and mechanisms.
2. **Linux Systems Experiments** — real execution of selected Linux/POSIX mechanisms and system interfaces.

OScope is an educational platform and does not attempt to replace or modify the Linux kernel.

## 2. Objectives

- Strengthen understanding of core Operating Systems concepts.
- Implement major algorithms covered in CI3202.
- Demonstrate real Linux/POSIX process, thread, IPC, synchronization, and monitoring mechanisms.
- Provide measurable experiments rather than isolated programs.
- Visualize execution and algorithm behavior.
- Compare algorithms using reproducible workloads and metrics.
- Provide optional AI-assisted analysis only after the core OS functionality is established.
- Follow maintainable, testable, documented software-engineering practices.

## 3. Scope

### 3.1 Tier 1 — Core OS Concepts

- Process lifecycle and process-state simulation
- Process tree simulation and Linux process experiments
- Threads
- CPU scheduling:
  - FCFS
  - SJF
  - SRTF
  - Priority
  - Round Robin
  - MLFQ
- Synchronization:
  - mutexes
  - semaphores
  - Peterson's solution simulation
  - classical synchronization demonstrations
- IPC:
  - pipes
  - FIFOs
  - message queues
  - shared memory
- Deadlocks:
  - Coffman conditions demonstration
  - Banker's algorithm
  - detection/recovery demonstrations
- Memory allocation:
  - First Fit
  - Best Fit
  - Worst Fit
  - fragmentation analysis
- Paging:
  - page tables
  - address translation
  - page faults
  - demand paging
  - FIFO
  - LRU
  - Optimal
  - thrashing demonstration
- Disk scheduling:
  - FCFS
  - LIFO
  - SSTF
  - SCAN
  - C-SCAN
- Experiment metrics and reproducibility

### 3.2 Tier 2 — OScope Platform

- Educational OScope shell
- File-system simulation
- Linux resource monitoring through `/proc` and other permitted interfaces
- Visualization
- Experiment management
- Result storage
- Benchmarking and comparison

### 3.3 Tier 3 — Advanced Educational Modules

- Buddy-system simulation
- Slab-allocation simulation
- Advanced workload generation
- AI-assisted experiment analysis
- Optional intelligent scheduling/resource-analysis experiments

### 3.4 Tier 4 — Future Scope

- eBPF-based instrumentation
- xv6 integration
- container-oriented experiments
- advanced kernel instrumentation
- additional visualization frontends

## 4. Explicit Boundaries

OScope will distinguish between:

| Area | Nature |
|---|---|
| Scheduling algorithms | Simulation |
| Page replacement | Simulation |
| Banker's algorithm | Simulation |
| Memory allocation | Simulation |
| Buddy/Slab | Educational simulation |
| fork/exec/wait | Real Linux/POSIX experiment |
| pthreads | Real Linux/POSIX experiment |
| pipe/FIFO/message queue/shared memory | Real Linux/POSIX experiment |
| `/proc` monitoring | Real Linux observation |

Simulated metrics must not be presented as measurements of the Linux kernel.

## 5. Educational Shell

The OScope shell is an educational command interface, not a Bash replacement.

Example commands:

```text
oscope> process tree
oscope> schedule rr
oscope> memory first-fit
oscope> paging lru
oscope> deadlock banker
oscope> monitor cpu
oscope> run ls
```

## 6. Experiment Philosophy

Every major module should support:

- defined inputs
- controlled workload
- execution
- events/state transitions
- metrics
- result capture
- visualization where useful
- comparison
- reproducibility

The Experiment Engine is the platform-level connector between OS modules and analysis.

## 7. High-Level Architecture

```text
                         OSCOPE
                           │
             ┌─────────────┴─────────────┐
             │                           │
       OS SIMULATION                LINUX SYSTEMS
             │                           │
      Algorithms / Models        POSIX / Linux APIs
             │                           │
             └─────────────┬─────────────┘
                           ▼
                    EXPERIMENT ENGINE
                           │
                  ┌────────┼────────┐
                  ▼        ▼        ▼
               Metrics   Events  Workloads
                  │        │        │
                  └────────┼────────┘
                           ▼
                    VISUALIZATION
                           │
                           ▼
                        ANALYTICS
                           │
                           ▼
                            AI
```

## 8. Technology Direction

- C++17 or later for core implementation
- Linux environment
- POSIX APIs for real systems experiments
- CMake for builds
- Python for selected visualization/analysis workflows
- Git for version control
- GoogleTest or an equivalent C++ testing framework
- Sanitizers and static analysis where practical
- JSON or another documented structured format for experiment results

Final technology decisions are recorded through ADRs.

## 9. Deliverables

- Project documentation
- Architecture documentation
- Architecture Decision Records
- C++ source code
- Tests
- Experiment workloads
- Result schema
- Visualization/analysis scripts
- Build and run instructions
- Demonstration scenarios
- Final report and presentation material

## 10. Milestones

### Phase 0 — Documentation and Design
Charter → PRD → SRS → TDD → Architecture → ADRs → API/contracts → test strategy.

### Phase 1 — Core Simulation Engine
Scheduling, memory allocation, paging, deadlock, disk scheduling.

### Phase 2 — Linux Systems Experiments
Processes, threads, IPC, synchronization, monitoring.

### Phase 3 — Experiment Engine
Workloads, event capture, metrics, result schema, reproducibility.

### Phase 4 — Platform Layer
Shell, visualization, file-system simulation, experiment management.

### Phase 5 — Advanced Features
Buddy/Slab simulations and optional AI analysis.

### Phase 6 — Validation and Finalization
Testing, benchmarking, documentation, demonstrations, final report.

## 11. Definition of Done

A feature is considered done when:

- requirements are satisfied;
- design decisions are documented;
- implementation is complete;
- unit/integration tests are present where applicable;
- edge cases are addressed;
- errors are handled;
- resources are released correctly;
- metrics/results are reproducible;
- documentation is updated;
- the feature is integrated into the build;
- the feature can be demonstrated independently.

## 12. Risks

- Scope becoming too large
- Mixing simulated and real Linux behavior
- Weak testing of OS edge cases
- Resource leaks in low-level code
- Platform-specific behavior
- AI distracting from core OS learning
- Difficulties reproducing timing-sensitive experiments

Mitigation: prioritize Tier 1, isolate real Linux experiments, automate tests, use RAII/resource wrappers, record environment information, and keep AI optional.

## 13. Success Criteria

OScope should demonstrate that the project can:

1. implement major CI3202 algorithms;
2. execute selected real Linux/POSIX mechanisms;
3. measure and explain behavior;
4. compare alternatives;
5. reproduce experiments;
6. connect theory to observable execution;
7. maintain a professional engineering workflow.

