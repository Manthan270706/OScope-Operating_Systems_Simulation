"""Scheduling data models for process configuration, execution results, and metrics."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class AlgorithmType(str, Enum):
    """Supported CPU scheduling algorithms matching the C++ backend."""
    FCFS = "FCFS"
    SJF = "SJF"
    SRTF = "SRTF"
    PRIORITY = "Priority"
    ROUND_ROBIN = "Round Robin"
    MLFQ = "MLFQ"
    COMPARE_ALL = "Compare All"

    @property
    def menu_choice(self) -> int:
        """Map algorithm to CLI interactive menu choice."""
        mapping = {
            AlgorithmType.FCFS: 1,
            AlgorithmType.SJF: 2,
            AlgorithmType.SRTF: 3,
            AlgorithmType.PRIORITY: 4,
            AlgorithmType.ROUND_ROBIN: 5,
            AlgorithmType.MLFQ: 6,
            AlgorithmType.COMPARE_ALL: 7,
        }
        return mapping[self]

    @property
    def display_name(self) -> str:
        """Human-readable algorithm label."""
        names = {
            AlgorithmType.FCFS: "First-Come, First-Served (FCFS)",
            AlgorithmType.SJF: "Shortest Job First (SJF - Non-Preemptive)",
            AlgorithmType.SRTF: "Shortest Remaining Time First (SRTF - Preemptive)",
            AlgorithmType.PRIORITY: "Priority Scheduling (Non-Preemptive)",
            AlgorithmType.ROUND_ROBIN: "Round Robin (RR)",
            AlgorithmType.MLFQ: "Multilevel Feedback Queue (MLFQ)",
            AlgorithmType.COMPARE_ALL: "Compare All Algorithms",
        }
        return names.get(self, self.value)

    @property
    def requires_priority(self) -> bool:
        """Whether this algorithm uses process priority."""
        return self in (AlgorithmType.PRIORITY, AlgorithmType.COMPARE_ALL)

    @property
    def requires_quantum(self) -> bool:
        """Whether this algorithm requires a time quantum input."""
        return self in (AlgorithmType.ROUND_ROBIN, AlgorithmType.COMPARE_ALL)

    @property
    def requires_mlfq_quanta(self) -> bool:
        """Whether this algorithm requires MLFQ queue quanta."""
        return self in (AlgorithmType.MLFQ, AlgorithmType.COMPARE_ALL)


@dataclass
class ProcessInput:
    """User-provided process input row."""
    pid: int
    arrival_time: int
    burst_time: int
    priority: int = 0

    def validate(self) -> Optional[str]:
        """Validate process fields. Returns error string if invalid, None if valid."""
        if self.pid < 0:
            return f"Process PID ({self.pid}) must be non-negative."
        if self.arrival_time < 0:
            return f"Arrival time ({self.arrival_time}) for PID {self.pid} must be non-negative (>= 0)."
        if self.burst_time <= 0:
            return f"Burst time ({self.burst_time}) for PID {self.pid} must be positive (> 0)."
        return None


@dataclass
class AlgorithmConfig:
    """Configuration parameters for CPU scheduling run."""
    algorithm: AlgorithmType = AlgorithmType.FCFS
    rr_quantum: int = 2
    mlfq_q0: int = 2
    mlfq_q1: int = 4
    mlfq_q2: int = 8

    def validate(self) -> Optional[str]:
        """Validate algorithm specific parameters."""
        if self.algorithm.requires_quantum and self.rr_quantum <= 0:
            return f"Round Robin time quantum must be positive (> 0), got {self.rr_quantum}."
        if self.algorithm.requires_mlfq_quanta:
            if self.mlfq_q0 <= 0:
                return f"MLFQ Queue 0 quantum must be positive (> 0), got {self.mlfq_q0}."
            if self.mlfq_q1 <= 0:
                return f"MLFQ Queue 1 quantum must be positive (> 0), got {self.mlfq_q1}."
            if self.mlfq_q2 <= 0:
                return f"MLFQ Queue 2 quantum must be positive (> 0), got {self.mlfq_q2}."
        return None


@dataclass
class ExecutionSegmentModel:
    """Single timeline execution segment (Process slice or Idle)."""
    start_time: int
    end_time: int
    pid: Optional[int]
    is_idle: bool = False

    @property
    def duration(self) -> int:
        return self.end_time - self.start_time


@dataclass
class ProcessResultModel:
    """Per-process metrics returned by the C++ scheduler."""
    pid: int
    arrival_time: int
    burst_time: int
    completion_time: int
    turnaround_time: int
    waiting_time: int
    response_time: int


@dataclass
class AverageMetricsModel:
    """Aggregate simulation metrics."""
    average_waiting_time: float = 0.0
    average_turnaround_time: float = 0.0
    average_response_time: float = 0.0


@dataclass
class SchedulingResultModel:
    """Complete results from a single algorithm simulation."""
    algorithm_name: str
    total_processes: int
    timeline: List[ExecutionSegmentModel] = field(default_factory=list)
    process_results: List[ProcessResultModel] = field(default_factory=list)
    averages: AverageMetricsModel = field(default_factory=AverageMetricsModel)
    total_duration: int = 0
    raw_output: str = ""


@dataclass
class ComparisonEntryModel:
    """Row in the multi-algorithm comparison summary."""
    algorithm: str
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float


@dataclass
class SchedulingComparisonResultModel:
    """Complete multi-algorithm comparison results."""
    entries: List[ComparisonEntryModel] = field(default_factory=list)
    raw_output: str = ""
