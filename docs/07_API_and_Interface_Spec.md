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

```text
analyze(resource_state)
    → DeadlockResult
```

Result may contain:

- safe/unsafe status;
- safe sequence;
- remaining resources;
- explanatory events.

## 7. Disk Scheduling Interface

```text
schedule(request_queue, initial_head, disk_config)
    → DiskResult
```

Result contains:

- service order;
- head movement;
- total movement;
- derived statistics.

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
