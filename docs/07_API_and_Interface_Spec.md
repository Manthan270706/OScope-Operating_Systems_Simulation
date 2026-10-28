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

### SCAN Boundary Sweep Convention
- **SCAN (Elevator)** services requests in the initial direction until reaching the physical disk boundary (`max_cylinder` when increasing, or `min_cylinder` when decreasing).
- Upon reaching the boundary, the head reverses direction and services all remaining requests in the opposite direction.
- In OScope, SCAN models the full boundary-to-boundary sweep convention: upon completing service of all requests in the reverse direction, the arm continues its traversal to the opposite physical disk boundary (`min_cylinder` when initial direction was increasing, or `max_cylinder` when decreasing).
- **Benchmark Reference:** For initial head $53$, range $[0, 199]$, initial direction `Increasing`, and requests $[98, 183, 37, 122, 14, 124, 65, 67]$:
  - Serviced Request Order: $65 \to 67 \to 98 \to 122 \to 124 \to 183 \to 37 \to 14$
  - Complete Head Path: $53 \to 65 \to 67 \to 98 \to 122 \to 124 \to 183 \to 199 \to 37 \to 14 \to 0$
  - Upward Movement: $199 - 53 = 146$ cylinders
  - Downward Movement: $199 - 0 = 199$ cylinders
  - Total Head Movement: $146 + 199 = \mathbf{345}$ cylinders
  - Final Head Position: $0$
- **Contrast with LOOK:** LOOK reverses strictly at the highest pending request ($183$) and terminates at the lowest pending request ($14$), producing path $53 \to 183 \to 14$, total movement $(183 - 53) + (183 - 14) = 130 + 169 = \mathbf{299}$ cylinders, and final head position $14$.

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

---

## 12. Virtual Memory and Address Translation APIs

Located in `include/oscope/paging/address_translation.hpp`:

```cpp
namespace oscope::paging {

struct AddressTranslationResult {
    bool valid = false;
    uint32_t virtual_address = 0;
    uint32_t page_number = 0;
    uint32_t offset = 0;
    uint32_t frame_number = 0;
    uint32_t physical_address = 0;
    bool page_fault = false;
    std::string message;
};

class VirtualAddressTranslator {
public:
    explicit VirtualAddressTranslator(uint32_t page_size = 4096);
    void map_page(uint32_t page_number, uint32_t frame_number, bool read_only = false);
    void unmap_page(uint32_t page_number);
    AddressTranslationResult translate(uint32_t virtual_address) const;
    void clear();
};

DemandPagingResult simulate_demand_paging(
    const std::vector<uint32_t>& virtual_addresses,
    uint32_t num_frames = 3,
    uint32_t page_size = 4096);

ThrashingSimulationResult simulate_thrashing_curve(
    const std::vector<uint32_t>& reference_pages,
    uint32_t min_frames = 1,
    uint32_t max_frames = 8);

} // namespace oscope::paging
```

## 13. Synchronization: Peterson's Algorithm API

Located in `include/oscope/synchronization/petersons_algorithm.hpp`:

```cpp
namespace oscope::synchronization {

struct PetersonTraceStep {
    uint32_t step_number = 0;
    uint32_t process_id = 0; // 0 or 1
    bool flag_p0 = false;
    bool flag_p1 = false;
    uint32_t turn = 0;
    std::string action;
};

struct PetersonsAlgorithmResult {
    bool mutual_exclusion_maintained = true;
    uint32_t p0_cs_entries = 0;
    uint32_t p1_cs_entries = 0;
    std::vector<PetersonTraceStep> trace;
    std::string educational_notes;
};

PetersonsAlgorithmResult run_petersons_algorithm(
    uint32_t rounds_p0 = 3,
    uint32_t rounds_p1 = 3,
    const std::vector<uint32_t>& interleaving_schedule = {});

} // namespace oscope::synchronization
```

## 14. Deadlock: Coffman Conditions API

Located in `include/oscope/deadlock/coffman_conditions.hpp`:

```cpp
namespace oscope::deadlock {

struct CoffmanAnalysisResult {
    bool mutual_exclusion = false;
    bool hold_and_wait = false;
    bool no_preemption = false;
    bool circular_wait = false;
    bool deadlock_vulnerable = false;
    std::string summary;
    std::vector<std::string> condition_details;
    std::vector<std::string> prevention_recommendations;
};

CoffmanAnalysisResult analyze_coffman_conditions(
    bool mutual_exclusion,
    bool hold_and_wait,
    bool no_preemption,
    bool circular_wait);

std::vector<std::string> get_prevention_strategies();

} // namespace oscope::deadlock
```

## 15. Linux Host Resource Monitoring API

Located in `include/oscope/monitoring/host_monitor.hpp`:

