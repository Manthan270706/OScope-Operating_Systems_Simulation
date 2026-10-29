# OScope — Implementation Plan

## 1. Guiding Rule

Do not implement features in random syllabus order. Build the reusable infrastructure first, then implement modules through increasing OS complexity.

---

## 2. Phase 1 — Repository and Tooling [COMPLETED]

- [x] initialize Git repository;
- [x] configure CMake;
- [x] establish C++17 standard;
- [x] create directory structure;
- [x] configure compiler warnings (`-Wall -Wextra -Wpedantic`);
- [x] configure GoogleTest unit/integration testing suite;
- [x] add formatting/static-analysis conventions;
- [x] create CI build/test workflow.

---

## 3. Phase 2 — Core Types and Utilities [COMPLETED]

Implemented:
- [x] result/status types;
- [x] validation utilities;
- [x] common IDs;
- [x] event model;
- [x] metric model;
- [x] workload model;
- [x] experiment metadata;
- [x] JSON serialization (v1.0.0);
- [x] logging.

---

## 4. Phase 3 — Scheduling [COMPLETED]

Implemented:
- [x] 1. FCFS
- [x] 2. SJF (non-preemptive)
- [x] 3. SRTF (preemptive SJF)
- [x] 4. Priority (non-preemptive)
- [x] 5. Round Robin
- [x] 6. MLFQ (Multilevel Feedback Queue)

Features:
- [x] unit tests;
- [x] common metrics (waiting time, turnaround time, response time, CPU utilization);
- [x] trace generation;
- [x] comparison against known benchmark examples.

---

## 5. Phase 4 — Memory and Paging [COMPLETED]

Implemented:
- [x] 1. First Fit
- [x] 2. Best Fit
- [x] 3. Worst Fit
- [x] 4. fragmentation metrics (internal and external)
- [x] 5. page-table model
- [x] 6. virtual-to-physical address translation
- [x] 7. FIFO page replacement
- [x] 8. LRU page replacement
- [x] 9. Optimal page replacement
- [x] 10. demand paging simulation
- [x] 11. thrashing demonstration across frame counts

---

## 6. Phase 5 — Deadlock and Disk [COMPLETED]

Implemented:
- [x] resource allocation and need matrices;
- [x] Coffman-condition demonstration;
- [x] Banker's safety algorithm;
- [x] Banker's resource-request algorithm with rollback;
- [x] deadlock detection (wait-for cycle analysis);
- [x] FCFS disk scheduling;
- [x] LIFO disk scheduling;
- [x] SSTF disk scheduling;
- [x] SCAN disk scheduling;
- [x] C-SCAN disk scheduling;
- [x] LOOK and C-LOOK disk scheduling;
- [x] side-by-side comparative disk benchmark.

---

## 7. Phase 6 — Linux Experiments [COMPLETED]

Implemented controlled demonstrations for:
- [x] process creation with `fork()`, `exec*()`, `waitpid()`;
- [x] zombie process generation and parent reaping;
- [x] orphan process adoption by `init`/systemd;
- [x] POSIX threads (`pthread_create`, `pthread_join`);
- [x] mutex synchronization and race conditions;
- [x] Peterson's algorithm simulation;
- [x] POSIX anonymous pipes;
- [x] POSIX named pipes (FIFOs);
- [x] POSIX shared memory (`shm_open`, `mmap`, `shm_unlink`);
- [x] explicit RAII cleanup and resource verification.

---

## 8. Phase 7 — Experiment Engine & Reporting [COMPLETED]

Integrated:
- [x] workload definitions;
- [x] execution lifecycles;
- [x] event collection;
- [x] metrics models;
- [x] structured result schema (v1.0.0);
- [x] environment metadata;
- [x] RFC 8259-compliant JSON serialization across all modules.

---

## 9. Phase 8 — Shell and Platform [COMPLETED]

Implemented the educational shell, submenus, and command routing:
- [x] help and usage descriptions;
- [x] robust input validation and EOF handling;
- [x] interactive module submenus (CPU scheduling, memory, paging, deadlock, disk, POSIX experiments);
- [x] direct demonstration flags (`--demo-all`, `--demo-paging`, `--demo-sync`, `--demo-coffman`, `--demo-monitor`, `--demo-fs`, `--demo-ipc`, `--demo-lifecycle`);
- [x] host monitoring integration (`/proc/stat`, `/proc/meminfo`, `/proc/[pid]/stat`, `/proc/diskstats`);
- [x] educational in-memory filesystem simulation (`SimpleFileSystem`).

---

## 10. Phase 9 — Visualization [COMPLETED]

Terminal-based visualizations implemented directly:
- [x] scheduling timeline / Gantt chart view;
- [x] paging frame access histories and fault traces;
- [x] memory block layout, splitting, and coalescing views;
- [x] free space block bitmaps;
- [x] tabular multi-algorithm comparison tables.

---

## 11. Phase 10 — Advanced Features [ASSESSED / P2 OPTIONAL]

Assessed per approved PRD §9 priorities:
- Buddy and Slab memory allocators: P2 optional.
- AI analysis layer: P2 optional, downstream consumer of structured JSON schema (schema v1.0.0 is verified compliant).

---

## 12. Phase 11 — Final Validation [COMPLETED]

- [x] complete bidirectional requirements traceability matrix (`11_Traceability_Matrix.md`);
- [x] POSIX semaphores and Producer-Consumer bounded-buffer classical synchronization (`FR-SYNC-003`, `FR-SYNC-005`);
- [x] POSIX message queues inter-process communication (`FR-IPC-003`);
- [x] Process `exec*()` image replacement demonstration (`FR-PROC-004`);
- [x] run full CTest regression suite: **356/356 tests passed (100%)**;
- [x] verified clean build under `-Wall -Wextra -Wpedantic`;
- [x] end-to-end JSON CLI verification with `python3 -m json.tool` across `--demo-all`, `--demo-sync`, `--demo-ipc`, `--demo-lifecycle`, and `--demo-disk`;
- [x] verified SCAN boundary benchmark behavior: head 53, range [0, 199], movement 345, final head 0;
- [x] finalized comprehensive documentation index and viva guide.
