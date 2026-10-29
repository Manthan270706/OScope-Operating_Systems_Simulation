import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.address_translation import (
    AddressTranslationConfig,
    AddressTranslationSimulationResultModel,
    DemandPagingResultModel,
    DemandPagingStepModel,
    PageTableEntryModel,
    ThrashingPointModel,
    ThrashingResultModel,
    TranslationResultModel,
)
from ..models.deadlock import (
    DeadlockConfig,
    DeadlockDetectionResultModel,
    DeadlockMode,
    DeadlockRequestResultModel,
    DeadlockSafetyResultModel,
)
from ..models.process_lifecycle import (
    ProcessInstanceModel,
    ProcessLifecycleConfig,
    ProcessLifecycleSimulationResultModel,
    ProcessLifecycleState,
    ProcessTransitionModel,
)
from ..models.disk import (
    DiskAlgorithm,
    DiskComparisonEntryModel,
    DiskComparisonResultModel,
    DiskConfig,
    DiskDirection,
    DiskSchedulingResultModel,
    DiskStepModel,
)
from ..models.filesystem import (
    AllocationTraceModel,
    FileInodeModel,
    FilesystemAllocationStrategy,
    FilesystemConfig,
    FilesystemOperationInput,
    FilesystemOperationType,
    FilesystemPreset,
    FilesystemSimulationResultModel,
    FilesystemStatusModel,
)
from ..models.host_monitor import (
    HostCpuModel,
    HostDiskIoModel,
    HostMemoryModel,
    HostMonitoringSnapshotModel,
    HostProcessModel,
    HostSystemModel,
)
from ..models.linux_experiments import (
    FifoIpcResultModel,
    LinuxExperimentCategory,
    LinuxExperimentsResultModel,
    MessageQueueIpcResultModel,
    MutexSyncResultModel,
    OrphanResultModel,
    PetersonResultModel,
    PipeIpcResultModel,
    PosixSemaphoreResultModel,
    ProcessExecResultModel,
    ProducerConsumerResultModel,
    SharedMemoryIpcResultModel,
    ThreadCreationResultModel,
    ZombieResultModel,
)
from ..models.memory import (
    MemoryBlockModel,
    MemoryComparisonEntryModel,
    MemoryComparisonResultModel,
    MemoryConfig,
    MemoryMetricsModel,
    MemoryOperationInput,
    MemoryOperationResultModel,
    MemoryOperationType,
    MemorySimulationResultModel,
    MemoryStrategy,
)
from ..models.paging import (
    PagingAlgorithm,
    PagingComparisonEntryModel,
    PagingComparisonResultModel,
    PagingConfig,
    PagingMetricsModel,
    PagingSimulationResultModel,
    PagingStepModel,
)
from ..models.scheduling import (
    AlgorithmConfig,
    AlgorithmType,
    AverageMetricsModel,
    ComparisonEntryModel,
    ExecutionSegmentModel,
    ProcessInput,
    ProcessResultModel,
    SchedulingComparisonResultModel,
    SchedulingResultModel,
)



def generate_scheduling_stdin(config: AlgorithmConfig, processes: List[ProcessInput]) -> str:
    """Generate exact line-delimited stdin sequence for oscope interactive CLI."""
    lines: List[str] = []

    # Main menu choice (1-7)
    choice = config.algorithm.menu_choice
    lines.append(str(choice))

    # Algorithm specific parameter prompts
    if config.algorithm == AlgorithmType.ROUND_ROBIN:
        lines.append(str(config.rr_quantum))
    elif config.algorithm == AlgorithmType.MLFQ:
        lines.append(str(config.mlfq_q0))
        lines.append(str(config.mlfq_q1))
        lines.append(str(config.mlfq_q2))
    elif config.algorithm == AlgorithmType.COMPARE_ALL:
        # Compare All prompts for RR quantum, then MLFQ Q0, Q1, Q2
        lines.append(str(config.rr_quantum))
        lines.append(str(config.mlfq_q0))
        lines.append(str(config.mlfq_q1))
        lines.append(str(config.mlfq_q2))

    # Process count
    lines.append(str(len(processes)))

    # Each process parameters: PID, Arrival, Burst, Priority
    for p in processes:
        lines.append(str(p.pid))
        lines.append(str(p.arrival_time))
        lines.append(str(p.burst_time))
        lines.append(str(p.priority))

    # Exit choice to terminate interactive CLI cleanly
    lines.append("13")

    return "\n".join(lines) + "\n"


def parse_scheduling_output(stdout: str, algorithm_name: str) -> SchedulingResultModel:
    """Parse single-algorithm simulation output from C++ backend."""
    # Check for backend errors
    fail_match = re.search(r"Simulation failed with error:\s*(.*)", stdout)
    if fail_match:
        raise RuntimeError(f"C++ simulation error: {fail_match.group(1).strip()}")

    # Extract total scheduled processes and segments count
    summary_match = re.search(
        r"Scheduled\s+(\d+)\s+process\(es\)\s+across\s+(\d+)\s+timeline\s+execution\s+segment\(s\)",
        stdout,
    )
    total_processes = int(summary_match.group(1)) if summary_match else 0

    # Extract duration interval: Total Simulation Interval: [start -> end] (Duration: D)
    interval_match = re.search(
        r"Total Simulation Interval:\s*\[(\d+)\s*->\s*(\d+)\]\s*\(Duration:\s*(\d+)\)",
        stdout,
    )
    total_duration = int(interval_match.group(3)) if interval_match else 0

    # Parse execution segments
    # Format 1: [0 -> 5] Process PID 1
    # Format 2: [0 -> 5] IDLE (CPU Idle)
    timeline: List[ExecutionSegmentModel] = []
    seg_regex = re.compile(
        r"^\s*\[(\d+)\s*->\s*(\d+)\]\s*(?:Process\s+PID\s+(\d+)|IDLE\s*\(CPU Idle\))",
        re.MULTILINE,
    )
    for match in seg_regex.finditer(stdout):
        start = int(match.group(1))
        end = int(match.group(2))
        pid_str = match.group(3)
        if pid_str is not None:
            timeline.append(ExecutionSegmentModel(start_time=start, end_time=end, pid=int(pid_str), is_idle=False))
        else:
            timeline.append(ExecutionSegmentModel(start_time=start, end_time=end, pid=None, is_idle=True))

    # Parse Process Metrics Table
    # Table header is:
    # PID   Arrival     Burst   Completion   Turnaround    Waiting   Response
    # --------------------------------------------------------------------------
    #   1         0         5            5            5          0          0
    process_results: List[ProcessResultModel] = []
    table_section = re.search(
        r"=== Process Metrics Table ===\s*\n\s*PID[^\n]+\n\-+\n([\s\S]*?)(?:\n===|$)",
        stdout,
    )
    if table_section:
        table_lines = table_section.group(1).strip().splitlines()
        for line in table_lines:
            tokens = line.split()
            if len(tokens) >= 7 and all(t.replace("-", "").isdigit() for t in tokens[:7]):
                try:
                    process_results.append(
                        ProcessResultModel(
                            pid=int(tokens[0]),
                            arrival_time=int(tokens[1]),
                            burst_time=int(tokens[2]),
                            completion_time=int(tokens[3]),
                            turnaround_time=int(tokens[4]),
                            waiting_time=int(tokens[5]),
                            response_time=int(tokens[6]),
                        )
                    )
                except ValueError:
                    continue

    # Parse Average Metrics
    avg_waiting = 0.0
    avg_turnaround = 0.0
    avg_response = 0.0

    w_match = re.search(r"Average Waiting Time:\s*([\d.]+)", stdout)
    if w_match:
        avg_waiting = float(w_match.group(1))

    t_match = re.search(r"Average Turnaround Time:\s*([\d.]+)", stdout)
    if t_match:
        avg_turnaround = float(t_match.group(1))

    r_match = re.search(r"Average Response Time:\s*([\d.]+)", stdout)
    if r_match:
        avg_response = float(r_match.group(1))

    averages = AverageMetricsModel(
        average_waiting_time=avg_waiting,
        average_turnaround_time=avg_turnaround,
        average_response_time=avg_response,
    )

    return SchedulingResultModel(
        algorithm_name=algorithm_name,
        total_processes=total_processes or len(process_results),
        timeline=timeline,
        process_results=process_results,
        averages=averages,
        total_duration=total_duration,
        raw_output=stdout,
    )


def parse_comparison_output(stdout: str) -> SchedulingComparisonResultModel:
    """Parse multi-algorithm comparison table from C++ backend."""
    entries: List[ComparisonEntryModel] = []

    # Table format:
    # Algorithm                    Avg Waiting  Avg Turnaround  Avg Response
    # ----------------------------------------------------------------------
    # FCFS                                3.33            8.67          3.33
    # ...
    table_section = re.search(
        r"=== Scheduling Algorithm Comparison ===\s*\n\s*Algorithm[^\n]+\n\-+\n([\s\S]*?)(?:\n\n|\n===|$)",
        stdout,
    )
    if table_section:
        table_lines = table_section.group(1).strip().splitlines()
        for line in table_lines:
            tokens = line.strip().rsplit(maxsplit=3)
            if len(tokens) == 4:
                algo_name = tokens[0].strip()
                try:
                    w = float(tokens[1])
                    t = float(tokens[2])
                    r = float(tokens[3])
                    entries.append(
                        ComparisonEntryModel(
                            algorithm=algo_name,
                            avg_waiting_time=w,
                            avg_turnaround_time=t,
                            avg_response_time=r,
                        )
                    )
                except ValueError:
                    continue

    return SchedulingComparisonResultModel(entries=entries, raw_output=stdout)


def generate_memory_stdin(config: MemoryConfig, operations: List[MemoryOperationInput]) -> str:
    """Generate exact line-delimited stdin sequence for oscope memory allocation interactive CLI."""
    lines: List[str] = []

    # Main menu choice: 9 for Memory Allocation
    lines.append("9")

    # Memory strategy choice: 1 (First Fit), 2 (Best Fit), 3 (Worst Fit), 4 (Compare All)
    lines.append(str(config.strategy.menu_choice))

    # Total memory size (bytes)
    lines.append(str(config.total_memory))

    # Number of operations
    lines.append(str(len(operations)))

    # For each operation:
    for op in operations:
        if op.op_type == MemoryOperationType.ALLOCATE:
            lines.append("1")  # 1 for Allocate
            lines.append(str(op.request_id))
            lines.append(str(op.size))
            lines.append(str(op.process_id if op.process_id is not None else -1))
        else:
            lines.append("2")  # 2 for Deallocate
            lines.append(str(op.request_id))

    # Return to main menu choice: 5
    lines.append("5")

    # Exit choice to terminate interactive CLI cleanly: 13
    lines.append("13")

    return "\n".join(lines) + "\n"


