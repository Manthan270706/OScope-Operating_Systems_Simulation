# OScope — Software Requirements Specification

## 1. Purpose

This SRS translates the OScope product requirements into implementable software requirements, interfaces, constraints, data structures, error behavior, observability requirements, and verification expectations.

## 2. System Context

```text
User
 │
 ▼
OScope CLI / Shell
 │
 ├── Simulation Modules
 │      ├── Scheduling
 │      ├── Memory
 │      ├── Paging
 │      ├── Deadlock
 │      ├── Disk
 │      └── File System
 │
 ├── Linux Experiment Modules
 │      ├── Process
 │      ├── Threads
 │      ├── IPC
 │      └── Synchronization
 │
 ├── Linux Monitoring
 │
 ▼
Experiment Engine
 │
 ├── Workload
 ├── Events
 ├── Metrics
 ├── Result Schema
 └── Reproducibility Metadata
 │
 ▼
Visualization / Analysis
 │
 ▼
Optional AI Layer
```

## 3. Runtime Model

OScope consists of:

1. **Core library** — algorithms, models, common types.
2. **Simulation layer** — deterministic educational models.
3. **Linux experiment layer** — POSIX/Linux programs and wrappers.
4. **Experiment engine** — workload, execution, events, metrics, results.
5. **CLI/shell** — user interaction.
6. **Analysis/visualization layer** — Python or other approved tooling.
7. **Optional AI adapter**.

## 4. Requirements

### 4.1 Input Requirements

Inputs may include:

- process arrival/burst/priority values;
- quantum and MLFQ configuration;
- memory block/request sizes;
- page reference strings and frame counts;
- resource matrices for deadlock experiments;
- disk request queues and initial head position;
- file-system operations;
- Linux experiment parameters;
- monitoring intervals;
- experiment configuration.

Inputs shall be validated before execution.

### 4.2 Output Requirements

Outputs may include:

- final algorithm result;
- execution timeline;
- event trace;
- metrics;
- allocation state;
- page-table state;
- deadlock safe sequence;
- disk seek sequence;
- Linux observation samples;
- structured experiment result.

## 5. Common Result Model

A result should contain, conceptually:

```text
ExperimentResult
 ├── experiment_id
 ├── module
 ├── algorithm
 ├── mode
 ├── configuration
 ├── workload
 ├── events
 ├── metrics
 ├── status
 ├── errors
 └── environment
```

`mode` shall distinguish at least:

- `simulation`
- `linux_experiment`
- `linux_monitoring`

## 6. Event Model

Events should be structured and timestamped relative to the experiment where applicable.

Examples:

```text
ProcessArrived
ProcessDispatched
ProcessPreempted
ProcessCompleted
MemoryAllocated
MemoryFreed
PageAccessed
PageFault
PageEvicted
ResourceRequested
ResourceGranted
ResourceReleased
IPCWrite
IPCRead
```

Real-time wall-clock timestamps and simulation timestamps must not be confused.

## 7. Metrics

### Scheduling Simulation

- waiting time
- turnaround time
- response time
- throughput
- simulated CPU utilization

### Paging

- page faults
- hit count
- fault rate
- replacement count

### Memory

- successful allocations
- failed allocations
- fragmentation measures

### Disk

- total head movement
- average movement where meaningful

### Linux Monitoring

- host CPU utilization
- host memory usage
- process observations
- selected I/O observations

All metrics must identify their source and meaning.

## 8. Detailed Module Specifications

### 8.1 Scheduling

Common input:

```text
Process {
  id
  arrival_time
  burst_time
  priority
}
```

Scheduling policies implement a common conceptual interface:

```text
schedule(workload, configuration) -> SchedulingResult
```

The scheduler shall produce execution segments and metrics.

### 8.2 Virtual Address Translation

The simulation shall follow:

```text
Virtual Address
      │
      ▼
Page Number + Offset
      │
      ▼
Page Table Lookup
      │
      ▼
Frame Number
      │
      ▼
Physical Address
```

The page offset is preserved during translation.

### 8.3 Paging

A page-reference experiment shall accept:

- reference string;
- number of frames;
- replacement policy.

Each access shall update the simulated frame state and event trace.

### 8.4 Demand Paging

Demand paging shall model:

1. reference to a non-resident page;
2. page fault;
3. frame allocation or replacement;
4. page-table update;
5. continuation of the reference.

### 8.5 Thrashing

The thrashing demonstration shall model the relationship between workload locality, available frames, and page-fault behavior. It is an educational simulation, not a kernel memory-management implementation.

### 8.6 Deadlock

The system shall model:

