# OScope — Requirements Traceability Matrix

| Requirement Area | Primary Requirement IDs | Design | Test |
|---|---|---|---|
| Shell | FR-SHELL-001–004 | TDD §Shell, Architecture | CLI integration tests |
| Processes | FR-PROC-001–006 | TDD Linux Process | Linux system tests |
| Threads | FR-THREAD-001–003 | TDD Linux Threads | Linux system tests |
| Scheduling | FR-SCHED-001–008 | TDD Scheduling | Unit + integration |
| Synchronization | FR-SYNC-001–007 | TDD Linux/Sync | Unit + system |
| IPC | FR-IPC-001–005 | TDD IPC | Linux system tests |
| Deadlock | FR-DEAD-001–008 | TDD Deadlock | Unit + integration |
| Memory | FR-MEM-001–005 | TDD Memory | Unit tests |
| Paging | FR-PAGE-001–012 | TDD Paging | Unit + integration |
| Buddy/Slab | FR-ALLOC-001–002 | Architecture | Module tests |
| File System | FR-FS-001–005 | Architecture | Integration |
| Disk | FR-DISK-001–006 | TDD Disk | Unit tests |
| Monitoring | FR-MON-001–004 | Linux Monitoring | System tests |
| Experiment Engine | FR-EXP-001–006 | TDD Experiment | Integration |
| Visualization | FR-VIZ-001–005 | Visualization boundary | Output checks |
| AI | FR-AI-001–004 | AI adapter | Contract tests |

## Verification Rule

No requirement should be marked complete without implementation evidence and an appropriate test or documented demonstration.
