"""Unit tests for C++ CLI input sequence generation and output parsing."""

import pytest
from oscope_gui.backend.parser import (
    generate_scheduling_stdin,
    parse_comparison_output,
    parse_scheduling_output,
)
from oscope_gui.models.scheduling import (
    AlgorithmConfig,
    AlgorithmType,
    ProcessInput,
)


def test_generate_stdin_fcfs():
    config = AlgorithmConfig(algorithm=AlgorithmType.FCFS)
    processes = [
        ProcessInput(pid=1, arrival_time=0, burst_time=5, priority=0),
        ProcessInput(pid=2, arrival_time=1, burst_time=3, priority=0),
    ]

    stdin_data = generate_scheduling_stdin(config, processes)
    expected_lines = [
        "1",  # Menu choice 1 for FCFS
        "2",  # Process count
        "1", "0", "5", "0",  # Process 1: PID, Arrival, Burst, Priority
        "2", "1", "3", "0",  # Process 2: PID, Arrival, Burst, Priority
        "13", # Exit choice
    ]
    assert stdin_data.strip().splitlines() == expected_lines


def test_generate_stdin_round_robin():
    config = AlgorithmConfig(algorithm=AlgorithmType.ROUND_ROBIN, rr_quantum=4)
    processes = [
        ProcessInput(pid=10, arrival_time=0, burst_time=12, priority=0),
    ]

    stdin_data = generate_scheduling_stdin(config, processes)
    lines = stdin_data.strip().splitlines()
    assert lines[0] == "5"   # Menu choice 5 for Round Robin
    assert lines[1] == "4"   # Time quantum
    assert lines[2] == "1"   # Process count
    assert lines[3:7] == ["10", "0", "12", "0"]
    assert lines[-1] == "13" # Exit


def test_generate_stdin_mlfq():
    config = AlgorithmConfig(algorithm=AlgorithmType.MLFQ, mlfq_q0=3, mlfq_q1=6, mlfq_q2=12)
    processes = [
        ProcessInput(pid=1, arrival_time=0, burst_time=10, priority=0),
    ]

    stdin_data = generate_scheduling_stdin(config, processes)
    lines = stdin_data.strip().splitlines()
    assert lines[0] == "6"   # Menu choice 6 for MLFQ
    assert lines[1] == "3"   # Q0 quantum
    assert lines[2] == "6"   # Q1 quantum
    assert lines[3] == "12"  # Q2 quantum
    assert lines[4] == "1"   # Process count
    assert lines[-1] == "13"


def test_generate_stdin_compare_all():
    config = AlgorithmConfig(algorithm=AlgorithmType.COMPARE_ALL, rr_quantum=2, mlfq_q0=2, mlfq_q1=4, mlfq_q2=8)
    processes = [
        ProcessInput(pid=1, arrival_time=0, burst_time=4, priority=1),
    ]

    stdin_data = generate_scheduling_stdin(config, processes)
    lines = stdin_data.strip().splitlines()
    assert lines[0] == "7"  # Choice 7: Compare all
    assert lines[1] == "2"  # RR quantum
    assert lines[2] == "2"  # MLFQ Q0
    assert lines[3] == "4"  # MLFQ Q1
    assert lines[4] == "8"  # MLFQ Q2
    assert lines[5] == "1"  # Process count
    assert lines[-1] == "13"


SAMPLE_FCFS_OUTPUT = """
Simulation completed successfully.
Scheduled 3 process(es) across 3 timeline execution segment(s).

=== Execution Timeline ===
Total Simulation Interval: [0 -> 16] (Duration: 16)

Gantt Chart:
| [P1 0-5] | [P2 5-8] | [P3 8-16] |

Execution Segments:
  [0 -> 5] Process PID 1
  [5 -> 8] Process PID 2
  [8 -> 16] Process PID 3

=== Process Metrics Table ===
   PID   Arrival     Burst   Completion   Turnaround    Waiting   Response
--------------------------------------------------------------------------
     1         0         5            5            5          0          0
     2         1         3            8            7          4          4
     3         2         8           16           14          6          6

=== Average Metrics ===
Average Waiting Time:    3.33
Average Turnaround Time: 8.67
Average Response Time:   3.33
"""