def parse_memory_output(stdout: str, strategy_name: str) -> MemorySimulationResultModel:
    """Parse single-strategy memory allocation output from C++ backend."""
    # Check for backend errors
    fail_match = re.search(r"Simulation failed with error:\s*(.*)", stdout)
    if fail_match:
        raise RuntimeError(f"C++ memory simulation error: {fail_match.group(1).strip()}")

    # Parse total memory size
    total_mem_match = re.search(r"Total Memory:\s*(\d+(?:\.\d+)?)\s*bytes", stdout)
    total_memory = int(float(total_mem_match.group(1))) if total_mem_match else 0

    # Parse operation log lines
    operations: List[MemoryOperationResultModel] = []
    op_num = 1

    for line in stdout.splitlines():
        line_s = line.strip()
        # Allocation successful
        m_alloc_ok = re.search(
            r"Allocation successful:\s*Request ID\s*(\d+)\s*allocated at address\s*(\d+)\s*\((\d+)\s*bytes,\s*Internal ID:\s*(\d+)\)",
            line_s,
        )
        if m_alloc_ok:
            req_id = int(m_alloc_ok.group(1))
            addr = int(m_alloc_ok.group(2))
            sz = int(m_alloc_ok.group(3))
            int_id = int(m_alloc_ok.group(4))
            operations.append(
                MemoryOperationResultModel(
                    op_number=op_num,
                    op_type="Allocate",
                    request_id=req_id,
                    success=True,
                    message=f"Allocated {sz} B at address {addr} (Internal ID: {int_id})",
                    start_address=addr,
                    size=sz,
                    internal_id=int_id,
                )
            )
            op_num += 1
            continue

        # Allocation failed
        m_alloc_fail = re.search(
            r"Allocation failed(?: for request ID\s*(\d+))?:\s*(.*)",
            line_s,
        )
        if m_alloc_fail:
            req_id = int(m_alloc_fail.group(1)) if m_alloc_fail.group(1) else op_num
            reason = m_alloc_fail.group(2).strip()
            operations.append(
                MemoryOperationResultModel(
                    op_number=op_num,
                    op_type="Allocate",
                    request_id=req_id,
                    success=False,
                    message=f"Allocation failed: {reason}",
                )
            )
            op_num += 1
            continue

        # Deallocation successful
        m_dealloc_ok = re.search(
            r"Deallocation successful:\s*Request ID\s*(\d+)\s*(?:\(Internal ID:\s*(\d+)\)\s*)?freed",
            line_s,
        )
        if m_dealloc_ok:
            req_id = int(m_dealloc_ok.group(1))
            int_id = int(m_dealloc_ok.group(2)) if m_dealloc_ok.group(2) else None
            operations.append(
                MemoryOperationResultModel(
                    op_number=op_num,
                    op_type="Deallocate",
                    request_id=req_id,
                    success=True,
                    message=f"Request ID {req_id} freed successfully",
                    internal_id=int_id,
                )
            )
            op_num += 1
            continue

        # Deallocation failed
        m_dealloc_fail = re.search(
            r"Deallocation failed:\s*(.*)",
            line_s,
        )
        if m_dealloc_fail:
            reason = m_dealloc_fail.group(1).strip()
            operations.append(
                MemoryOperationResultModel(
                    op_number=op_num,
                    op_type="Deallocate",
                    request_id=op_num,
                    success=False,
                    message=f"Deallocation failed: {reason}",
                )
            )
            op_num += 1
            continue

    # Parse Memory Block Layout
    # Block   Start Address   Size (B)    Status      Alloc ID    PID
    # ----------------------------------------------------------------------
    # 1       0               200         Free        -           -
    # 2       200             300         Allocated   2           2
    blocks: List[MemoryBlockModel] = []
    block_section = re.search(
        r"=== Memory Block Layout ===\s*\n\s*Block[^\n]+\n\-+\n([\s\S]*?)(?:\n\n|\n===|$)",
        stdout,
    )
    if block_section:
        for b_line in block_section.group(1).strip().splitlines():
            tokens = b_line.strip().split()
            if len(tokens) >= 4 and tokens[0].isdigit():
                try:
                    b_idx = int(tokens[0])
                    start_addr = int(tokens[1])
                    b_size = int(tokens[2])
                    status = tokens[3]
                    is_alloc = (status.lower() == "allocated")

                    alloc_id = None
                    if len(tokens) >= 5 and tokens[4] != "-" and tokens[4].isdigit():
                        alloc_id = int(tokens[4])

                    pid = None
                    if len(tokens) >= 6 and tokens[5] != "-" and tokens[5].isdigit():
                        pid = int(tokens[5])

                    blocks.append(
                        MemoryBlockModel(
                            block_index=b_idx,
                            start_address=start_addr,
                            size=b_size,
                            is_allocated=is_alloc,
                            allocation_id=alloc_id,
                            process_id=pid,
                        )
                    )
                except ValueError:
                    continue

    # Parse Memory Allocation Metrics
    # Total Memory:           1000 bytes
    # Allocated Memory:       300 bytes
    # Free Memory:            700 bytes
    # Largest Free Block:     500 bytes
    # External Fragmentation: 28.57% (0.29)
    alloc_mem_match = re.search(r"Allocated Memory:\s*(\d+(?:\.\d+)?)\s*bytes", stdout)
    free_mem_match = re.search(r"Free Memory:\s*(\d+(?:\.\d+)?)\s*bytes", stdout)
    largest_free_match = re.search(r"Largest Free Block:\s*(\d+(?:\.\d+)?)\s*bytes", stdout)
    ext_frag_match = re.search(r"External Fragmentation:\s*([\d\.]+)%\s*\(([\d\.]+)\)", stdout)

    metrics = MemoryMetricsModel(
        total_memory=total_memory,
        allocated_memory=int(float(alloc_mem_match.group(1))) if alloc_mem_match else 0,
        free_memory=int(float(free_mem_match.group(1))) if free_mem_match else 0,
        largest_free_block=int(float(largest_free_match.group(1))) if largest_free_match else 0,
        external_fragmentation=float(ext_frag_match.group(2)) if ext_frag_match else 0.0,
    )

    return MemorySimulationResultModel(
        strategy_name=strategy_name,
        total_memory=total_memory,
        operations=operations,
        blocks=blocks,
        metrics=metrics,
        raw_output=stdout,
    )


def parse_memory_comparison_output(stdout: str) -> MemoryComparisonResultModel:
    """Parse multi-strategy memory comparison table from C++ backend."""
    # Check for backend errors
    fail_match = re.search(r"Comparison failed with error:\s*(.*)", stdout)
    if fail_match:
        raise RuntimeError(f"C++ memory comparison error: {fail_match.group(1).strip()}")

    # Extract header info
    # Total Memory: 1000 bytes | Total Workload Operations: 3
    hdr_match = re.search(r"Total Memory:\s*(\d+)\s*bytes\s*\|\s*Total Workload Operations:\s*(\d+)", stdout)
    total_mem = int(hdr_match.group(1)) if hdr_match else 0
    total_ops = int(hdr_match.group(2)) if hdr_match else 0

    entries: List[MemoryComparisonEntryModel] = []

    # Strategy      Attempts   Success  Failures  Success Rate Allocated (B)    Free (B)  Largest Free    Ext Frag
    # --------------------------------------------------------------------------------------------------
    # First Fit            2         2         0       100.00%           300         700           500      28.57%
    comp_section = re.search(
        r"=== Memory Allocation Strategy Comparison ===[\s\S]*?\n\-+\n([\s\S]*?)(?:\n\n|\n===|$)",
        stdout,
    )
    if comp_section:
        for line in comp_section.group(1).strip().splitlines():
            line_str = line.strip()
            tokens = line_str.rsplit(maxsplit=8)
            if len(tokens) == 9:
                strat_name = tokens[0].strip()
                try:
                    attempts = int(tokens[1])
                    success = int(tokens[2])
                    failures = int(tokens[3])
                    s_rate_str = tokens[4].replace("%", "").strip()
                    success_rate = float(s_rate_str) / 100.0
                    allocated = int(float(tokens[5]))
                    free_b = int(float(tokens[6]))
                    largest_f = int(float(tokens[7]))
                    ext_f_str = tokens[8].replace("%", "").strip()
                    ext_frag = float(ext_f_str) / 100.0

                    entries.append(
                        MemoryComparisonEntryModel(
                            strategy_name=strat_name,
                            attempts=attempts,
                            success=success,
                            failures=failures,
                            success_rate=success_rate,
                            allocated_bytes=allocated,
                            free_bytes=free_b,
                            largest_free_bytes=largest_f,
                            external_fragmentation=ext_frag,
                        )
                    )
                except ValueError:
                    continue

    return MemoryComparisonResultModel(
        total_memory=total_mem,
        total_operations=total_ops,
        entries=entries,
        raw_output=stdout,
    )


def generate_paging_stdin(config: PagingConfig) -> str:
    """Generate exact line-delimited stdin sequence for oscope paging interactive CLI."""
    lines: List[str] = []

    # Main menu choice: 8 for Page Replacement (Paging)
    lines.append("8")

    # Paging algorithm choice: 1 (FIFO), 2 (LRU), 3 (Optimal), 4 (Compare All)
    lines.append(str(config.algorithm.menu_choice))

    # Number of frames (positive integer)
    lines.append(str(config.frame_count))

    # Reference string on a single line (space-separated integers)
    ref_line = " ".join(str(p) for p in config.reference_string)
    lines.append(ref_line)

    # Return to main menu choice: 5
    lines.append("5")

    # Exit choice to terminate interactive CLI cleanly: 13
    lines.append("13")

    return "\n".join(lines) + "\n"


def parse_paging_output(
    stdout: str,
    algorithm_name: str,
    frame_count: int,
    reference_string: Optional[List[int]] = None,
) -> PagingSimulationResultModel:
    """Parse single page replacement algorithm output from C++ backend."""
    # Check for backend errors
    fail_match = re.search(r"Simulation failed with error:\s*(.*)", stdout)
    if fail_match:
        raise RuntimeError(f"C++ paging simulation error: {fail_match.group(1).strip()}")

    ref_str = list(reference_string) if reference_string else []

    # Parse Step-by-Step Table
    #   Step    Page    Result    Evicted  Frames
    # -------------------------------------------------------
    #      1       7     Fault       None  [7, -1, -1]
    #      4       2     Fault          7  [2, 0, 1]
    steps: List[PagingStepModel] = []

    step_section = re.search(
        r"=== Page Replacement Step-by-Step Execution ===\s*\n\s*Step[^\n]+\n\-+\n([\s\S]*?)(?:\n\n|\n===|$)",
        stdout,
    )
    if step_section:
        for line in step_section.group(1).strip().splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            # Regex to match step lines
            # Format: <step> <page> <Result: Fault|Hit> <Evicted: None|int> [frame_0, frame_1, ...]
            m = re.match(r"^(\d+)\s+(\d+)\s+(Fault|Hit)\s+(None|\d+)\s+\[(.*)\]$", line_str)
            if m:
                step_num = int(m.group(1))
                page_num = int(m.group(2))
                is_fault = (m.group(3) == "Fault")
                evicted_str = m.group(4)
                evicted_page = int(evicted_str) if evicted_str != "None" else None

                frames_raw = m.group(5).strip()
                frames: List[int] = []
                if frames_raw:
                    for f_token in frames_raw.split(","):
                        f_token = f_token.strip()
                        if f_token:
                            try:
                                frames.append(int(f_token))
                            except ValueError:
                                pass

                steps.append(
                    PagingStepModel(
                        step_number=step_num,
                        page=page_num,
                        is_fault=is_fault,
                        frames=frames,
                        evicted_page=evicted_page,
                    )
                )

    if not ref_str and steps:
        ref_str = [s.page for s in steps]

    # Parse Metrics
    # Total Page References: 13
    # Page Faults:           10
    # Page Hits:             3
    # Page-Fault Rate:       76.92% (0.77)
    # Page-Hit Rate:         23.08% (0.23)
    total_refs_match = re.search(r"Total Page References:\s*(\d+)", stdout)
    faults_match = re.search(r"Page Faults:\s*(\d+)", stdout)
    hits_match = re.search(r"Page Hits:\s*(\d+)", stdout)
    fault_rate_match = re.search(r"Page-Fault Rate:\s*[\d\.]+%\s*\(([\d\.]+)\)", stdout)
    hit_rate_match = re.search(r"Page-Hit Rate:\s*[\d\.]+%\s*\(([\d\.]+)\)", stdout)

    total_refs = int(total_refs_match.group(1)) if total_refs_match else len(steps)
    faults = int(faults_match.group(1)) if faults_match else sum(1 for s in steps if s.is_fault)
    hits = int(hits_match.group(1)) if hits_match else sum(1 for s in steps if not s.is_fault)

    f_rate = float(fault_rate_match.group(1)) if fault_rate_match else (faults / total_refs if total_refs > 0 else 0.0)
    h_rate = float(hit_rate_match.group(1)) if hit_rate_match else (hits / total_refs if total_refs > 0 else 0.0)

    metrics = PagingMetricsModel(
        total_references=total_refs,
        page_faults=faults,
        page_hits=hits,
        fault_rate=f_rate,
        hit_rate=h_rate,
    )

    return PagingSimulationResultModel(
        algorithm_name=algorithm_name,
        frame_count=frame_count,
        reference_string=ref_str,
        steps=steps,
        metrics=metrics,
        raw_output=stdout,
    )


