# OScope Desktop GUI (Stage 1)

**OScope** is an interactive Operating Systems learning, simulation, and experimentation platform.
This desktop application provides a modern, dark-themed Windows presentation layer built on **PySide6**, integrating seamlessly with the verified C++ backend.

---

## 1. Stage 1 Backend & Architecture Audit Findings

### A. Verified CPU Scheduling Commands & Input Format
- **C++ Executable Target:** `build/oscope` (compiled under WSL Ubuntu, C++17, CMake).
- **Interactive Mode:** Invoked without flags (`./build/oscope`). Stdin stream accepts line-delimited commands:
  - Algorithm Choice: `1` (FCFS), `2` (SJF), `3` (SRTF), `4` (Priority), `5` (Round Robin), `6` (MLFQ), `7` (Compare All).
  - Algorithm Parameters:
    - Round Robin: Time quantum integer (`> 0`).
    - MLFQ: Quanta integers for `Q0`, `Q1`, `Q2` (`> 0`).
    - Compare All: Time quantum for RR, followed by `Q0`, `Q1`, `Q2` for MLFQ.
  - Process Count: Positive integer `N` (`> 0`).
  - Process Attributes: For each process `1..N`:
    - `PID`: Unique integer (`>= 0`).
    - `Arrival Time`: Non-negative integer (`>= 0`).
    - `Burst Time`: Positive integer (`> 0`).
    - `Priority`: Integer (lower numeric value = higher priority; ignored by FCFS/SJF/SRTF/RR/MLFQ, used by Priority and Compare All).
  - Termination: Choice `13` cleanly exits the interactive shell.

### B. Output Schema and Metrics
- **Execution Timeline Segments:**
  - `[start -> end] Process PID <id>`
  - `[start -> end] IDLE (CPU Idle)`
- **Per-Process Metrics:** PID, Arrival Time, Burst Time, Completion Time, Turnaround Time, Waiting Time, Response Time.
- **Aggregate Metrics:** Average Waiting Time, Average Turnaround Time, Average Response Time.
- **Comparison Table:** Tabulates Average Waiting, Turnaround, and Response times across all 6 algorithms on the identical workload.

### C. Executable Availability on Windows vs. WSL
- **Current State:** The C++ backend depends on POSIX/Linux-specific system headers (`<mqueue.h>`, `<semaphore.h>`, `<sys/wait.h>`, `/proc/` filesystem monitoring) implemented for course requirements.
- **Consequence:** The existing codebase compiles to a Linux ELF binary (`build/oscope`) in WSL Ubuntu. Compiling natively on MSVC/Windows without a POSIX compatibility layer (such as MSYS2 or Cygwin) is not feasible without altering verified POSIX course modules.
- **GUI-to-Backend Architecture:**
  - The Python GUI runs **natively on Windows** (`python.exe` with PySide6).
  - It utilizes an extensible `BaseBackendRunner` interface:
    - `WSLBackendRunner`: Invokes the verified ELF executable via `wsl.exe --cd <repo_dir> ./build/oscope` with direct argument lists (no shell injection, separate stdout/stderr capture, process timeout and cancellation support).
    - `NativeBackendRunner`: Auto-detects and seamlessly switches to a native `oscope.exe` if built via MinGW or configured via `OSCOPE_BINARY`.

---

## 2. Prerequisites & Environment Setup

### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10 to 3.13 (64-bit)
- Windows Subsystem for Linux (WSL) with Ubuntu installed
- Compiled OScope binary (`cd /mnt/d/... && cmake -B build && cmake --build build`)

### Virtual Environment Setup on Windows
```powershell
# Navigate to repository root
cd D:\College\3rd_Year\OS\OS_CP

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r gui/requirements.txt
```

Alternatively, to install only the core desktop GUI components:
```powershell
pip install PySide6-Essentials pytest
```

---

## 3. Launching the Application

From PowerShell or Command Prompt:
```powershell
python gui\run_gui.py
```

---

## 4. Features Implemented in Stage 1

### A. Modern Student-Friendly Dark Dashboard
- **Clean Academic Branding:** "OScope — Operating Systems Simulation Lab" without clutter or raw backend internals.
- **User-Facing Engine Status:** Simple, informative indicator ("Ready to run experiments" or "Experiment engine unavailable") with a retry action if unavailable.
- **Compact Hero Card:** Direct, prominent access to the CPU Scheduling simulator with algorithm capability tags (`FCFS`, `SJF`, `SRTF`, `Priority`, `Round Robin`, `MLFQ`, `Compare All`).
- **Honest Roadmap Grid:** Balanced, clean cards for all modules with accurate availability states:
  - CPU Scheduling: *Available*
  - Dynamic Memory Allocation: *Available*
  - Virtual Memory / Page Replacement: *Available*
  - Deadlock Management: *Available*
  - Disk Scheduling: *Planned*
  - Linux / POSIX Experiments: *Planned*
