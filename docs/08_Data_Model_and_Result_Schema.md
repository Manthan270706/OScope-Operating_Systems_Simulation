# OScope — Data Model and Result Schema

## 1. Purpose

This document defines the initial conceptual data model for workloads, events, metrics, and experiment results.

## 2. Workload

A workload is a deterministic description of an experiment's input.

Examples:

- process list;
- page reference string;
- memory requests;
- disk request queue;
- resource matrices.

## 3. Event

```text
Event
- event_id
- type
- simulation_time or relative_time
- actor
- payload
```

The timestamp field must identify whether it is simulated time or real elapsed time.

## 4. Metrics

```text
Metric
- name
- value
- unit
- source
- description
```

## 5. Experiment Metadata

```text
ExperimentMetadata
- experiment_id
- module
- algorithm
- mode
- created_at
- oscope_version
- seed
- environment
```

## 6. Result

```text
{
  "schema_version": "1.0",
  "experiment": {},
  "workload": {},
  "events": [],
  "metrics": {},
  "status": "success",
  "errors": []
}
```

## 7. Reproducibility Fields

For deterministic simulations:

- input;
- configuration;
- seed if applicable;
- algorithm version.

For Linux experiments:

- kernel/environment information where available;
- compiler/build version;
- host resource context where relevant.

## 8. Naming

Names should be stable, machine-readable, and documented. Avoid using presentation-only labels as schema identifiers.

## 9. Compatibility

Schema changes shall prefer additive evolution. Breaking changes require a version change and ADR.

---

## 10. Linux/POSIX Experiments JSON Schema (v1.0.0)

OScope provides structured, machine-readable JSON reporting for Linux/POSIX experiments via `oscope::reporting`.

### 10.1 Schema Overview

All experiment JSON outputs share a uniform top-level envelope:

```json
{
  "schema_version": "1.0.0",
  "category": "linux_posix_experiment",
  "experiment": "<experiment_name>",
  "status": "success | failure",
  "success": true,
  "result": { ... },
  "error": null
}
```

- `schema_version`: Semantic schema version string (`"1.0.0"`).
- `category`: Category identifier (`"linux_posix_experiment"`).
- `experiment`: Name of experiment (`"process_creation"`, `"thread_creation"`, `"thread_synchronization"`, `"pipe_ipc"`).
- `status`: High-level execution status string (`"success"` or `"failure"`).
- `success`: Boolean flag indicating whether the experiment satisfied all validation checks.
- `result`: Experiment-specific metrics and execution details.
- `error`: `null` on success, or an object containing error information (`message`, `status_code`) on failure.

### 10.2 Experiment Result Schemas & Examples

#### Process Creation (`process_creation`)

Result fields:
- `parent_pid` (integer): PID of parent process.
- `child_pid` (integer | null): PID of spawned child process, or null if fork failed.
- `child_exited_normally` (boolean): Whether child terminated via normal exit.
- `child_exit_code` (integer | null): Child exit code if exited normally, else null.
- `child_termination_signal` (integer | null): Termination signal if killed by signal, else null.
- `status_code` (string): Specific experiment status (`"success"`, `"fork_failed"`, `"wait_failed"`, `"abnormal_termination"`, `"unexpected_exit_code"`).
- `message` (string): Descriptive status summary.

Example Success:
```json
{
  "schema_version": "1.0.0",
  "category": "linux_posix_experiment",
  "experiment": "process_creation",
  "status": "success",
  "success": true,
  "result": {
    "parent_pid": 4998,
    "child_pid": 4999,
    "child_exited_normally": true,
    "child_exit_code": 42,
    "child_termination_signal": null,
    "status_code": "success",
    "message": "Child process exited normally with expected exit code 42."
  },
  "error": null
}
```

#### Thread Creation (`thread_creation`)