def test_parse_scheduling_output_fcfs():
    result = parse_scheduling_output(SAMPLE_FCFS_OUTPUT, "First-Come, First-Served (FCFS)")

    assert result.total_processes == 3
    assert result.total_duration == 16
    assert len(result.timeline) == 3

    assert result.timeline[0].start_time == 0
    assert result.timeline[0].end_time == 5
    assert result.timeline[0].pid == 1
    assert not result.timeline[0].is_idle

    assert result.timeline[2].start_time == 8
    assert result.timeline[2].end_time == 16
    assert result.timeline[2].pid == 3

    assert len(result.process_results) == 3
    pr1 = result.process_results[0]
    assert pr1.pid == 1
    assert pr1.arrival_time == 0
    assert pr1.burst_time == 5
    assert pr1.completion_time == 5
    assert pr1.turnaround_time == 5
    assert pr1.waiting_time == 0
    assert pr1.response_time == 0

    assert pytest.approx(result.averages.average_waiting_time, 0.01) == 3.33
    assert pytest.approx(result.averages.average_turnaround_time, 0.01) == 8.67
    assert pytest.approx(result.averages.average_response_time, 0.01) == 3.33


SAMPLE_IDLE_OUTPUT = """
Simulation completed successfully.
Scheduled 1 process(es) across 1 timeline execution segment(s).

=== Execution Timeline ===
Total Simulation Interval: [2 -> 7] (Duration: 5)

Gantt Chart:
| [IDLE 0-2] | [P1 2-7] |

Execution Segments:
  [0 -> 2] IDLE (CPU Idle)
  [2 -> 7] Process PID 1

=== Process Metrics Table ===
   PID   Arrival     Burst   Completion   Turnaround    Waiting   Response
--------------------------------------------------------------------------
     1         2         5            7            5          0          0

=== Average Metrics ===
Average Waiting Time:    0.00
Average Turnaround Time: 5.00
Average Response Time:   0.00
"""


def test_parse_scheduling_output_with_idle():
    result = parse_scheduling_output(SAMPLE_IDLE_OUTPUT, "FCFS")

    assert len(result.timeline) == 2
    assert result.timeline[0].is_idle
    assert result.timeline[0].pid is None
    assert result.timeline[0].start_time == 0
    assert result.timeline[0].end_time == 2

    assert not result.timeline[1].is_idle
    assert result.timeline[1].pid == 1
    assert result.timeline[1].start_time == 2
    assert result.timeline[1].end_time == 7


SAMPLE_COMPARISON_OUTPUT = """
Comparison completed successfully across 6 algorithm(s).

=== Scheduling Algorithm Comparison ===
Algorithm                    Avg Waiting  Avg Turnaround  Avg Response
----------------------------------------------------------------------
FCFS                                3.33            8.67          3.33
SJF                                 3.33            8.67          3.33
SRTF                                3.00            8.33          2.00
Priority                            3.33            8.67          3.33
Round Robin (q=2)                   6.00           11.33          1.00
MLFQ (q0=2, q1=4, q2=8)             5.33           10.67          1.00
"""


def test_parse_comparison_output():
    comp = parse_comparison_output(SAMPLE_COMPARISON_OUTPUT)
    assert len(comp.entries) == 6

    assert comp.entries[0].algorithm == "FCFS"
    assert pytest.approx(comp.entries[0].avg_waiting_time, 0.01) == 3.33
    assert pytest.approx(comp.entries[0].avg_turnaround_time, 0.01) == 8.67

    assert comp.entries[2].algorithm == "SRTF"
    assert pytest.approx(comp.entries[2].avg_response_time, 0.01) == 2.00

    assert "Round Robin (q=2)" in comp.entries[4].algorithm
    assert "MLFQ" in comp.entries[5].algorithm


def test_parse_scheduling_error():
    err_output = "Simulation failed with error: Time quantum must be strictly positive."
    with pytest.raises(RuntimeError) as exc_info:
        parse_scheduling_output(err_output, "Round Robin")
    assert "Time quantum must be strictly positive" in str(exc_info.value)


def test_generate_memory_stdin():
    from oscope_gui.backend.parser import generate_memory_stdin
    from oscope_gui.models.memory import (
        MemoryConfig,
        MemoryOperationInput,
        MemoryOperationType,
        MemoryStrategy,
    )

    config = MemoryConfig(strategy=MemoryStrategy.FIRST_FIT, total_memory=1000)
    operations = [
        MemoryOperationInput(op_type=MemoryOperationType.ALLOCATE, request_id=1, size=200, process_id=1),
        MemoryOperationInput(op_type=MemoryOperationType.ALLOCATE, request_id=2, size=300, process_id=2),
        MemoryOperationInput(op_type=MemoryOperationType.DEALLOCATE, request_id=1),
    ]

    stdin_data = generate_memory_stdin(config, operations)
    expected_lines = [
        "9",   # Memory Allocation choice
        "1",   # Strategy choice: 1 for First Fit
        "1000",# Total memory
        "3",   # Number of operations
        "1", "1", "200", "1", # Op 1: Alloc, req_id 1, size 200, pid 1
        "1", "2", "300", "2", # Op 2: Alloc, req_id 2, size 300, pid 2
        "2", "1",             # Op 3: Dealloc, req_id 1
        "5",   # Return to main menu
        "13",  # Exit choice
    ]
    assert stdin_data.strip().splitlines() == expected_lines


