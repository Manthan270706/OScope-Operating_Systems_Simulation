# OScope: Operating Systems Concepts & Viva Preparation Guide

This guide details all operating system concepts, algorithms, formulas, and trade-offs implemented in **OScope — Operating Systems Simulation & Experimentation Laboratory**. It is structured for course review, lab evaluations, and technical interviews.

---

## 1. CPU Scheduling

### The Problem
The CPU is the primary computational resource in a system. When multiple processes reside in the Ready Queue, the OS **CPU Scheduler (Short-Term Scheduler)** decides which process receives the CPU next, aiming to maximize throughput and minimize waiting time.

### Fundamental Metrics
* **Arrival Time ($AT$)**: Timestamp when a process enters the Ready Queue.
* **Burst Time ($BT$)**: CPU execution time required to complete the task.
* **Completion Time ($CT$)**: Timestamp when the process finishes execution.
* **Turnaround Time ($TAT$)**: Total elapsed lifespan of the process in the system:
  $$\text{TAT} = CT - AT$$
* **Waiting Time ($WT$)**: Total time spent waiting inside the Ready Queue:
  $$\text{WT} = \text{TAT} - BT$$
* **Response Time ($RT$)**: Time elapsed from arrival until the process obtains CPU execution for the very first time.

### Algorithms Implemented
| Algorithm | Type | Decision Logic | Tradeoffs / Pitfalls |
| :--- | :--- | :--- | :--- |
| **FCFS** (First-Come, First-Served) | Non-Preemptive | Executes processes in order of arrival time ($AT$). | **Convoy Effect**: Short I/O-bound jobs get blocked behind a long CPU-bound job, degrading average waiting time. |
| **SJF** (Shortest Job First) | Non-Preemptive | Selects the process with the smallest burst time ($BT$). | Provably optimal for minimizing average waiting time among non-preemptive schedulers. Difficult to predict actual burst time in advance. |
| **SRTF** (Shortest Remaining Time First) | Preemptive | Preempts the running job if a newly arrived job has a smaller remaining burst time. | Minimizes average turnaround time, but causes **Starvation** for long jobs if short jobs arrive continuously. |
| **Round Robin (RR)** | Preemptive | Assigns each process a fixed slice of time (**Time Quantum $q$**). When $q$ expires, the process is moved to the tail of the queue. | Bound response time to $(n-1) \times q$. If $q$ is too small, context-switch overhead dominates; if $q$ is too large, it degenerates into FCFS. |
| **Priority Scheduling** | Preemptive / Non-Preemptive | Dispatches the job with highest priority (lower integer = higher priority in OScope). | Suffers from **Starvation**. Mitigated via **Aging**: progressively increasing a process's priority the longer it waits in queue. |
| **MLFQ** (Multilevel Feedback Queue) | Dynamic Preemptive | Multiple queues with descending priority and ascending time quantums. Jobs move down queues as they consume CPU time. | Approximates SJF dynamically without needing prior knowledge of burst times. Promotes interactive I/O jobs and demotes CPU hogs. |

---

## 2. Dynamic Memory Allocation

### The Problem
During execution, processes dynamically request contiguous variable-size blocks of physical RAM (`malloc` / `free`). When processes terminate, holes of free memory are scattered across physical address space.

### Partitioning Strategies
1. **First-Fit**:
   - Searches the free list sequentially from index 0 and allocates the **first available hole** that is large enough ($\text{Hole Size} \ge \text{Requested Size}$).
   - *Advantage*: Fast allocation; low computational overhead.
2. **Best-Fit**:
   - Scans the entire list to find the **smallest available hole** that satisfies the request.
   - *Disadvantage*: Leaves behind tiny, unusable slivers of free space.
3. **Worst-Fit**:
   - Scans the entire list and allocates from the **largest available hole**.
   - *Rationale*: Leaves behind a remaining partition large enough to be allocated to subsequent processes.

### Fragmentation & Coalescing
* **Internal Fragmentation**: Space wasted *inside* an allocated block when memory is provided in fixed chunk granularities larger than requested.
* **External Fragmentation**: Total free memory across the system is sufficient to satisfy an incoming request, but it is divided into non-contiguous fragments.
* **Block Coalescing**: When block $B_k$ is freed, the allocator inspects neighbors $B_{k-1}$ and $B_{k+1}$. If either is also free, it merges them into a single contiguous block to counter external fragmentation.

---

## 3. Virtual Memory & Page Replacement

### The Problem
Physical RAM is smaller than the combined virtual address spaces of all running programs. Through **Demand Paging**, the operating system loads virtual pages into physical frames only when referenced. When RAM is full and a new page is referenced, a **victim page** must be evicted.

### Core Concepts
* **Virtual Page**: Fixed-size unit of logical memory (e.g., 4 KB).
* **Physical Frame**: Fixed-size slot in physical RAM matching the page size.
* **Page Fault**: Occurs when a referenced page is not present in physical RAM (valid-invalid bit is 0). The kernel traps to disk storage to retrieve the page.
* **Hit Ratio**:
  $$\text{Hit Ratio} = \frac{\text{Page Hits}}{\text{Total References}} \times 100\%$$

