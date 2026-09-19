# OScope — Risk Register

| ID | Risk | Impact | Mitigation | Status |
|---|---|---|---|---|
| R-001 | Scope expansion | High | Tiered scope and milestone gates | Open |
| R-002 | Simulation confused with Linux behavior | High | Explicit architectural boundary and mode field | Controlled |
| R-003 | Resource leaks | High | RAII and cleanup tests | Open |
| R-004 | Timing-sensitive experiments vary | Medium | Record environment and use qualitative interpretation | Open |
| R-005 | Linux-specific incompatibility | Medium | Define supported environment | Open |
| R-006 | AI distracts from OS implementation | Medium | AI is P2 and downstream | Controlled |
| R-007 | Weak edge-case testing | High | Dedicated test strategy | Open |
| R-008 | Documentation drift | Medium | Stable IDs and traceability | Open |
| R-009 | Build complexity | Medium | CMake and staged integration | Open |
| R-010 | Unsafe host command execution | High | Explicit command boundary and no implicit shell interpolation | Controlled |
