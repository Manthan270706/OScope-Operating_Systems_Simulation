# OScope — Operating Systems Simulation & Experimentation Laboratory

**OScope** is a high-precision, production-grade Operating Systems laboratory designed for computer science education. It connects an authoritative C++20 simulation core with modern, interactive user interfaces — allowing students and researchers to configure inputs, step through algorithmic execution, inspect vector visualizers (SVG Gantt charts, memory partition maps, page replacement steppers, disk seek trajectories), and benchmark metrics against standard OS textbook problems.

---

## Quick Start

### 1. Launch the Modern Web Application (Recommended)

The web application runs with **zero extra pip dependencies** using Python's standard library and opens directly in your browser:

```bash
python run_web.py
```

* Flags:
  * `--port 8080`: Custom port (auto-detects open port if occupied).
  * `--no-browser`: Start server without automatically launching the browser.
  * Access in any browser at `http://127.0.0.1:8080`.

### 2. Launch the Desktop PySide6 Application

If you prefer the native desktop Qt experience:

```bash
python gui/run_gui.py
```

### 3. Run Automated Tests

To run the complete test suite (150 tests across backend parser, domain models, GUI smoke tests, web API, and HTTP server):

```bash
python -m pytest gui/tests
```

To run C++ backend tests in WSL:

```bash
wsl ./build/oscope_tests
```

---

## Modern Web Design System

The OScope web laboratory has been reimagined from the ground up, eliminating generic dark neon "AI slop" in favor of an **academic devtool light theme** (inspired by Linear and Vercel Geist design guidelines):

- **Achromatic Canvas**: Soft cool off-white canvas (`#f8fafc`) with crisp white surfaces (`#ffffff`) for elevated readability without eye strain.
- **Hairline Precision**: 1px structural borders (`#e2e8f0` / `#cbd5e1`) and subtle ambient shadows provide clear visual hierarchy.
- **Academic Process Palette**: High-contrast, non-neon process tokens (Royal Blue, Deep Violet, Emerald, Amber, Crimson, Cyan, Terracotta).
- **Tabular Numerics**: Monospace alignment (`font-variant-numeric: tabular-nums`) for exact comparison across turnaround, waiting, and burst time calculations.

---

## Supported Simulation Modules

| Module | Core Features | Visualizer |
| :--- | :--- | :--- |
| **1. CPU Scheduling** | FCFS, SJF (Preemptive/Non-preemptive), Round Robin, Priority (Preemptive/Non-preemptive) | Vector SVG Gantt Chart with idle hatching & tick markers |
| **2. Dynamic Memory** | First-Fit, Best-Fit, Worst-Fit allocation & deallocation | Dynamic Memory Partition Map with fragmentation analysis |
| **3. Page Replacement** | FIFO, LRU, Optimal algorithms, custom reference strings | Interactive Step-by-Step Frame Stepper & Hit/Fault gauges |
| **4. Deadlock Management** | Dijkstra's Banker's Algorithm, Safe Sequences, Request Vector grant tests | Interactive Resource-Allocation & Need Matrices |
| **5. Disk Arm Scheduling** | FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK algorithms | High-resolution Cylinder Trajectory & Head Seek Plot |
| **6. Virtual Memory & MMU** | Logical-to-Physical translation, page number/offset split, demand paging | Interactive Two-level MMU Architecture Flowchart |
| **7. Simulated File System** | Contiguous and Indexed allocation, inode metadata, directory hierarchy | 64-Block Physical Storage Allocation Grid & Inode Tree |
| **8. Process Lifecycle** | 5-state lifecycle (New, Ready, Running, Waiting, Terminated) | State Transition Sequence & Signal Trace |
| **9. POSIX & Linux Concurrency** | Pipes, POSIX semaphores, shared memory, Peterson's algorithm | Real POSIX IPC Output & Synchronization Inspector |
| **10. Host System Diagnostics** | Live Linux kernel metrics parsed from `/proc/stat` and `/proc/meminfo` | System Load Gauges & Memory Utilization Breakdown |

---

## Architecture

```
OScope Repository
├── build/                 # Authoritative C++20 simulation binaries (oscope & oscope_tests)
├── src/ & include/        # C++ simulation algorithms & domain core
├── gui/
│   ├── oscope_gui/        # Native PySide6 desktop GUI application
│   └── tests/             # Pytest test suite (150 tests)
├── web/
│   ├── index.html         # Responsive Single Page Application (10 experiment workbenches)
│   ├── server.py          # Multi-threaded HTTP server (Python standard library)
│   ├── api.py             # Domain model & C++ runner translation bridge
│   └── static/
│       ├── css/main.css   # Modern light-mode engineering design system
│       ├── js/api.js      # REST API client
│       ├── js/visualizations.js # Custom SVG visualizers (Gantt, Memory, Stepper, Disk, MMU)
│       └── js/app.js      # State controller, form management & presets
└── run_web.py             # One-click web application launcher
```

---

## Documentation & Viva Preparation

* **Concepts & Viva Guide**: [docs/OS_CONCEPTS_GUIDE.md](docs/OS_CONCEPTS_GUIDE.md) — Comprehensive guide covering algorithms, mathematical formulas, Coffman conditions, Belady's Anomaly, address translation, and typical viva examination questions.

