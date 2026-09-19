# OScope — Test Strategy

## 1. Testing Objectives

Testing must establish:

- algorithmic correctness;
- edge-case correctness;
- interface correctness;
- reproducibility;
- Linux experiment behavior;
- resource cleanup.

## 2. Test Pyramid

```text
             System Tests
           /              \
      Integration Tests
     /                    \
           Unit Tests
```

Most algorithmic logic should be covered by unit tests.

## 3. Unit Test Areas

### Scheduling
- FCFS;
- SJF;
- SRTF;
- Priority;
- RR;
- MLFQ;
- arrival-time edge cases;
- equal priorities;
- zero/large quantum handling.

### Paging
- FIFO;
- LRU;
- Optimal;
- empty reference string;
- one frame;
- repeated references;
- all references fitting in memory.

### Memory
- First Fit;
- Best Fit;
- Worst Fit;
- exact-fit allocation;
- failed allocation;
- deallocation;
- fragmentation.

### Deadlock
- safe state;
- unsafe state;
- no available resources;
- single-resource edge cases.

### Disk
- empty queue;
- one request;
- duplicate requests;
- head at request position;
- boundary movement.

## 4. Integration Tests

- command parsing → module execution;
- module → result serialization;
- experiment → metrics;
- result → visualization input.

## 5. Linux System Tests

Test controlled demonstrations of:

- fork;
- exec;
- wait;
- zombie;
- orphan;
- pthread;
- pipe;
- FIFO;
- message queue;
- shared memory;
- synchronization.

Tests must avoid leaving orphaned resources or processes.

## 6. Resource Leak Checks

Use appropriate Linux tooling during development, such as:

- sanitizers for C/C++ memory errors;
- descriptor checks;
- process inspection;
- manual cleanup verification.

## 7. Regression Testing

Every fixed defect should receive a regression test where practical.

## 8. Test Evidence

For major modules, retain:

- command used;
- input;
- expected result;
- actual result;
- pass/fail;
- environment where relevant.

## 9. Acceptance Gate

A module is release-ready only when:

- tests pass;
- known edge cases are covered;
- resources are cleaned;
- documentation is complete;
- reproducibility has been demonstrated where applicable.