```cpp
namespace oscope::monitoring {

struct HostCpuObservation {
    double total_cpu_usage_percent = 0.0;
    double user_percent = 0.0;
    double system_percent = 0.0;
    double idle_percent = 0.0;
};

struct HostMemoryObservation {
    uint64_t total_ram_bytes = 0;
    uint64_t free_ram_bytes = 0;
    uint64_t available_ram_bytes = 0;
    double used_percent = 0.0;
};

struct ProcessObservation {
    pid_t pid = 0;
    std::string comm;
    char state = '?';
    uint64_t utime_ticks = 0;
    uint64_t stime_ticks = 0;
    uint64_t rss_bytes = 0;
    uint64_t vsize_bytes = 0;
};

struct HostObservationSnapshot {
    std::string timestamp;
    HostCpuObservation cpu;
    HostMemoryObservation memory;
    ProcessObservation self_process;
    std::vector<DiskIoObservation> disks;
};

class HostMonitor {
public:
    explicit HostMonitor(std::string proc_root = "/proc");
    HostObservationSnapshot sample_snapshot(pid_t target_pid = 0) const;
};

} // namespace oscope::monitoring
```

## 16. Educational File System Simulation API

Located in `include/oscope/filesystem/simple_fs.hpp`:

```cpp
namespace oscope::filesystem {

enum class AllocationStrategy {
    Contiguous,
    Linked,
    Indexed
};

class SimpleFileSystem {
public:
    explicit SimpleFileSystem(uint32_t total_blocks = 64, uint32_t block_size = 512);
    bool format();
    bool create_directory(const std::string& parent_path, const std::string& name);
    bool create_file(const std::string& parent_path, const std::string& name,
                     uint32_t size_bytes, AllocationStrategy strategy);
    std::vector<DirectoryEntry> list_directory(const std::string& path) const;
    FileSystemMetrics get_metrics() const;
    std::vector<bool> get_free_block_bitmap() const;
};

} // namespace oscope::filesystem
```

## 17. Linux POSIX IPC & Lifecycle Experiment APIs

Located in `include/oscope/experiments/ipc_experiments.hpp` and `include/oscope/experiments/process_lifecycle_experiment.hpp`:

```cpp
namespace oscope::experiments {

// POSIX FIFO (named pipe)
FifoIpcResult run_fifo_ipc_experiment(const std::string& test_message = "OScope Named Pipe Demo");

// POSIX Shared Memory (shm_open, mmap, shm_unlink)
SharedMemoryIpcResult run_shared_memory_ipc_experiment(const std::string& test_payload = "OScope Shared Memory Demo");

// Zombie Process Reaping
ZombieDemonstrationResult run_zombie_demonstration();

// Orphan Process Reparenting
OrphanDemonstrationResult run_orphan_demonstration();

} // namespace oscope::experiments
```

## 18. Demonstration CLI Flags

```text
oscope [options]
  --demo-all              Execute comprehensive demonstrations for all modules
  --demo-paging           Demonstrate address translation, demand paging, and thrashing
  --demo-sync             Demonstrate thread synchronization (Peterson's, POSIX semaphores, producer-consumer)
  --demo-coffman          Demonstrate Coffman conditions and deadlock prevention
  --demo-monitor          Observe real Linux host CPU, memory, and process state
  --demo-fs               Demonstrate educational filesystem allocation and bitmap
  --demo-ipc              Demonstrate POSIX FIFO, shared memory, and message queue IPC
  --demo-lifecycle        Demonstrate process exec, zombie reaping, and orphan adoption
  --demo-disk             Demonstrate disk scheduling algorithms (FCFS, SSTF, SCAN, etc.)
  -j, --json              Output experiment results in structured JSON format
  -h, --help              Display help message and exit
```

## 19. Linux/POSIX Synchronization & IPC Extensions API

### 19.1 POSIX Semaphores & Bounded-Buffer Producer-Consumer (`<oscope/synchronization/semaphore_experiment.hpp>`)
- `SemaphoreExperimentResult run_semaphore_experiment(size_t num_threads = 4, size_t iterations_per_thread = 10000)`: Evaluates POSIX unnamed semaphores (`sem_init`, `sem_wait`, `sem_post`, `sem_destroy`) with multi-threaded atomic counter verification.
- `ProducerConsumerResult run_producer_consumer_experiment(size_t buffer_capacity = 5, size_t total_items = 50, size_t num_producers = 2, size_t num_consumers = 2)`: Classical bounded-buffer problem utilizing counting semaphores for empty/occupied slots and a mutex for thread-safe circular buffer access.

### 19.2 POSIX Message Queues (`<oscope/experiments/ipc_experiments.hpp>`)
- `MessageQueueExperimentResult run_message_queue_experiment(const std::string& message = "...", unsigned int priority = 1)`: POSIX message queue inter-process communication using `mq_open`, `mq_send`, `mq_receive`/`mq_timedreceive`, `mq_close`, and `mq_unlink`.

### 19.3 Process Image Replacement (`<oscope/experiments/process_experiment.hpp>`)
- `ProcessExecResult run_process_exec_experiment(const std::string& executable_path = "/bin/echo", const std::string& argument = "...")`: Controlled process-image replacement demonstration via `fork()` -> `execv()`/`execvp()` -> `waitpid()`. Captures child stdout and verifies exit code.