def parse_paging_comparison_output(stdout: str) -> PagingComparisonResultModel:
    """Parse multi-algorithm page replacement comparison table from C++ backend."""
    # Check for backend errors
    fail_match = re.search(r"Comparison failed with error:\s*(.*)", stdout)
    if fail_match:
        raise RuntimeError(f"C++ paging comparison error: {fail_match.group(1).strip()}")

    # Header info: Frame Count: 3 | Total References: 13
    hdr_match = re.search(r"Frame Count:\s*(\d+)\s*\|\s*Total References:\s*(\d+)", stdout)
    frame_count = int(hdr_match.group(1)) if hdr_match else 0
    total_refs = int(hdr_match.group(2)) if hdr_match else 0

    entries: List[PagingComparisonEntryModel] = []

    # Table:
    # Algorithm         References    Faults    Hits     Fault Rate       Hit Rate
    # ----------------------------------------------------------------------------
    # FIFO                      13        10       3         76.92%         23.08%
    # LRU                       13         9       4         69.23%         30.77%
    # Optimal                   13         7       6         53.85%         46.15%
    comp_section = re.search(
        r"=== Page Replacement Algorithm Comparison ===[\s\S]*?\n\-+\n([\s\S]*?)(?:\n\n|\n===|$)",
        stdout,
    )
    if comp_section:
        for line in comp_section.group(1).strip().splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            tokens = line_str.rsplit(maxsplit=5)
            if len(tokens) == 6:
                algo_name = tokens[0].strip()
                try:
                    refs = int(tokens[1])
                    faults = int(tokens[2])
                    hits = int(tokens[3])
                    f_rate = float(tokens[4].replace("%", "").strip()) / 100.0
                    h_rate = float(tokens[5].replace("%", "").strip()) / 100.0

                    entries.append(
                        PagingComparisonEntryModel(
                            algorithm_name=algo_name,
                            total_references=refs,
                            page_faults=faults,
                            page_hits=hits,
                            fault_rate=f_rate,
                            hit_rate=h_rate,
                        )
                    )
                except ValueError:
                    continue

    return PagingComparisonResultModel(
        frame_count=frame_count,
        total_references=total_refs,
        entries=entries,
        raw_output=stdout,
    )


# ============================================================================
# Deadlock Management Parsers and Stdin Generators
# ============================================================================


def generate_deadlock_stdin(config: DeadlockConfig) -> str:
    """Generate exact stdin command stream for C++ interactive deadlock CLI."""
    lines: List[str] = []
    # Main menu choice 11 (Deadlock Management)
    lines.append("11")

    # Sub-menu choice (1: Safety, 2: Request, 3: Detection)
    lines.append(str(config.mode.cli_choice))

    if config.mode == DeadlockMode.SAFETY:
        lines.append(str(config.num_processes))
        lines.append(str(config.num_resources))
        lines.append(" ".join(str(x) for x in config.available))
        for row in config.allocation:
            lines.append(" ".join(str(x) for x in row))
        for row in config.max_claim:
            lines.append(" ".join(str(x) for x in row))
    elif config.mode == DeadlockMode.RESOURCE_REQUEST:
        lines.append(str(config.num_processes))
        lines.append(str(config.num_resources))
        lines.append(" ".join(str(x) for x in config.available))
        for row in config.allocation:
            lines.append(" ".join(str(x) for x in row))
        for row in config.max_claim:
            lines.append(" ".join(str(x) for x in row))
        lines.append(str(config.requesting_process_id))
        lines.append(" ".join(str(x) for x in config.request_vector))
    elif config.mode == DeadlockMode.DETECTION:
        lines.append(str(config.num_processes))
        lines.append(str(config.num_resources))
        lines.append(" ".join(str(x) for x in config.available))
        for row in config.allocation:
            lines.append(" ".join(str(x) for x in row))
        for row in config.request_matrix:
            lines.append(" ".join(str(x) for x in row))

    # Return to main menu: 4
    lines.append("4")
    # Exit: 13
    lines.append("13")

    return "\n".join(lines) + "\n"


def parse_deadlock_safety_output(stdout: str, config: DeadlockConfig) -> DeadlockSafetyResultModel:
    """Parse Banker's Safety Analysis output from C++ backend."""
    # Check for validation or runtime errors
    if "Validation error:" in stdout:
        err_match = re.search(r"Validation error:\s*(.*?)(?:\nPlease|\n===|$)", stdout, re.DOTALL)
        err_text = err_match.group(1).strip() if err_match else "Backend reported invalid matrix dimensions or claims."
        raise ValueError(f"C++ Validation Error: {err_text}")

    # Check for System State
    state_match = re.search(r"System State:\s*(SAFE|UNSAFE)", stdout)
    if not state_match:
        raise RuntimeError("C++ output does not contain expected 'System State: SAFE/UNSAFE'.")

    is_safe = state_match.group(1).upper() == "SAFE"

    # Extract Analysis / message
    msg_match = re.search(r"Analysis:\s*(.*?)(?:\nSafe|\nBlocked|\nResource|\n=|$)", stdout)
    message = msg_match.group(1).strip() if msg_match else ("System is in a safe state." if is_safe else "System is in an unsafe state.")

    # Safe sequence: e.g. "Safe Execution Sequence: P0 -> P1 -> P2"
    safe_sequence: List[int] = []
    if is_safe:
        seq_match = re.search(r"Safe Execution Sequence:\s*(.*)", stdout)
        if seq_match:
            seq_str = seq_match.group(1).strip()
            for p_match in re.finditer(r"P(\d+)", seq_str):
                safe_sequence.append(int(p_match.group(1)))

    # Blocked processes: e.g. "Blocked Processes: P0, P1, P2"
    blocked_processes: List[int] = []
    if not is_safe:
        blocked_match = re.search(r"Blocked Processes:\s*(.*)", stdout)
        if blocked_match:
            b_str = blocked_match.group(1).strip()
            for p_match in re.finditer(r"P(\d+)", b_str):
                blocked_processes.append(int(p_match.group(1)))
        else:
            # If not explicitly printed, all processes that didn't finish
            blocked_processes = [i for i in range(config.num_processes) if i not in safe_sequence]

    need = config.compute_need()

    return DeadlockSafetyResultModel(
        is_safe=is_safe,
        safe_sequence=safe_sequence,
        blocked_processes=blocked_processes,
        message=message,
        num_processes=config.num_processes,
        num_resources=config.num_resources,
        available=list(config.available),
        allocation=[list(r) for r in config.allocation],
        max_claim=[list(r) for r in config.max_claim],
        need=need,
        raw_output=stdout,
    )


def parse_deadlock_request_output(stdout: str, config: DeadlockConfig) -> DeadlockRequestResultModel:
    """Parse Banker's Resource Request Simulation output from C++ backend."""
    # Check decision: GRANTED vs DENIED
    decision_match = re.search(r"Allocation Decision:\s*(GRANTED|DENIED)", stdout)
    if not decision_match:
        raise RuntimeError("C++ output does not contain expected 'Allocation Decision: GRANTED/DENIED'.")

    granted = decision_match.group(1).upper() == "GRANTED"

    # Extract Reason / message
    reason_match = re.search(r"Reason:\s*(.*?)(?:\nResulting|\nOriginal|\n===|$)", stdout)
    message = reason_match.group(1).strip() if reason_match else ("Request granted." if granted else "Request denied.")

    # Status code
    if granted:
        status_code = "Granted"
    elif "exceeds its maximum declared need" in message or "exceeds" in message and "need" in message:
        status_code = "DeniedExceedsNeed"
    elif "exceeds available" in message or "must wait" in message:
        status_code = "DeniedExceedsAvailable"
    elif "unsafe state" in message:
        status_code = "DeniedUnsafeState"
    else:
        status_code = "Denied"

    # Safe sequence if granted
    safe_sequence: List[int] = []
    if granted:
        seq_match = re.search(r"Resulting Safe Sequence:\s*(.*)", stdout)
        if seq_match:
            seq_str = seq_match.group(1).strip()
            for p_match in re.finditer(r"P(\d+)", seq_str):
                safe_sequence.append(int(p_match.group(1)))

    # Process and request vector
    proc_id = config.requesting_process_id
    req_vec = list(config.request_vector)

    # Resulting state
    resulting_available = list(config.available)
    resulting_allocation = [list(r) for r in config.allocation]
    resulting_need = config.compute_need()

    if granted:
        for j in range(config.num_resources):
            resulting_available[j] -= req_vec[j]
            resulting_allocation[proc_id][j] += req_vec[j]
            resulting_need[proc_id][j] = max(0, resulting_need[proc_id][j] - req_vec[j])

    return DeadlockRequestResultModel(
        process_id=proc_id,
        requested=req_vec,
        granted=granted,
        status_code=status_code,
        message=message,
        safe_sequence=safe_sequence,
        num_processes=config.num_processes,
        num_resources=config.num_resources,
        available=resulting_available,
        allocation=resulting_allocation,
        max_claim=[list(r) for r in config.max_claim],
        need=resulting_need,
        raw_output=stdout,
    )


def parse_deadlock_detection_output(stdout: str, config: DeadlockConfig) -> DeadlockDetectionResultModel:
    """Parse Deadlock Detection Analysis output from C++ backend."""
    det_match = re.search(r"Detection Result:\s*(DEADLOCK DETECTED|NO DEADLOCK)", stdout)
    if not det_match:
        raise RuntimeError("C++ output does not contain expected 'Detection Result: DEADLOCK DETECTED/NO DEADLOCK'.")

    is_deadlocked = det_match.group(1).upper() == "DEADLOCK DETECTED"

    msg_match = re.search(r"Diagnostic Message:\s*(.*?)(?:\nDeadlocked|\nExecution|\n===|$)", stdout)
    message = msg_match.group(1).strip() if msg_match else ("Deadlock detected!" if is_deadlocked else "No deadlock detected.")

    deadlocked_processes: List[int] = []
    if is_deadlocked:
        dl_match = re.search(r"Deadlocked Processes:\s*(.*)", stdout)
        if dl_match:
            dl_str = dl_match.group(1).strip()
            for p_match in re.finditer(r"P(\d+)", dl_str):
                deadlocked_processes.append(int(p_match.group(1)))

    finished_processes = [i for i in range(config.num_processes) if i not in deadlocked_processes]

    return DeadlockDetectionResultModel(
        is_deadlocked=is_deadlocked,
        deadlocked_processes=deadlocked_processes,
        finished_processes=finished_processes,
        message=message,
        num_processes=config.num_processes,
        num_resources=config.num_resources,
        available=list(config.available),
        allocation=[list(r) for r in config.allocation],
        request_matrix=[list(r) for r in config.request_matrix],
        raw_output=stdout,
    )


