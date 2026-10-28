# OScope — Demo and Evaluation Plan

## 1. Demonstration Goal

The final demonstration shows the complete OScope philosophy: an integrated, observable platform bridging pure operating systems concepts with hands-on Linux system programming experiments.

---

## 2. Command-Line Demonstration Workflows

### Master Command: Run All Demos
To run an automated, end-to-end demonstration of all core OScope subsystems:

```bash
./build/oscope --demo-all
```

To output the exact experiment telemetry across all modules as machine-readable JSON (Schema v1.0.0):

```bash
./build/oscope --demo-all --json | python3 -m json.tool
```

---

### Focused Subsystem Demonstrations

#### Demo 1: Virtual Address Translation, Demand Paging & Thrashing
```bash
./build/oscope --demo-paging
```
- **Demonstration:**
  - Translates virtual address `0x2050` with 4 KB page size to physical address `0x7050` (Page 2 -> Frame 7, Offset 0x50).
  - Traces demand paging under page faults and evictions.
  - Generates the thrashing curve (page fault rate vs. allocated frame count) showing how inadequate physical frames lead to thrashing.

#### Demo 2: Thread Synchronization (Peterson's, POSIX Semaphores, Producer-Consumer)
```bash
./build/oscope --demo-sync
```
- **Demonstration:**
  - Simulates Process 0 and Process 1 competing for Critical Sections via Peterson's algorithm.
  - Illustrates the `flag[i] = true` intent declaration and `turn = j` yield mechanism, verifying mutual exclusion.
  - POSIX Semaphores: validates unnamed semaphores (`sem_init`, `sem_wait`, `sem_post`, `sem_destroy`) coordinating multi-threaded increments without data races.
  - Classical Producer-Consumer: executes bounded-buffer problem with counting semaphores (`empty_slots`, `occupied_slots`) and mutex, proving 100% item preservation and zero loss or duplication.

#### Demo 3: Coffman Deadlock Conditions & Prevention Strategies
```bash
./build/oscope --demo-coffman
```
- **Demonstration:**
  - Evaluates the four Coffman conditions: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait.
  - Demonstrates how breaking any single condition (e.g., resource ordering or preemption) prevents deadlocks.

#### Demo 4: Real Linux Host Resource Monitoring
```bash
./build/oscope --demo-monitor
```
- **Demonstration:**
  - Reads live system observations from `/proc/stat` (CPU usage breakdown: user, system, idle).
  - Reads live system memory metrics from `/proc/meminfo` (Total, Used, Available RAM).
  - Reads self-process statistics from `/proc/self/stat` (PID, state, user/system ticks, RSS, virtual memory).
  - Inspects `/proc/diskstats` for host block device reads/writes.
  - Clearly labels all data as real host measurements rather than simulated figures.

#### Demo 5: Educational File System Simulation
```bash
./build/oscope --demo-fs
```
- **Demonstration:**
  - Initializes a 32-block file system with 512-byte blocks.
  - Recursively traverses and renders directory hierarchy (`/home/docs/`).
  - Compares Contiguous, Linked, and Indexed block allocation strategies.
  - Displays the 32-bit free-space allocation bitmap (`11111111 00000000 ...`).

#### Demo 6: Linux POSIX IPC Extensions (FIFO, Shared Memory & Message Queues)
```bash
./build/oscope --demo-ipc
```
- **Demonstration:**
  - POSIX Named Pipe (FIFO): creates `/tmp/oscope_fifo_*`, forks reader and writer processes, validates byte-for-byte transmission, and verifies filesystem node unlinking.
  - POSIX Shared Memory: allocates segment with `shm_open`, maps via `mmap()`, exchanges payloads across parent/child, and verifies unmapping and `shm_unlink()`.
  - POSIX Message Queue: establishes `/oscope_mq_*` via `mq_open()`, transfers priority-tagged payloads via `mq_send()` and `mq_timedreceive()`, and verifies `mq_close()` and `mq_unlink()` cleanup.

#### Demo 7: Linux Process Lifecycle (Exec, Zombie & Orphan Demonstrations)
```bash
./build/oscope --demo-lifecycle
```
- **Demonstration:**
  - Process Image Replacement: forks child process that replaces its memory image via `execv()`/`execvp()`, parent captures stdout and validates termination status 0 via `waitpid()`.
  - Zombie: Child exits while parent pauses; observes child in state `'Z'` in `/proc/[pid]/stat`; parent reaps child via `waitpid()`, releasing its PCB entry.
  - Orphan: Child is spawned by intermediate process; intermediate process terminates; child is reparented to `init` (PID 1) or systemd subreaper.

#### Demo 8: Disk Scheduling Algorithms Benchmark Comparison
```bash
./build/oscope --demo-disk
```
- **Demonstration:**
  - Evaluates all seven disk scheduling algorithms (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK, LIFO) on the standard textbook workload ($53$, range $[0, 199]$, direction Up, requests $[98, 183, 37, 122, 14, 124, 65, 67]$).
  - Validates exact head movement metrics: FCFS ($640$), SSTF ($236$), SCAN ($345$), C-SCAN ($382$), LOOK ($299$), C-LOOK ($322$), LIFO ($609$).
  - Illustrates SCAN full boundary-to-boundary sweep ($199 \to 0$, $345$ cylinders) versus LOOK request-reversal ($183 \to 14$, $299$ cylinders).

---

### Interactive Submenu Demonstrations