### Page Replacement Algorithms
1. **FIFO (First-In, First-Out)**:
   - Evicts the oldest page brought into memory.
   - **Belady’s Anomaly**: For specific reference strings (e.g., `1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5`), allocating *more* physical frame slots (from 3 to 4) results in *more* page faults (increasing from 9 to 10).
2. **LRU (Least Recently Used)**:
   - Evicts the page that has not been accessed for the longest duration in the past.
   - Immune to Belady's Anomaly because it satisfies the **Stack Property** (the set of pages in an $n$-frame memory is always a subset of pages in an $(n+1)$-frame memory).
3. **Optimal (OPT / Belady's Min)**:
   - Evicts the page that will not be referenced for the longest duration in the *future*.
   - Serves as the theoretical benchmark for algorithmic efficiency (unimplementable in production general-purpose OS kernels without future knowledge).

---

## 4. Deadlock Management & Banker's Algorithm

### Deadlock Definition
A permanent blocking state where every process in a set is holding resources and waiting for other resources held by other processes in the same set.

### The 4 Coffman Conditions
All four conditions must hold simultaneously for a deadlock to exist:
1. **Mutual Exclusion**: Resources cannot be used simultaneously by more than one process.
2. **Hold and Wait**: A process currently holding allocated resources requests additional resources without releasing existing ones.
3. **No Preemption**: Resources cannot be forcibly revoked from a process; they can only be released voluntarily upon task completion.
4. **Circular Wait**: A closed chain of processes exists: $P_0 \rightarrow P_1 \rightarrow P_2 \dots \rightarrow P_n \rightarrow P_0$, where each process waits for a resource held by the next.

### Dijkstra's Banker's Algorithm (Avoidance)
Maintains the system in a **Safe State** by simulating worst-case resource consumption before granting any resource allocation request:
* **Vectors and Matrices**:
  - $\text{Available}[j]$: Quantity of resource type $R_j$ currently free.
  - $\text{Allocation}[i][j]$: Quantity of resource $R_j$ currently assigned to process $P_i$.
  - $\text{Max}[i][j]$: Maximum quantity of resource $R_j$ process $P_i$ may request.
  - $\text{Need}[i][j] = \text{Max}[i][j] - \text{Allocation}[i][j]$
* **Safety Verification Step**:
  1. Let $\text{Work} = \text{Available}$ and $\text{Finish}[i] = \text{false}$ for all $i$.
  2. Find an index $i$ such that $\text{Finish}[i] == \text{false}$ and $\text{Need}_i \le \text{Work}$.
  3. If found:
     $$\text{Work} = \text{Work} + \text{Allocation}_i$$
     $$\text{Finish}[i] = \text{true}$$
     Repeat Step 2 until all processes finish.
  4. If all processes complete ($\text{Finish}[i] == \text{true} \ \forall i$), the state is **SAFE**, and the resulting order of completion forms the **Safe Execution Sequence**.

---

## 5. Secondary Storage & Disk Scheduling

### The Problem
Mechanical hard drives consist of spinning platters and read/write heads mounted on a movable arm. The time required to move the arm to the target track (**Seek Time**) accounts for the majority of secondary storage latency.

### Disk Scheduling Algorithms
1. **FCFS**: Processes cylinder requests in the exact order received. Fair, but results in high head travel distance.
2. **SSTF (Shortest Seek Time First)**: Selects the pending request closest to the current cylinder position. Minimizes immediate travel, but causes starvation for requests on edge cylinders.
3. **SCAN (Elevator Algorithm)**: The arm moves in one direction servicing requests until it reaches the physical disk boundary ($0$ or $\text{Max}$), then reverses direction.
4. **C-SCAN (Circular SCAN)**: Moves in one direction servicing requests. When it hits the disk boundary, it immediately returns to cylinder 0 *without servicing requests on the return stroke*, providing more uniform wait times.
5. **LOOK & C-LOOK**: Enhancements to SCAN and C-SCAN. The disk arm only travels as far as the **last request** in the current direction before reversing or returning, avoiding empty trips to physical platter limits.

---

## 6. Virtual Memory & MMU Address Translation

### Hardware Paging Architecture
The CPU generates a **Logical (Virtual) Address**, which the hardware **Memory Management Unit (MMU)** translates into a **Physical Address** in RAM.

### Translation Mechanics
For an architecture with page size $S = 2^k$ bytes (e.g., $4096 = 2^{12}$ bytes):
1. **Split**: The logical address is split bitwise into:
   - **Page Number ($p$)**: High-order bits indexing into the process Page Table.
   - **Offset ($d$)**: Lowest $k$ bits (e.g., 12 bits) denoting the exact byte position within the page.
2. **Lookup**: The MMU reads entry $p$ in the Page Table to obtain physical **Frame Number ($f$)** and checks the valid-invalid protection bit.
3. **Synthesis**:
   $$\text{Physical Address} = (f \times S) + d$$
4. *Key Invariant*: The offset $d$ remains identical between logical and physical memory because pages and frames are geometrically equal in size.

---

## 7. Simulated File System

### Core Architecture
1. **Inode (Index Node)**: A kernel data structure holding file metadata (file size, access permissions, owner ID, timestamp) and pointers to physical data blocks.
2. **Allocation Strategies**:
   - **Contiguous Allocation**: File blocks are assigned sequentially on disk. Fast sequential I/O, but causes severe external fragmentation and prevents file growth.
   - **Indexed Allocation**: An index block contains pointers to data blocks distributed across disk sectors. Completely eliminates external fragmentation and supports direct random access.
3. **Storage Allocation Bitmap**: A bit-vector where each bit represents the occupancy of a physical sector (`0 = free`, `1 = allocated`).

---

## 8. Process Lifecycle & State Machine

### 5-State Transition Flow
```
        [New]
          │ (admitted)
          v
  ┌──> [Ready] <──┐
  │       │       │ (timeout / preempt)
  │   (dispatch)  │
  │       v       │
  │   [Running] ──┘
  │       │
  │  (I/O or wait)
  │       v
  │   [Waiting]
  │       │
  └───────┘ (I/O completion)
          │
      [Running] ──(exit)──> [Terminated]
```

### Key POSIX System Calls & Definitions
* `fork()`: Creates a new child process by duplicating the calling process's address space. Returns `0` to the child and the **Child PID** to the parent.
* `execve()`: Replaces the current process image with a new binary executable file, initializing a fresh stack, heap, and code segment.
* **Zombie Process**: A terminated process whose exit status has not yet been collected by its parent via `wait()` or `waitpid()`. Retains a record in the OS Process Table.
* **Orphan Process**: A child process whose parent terminated while the child was still executing. Automatically adopted by `init` / `systemd` (PID 1), which reaps its exit status upon completion.

---

## 9. POSIX & Linux Concurrency

### The Critical Section Problem
When concurrent threads or processes access shared memory, non-atomic interleaved instructions cause **Race Conditions**. A correct synchronization solution must satisfy:
1. **Mutual Exclusion**: No two threads can execute inside their critical sections simultaneously.
2. **Progress**: If no thread is in the critical section, selection of the next entrant cannot be blocked indefinitely.
3. **Bounded Waiting**: A limit must exist on the number of times other threads can enter after a thread has requested access.

### Concurrency Primitives
* **Peterson's Algorithm**: A 2-process software mutual exclusion mechanism using a shared boolean array `flag[2]` and a shared integer variable `turn`.
* **POSIX Semaphores**:
  - `sem_wait(&s)`: Decrements counter. If $\le 0$, caller blocks until signaled.
  - `sem_post(&s)`: Increments counter and unblocks waiting threads.
* **Anonymous Pipes**: Unidirectional IPC byte-stream channels established via `pipe(int fd[2])`. `fd[0]` serves as the read handle, and `fd[1]` serves as the write handle.

---

## 10. Host System Diagnostics (`procfs`)

### What is `/proc`?
Linux provides access to live kernel telemetry via a virtual, in-memory pseudo-filesystem mounted at `/proc`:
* `/proc/stat`: Reports CPU tick counters (Jiffies) distributed across User, System, Idle, Nice, and I/O-wait states.
* `/proc/meminfo`: Exposes kernel memory counters including `MemTotal`, `MemFree`, `Buffers`, and `Cached`.
* **CPU Load Calculation**:
  $$\text{CPU Usage} = \left( 1 - \frac{\Delta\text{Idle Jiffies}}{\Delta\text{Total Jiffies}} \right) \times 100\%$$

---

## Viva & Interview Quick-Fire Questions

### Q1: Why is Round Robin preferred over FCFS in interactive operating systems?
**Answer**: FCFS can block interactive jobs behind long batch calculations (the Convoy Effect). Round Robin enforces a strict bound on response time $(n-1) \times q$, ensuring every interactive process receives regular CPU access.

### Q2: What causes Belady's Anomaly?
**Answer**: In FIFO page replacement, eviction is based strictly on arrival order rather than reference frequency or recency. Allocating additional frames alters the timeline of page evictions, occasionally discarding a page just before it is referenced again.

### Q3: What is the core difference between Deadlock Prevention and Deadlock Avoidance?
**Answer**:
* **Prevention** eliminates at least one of the 4 Coffman conditions statically through protocol rules (e.g., acquiring resources in strict linear order to break circular wait).
* **Avoidance** dynamically inspects every incoming resource request using current allocation matrices (such as Banker's Algorithm) to guarantee the system never transitions into an unsafe state.

### Q4: Why does the page offset remain unchanged during address translation?
**Answer**: Because virtual pages and physical frames are identical in size ($2^k$ bytes), any relative byte offset within a virtual page corresponds to the exact same relative offset within the target physical frame.

### Q5: How do Zombie and Orphan processes differ?
**Answer**:
* A **Zombie** is dead (finished execution) but still occupies an entry in the process table because its parent has not yet read its exit code via `wait()`.
* An **Orphan** is still executing, but its parent process has terminated. The operating system re-parents the orphan to PID 1 (`init` / `systemd`).
