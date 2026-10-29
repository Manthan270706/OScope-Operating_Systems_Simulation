# OScope — Operating Systems Simulation Lab

**OScope** is an interactive desktop application for learning, simulating, and experimenting with core Operating Systems concepts. It combines a **C++17 simulation backend** with a **Python/PySide6 graphical user interface (GUI)** to make operating systems concepts easier to understand through visualizations and interactive experiments.

The project is designed for students who want to explore CPU scheduling, memory management, virtual memory, deadlocks, disk scheduling, Linux/POSIX operations, and other OS concepts in one application.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation and Setup on Windows](#installation-and-setup-on-windows)
- [Build the C++ Backend](#build-the-c-backend)
- [Install the Python GUI](#install-the-python-gui)
- [Launch OScope](#launch-oscope)
- [Running on Linux](#running-on-linux)
- [Run the Tests](#run-the-tests)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Development Tools](#development-tools)

---

## Features

OScope brings multiple Operating Systems topics together in an interactive desktop interface.

### 1. CPU Scheduling

Explore and compare CPU scheduling algorithms:

- First-Come, First-Served (FCFS)
- Shortest Job First (SJF)
- Shortest Remaining Time First (SRTF)
- Priority Scheduling
- Round Robin (RR)
- Multilevel Feedback Queue (MLFQ)
- Compare All

Visualize process execution using Gantt charts and examine waiting time, turnaround time, response time, and other scheduling metrics.

### 2. Dynamic Memory Allocation

Experiment with memory allocation strategies:

- First Fit
- Best Fit
- Worst Fit
- Compare All

Explore partition splitting, deallocation, free-block coalescing, and external fragmentation through memory layout visualizations and result tables.

### 3. Page Replacement

Understand how virtual memory pages are managed using:

- FIFO (First-In, First-Out)
- LRU (Least Recently Used)
- Optimal Page Replacement
- Compare All

Inspect page hits, page faults, evictions, frame contents, and algorithm performance using step-by-step visualizations.

### 4. Deadlock Management

Study deadlock avoidance and detection through:

- Banker's Safety Algorithm
- Resource request evaluation
- Deadlock detection
- Safe sequence analysis
- Resource allocation visualization

Modify resource allocation states and examine whether processes can complete safely.

### 5. Disk Scheduling

Explore disk-head movement and compare disk scheduling strategies using interactive visualizations and scheduling results.

### 6. Linux and POSIX Experiments

Explore operating system mechanisms such as:

- Process management
- Thread experiments
- Inter-process communication (IPC)
- Pipes and message queues
- Synchronization
- Semaphores
- Peterson's algorithm

Linux-specific experiments require an appropriate Linux environment.

### 7. Host Resource Monitoring

Inspect host resource information exposed by the monitoring implementation and visualize available metrics.

### 8. Simulated File System

Explore a simulated file system through file operations, directory and storage representations, and operation results.

### 9. Virtual Memory and Address Translation

Study logical-to-physical address translation and memory-management concepts through interactive address translation visualizations.

### 10. Process Lifecycle Explorer

Explore process states and lifecycle transitions through a state-machine-based visualization.

> Feature availability and supported operations depend on the implementation of each module. The application and its backend must be built and configured correctly for the relevant experiments to run.

---

## Technology Stack

| Component                 | Technology                               |
| ------------------------- | ---------------------------------------- |
| Backend                   | C++17                                    |
| Build system              | CMake                                    |
| GUI                       | Python, PySide6                          |
| GUI testing               | pytest                                   |
| C++ testing               | GoogleTest                               |
| Windows Linux environment | WSL 2 with Ubuntu                        |
| Linux compiler            | GCC or another compatible C++17 compiler |

## Prerequisites

### Required software

For the recommended Windows setup, install the following:

| Software                    | Purpose                                                        | Download                                                                        |
| --------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Python 3.12 or 3.13, 64-bit | Run the desktop GUI                                            | [Python Downloads](https://www.python.org/downloads/)                           |
| WSL 2 with Ubuntu           | Build and run the Linux backend and Linux-specific experiments | [WSL Installation Guide](https://learn.microsoft.com/en-us/windows/wsl/install) |
| CMake                       | Configure the C++ project                                      | [CMake Downloads](https://cmake.org/download/)                                  |
| GCC / G++                   | Compile the C++ backend                                        | Installed through Ubuntu's `build-essential` package                            |

Python 3.12 or 3.13 is recommended, provided the dependencies in `gui/requirements.txt` support the selected version.

---

## Installation and Setup on Windows

The recommended architecture runs the **PySide6 GUI directly on Windows** while using **WSL Ubuntu for the Linux C++ backend**.

### Step 1 — Install WSL and Ubuntu

Open PowerShell as Administrator and run:

```powershell
wsl --install -d Ubuntu
```

Restart your computer if Windows requests it. Complete the initial Ubuntu setup and create your Linux username and password.

If WSL and Ubuntu are already installed, verify the environment:

```powershell
wsl --list --verbose
```

Ensure that Ubuntu is using WSL 2.

### Step 2 — Clone the repository

Open PowerShell and run:

```powershell
New-Item -ItemType Directory -Force C:\dev
Set-Location C:\dev

git clone https://github.com/Nitish-0710/OScope.git
Set-Location OScope
```

The repository will be located at:

```text
C:\dev\OScope
```

Keeping the repository under a Windows drive accessible to WSL makes it straightforward for the Windows GUI to invoke the backend through WSL.

If you choose another directory or drive, adjust the corresponding paths in the following instructions.

---

## Build the C++ Backend

### Step 3 — Install build dependencies in Ubuntu

Open the Ubuntu terminal and run:

```bash
sudo apt update
sudo apt install -y build-essential cmake git
```

These packages provide the compiler, CMake, and Git needed for the recommended build workflow.

### Step 4 — Navigate to the repository in WSL

For the example repository path `C:\dev\OScope`, run:

```bash
cd /mnt/c/dev/OScope
```

Windows drives are typically accessible in WSL under `/mnt/<drive-letter>/`.

For example, a repository under `D:\College\OS\OScope` would normally be accessible at `/mnt/d/College/OS/OScope`.

### Step 5 — Configure and compile the backend

From the repository root inside Ubuntu:

```bash
cmake -S . -B build
cmake --build build -j2
```

CMake configures the project, downloads its declared GoogleTest dependency when needed, and compiles the C++ targets.

The main backend executable should be created at:

```text
build/oscope
```

Verify that the executable exists:

```bash
test -x build/oscope && echo "OScope backend built successfully"
```

If configuration or compilation fails, resolve the reported errors before launching the GUI.

---

## Install the Python GUI

### Step 6 — Create a virtual environment

Open a new PowerShell terminal and navigate to the cloned repository:

```powershell
Set-Location C:\dev\OScope
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation because of the execution policy, you can activate the environment from Command Prompt instead:

```cmd
.venv\Scripts\activate.bat
```

Alternatively, use the Python executable inside `.venv` directly without activating it.

### Step 7 — Install Python dependencies

With the virtual environment activated, run:

```powershell
python -m pip install --upgrade pip
python -m pip install -r gui/requirements.txt
```

The requirements file is the source of truth for the GUI's Python dependencies.

Verify the GUI framework installation:

```powershell
python -c "import PySide6; print('PySide6 installed successfully')"
```

---

## Launch OScope

### Step 8 — Start the desktop application

From the repository root in PowerShell, with the virtual environment activated:

```powershell
python gui/run_gui.py
```

OScope should open in its own desktop window.

The GUI's backend runner must be able to locate the compiled executable in WSL. If the application reports that the experiment engine is unavailable, verify that the backend build succeeded and that the repository path is accessible through WSL.

### Running the backend separately

To inspect the backend directly, open Ubuntu and run:

```bash
cd /mnt/c/dev/OScope
./build/oscope
```

The backend supports an interactive command-line interface. Its available operations depend on the implemented CLI commands.

The desktop GUI is the recommended way to explore the simulations visually.

---

## Running on Linux

A native Linux setup can use GCC, CMake, Python, and PySide6 without requiring Windows or WSL.

### Install system dependencies

On Ubuntu or a compatible Debian-based distribution:

```bash
sudo apt update
sudo apt install -y git cmake build-essential python3 python3-venv python3-pip
```

### Clone and build

```bash
git clone https://github.com/Nitish-0710/OScope.git
cd OScope

cmake -S . -B build
cmake --build build -j2
```

### Install GUI dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r gui/requirements.txt
```

### Launch the application

```bash
python gui/run_gui.py
```

Native Linux execution depends on the GUI's backend runner correctly locating and invoking the native executable. The Windows + WSL setup is the recommended documented workflow; native Linux and macOS configurations should be verified against the current backend runner and platform dependencies before being considered fully supported.

---

## Run the Tests

OScope includes C++ and Python test suites.

### C++ tests

Run these commands in Ubuntu from the repository root:

```bash
cmake -S . -B build
cmake --build build -j2
ctest --test-dir build --output-on-failure
```

CTest reports the executed tests and any failures.

### Python GUI tests

Run these commands from the repository root in PowerShell with the virtual environment activated:

```powershell
$env:PYTHONPATH = "gui"
python -m pytest gui/tests -v
```

On Linux, run:

```bash
PYTHONPATH=gui python -m pytest gui/tests -v
```

The Python suite covers GUI models, backend execution and parsing, individual modules, and GUI smoke tests.

Use the actual test output to determine whether the suite passes on your machine; test counts can change as the project evolves.

---

## Troubleshooting

### 1. `cmake` is not recognized

Install CMake and ensure it is available on your PATH. In the recommended Windows workflow, run CMake inside Ubuntu after installing it with `apt`.

### 2. `g++` is not found

In Ubuntu, install the compiler toolchain:

```bash
sudo apt update
sudo apt install -y build-essential
```

### 3. The GUI starts but the backend is unavailable

Check that the executable exists:

```bash
cd /mnt/c/dev/OScope
ls -l build/oscope
```

If it does not exist, build the backend again:

```bash
cmake -S . -B build
cmake --build build -j2
```

Also verify that Ubuntu is installed and that WSL can access the repository directory.

### 4. Python cannot import PySide6

Activate the correct virtual environment and install the declared dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r gui/requirements.txt
```

Make sure you are using the same Python environment for installation and execution.

### 5. `pytest` cannot find the GUI package

Run the test command from the repository root and set the Python import path:

```powershell
$env:PYTHONPATH = "gui"
python -m pytest gui/tests -v
```

### 6. CMake cannot download GoogleTest

Check your internet connection and retry CMake configuration. The project declares GoogleTest through CMake's `FetchContent` mechanism, so the initial configuration may require downloading its source.

### 7. Linux-specific experiments fail

Some experiments rely on Linux/POSIX facilities. On Windows, use the recommended WSL Ubuntu environment and ensure the backend is compiled and executed there.

---

## Project Structure

```text
OScope/
├── .github/
│   └── workflows/          # GitHub Actions workflows
├── docs/                   # Project documentation
├── gui/
│   ├── oscope_gui/
│   │   ├── backend/        # Backend execution and output parsing
│   │   ├── models/         # GUI-side data and models
│   │   ├── pages/          # Application pages
│   │   └── widgets/        # Reusable visual components
│   ├── tests/              # Python GUI tests
│   ├── requirements.txt   # Python dependencies
│   └── run_gui.py          # GUI entry point
├── include/
│   └── oscope/             # C++ headers
├── scripts/                # Verification and audit utilities
├── src/                    # C++ implementation
├── tests/                  # C++ tests
├── CMakeLists.txt          # CMake build configuration
└── README.md               # Project documentation
```

---

## Development Tools

The following tools are optional:

- **Microsoft Visual Studio IDE:** Not required for the recommended WSL/GCC build.
- **Visual Studio Code:** Optional editor.
- **Other code editors:** Any editor can be used to modify the source code.

You can build, test, and run OScope entirely from terminals without using an IDE.

## Contributing

Contributions, bug reports, and suggestions are welcome. Before submitting changes, build the C++ backend and run the relevant C++ and Python tests.

When reporting a problem, include the operating system, Python version, compiler version, relevant error output, and the steps needed to reproduce the issue.

## License

Check the repository for its applicable license before redistributing or modifying OScope.

---

**Repository:** https://github.com/Nitish-0710/OScope

**OScope — Explore Operating Systems through simulation and experimentation.**