SAMPLE_MEMORY_OUTPUT = """
Allocation successful: Request ID 1 allocated at address 0 (200 bytes, Internal ID: 1)
Allocation successful: Request ID 2 allocated at address 200 (300 bytes, Internal ID: 2)
Deallocation successful: Request ID 1 (Internal ID: 1) freed

=== Memory Block Layout ===
Block   Start Address   Size (B)    Status      Alloc ID    PID
----------------------------------------------------------------------
1       0               200         Free        -           -
2       200             300         Allocated   2           2
3       500             500         Free        -           -

=== Memory Allocation Metrics ===
Total Memory:           1000 bytes
Allocated Memory:       300 bytes
Free Memory:            700 bytes
Largest Free Block:     500 bytes
External Fragmentation: 28.57% (0.29)
"""


def test_parse_memory_output():
    from oscope_gui.backend.parser import parse_memory_output

    result = parse_memory_output(SAMPLE_MEMORY_OUTPUT, "First Fit")
    assert result.strategy_name == "First Fit"
    assert result.total_memory == 1000

    # Operations log
    assert len(result.operations) == 3
    assert result.operations[0].success is True
    assert result.operations[0].start_address == 0
    assert result.operations[0].size == 200
    assert result.operations[2].op_type == "Deallocate"

    # Blocks layout
    assert len(result.blocks) == 3
    assert not result.blocks[0].is_allocated
    assert result.blocks[0].start_address == 0
    assert result.blocks[0].size == 200

    assert result.blocks[1].is_allocated
    assert result.blocks[1].start_address == 200
    assert result.blocks[1].size == 300
    assert result.blocks[1].process_id == 2

    # Metrics
    assert result.metrics.allocated_memory == 300
    assert result.metrics.free_memory == 700
    assert result.metrics.largest_free_block == 500
    assert pytest.approx(result.metrics.external_fragmentation, 0.01) == 0.29
    assert pytest.approx(result.metrics.utilization_percentage, 0.1) == 30.0


SAMPLE_MEMORY_COMPARISON_OUTPUT = """
Total Memory: 1000 bytes | Total Workload Operations: 3

=== Memory Allocation Strategy Comparison ===
Strategy      Attempts   Success  Failures  Success Rate Allocated (B)    Free (B)  Largest Free    Ext Frag
--------------------------------------------------------------------------------------------------
First Fit            3         3         0       100.00%           300         700           500      28.57%
Best Fit             3         3         0       100.00%           300         700           500      28.57%
Worst Fit            3         3         0       100.00%           300         700           500      28.57%
"""


def test_parse_memory_comparison_output():
    from oscope_gui.backend.parser import parse_memory_comparison_output

    comp = parse_memory_comparison_output(SAMPLE_MEMORY_COMPARISON_OUTPUT)
    assert comp.total_memory == 1000
    assert comp.total_operations == 3
    assert len(comp.entries) == 3

    assert comp.entries[0].strategy_name == "First Fit"
    assert comp.entries[0].attempts == 3
    assert comp.entries[0].success == 3
    assert comp.entries[0].failures == 0
    assert pytest.approx(comp.entries[0].success_rate, 0.01) == 1.0
    assert comp.entries[0].allocated_bytes == 300
    assert comp.entries[0].free_bytes == 700
    assert comp.entries[0].largest_free_bytes == 500
    assert pytest.approx(comp.entries[0].external_fragmentation, 0.01) == 0.2857


def test_generate_paging_stdin():
    from oscope_gui.backend.parser import generate_paging_stdin
    from oscope_gui.models.paging import PagingAlgorithm, PagingConfig

    config = PagingConfig(
        algorithm=PagingAlgorithm.FIFO,
        frame_count=3,
        reference_string=[7, 0, 1, 2, 0, 3],
    )
    stdin_data = generate_paging_stdin(config)
    expected_lines = [
        "8",                      # Main menu choice: Page replacement
        "1",                      # Sub-choice: 1 for FIFO
        "3",                      # Frame count
        "7 0 1 2 0 3",            # Reference string on one line
        "5",                      # Return to main menu
        "13",                     # Exit
    ]
    assert stdin_data.strip().splitlines() == expected_lines