# ============================================================================
# Disk Scheduling Parsers
# ============================================================================

def generate_disk_stdin(config: DiskConfig) -> str:
    """Generate exact interactive stdin stream for Disk Scheduling CLI."""
    lines: List[str] = []

    # Main menu choice: 12 for Disk Scheduling
    lines.append("12")

    # Algorithm sub-menu choice (1-8)
    lines.append(str(config.algorithm.menu_choice))

    # Minimum cylinder
    lines.append(str(config.min_cylinder))

    # Maximum cylinder
    lines.append(str(config.max_cylinder))

    # Initial head position
    lines.append(str(config.initial_head))

    # Direction if needed
    if config.algorithm.needs_direction:
        lines.append(str(config.direction.cli_value))

    # Sequence of cylinder requests
    lines.append(" ".join(str(r) for r in config.requests))

    # Return to main menu choice: 9
    lines.append("9")

    # Exit choice to terminate interactive CLI cleanly: 13
    lines.append("13")

    return "\n".join(lines) + "\n"


def parse_disk_output(stdout: str, config: DiskConfig) -> DiskSchedulingResultModel:
    """Parse single disk arm scheduling output from C++ backend."""
    algo_match = re.search(r"=== Disk Scheduling Result:\s*(.*?)\s*===", stdout)
    if not algo_match:
        algo_match = re.search(r"===\s*(.*?)\s*(?:Disk Scheduling Result|Disk Scheduling)\s*===", stdout)
    if not algo_match:
        fail_match = re.search(r"Error:\s*(.*)", stdout)
        if fail_match:
            raise RuntimeError(f"C++ disk scheduling error: {fail_match.group(1).strip()}")
        raise RuntimeError("C++ output does not contain expected '=== Disk Scheduling Result: ... ==='.")

    algo_name = algo_match.group(1).strip()

    # Serviced requests
    serviced_requests: List[int] = []
    srv_match = re.search(r"Serviced Requests:\s*\[(.*?)\]", stdout)
    if srv_match and srv_match.group(1).strip():
        serviced_requests = [int(x.strip()) for x in srv_match.group(1).split(",") if x.strip()]

    # Head path
    head_path: List[int] = []
    path_match = re.search(r"(?:Head Movement Path|Service Order):\s*(.*)", stdout)
    if path_match and path_match.group(1).strip():
        raw_items = [x.strip() for x in path_match.group(1).split("->") if x.strip()]
        for it in raw_items:
            m_num = re.search(r"\d+", it)
            if m_num:
                head_path.append(int(m_num.group(0)))

    # Total movement
    total_mov_match = re.search(r"Total Head Movement:\s*(\d+)", stdout)
    total_movement = int(total_mov_match.group(1)) if total_mov_match else 0

    # Wraparound movement
    wrap_match = re.search(r"Includes circular wraparound traversal:\s*(\d+)", stdout)
    wraparound_movement = int(wrap_match.group(1)) if wrap_match else 0

    # Average movement
    avg_match = re.search(r"(?:Average Head Movement|Average Seek):\s*([\d\.]+)", stdout)
    average_movement = float(avg_match.group(1)) if avg_match else 0.0

    # Initial and final
    init_match = re.search(r"Initial Head Position:\s*(\d+)", stdout)
    initial_pos = int(init_match.group(1)) if init_match else (head_path[0] if head_path else config.initial_head)

    final_match = re.search(r"Final Head Position:\s*(\d+)", stdout)
    final_pos = int(final_match.group(1)) if final_match else (head_path[-1] if head_path else initial_pos)

    # Build step-by-step models
    steps: List[DiskStepModel] = []
    cum_movement = 0
    pending_requests = list(config.requests)

    for i in range(1, len(head_path)):
        from_c = head_path[i - 1]
        to_c = head_path[i]
        move = abs(to_c - from_c)
        cum_movement += move

        # Check if to_c is a circular wraparound jump
        is_wrap = False
        if wraparound_movement > 0 and move == wraparound_movement:
            is_wrap = True
        elif config.algorithm in (DiskAlgorithm.CSCAN, DiskAlgorithm.CLOOK):
            if (from_c == config.max_cylinder and to_c == config.min_cylinder) or \
               (from_c == config.min_cylinder and to_c == config.max_cylinder):
                is_wrap = True
            elif config.algorithm == DiskAlgorithm.CLOOK and wraparound_movement > 0 and move == wraparound_movement:
                is_wrap = True

        # Check if boundary reversal in SCAN / CSCAN
        is_boundary = False
        if not is_wrap and config.algorithm in (DiskAlgorithm.SCAN, DiskAlgorithm.CSCAN):
            if to_c in (config.min_cylinder, config.max_cylinder) and to_c not in pending_requests:
                is_boundary = True

        # Check if request was serviced
        is_req = False
        if not is_wrap and not is_boundary:
            if to_c in pending_requests:
                is_req = True
                pending_requests.remove(to_c)
            elif to_c in serviced_requests:
                is_req = True

        if is_wrap:
            desc = f"Circular wraparound jump from cylinder {from_c} to {to_c}"
        elif is_boundary:
            desc = f"Traversed to boundary cylinder {to_c} and reversed sweep direction"
        elif is_req:
            desc = f"Serviced I/O cylinder request {to_c}"
        else:
            desc = f"Head seek movement to cylinder {to_c}"

        steps.append(
            DiskStepModel(
                step_number=i,
                from_cylinder=from_c,
                to_cylinder=to_c,
                movement=move,
                cumulative_movement=cum_movement,
                is_request=is_req,
                is_boundary=is_boundary,
                is_wraparound=is_wrap,
                action_description=desc,
            )
        )

    return DiskSchedulingResultModel(
        algorithm=config.algorithm,
        algorithm_name=algo_name,
        serviced_requests=serviced_requests,
        head_path=head_path,
        total_head_movement=total_movement,
        wraparound_movement=wraparound_movement,
        average_head_movement=average_movement,
        initial_head_position=initial_pos,
        final_head_position=final_pos,
        message=f"{algo_name} simulated successfully with {len(serviced_requests)} requests serviced.",
        steps=steps,
        raw_output=stdout,
    )


def parse_disk_comparison_output(stdout: str, config: DiskConfig) -> DiskComparisonResultModel:
    """Parse comparison table output from C++ backend."""
    comp_header = re.search(r"Disk Scheduling (?:Algorithm )?Comparison", stdout)
    if not comp_header:
        fail_match = re.search(r"Error:\s*(.*)", stdout)
        if fail_match:
            raise RuntimeError(f"C++ disk comparison error: {fail_match.group(1).strip()}")
        raise RuntimeError("C++ output does not contain expected 'Disk Scheduling Comparison' header.")

    table_section = re.search(
        r"-{20,}\s*\n([\s\S]*?)(?:\n={20,}|\Z)",
        stdout,
    )
    entries: List[DiskComparisonEntryModel] = []
    if table_section:
        for line in table_section.group(1).splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("Best algorithm") or line_str.startswith("Note:") or line_str.startswith("Algorithm") or line_str.startswith("```"):
                continue
            # Row format:
            # First-Come, First-Served (FCFS)                    640               80.00            67
            # or
            # SSTF                         236 cylinders          29.50 cyl/req      +63.1%
            m = re.match(r"^(.*?)\s{2,}(\d+)(?:\s+cylinders)?\s+([\d\.]+)(?:\s+cyl/req)?(?:\s+(.*))?$", line_str)
            if m:
                algo_str = m.group(1).strip()
                tot_mov = int(m.group(2))
                avg_mov = float(m.group(3))
                col4 = (m.group(4) or "").strip()
                fin_head = int(col4) if col4.isdigit() else 0
                imp_val = 0.0
                if "%" in col4:
                    try:
                        clean_col4 = col4.replace("%", "").replace("+", "").replace("(baseline)", "0").strip()
                        imp_val = float(clean_col4)
                    except ValueError:
                        imp_val = 0.0
                entries.append(
                    DiskComparisonEntryModel(
                        algorithm_name=algo_str,
                        total_head_movement=tot_mov,
                        average_head_movement=avg_mov,
                        final_head_position=fin_head,
                        improvement_vs_fcfs=imp_val,
                    )
                )

    dir_str = config.direction.display_name if config.algorithm.needs_direction else "N/A"

    return DiskComparisonResultModel(
        original_requests=list(config.requests),
        min_cylinder=config.min_cylinder,
        max_cylinder=config.max_cylinder,
        initial_head=config.initial_head,
        direction=dir_str,
        entries=entries,
        raw_output=stdout,
    )


def generate_linux_experiments_stdin(category: LinuxExperimentCategory) -> str:
    """Generate interactive CLI stdin sequence for Linux/POSIX experiments menu 10."""
    lines: List[str] = ["10"]  # Enter Linux/POSIX Experiments menu

    if category == LinuxExperimentCategory.ALL:
        lines.extend(["1", "2", "3", "4"])
    elif category == LinuxExperimentCategory.LIFECYCLE:
        lines.append("1")
    elif category == LinuxExperimentCategory.SYNCHRONIZATION:
        lines.append("3")
    elif category == LinuxExperimentCategory.PRODUCER_CONSUMER:
        lines.append("3")
    elif category == LinuxExperimentCategory.IPC:
        lines.append("4")

    lines.append("5")   # Return to Main Menu
    lines.append("13")  # Exit OScope
    return "\n".join(lines) + "\n"