Users can also launch interactive submenus via `./build/oscope`:
1. **CPU Scheduling:** FCFS, SJF, SRTF, Priority, Round Robin, MLFQ, and comparative metrics.
2. **Paging:** FIFO, LRU, Optimal page replacement with hit/fault rates and frame matrices.
3. **Deadlock Management:** Banker's safety check, resource-request evaluation, and cycle detection.
4. **Dynamic Memory Allocation:** First Fit, Best Fit, Worst Fit with block splitting, coalescing, and internal/external fragmentation tracking.
5. **Disk Scheduling:** FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK with head movement metrics.
6. **Linux Experiments:** Process creation, POSIX threads, mutex synchronization, and pipe IPC.

---

## 3. Evaluation Viva Preparation

### 1. Why are simulation modules and Linux experiments kept strictly separated?
Simulations model algorithmic policies deterministically in logical/virtual time (e.g., simulating CPU scheduling or page replacement algorithms over artificial workloads). Linux experiments interact directly with the real Linux kernel and WSL environment using POSIX system calls (`fork`, `pthread_create`, `pipe`, `shm_open`, `waitpid`) in real elapsed wall-clock time. Blurring the two creates confusion between conceptual algorithms and real OS kernel implementations.

### 2. Why does the CPU scheduler not replace the Linux OS scheduler?
Replacing the Linux scheduler requires building an in-kernel scheduling class or eBPF scheduler (`sched_ext`). OScope's CPU scheduler is an educational discrete-event simulation designed to explore and compare how algorithms (FCFS, SJF, SRTF, Priority, RR, MLFQ) behave on reproducible workloads, generating Gantt charts and exact metrics (waiting, turnaround, response times) without risking kernel panics or thread instability.

### 3. How are scheduling and memory metrics derived?
- **Turnaround Time ($TAT$):** $Completion\_Time - Arrival\_Time$.
- **Waiting Time ($WT$):** $Turnaround\_Time - Burst\_Time$.
- **Response Time ($RT$):** $First\_Dispatch\_Time - Arrival\_Time$.
- **Internal Fragmentation:** Difference between allocated block capacity and process request size.
- **External Fragmentation:** Total unallocated free memory that cannot be utilized because free blocks are contiguous or fragmented across disparate locations.

### 4. How are low-level POSIX resources safely managed and cleaned up?
OScope enforces strict RAII (Resource Acquisition Is Initialization) and explicit error-path cleanup:
- File descriptors are closed using `::close()` or RAII handle wrappers.
- Named pipes (FIFOs) are unlinked using `::unlink(path)`.
- Shared memory segments are unmapped using `::munmap()` and removed from `/dev/shm` using `::shm_unlink()`.
- Processes spawned in tests/experiments are always joined or reaped using `::waitpid(pid, &status, 0)` with bounded timeouts to prevent runaway zombies or test hangs.

### 5. Why does Peterson's Algorithm require assumptions on modern hardware?
Peterson's Algorithm was designed for two processes under the assumption of **Sequential Consistency** and atomic memory access. On modern x86-64 and ARM superscalar processors with store buffers and out-of-order execution, memory writes to `flag` and `turn` can be reordered by the CPU or compiler. In real systems, memory barriers (`std::atomic_thread_fence`, `mfence`) or `std::atomic<bool>` with `memory_order_seq_cst` are strictly required to ensure correctness.

### 6. How does virtual address translation preserve page offset?
Given a virtual address $VA$ and page size $P = 2^k$:
- Page Number $PN = \lfloor VA / P \rfloor$ (or $VA \gg k$).
- Page Offset $Offset = VA \pmod P$ (or $VA \ \& \ (P - 1)$).
During translation, the page table maps $PN \to Frame\ Number\ (FN)$. The physical address is constructed as $PA = (FN \times P) + Offset$. The offset within the physical frame is identically preserved.

### 7. Why is Optimal (OPT/Belady's) page replacement primarily a benchmark?
Optimal page replacement evicts the page that will not be accessed for the longest time in the future. Because an operating system in general cannot predict future page accesses, Optimal cannot be implemented in general-purpose virtual memory management. It serves as an upper-bound theoretical benchmark against which practical heuristics (LRU, Clock, FIFO) are evaluated.

### 8. What distinguishes a safe state from a deadlocked or unsafe state in Banker's Algorithm?
A state is **safe** if there exists at least one sequence $\langle P_1, P_2, \dots, P_n \rangle$ of all processes such that each process $P_i$ can satisfy its maximum remaining resource need using currently available resources plus the resources held by all preceding processes $P_j$ ($j < i$). An **unsafe** state is not necessarily deadlocked, but it has the potential to transition into deadlock if processes claim their maximum declared demands. A **deadlocked** state is an unsafe state where no progress is possible.

### 9. How do pipes, FIFOs, and shared memory differ?
- **Anonymous Pipes (`pipe`):** Unidirectional, byte-stream IPC mechanism limited to processes sharing a common parent/ancestor. Represented as ephemeral kernel buffer descriptors with no filesystem directory entry.
- **FIFOs (Named Pipes, `mkfifo`):** Unidirectional or bidirectional byte-stream IPC that exists as a named special file node in the filesystem, allowing unrelated processes to communicate.
- **Shared Memory (`shm_open`, `mmap`):** Highest-speed IPC mechanism where a memory region is mapped directly into the address spaces of multiple processes. Data exchange occurs without copying data through kernel space, requiring explicit synchronization (mutexes/semaphores).