SAMPLE_PAGING_OUTPUT = """
[FIFO Page Replacement Simulation]
Simulation completed successfully with 5 reference(s) across 3 frame(s).

=== Page Replacement Step-by-Step Execution ===
  Step    Page    Result    Evicted  Frames
-------------------------------------------------------
     1       7     Fault       None  [7, -1, -1]
     2       0     Fault       None  [7, 0, -1]
     3       1     Fault       None  [7, 0, 1]
     4       2     Fault          7  [2, 0, 1]
     5       0       Hit       None  [2, 0, 1]

=== Page Replacement Metrics ===
Total Page References: 5
Page Faults:           4
Page Hits:             1
Page-Fault Rate:       80.00% (0.80)
Page-Hit Rate:         20.00% (0.20)
"""


def test_parse_paging_output():
    from oscope_gui.backend.parser import parse_paging_output

    result = parse_paging_output(SAMPLE_PAGING_OUTPUT, "FIFO", frame_count=3)
    assert result.algorithm_name == "FIFO"
    assert result.frame_count == 3
    assert len(result.steps) == 5

    # Check Step 1 (Fault, empty frames)
    s1 = result.steps[0]
    assert s1.step_number == 1
    assert s1.page == 7
    assert s1.is_fault is True
    assert s1.evicted_page is None
    assert s1.frames == [7, -1, -1]

    # Check Step 4 (Fault, eviction of 7)
    s4 = result.steps[3]
    assert s4.step_number == 4
    assert s4.page == 2
    assert s4.is_fault is True
    assert s4.evicted_page == 7
    assert s4.frames == [2, 0, 1]

    # Check Step 5 (Hit, no eviction)
    s5 = result.steps[4]
    assert s5.step_number == 5
    assert s5.page == 0
    assert s5.is_fault is False
    assert s5.evicted_page is None

    # Check Metrics
    assert result.metrics.total_references == 5
    assert result.metrics.page_faults == 4
    assert result.metrics.page_hits == 1
    assert pytest.approx(result.metrics.fault_rate, 0.01) == 0.80
    assert pytest.approx(result.metrics.hit_rate, 0.01) == 0.20
    assert pytest.approx(result.metrics.fault_percentage, 0.1) == 80.0
    assert pytest.approx(result.metrics.hit_percentage, 0.1) == 20.0


SAMPLE_PAGING_COMPARISON_OUTPUT = """
Comparison completed successfully across 3 page replacement algorithm(s).

=== Page Replacement Algorithm Comparison ===
Frame Count: 3 | Total References: 13

Algorithm         References    Faults    Hits     Fault Rate       Hit Rate
----------------------------------------------------------------------------
FIFO                      13        10       3         76.92%         23.08%
LRU                       13         9       4         69.23%         30.77%
Optimal                   13         7       6         53.85%         46.15%
"""


def test_parse_paging_comparison_output():
    from oscope_gui.backend.parser import parse_paging_comparison_output

    comp = parse_paging_comparison_output(SAMPLE_PAGING_COMPARISON_OUTPUT)
    assert comp.frame_count == 3
    assert comp.total_references == 13
    assert len(comp.entries) == 3

    assert comp.entries[0].algorithm_name == "FIFO"
    assert comp.entries[0].page_faults == 10
    assert comp.entries[0].page_hits == 3
    assert pytest.approx(comp.entries[0].fault_rate, 0.01) == 0.7692

    assert comp.entries[1].algorithm_name == "LRU"
    assert comp.entries[1].page_faults == 9
    assert comp.entries[1].page_hits == 4

    assert comp.entries[2].algorithm_name == "Optimal"
    assert comp.entries[2].page_faults == 7
    assert comp.entries[2].page_hits == 6


SAMPLE_DEADLOCK_SAFETY_OUTPUT = """
=== Banker's Safety Analysis ===
System State:           SAFE
Analysis:               System is in a safe state.
Safe Execution Sequence: P0 -> P1 -> P2

Resource Matrices Summary:
Process Allocation      Max Claim       Need
           --------------------------------------------------------
P0      1 0             2 1             1 1             
P1      0 1             1 1             1 0             
P2      1 1             1 2             0 1             

Available Resources:    1 1 
"""

SAMPLE_DEADLOCK_REQUEST_OUTPUT = """
=== Resource Request Simulation ===
Requesting Process:     P0
Requested Resources:    [1, 0]
Allocation Decision:    GRANTED
Reason:                 Request granted. System remains in a safe state.
Resulting Safe Sequence: P0 -> P1 -> P2
"""