- **Session Execution History:** Tracks genuine simulation runs conducted during the active session with an informative empty state prior to first run.

### B. Educational CPU Scheduling Simulator
- **Supported Algorithms:**
  - First-Come, First-Served (FCFS)
  - Shortest Job First (SJF - Non-Preemptive)
  - Shortest Remaining Time First (SRTF - Preemptive)
  - Priority Scheduling (Non-Preemptive; lower number = higher priority)
  - Round Robin (RR) with configurable time quantum
  - Multilevel Feedback Queue (MLFQ) with configurable Q0, Q1, Q2 quanta
  - Compare Algorithms (side-by-side benchmark)
- **Beginner Guidance ("Understanding the Inputs"):**
  - Explains Process ID (PID), Arrival Time, CPU Burst Time, and Priority in clear, accessible terms.
  - Documents the exact priority convention used by the C++ scheduler (`Lower numeric value = Higher scheduling priority`).
  - Includes a concrete illustrative example workload (P1, P2) showing what each parameter represents before running.
- **Fixed & Readable Process Table:**
  - High-contrast, fully visible column headers: `Process ID (PID)`, `Arrival Time (>= 0)`, `CPU Burst Time (> 0)`, `Priority (Lower = Higher)`.
  - Dynamic priority handling: when non-priority algorithms are chosen, priority column header updates to `Priority (Ignored)` with dimmed values and read-only styling.
  - Generous 36px row heights and hidden vertical row indices to eliminate awkward scrollbars and clipping.
  - Quick presets: *Standard 3-Process*, *Convoy Effect*, *Preemptive SJF/SRTF Split*, *Priority Differentiation*.
  - Strict input validation before backend invocation with pinpoint error feedback.
- **Educational Visual Results:**
  - Custom `QPainter` **Gantt Chart** with distinct process colors, clear idle blocks, tick marks, and hover inspection tooltips explaining start, end, and duration.
  - Summary metric cards with educational tooltips explaining Waiting Time, Turnaround Time, Response Time, and Total Duration.
  - Per-process results table with formula caption (`Turnaround = Completion - Arrival`, `Waiting = Turnaround - Burst`).
  - Multi-algorithm comparison table for side-by-side performance comparison.
  - Optional raw C++ terminal output tab for complete transparency.

### C. Interactive Memory Allocation Simulator
- **Supported Allocation Strategies:**
  - **First Fit:** Selects the first free block from the start of memory that is large enough. Fast, but can leave small fragments at the beginning of the pool.
  - **Best Fit:** Searches the entire memory pool to find the smallest suitable free block. Minimizes wasted capacity per block, but can produce tiny unusable slivers.
  - **Worst Fit:** Allocates from the largest available free block. Leaves the largest possible remainder block, which may remain usable for future requests.
  - **Compare All Strategies:** Side-by-side benchmark comparing First Fit, Best Fit, and Worst Fit against the identical sequence of operations.
- **Dynamic Partition Management:**
  - Automatic partition splitting upon allocation.
  - Automatic coalescing of adjacent free partitions upon deallocation.
  - Genuine external fragmentation reporting: `(Free Memory - Largest Free Block) / Free Memory`.
- **Educational Guidance & Presets:**
  - "Understanding Memory Allocation" concept cards explaining Memory Pool, Logical Request ID, Block Capacity vs Process Size, and Free Coalescing.
  - Built-in presets: *Standard Partitioning*, *Fragmentation & Coalescing*, *Strategy Differentiation*.
  - Inline input validation preventing negative/zero memory sizes or invalid logical IDs.
- **Real-Time Memory Pool Visualization:**
  - Custom `QPainter` **MemoryMapWidget** presenting contiguous physical address space `[0 → Total]`.
  - Distinct color palette: Cyan/Sky for allocated partitions (`P{pid}`, size), Emerald/Mint for free partitions, Rose for failed allocations.
  - Address axis ticks at partition boundaries.
  - Interactive mouse hover inspection tooltips with block index, start/end range, byte size, percentage of total pool, and assigned PID.
