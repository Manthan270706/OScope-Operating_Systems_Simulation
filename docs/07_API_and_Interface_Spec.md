# OScope — API and Interface Specification

## 1. Purpose

This document defines the stable conceptual interfaces between OScope modules before implementation.

## 2. Common Result Contract

Every major simulation should conceptually return:

```text
Result<T>
- status
- value
- errors
- warnings
- metadata
```

The exact C++ implementation will be finalized during coding.

## 3. Scheduling Interface

```text
schedule(workload, config)
    → SchedulingResult
```

`SchedulingResult` contains:

- execution segments;
- per-process metrics;
- aggregate metrics;
- warnings/errors.

## 4. Page Replacement Interface

```text
simulate(reference_string, frame_count)
    → PagingResult
```

The policy is supplied by the concrete algorithm.

## 5. Memory Allocation Interface

```text
allocate(request_size)
deallocate(allocation_id)
snapshot()
```

The allocator reports allocation state and fragmentation information.

## 6. Deadlock Interface

The Deadlock Management module (`include/oscope/deadlock/`) provides Banker's safety analysis, resource-request simulation, and deadlock detection:

```cpp
namespace oscope::deadlock {

// Banker's safety algorithm: checks safety and returns safe sequence or blocked processes
SafetyResult check_safety(const DeadlockState& state);

// Resource-request algorithm: validates request, tests tentative safety, and commits or rolls back
ResourceRequestResult request_resources(
    const DeadlockState& current_state,
    int process_id,
    const std::vector<int>& request);

// Deadlock detection algorithm: identifies processes that cannot finish given allocation and current requests
DetectionResult detect_deadlock(
    int num_processes,
    int num_resources,
    const std::vector<int>& available,
    const std::vector<std::vector<int>>& allocation,
    const std::vector<std::vector<int>>& request);

} // namespace oscope::deadlock
```

### Distinction: Avoidance (Safe vs Unsafe) vs Detection (Deadlock)
- **Banker's Safety (Avoidance):** Evaluates whether there exists at least one order in which all processes can execute assuming each process may eventually claim up to its maximum declared need (`Max`). An **unsafe state** is *not* a deadlock; it is an operational state where deadlock is no longer guaranteed to be avoidable if processes simultaneously claim their maximum requirements.
- **Deadlock Detection:** Evaluates the *current* real or simulated execution state where processes are actually blocked waiting on outstanding requests (`Request` / `Allocation`), identifying processes currently unable to progress.

## 7. Disk Scheduling Interface

The Disk Scheduling module (`include/oscope/disk/`) provides scheduling algorithms and comparative evaluation:

```cpp
namespace oscope::disk {

enum class DiskAlgorithm {
    FCFS,
    SSTF,
    SCAN,
    CSCAN,
    LOOK,
    CLOOK
};

enum class Direction {
    Up,   // Toward higher cylinder numbers
    Down  // Toward lower cylinder numbers
};

// Execute single algorithm
DiskSchedulingResult schedule_disk(
    DiskAlgorithm algorithm,
    const DiskWorkload& workload,
    const DiskConfig& config);

// Compare all six algorithms on identical workload without mutating input
DiskComparisonResult compare_all_disk_algorithms(
    const DiskWorkload& workload,
    const DiskConfig& config);

} // namespace oscope::disk
```

### Circular Wraparound Accounting Convention
- **C-SCAN and C-LOOK** service requests in one direction (e.g., Up toward higher cylinders). Upon completing service in that direction, the head jumps to the opposite end (C-SCAN: from `max_cylinder` down to `min_cylinder`; C-LOOK: from largest serviced request down to smallest remaining request) without servicing requests during the return trip.
- In OScope, the return jump distance is tracked explicitly in `wraparound_movement` and accounted for in `total_head_movement = service_movement + wraparound_movement` to ensure exact, transparent, and reproducible accounting.

## 8. Experiment Interface

```text
Experiment
  configure()
  validate()
  run()
  collect_result()
```

The experiment abstraction should support both simulation and Linux experiment modes.

## 9. Shell Interface

Conceptual syntax:

```text
schedule <algorithm> [options]
paging <algorithm> [options]
memory <algorithm> [options]
deadlock <algorithm> [options]
disk <algorithm> [options]
process <demo> [options]
thread <demo> [options]
ipc <demo> [options]
sync <demo> [options]
monitor <resource> [options]
experiment <command> [options]
```

## 10. Result Serialization

The serialization layer must:

- preserve required fields;
- reject malformed results;
- include schema/version information;
- support future backward-compatible changes.

## 11. Versioning

Any breaking result-schema or public-interface change shall be documented in an ADR and reflected in the project changelog.