SAMPLE_DEADLOCK_DETECTION_OUTPUT = """
=== Deadlock Detection Analysis ===
Detection Result:       DEADLOCK DETECTED
Diagnostic Message:     Deadlock detected! Deadlocked processes: [P0, P1].
Deadlocked Processes:   P0, P1
"""


def test_generate_deadlock_stdin():
    from oscope_gui.backend.parser import generate_deadlock_stdin
    from oscope_gui.models.deadlock import DeadlockConfig, DeadlockMode

    cfg_safety = DeadlockConfig(
        mode=DeadlockMode.SAFETY,
        num_processes=3,
        num_resources=2,
        available=[1, 1],
        allocation=[[1, 0], [0, 1], [1, 1]],
        max_claim=[[2, 1], [1, 1], [1, 2]],
    )
    s = generate_deadlock_stdin(cfg_safety)
    expected_lines = [
        "11",   # Deadlock menu
        "1",    # Banker's safety
        "3",    # 3 procs
        "2",    # 2 resources
        "1 1",  # Avail
        "1 0",  # Alloc P0
        "0 1",  # Alloc P1
        "1 1",  # Alloc P2
        "2 1",  # Max P0
        "1 1",  # Max P1
        "1 2",  # Max P2
        "4",    # Return to main menu
        "13",   # Exit
    ]
    assert s.strip().splitlines() == expected_lines

    cfg_req = DeadlockConfig(
        mode=DeadlockMode.RESOURCE_REQUEST,
        num_processes=3,
        num_resources=2,
        available=[2, 2],
        allocation=[[1, 0], [0, 1], [1, 1]],
        max_claim=[[2, 1], [1, 1], [1, 2]],
        requesting_process_id=0,
        request_vector=[1, 0],
    )
    s_req = generate_deadlock_stdin(cfg_req)
    req_lines = s_req.strip().splitlines()
    assert req_lines[0] == "11"
    assert req_lines[1] == "2" # Resource request
    assert req_lines[-4] == "0" # Requesting proc
    assert req_lines[-3] == "1 0" # Req vector


def test_parse_deadlock_safety_output():
    from oscope_gui.backend.parser import parse_deadlock_safety_output
    from oscope_gui.models.deadlock import DeadlockConfig, DeadlockMode

    cfg = DeadlockConfig(
        mode=DeadlockMode.SAFETY,
        num_processes=3,
        num_resources=2,
        available=[1, 1],
        allocation=[[1, 0], [0, 1], [1, 1]],
        max_claim=[[2, 1], [1, 1], [1, 2]],
    )
    res = parse_deadlock_safety_output(SAMPLE_DEADLOCK_SAFETY_OUTPUT, cfg)
    assert res.is_safe is True
    assert res.safe_sequence == [0, 1, 2]
    assert res.safe_sequence_str == "P0 -> P1 -> P2"
    assert res.blocked_processes == []
    assert "safe state" in res.message


def test_parse_deadlock_request_output():
    from oscope_gui.backend.parser import parse_deadlock_request_output
    from oscope_gui.models.deadlock import DeadlockConfig, DeadlockMode

    cfg = DeadlockConfig(
        mode=DeadlockMode.RESOURCE_REQUEST,
        num_processes=3,
        num_resources=2,
        available=[2, 2],
        allocation=[[1, 0], [0, 1], [1, 1]],
        max_claim=[[2, 1], [1, 1], [1, 2]],
        requesting_process_id=0,
        request_vector=[1, 0],
    )
    res = parse_deadlock_request_output(SAMPLE_DEADLOCK_REQUEST_OUTPUT, cfg)
    assert res.granted is True
    assert res.process_id == 0
    assert res.requested == [1, 0]
    assert res.safe_sequence == [0, 1, 2]
    assert res.status_code == "Granted"
    assert res.available == [1, 2]
    assert res.allocation[0] == [2, 0]


def test_parse_deadlock_detection_output():
    from oscope_gui.backend.parser import parse_deadlock_detection_output
    from oscope_gui.models.deadlock import DeadlockConfig, DeadlockMode

    cfg = DeadlockConfig(
        mode=DeadlockMode.DETECTION,
        num_processes=2,
        num_resources=1,
        available=[0],
        allocation=[[1], [1]],
        request_matrix=[[1], [1]],
    )
    res = parse_deadlock_detection_output(SAMPLE_DEADLOCK_DETECTION_OUTPUT, cfg)
    assert res.is_deadlocked is True
    assert res.deadlocked_processes == [0, 1]
    assert res.deadlocked_str == "P0, P1"
    assert "Deadlock detected" in res.message



