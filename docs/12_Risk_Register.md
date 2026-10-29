# OScope — Risk Register

| ID | Risk | Impact | Mitigation | Status |
|---|---|---|---|---|
| R-001 | Scope expansion | High | Strict adherence to PRD §9 priorities; P0/P1 completed, P2 optional isolated. | Mitigated |
| R-002 | Simulation confused with Linux behavior | High | Explicit architectural separation; mode fields in JSON and distinct CLI demo sections. | Resolved |
| R-003 | Resource leaks in Linux experiments | High | Comprehensive RAII wrappers, explicit `unlink`, `shm_unlink`, `munmap`, `waitpid`, and automated resource-safety tests. | Resolved |
| R-004 | Timing-sensitive experiments vary | Medium | Deterministic unit tests with bounded waits, synchronization pipes, and invariant assertions instead of arbitrary sleeps. | Resolved |
| R-005 | Linux-specific incompatibility | Medium | WSL Ubuntu C++17 standardized, `/proc` parsers validate file existence and handle errors gracefully. | Mitigated |
| R-006 | AI distracts from OS implementation | Medium | AI decoupled downstream of core algorithms and JSON schema v1.0.0. Core OS modules 100% verified first. | Mitigated |
| R-007 | Weak edge-case testing | High | 340 automated GoogleTests covering empty inputs, boundary values, zero bursts, full disks, unmapped pages, and cycle detection. | Resolved |
| R-008 | Documentation drift | Medium | Full bidirectional traceability matrix (`11_Traceability_Matrix.md`), API specs, and JSON schemas updated to match code. | Resolved |
| R-009 | Build complexity | Medium | Modular CMake target configuration (`oscope_core`, `oscope`, `oscope_tests`) with strict compiler warnings. | Resolved |
| R-010 | Unsafe host command execution | High | Educational shell strictly sandboxes simulation and experiment commands; no arbitrary unverified shell execution. | Resolved |
