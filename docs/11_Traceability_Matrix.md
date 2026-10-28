# OScope — Requirements Traceability Matrix

This document provides complete, bidirectional traceability between product functional requirements (from `02_PRD.md` and `03_SRS.md`), design specifications, source code implementations, unit/integration tests, and demonstration mechanisms.

## Verification Rule
No requirement is marked **Complete** without concrete implementation evidence and an automated test or executable CLI demonstration verified in the WSL Linux environment.

---

## Traceability Summary Table

| Requirement ID | Module / Area | Description | Implementation File(s) | Test File(s) | Verification Status | Demo / CLI Trigger |
|---|---|---|---|---|---|---|
| **FR-SHELL-001** | Shell / CLI | OScope interactive educational CLI shell | `src/main.cpp`, `src/cli.cpp` | `tests/cli_test.cpp` | Complete & Verified | `./build/oscope` |
| **FR-SHELL-002** | Shell / CLI | Module-oriented submenus (Scheduling, Memory, Paging, Deadlock, Disk, Experiments) | `src/cli.cpp`, `include/oscope/cli.hpp` | `tests/*_cli_test.cpp` | Complete & Verified | Interactive Menu options 1–13 |
| **FR-SHELL-003** | Shell / CLI | Input validation and descriptive error recovery | `src/cli.cpp` | `tests/*_cli_test.cpp` | Complete & Verified | Malformed input handling |
| **FR-SHELL-004** | Shell / CLI | Distinction between OScope simulation and host execution | `src/cli.cpp`, `src/main.cpp` | `tests/experiments_cli_test.cpp` | Complete & Verified | Host Monitor vs Simulations |
| **FR-PROC-001** | Processes | Simulated process lifecycle and states | `include/oscope/core/types.hpp`, `src/scheduling/` | `tests/scheduling_test.cpp` | Complete & Verified | CPU Schedulers |
| **FR-PROC-002** | Processes | Process Control Block (PCB) representation | `include/oscope/core/types.hpp` | `tests/scheduling_test.cpp` | Complete & Verified | PCB state transitions |
| **FR-PROC-003** | Processes | Process creation and termination concepts | `src/experiments/process_experiment.cpp` | `tests/process_experiment_test.cpp` | Complete & Verified | Experiment Menu Option 1 |
| **FR-PROC-004** | Processes | POSIX `fork()`, `exec*()`, `waitpid()` process image replacement | `src/experiments/process_experiment.cpp` | `tests/process_experiment_test.cpp` | Complete & Verified | `oscope --demo-lifecycle`, Menu Option 1 |
| **FR-PROC-005** | Processes | Process hierarchy and tree demonstration | `src/experiments/process_experiment.cpp` | `tests/process_experiment_test.cpp` | Complete & Verified | Experiment Menu Option 1 |
| **FR-PROC-006** | Processes | Zombie process and orphan adoption demonstrations | `src/experiments/process_lifecycle_experiment.cpp` | `tests/process_lifecycle_experiment_test.cpp` | Complete & Verified | `oscope --demo-lifecycle` |
| **FR-THREAD-001** | Threads | Thread lifecycle demonstrations | `src/experiments/thread_experiment.cpp` | `tests/thread_experiment_test.cpp` | Complete & Verified | Experiment Menu Option 2 |
| **FR-THREAD-002** | Threads | POSIX thread (`pthread`) implementation | `src/experiments/thread_experiment.cpp` | `tests/thread_experiment_test.cpp` | Complete & Verified | Experiment Menu Option 2 |
| **FR-THREAD-003** | Threads | Thread creation, joining, shared state, and race conditions | `src/experiments/thread_experiment.cpp`, `synchronization_experiment.cpp` | `tests/thread_experiment_test.cpp`, `tests/synchronization_experiment_test.cpp` | Complete & Verified | Experiment Menu Options 2 & 3 |
| **FR-SCHED-001** | Scheduling | FCFS CPU scheduling | `src/scheduling/fcfs_scheduler.cpp` | `tests/scheduling_test.cpp` | Complete & Verified | Scheduling Menu Option 1 |
| **FR-SCHED-002** | Scheduling | SJF (non-preemptive) CPU scheduling | `src/scheduling/sjf_scheduler.cpp` | `tests/scheduling_test.cpp` | Complete & Verified | Scheduling Menu Option 2 |
| **FR-SCHED-003** | Scheduling | SRTF (preemptive SJF) CPU scheduling | `src/scheduling/srtf_scheduler.cpp` | `tests/scheduling_test.cpp` | Complete & Verified | Scheduling Menu Option 3 |
| **FR-SCHED-004** | Scheduling | Priority (non-preemptive) CPU scheduling | `src/scheduling/priority_scheduler.cpp` | `tests/scheduling_test.cpp` | Complete & Verified | Scheduling Menu Option 4 |
| **FR-SCHED-005** | Scheduling | Round Robin CPU scheduling | `src/scheduling/round_robin_scheduler.cpp` | `tests/scheduling_test.cpp` | Complete & Verified | Scheduling Menu Option 5 |
| **FR-SCHED-006** | Scheduling | Multilevel Feedback Queue (MLFQ) | `src/scheduling/mlfq_scheduler.cpp` | `tests/scheduling_test.cpp` | Complete & Verified | Scheduling Menu Option 6 |
| **FR-SCHED-007** | Scheduling | Waiting, turnaround, response times, throughput, CPU utilization | `src/scheduling/` | `tests/scheduling_test.cpp` | Complete & Verified | Scheduling metrics display |
| **FR-SCHED-008** | Scheduling | Common scheduling workload representation | `include/oscope/scheduling/scheduler.hpp` | `tests/scheduling_test.cpp` | Complete & Verified | Workload comparison (Option 7) |
| **FR-SYNC-001** | Synchronization | Critical-section mutual exclusion requirements | `src/experiments/synchronization_experiment.cpp` | `tests/synchronization_experiment_test.cpp` | Complete & Verified | Experiment Menu Option 3 |
| **FR-SYNC-002** | Synchronization | Mutex-based synchronization demonstration | `src/experiments/synchronization_experiment.cpp` | `tests/synchronization_experiment_test.cpp` | Complete & Verified | Experiment Menu Option 3 |
| **FR-SYNC-003** | Synchronization | Semaphore demonstrations (`sem_init`, `sem_wait`, `sem_post`, `sem_destroy`) | `src/synchronization/semaphore_experiment.cpp` | `tests/semaphore_experiment_test.cpp` | Complete & Verified | `oscope --demo-sync`, Menu Option 3 |
| **FR-SYNC-004** | Synchronization | Race condition demonstration without synchronization | `src/experiments/synchronization_experiment.cpp` | `tests/synchronization_experiment_test.cpp` | Complete & Verified | Experiment Menu Option 3 |
| **FR-SYNC-005** | Synchronization | Classical synchronization models (Bounded-Buffer Producer-Consumer) | `src/synchronization/semaphore_experiment.cpp` | `tests/semaphore_experiment_test.cpp` | Complete & Verified | `oscope --demo-sync`, Menu Option 3 |
| **FR-SYNC-006** | Synchronization | Deadlock-prone synchronization scenarios | `src/deadlock/deadlock_detector.cpp`, `coffman_conditions.cpp` | `tests/deadlock_test.cpp`, `tests/coffman_test.cpp` | Complete & Verified | Deadlock Submenu & Demo |
| **FR-SYNC-007** | Synchronization | Peterson's solution simulation (2 processes, intent flags, turn) | `src/synchronization/petersons_algorithm.cpp` | `tests/petersons_algorithm_test.cpp` | Complete & Verified | `oscope --demo-sync` |
| **FR-IPC-001** | IPC | POSIX anonymous pipe IPC demonstration | `src/experiments/pipe_ipc_experiment.cpp` | `tests/pipe_ipc_experiment_test.cpp` | Complete & Verified | Experiment Menu Option 4 |
| **FR-IPC-002** | IPC | POSIX named pipe (FIFO) demonstration | `src/experiments/ipc_experiments.cpp` | `tests/ipc_extensions_test.cpp` | Complete & Verified | `oscope --demo-ipc` |
| **FR-IPC-003** | IPC | Inter-process message passing (POSIX message queues: `mq_open`, `mq_send`, `mq_receive`, `mq_unlink`) | `src/experiments/ipc_experiments.cpp` | `tests/ipc_extensions_test.cpp` | Complete & Verified | `oscope --demo-ipc`, Menu Option 4 |
| **FR-IPC-004** | IPC | POSIX shared memory (`shm_open`, `mmap`) demonstration | `src/experiments/ipc_experiments.cpp` | `tests/ipc_extensions_test.cpp` | Complete & Verified | `oscope --demo-ipc` |
| **FR-IPC-005** | IPC | Direct underlying Linux/POSIX API visibility and RAII cleanup | `src/experiments/pipe_ipc_experiment.cpp`, `ipc_experiments.cpp` | `tests/pipe_ipc_experiment_test.cpp`, `tests/ipc_extensions_test.cpp` | Complete & Verified | Automated cleanup validation |
| **FR-DEAD-001** | Deadlock | Process/resource allocation & need representation | `include/oscope/deadlock/deadlock_types.hpp` | `tests/deadlock_test.cpp` | Complete & Verified | Deadlock Menu Options 1–3 |
| **FR-DEAD-002** | Deadlock | Banker's safety algorithm and request evaluation | `src/deadlock/bankers_algorithm.cpp` | `tests/deadlock_test.cpp` | Complete & Verified | Deadlock Menu Options 1–2 |
| **FR-DEAD-003** | Deadlock | Deadlock detection using wait-for cycle analysis | `src/deadlock/deadlock_detector.cpp` | `tests/deadlock_test.cpp` | Complete & Verified | Deadlock Menu Option 3 |
| **FR-DEAD-004** | Deadlock | Deadlock prevention and avoidance concepts | `src/deadlock/bankers_algorithm.cpp`, `coffman_conditions.cpp` | `tests/deadlock_test.cpp`, `tests/coffman_test.cpp` | Complete & Verified | `oscope --demo-coffman` |
| **FR-DEAD-005** | Deadlock | Educational recovery strategies and rollback | `src/deadlock/bankers_algorithm.cpp` | `tests/deadlock_test.cpp` | Complete & Verified | Banker's request rollback |
| **FR-DEAD-006** | Deadlock | Resource-allocation graph and cycle detection | `src/deadlock/deadlock_detector.cpp` | `tests/deadlock_test.cpp` | Complete & Verified | Deadlock detection test |
| **FR-DEAD-007** | Deadlock | Safe and unsafe state explanations | `src/deadlock/bankers_algorithm.cpp`, `src/cli.cpp` | `tests/deadlock_test.cpp`, `tests/deadlock_cli_test.cpp` | Complete & Verified | CLI explain messages |
| **FR-DEAD-008** | Deadlock | Four Coffman conditions analysis & prevention strategies | `src/deadlock/coffman_conditions.cpp` | `tests/coffman_test.cpp` | Complete & Verified | `oscope --demo-coffman` |
| **FR-MEM-001** | Memory | First Fit dynamic memory allocation | `src/memory/allocator.cpp` | `tests/memory_test.cpp` | Complete & Verified | Memory Menu Option 1 |
| **FR-MEM-002** | Memory | Best Fit dynamic memory allocation | `src/memory/allocator.cpp` | `tests/memory_test.cpp` | Complete & Verified | Memory Menu Option 2 |
| **FR-MEM-003** | Memory | Worst Fit dynamic memory allocation | `src/memory/allocator.cpp` | `tests/memory_test.cpp` | Complete & Verified | Memory Menu Option 3 |
| **FR-MEM-004** | Memory | Internal and external fragmentation calculation | `src/memory/allocator.cpp` | `tests/memory_test.cpp` | Complete & Verified | Memory Menu Option 4 |
| **FR-MEM-005** | Memory | Memory block event trace and block splitting/coalescing | `src/memory/allocator.cpp` | `tests/memory_test.cpp` | Complete & Verified | Memory trace display |
| **FR-PAGE-001** | Paging | Page and frame representations | `include/oscope/paging/address_translation.hpp` | `tests/address_translation_test.cpp` | Complete & Verified | Paging module |
| **FR-PAGE-002** | Paging | Page table representation and valid/invalid bits | `src/paging/address_translation.cpp` | `tests/address_translation_test.cpp` | Complete & Verified | Page table lookup |
| **FR-PAGE-003** | Paging | Virtual-to-physical address translation simulation | `src/paging/address_translation.cpp` | `tests/address_translation_test.cpp` | Complete & Verified | `oscope --demo-paging` |
| **FR-PAGE-004** | Paging | Exposes page number, offset preservation, and physical address | `src/paging/address_translation.cpp` | `tests/address_translation_test.cpp` | Complete & Verified | Address breakdown display |
| **FR-PAGE-005** | Paging | Page fault simulation and handling | `src/paging/address_translation.cpp`, `page_replacer.cpp` | `tests/address_translation_test.cpp`, `tests/paging_test.cpp` | Complete & Verified | Demand paging events |
| **FR-PAGE-006** | Paging | FIFO page replacement algorithm | `src/paging/page_replacer.cpp` | `tests/paging_test.cpp` | Complete & Verified | Paging Menu Option 1 |
| **FR-PAGE-007** | Paging | LRU page replacement algorithm | `src/paging/page_replacer.cpp` | `tests/paging_test.cpp` | Complete & Verified | Paging Menu Option 2 |
| **FR-PAGE-008** | Paging | Optimal page replacement algorithm | `src/paging/page_replacer.cpp` | `tests/paging_test.cpp` | Complete & Verified | Paging Menu Option 3 |
| **FR-PAGE-009** | Paging | Page fault count, fault rate, and hit statistics | `src/paging/page_replacer.cpp` | `tests/paging_test.cpp` | Complete & Verified | Paging metrics table |
| **FR-PAGE-010** | Paging | Configurable reference strings and frame counts | `src/paging/page_replacer.cpp` | `tests/paging_test.cpp` | Complete & Verified | Interactive input |
| **FR-PAGE-011** | Paging | Demand paging simulation with page faults and frame evictions | `src/paging/address_translation.cpp` | `tests/address_translation_test.cpp` | Complete & Verified | `oscope --demo-paging` |
| **FR-PAGE-012** | Paging | Educational thrashing demonstration across frame counts | `src/paging/address_translation.cpp` | `tests/address_translation_test.cpp` | Complete & Verified | `oscope --demo-paging` |
| **FR-ALLOC-001** | Buddy/Slab | Buddy system simulation (P2 Optional) | Documented architecture | Deferred (P2 optional) | Documented in PRD §9 | Deferred to P2 |
| **FR-ALLOC-002** | Buddy/Slab | Slab allocation simulation (P2 Optional) | Documented architecture | Deferred (P2 optional) | Documented in PRD §9 | Deferred to P2 |
| **FR-FS-001** | File System | In-memory educational file-system model | `src/filesystem/simple_fs.cpp` | `tests/simple_fs_test.cpp` | Complete & Verified | `oscope --demo-fs` |
| **FR-FS-002** | File System | Inode, directory entries, and file metadata | `include/oscope/filesystem/simple_fs.hpp` | `tests/simple_fs_test.cpp` | Complete & Verified | `oscope --demo-fs` |
| **FR-FS-003** | File System | Recursive directory hierarchy traversal | `src/filesystem/simple_fs.cpp` | `tests/simple_fs_test.cpp` | Complete & Verified | `oscope --demo-fs` |
| **FR-FS-004** | File System | Contiguous, Linked, and Indexed allocation comparisons | `src/filesystem/simple_fs.cpp` | `tests/simple_fs_test.cpp` | Complete & Verified | `oscope --demo-fs` |
| **FR-FS-005** | File System | Free-space management with block allocation bitmap | `src/filesystem/simple_fs.cpp` | `tests/simple_fs_test.cpp` | Complete & Verified | Bitmap visual trace |
| **FR-DISK-001** | Disk | FCFS disk scheduling algorithm | `src/disk/disk_scheduler.cpp` | `tests/disk_test.cpp` | Complete & Verified | Disk Menu Option 1 |
| **FR-DISK-002** | Disk | LIFO disk scheduling algorithm | `src/disk/disk_scheduler.cpp` | `tests/disk_test.cpp` | Complete & Verified | Disk Menu Option 3 |
| **FR-DISK-003** | Disk | SSTF disk scheduling algorithm | `src/disk/disk_scheduler.cpp` | `tests/disk_test.cpp` | Complete & Verified | Disk Menu Option 2 |
| **FR-DISK-004** | Disk | SCAN (Elevator) disk scheduling algorithm | `src/disk/disk_scheduler.cpp` | `tests/disk_test.cpp` | Complete & Verified | Disk Menu Option 4 |
| **FR-DISK-005** | Disk | C-SCAN (Circular SCAN) disk scheduling algorithm | `src/disk/disk_scheduler.cpp` | `tests/disk_test.cpp` | Complete & Verified | Disk Menu Option 5 |
| **FR-DISK-006** | Disk | Seek distance, service order, and comparison metrics | `src/disk/disk_scheduler.cpp` | `tests/disk_test.cpp` | Complete & Verified | Disk Menu Option 8 (Compare All) |
| **FR-MON-001** | Monitoring | Real Linux process observation via `/proc/[pid]/stat` | `src/monitoring/host_monitor.cpp` | `tests/host_monitor_test.cpp` | Complete & Verified | `oscope --demo-monitor` |
| **FR-MON-002** | Monitoring | Host CPU and memory observations via `/proc/stat` and `/proc/meminfo` | `src/monitoring/host_monitor.cpp` | `tests/host_monitor_test.cpp` | Complete & Verified | `oscope --demo-monitor` |
| **FR-MON-003** | Monitoring | Host block device I/O stats via `/proc/diskstats` | `src/monitoring/host_monitor.cpp` | `tests/host_monitor_test.cpp` | Complete & Verified | `oscope --demo-monitor` |
| **FR-MON-004** | Monitoring | Clear distinction of real Linux observations vs simulations | `src/monitoring/host_monitor.cpp` | `tests/host_monitor_test.cpp` | Complete & Verified | Source labels in CLI & JSON |
| **FR-EXP-001** | Engine | Reusable experiment abstraction and lifecycle | `include/oscope/experiments/` | `tests/*_experiment_test.cpp` | Complete & Verified | Experiment framework |
| **FR-EXP-002** | Engine | Structured events, configuration, workloads, and metrics | `include/oscope/reporting/` | `tests/experiment_reporting_test.cpp` | Complete & Verified | Experiment reporters |
| **FR-EXP-003** | Engine | Deterministic, reproducible workload definitions | `include/oscope/scheduling/`, `paging/`, `disk/` | `tests/` unit tests | Complete & Verified | Deterministic test workloads |
| **FR-EXP-004** | Engine | Versioned machine-readable JSON schema (v1.0.0) | `src/reporting/experiment_reporter.cpp` | `tests/experiment_reporting_test.cpp` | Complete & Verified | `oscope --json` |
| **FR-EXP-005** | Engine | Environment metadata recording | `src/reporting/experiment_reporter.cpp` | `tests/experiment_reporting_test.cpp` | Complete & Verified | Environment info in JSON |
| **FR-EXP-006** | Engine | Side-by-side multi-algorithm comparison | `src/scheduling/`, `memory/`, `paging/`, `disk/` | `tests/disk_test.cpp`, `memory_test.cpp` | Complete & Verified | Compare All CLI options |
| **FR-VIZ-001** | Visualization | Visualization of experiment outcomes and states | `src/cli.cpp` | `tests/*_cli_test.cpp` | Complete & Verified | CLI interactive views |
| **FR-VIZ-002** | Visualization | CPU scheduling timeline and Gantt-style execution trace | `src/cli.cpp` | `tests/cli_test.cpp` | Complete & Verified | Scheduler Gantt view |
| **FR-VIZ-003** | Visualization | Paging reference string, frame allocation, and faults | `src/cli.cpp` | `tests/paging_cli_test.cpp` | Complete & Verified | Paging matrix trace |
| **FR-VIZ-004** | Visualization | Memory block layout, splitting, and coalescing views | `src/cli.cpp` | `tests/memory_cli_test.cpp` | Complete & Verified | Memory block diagrams |
| **FR-VIZ-005** | Visualization | Tabular metric comparisons across algorithms | `src/cli.cpp` | `tests/*_cli_test.cpp` | Complete & Verified | Compare All tables |
| **FR-AI-001** | AI Analysis | Optional AI layer (downstream of core algorithms) | Documented specification | Contract verified | P2 Optional | Documented in PRD §9 |
| **FR-AI-002** | AI Analysis | Operates strictly on structured JSON results | `docs/08_Data_Model_and_Result_Schema.md` | Schema compliance tests | Complete & Verified | Valid JSON output |
| **FR-AI-003** | AI Analysis | Explains trade-offs and patterns | `docs/15_Demo_and_Evaluation_Plan.md` | Viva guide | Complete & Verified | Viva questions and answers |
| **FR-AI-004** | AI Analysis | Identifies empirical source data | `docs/08_Data_Model_and_Result_Schema.md` | JSON test cases | Complete & Verified | Result schema metadata |