def parse_linux_experiments_output(
    stdout: str,
    category: LinuxExperimentCategory = LinuxExperimentCategory.ALL,
    exit_code: int = 0,
    duration_ms: float = 0.0,
) -> LinuxExperimentsResultModel:
    """Parse JSON or human-readable stdout from Linux/POSIX backend experiments."""
    res = LinuxExperimentsResultModel(
        category=category,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        exit_code=exit_code,
        execution_duration_ms=duration_ms,
        raw_output=stdout,
    )

    # 1. Attempt JSON parsing (from --json or embedded json blocks)
    parsed_json_items: List[Dict[str, Any]] = []
    try:
        # Check for clean json array or object
        trimmed = stdout.strip()
        if trimmed.startswith("[") and trimmed.endswith("]"):
            data = json.loads(trimmed)
            if isinstance(data, list):
                parsed_json_items = data
        elif trimmed.startswith("{") and trimmed.endswith("}"):
            data = json.loads(trimmed)
            if isinstance(data, dict):
                parsed_json_items = [data]
        else:
            # Look for ```json ... ``` code fence or embedded array
            json_block = re.search(r"```json\s*([\s\S]*?)\s*```", stdout)
            if json_block:
                data = json.loads(json_block.group(1).strip())
                if isinstance(data, list):
                    parsed_json_items = data
                elif isinstance(data, dict):
                    parsed_json_items = [data]
            else:
                arr_match = re.search(r"(\[\s*\{[\s\S]*\}\s*\])", stdout)
                if arr_match:
                    data = json.loads(arr_match.group(1).strip())
                    if isinstance(data, list):
                        parsed_json_items = data
    except Exception:
        parsed_json_items = []

    if parsed_json_items:
        res.raw_json = parsed_json_items
        for item in parsed_json_items:
            exp_type = item.get("experiment", "")
            r = item.get("result", {})
            status_ok = item.get("success", True) and item.get("status") != "failure"

            if exp_type == "process_exec":
                res.process_exec = ProcessExecResultModel(
                    child_pid=int(r.get("child_pid", 0)),
                    program_executed=str(r.get("program_executed", "/bin/echo")),
                    image_replaced=bool(r.get("image_replaced", True)),
                    captured_output=str(r.get("captured_output", "")),
                    child_exit_code=int(r.get("child_exit_code", 0)),
                    details=str(r.get("details", "")),
                    success=status_ok,
                )
            elif exp_type == "zombie_demonstration":
                res.zombie_demo = ZombieResultModel(
                    child_pid=int(r.get("child_pid", 0)),
                    observed_state=str(r.get("observed_state", "Z")),
                    zombie_observed=bool(r.get("zombie_observed", True)),
                    reaped_successfully=bool(r.get("reaped_successfully", True)),
                    details=str(r.get("details", "")),
                    success=status_ok,
                )
            elif exp_type == "orphan_demonstration":
                res.orphan_demo = OrphanResultModel(
                    child_pid=int(r.get("child_pid", 0)),
                    initial_parent_pid=int(r.get("initial_parent_pid", 0)),
                    adopted_parent_pid=int(r.get("adopted_parent_pid", 1)),
                    reparented_to_init_or_subreaper=bool(r.get("reparented_to_init_or_subreaper", True)),
                    details=str(r.get("details", "")),
                    success=status_ok,
                )
            elif exp_type == "thread_creation":
                res.thread_creation = ThreadCreationResultModel(
                    requested_threads=int(r.get("requested_threads", 4)),
                    started_threads=int(r.get("started_threads", 4)),
                    completed_threads=int(r.get("completed_threads", 4)),
                    worker_results=list(r.get("worker_results", [])),
                    success=status_ok,
                )
            elif exp_type == "thread_synchronization":
                res.mutex_sync = MutexSyncResultModel(
                    num_threads=int(r.get("num_threads", 4)),
                    iterations_per_thread=int(r.get("iterations_per_thread", 10000)),
                    threads_completed=int(r.get("threads_completed", 4)),
                    expected_counter=int(r.get("expected_counter", 40000)),
                    actual_counter=int(r.get("actual_counter", 40000)),
                    success=status_ok,
                )
            elif exp_type == "posix_semaphore":
                res.posix_semaphore = PosixSemaphoreResultModel(
                    num_threads=int(r.get("num_threads", 4)),
                    iterations_per_thread=int(r.get("iterations_per_thread", 5000)),
                    threads_completed=int(r.get("threads_completed", 4)),
                    expected_counter=int(r.get("expected_counter", 20000)),
                    actual_counter=int(r.get("actual_counter", 20000)),
                    initial_value=int(r.get("initial_value", 1)),
                    counter_match=bool(r.get("counter_match", True)),
                    success=status_ok,
                )
            elif exp_type == "petersons_algorithm":
                res.petersons_algo = PetersonResultModel(
                    mutual_exclusion_maintained=bool(r.get("mutual_exclusion_maintained", True)),
                    p0_critical_entries=int(r.get("p0_critical_entries", 2)),
                    p1_critical_entries=int(r.get("p1_critical_entries", 2)),
                    total_steps=int(r.get("total_steps", 26)),
                    explanation=str(r.get("explanation", "")),
                    success=status_ok,
                )
            elif exp_type == "producer_consumer":
                res.producer_consumer = ProducerConsumerResultModel(
                    buffer_capacity=int(r.get("buffer_capacity", 5)),
                    total_items=int(r.get("total_items", 50)),
                    num_producers=int(r.get("num_producers", 2)),
                    num_consumers=int(r.get("num_consumers", 2)),
                    items_produced=int(r.get("items_produced", 50)),
                    items_consumed=int(r.get("items_consumed", 50)),
                    items_preserved=bool(r.get("items_preserved", True)),
                    max_buffer_occupancy_observed=int(r.get("max_buffer_occupancy_observed", 5)),
                    success=status_ok,
                )
            elif exp_type == "pipe_ipc":
                res.pipe_ipc = PipeIpcResultModel(
                    parent_pid=int(r.get("parent_pid", 0)),
                    child_pid=int(r.get("child_pid", 0)),
                    child_exit_code=int(r.get("child_exit_code", 0)),
                    sent_message=str(r.get("sent_message", "")),
                    received_message=str(r.get("received_message", "")),
                    success=status_ok,
                )
            elif exp_type == "fifo_ipc":
                res.fifo_ipc = FifoIpcResultModel(
                    fifo_path=str(r.get("fifo_path", "")),
                    message_sent=str(r.get("message_sent", "")),
                    message_received=str(r.get("message_received", "")),
                    details=str(r.get("details", "")),
                    success=status_ok,
                )
            elif exp_type == "shared_memory_ipc":
                res.shared_memory_ipc = SharedMemoryIpcResultModel(
                    segment_name=str(r.get("segment_name", "")),
                    size_bytes=int(r.get("size_bytes", 4096)),
                    message_written=str(r.get("message_written", "")),
                    message_read=str(r.get("message_read", "")),
                    details=str(r.get("details", "")),
                    success=status_ok,
                )
            elif exp_type == "message_queue_ipc":
                res.message_queue_ipc = MessageQueueIpcResultModel(
                    queue_name=str(r.get("queue_name", "")),
                    messages_sent=int(r.get("messages_sent", 1)),
                    messages_received=int(r.get("messages_received", 1)),
                    message_content=str(r.get("message_content", "")),
                    details=str(r.get("details", "")),
                    success=status_ok,
                )

        return res

    # 2. Fallback text parsing for human-readable output
    # Process Exec
    m_exec = re.search(r"Child PID:\s*(\d+)[\s\S]*?Image Replaced:\s*(YES|NO)[\s\S]*?Captured Output:\s*(.*?)\n\s*Exit Code:\s*(\d+)", stdout)
    if m_exec:
        res.process_exec = ProcessExecResultModel(
            child_pid=int(m_exec.group(1)),
            image_replaced=(m_exec.group(2) == "YES"),
            captured_output=m_exec.group(3).strip(),
            child_exit_code=int(m_exec.group(4)),
            success=True,
        )

    # Zombie
    m_zomb = re.search(r"Zombie Process[\s\S]*?Child PID:\s*(\d+)[\s\S]*?Observed /proc State:\s*'(\w+)'[\s\S]*?Reaped by Parent:\s*(.*?)\n", stdout)
    if m_zomb:
        res.zombie_demo = ZombieResultModel(
            child_pid=int(m_zomb.group(1)),
            observed_state=m_zomb.group(2),
            zombie_observed=True,
            reaped_successfully=("SUCCESS" in m_zomb.group(3)),
            details=m_zomb.group(3).strip(),
            success=True,
        )

    # Orphan
    m_orph = re.search(r"Orphan Process[\s\S]*?Child PID:\s*(\d+)[\s\S]*?Original Parent:\s*PID\s*(\d+)[\s\S]*?Adopted Parent:\s*PID\s*(\d+)", stdout)
    if m_orph:
        res.orphan_demo = OrphanResultModel(
            child_pid=int(m_orph.group(1)),
            initial_parent_pid=int(m_orph.group(2)),
            adopted_parent_pid=int(m_orph.group(3)),
            reparented_to_init_or_subreaper=True,
            success=True,
        )

    # Thread Synchronization (Mutex)
    m_sync = re.search(r"Thread Synchronization[\s\S]*?Concurrent Threads:\s*(\d+)[\s\S]*?Iterations Per Thread:\s*(\d+)[\s\S]*?Expected Counter:\s*(\d+)[\s\S]*?Actual Counter:\s*(\d+)", stdout)
    if m_sync:
        res.mutex_sync = MutexSyncResultModel(
            num_threads=int(m_sync.group(1)),
            iterations_per_thread=int(m_sync.group(2)),
            threads_completed=int(m_sync.group(1)),
            expected_counter=int(m_sync.group(3)),
            actual_counter=int(m_sync.group(4)),
            success=(int(m_sync.group(3)) == int(m_sync.group(4))),
        )

    # POSIX Semaphore
    m_sem = re.search(r"POSIX Semaphore Synchronization[\s\S]*?Threads:\s*(\d+)[\s\S]*?Expected Counter:\s*(\d+)[\s\S]*?Actual Counter:\s*(\d+)", stdout)
    if m_sem:
        res.posix_semaphore = PosixSemaphoreResultModel(
            num_threads=int(m_sem.group(1)),
            expected_counter=int(m_sem.group(2)),
            actual_counter=int(m_sem.group(3)),
            counter_match=(int(m_sem.group(2)) == int(m_sem.group(3))),
            success=True,
        )

    # Producer Consumer
    m_pc = re.search(r"Producer-Consumer[\s\S]*?Buffer Capacity:\s*(\d+)[\s\S]*?Items Produced:\s*(\d+)[\s\S]*?Items Consumed:\s*(\d+)", stdout)
    if m_pc:
        res.producer_consumer = ProducerConsumerResultModel(
            buffer_capacity=int(m_pc.group(1)),
            items_produced=int(m_pc.group(2)),
            items_consumed=int(m_pc.group(3)),
            items_preserved=True,
            success=True,
        )

    # Pipe IPC
    m_pipe = re.search(r"Pipe-based IPC[\s\S]*?Parent PID:\s*(\d+)[\s\S]*?Child PID:\s*(\d+)[\s\S]*?Sent Message:\s*\"(.*?)\"[\s\S]*?Received Message:\s*\"(.*?)\"", stdout)
    if m_pipe:
        res.pipe_ipc = PipeIpcResultModel(
            parent_pid=int(m_pipe.group(1)),
            child_pid=int(m_pipe.group(2)),
            sent_message=m_pipe.group(3),
            received_message=m_pipe.group(4),
            success=True,
        )

    # FIFO
    m_fifo = re.search(r"POSIX Named Pipe \(FIFO\)[\s\S]*?FIFO Path:\s*(.*?)\n[\s\S]*?Message Sent:\s*\"(.*?)\"[\s\S]*?Message Received:\s*\"(.*?)\"", stdout)
    if m_fifo:
        res.fifo_ipc = FifoIpcResultModel(
            fifo_path=m_fifo.group(1).strip(),
            message_sent=m_fifo.group(2),
            message_received=m_fifo.group(3),
            success=True,
        )

    # Shared Memory
    m_shm = re.search(r"POSIX Shared Memory[\s\S]*?Segment Name:\s*(.*?)\n[\s\S]*?Message Written:\s*\"(.*?)\"[\s\S]*?Message Read:\s*\"(.*?)\"", stdout)
    if m_shm:
        res.shared_memory_ipc = SharedMemoryIpcResultModel(
            segment_name=m_shm.group(1).strip(),
            message_written=m_shm.group(2),
            message_read=m_shm.group(3),
            success=True,
        )

    # Message Queue
    m_mq = re.search(r"POSIX Message Queue[\s\S]*?Queue Name:\s*(.*?)\n[\s\S]*?Messages Sent:\s*(\d+)[\s\S]*?Messages Received:\s*(\d+)[\s\S]*?Payload:\s*\"(.*?)\"", stdout)
    if m_mq:
        res.message_queue_ipc = MessageQueueIpcResultModel(
            queue_name=m_mq.group(1).strip(),
            messages_sent=int(m_mq.group(2)),
            messages_received=int(m_mq.group(3)),
            message_content=m_mq.group(4),
            success=True,
        )

    return res


# ============================================================================
# Host Resource Monitoring Parser
# ============================================================================

