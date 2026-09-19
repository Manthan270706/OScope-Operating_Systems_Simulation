# OScope — Implementation Plan

## 1. Guiding Rule

Do not implement features in random syllabus order. Build the reusable infrastructure first, then implement modules through increasing OS complexity.

## 2. Phase 1 — Repository and Tooling

- initialize Git repository;
- configure CMake;
- establish C++ standard;
- create directory structure;
- configure compiler warnings;
- configure tests;
- add formatting/static-analysis conventions;
- create CI build/test workflow.

## 3. Phase 2 — Core Types and Utilities

Implement:

- result/status types;
- validation utilities;
- common IDs;
- event model;
- metric model;
- workload model;
- experiment metadata;
- JSON serialization;
- logging.

## 4. Phase 3 — Scheduling

Implement in order:

1. FCFS
2. SJF
3. SRTF
4. Priority
5. Round Robin
6. MLFQ

After each algorithm:

- unit tests;
- common metrics;
- trace generation;
- comparison against known examples.

## 5. Phase 4 — Memory and Paging

Implement:

1. First Fit
2. Best Fit
3. Worst Fit
4. fragmentation metrics
5. page-table model
6. address translation
7. FIFO
8. LRU
9. Optimal
10. demand paging
11. thrashing demonstration

## 6. Phase 5 — Deadlock and Disk

Implement:

- resource model;
- Coffman-condition demonstration;
- Banker's algorithm;
- deadlock detection;
- educational recovery;
- FCFS disk;
- LIFO;
- SSTF;
- SCAN;
- C-SCAN.

## 7. Phase 6 — Linux Experiments

Implement controlled demonstrations for:

- process creation;
- exec;
- wait;
- zombie/orphan;
- process tree;
- pthreads;
- mutex/semaphore;
- Peterson simulation;
- pipes;
- FIFOs;
- message queues;
- shared memory.

## 8. Phase 7 — Experiment Engine

Integrate:

- workload definitions;
- execution;
- event collection;
- metrics;
- result schema;
- environment metadata;
- result storage.

## 9. Phase 8 — Shell and Platform

Implement the educational shell and command routing.

Add:

- help;
- validation;
- module commands;
- experiment commands;
- optional host command execution.

## 10. Phase 9 — Visualization

Create Python tools for:

- scheduling timelines;
- paging frame diagrams;
- memory blocks;
- deadlock/resource graphs;
- disk head movement;
- experiment comparison.

## 11. Phase 10 — Advanced Features

Only after the core is stable:

- Buddy simulation;
- Slab simulation;
- advanced analytics;
- AI analysis.

## 12. Phase 11 — Final Validation

- complete traceability;
- run full test suite;
- reproduce representative experiments;
- benchmark;
- fix defects;
- finalize README;
- prepare final report/demo.