- **Comprehensive Results View:**
  - 4 StatCards: Allocated Memory, Free Memory, Largest Free Block, External Fragmentation percentage.
  - Tab 1: Verified Memory Block Layout Table (Block #, Start Address, Size, Status, Allocation ID, Process ID).
  - Tab 2: Operation Execution Log (Step, Type, Request ID, Result badge, Details / Error message).
  - Tab 3: Multi-Strategy Comparison Table (Attempts, Success, Failures, Success Rate, Allocated, Free, Ext Frag).
  - Tab 4: Raw Terminal Output from C++ execution.

### D. Interactive Page Replacement Simulator
- **Supported Algorithms:**
  - **FIFO (First-In, First-Out):** Evicts the page residing in physical memory the longest. Susceptible to Belady's Anomaly where allocating more frames can yield more page faults.
  - **LRU (Least Recently Used):** Evicts the page that has not been referenced for the longest time, leveraging temporal locality.
  - **Optimal (MIN / Belady's Optimal):** Evicts the page whose next reference occurs farthest in the future (or is never referenced again). Serves as a theoretical upper bound for algorithmic efficiency.
  - **Compare All Algorithms:** Side-by-side comparison benchmark running FIFO, LRU, and Optimal against the identical reference sequence and frame budget.
- **Educational Guidance & Presets:**
  - "Virtual Memory Concepts" explanation banner dynamically updating with deep theoretical insights per selected algorithm.
  - Intuitive presets:
    - *Classic Textbook Sequence:* `7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2` (3 frames).
    - *Belady's Anomaly Demonstration:* `1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5` (3 frames vs 4 frames FIFO anomaly).
    - *High Locality Sequence:* `1, 1, 2, 2, 3, 1, 2, 3, 4, 4, 1, 2` (4 frames, highlights LRU cache-friendliness).
    - *Sequential Cyclic Access:* `0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3` (3 frames worst-case looping).
  - Flexible reference string parsing supporting comma-delimited, space-delimited, or mixed notation with rigorous non-negative integer validation.
- **Interactive Frame-by-Frame Timeline & Stepper:**
  - Custom `FrameGridWidget` visualizing memory frames horizontally across every reference step.
  - Color-coded step columns:
    - Step number header and referenced Page ID badge (`Page X`).
    - Prominent Outcome Badge: vibrant Emerald `HIT` or Rose `FAULT`.
    - Physical Memory Frame slots showing loaded page values, glowing Cyan border on the referenced page, and dashed dim indicators for empty slots (`—`).
    - Eviction Tag: cleanly indicating which page was displaced (`Evicted: P{X}`) or `None`.
  - Active step column highlighting with auto-scroll tracking.
  - Animation & Stepper Controls:
    - `|<< First`, `< Prev`, `Next >`, `Last >>` for manual step inspection.
    - Play / Pause animation button (`▶ Play` / `⏸ Pause`) running a non-blocking `QTimer`.
    - Playback speed selector: Normal (600ms), Fast (250ms), and Slow (1200ms).
  - Natural Language Step Analysis Inspector: dynamically breaks down the exact OS memory event for the active step (e.g. *"Page hit: Page 0 is already resident in Frame 1. No page fault occurred."* or *"Page fault with replacement: Page 3 loaded into Frame 0. Evicted Page 7 according to FIFO rules."*).
- **Comprehensive Results & Comparison View:**
  - 4 StatCards: Total References, Page Faults, Page Hits, Page Fault Rate / Hit Rate.
  - Tab 1: Detailed Step-by-Step History Table (Step, Page, Result badge, Evicted page, Frame slots state).
  - Tab 2: Multi-Algorithm Comparison Table (Algorithm, Page Faults, Page Hits, Fault Rate %, Hit Rate %, Best Algorithm indicator).
  - Tab 3: Raw C++ Execution Output.

### E. Interactive Deadlock Management Simulator
- **Supported Analysis Modes:**
  - **Banker's Safety Algorithm (Avoidance):** Proactively analyzes declared maximum claims before granting resources. Evaluates Work and Finish vectors to determine whether at least one safe execution sequence exists that guarantees all processes can finish under maximum claims without deadlock.
  - **Simulate Resource Request (Avoidance / Grant Evaluation):** Simulates an immediate resource acquisition request by a process. Tentatively updates Allocation and Available, then executes the Banker's safety check. If the resulting state is safe, the request is **GRANTED**; otherwise it is **DENIED** and the original system state is preserved uncorrupted.
  - **Deadlock Detection Algorithm (Recovery / Detection):** Evaluates active allocations and outstanding unfulfilled requests. Finds processes that can complete with currently Available resources and held Allocations. Processes that cannot finish are identified as **DEADLOCKED**.
- **Educational Guidance & Presets:**
  - "Understanding Deadlock & Banker's Algorithm Concepts" banner explaining Available pool, held Allocations, declared Maximum claims, and calculated Need.
  - Built-in educational presets:
    - *Textbook Safe State (Silberschatz 5P/3R):* Classic textbook safe state resolving in order `P1 ➔ P3 ➔ P4 ➔ P0 ➔ P2` (or `P1 ➔ P3 ➔ P0 ➔ P2 ➔ P4`).
    - *Unsafe State (Potential Deadlock):* Starvation / unsafe configuration where no process can satisfy its remaining need.
    - *Eligible Safe Grant (Banker's Request):* Process P1 requests `[1, 0, 2]`; granted safely.
    - *Unsafe Denial (Banker's Request):* Process P4 requests `[3, 3, 0]`; safely denied to prevent entering an unsafe state.
    - *Circular Wait Deadlock (Detection):* Circular wait involving P1, P2, P3, P4 unable to proceed.
    - *Resolvable Workload (Detection):* Processes P0 and P2 can finish and release held resources, resolving the system.
- **Dynamic Need Matrix Calculation:**
  - Live recalculation of $Need = Maximum - Allocation$ as users edit cells in Allocation or Max Claim tables.
  - Real-time cell highlighting: Emerald for positive remaining need, Muted for 0, and vibrant Rose error flagging when $Allocation > Maximum$.
- **Centerpiece Resource Allocation Graph & Sequence Flow Widget:**
  - Custom `ResourceGraphWidget` with a high-contrast visual canvas:
    - Process Cards (left) with PID emblems, active status badges (`SAFE`, `BLOCKED`, `ACTIVE`), and allocation vector summaries.
    - Resource Nodes (right) with resource badges and available pool quantities.
    - Solid Cyan cubic bezier curves representing allocated (held) resources ($R_j \rightarrow P_i$) with quantity badges.
    - Dashed Amber/Rose cubic bezier curves representing pending requests / remaining need ($P_i \rightarrow R_j$) with quantity badges.
    - Dynamic hover highlight state spotlighting connected edges and connected nodes.
  - Horizontal `SequenceFlowBar` displaying the step-by-step resolution order (e.g. `Step 1: P1 ➔ Step 2: P3 ➔ ...`) for safe states, or a prominent alert for unsafe / deadlocked states.
- **Comprehensive Results View:**
  - 4 StatCards: Analysis Outcome, Safe Sequence / Deadlocked Processes, Process Count, Available Pool.
  - Tab 1: Matrices Breakdown Table (Process, Allocation, Max Claim / Request, Need).
  - Tab 2: Natural Language Diagnostic Report explaining system state, Coffman condition implications, and execution status.
  - Tab 3: Raw C++ Output from backend execution.

---

## 5. Running Tests

Run the Python automated test suite:
```powershell
$env:PYTHONPATH='gui'; python -m pytest gui/tests -v
```

The test suite contains **85 automated tests** with 100% pass rate:
- **Backend Runner & Path Conversion:** WSL path transformation, argument list construction, non-zero exit handling, process cancellation.
- **Parser & Generator Tests:** Stdin command stream generation and stdout parsing for CPU scheduling, dynamic memory allocation, page replacement, and deadlock management.
- **Deadlock Model & Validation Tests:** Enum mappings, dimension matching, available vector bounds, allocation <= max claim checks, request bounds, and properties.
- **Interactive Navigation & Smoke Tests:** Main window sidebar navigation across all 5 pages (Dashboard, Scheduling, Memory, Paging, Deadlock), stack switching, close event cleanup, and widget creation.
- **CPU Scheduling Suite:** Single algorithms, preemptive/non-preemptive Gantt chart rendering, idle blocks, multi-algorithm comparison tables.
- **Memory Allocation Suite:** First Fit, Best Fit, Worst Fit, block splitting, free coalescing, external fragmentation metrics, memory map rendering.
- **Page Replacement Suite:** FIFO, LRU, Optimal, Compare All CLI mappings, frame slot state verification, step navigation, animation timer safety.
- **Deadlock Management Suite:** Banker's Safety algorithm, resource request simulation, deadlock detection, matrix dimension validation, live Need calculation, safe sequence display, unsafe state handling, educational presets, graph canvas consistency, and non-regression guarantees across all modules.