def parse_host_monitoring_output(
    stdout: str,
    exit_code: int = 0,
    duration_ms: float = 0.0,
) -> HostMonitoringSnapshotModel:
    """Parse JSON or human-readable stdout from Linux host resource monitoring."""
    snapshot = HostMonitoringSnapshotModel(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        raw_output=stdout,
    )

    if exit_code != 0:
        snapshot.success = False
        snapshot.error_message = f"Process exited with non-zero exit code {exit_code}"

    # 1. Attempt JSON parsing
    json_item = None
    try:
        trimmed = stdout.strip()
        if trimmed.startswith("{") and trimmed.endswith("}"):
            data = json.loads(trimmed)
            if isinstance(data, dict):
                json_item = data
        elif trimmed.startswith("[") and trimmed.endswith("]"):
            data = json.loads(trimmed)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("experiment") == "host_observation":
                        json_item = item
                        break
        else:
            json_block = re.search(r"```json\s*([\s\S]*?)\s*```", stdout)
            if json_block:
                data = json.loads(json_block.group(1).strip())
                if isinstance(data, dict):
                    json_item = data
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("experiment") == "host_observation":
                            json_item = item
                            break
    except Exception:
        json_item = None

    if json_item and isinstance(json_item, dict):
        snapshot.raw_json = json_item
        res = json_item.get("result", {})
        snapshot.source = str(res.get("source", "real_linux_host"))
        if "timestamp" in res and res["timestamp"]:
            snapshot.timestamp = str(res["timestamp"])
        snapshot.success = bool(json_item.get("success", True))
        snapshot.error_message = json_item.get("error")

        # CPU
        try:
            total_cpu = float(res.get("cpu_usage_percent", 0.0))
            u_cpu = float(res.get("cpu_user_percent", 0.0))
            s_cpu = float(res.get("cpu_system_percent", 0.0))
            i_cpu = float(res.get("cpu_idle_percent", 100.0 - total_cpu))
            snapshot.cpu = HostCpuModel(
                total_usage_percent=total_cpu,
                user_percent=u_cpu,
                system_percent=s_cpu,
                idle_percent=i_cpu,
                valid=True,
            )
        except (ValueError, TypeError):
            pass

        # Memory
        try:
            tot_mem = int(res.get("memory_total_kb", 0))
            used_mem = int(res.get("memory_used_kb", 0))
            avail_mem = int(res.get("memory_available_kb", 0))
            free_mem = int(res.get("memory_free_kb", 0))
            used_pct = float(res.get("memory_used_percent", 0.0))
            if tot_mem > 0 and avail_mem == 0:
                avail_mem = max(0, tot_mem - used_mem)
            if tot_mem > 0 and used_pct == 0.0:
                used_pct = (used_mem / tot_mem) * 100.0
            snapshot.memory = HostMemoryModel(
                total_kb=tot_mem,
                used_kb=used_mem,
                available_kb=avail_mem,
                free_kb=free_mem,
                used_percent=used_pct,
                valid=(tot_mem > 0),
            )
        except (ValueError, TypeError):
            pass

        # System
        try:
            up_sec = float(res.get("uptime_seconds", 0.0))
            l1 = float(res.get("load_1min", 0.0))
            l5 = float(res.get("load_5min", 0.0))
            l15 = float(res.get("load_15min", 0.0))
            tot_p = int(res.get("total_processes", 0))
            run_p = int(res.get("running_processes", 0))
            d_tot = int(res.get("disk_total_bytes", 0))
            d_used = int(res.get("disk_used_bytes", 0))
            d_avail = int(res.get("disk_available_bytes", 0))
            d_pct = float(res.get("disk_used_percent", 0.0))
            snapshot.system = HostSystemModel(
                uptime_seconds=up_sec,
                load_1min=l1,
                load_5min=l5,
                load_15min=l15,
                total_processes=tot_p,
                running_processes=run_p,
                disk_total_bytes=d_tot,
                disk_used_bytes=d_used,
                disk_available_bytes=d_avail,
                disk_used_percent=d_pct,
                valid=True,
            )
        except (ValueError, TypeError):
            pass

        # Self-Process
        try:
            pid = int(res.get("self_pid", 0))
            ppid = int(res.get("self_ppid", 0))
            comm = str(res.get("self_comm", "oscope"))
            state = str(res.get("self_state", "R"))
            rss = int(res.get("self_rss_kb", 0))
            vm = int(res.get("self_vm_size_bytes", 0))
            snapshot.self_process = HostProcessModel(
                pid=pid,
                ppid=ppid,
                comm=comm,
                state=state,
                rss_kb=rss,
                vm_size_bytes=vm,
                valid=(pid > 0),
            )
        except (ValueError, TypeError):
            pass

        # Disks
        disks_data = res.get("disks", [])
        if isinstance(disks_data, list):
            for d in disks_data:
                if isinstance(d, dict):
                    snapshot.disks.append(HostDiskIoModel(
                        device_name=str(d.get("device_name", "")),
                        reads_completed=int(d.get("reads_completed", 0)),
                        sectors_read=int(d.get("sectors_read", 0)),
                        writes_completed=int(d.get("writes_completed", 0)),
                        sectors_written=int(d.get("sectors_written", 0)),
                        valid=True,
                    ))

        return snapshot

    # 2. Text Parsing Fallback
    # CPU
    m_cpu = re.search(r"Total CPU Usage:\s*([\d\.]+)\s*%", stdout)
    if m_cpu:
        tot_cpu = float(m_cpu.group(1))
        m_u = re.search(r"User Space:\s*([\d\.]+)\s*%", stdout)
        m_s = re.search(r"Kernel / System:\s*([\d\.]+)\s*%", stdout)
        m_i = re.search(r"Idle:\s*([\d\.]+)\s*%", stdout)
        snapshot.cpu = HostCpuModel(
            total_usage_percent=tot_cpu,
            user_percent=float(m_u.group(1)) if m_u else 0.0,
            system_percent=float(m_s.group(1)) if m_s else 0.0,
            idle_percent=float(m_i.group(1)) if m_i else max(0.0, 100.0 - tot_cpu),
            valid=True,
        )

    # Memory
    m_tot_mem = re.search(r"Total RAM:\s*(\d+)\s*kB", stdout)
    m_used_mem = re.search(r"Used RAM:\s*(\d+)\s*kB", stdout)
    m_avail_mem = re.search(r"Available RAM:\s*(\d+)\s*kB", stdout)
    m_pct_mem = re.search(r"Utilization:\s*([\d\.]+)\s*%", stdout)
    if m_tot_mem:
        tot_k = int(m_tot_mem.group(1))
        used_k = int(m_used_mem.group(1)) if m_used_mem else 0
        avail_k = int(m_avail_mem.group(1)) if m_avail_mem else max(0, tot_k - used_k)
        pct = float(m_pct_mem.group(1)) if m_pct_mem else ((used_k / tot_k) * 100.0 if tot_k else 0.0)
        snapshot.memory = HostMemoryModel(
            total_kb=tot_k,
            used_kb=used_k,
            available_kb=avail_k,
            free_kb=avail_k,
            used_percent=pct,
            valid=True,
        )

    # Self-Process
    m_pid = re.search(r"PID:\s*(\d+)", stdout)
    if m_pid:
        pid = int(m_pid.group(1))
        m_comm = re.search(r"Executable Name:\s*(.+)", stdout)
        m_state = re.search(r"Process State:\s*(\w+)", stdout)
        m_uticks = re.search(r"User CPU Ticks:\s*(\d+)", stdout)
        m_sticks = re.search(r"System CPU Ticks:\s*(\d+)", stdout)
        m_vm = re.search(r"Virtual Memory:\s*(\d+)\s*kB", stdout)
        m_rss = re.search(r"Resident Set:\s*(\d+)\s*kB", stdout)
        snapshot.self_process = HostProcessModel(
            pid=pid,
            comm=m_comm.group(1).strip() if m_comm else "oscope",
            state=m_state.group(1).strip() if m_state else "R",
            utime_ticks=int(m_uticks.group(1)) if m_uticks else 0,
            stime_ticks=int(m_sticks.group(1)) if m_sticks else 0,
            vm_size_bytes=int(m_vm.group(1)) * 1024 if m_vm else 0,
            rss_kb=int(m_rss.group(1)) if m_rss else 0,
            valid=True,
        )

    # System & Filesystem
    m_up = re.search(r"Uptime:\s*([\d\.]+)\s*seconds", stdout)
    m_load = re.search(r"Load Averages:\s*([\d\.]+)\s*\(1m\),\s*([\d\.]+)\s*\(5m\),\s*([\d\.]+)\s*\(15m\)", stdout)
    m_procs = re.search(r"Process Count:\s*(\d+)\s*total\s*\((\d+)\s*runnable\)", stdout)
    m_disk_tot = re.search(r"Disk Capacity:\s*(\d+)\s*MB", stdout)
    m_disk_used = re.search(r"Disk Used:\s*(\d+)\s*MB\s*\(([\d\.]+)\s*%\)", stdout)
    m_disk_avail = re.search(r"Disk Available:\s*(\d+)\s*MB", stdout)

    if m_up or m_load or m_procs or m_disk_tot:
        snapshot.system = HostSystemModel(
            uptime_seconds=float(m_up.group(1)) if m_up else 0.0,
            load_1min=float(m_load.group(1)) if m_load else 0.0,
            load_5min=float(m_load.group(2)) if m_load else 0.0,
            load_15min=float(m_load.group(3)) if m_load else 0.0,
            total_processes=int(m_procs.group(1)) if m_procs else 0,
            running_processes=int(m_procs.group(2)) if m_procs else 0,
            disk_total_bytes=int(m_disk_tot.group(1)) * 1024 * 1024 if m_disk_tot else 0,
            disk_used_bytes=int(m_disk_used.group(1)) * 1024 * 1024 if m_disk_used else 0,
            disk_available_bytes=int(m_disk_avail.group(1)) * 1024 * 1024 if m_disk_avail else 0,
            disk_used_percent=float(m_disk_used.group(2)) if m_disk_used else 0.0,
            valid=True,
        )

    # Disks table from text
    for line in stdout.splitlines():
        d_match = re.search(
            r"Device:\s*(\w+)\s*\|\s*Reads:\s*(\d+)\s*\|\s*Sectors Read:\s*(\d+)\s*\|\s*Writes:\s*(\d+)\s*\|\s*Sectors Written:\s*(\d+)",
            line,
        )
        if d_match:
            snapshot.disks.append(HostDiskIoModel(
                device_name=d_match.group(1).strip(),
                reads_completed=int(d_match.group(2)),
                sectors_read=int(d_match.group(3)),
                writes_completed=int(d_match.group(4)),
                sectors_written=int(d_match.group(5)),
                valid=True,
            ))

    snapshot.success = snapshot.cpu.valid or snapshot.memory.valid or snapshot.self_process.valid
    return snapshot


def generate_filesystem_stdin(config: FilesystemConfig) -> str:
    """Generate line-delimited commands for --fs-ops stdin execution."""
    lines: List[str] = [f"config {config.total_blocks} {config.block_size}"]
    for op in config.operations:
        cmd = op.to_cli_command()
        if cmd:
            lines.append(cmd)
    return "\n".join(lines) + "\n"


