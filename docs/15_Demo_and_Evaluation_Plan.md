# OScope — Demo and Evaluation Plan

## 1. Demonstration Goal

The final demonstration should show the complete OScope philosophy rather than a collection of disconnected commands.

## 2. Recommended Demo Flow

### Demo 1 — Scheduling

1. Define a workload.
2. Run FCFS.
3. Run Round Robin.
4. Show execution traces.
5. Compare waiting/turnaround/response metrics.
6. Explain why results differ.

### Demo 2 — Paging

1. Enter a reference string.
2. Run FIFO.
3. Run LRU.
4. Run Optimal.
5. Show frame state after each access.
6. Compare page faults.

### Demo 3 — Deadlock

1. Define resources.
2. Run Banker's algorithm.
3. Show safe/unsafe result.
4. Display safe sequence where applicable.
5. Demonstrate Coffman conditions conceptually.

### Demo 4 — Real Linux Experiment

1. Run a fork/exec/wait demonstration.
2. Show process IDs.
3. Run a pthread demonstration.
4. Demonstrate one IPC mechanism.
5. Explain resource cleanup.

### Demo 5 — Experiment Engine

1. Run the same workload through multiple algorithms.
2. Save structured results.
3. Generate a comparison visualization.
4. Explain reproducibility metadata.

### Demo 6 — Monitoring

1. Run a controlled workload.
2. Observe host CPU/memory/process information.
3. Clearly distinguish these measurements from simulated metrics.

## 3. Evaluation Dimensions

- OS concept correctness;
- implementation correctness;
- Linux/POSIX understanding;
- measurement quality;
- reproducibility;
- code quality;
- testing;
- documentation;
- ability to explain trade-offs.

## 4. Viva Preparation

Be able to explain:

- why simulation and Linux experiments are separated;
- why the scheduler does not replace the Linux scheduler;
- how metrics are derived;
- how resources are cleaned up;
- why Peterson's solution has assumptions;
- how page translation works;
- why Optimal page replacement is mainly an educational benchmark;
- what makes a deadlock state safe;
- how pipes/FIFOs/message queues/shared memory differ;
- why Linux monitoring is different from simulation.
