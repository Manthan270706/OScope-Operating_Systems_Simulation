# OScope — Product Requirements Document

## 1. Product Overview

OScope is an interactive Operating Systems learning and experimentation platform.

It combines:

- educational OS algorithm simulation;
- real Linux/POSIX experiments;
- controlled workloads;
- metrics;
- visualization;
- comparison;
- optional AI-assisted analysis.

The product is intended primarily for CI3202 learning and demonstration.

## 2. Problem Statement

Operating Systems concepts are often learned as separate algorithms, definitions, and practical programs. OScope aims to connect those pieces into an observable experimental workflow.

The central product loop is:

> **Learn → Implement → Execute → Observe → Measure → Compare → Analyze**

## 3. Product Goals

- Make OS algorithms executable and observable.
- Make Linux mechanisms demonstrable through real experiments.
- Enable controlled comparisons.
- Preserve a clear distinction between simulation and real-system behavior.
- Provide reusable experiment infrastructure.
- Support course syllabus coverage.
- Encourage engineering practices such as modularity, testing, reproducibility, and documentation.

## 4. Non-Goals

OScope will not:

- replace Bash;
- replace the Linux kernel;
- modify kernel scheduling behavior;
- implement a production operating system;
- claim simulated metrics represent kernel measurements;
- make AI a required component of the core system.

## 5. Users

### Primary
- OS students
- project team members
- instructors/evaluators

### Secondary
- developers interested in OS experiments
- learners exploring Linux/POSIX mechanisms

## 6. Product Principles

1. **Concept first**
2. **Implementation must be observable**
3. **Simulation and real Linux experiments must be separated**
4. **Metrics must be explicit**
5. **Experiments should be reproducible**
6. **AI is optional and downstream of core functionality**
7. **Modules should be testable independently**
8. **The system should favor explainability over hidden abstraction**

## 7. Functional Requirements

### 7.1 Educational Shell

**FR-SHELL-001** The system shall provide an OScope educational shell.

**FR-SHELL-002** The shell shall support module-oriented commands.

**FR-SHELL-003** The shell shall provide command validation and meaningful errors.

**FR-SHELL-004** The shell shall distinguish OScope commands from optional host-command execution.

### 7.2 Processes

**FR-PROC-001** The system shall simulate process states.

**FR-PROC-002** The system shall represent process metadata using a PCB-style model.

**FR-PROC-003** The system shall demonstrate process creation and termination concepts.

**FR-PROC-004** The Linux experiment layer shall demonstrate `fork()`, `exec*()`, `wait()/waitpid()`, and related process behavior.

**FR-PROC-005** The system shall support process-tree demonstrations.

**FR-PROC-006** The system shall provide zombie and orphan demonstrations.

### 7.3 Threads

**FR-THREAD-001** The system shall provide thread demonstrations.

**FR-THREAD-002** Linux experiments shall use POSIX threads where applicable.

**FR-THREAD-003** The system shall demonstrate thread creation, joining, synchronization, and race conditions.

### 7.4 CPU Scheduling

**FR-SCHED-001** The system shall implement FCFS.

**FR-SCHED-002** The system shall implement SJF.

**FR-SCHED-003** The system shall implement SRTF.

**FR-SCHED-004** The system shall implement Priority Scheduling.

**FR-SCHED-005** The system shall implement Round Robin.

**FR-SCHED-006** The system shall implement MLFQ.

**FR-SCHED-007** The system shall calculate waiting time, turnaround time, response time, throughput, and simulated CPU utilization where meaningful.

**FR-SCHED-008** The system shall expose a common scheduling workload representation.

### 7.5 Synchronization

**FR-SYNC-001** The system shall demonstrate critical-section requirements.

**FR-SYNC-002** The system shall provide mutex-based synchronization demonstrations.

**FR-SYNC-003** The system shall provide semaphore demonstrations.

**FR-SYNC-004** The system shall demonstrate race conditions.

**FR-SYNC-005** The system shall provide classical synchronization examples.

**FR-SYNC-006** The system shall demonstrate deadlock-prone synchronization scenarios.

**FR-SYNC-007** The system shall provide an educational simulation of Peterson's solution for two processes.

### 7.6 IPC

**FR-IPC-001** The system shall demonstrate anonymous pipes.

**FR-IPC-002** The system shall demonstrate FIFOs.

**FR-IPC-003** The system shall demonstrate POSIX/System V message-queue mechanisms as selected during design.

**FR-IPC-004** The system shall demonstrate shared memory.

**FR-IPC-005** Demonstrations shall expose the underlying Linux/POSIX mechanism rather than hiding it behind a generic abstraction.

### 7.7 Deadlocks

**FR-DEAD-001** The system shall represent processes, resources, allocations, and outstanding requests.

**FR-DEAD-002** The system shall implement the Banker's algorithm.

**FR-DEAD-003** The system shall support deadlock detection demonstrations.

**FR-DEAD-004** The system shall demonstrate prevention/avoidance concepts.

**FR-DEAD-005** The system shall provide recovery demonstrations at an educational level.

**FR-DEAD-006** The system shall represent resource-allocation graphs where appropriate.

**FR-DEAD-007** The system shall explain safe and unsafe states.

**FR-DEAD-008** The system shall provide an educational demonstration of the four Coffman deadlock conditions.

### 7.8 Memory Allocation

**FR-MEM-001** The system shall implement First Fit.

**FR-MEM-002** The system shall implement Best Fit.

**FR-MEM-003** The system shall implement Worst Fit.

**FR-MEM-004** The system shall calculate internal/external fragmentation where applicable.

**FR-MEM-005** The system shall provide allocation/deallocation event traces.