- available resources;
- maximum demand;
- current allocation;
- remaining need.

Banker's safety evaluation shall determine whether a safe sequence exists.

### 8.7 Coffman Conditions

The deadlock demonstration shall explicitly represent:

- mutual exclusion;
- hold and wait;
- no preemption;
- circular wait.

### 8.8 Peterson's Solution

The simulation shall model two competing processes using:

- intent flags;
- turn variable;
- entry/critical/exit behavior.

It shall explain that Peterson's algorithm is an educational mutual-exclusion solution under its stated assumptions.

### 8.9 Linux Processes

The real experiment layer may use:

```text
fork()
exec*()
wait()
waitpid()
getpid()
getppid()
```

The implementation must check system-call return values and release resources appropriately.

### 8.10 Linux Threads

The experiment layer shall demonstrate:

- thread creation;
- argument passing;
- joining;
- synchronization;
- race conditions.

### 8.11 IPC

The real Linux experiment layer shall retain visibility of the underlying primitives:

- `pipe()`
- FIFO APIs
- message queue APIs
- shared-memory APIs

Experiments shall document ownership and cleanup requirements.

### 8.12 Monitoring

Monitoring shall read documented Linux interfaces and expose the collected values with units and sampling intervals.

## 9. Resource Management

Low-level resources shall have explicit ownership.

Resources include:

- heap memory;
- file descriptors;
- processes;
- threads;
- pipes;
- FIFOs;
- message queues;
- shared-memory segments;
- mutexes;
- semaphores.

Where appropriate, C++ RAII wrappers should manage lifetime. POSIX resources that cannot be naturally represented by ordinary RAII must still have explicit cleanup paths.

## 10. Error Handling

The system shall handle:

- invalid command;
- invalid numeric input;
- empty workload;
- negative values where invalid;
- impossible allocation;
- invalid page/frame configuration;
- malformed deadlock matrices;
- system-call failure;
- unavailable Linux interface;
- resource exhaustion;
- experiment interruption.

Errors should be structured internally and presented as actionable CLI messages.

## 11. Logging

Logging levels should conceptually include:

- ERROR
- WARN
- INFO
- DEBUG
- TRACE

The default user experience should avoid excessive low-level output while retaining sufficient diagnostic information for development.

## 12. Configuration

Configuration shall be separated from source code.

Possible configuration categories:

- logging;
- experiment defaults;
- visualization;
- workload generation;
- monitoring interval;
- output location.

## 13. Reproducibility

A reproducible experiment should record:

- algorithm;
- input/workload;
- configuration;
- random seed when applicable;
- OScope version/commit where available;
- compiler/build information where relevant;
- host environment for real Linux experiments.

## 14. Concurrency Requirements

- Shared state must have explicit synchronization.
- Data races must be avoided in production experiment code.
- Demonstrations intentionally showing races must isolate that behavior and label it as such.
- Deadlocks introduced intentionally for education must have safe termination controls.

## 15. Security Requirements

- No privileged operation by default.
- Host-command execution must require explicit user action.
- Inputs must not be blindly interpolated into shell commands.
- Linux experiments should run with ordinary user privileges whenever possible.

## 16. Testing Requirements

Testing shall include:

### Unit tests
- scheduling calculations;
- page replacement;
- memory allocation;
- Banker's algorithm;
- disk scheduling;
- address translation.

### Integration tests
- CLI command routing;
- experiment execution;
- result serialization;
- module integration.

### System tests
- selected Linux process/thread/IPC demonstrations;
- monitoring behavior on the supported Linux environment.

### Property/edge tests
- empty workloads;
- single-item workloads;
- simultaneous arrivals;
- equal priorities;
- zero/large quantum boundaries;
- full memory;
- repeated page references;
- impossible resource states.

## 17. Traceability

Each requirement shall map to:

```text
Requirement
   ↓
Design component
   ↓
Implementation module
   ↓
Test
   ↓
Demonstration / evidence
```

Requirement IDs must remain stable throughout development.

## 18. Known Limitations

- Linux behavior is environment-dependent.
- Timing-sensitive demonstrations may vary between runs.
- Simulations intentionally simplify real kernel behavior.
- Buddy/Slab are educational models.
- AI output is advisory analysis, not authoritative OS behavior.
- File-system simulation is not a production filesystem.

## 19. Definition of Ready for Implementation

A module is ready to implement when:

- its requirements are stable;
- its inputs/outputs are defined;
- ownership/lifetime is understood;
- algorithm/model behavior is specified;
- errors and edge cases are identified;
- tests can be written;
- dependencies are known.