Result fields:
- `requested_threads` (unsigned integer): Number of threads requested.
- `started_threads` (unsigned integer): Number of worker threads successfully created.
- `completed_threads` (unsigned integer): Number of worker threads joined after task completion.
- `worker_results` (array of integers): Ordered computational outputs from each worker thread.

Example Success:
```json
{
  "schema_version": "1.0.0",
  "category": "linux_posix_experiment",
  "experiment": "thread_creation",
  "status": "success",
  "success": true,
  "result": {
    "requested_threads": 4,
    "started_threads": 4,
    "completed_threads": 4,
    "worker_results": [100, 200, 300, 400]
  },
  "error": null
}
```

#### Thread Synchronization (`thread_synchronization`)

Result fields:
- `num_threads` (unsigned integer): Concurrent worker count.
- `iterations_per_thread` (unsigned integer): Increments per thread.
- `threads_completed` (unsigned integer): Successfully joined workers.
- `expected_counter` (unsigned integer): Mathematical expected counter total.
- `actual_counter` (unsigned integer): Shared counter value protected by mutex.
- `counter_match` (boolean): `true` if actual matches expected, demonstrating no data race.

Example Success:
```json
{
  "schema_version": "1.0.0",
  "category": "linux_posix_experiment",
  "experiment": "thread_synchronization",
  "status": "success",
  "success": true,
  "result": {
    "num_threads": 4,
    "iterations_per_thread": 10000,
    "threads_completed": 4,
    "expected_counter": 40000,
    "actual_counter": 40000,
    "counter_match": true
  },
  "error": null
}
```

#### Pipe-based IPC (`pipe_ipc`)

Result fields:
- `direction` (string): Unidirectional pipe flow (`"child_to_parent"`).
- `parent_pid` (integer): Reader parent process PID.
- `child_pid` (integer | null): Writer child process PID.
- `child_exited_normally` (boolean): Child exit state.
- `child_exit_code` (integer | null): Exit code from child.
- `child_termination_signal` (integer | null): Signal if terminated abnormally.
- `sent_message` (string): Message written by child into pipe.
- `received_message` (string): Message read by parent from pipe.
- `messages_match` (boolean): Integrity verification check.
- `status_code` (string): Experiment status code (`"success"`, `"read_failed"`, `"write_failed"`, etc.).

Example Success:
```json
{
  "schema_version": "1.0.0",
  "category": "linux_posix_experiment",
  "experiment": "pipe_ipc",
  "status": "success",
  "success": true,
  "result": {
    "direction": "child_to_parent",
    "parent_pid": 4998,
    "child_pid": 5008,
    "child_exited_normally": true,
    "child_exit_code": 0,
    "child_termination_signal": null,
    "sent_message": "Hello from OScope child process via POSIX pipe!",
    "received_message": "Hello from OScope child process via POSIX pipe!",
    "messages_match": true,
    "status_code": "success"
  },
  "error": null
}
```

### 10.3 CLI Usage and Output Contract

1. **Default Mode (Human-Readable):**
   ```bash
   ./build/oscope
   ```
   Interactive menus, prompts, banners, and formatted tables are written to standard output.

2. **JSON Output Mode:**
   ```bash
   ./build/oscope --json
   # or
   ./build/oscope -j
   # or
   ./build/oscope --format json
   ```
   **Output Contract:** Standard output emits a single valid JSON document containing an array of all experiment results executed during the session (e.g., `[ { ... }, { ... } ]`). When no experiments are run, an empty array `[]` is emitted. Interactive navigation menus, prompts, and input validation diagnostics are routed to standard error (`stderr`), ensuring standard output (`stdout`) remains strictly valid, machine-readable JSON suitable for piping directly to tools like `python3 -m json.tool` or `jq`.

3. **Programmatic API:**
   ```cpp
   #include "oscope/reporting/experiment_reporter.hpp"

   auto result = oscope::experiments::run_pipe_ipc_experiment();
   std::string json_output = oscope::reporting::serialize_result(result, true);
   ```