def parse_filesystem_output(
    stdout: str,
    preset: FilesystemPreset = FilesystemPreset.STANDARD_DEMO,
    exit_code: int = 0,
    duration_ms: float = 0.0,
) -> FilesystemSimulationResultModel:
    """Parse C++ simple_filesystem JSON or human-readable stdout."""
    # 1. Try JSON parsing
    try:
        # Find JSON object bounds
        first_brace = stdout.find("{")
        last_brace = stdout.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            data = json.loads(stdout[first_brace : last_brace + 1])
            res = data.get("result", {})
            if isinstance(res, dict) and "total_blocks" in res:
                total_blocks = int(res.get("total_blocks", 32))
                block_size = int(res.get("block_size", 512))
                used_blocks = int(res.get("used_blocks", 0))
                free_blocks = int(res.get("free_blocks", total_blocks - used_blocks))
                file_count = int(res.get("file_count", 0))
                directory_count = int(res.get("directory_count", 1))

                raw_bitmap = res.get("block_bitmap", [])
                block_bitmap = [bool(b) for b in raw_bitmap] if raw_bitmap else [False] * total_blocks

                inodes: List[FileInodeModel] = []
                for in_data in res.get("inodes", []):
                    inodes.append(
                        FileInodeModel(
                            inode_id=int(in_data.get("inode_id", 0)),
                            name=str(in_data.get("name", "")),
                            path=str(in_data.get("path", "")),
                            is_directory=bool(in_data.get("is_directory", False)),
                            size_bytes=int(in_data.get("size_bytes", 0)),
                            strategy=str(in_data.get("strategy", "Indexed")),
                            start_block=int(in_data.get("start_block", -1)),
                            index_block=int(in_data.get("index_block", -1)),
                            block_count=int(in_data.get("block_count", 0)),
                            allocated_blocks=[int(b) for b in in_data.get("allocated_blocks", [])],
                        )
                    )

                traces: List[AllocationTraceModel] = []
                for tr_data in res.get("allocation_traces", []):
                    traces.append(
                        AllocationTraceModel(
                            name=str(tr_data.get("name", "")),
                            path=str(tr_data.get("path", "")),
                            strategy=str(tr_data.get("strategy", "")),
                            start_block=int(tr_data.get("start_block", -1)),
                            index_block=int(tr_data.get("index_block", -1)),
                            block_count=int(tr_data.get("block_count", 0)),
                            allocated_blocks=[int(b) for b in tr_data.get("allocated_blocks", [])],
                        )
                    )

                raw_logs = res.get("operation_logs", [])
                operation_logs = [str(l) for l in raw_logs]

                status_model = FilesystemStatusModel(
                    total_blocks=total_blocks,
                    block_size=block_size,
                    used_blocks=used_blocks,
                    free_blocks=free_blocks,
                    file_count=file_count,
                    directory_count=directory_count,
                    block_bitmap=block_bitmap,
                    inodes=inodes,
                    allocation_traces=traces,
                    operation_logs=operation_logs,
                )
                return FilesystemSimulationResultModel(
                    status=status_model,
                    preset=preset,
                    raw_stdout=stdout,
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                    is_success=True,
                )
    except Exception:
        pass

    # 2. Text fallback parsing
    total_blocks = 32
    block_size = 512
    used_blocks = 0
    free_blocks = 32
    dir_count = 1
    file_count = 0
    bitmap: List[bool] = []
    inodes: List[FileInodeModel] = [
        FileInodeModel(inode_id=0, name="/", path="/", is_directory=True, size_bytes=0)
    ]
    traces: List[AllocationTraceModel] = []
    logs: List[str] = []

    m_tot = re.search(r"Total Blocks:\s*(\d+)", stdout)
    if m_tot:
        total_blocks = int(m_tot.group(1))
    m_bs = re.search(r"Block Size:\s*(\d+)", stdout)
    if m_bs:
        block_size = int(m_bs.group(1))
    m_used = re.search(r"Used Blocks:\s*(\d+)", stdout)
    if m_used:
        used_blocks = int(m_used.group(1))
    m_free = re.search(r"Free Blocks:\s*(\d+)", stdout)
    if m_free:
        free_blocks = int(m_free.group(1))
    m_dirs = re.search(r"Directories:\s*(\d+)", stdout)
    if m_dirs:
        dir_count = int(m_dirs.group(1))
    m_files = re.search(r"Files:\s*(\d+)", stdout)
    if m_files:
        file_count = int(m_files.group(1))

    # Parse directory hierarchy lines
    for line in stdout.splitlines():
        line_clean = line.strip()
        m_entry = re.search(
            r"\[(DIR\s*|FILE)\]\s*(\S+)\s*\(Inode\s*(\d+),\s*(\d+)\s*bytes\)",
            line_clean,
        )
        if m_entry:
            is_dir = "DIR" in m_entry.group(1)
            name = m_entry.group(2)
            ino = int(m_entry.group(3))
            sz = int(m_entry.group(4))
            inodes.append(
                FileInodeModel(
                    inode_id=ino,
                    name=name,
                    path=f"/home/{name}" if name != "docs" else "/home/docs",
                    is_directory=is_dir,
                    size_bytes=sz,
                )
            )

        # Parse allocation comparison traces
        m_contig = re.search(
            r"1\.\s*Contiguous:\s*(\S+)\s*->\s*Start Block:\s*(\d+),\s*Count:\s*(\d+)",
            line_clean,
        )
        if m_contig:
            fname = m_contig.group(1)
            sb = int(m_contig.group(2))
            cnt = int(m_contig.group(3))
            blks = list(range(sb, sb + cnt))
            traces.append(
                AllocationTraceModel(
                    name=fname,
                    path=f"/home/{fname}",
                    strategy="Contiguous",
                    start_block=sb,
                    index_block=-1,
                    block_count=cnt,
                    allocated_blocks=blks,
                )
            )
            # Update matching inode
            for in_obj in inodes:
                if in_obj.name == fname:
                    in_obj.strategy = "Contiguous"
                    in_obj.start_block = sb
                    in_obj.block_count = cnt
                    in_obj.allocated_blocks = blks

        m_linked = re.search(r"2\.\s*Linked:\s*(\S+)\s*->\s*Blocks:\s*([0-9\s]+)\[", line_clean)
        if m_linked:
            fname = m_linked.group(1)
            blks = [int(b) for b in m_linked.group(2).split() if b.isdigit()]
            sb = blks[0] if blks else -1
            traces.append(
                AllocationTraceModel(
                    name=fname,
                    path=f"/home/{fname}",
                    strategy="Linked",
                    start_block=sb,
                    index_block=-1,
                    block_count=len(blks),
                    allocated_blocks=blks,
                )
            )
            for in_obj in inodes:
                if in_obj.name == fname:
                    in_obj.strategy = "Linked"
                    in_obj.start_block = sb
                    in_obj.block_count = len(blks)
                    in_obj.allocated_blocks = blks

        m_idx = re.search(
            r"3\.\s*Indexed:\s*(\S+)\s*->\s*Index Block:\s*(\d+),\s*Data Blocks:\s*([0-9\s]+)\[",
            line_clean,
        )
        if m_idx:
            fname = m_idx.group(1)
            ib = int(m_idx.group(2))
            blks = [int(b) for b in m_idx.group(3).split() if b.isdigit()]
            traces.append(
                AllocationTraceModel(
                    name=fname,
                    path=f"/home/{fname}",
                    strategy="Indexed",
                    start_block=ib,
                    index_block=ib,
                    block_count=len(blks) + 1,
                    allocated_blocks=blks,
                )
            )
            for in_obj in inodes:
                if in_obj.name == fname:
                    in_obj.strategy = "Indexed"
                    in_obj.start_block = ib
                    in_obj.index_block = ib
                    in_obj.block_count = len(blks) + 1
                    in_obj.allocated_blocks = blks

        # Bullet log lines
        if line_clean.startswith("*"):
            logs.append(line_clean.lstrip("* ").strip())

        # Bitmap row
        if re.search(r"^[01\s]{8,}$", line_clean):
            bits = line_clean.replace(" ", "")
            for ch in bits:
                bitmap.append(ch == "1")

    if not bitmap:
        bitmap = [False] * total_blocks
        for tr in traces:
            for b in tr.allocated_blocks:
                if 0 <= b < total_blocks:
                    bitmap[b] = True
            if tr.index_block >= 0 and tr.index_block < total_blocks:
                bitmap[tr.index_block] = True

    status_model = FilesystemStatusModel(
        total_blocks=total_blocks,
        block_size=block_size,
        used_blocks=used_blocks,
        free_blocks=free_blocks,
        file_count=file_count,
        directory_count=dir_count,
        block_bitmap=bitmap,
        inodes=inodes,
        allocation_traces=traces,
        operation_logs=logs,
    )
    return FilesystemSimulationResultModel(
        status=status_model,
        preset=preset,
        raw_stdout=stdout,
        exit_code=exit_code,
        duration_ms=duration_ms,
        is_success=exit_code == 0 or len(inodes) > 1,
    )


def generate_paging_ops_stdin(config: AddressTranslationConfig) -> str:
    """Generate line-delimited commands for --paging-ops."""
    lines: List[str] = [f"pagesize {config.page_size}"]
    for page, frame in config.custom_mappings:
        lines.append(f"map {page} {frame}")
    for va in config.virtual_addresses_to_translate:
        lines.append(f"translate {va}")
    if config.demand_paging_addresses:
        vas_str = " ".join(str(va) for va in config.demand_paging_addresses)
        lines.append(f"demand {config.demand_paging_frames} {vas_str}")
    if config.thrashing_reference_string:
        refs_str = " ".join(str(r) for r in config.thrashing_reference_string)
        lines.append(f"thrash {config.thrashing_min_frames} {config.thrashing_max_frames} {refs_str}")
    return "\n".join(lines) + "\n"