### 7.9 Paging and Virtual Memory

**FR-PAGE-001** The system shall represent pages and frames.

**FR-PAGE-002** The system shall provide page-table simulation.

**FR-PAGE-003** The system shall simulate virtual-to-physical address translation.

**FR-PAGE-004** The translation model shall expose page number, offset, frame number, and physical address.

**FR-PAGE-005** The system shall simulate page faults.

**FR-PAGE-006** The system shall implement FIFO page replacement.

**FR-PAGE-007** The system shall implement LRU page replacement.

**FR-PAGE-008** The system shall implement Optimal page replacement.

**FR-PAGE-009** The system shall calculate page-fault statistics.

**FR-PAGE-010** The system shall support configurable reference strings and frame counts.

**FR-PAGE-011** The system shall provide a demand-paging simulation.

**FR-PAGE-012** The system shall provide an educational thrashing demonstration.

### 7.10 Buddy and Slab

**FR-ALLOC-001** The system may provide a Buddy System simulation.

**FR-ALLOC-002** The system may provide a Slab allocation simulation.

These modules are educational models and shall not claim to reproduce the complete Linux kernel allocator implementation.

### 7.11 File System Simulation

**FR-FS-001** The system shall provide a simulated file-system model.

**FR-FS-002** The model shall represent files/directories and metadata.

**FR-FS-003** The system shall demonstrate directory traversal.

**FR-FS-004** The system shall provide educational file-allocation demonstrations.

**FR-FS-005** The system shall provide free-space management demonstrations.

File-system simulation is a platform feature and is not required to reproduce a production filesystem.

### 7.12 Disk Scheduling

**FR-DISK-001** The system shall implement FCFS disk scheduling.

**FR-DISK-002** The system shall implement LIFO.

**FR-DISK-003** The system shall implement SSTF.

**FR-DISK-004** The system shall implement SCAN.

**FR-DISK-005** The system shall implement C-SCAN.

**FR-DISK-006** The system shall calculate seek-distance and related comparison metrics.

> Note: the course syllabus may use the term STTF; OScope uses the conventional term SSTF (Shortest Seek Time First).

### 7.13 Linux Monitoring

**FR-MON-001** The system shall provide Linux process monitoring.

**FR-MON-002** The system shall collect host CPU and memory observations using permitted Linux interfaces.

**FR-MON-003** The system shall collect selected disk/I/O observations where supported.

**FR-MON-004** Monitoring results shall be clearly identified as real host measurements.

### 7.14 Experiment Engine

**FR-EXP-001** The system shall define a reusable experiment abstraction.

**FR-EXP-002** An experiment shall contain configuration, workload, execution information, events, metrics, and results.

**FR-EXP-003** The system shall support reproducible workload definitions.

**FR-EXP-004** Experiment results shall use a documented machine-readable schema.

**FR-EXP-005** The system shall record relevant environment metadata.

**FR-EXP-006** The system shall support comparison of multiple algorithms under compatible workloads.

### 7.15 Visualization

**FR-VIZ-001** The system shall provide visualizations for selected simulations.

**FR-VIZ-002** Scheduling visualization shall support timeline/Gantt-style views.

**FR-VIZ-003** Paging visualization shall show reference-string/frame behavior.

**FR-VIZ-004** Memory allocation visualization shall show block states.

**FR-VIZ-005** Experiment results shall be viewable in tabular form.

### 7.16 AI Analysis

**FR-AI-001** AI functionality shall be optional.

**FR-AI-002** AI shall operate on structured experiment results rather than replacing core algorithms.

**FR-AI-003** AI analysis shall explain observed patterns and trade-offs.

**FR-AI-004** AI output shall identify the experiment data used for its conclusions where practical.

## 8. Non-Functional Requirements

### Performance
- Simulation modules should execute deterministically for identical inputs.
- Large workloads should not cause unnecessary quadratic work where avoidable.
- Monitoring should avoid excessive polling overhead.

### Reliability
- Invalid inputs must be rejected cleanly.
- Failures in one experiment must not corrupt unrelated experiments.

### Maintainability
- Modules should have clear interfaces.
- Shared concepts should not be duplicated.
- Resource ownership should be explicit.

### Reproducibility
- Seeds, inputs, configuration, and relevant environment metadata should be recorded.

### Observability
- Experiments should produce structured events and metrics where useful.

### Portability
- Primary target is Linux.
- Linux-specific experiments must be clearly marked.

### Security
- Host-command execution shall be explicit.
- No module should execute arbitrary privileged operations by default.

## 9. Priority Model

| Priority | Meaning |
|---|---|
| P0 | Core implementation target |
| P1 | Planned platform capability |
| P2 | Advanced/optional |
| P3 | Future |

### P0
Process, threads, scheduling, synchronization, IPC, deadlock, memory allocation, paging, page replacement, disk scheduling, experiment metrics.

### P1
Educational shell, file-system simulation, monitoring, visualization, experiment management, MLFQ integration if scheduled after the initial scheduler set.

### P2
Buddy, Slab, advanced analytics, AI-assisted analysis.

### P3
eBPF, xv6, containers, advanced kernel instrumentation.

## 10. Acceptance Criteria

A feature is accepted when:

- expected inputs produce correct outputs;
- invalid inputs produce controlled errors;
- edge cases are tested;
- relevant metrics are correct;
- behavior is documented;
- the module builds in the supported environment;
- reproducibility requirements are met where applicable.

## 11. Key Product Metric

The primary success measure is not the number of modules. It is whether a learner can move from an OS concept to an executable experiment and explain the observed behavior using measurements and evidence.