def parse_address_translation_output(
    stdout: str,
    config: Optional[AddressTranslationConfig] = None,
) -> AddressTranslationSimulationResultModel:
    """Parse C++ address translation / demand paging / thrashing stdout."""
    res_model = AddressTranslationSimulationResultModel(
        page_size=config.page_size if config else 4096,
        page_table=[],
        translations=[],
        demand_paging=None,
        thrashing=None,
        logs=[],
    )

    # 1. Try structured JSON parsing
    try:
        first_bracket = stdout.find("[")
        last_bracket = stdout.rfind("]")
        first_brace = stdout.find("{")
        last_brace = stdout.rfind("}")

        json_data = None
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            json_data = json.loads(stdout[first_bracket : last_bracket + 1])
        elif first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            obj = json.loads(stdout[first_brace : last_brace + 1])
            json_data = [obj] if isinstance(obj, dict) else obj

        if isinstance(json_data, list):
            for item in json_data:
                if not isinstance(item, dict):
                    continue
                exp = item.get("experiment", "")
                result_data = item.get("result", {})

                if exp == "paging_overview":
                    res_model.page_size = int(result_data.get("page_size", res_model.page_size))
                    for pt_raw in result_data.get("page_table", []):
                        res_model.page_table.append(
                            PageTableEntryModel(
                                page_number=int(pt_raw.get("page_number", 0)),
                                frame_number=int(pt_raw.get("frame_number", -1)),
                                valid=bool(pt_raw.get("valid", True)),
                                dirty=bool(pt_raw.get("dirty", False)),
                                referenced=bool(pt_raw.get("referenced", True)),
                            )
                        )
                    res_model.logs.extend([str(l) for l in result_data.get("logs", [])])

                elif exp == "address_translation":
                    va = int(result_data.get("virtual_address", 0))
                    pn = int(result_data.get("page_number", 0))
                    offset = int(result_data.get("offset", 0))
                    page_fault = bool(result_data.get("page_fault", False))
                    fn = int(result_data.get("frame_number") or -1) if not page_fault else -1
                    pa = int(result_data.get("physical_address") or 0) if not page_fault else 0
                    msg = str(result_data.get("message", ""))
                    res_model.translations.append(
                        TranslationResultModel(
                            virtual_address=va,
                            page_number=pn,
                            offset=offset,
                            page_fault=page_fault,
                            frame_number=fn,
                            physical_address=pa,
                            message=msg,
                        )
                    )

                elif exp == "demand_paging":
                    ps = int(result_data.get("page_size", res_model.page_size))
                    tf = int(result_data.get("total_frames", 3))
                    ta = int(result_data.get("total_accesses", 0))
                    pf = int(result_data.get("page_faults", 0))
                    ph = int(result_data.get("page_hits", 0))
                    fr = float(result_data.get("fault_rate", 0.0))
                    steps: List[DemandPagingStepModel] = []
                    for st_raw in result_data.get("steps", []):
                        steps.append(
                            DemandPagingStepModel(
                                virtual_address=int(st_raw.get("virtual_address", 0)),
                                page_number=int(st_raw.get("page_number", 0)),
                                offset=int(st_raw.get("offset", 0)),
                                page_fault=bool(st_raw.get("page_fault", False)),
                                frame_number=int(st_raw.get("frame_number", -1)),
                                physical_address=int(st_raw.get("physical_address", 0)),
                                victim_page=int(st_raw.get("victim_page", -1)),
                                frame_contents=[int(c) for c in st_raw.get("frame_contents", [])],
                            )
                        )
                    res_model.demand_paging = DemandPagingResultModel(
                        page_size=ps,
                        total_frames=tf,
                        total_accesses=ta,
                        page_faults=pf,
                        page_hits=ph,
                        fault_rate=fr,
                        steps=steps,
                    )

                elif exp == "thrashing_curve":
                    thresh = int(result_data.get("thrashing_threshold_frames", 0))
                    ref_str = [int(r) for r in result_data.get("reference_string", [])]
                    pts: List[ThrashingPointModel] = []
                    for p_raw in result_data.get("points", []):
                        pts.append(
                            ThrashingPointModel(
                                frames=int(p_raw.get("frames", 0)),
                                page_faults=int(p_raw.get("page_faults", 0)),
                                fault_rate=float(p_raw.get("fault_rate", 0.0)),
                            )
                        )
                    res_model.thrashing = ThrashingResultModel(
                        reference_string=ref_str,
                        points=pts,
                        thrashing_threshold_frames=thresh,
                    )

            if not res_model.page_table:
                if config and config.custom_mappings:
                    for p, f in config.custom_mappings:
                        res_model.page_table.append(PageTableEntryModel(page_number=p, frame_number=f, valid=True))
                else:
                    res_model.page_table = [
                        PageTableEntryModel(page_number=0, frame_number=5, valid=True),
                        PageTableEntryModel(page_number=1, frame_number=2, valid=True),
                        PageTableEntryModel(page_number=7, frame_number=10, valid=True),
                    ]

            return res_model
    except Exception:
        pass

    # 2. Fallback regex parsing on human-readable text
    ps_match = re.search(r"Page Size:\s*(\d+)", stdout, re.IGNORECASE)
    if ps_match:
        res_model.page_size = int(ps_match.group(1))

    # Parse translation blocks
    va_matches = re.finditer(
        r"Virtual Address:\s*(\d+).*?Page Number:\s*(\d+).*?(?:Present in Frame (\d+).*?Physical Address:\s*(\d+)|Page Fault:\s*([^\n]+))",
        stdout,
        re.DOTALL,
    )
    for m in va_matches:
        va = int(m.group(1))
        pn = int(m.group(2))
        offset = va % res_model.page_size
        if m.group(3):
            fn = int(m.group(3))
            pa = int(m.group(4))
            res_model.translations.append(
                TranslationResultModel(
                    virtual_address=va,
                    page_number=pn,
                    offset=offset,
                    page_fault=False,
                    frame_number=fn,
                    physical_address=pa,
                    message="Address translated successfully.",
                )
            )
        else:
            msg = m.group(5).strip() if m.group(5) else "Page fault"
            res_model.translations.append(
                TranslationResultModel(
                    virtual_address=va,
                    page_number=pn,
                    offset=offset,
                    page_fault=True,
                    frame_number=-1,
                    physical_address=0,
                    message=msg,
                )
            )

    # Parse demand paging steps
    steps: List[DemandPagingStepModel] = []
    step_rows = re.findall(
        r"^\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(YES|NO)\s*\|\s*(\d+)\s*\|\s*([0-9\-]+)",
        stdout,
        re.MULTILINE,
    )
    for row in step_rows:
        va = int(row[1])
        pn = int(row[2])
        off = int(row[3])
        pf = row[4].strip() == "YES"
        fn = int(row[5])
        victim = int(row[6]) if row[6] != "-" else -1
        pa = fn * res_model.page_size + off if not pf or fn >= 0 else 0
        steps.append(
            DemandPagingStepModel(
                virtual_address=va,
                page_number=pn,
                offset=off,
                page_fault=pf,
                frame_number=fn,
                physical_address=pa,
                victim_page=victim,
            )
        )

    if steps:
        summary_m = re.search(
            r"Summary:\s*(\d+)\s*accesses,\s*(\d+)\s*faults,\s*(\d+)\s*hits(?:\s*\(Fault Rate:\s*([\d\.]+)%\))?",
            stdout,
        )
        if summary_m:
            ta = int(summary_m.group(1))
            pf = int(summary_m.group(2))
            ph = int(summary_m.group(3))
            fr = float(summary_m.group(4)) / 100.0 if summary_m.group(4) else (pf / ta if ta > 0 else 0.0)
        else:
            ta = len(steps)
            pf = sum(1 for s in steps if s.page_fault)
            ph = ta - pf
            fr = pf / ta if ta > 0 else 0.0

        res_model.demand_paging = DemandPagingResultModel(
            page_size=res_model.page_size,
            total_frames=3,
            total_accesses=ta,
            page_faults=pf,
            page_hits=ph,
            fault_rate=fr,
            steps=steps,
        )

    # Parse thrashing points
    pts: List[ThrashingPointModel] = []
    thrash_rows = re.findall(
        r"Frames:\s*(\d+)\s*->\s*Faults:\s*(\d+)\s*\(([\d\.]+)%\s*fault rate\)",
        stdout,
    )
    for tr in thrash_rows:
        pts.append(
            ThrashingPointModel(
                frames=int(tr[0]),
                page_faults=int(tr[1]),
                fault_rate=float(tr[2]) / 100.0,
            )
        )
    knee_m = re.search(r"Thrashing Threshold\):\s*(\d+)\s*frames", stdout)
    threshold = int(knee_m.group(1)) if knee_m else (pts[0].frames if pts else 0)

    if pts:
        res_model.thrashing = ThrashingResultModel(
            reference_string=[],
            points=pts,
            thrashing_threshold_frames=threshold,
        )

    if not res_model.page_table:
        res_model.page_table = [
            PageTableEntryModel(page_number=0, frame_number=5, valid=True),
            PageTableEntryModel(page_number=1, frame_number=2, valid=True),
            PageTableEntryModel(page_number=7, frame_number=10, valid=True),
        ]

    return res_model


def generate_process_ops_stdin(config_or_ops: Any) -> str:
    """Generate line-delimited commands for --process-ops."""
    lines: List[str] = []
    ops = getattr(config_or_ops, "operations", config_or_ops)
    if not isinstance(ops, (list, tuple)):
        return ""
    for op in ops:
        if not op:
            continue
        cmd = op[0]
        if cmd == "create":
            pid = op[1]
            arr = op[2] if len(op) > 2 else 0
            burst = op[3] if len(op) > 3 else 1
            prio = op[4] if len(op) > 4 else 1
            lines.append(f"create {pid} {arr} {burst} {prio}")
        elif cmd == "transition":
            pid = op[1]
            state = op[2]
            lines.append(f"transition {pid} {state}")
        elif cmd == "clear":
            lines.append("clear")
    return "\n".join(lines) + "\n"


def parse_process_lifecycle_output(stdout: str) -> ProcessLifecycleSimulationResultModel:
    """Parse C++ process lifecycle state machine stdout."""
    res_model = ProcessLifecycleSimulationResultModel()

    # 1. Try structured JSON parsing
    try:
        first_brace = stdout.find("{")
        last_brace = stdout.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            data = json.loads(stdout[first_brace : last_brace + 1])
            res = data.get("result", data)
            if isinstance(res, dict) and ("processes" in res or "transitions" in res):
                res_model.total_processes = int(res.get("total_processes", len(res.get("processes", []))))

                for p_raw in res.get("processes", []):
                    st = p_raw.get("state") or p_raw.get("current_state") or "New"
                    res_model.processes.append(
                        ProcessInstanceModel(
                            pid=int(p_raw.get("pid", 1)),
                            arrival_time=int(p_raw.get("arrival_time", 0)),
                            burst_time=int(p_raw.get("burst_time", 1)),
                            priority=int(p_raw.get("priority", 1)),
                            state=str(st),
                        )
                    )

                for t_raw in res.get("transitions", []):
                    req_st = t_raw.get("requested_state") or t_raw.get("to_state") or "None"
                    res_st = t_raw.get("resulting_state") or t_raw.get("to_state") or "None"
                    msg = t_raw.get("message") or t_raw.get("detail") or ""
                    res_model.transitions.append(
                        ProcessTransitionModel(
                            pid=int(t_raw.get("pid", 1)),
                            from_state=str(t_raw.get("from_state", "None")),
                            requested_state=str(req_st),
                            success=bool(t_raw.get("success", False)),
                            to_state=str(res_st),
                            message=str(msg),
                        )
                    )

                res_model.logs = [str(l) for l in res.get("logs", [])]
                return res_model
    except Exception:
        pass

    # 2. Text fallback parsing
    lines = stdout.splitlines()
    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        res_model.logs.append(line_s)
        m = re.match(
            r"PID\s+(\d+)\s+\|\s+(\w+)\s+->\s+(\w+)\s+\|\s+(SUCCESS|REJECTED)\s+\|\s+Resulting State:\s+(\w+)",
            line_s,
        )
        if m:
            pid = int(m.group(1))
            from_s = m.group(2)
            req_s = m.group(3)
            succ = m.group(4) == "SUCCESS"
            to_s = m.group(5)
            res_model.transitions.append(
                ProcessTransitionModel(
                    pid=pid,
                    from_state=from_s,
                    requested_state=req_s,
                    success=succ,
                    to_state=to_s,
                    message="Parsed from text output",
                )
            )
            continue

        m2 = re.match(
            r"(?:REJECTED:\s+)?Transition\s+PID\s+(\d+):\s+(\w+)\s+->\s+(\w+)(?:\s+\[(SUCCESS|REJECTED)\]|\s+is\s+illegal)?",
            line_s,
        )
        if m2:
            pid = int(m2.group(1))
            from_s = m2.group(2)
            req_s = m2.group(3)
            status_flag = m2.group(4)
            succ = (status_flag == "SUCCESS") and ("REJECTED" not in line_s) and ("illegal" not in line_s)
            res_model.transitions.append(
                ProcessTransitionModel(
                    pid=pid,
                    from_state=from_s,
                    requested_state=req_s,
                    success=succ,
                    to_state=req_s if succ else from_s,
                    message="Parsed from transition log",
                )
            )
            continue

        m3 = re.match(r"PID\s+(\d+):\s+.*state=(\w+)", line_s)
        if m3:
            pid = int(m3.group(1))
            st = m3.group(2)
            existing = next((p for p in res_model.processes if p.pid == pid), None)
            if existing:
                existing.state = st
            else:
                res_model.processes.append(
                    ProcessInstanceModel(pid=pid, arrival_time=0, burst_time=1, priority=1, state=st)
                )

    res_model.total_processes = len(res_model.processes)
    return res_model





